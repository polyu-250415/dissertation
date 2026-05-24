import pandas as pd


class SectorKG:
    def __init__(self):
        self.rebuild_kg_path = "../data/graph/case_study/case_6_rebuild_kg/"
        self.unite_sector_path = "../data/graph/case_study/sector_1_unite/"
        pass

    def concat_cases_by_sector(self, call_ids):
        df_nodes = pd.DataFrame()
        df_edges = pd.DataFrame()
        for call_id in call_ids:
            node_file = self.rebuild_kg_path + f'{call_id}_nodes.csv'
            edge_file = self.rebuild_kg_path + f'{call_id}_relations.csv'
            df_nodes = pd.concat([df_nodes, pd.read_csv(node_file)])
            df_edges = pd.concat([df_edges, pd.read_csv(edge_file)])

        df_nodes.to_csv(self.unite_sector_path + 'nodes.csv', index=False)
        df_edges.to_csv(self.unite_sector_path + 'relations.csv', index=False)

    def build_mid_layer(self):
        pass


if __name__ == '__main__':
    obj = SectorKG()
    call_ids = ['c001', 'c002', 'c003', 'c004', 'c005', 'c006']
    obj.concat_cases_by_sector(call_ids)