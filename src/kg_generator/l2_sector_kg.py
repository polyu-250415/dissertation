import pandas as pd
import os

from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_files
from src.utils.graph_tools.create_paper_graph_by_id import clear_whole_database


class SectorKG:
    def __init__(self):
        self.rebuild_kg_path = "../data/graph/case_study/case_6_rebuild_kg/"
        self.sector_raw_path = "../data/graph/case_study/sector_1_raw_m/"
        self.norm_nodes_path = "../data/graph/case_study/sector_2_norm_nodes/"

        if not os.path.exists(self.sector_raw_path):
            os.makedirs(self.sector_raw_path, exist_ok=True)

        if not os.path.exists(self.norm_nodes_path):
            os.makedirs(self.norm_nodes_path, exist_ok=True)

    def concat_cases_by_sector(self, sector_id, case_ids):
        df_nodes = pd.DataFrame()
        df_edges = pd.DataFrame()
        for case_id in case_ids:
            node_file = self.rebuild_kg_path + f'{case_id}_nodes.csv'
            edge_file = self.rebuild_kg_path + f'{case_id}_relations.csv'
            df_nodes = pd.concat([df_nodes, pd.read_csv(node_file)])
            df_edges = pd.concat([df_edges, pd.read_csv(edge_file)])

        df_nodes.to_csv(self.sector_raw_path + f'{sector_id}_nodes.csv', index=False)
        df_edges.to_csv(self.sector_raw_path + f'{sector_id}_relations.csv', index=False)

    def conceptualize_nodes_by_model(self):
        # prompt: sector_l1_conceptualizing_kg
        pass

    def build_mid_nodes(self, sector_id):
        src_file = self.sector_raw_path + f'{sector_id}_nodes_gemini.csv'
        mid_l1_node_file = self.norm_nodes_path + f'{sector_id}_l1_nodes.csv'
        mid_l2_node_file = self.norm_nodes_path + f'{sector_id}_l2_nodes.csv'
        mid_relation_file = self.norm_nodes_path + f'{sector_id}_l12_relations.csv'

        # Step 1: Read original CSV file
        print("Reading original CSV file...")
        df_original = pd.read_csv(src_file)
        print(f"Successfully loaded data: {len(df_original)} records")

        # Step 2: Process Layer 1 Knowledge Graph Nodes
        print("\nProcessing Layer 1 Knowledge Graph Nodes...")
        # Add s001M02 prefix to sub_category_id
        df_original['prefixed_subcat_id'] = 's001M02' + df_original['sub_category_id']

        # Extract and rename columns for Layer 1
        layer1_mapping = {
            'node_id': 'node_id',
            'node_name': 'node_name',
            'prefixed_subcat_id': 'parent_id',
            'sub_category': 'category',
            'case_title': 'case_title',
            'evidence_statement': 'evidence_statement'
        }

        layer1_df = df_original[list(layer1_mapping.keys())].copy()
        layer1_df.columns = list(layer1_mapping.values())
        print(f"Layer 1 nodes generated: {len(layer1_df)} nodes")

        # Step 3: Process Layer 2 Knowledge Graph Nodes
        print("\nProcessing Layer 2 Knowledge Graph Nodes...")
        # Extract unique subcategory data
        layer2_data = df_original[['prefixed_subcat_id', 'sub_category', 'category']].drop_duplicates()
        layer2_data['evidence_label'] ='I'
        layer2_data['case_title'] = 'construction'
        # Rename columns for Layer 2
        layer2_mapping = {
            'prefixed_subcat_id': 'node_id',
            'sub_category': 'node_name',
            'category': 'category',
            'evidence_label':'evidence_label',
            'case_title': 'case_title'
        }

        layer2_df = layer2_data.copy()
        layer2_df.columns = list(layer2_mapping.values())
        layer2_df = layer2_df.drop_duplicates(subset='node_id')
        print(f"Layer 2 nodes generated: {len(layer2_df)} nodes")

        # Step 4: Create Child-Parent Relationships
        print("\nCreating child-parent relationships...")
        relationship_df = layer1_df[['node_id', 'parent_id']].copy()
        relationship_df['relation_type'] = 'is an instance of'
        relationship_df['case_title'] = 'construction'
        relationship_df = relationship_df.rename(columns={'node_id': 'src_node_id',
                                                          'parent_id': 'dst_node_id'})
        relationship_df = relationship_df.drop_duplicates()

        # Validate relationships
        valid_parents = set(layer2_df['node_id'])
        relationship_parents = set(relationship_df['dst_node_id'])
        missing_parents = relationship_parents - valid_parents

        if not missing_parents:
            print("✅ Relationship validation passed: All parent IDs exist in Layer 2")
        else:
            print(f"⚠️ Missing parent IDs found: {missing_parents}")

        print(f"Relationships generated: {len(relationship_df)} records")

        # Save all output files
        print("\nSaving output files...")

        layer1_df.to_csv(mid_l1_node_file, index=False)
        layer2_df.to_csv(mid_l2_node_file, index=False)
        relationship_df.to_csv(mid_relation_file, index=False)

    def build_l2_relations(self, sector_id):
        """
        Build L2 Layer Knowledge Graph Relations
        Steps:
        1. Read original relations and node files
        2. Map each node to its parent ID (with s001M02 prefix)
        3. Reuse original relation types between parent nodes
        4. Generate deduplicated L2 relation set
        """
        # --------------------------
        # Step 1: Read input files
        # --------------------------
        relations_input_path = self.sector_raw_path + f'{sector_id}_relations.csv'
        nodes_input_path = self.norm_nodes_path + f'{sector_id}_l1_nodes.csv'
        output_path: str = self.norm_nodes_path + f'{sector_id}_l2_relations.csv'

        print("=== Step 1: Reading Input Files ===")

        if not os.path.exists(relations_input_path):
            raise FileNotFoundError(f"Relations file not found: {relations_input_path}")
        relations_df = pd.read_csv(relations_input_path)
        print(f"✅ Loaded relations file: {len(relations_df)} records")

        if not os.path.exists(nodes_input_path):
            raise FileNotFoundError(f"Nodes file not found: {nodes_input_path}")
        nodes_df = pd.read_csv(nodes_input_path)

        # --------------------------
        # Step 2: Create node -> parent mapping
        # --------------------------
        print("\n=== Step 2: Creating Node to Parent Mapping ===")
        node_parent_map = dict(zip(nodes_df["node_id"], nodes_df["parent_id"]))
        print(f"✅ Created mapping for {len(node_parent_map)} nodes")

        # --------------------------
        # Step 3: Filter invalid relations
        # --------------------------
        print("\n=== Step 3: Filtering Invalid Relations ===")
        valid_mask = (
                relations_df["src_node_id"].isin(node_parent_map) &
                relations_df["dst_node_id"].isin(node_parent_map)
        )
        valid_relations = relations_df[valid_mask].copy()
        filtered = len(relations_df) - len(valid_relations)
        print(f"✅ Valid relations kept: {len(valid_relations)} (filtered {filtered} invalid)")

        # --------------------------
        # Step 4: Build L2 relations
        # --------------------------
        print("\n=== Step 4: Building L2 Layer Relations ===")
        valid_relations["src_l2_node_id"] = valid_relations["src_node_id"].map(node_parent_map)
        valid_relations["dst_l2_node_id"] = valid_relations["dst_node_id"].map(node_parent_map)

        # Define output columns
        l2_columns = [
            "src_l2_node_id",
            "dst_l2_node_id",
            "relation_type",
            "src_node_id",
            "dst_node_id",
            "evidence_label",
            "case_title",
            "evidence_statement"
        ]

        l2_relations = valid_relations[l2_columns].copy()

        # Deduplicate
        before_dedup = len(l2_relations)
        l2_relations = l2_relations.drop_duplicates(
            subset=["src_l2_node_id", "dst_l2_node_id", "relation_type"],
            keep="first"
        )

        l2_relations = l2_relations.rename(columns={
            "src_node_id": "src_l1_node_id",
            "dst_node_id": "dst_l1_node_id",
        }).rename(columns={
            "src_l2_node_id": "src_node_id",
            "dst_l2_node_id": "dst_node_id",
        })
        print(f"✅ Deduplication: {before_dedup} → {len(l2_relations)} records")

        # --------------------------
        # Step 5: Save output
        # --------------------------
        print("\n=== Step 5: Saving L2 Relations File ===")
        l2_relations.to_csv(output_path, index=False)
        print(f"✅ L2 relations saved to: {os.path.abspath(output_path)}")

        # --------------------------
        # Step 6: Show statistics
        # --------------------------
        print("\n=== L2 Relations Statistics ===")
        print(f"Total L2 relations: {len(l2_relations)}")
        print("\nRelation type distribution:")
        print(l2_relations["relation_type"].value_counts())

    def create_sector_kg(self, clean_flag=False):

        path_dir = self.norm_nodes_path
        file_path = [
            's001_l1_nodes.csv',
            's001_l2_nodes.csv',
            's001_l12_relations.csv',
            's001_l2_relations.csv',
        ]
        create_kg_by_files(file_path, path_dir=path_dir, clean_flag=clean_flag)

    def complement_l1_relations(self):

        path_dir = self.sector_raw_path
        file_path = [
            's001_relations.csv',
        ]
        create_kg_by_files(file_path, path_dir=path_dir, clean_flag=False)



if __name__ == '__main__':
    obj = SectorKG()
    sector_ids = ['s001']
    case_ids = ['c001', 'c002', 'c003', 'c004', 'c005', 'c006']
    start = 1
    end = 3
    for turn in range(start, end + 1):
        if turn == 1:
            for sector_id in sector_ids:
                obj.concat_cases_by_sector(sector_id, case_ids)

        if turn == 2:
            for sector_id in sector_ids:
                obj.build_mid_nodes(sector_id)
                obj.build_l2_relations(sector_id)

        if turn == 3:
            for sector_id in sector_ids:
                obj.create_sector_kg(clean_flag=True)

        if turn == 4:
            for case_id in case_ids:
                obj.complement_l1_relations()