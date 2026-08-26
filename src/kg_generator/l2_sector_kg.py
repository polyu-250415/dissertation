import pandas as pd
import os

from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_files,clear_kg


class SectorKG:
    def __init__(self):
        self.rebuild_kg_path = "../data/graph/case_study/case_6_v_ds/"
        self.sector_raw_path = "../data/graph/case_study/sector_1_raw/"
        self.annotate_nodes_path = "../data/graph/case_study/sector_2_annotate_m/"
        self.norm_nodes_path = "../data/graph/case_study/sector_3_norm_nodes/"

        if not os.path.exists(self.sector_raw_path):
            os.makedirs(self.sector_raw_path, exist_ok=True)

        if not os.path.exists(self.norm_nodes_path):
            os.makedirs(self.norm_nodes_path, exist_ok=True)

        self.sic = {
            "s001":"SIC 15 - Construction (Building Construction—General Contractors And Operative Builders)",
            "s002":"SIC 80 - Services (Health Services)",
            "s003":"SIC 20-39 - Manufacturing"
        }

        self.category_file_flag = {
            "Explicit Knowledge":"ek",
            "Technology-enable Practice":"tp",
            "Knowledge Holder":"kh",
            "Knowledge Learner": "kl",
            "Limitation":"li",
            "Digital Technology":"dt",
            "Traditional Human-central Practice":"thp",
            "Tacit Knowledge":"tk",
            "Organizational Dependency":"od",
            "Environmental Dependency":"ed"
        }

    def concat_cases_by_sector(self, sector_id, case_ids):
        df_nodes = pd.DataFrame()
        df_edges = pd.DataFrame()
        for case_id in case_ids:
            try:
                node_file = self.rebuild_kg_path + f'{case_id}_nodes.csv'
                edge_file = self.rebuild_kg_path + f'{case_id}_edges.csv'
                df_nodes = pd.concat([df_nodes, pd.read_csv(node_file)])
                df_edges = pd.concat([df_edges, pd.read_csv(edge_file)])
            except Exception as e:
                print(e)
                pass

        df_nodes.to_csv(self.sector_raw_path + f'{sector_id}_nodes.csv', index=False)
        df_edges.to_csv(self.sector_raw_path + f'{sector_id}_edges.csv', index=False)

    def split_nodes_by_label(self, sector_id):

        input_file = self.sector_raw_path + f'{sector_id}_nodes.csv'
        df = pd.read_csv(input_file)
        for category, group in df.groupby("category", dropna=False):
            output_file = self.sector_raw_path + (f'{sector_id}/{sector_id}'
                                                  f'_{self.category_file_flag[category]}_nodes.csv')
            group.to_csv(output_file, index=False, encoding="utf-8")
            pd.DataFrame().to_csv(self.sector_raw_path + f'{sector_id}/{sector_id}'
                                                f'_{self.category_file_flag[category]}_nodes_annotation.csv',
                                  index=False,
                                  encoding="utf-8")

        print("Split completed successfully!")

    def combine_nodes_by_sector(self, sector_id):

        df_nodes = pd.read_csv(self.sector_raw_path + f'{sector_id}_nodes.csv')
        df_node_annotation = pd.DataFrame()
        for root, dirs, files in os.walk(self.annotate_nodes_path):
            for file in files:
                if (not file.startswith(sector_id)
                        or ("nodes" not in file)
                        or ("expand" not in file)):
                    continue

                file = os.path.join(root, file)
                df = pd.read_csv(file)
                df = df.astype(str)
                df_node_annotation = pd.concat([df_node_annotation, df])

        df_node_annotation.rename(columns={"sub_category_id":"raw_sub_category_id",
                           "sub_category":"raw_sub_category",
                           "adjust_sub_category_id":"sub_category_id",
                           "adjust_sub_category":"sub_category"}, inplace=True)

        df_nodes.to_csv(self.annotate_nodes_path + f'{sector_id}_node_annotation.csv', index=False)

        map_sub_id = df_node_annotation.set_index("node_id")["sub_category_id"]
        map_sub_name = df_node_annotation.set_index("node_id")["sub_category"]

        df_nodes["sub_category_id"] = df_nodes["node_id"].map(map_sub_id)
        df_nodes["sub_category"] = df_nodes["node_id"].map(map_sub_name)
        df_nodes.to_csv(self.annotate_nodes_path + f'{sector_id}_nodes.csv', index=False)


    def combine_normalized_splits(self, sector_ids):
        for sector_id in sector_ids:
            self.combine_nodes_by_sector(sector_id)

    @staticmethod
    def generate_mapping_dict():
        sheets = [
            "Tacit Knowledge",
            "Digital Technology",
            "Traditional Human-central Pract",
            "Environmental Dependency",
            "Organizational Dependency",
            "Limitation",
            "Knowledge Holder",
            "Knowledge Learner",
            "Explicit Knowledge",
            "Technology-enable Practice"
        ]

        result = {}

        for sheet in sheets:
            try:
                df = pd.read_excel("../conf/coding_schema/coding_schema.xlsx", sheet_name=sheet)
                # 确保列名存在（可根据实际列名调整）
                if "Name" in df.columns and "Scope" in df.columns:
                    # 以 ID 为 key，Name 为 value；若 ID 重复则保留最后一个
                    result.update(dict(zip(df["Name"], df["Scope"])))
            except Exception as e:
                print(e)

        return result

    def build_mid_nodes(self, sector_id):
        src_file = self.annotate_nodes_path + f'{sector_id}_nodes.csv'
        mid_l1_node_file = self.norm_nodes_path + f'{sector_id}_l1_nodes.csv'
        mid_l2_node_file = self.norm_nodes_path + f'{sector_id}_l2_nodes.csv'
        mid_relation_file = self.norm_nodes_path + f'{sector_id}_l12_edges.csv'

        # Step 1: Read original CSV file
        print("Reading original CSV file...")
        df_original = pd.read_csv(src_file)
        print(f"Successfully loaded data: {len(df_original)} records")

        # Step 2: Process Layer 1 Knowledge Graph Nodes
        print("\nProcessing Layer 1 Knowledge Graph Nodes...")
        # Add s001M02 prefix to sub_category_id
        df_original['prefixed_subcat_id'] = f'{sector_id}M01' + df_original['sub_category_id']

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

        # Generate Layer 2 DataFrame (Group by prefixed_subcat_id)
        layer2_df = df_original.groupby('prefixed_subcat_id').agg(
            node_id=('prefixed_subcat_id', 'first'),
            node_name=('sub_category', 'first'),
            category=('category', 'first'),
            evidence_label=('evidence_label', 'first'),
            case_title=('case_title', 'first'),
            evidence_count=('evidence_statement', lambda x: int(x.dropna().nunique() or 0)),
            evidence_statement=('evidence_statement', lambda series:
            '\n'.join(
                f"{nid} | {name}: {stmt}"
                for nid, name, stmt in zip(
                    df_original.loc[series.index, 'node_id'],
                    df_original.loc[series.index, 'node_name'],
                    series.dropna().astype(str)
                )
            ))
        ).reset_index(drop=True)

        # Set fixed values
        layer2_df['evidence_label'] = 'G'
        layer2_df['case_title'] = self.sic[sector_id]

        # Deduplicate
        layer2_df = layer2_df.drop_duplicates(subset='node_id')
        print(f"Layer 2 nodes generated: {len(layer2_df)} nodes")

        mapping_dict=self.generate_mapping_dict()
        layer2_df["definition"] = layer2_df["node_name"].map(mapping_dict).fillna("")

        # Step 4: Create Child-Parent Relationships
        print("\nCreating child-parent relationships...")
        relationship_df = layer1_df[['node_id', 'parent_id']].copy()
        relationship_df['relation_type'] = 'is an instance of'
        relationship_df['evidence_label'] = 'G'
        relationship_df['case_title'] = self.sic[sector_id]
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

    def build_l2_edges(self, sector_id):
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
        relations_input_path = self.sector_raw_path + f'{sector_id}_edges.csv'
        nodes_input_path = self.norm_nodes_path + f'{sector_id}_l1_nodes.csv'
        output_path: str = self.norm_nodes_path + f'{sector_id}_l2_edges.csv'

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
        valid_edges = relations_df[valid_mask].copy()
        filtered = len(relations_df) - len(valid_edges)
        print(f"✅ Valid relations kept: {len(valid_edges)} (filtered {filtered} invalid)")

        # --------------------------
        # Step 4: Build L2 relations
        # --------------------------
        print("\n=== Step 4: Building L2 Layer Relations ===")
        valid_edges["src_l2_node_id"] = valid_edges["src_node_id"].map(node_parent_map)
        valid_edges["dst_l2_node_id"] = valid_edges["dst_node_id"].map(node_parent_map)

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

        l2_edges = valid_edges[l2_columns].copy()

        # Deduplicate
        before_dedup = len(l2_edges)

        group_keys = ["src_l2_node_id", "dst_l2_node_id", "relation_type"]

        # 方案A：evidence 保存为列表
        l2_edges = l2_edges.groupby(group_keys).agg(
            src_l2_node_id=('src_l2_node_id', 'first'),
            dst_l2_node_id=('dst_l2_node_id', 'first'),
            relation_type=('relation_type', 'first'),
            evidence_count=('evidence_statement', lambda x: int(x.dropna().nunique() or 0)),
            evidence_statement=('evidence_statement', lambda series:
            '\n'.join(
                f"{src_node_id} - {relation_type}: {stmt}"
                for src_node_id, relation_type, stmt in zip(
                    l2_edges.loc[series.index, 'src_node_id'],
                    l2_edges.loc[series.index, 'dst_node_id'],
                    series.dropna().astype(str)
                )
            )))

        l2_edges["case_title"] = self.sic[sector_id]
        l2_edges["evidence_label"] = 'Aggregation'
        l2_edges = l2_edges[l2_edges['src_l2_node_id'] != l2_edges['dst_l2_node_id']]

        l2_edges = l2_edges.rename(columns={
            "src_l2_node_id": "src_node_id",
            "dst_l2_node_id": "dst_node_id",
        })

        print(f"✅ Deduplication: {before_dedup} → {len(l2_edges)} records")

        # --------------------------
        # Step 5: Save output
        # --------------------------
        print("\n=== Step 5: Saving L2 Relations File ===")
        l2_edges.to_csv(output_path, index=False)
        print(f"✅ L2 relations saved to: {os.path.abspath(output_path)}")

        # --------------------------
        # Step 6: Show statistics
        # --------------------------
        print("\n=== L2 Relations Statistics ===")
        print(f"Total L2 relations: {len(l2_edges)}")
        print("\nRelation type distribution:")
        print(l2_edges["relation_type"].value_counts())

    def create_sector_kg(self, clean_flag=False, excluded_properties=[]):

        path_dir = self.norm_nodes_path
        file_path = [
            f'{sector_id}_l2_nodes.csv',
            f'{sector_id}_l2_edges.csv',
        ]
        create_kg_by_files(file_path, path_dir=path_dir, clean_flag=clean_flag, excluded_properties=excluded_properties)

    def complement_l1_edges(self, sector_id):

        path_dir = self.norm_nodes_path
        file_path = [
            f'{sector_id}_l1_nodes.csv',
            f'{sector_id}_l12_edges.csv',
        ]
        create_kg_by_files(file_path, path_dir=path_dir, clean_flag=False)

        path_dir = self.sector_raw_path
        file_path = [
            f'{sector_id}_edges.csv',
        ]
        create_kg_by_files(file_path, path_dir=path_dir, clean_flag=False)


if __name__ == '__main__':

    case_ids = {
        "s001": ['c001','c002','c003','c004','c005','c006','c007','c008','c009','c010','c011','c012','c013','c014','c015','c016','c017'],
        "s002": ['c101', 'c102', 'c103', 'c104', 'c105', 'c106', 'c107', 'c108', 'c109','c110','c111', 'c112', 'c113', 'c114', 'c115', 'c116', 'c117', 'c118', 'c119','c120','c121', 'c122', 'c123', 'c124', 'c125', 'c126'],
        "s003": ['c201', 'c202', 'c203', 'c204', 'c205', 'c206', 'c207', 'c208', 'c209', 'c210', 'c211','c212','c213', 'c214', 'c215', 'c216', 'c217', 'c218', 'c219', 'c220', 'c221','c222','c223', 'c224', 'c225', 'c226', 'c227']
    }

    obj = SectorKG()
    sector_ids = ['s001','s002','s003']

    start = 2
    end = 3
    for turn in range(start, end + 1):
        if turn == 1:
            for sector_id in sector_ids:
                obj.concat_cases_by_sector(sector_id, case_ids[sector_id])
                obj.split_nodes_by_label(sector_id)

        if turn == 2:
            for sector_id in sector_ids:
                obj.combine_normalized_splits(sector_ids)
                obj.build_mid_nodes(sector_id)
                obj.build_l2_edges(sector_id)

        if turn == 3:
            clear_kg()

            for sector_id in sector_ids:
                excluded_properties = ['case_title',
                                       'evidence_location',
                                       'evidence_label',
                                       'object_definition']
                obj.create_sector_kg(clean_flag=False, excluded_properties=excluded_properties)

        if turn == 4:
            for sector_id in sector_ids:
                obj.complement_l1_edges(sector_id)