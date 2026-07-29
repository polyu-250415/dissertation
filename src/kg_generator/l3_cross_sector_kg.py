import pandas as pd
import os

from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_files

class CrossSectorKg:

    def __init__(self):
        self.sector_norm_path = "../data/graph/case_study/sector_3_norm_nodes/"
        self.cross_sector_raw_path = "../data/graph/case_study/cross_sector_raw_m/"

        if not os.path.exists(self.cross_sector_raw_path):
            os.makedirs(self.cross_sector_raw_path, exist_ok=True)

        self.sic = {
            "s001": "SIC 15 - Construction (Building Construction—General Contractors And Operative Builders)",
            "s002": "SIC 80 - Services (Health Services)",
            "s003": "SIC 20-39 - Manufacturing"
        }

    def concat_cases_by_sector(self, sector_ids):
        df_nodes = pd.DataFrame()
        df_edges = pd.DataFrame()
        for sector_id in sector_ids:
            node_file = self.sector_norm_path + f'{sector_id}_l2_nodes.csv'
            edge_file = self.sector_norm_path + f'{sector_id}_l2_edges.csv'
            df_nodes = pd.concat([df_nodes, pd.read_csv(node_file)])
            df_edges = pd.concat([df_edges, pd.read_csv(edge_file)])

        df_nodes.to_csv(self.cross_sector_raw_path + f'cross_sector_nodes.csv', index=False)
        df_edges.to_csv(self.cross_sector_raw_path + f'cross_sector_edges.csv', index=False)

    def create_sector_kg(self, clean_flag=False):

        path_dir = self.cross_sector_raw_path
        file_path = [
            f'cross_sector_nodes.csv',
            f'cross_sector_edges.csv',
            f'h001_nodes.csv',
            f'h001_edges.csv',
            f'h001_l_edges.csv',
        ]
        create_kg_by_files(file_path, path_dir=path_dir, clean_flag=clean_flag)

    @staticmethod
    def excel_sheets_to_dict(sheet_name_list, prefix = 'h001M02'):
        template_path = '../conf/coding_schema/coding_schema.xlsx'
        map_dict = {}
        for sheet_name in sheet_name_list:
            try:
                df = pd.read_excel(template_path, sheet_name=sheet_name).dropna(how="all")
                df['ID'] = prefix + df['ID']
                tmp_dic = dict(zip(df['ID'], df['Scope']))
                map_dict = map_dict | tmp_dic
            except Exception as e:
                print(e)
                pass

        return map_dict


    def build_h001_kg(self):

        df = pd.read_csv(self.cross_sector_raw_path + 'cross_sector_nodes.csv')
        df_sector_edges = pd.read_csv(self.cross_sector_raw_path + 'cross_sector_edges.csv')
        df_nodes = df.copy()
        df_nodes['child_id'] = df['node_id']
        df_nodes['node_id'] = df['node_id'].apply(lambda x: 'h001' + x[4:] if len(x) >= 4 else x)

        df_nodes['node_name'] = df['node_name'].astype(str) + ' Set'

        node_map = dict(zip(df_nodes['child_id'], df_nodes['node_id']))

        df_l_edges = pd.DataFrame()
        df_l_edges['src_node_id'] = df_nodes['child_id'].astype(str)
        df_l_edges['dst_node_id'] = df_nodes['node_id'].astype(str)
        df_l_edges['relation_type'] = 'is_an_instance_of'
        df_l_edges['evidence_label'] = 'G'
        df_l_edges['case_title'] = "HOO1:Hard Aggregation"

        df['category'] = df_nodes['node_id']

        df_nodes_agg = df_nodes.groupby('node_id').agg(
            total_evidence_count=('evidence_count', 'sum'),
            node_name=('node_name', 'first'),  # 取组内第一个值（假设相同）
            category=('category', 'first'),
        ).reset_index()

        df_nodes_agg.drop_duplicates(subset='node_id', inplace=True)
        df_nodes_agg['evidence_label'] = 'G'
        df_nodes_agg['case_title'] = 'HOO1:Hard Aggregation'


        sheet_name_list = df_nodes_agg['category'].unique().tolist()
        evidence_map = self.excel_sheets_to_dict(sheet_name_list)
        df_nodes_agg['Description'] = df_nodes_agg['node_id'].map(evidence_map)

        df_nodes_agg.to_csv(self.cross_sector_raw_path + 'h001_nodes.csv', index=False)
        df_l_edges.to_csv(self.cross_sector_raw_path + 'h001_l_edges.csv', index=False)
        df.to_csv(self.cross_sector_raw_path + 'cross_sector_nodes.csv', index=False)

        df_edges = df_sector_edges.copy()
        df_edges['child_src_id'] = df_sector_edges['src_node_id'].astype(str)
        df_edges['child_dst_id'] = df_sector_edges['dst_node_id'].astype(str)
        df_edges['src_node_id'] = df_sector_edges['src_node_id'].map(node_map)
        df_edges['dst_node_id'] = df_sector_edges['dst_node_id'].map(node_map)

        df_edges = df_edges.drop_duplicates(['src_node_id', 'dst_node_id'])

        df_edges.to_csv(self.cross_sector_raw_path + 'h001_edges.csv', index=False)




if __name__ == '__main__':
    obj = CrossSectorKg()
    sector_ids = ['s001','s002','s003']
    obj.concat_cases_by_sector(sector_ids)

    obj.build_h001_kg()

    obj.create_sector_kg(clean_flag=True)