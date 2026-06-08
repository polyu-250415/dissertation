from src.utils.rag_tool.kg_rag_auditor import KGRAGAuditor
import pandas as pd, json
from src.utils.rag_tool.llm_rag_auditor import RAGAuditor
from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_case

class EvaluateDSVQ:
    def __init__(self,
                 data_base_path='../../data/graph/case_study/',
                 conf_path = '../../conf/coding_schema/'):
        self.kg_rag_auditor = KGRAGAuditor()
        self.v_ds_path = f"{data_base_path}case_6_v_ds"
        self.final_kg_path = f"{data_base_path}/case_7_final_kg"
        self.kg_rag_auditor = KGRAGAuditor()
        self.rag_auditor = RAGAuditor()
        self.v_ds_template = f"{conf_path}coding_schema.xlsx"
        self.pdf_path = f"{data_base_path}/raw_pdf_m"

    def build_vector_db(self, case_ids):

        for case_id in case_ids:
            custom_meta_data: dict = {
                "case_id": case_id
            }
            self.rag_auditor.ingest(self.pdf_path + "/" +case_id,
                                    custom_meta=custom_meta_data)

    def query_with_retry(self,question, try_times=2):

        for i in range(try_times):
            try:
                rsp = self.kg_rag_auditor.query(question)
                rsp_j =  json.loads(rsp)
                if len(rsp_j['evidence']) <= 2:
                    continue
                return rsp_j
            except Exception as e:
                print(e)
                return {"answer": "Exception", "evidence": ""}

        return {"answer": "Not Mention", "evidence": ""}

    def do_ds_rag(self, case_id):

        # build KG
        create_kg_by_case(case_id, path_dir = self.v_ds_path)
        self.kg_rag_auditor.refresh_kg_schema()

        # build VQ
        df_question = pd.read_excel(self.v_ds_template, sheet_name="downstream_task").dropna(how="all")
        answer_list = []
        evidence_list = []
        for question in df_question['Question']:
            print(f"Question from {case_id}: {question}")
            rsp = self.query_with_retry(question)
            answer_list.append(rsp['answer'])
            evidence_list.append(rsp['evidence'])

        df_question['ID'] = case_id + df_question['ID']
        df_question['Answer'] = answer_list
        df_question['Evidence'] = evidence_list
        output_file = f"{self.v_ds_path}/{case_id}_ds_rag.csv"
        df_question.to_csv(output_file, index=False)

    def do_all_ds_rag(self, case_ids):
        for case_id in case_ids:
            self.do_ds_rag(case_id)

    @staticmethod
    def convert_to_valid_int(resp_list):
        result = []
        for item in resp_list:
            try:
                num = int(item)
                if 1 <= num <= 5:
                    result.append(num)
                else:
                    result.append(0)
            except (ValueError, TypeError):
                result.append(0)
        return result

    def evaluate_ds_rag(self, case_id):

        input_file = f"{self.v_ds_path}/{case_id}_ds_rag.csv"

        try:
            df_rag = pd.read_csv(input_file)
            question_list = df_rag['Question'].to_list()

            filters = {"field": "meta.case_id", "operator": "==", "value": case_id}
            resp_list = self.rag_auditor.query(question_list, filters)
            df_rag['rag_rate'] = resp_list

            df_rag.to_csv(self.v_ds_path + "/" + case_id + '_ds_rag_evaluation.csv', index=False)
        except Exception as e:
            print(e)

    def evaluate_all_ds_rag(self, case_ids):

        self.build_vector_db(case_ids)

        for case_id in case_ids:
            self.evaluate_ds_rag(case_id)

if __name__ == '__main__':
    obj = EvaluateDSVQ()

    case_ids = ['c101', 'c102', 'c103', 'c104', 'c105', 'c106', 'c107','c108', 'c109','c201', 'c202', 'c203', 'c204',
                'c205','c206','c207','c208','c209','c210','c211']
    obj.do_all_ds_rag(case_ids)
    #obj.evaluate_all_ds_rag(case_ids)