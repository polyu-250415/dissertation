from pathlib import Path

import pandas as pd
from src.utils.llm_rag_tool.rag_auditor import RAGAuditor


class EvaluateEA:

    def __init__(self):
        self.pdf_path = "../../data/graph/case_study/raw_pdf_m"
        self.rag_ea_path = "../../data/graph/case_study/case_5_v_ea/"
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

    def evaluate_ea(self, call_id):

        filters = {"field": "meta.call_id", "operator": "==", "value": call_id}

        # process nodes
        node_vq_path = self.rag_ea_path + "/" + call_id + '_ea_vq.csv'
        df_node = pd.read_csv(node_vq_path)
        question_list = df_node["question"].values.tolist()

        resp_list = self.rag_auditor.ask(question_list, filters=filters)
        df_node['rag_rate'] = resp_list
        try:
            evaluation_label_list = [1 if (v == 1 and e >= 3) or (v == 0 and e < 3) else 0
                                     for v, e in zip(df_node['verification_label'].tolist(), self.convert_to_valid_int(resp_list))]
            df_node['evaluation_label'] = evaluation_label_list
            df_node.to_csv(self.rag_ea_path + "/" + call_id + '_ea_vq_evaluation.csv', index=False)
        except Exception as e:
            df_node.to_csv(self.rag_ea_path + "/" + call_id + '_ea_vq_evaluation_tmp.csv', index=False)
            print(e)


    def evaluate_all_ea(self, call_ids):

        self.build_vector_db()

        for call_id in call_ids:
            self.evaluate_ea(call_id)

    @staticmethod
    def find_redundant_nodes(id_to_name, csv_path: str):
        """
        Reads a CSV file, groups by (src_node_id, dst_node_id), and returns
        the list of pairs where every row in the group has evaluation_label == 1.
        """
        df = pd.read_csv(csv_path)

        # Group by src_node_id and dst_node_id
        grouped = df.groupby(['node_id_1', 'node_id_2'])

        valid_pairs = []

        for (src, dst), group in grouped:
            # Check if all evaluation_label values in the group are 1
            if (group['evaluation_label'] == 1).all():
                valid_pairs.append({
                    'node_id': dst,
                    'node_name': id_to_name[dst],
                    'new_node_id':src,
                    'new_node_name': id_to_name[src]
                                   })
        return valid_pairs

    def find_all_redundant_nodes(self, call_ids):
        valid_pairs = []

        for call_id in call_ids:
            nodes_file = f'{self.rag_ea_path}{call_id}_nodes.csv'
            src = pd.read_csv(nodes_file)
            # Create fast lookup dictionary: {id: name}
            id_to_name = dict(zip(src['node_id'], src['node_name']))
            csv_path = self.rag_ea_path + "/" + call_id + "_ea_vq_evaluation.csv"

            valid_pairs.extend(self.find_redundant_nodes(id_to_name, csv_path))

        pd.DataFrame(valid_pairs).to_csv(self.rag_ea_path + "/" + 'redundant_pairs.csv', index=False)

if __name__ == '__main__':
    obj = EvaluateEA()


    call_ids = ['c002']
    obj.evaluate_all_ea(call_ids)
    obj.find_all_redundant_nodes(call_ids)