import os
import pandas as pd
from src.Dissertation.graphy_tools.create_paper_graph_by_id import create_paper_graph

class GraphBuilder:
    def __init__(self):
        self.graph_data_path = "../data/graph/case study/cases/"
        self.graph_build_dir = "../data/papers/midput/building_graph_t1/"
        pass

    def build_node_set(self):

        df_node_combine = pd.DataFrame()
        df_relation_combine = pd.DataFrame()

        for file in os.listdir(self.graph_data_path):
            if file.endswith("nodes.csv"):

                df_node = pd.read_csv(os.path.join(self.graph_data_path, file))
                df_node_combine = pd.concat([df_node_combine, df_node], axis=0, ignore_index=True)

            if file.endswith("relations.csv"):
                df_relation = pd.read_csv(os.path.join(self.graph_data_path, file))
                df_relation_combine = pd.concat([df_relation_combine, df_relation], axis=0, ignore_index=True)

        df_node_combine.to_csv(os.path.join(self.graph_build_dir, "nodes.csv"), index=False)
        df_relation_combine.to_csv(os.path.join(self.graph_build_dir, "relations.csv"), index=False)


    def build_middle_layer(self):
        df_map = pd.read_csv(f"{self.graph_build_dir}nodes_midlayer_mapping.csv")
        df_nodes = pd.read_csv(f"{self.graph_build_dir}nodes.csv")
        df_relations = pd.read_csv(f"{self.graph_build_dir}relations.csv")

        # 1. 取出唯一的中层概念（去重）
        unique_concepts = df_map['mid_layer_concept'].drop_duplicates().reset_index(drop=True)
        # 2. 给唯一概念分配编号 m001, m002, m003...
        concept_map = {concept: f'm{i + 1:03d}' for i, concept in enumerate(unique_concepts)}
        # 3. 把编号回填到 df_map（重复概念自动用同一个编号）
        df_map['node_id'] = df_map['mid_layer_concept'].map(concept_map)

        df_nodes.rename(columns={'id': 'old_id', 'name': 'old_name'}, inplace=True)
        df_nodes['id'] = df_map['node_id']
        df_nodes['name'] = df_map['mid_layer_concept']

        # 聚合：按 id + name + category + labels 分组，old id 用 ; 拼接
        df_node_unique = df_nodes.groupby(['id', 'name', 'category', 'labels'], as_index=False)['old_id'].agg(
            lambda x: ';'.join(x.astype(str).unique())  # 去重 + 分号拼接
        )

        df_node_unique['case_id'] = df_node_unique['old_id']

        # 1. 按 id 去重（保留第一次出现的行，其余重复删除）
        df_node_unique = df_node_unique.drop_duplicates(subset=['id'], keep='first')
        # 2. 删除 old_id 列
        df_node_unique = df_node_unique.drop(columns=['old_id'])
        df_node_unique.to_csv(f"{self.graph_build_dir}concept_nodes.csv", index=False)

        node_dict = dict(zip(df_map['id'], df_map['node_id']))
        df_relations['start_id'] = df_relations['start_id'].map(node_dict)
        df_relations['end_id'] = df_relations['end_id'].map(node_dict)

        df_relations.to_csv(f"{self.graph_build_dir}concept_relations.csv", index=False)


    def build_graph_by_key(self, key, path_dir):
        create_paper_graph(key,path_dir=path_dir)

if __name__ == '__main__':
    graph = GraphBuilder()
    path_dir = "../data/papers/midput/building_graph_t1/cases"
    graph.build_graph_by_key("concept",path_dir)
