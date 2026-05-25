from pathlib import Path

import pandas as pd

from src.utils.llm_rag_tool.rag_auditor import RAGAuditor


class EvaluateVQ:

    def __init__(self):
        self.pdf_path = "../../data/graph/case_study/raw_pdf_m"
        self.vq_path = "../../data/graph/case_study/case_4_v_kg"
        self.rag_auditor = RAGAuditor()
        pass

    def build_vector_db(self):

        root = Path(self.pdf_path)
        sub_dirs = [f for f in root.iterdir() if f.is_dir()]

        for d in sub_dirs:
            custom_meta_data: dict = {
                "call_id": d.name
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

    def evaluate_vq(self, call_id):

        filters = {"field": "meta.call_id", "operator": "==", "value": call_id}

        # process nodes
        node_vq_path = self.vq_path + "/" + call_id + '_nodes_vq.csv'
        df_node = pd.read_csv(node_vq_path)
        question_list = df_node["question"].values.tolist()

        resp_list = self.rag_auditor.ask(question_list, filters=filters)
        df_node['rag_rate'] = resp_list
        try:
            evaluation_label_list = [1 if (v == 1 and e >= 3) or (v == 0 and e < 3) else 0
                                     for v, e in zip(df_node['verification_label'].tolist(), self.convert_to_valid_int(resp_list))]
            df_node['evaluation_label'] = evaluation_label_list
            df_node.to_csv(self.vq_path + "/" + call_id + '_nodes_vq_evaluation.csv', index=False)
        except Exception as e:
            df_node.to_csv(self.vq_path + "/" + call_id + '_nodes_vq_evaluation_tmp.csv', index=False)

        # process relations
        relation_vq_path = self.vq_path + "/" + call_id + '_relations_vq.csv'
        df_relation = pd.read_csv(relation_vq_path)
        question_list = df_relation["question"].values.tolist()

        resp_list = self.rag_auditor.ask(question_list, filters=filters)
        df_relation['rag_rate'] = resp_list

        try:
            evaluation_label_list = [1 if (v == 1 and e >= 3) or (v == 0 and e < 3) else 0
                                     for v, e in
                                     zip(df_relation['verification_label'].tolist(), self.convert_to_valid_int(resp_list))]
            df_relation['evaluation_label'] = evaluation_label_list
            df_relation.to_csv(self.vq_path + "/" + call_id + '_relations_vq_evaluation.csv', index=False)
        except Exception as e:
            print(e)
            df_relation.to_csv(self.vq_path + "/" + call_id + '_relations_vq_evaluation_tmp.csv', index=False)

    def evaluate_all_vq(self, call_ids):

        self.build_vector_db()

        for call_id in call_ids:
            self.evaluate_vq(call_id)


if __name__ == '__main__':
    obj = EvaluateVQ()

    call_ids = ['c002']
    obj.evaluate_all_vq(call_ids)