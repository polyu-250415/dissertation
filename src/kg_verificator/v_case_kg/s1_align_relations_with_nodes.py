from pathlib import Path

import pandas as pd

from src.utils.llm_rag_tool.rag_auditor import RAGAuditor


class AlignRwN:

    def __init__(self):
        self.pdf_path = "../../data/graph/case_study/raw_pdf_m"
        self.unit_path = "../../data/graph/case_study/case_3_unite"
        self.vq_path = "../../data/graph/case_study/case_4_v_kg"
        self.ea_path = "../../data/graph/case_study/case_5_v_ea"
        self.rag_auditor = RAGAuditor()
        pass

    @staticmethod
    def align_relations_with_nodes(nodes_csv_path,
                                   relations_csv_path,
                                   output_nodes_path,
                                   output_relations_path,
                                   unite_nodes_csv_path,
                                   unite_relations_csv_path,
                                   filter_nodes_path,
                                   filter_relations_path,
                                   ):
        """
        Ensure that valid relations only connect valid nodes.

        - Valid node: evaluation_label == 1
        - Valid relation: evaluation_label == 1
        - If a relation is valid but its source or destination node is invalid,
          the relation's evaluation_label is set to 0.

        Args:
            nodes_csv_path (str): Path to nodes CSV file.
            relations_csv_path (str): Path to relations CSV file.
            output_nodes_path (str, optional): Path to save cleaned nodes CSV.
            output_relations_path (str, optional): Path to save cleaned relations CSV.

        Returns:
            tuple: (nodes_df, relations_df) after alignment.
        """
        # Load data
        nodes_df = pd.read_csv(nodes_csv_path)
        relations_df = pd.read_csv(relations_csv_path)

        # Group stats
        group_ok = relations_df.groupby("group")["evaluation_label"].agg(
            lambda x: (x == 1).all()
        )
        groups_to_keep = group_ok[group_ok].index.tolist()

        print(f"Groups kept: {len(groups_to_keep)}")
        relations_df = relations_df[relations_df["group"].isin(groups_to_keep)].copy()

        # Get set of valid node IDs
        valid_nodes = set(nodes_df[nodes_df['evaluation_label'] == 1]['node_id'])

        # Track changes
        invalidated_relations = []

        # Process each relation
        for idx, row in relations_df.iterrows():
            if row['evaluation_label'] == 1:
                src = row['src_node_id']
                dst = row['dst_node_id']
                if src not in valid_nodes or dst not in valid_nodes:
                    # Demote this relation to invalid
                    relations_df.at[idx, 'evaluation_label'] = 0
                    invalidated_relations.append((row['src_node_id'], row['dst_node_id'], row['relation_type']))

        # Output summary
        print(
            f"Total relations initially valid: {len(relations_df[relations_df['evaluation_label'] == 1]) + len(invalidated_relations)}")
        print(f"Relations demoted due to invalid endpoints: {len(invalidated_relations)}")
        print(f"Remaining valid relations: {len(relations_df[relations_df['evaluation_label'] == 1])}")

        align_nodes_df = nodes_df[nodes_df['evaluation_label'] == 1]
        if output_nodes_path:
            align_nodes_df.to_csv(output_nodes_path, index=False)
            print(f"Nodes saved to {output_nodes_path}")

        align_relations_df = relations_df[relations_df['evaluation_label'] == 1]
        if output_relations_path:
            align_relations_df.to_csv(output_relations_path, index=False)
            print(f"Relations saved to {output_relations_path}")

        valid_node_idx = align_nodes_df['node_id'].unique().tolist()
        unite_nodes_df = pd.read_csv(unite_nodes_csv_path)
        unite_nodes_df = unite_nodes_df[unite_nodes_df['node_id'].isin(valid_node_idx)]
        unite_nodes_df.to_csv(filter_nodes_path, index=False)


        unite_relations_df = pd.read_csv(unite_relations_csv_path)
        align_relations_df['key'] = (align_relations_df['src_node_id'].astype(str) + "_" +
                                     align_relations_df['relation_type'].astype(str) + "_" +
                                     align_relations_df['dst_node_id'].astype(str))
        valid_relation_keys = align_relations_df['key'].unique().tolist()
        unite_relations_df['key'] = (unite_relations_df['src_node_id'].astype(str) + "_" +
                                     unite_relations_df['relation_type'].astype(str) + "_" +
                                     unite_relations_df['dst_node_id'].astype(str))
        unite_relations_df = unite_relations_df[unite_relations_df['key'].isin(valid_relation_keys)].drop('key', axis=1)
        unite_relations_df.to_csv(filter_relations_path, index=False)


    def screen_nodes(self, call_ids):
        for call_id in call_ids:
            vq_nodes_file = f"{self.vq_path}/{call_id}_nodes_vq_evaluation.csv"
            vq_relations_file = f"{self.vq_path}/{call_id}_relations_vq_evaluation.csv"

            aligned_nodes_file = f"{self.vq_path}/{call_id}_nodes_aligned.csv"
            aligned_relations_file = f"{self.vq_path}/{call_id}_relations_aligned.csv"

            nodes_file = f"{self.unit_path}/{call_id}_nodes.csv"
            relations_file = f"{self.unit_path}/{call_id}_relations.csv"

            filter_nodes_file = f"{self.ea_path}/{call_id}_nodes.csv"
            filter_relations_file = f"{self.ea_path}/{call_id}_relations.csv"

            self.align_relations_with_nodes(
                nodes_csv_path=vq_nodes_file,
                relations_csv_path=vq_relations_file,
                output_nodes_path=aligned_nodes_file,
                output_relations_path=aligned_relations_file,
                unite_nodes_csv_path=nodes_file,
                unite_relations_csv_path=relations_file,
                filter_nodes_path=filter_nodes_file,
                filter_relations_path=filter_relations_file
            )


if __name__ == '__main__':
    obj = AlignRwN()

    call_ids = ['c002']
    obj.screen_nodes(call_ids)