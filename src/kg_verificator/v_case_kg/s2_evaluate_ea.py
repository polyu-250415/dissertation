from pathlib import Path

import pandas as pd
from src.utils.rag_tool.llm_rag_auditor import RAGAuditor


class EvaluateEA:

    def __init__(self,data_base_path='../../data/graph/case_study/'):
        self.pdf_path = f"{data_base_path}/raw_pdf_m"
        self.rag_ea_path = f"{data_base_path}/case_5_v_ea/"
        self.rag_auditor = RAGAuditor()
        self.accept_threshold = 0.9
        pass

    def build_vector_db(self, case_ids):

        for case_id in case_ids:
            custom_meta_data: dict = {
                "case_id": case_id
            }
            self.rag_auditor.ingest(self.pdf_path + "/" +case_id,
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

    def evaluate_ea(self, case_id):

        filters = {"field": "meta.case_id", "operator": "==", "value": case_id}
        try:
            node_vq_path = self.rag_ea_path + "/" + case_id + '_ea_vq.csv'
            df_node = pd.read_csv(node_vq_path)

            question_list = df_node[['sample_type', 'question']].to_dict(orient='records')

            resp_list = self.rag_auditor.ask(question_list, filters=filters)
            df_node['rag_rate'] = resp_list

            evaluation_label_list = [1 if (v == 1 and e >= 4) or (v == 0 and e < 3) else 0
                                     for v, e in zip(df_node['verification_label'].tolist(), self.convert_to_valid_int(resp_list))]
            df_node['evaluation_label'] = evaluation_label_list
            df_node.to_csv(self.rag_ea_path + "/" + case_id + '_ea_vq_evaluation.csv', index=False)
        except Exception as e:
            df_node.to_csv(self.rag_ea_path + "/" + case_id + '_ea_vq_evaluation_tmp.csv', index=False)
            print(e)


    def evaluate_all_ea(self, case_ids):

        self.build_vector_db(case_ids)

        for case_id in case_ids:
            self.evaluate_ea(case_id)

    @staticmethod
    def find_redundant_nodes_from_ds_evaluation(id_to_name, csv_path: str):
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

    def find_redundant_nodes_from_accepted_threshold(self,id_to_name, csv_path: str):
        """
        Reads a CSV file, groups by (src_node_id, dst_node_id), and returns
        the list of pairs where every row in the group has evaluation_label == 1.
        """
        df = pd.read_csv(csv_path)
        df_filter = df[df['similarity_score'] >= self.accept_threshold]

        valid_pairs = []
        for _, row in df_filter.iterrows():

            valid_pairs.append({
                    'node_id': row['node_id_2'],
                    'node_name': id_to_name[row['node_id_2']],
                    'new_node_id':row['node_id_1'],
                    'new_node_name': id_to_name[row['node_id_1']]
                                   })
        return valid_pairs

    def find_all_redundant_nodes(self, case_ids):
        valid_pairs = []

        for case_id in case_ids:
            try:
                nodes_file = f'{self.rag_ea_path}{case_id}_nodes.csv'
                src = pd.read_csv(nodes_file)
                id_to_name = dict(zip(src['node_id'], src['node_name']))

                similarity_csv_path = self.rag_ea_path + "/" + case_id + "_nodes_similarity.csv"
                valid_pairs.extend(self.find_redundant_nodes_from_accepted_threshold(id_to_name, similarity_csv_path))

                csv_path = self.rag_ea_path + "/" + case_id + "_ea_vq_evaluation.csv"
                valid_pairs.extend(self.find_redundant_nodes_from_ds_evaluation(id_to_name, csv_path))
            except Exception as e:
                print(e)
                pass

        pd.DataFrame(valid_pairs).to_csv(self.rag_ea_path + "/" + 'redundant_pairs.csv', index=False)

if __name__ == '__main__':
    obj = EvaluateEA()

    case_ids = ['c002']
    obj.evaluate_all_ea(case_ids)
    obj.find_all_redundant_nodes(case_ids)