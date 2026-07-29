from pathlib import Path

import pandas as pd
from src.utils.rag_tool.llm_rag_auditor import RAGAuditor


class EvaluateVQ:

    def __init__(self, data_base_path='../../data/graph/case_study/'):
        self.pdf_path = f"{data_base_path}raw_pdf_m"
        self.vq_path = f"{data_base_path}/case_4_v_kg"
        self.rag_auditor = RAGAuditor()
        pass

    def build_vector_db(self, case_ids=[]):

        root = Path(self.pdf_path)
        sub_dirs = [f for f in root.iterdir() if f.is_dir()]

        for d in sub_dirs:
            if d.name in case_ids:
                custom_meta_data: dict = {
                    "case_id": d.name
                }
                self.rag_auditor.ingest(self.pdf_path + "/" + d.name,
                                        custom_meta=custom_meta_data)

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

    def check_evaluation_condition(self, df):
        evaluation_label_list = []
        # 遍历三个列表：验证标签、分数、样本类型
        for v, e, st in zip(
                df['verification_label'].tolist(),
                self.convert_to_valid_int(df['rag_rate']),
                df['sample_type'].tolist()
        ):
            # 按 sample_type 决定判断条件
            if st == "evidence":
                condition = (e >= 4)
            elif st == "assemble":
                condition = (e == 1)
            else:
                condition = False  # 其他类型默认不通过

            # 你原本的规则：验证标签匹配 → 1，否则 0
            if (v == 1 and condition) or (v == 0 and not condition):
                evaluation_label_list.append(1)
            else:
                evaluation_label_list.append(0)
        return evaluation_label_list

    def evaluate_vq(self, case_id):

        filters = {"field": "meta.case_id", "operator": "==", "value": case_id}

        # process nodes
        node_vq_path = self.vq_path + "/" + case_id + '_nodes_vq.csv'
        df_node = pd.read_csv(node_vq_path)
        question_list = df_node[['sample_type', 'question']].to_dict(orient='records')
        resp_list = self.rag_auditor.ask_by_local_llm(question_list, filters=filters)
        df_node['rag_rate'] = resp_list
        try:
            evaluation_label_list = self.check_evaluation_condition(df_node)
            df_node['evaluation_label'] = evaluation_label_list
            df_node.to_csv(self.vq_path + "/" + case_id + '_nodes_vq_evaluation.csv', index=False)
        except Exception as e:
            print(e)
            df_node.to_csv(self.vq_path + "/" + case_id + '_nodes_vq_evaluation_tmp.csv', index=False)

        # process relations
        relation_vq_path = self.vq_path + "/" + case_id + '_edges_vq.csv'
        df_relation = pd.read_csv(relation_vq_path)
        question_list = df_relation[['sample_type', 'question']].to_dict(orient='records')
        resp_list = self.rag_auditor.ask_by_local_llm(question_list, filters=filters)
        df_relation['rag_rate'] = resp_list

        try:
            evaluation_label_list = self.check_evaluation_condition(df_relation)
            df_relation['evaluation_label'] = evaluation_label_list
            df_relation.to_csv(self.vq_path + "/" + case_id + '_edges_vq_evaluation.csv', index=False)
        except Exception as e:
            print(e)
            df_relation.to_csv(self.vq_path + "/" + case_id + '_edges_vq_evaluation_tmp.csv', index=False)

    def evaluate_all_vq(self, case_ids):

        self.build_vector_db(case_ids)

        for case_id in case_ids:
            self.evaluate_vq(case_id)


if __name__ == '__main__':
    obj = EvaluateVQ()

    case_ids = ['c001']
    obj.evaluate_all_vq(case_ids)