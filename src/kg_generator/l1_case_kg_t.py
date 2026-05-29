from src.kg_verificator.v_case_kg.s0_verify_structure import VerifySchema
from src.kg_verificator.v_case_kg.s1_assemble_factcheck_vq import AssembleVQ
from src.kg_verificator.v_case_kg.s1_evaluate_factcheck_vq import EvaluateVQ
from src.kg_verificator.v_case_kg.s1_rebuild_kg import AlignRwN
from src.kg_verificator.v_case_kg.s2_assemble_ea_vq import AssembleEAVQ
from src.kg_verificator.v_case_kg.s2_evaluate_ea import EvaluateEA
from src.kg_verificator.v_case_kg.s2_rebuild_kg import RebuildKG
from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_case


class CaseKG:
    def __init__(self):
        self.rebuild_kg_path = "../data/graph/case_study/case_6_rebuild_kg/"

    def build_case_kg(self,case_id, clear_flag=False):
        create_kg_by_case(case_id, path_dir=self.rebuild_kg_path, clear_flag=clear_flag)

    @staticmethod
    def build_case_kg_test(case_id, path, mid_seg, clear_flag=False):
        create_kg_by_case(case_id, path_dir=path, mid_seg=mid_seg, clear_flag=clear_flag)


if __name__ == '__main__':

    obj = CaseKG()
    path = "../data/graph/case_study/case_6_rebuild_kg/"
    mid_seg = '_gemini'
    #mid_seg = '_deepseek'
    obj.build_case_kg_test("c101", path, "", clear_flag=True)
