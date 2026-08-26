from src.utils.rag_tool.kg_rag_auditor import KGRAGAuditor
import pandas as pd, json, os
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

    def query_with_retry(self,question, cypher_stmt='', try_times=1):
        rsp = {}
        for i in range(try_times):
            try:
                rsp = self.kg_rag_auditor.query(question, cypher_stmt=cypher_stmt)
                return rsp
            except Exception as e:
                print(e)

        if isinstance(rsp, dict) and "cypher" in rsp.keys():
            return {"answer": "Exception", "evidence": ""}
        else:
            return {"answer": "Exception", "evidence": ""}

    def do_ds_rag(self, case_id):

        # build KG
        create_kg_by_case(case_id, path_dir = self.v_ds_path, excluded_properties=['case_title', 'evidence_location','evidence_label', 'object_definition'])
        self.kg_rag_auditor.refresh_kg_schema()

        if not os.path.exists(f"{self.v_ds_path}/{case_id}_nodes.csv"):
            return

        # build VQ
        df_question = pd.read_excel(self.v_ds_template, sheet_name="downstream_task").dropna(how="all")
        answer_list = []
        evidence_list = []
        for index, row in df_question.iterrows():
            print(f"Question from {case_id}: {row['Question']}")
            rsp = self.query_with_retry(row['Question'],row['Cypher'])
            answer_list.append(rsp['answer'])
            evidence_list.append(rsp['evidence'])

        df_question['ID'] = case_id + df_question['ID']
        df_question['Answer'] = answer_list
        df_question['Evidence'] = evidence_list
        output_file = f"{self.v_ds_path}/{case_id}_ds_rag.csv"
        df_question.to_csv(output_file, index=False)

    def redo_ds_rag(self, case_id):
        """
        重跑Evidence为空的问题，原地更新csv
        """
        output_file = f"{self.v_ds_path}/{case_id}_ds_rag.csv"
        df = pd.read_csv(output_file)

        # 识别空证据：NaN / "" / "   "
        mask_empty = df["Evidence"].isna() | (df["Evidence"].astype(str).str.strip() == "")
        rerun_subset = df[mask_empty]

        if rerun_subset.shape[0] == 0:
            print(f"[{case_id}] 无Evidence为空记录，跳过redo")
            return

        print(f"[{case_id}] 待重跑条数：{rerun_subset.shape[0]}")

        for index, row in rerun_subset.iterrows():
            print(f"Question from {case_id}: {row['Question']}")
            rsp = self.query_with_retry(row['Question'], row['Cypher'])
            df.at[index, "Answer"] = rsp["answer"]
            df.at[index, "Evidence"] = rsp["evidence"]

        # 覆盖原文件
        df.to_csv(output_file, index=False)
        print(f"[{case_id}] redo完成，文件已更新：{output_file}")

    def do_all_ds_rag(self, case_ids, redo_flag =False):
        for case_id in case_ids:
            try:
                if not redo_flag:
                    self.do_ds_rag(case_id)
                else:
                    self.redo_ds_rag(case_id)
            except Exception as e:
                print(e)

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

    sector_ids = {"s001": ['c001','c002','c003','c004','c005','c006','c007','c008','c009','c010','c011','c012','c013','c014','c015','c016','c017'],
        "s002": ['c101', 'c102', 'c103', 'c104', 'c105', 'c106', 'c107', 'c108', 'c109','c110','c111', 'c112', 'c113', 'c114', 'c115', 'c116', 'c117', 'c118', 'c119','c120','c121', 'c122', 'c123', 'c124', 'c125', 'c126'],
        "s003": ['c201', 'c202', 'c203', 'c204', 'c205', 'c206', 'c207', 'c208', 'c209', 'c210', 'c211','c212','c213', 'c214', 'c215', 'c216', 'c217', 'c218', 'c219', 'c220', 'c221','c222','c223', 'c224', 'c225', 'c226', 'c227']
                  }
    sector_id = 's003'
    obj.do_all_ds_rag(sector_ids[sector_id], redo_flag=False)
    for time in range(1):
        obj.do_all_ds_rag(sector_ids[sector_id], redo_flag=True)