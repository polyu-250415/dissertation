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
            edge_file = self.sector_norm_path + f'{sector_id}_l2_relations.csv'
            df_nodes = pd.concat([df_nodes, pd.read_csv(node_file)])
            df_edges = pd.concat([df_edges, pd.read_csv(edge_file)])

        df_nodes.to_csv(self.cross_sector_raw_path + f'cross_sector_nodes.csv', index=False)
        df_edges.to_csv(self.cross_sector_raw_path + f'cross_sector_relations.csv', index=False)

    def create_sector_kg(self, clean_flag=False):

        path_dir = self.cross_sector_raw_path
        file_path = [
            f'cross_sector_nodes.csv',
            f'cross_sector_relations.csv',
        ]
        create_kg_by_files(file_path, path_dir=path_dir, clean_flag=clean_flag)

if __name__ == '__main__':
    obj = CrossSectorKg()
    sector_ids = ['s003']
    obj.concat_cases_by_sector(sector_ids)

    obj.create_sector_kg(clean_flag=True)