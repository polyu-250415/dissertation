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

    def query_with_retry(self,question, try_times=1):
        rsp = {}
        for i in range(try_times):
            try:
                rsp = self.kg_rag_auditor.query(question)
                if 'evidence' in rsp.keys() and len(rsp['evidence']) <= 2:
                    continue
                return rsp
            except Exception as e:
                print(e)

        if isinstance(rsp, dict) and "cypher" in rsp.keys():
            return {"answer": "Exception", "evidence": "", "cypher": rsp["cypher"]}
        else:
            return {"answer": "Exception", "evidence": "", "cypher": ""}

    def do_ds_rag(self, sector_id):
        # build KG
        create_kg_by_case(sector_id, path_dir = self.v_ds_path, excluded_properties=[])
        self.kg_rag_auditor.refresh_kg_schema()

        # build VQ
        df_question = pd.read_excel(self.v_ds_template, sheet_name="downstream_task").dropna(how="all")
        answer_list = []
        evidence_list = []
        cypher_list = []
        for question in df_question['Question']:
            print(f"Question from {sector_id}: {question}")
            rsp = self.query_with_retry(question)
            answer_list.append(rsp['answer'])
            evidence_list.append(rsp['evidence'])
            cypher_list.append(rsp['cypher'])

        df_question['ID'] = sector_id + df_question['ID']
        df_question['Answer'] = answer_list
        df_question['Evidence'] = evidence_list
        df_question['Cypher'] = cypher_list
        output_file = f"{self.v_ds_path}/{sector_id}_ds_rag.csv"
        df_question.to_csv(output_file, index=False)

    def redo_ds_rag(self, sector_id):
        """
        重跑Evidence为空的问题，原地更新csv
        """
        output_file = f"{self.v_ds_path}/{sector_id}_ds_rag.csv"
        df = pd.read_csv(output_file)

        # 识别空证据：NaN / "" / "   "
        mask_empty = df["Evidence"].isna() | (df["Evidence"].astype(str).str.strip() == "")
        rerun_subset = df[mask_empty]

        if rerun_subset.shape[0] == 0:
            print(f"[{sector_id}] 无Evidence为空记录，跳过redo")
            return

        print(f"[{sector_id}] 待重跑条数：{rerun_subset.shape[0]}")

        for loc_idx, row in rerun_subset.iterrows():
            q = row["Question"]
            print(f"redo query: {q}")
            resp = self.query_with_retry(q)
            df.at[loc_idx, "Answer"] = resp["answer"]
            df.at[loc_idx, "Evidence"] = resp["evidence"]

        # 覆盖原文件
        df.to_csv(output_file, index=False)
        print(f"[{sector_id}] redo完成，文件已更新：{output_file}")

    def do_all_ds_rag(self, sector_ids, redo_flag =False):
        for sector_id in sector_ids:
            if not redo_flag:
                self.do_ds_rag(sector_id)
            else:
                self.redo_ds_rag(sector_id)

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

    def evaluate_ds_rag(self, sector_id):

        input_file = f"{self.v_ds_path}/{sector_id}_ds_rag.csv"

        try:
            df_rag = pd.read_csv(input_file)
            question_list = df_rag['Question'].to_list()

            filters = {"field": "meta.sector_id", "operator": "==", "value": sector_id}
            resp_list = self.rag_auditor.query(question_list, filters)
            df_rag['rag_rate'] = resp_list

            df_rag.to_csv(self.v_ds_path + "/" + sector_id + '_ds_rag_evaluation.csv', index=False)
        except Exception as e:
            print(e)

    def evaluate_all_ds_rag(self, sector_ids):

        for sector_id in sector_ids:
            self.evaluate_ds_rag(sector_id)

if __name__ == '__main__':
    obj = EvaluateDSVQ()

    sector_ids = ['c115','c119']
    obj.do_all_ds_rag(sector_ids, redo_flag=False)

    for time in range(1):
        obj.do_all_ds_rag(sector_ids, redo_flag=True)