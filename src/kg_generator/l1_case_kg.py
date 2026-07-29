from src.kg_verificator.v_case_kg.s0_verify_structure import VerifySchema
from src.kg_verificator.v_case_kg.s1_assemble_factcheck_vq import AssembleVQ
from src.kg_verificator.v_case_kg.s1_evaluate_factcheck_vq import EvaluateVQ
from src.kg_verificator.v_case_kg.s1_rebuild_kg import AlignRwN
from src.kg_verificator.v_case_kg.s2_assemble_ea_vq import AssembleEAVQ
from src.kg_verificator.v_case_kg.s2_evaluate_ea import EvaluateEA
from src.kg_verificator.v_case_kg.s2_rebuild_kg import RebuildKG
from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_case
from src.kg_generator.l1_case_measure import calculate_kg_verification

from src.kg_generator.l0_preparing import (transfer_nodes, transfer_edges, combine_data, delete_isolated_nodes)


class CaseKG:
    def __init__(self):
        self.rebuild_kg_path = "../data/graph/case_study/case_6_v_ds/"

    def build_case_kg(self,case_id, clear_flag=False):
        create_kg_by_case(case_id, path_dir=self.rebuild_kg_path, clear_flag=clear_flag)

    @staticmethod
    def build_case_kg_test(case_id, path, mid_seg, clear_flag=False):
        create_kg_by_case(case_id, path_dir=path, mid_seg=mid_seg, clear_flag=clear_flag)


if __name__ == '__main__':

    start = 3
    end = 3
    obj = CaseKG()

    sector_id = 's002'

    case_ids = {
        "s001": ['c001', 'c002', 'c003', 'c004', 'c005', 'c006', 'c007'],
        "s002": ['c101', 'c102', 'c103', 'c104', 'c105', 'c106', 'c107', 'c108', 'c109'],
        "s003": ['c201', 'c202', 'c203', 'c204', 'c205', 'c206', 'c207', 'c208', 'c209', 'c210', 'c211'],
    }

    for turn in range(start,end + 1):
        if turn == 1:
            transfer_nodes(case_ids[sector_id])
            transfer_edges(case_ids[sector_id])
            combine_data(case_ids[sector_id])
            delete_isolated_nodes(case_ids[sector_id])

            vs = VerifySchema(data_base_path="../data/graph/case_study/")
            vs.validate_schema(case_ids[sector_id])

        if turn ==2:
            vq = AssembleVQ(data_base_path="../data/graph/case_study/")
            vq.assemble_entity_vq(case_ids[sector_id])
            vq.assemble_relation_vq(case_ids[sector_id])

            obj = EvaluateVQ(data_base_path="../data/graph/case_study/")
            obj.evaluate_all_vq(case_ids[sector_id])

            obj = AlignRwN(data_base_path="../data/graph/case_study/")
            obj.screen_nodes(case_ids[sector_id])

        if turn == 3:
            obj = AssembleEAVQ(data_base_path="../data/graph/case_study/")
            obj.init_embedder()
            obj.find_best_pairs(case_ids[sector_id])
            obj.assemble_ea_vq(case_ids[sector_id])

        if turn == 4:
            obj = EvaluateEA(data_base_path="../data/graph/case_study/")
            obj.evaluate_all_ea(case_ids[sector_id])
            obj.find_all_redundant_nodes(case_ids[sector_id])

            obj = RebuildKG(data_base_path="../data/graph/case_study/")
            obj.rebuild_all_kg(case_ids[sector_id])

        if turn == 5:
            obj = CaseKG()
            for case_id in case_ids[sector_id]:
                obj.build_case_kg(case_id)

        if turn == 6:
            calculate_kg_verification([sector_id])