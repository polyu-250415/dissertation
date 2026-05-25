import pandas as pd
import os

from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_case


class CaseKG:
    def __init__(self):
        self.rebuild_kg_path = "../data/graph/case_study/case_6_rebuild_kg/"

    def build_case_kg(self,case_id, mid_seg=''):
        create_kg_by_case(case_id, path_dir=self.rebuild_kg_path, mid_seg=mid_seg)


if __name__ == '__main__':
    obj = CaseKG()
    obj.build_case_kg("c002", mid_seg='')