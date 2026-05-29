import pandas as pd


class RebuildKG():

    def __init__(self, data_base_path="../../data/graph/case_study/"):
        self.rag_ea_path = f"{data_base_path}case_5_v_ea/"
        self.rebuild_kg_path = f"{data_base_path}case_6_rebuild_kg/"
        pass

    def normalize_entities(self, redundant_id_dict, case_id):
        """
        Normalize duplicate node IDs based on a mapping file.

        Steps:
        1. Build mapping dict from redundant_pairs.csv (node_id -> new_node_id).
        2. Remove rows from nodes CSV whose node_id is in the mapping.
        3. Replace src_node_id / dst_node_id in relations CSV using the mapping.
        """

        src_nodes_path = self.rag_ea_path + case_id + "_nodes.csv"
        dst_nodes_path = self.rebuild_kg_path + case_id + "_nodes.csv"
        src_relations_path = self.rag_ea_path + case_id + "_relations.csv"
        dst_relations_path = self.rebuild_kg_path + case_id + "_relations.csv"

        df_src_nodes = pd.read_csv(src_nodes_path)

        original_count = len(df_src_nodes)
        # Filter out rows where node_id is in the mapping (i.e., redundant nodes)
        nodes_df_filtered = df_src_nodes[~df_src_nodes['node_id'].isin(redundant_id_dict.keys())]
        removed_count = original_count - len(nodes_df_filtered)
        print(f"Nodes: {original_count} rows -> removed {removed_count} redundant nodes, "
              f"{len(nodes_df_filtered)} remain.")
        nodes_df_filtered.to_csv(dst_nodes_path, index=False)
        print(f"Saved filtered nodes to {dst_nodes_path}")

        relations_df = pd.read_csv(src_relations_path)
        relations_df['src_node_id'] = relations_df['src_node_id'].replace(redundant_id_dict)
        relations_df['dst_node_id'] = relations_df['dst_node_id'].replace(redundant_id_dict)

        filter_relations_df = relations_df.drop_duplicates(
            subset=["src_node_id", "dst_node_id", "relation_type"],
            keep="first"
        )

        filter_relations_df.to_csv(dst_relations_path, index=False)
        print(f"Updated relations saved to {dst_relations_path}")
        print("Done.")

    def rebuild_all_kg(self, case_ids):
        redundant_id_path = self.rag_ea_path + "redundant_pairs.csv"
        df_redundant_id = pd.read_csv(redundant_id_path)
        redundant_id_dict = dict(zip(df_redundant_id['node_id'], df_redundant_id['new_node_id']))

        for case_id in case_ids:
            self.normalize_entities(redundant_id_dict, case_id=case_id)

if __name__ == '__main__':
    obj = RebuildKG()
    case_ids = ['c002']
    obj.rebuild_all_kg(case_ids)
