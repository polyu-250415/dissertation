from pathlib import Path

import pandas as pd

from src.utils.llm_rag_tool.rag_auditor import RAGAuditor


class AlignRwN:

    def __init__(self):
        self.pdf_path = "../data/graph/case_study/raw_pdf"
        self.vq_path = "../data/graph/case_study/case_4_v_kg"
        self.rag_auditor = RAGAuditor()
        pass

    @staticmethod
    def align_relations_with_nodes(nodes_csv_path, relations_csv_path,
                                   output_nodes_path=None, output_relations_path=None):
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

        # Save cleaned files if paths provided
        if output_nodes_path:
            nodes_df.to_csv(output_nodes_path, index=False)
            print(f"Nodes saved to {output_nodes_path}")
        if output_relations_path:
            relations_df.to_csv(output_relations_path, index=False)
            print(f"Relations saved to {output_relations_path}")

    @staticmethod
    def filter_by_node_id(nodes_path, relations_path,
                          output_nodes_path="c001_nodes_filtered.csv",
                          output_relations_path="c001_relations_filtered.csv",
                          keep_unreferenced_nodes=True):
        """
        Filter nodes and relations using node_id as the key.

        Steps:
        1. Deduplicate nodes by node_id (keep first occurrence).
        2. Filter relations: keep only rows where src_node_id and dst_node_id exist in nodes.
        3. Optionally remove nodes that are not referenced in any relation.

        Args:
            nodes_path (str): Path to original nodes CSV.
            relations_path (str): Path to original relations CSV.
            output_nodes_path (str): Output path for filtered nodes.
            output_relations_path (str): Output path for filtered relations.
            keep_unreferenced_nodes (bool): If True, keep all unique nodes.
                                            If False, keep only nodes appearing in relations.
        """
        # Load data
        nodes_df = pd.read_csv(nodes_path)
        relations_df = pd.read_csv(relations_path)

        # 1. Deduplicate nodes by node_id (keep first row)
        nodes_unique = nodes_df.drop_duplicates(subset=['node_id'], keep='first')
        print(f"Original nodes: {len(nodes_df)} rows, unique node_ids: {len(nodes_unique)}")

        # 2. Get set of valid node IDs
        valid_node_ids = set(nodes_unique['node_id'])

        # 3. Filter relations
        initial_rel_count = len(relations_df)
        relations_filtered = relations_df[
            relations_df['src_node_id'].isin(valid_node_ids) &
            relations_df['dst_node_id'].isin(valid_node_ids)
            ].copy()
        print(f"Original relations: {initial_rel_count}, kept: {len(relations_filtered)}")
        print(f"Dropped {initial_rel_count - len(relations_filtered)} relations with invalid node IDs.")

        # 4. Optionally filter nodes to only those that appear in remaining relations
        if not keep_unreferenced_nodes:
            referenced_nodes = set(relations_filtered['src_node_id']).union(set(relations_filtered['dst_node_id']))
            nodes_final = nodes_unique[nodes_unique['node_id'].isin(referenced_nodes)]
            print(f"Nodes kept (only those referenced in relations): {len(nodes_final)}")
        else:
            nodes_final = nodes_unique
            print(f"Nodes kept (all unique nodes): {len(nodes_final)}")

        # Save to CSV
        nodes_final.to_csv(output_nodes_path, index=False)
        relations_filtered.to_csv(output_relations_path, index=False)
        print(f"\nFiltered nodes saved to: {output_nodes_path}")
        print(f"Filtered relations saved to: {output_relations_path}")

        return nodes_final, relations_filtered

    def screen_nodes(self, call_ids):
        for call_id in call_ids:
            vq_nodes_file = f"../data/graph/case_study/case_4_v_kg/{call_id}_nodes_vq_evaluation.csv"
            vq_relations_file = f"../data/graph/case_study/case_4_v_kg/{call_id}_relations_vq_evaluation.csv"

            aligned_nodes_file = f"../data/graph/case_study/case_4_v_kg/{call_id}_nodes_aligned.csv"
            aligned_relations_file = f"../data/graph/case_study/case_4_v_kg/{call_id}_relations_aligned.csv"

            nodes_file = f"../data/graph/case_study/combination_kg/{call_id}_nodes.csv"
            relations_file = f"../data/graph/case_study/combination_kg/{call_id}_relations.csv"

            rebuilt_nodes_file = f"../data/graph/case_study/rebuild_kg/{call_id}_nodes.csv"
            rebuilt_relations_file = f"../data/graph/case_study/rebuild_kg/{call_id}_relations.csv"

            self.align_relations_with_nodes(
                nodes_csv_path=vq_nodes_file,
                relations_csv_path=vq_relations_file,
                output_nodes_path=aligned_nodes_file,
                output_relations_path=aligned_relations_file
            )

            self.filter_by_node_id(
                nodes_path=nodes_file,
                relations_path=relations_file,
                output_nodes_path=rebuilt_nodes_file,
                output_relations_path=rebuilt_relations_file,
                keep_unreferenced_nodes=True
            )


if __name__ == '__main__':
    obj = AlignRwN()

    call_ids = ['c005', 'c006']
    obj.screen_nodes(call_ids)