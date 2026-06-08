import pandas as pd
import os


case_ids = {
        "s001": ['c001', 'c002', 'c003', 'c004', 'c005', 'c006', 'c007'],
        "s002": ['c101', 'c102', 'c103', 'c104', 'c105', 'c106', 'c107', 'c108', 'c109'],
        "s003": ['c201', 'c202', 'c203', 'c204', 'c205', 'c206', 'c207', 'c208', 'c209', 'c210', 'c211'],
    }

def calculate_dtv(file_path):
    valid_num = 0
    total_num = 0
    try:
        df = pd.read_csv(file_path)
        total_num = len(df)
        for _, row in df.iterrows():
            if 'Not Mention' in row["Answer"] or 'Exception' == row["Answer"]:
                continue
            valid_num = valid_num + 1
    except Exception as e:
        print(e)

    if total_num:
        return valid_num / total_num
    else:
        return 0


def calculate_kg_verification(sector_ids):
    for sector_id in sector_ids:
        print(f" ------------{sector_id}----------------\n")

        stat_dict_list = []
        for case_id in case_ids[sector_id]:

            print(f" ------------{case_id}----------------\n")

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

                stat_dict['dtv_valid'] = round(calculate_dtv(case_ea_alignment + case_id + '_ds_rag.csv'),2)

                stat_dict_list.append(stat_dict)
            except Exception as e:
                print(e)
                pass

        pd.DataFrame(stat_dict_list).to_csv(f"../data/graph/case_study/case_7_stat/{sector_id}_stat.csv", index=False)

def calc_ds_coverage(sector_ids, row_num=31):

    df_question = pd.read_excel("../conf/coding_schema/coding_schema.xlsx", sheet_name="downstream_task").dropna(how="all")
    for sector_id in sector_ids:

        for case_id in case_ids[sector_id]:
            file_path = f"../data/graph/case_study/case_6_v_ds/{case_id}_ds_rag.csv"
            values = [0 for i in range(row_num)]
            try:
                df = pd.read_csv(file_path)
                if df.shape[0] != row_num:
                    print(f"{file_path} line no. {df.shape[0]}, drop")
                    continue

                for index, row in df.iterrows():
                    if 'Not Mention' in row["Answer"] or 'Exception' == row["Answer"]:
                        continue
                    values[index] = 1

            except Exception as e:
                print(f"Read {file_path} failed: {str(e)}")
                continue

            df_question[case_id] = values

    df_question.to_csv(f"../data/graph/case_study/case_7_stat/coverage_stat.csv", index=False)


if __name__ == '__main__':
    sector_ids = ["s001","s002","s003"]
    calculate_kg_verification(sector_ids)
    calc_ds_coverage(sector_ids)