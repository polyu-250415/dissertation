
from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_case


class CaseKG:
    def __init__(self):
        self.rebuild_kg_path = "../data/graph/case_study/case_6_v_ds/"

    def build_case_kg(self,case_id, clear_flag=False):
        create_kg_by_case(case_id, path_dir=self.rebuild_kg_path, clear_flag=clear_flag)

    @staticmethod
    def build_case_kg_test(case_id, path, mid_seg, clear_flag=False):
        create_kg_by_case(case_id, path_dir=path, mid_seg=mid_seg, clear_flag=clear_flag)


if __name__ == '__main__':

    obj = CaseKG()
    path = "../data/graph/case_study/case_6_v_ds/"
    mid_seg = '_gemini'
    #mid_seg = '_deepseek'
    for id in range(1, 2):
        obj.build_case_kg_test(f"c00{id}", path, "", clear_flag=True)
