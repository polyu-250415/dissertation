import pandas as pd
import os


case_ids = {
        "s001": ['c001', 'c002', 'c003', 'c004', 'c005', 'c006', 'c007'],
        "s002": ['c101', 'c102', 'c103', 'c104', 'c105', 'c106', 'c107', 'c108', 'c109'],
        "s003": ['c201', 'c202', 'c203', 'c204', 'c205', 'c206', 'c207', 'c208', 'c209', 'c210', 'c211'],
    }

def calculate_kg_verification(sector_ids):
    for sector_id in sector_ids:
        print(f" ------------{sector_id}----------------\n")

        stat_dict_list = []
        for case_id in case_ids[sector_id]:

            try:
                stat_dict = {'case_id': case_id}

                initial_case_kg = "../data/graph/case_study/case_1_raw_kg_m/"
                try:
                    stat_dict['Initial_deepseek_nodes'] = len(pd.read_csv(initial_case_kg + case_id + '_deepseek_nodes.csv'))
                    stat_dict['Initial_deepseek_relations'] = len(pd.read_csv(initial_case_kg + case_id + '_deepseek_relations.csv'))
                except Exception as e:
                    stat_dict['Initial_deepseek_nodes'] = 0
                    stat_dict['Initial_deepseek_relations'] = 0
                    print(e)

                try:
                    stat_dict['Initial_gemini_nodes'] = len(pd.read_csv(initial_case_kg + case_id + '_gemini_nodes.csv'))
                    stat_dict['Initial_gemini_relations'] = len( pd.read_csv(initial_case_kg + case_id + '_gemini_relations.csv'))
                except Exception as e:
                    stat_dict['Initial_gemini_nodes'] = 0
                    stat_dict['Initial_gemini_relations'] = 0
                    print(e)

                case_schema_check = "../data/graph/case_study/case_4_v_kg/"
                stat_dict['r1_nodes'] = len(pd.read_csv(case_schema_check + case_id + '_nodes.csv'))
                stat_dict['r1_relations'] = len(pd.read_csv(case_schema_check + case_id + '_relations.csv'))

                case_fact_check = "../data/graph/case_study/case_5_v_ea/"
                stat_dict['r2_nodes'] = len(pd.read_csv(case_fact_check + case_id + '_nodes.csv'))
                stat_dict['r2_relations'] = len(pd.read_csv(case_fact_check + case_id + '_relations.csv'))

                case_ea_alignment = "../data/graph/case_study/case_6_v_ds/"
                stat_dict['r3_nodes'] = len(pd.read_csv(case_ea_alignment + case_id + '_nodes.csv'))
                stat_dict['r3_relations'] = len(pd.read_csv(case_ea_alignment + case_id + '_relations.csv'))

                stat_dict['node_accepted_rate'] = round(stat_dict['r3_nodes'] / (stat_dict['Initial_gemini_nodes'] +
                                                                                 stat_dict[
                                                                                     'Initial_deepseek_nodes']), 2)
                stat_dict['relation_accepted_rate'] = round(stat_dict['r3_relations'] / (
                            stat_dict['Initial_deepseek_relations'] + stat_dict['Initial_gemini_relations']),2)

                stat_dict_list.append(stat_dict)
            except Exception as e:
                print(e)
                pass

        pd.DataFrame(stat_dict_list).to_csv(f"../data/graph/case_study/case_8_stat/{sector_id}_stat.csv", index=False)


if __name__ == '__main__':
    calculate_kg_verification(["s001","s002","s003"])