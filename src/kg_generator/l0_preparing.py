import os
import pandas as pd
from src.utils.op_files import clear_directory

data_path = "../data/graph/case_study/case_1_raw_kg_m/"
norm_path = os.path.abspath('../data/graph/case_study/') + '/case_2_norm_id/'
combination_path = os.path.abspath('../data/graph/case_study/') + '/case_3_unite/'


def get_models():
    return ['gemini', 'deepseek']

def get_model_flag(model):
    if "deepseek" == model:
        return "M02"
    elif "gemini" == model:
        return "M01"
    else:
        return "M00"

def transfer_nodes(case_ids):

    df_map = pd.read_csv('../conf/case_id_map')
    map_dict = dict(zip(df_map['node_id_prex'], df_map['case_title']))

    for case_id in case_ids:
        for model in get_models():
            file = f'{data_path}{case_id}_{model}_nodes.csv'
            output_file_name = f'{norm_path}{case_id}_{model}_nodes.csv'
            print(f"Processing {file}")
            try:
                if not file.endswith("nodes.csv"):
                    continue

                model_flag = get_model_flag(model)
                df = pd.read_csv(file)
                df = df.astype(str)
                df['node_id'] = case_id + model_flag + df['node_id']
                df['case_title'] = map_dict[case_id]

                df.to_csv(output_file_name, index=False)
            except Exception as e:
                print(e)


def transfer_relations(case_ids):
    df_map = pd.read_csv('../conf/case_id_map')
    map_dict = dict(zip(df_map['node_id_prex'], df_map['case_title']))

    for case_id in case_ids:
        for model in get_models():
            file = f'{data_path}{case_id}_{model}_relations.csv'
            output_file_name = f'{norm_path}{case_id}_{model}_relations.csv'
            print(f"Processing {file}")

            try:
                print(f"Processing {file}")

                model_flag = get_model_flag(model)

                df = pd.read_csv(file)
                df['case_title'] = map_dict[case_id]
                df = df.astype(str)
                df['src_node_id'] = case_id + model_flag + df['src_node_id']
                df['dst_node_id'] = case_id + model_flag + df['dst_node_id']

                df.to_csv(output_file_name, index=False)
            except Exception as e:
                print(e)

def delete_isolated_nodes(case_ids):
    
    for case_id in case_ids:
        node_path= f'{combination_path}{case_id}_nodes.csv'
        relation_path = f'{combination_path}{case_id}_relations.csv'
        df_nodes = pd.read_csv(node_path)
        df_relations = pd.read_csv(relation_path)
    
        # Collect all node IDs that appear in relationships
        used_node_ids = set(df_relations["src_node_id"]).union(set(df_relations["dst_node_id"]))
    
        # Filter out isolated nodes with no relationships
        df_nodes_accepted = df_nodes[df_nodes["node_id"].isin(used_node_ids)]
        df_nodes_deleted = df_nodes[~df_nodes["node_id"].isin(used_node_ids)]
    
        # Save filtered result (overwrite original file)
        df_nodes_accepted.to_csv(node_path, index=False)

        # Use the line below if you want to save as a new file instead
        df_nodes_deleted.to_csv(node_path.replace("nodes", "nodes_island_deleted"), index=False)
    
        print(f"Original node count: {len(df_nodes)}")
        print(f"Filtered node count: {len(df_nodes_accepted)}")
        print(f"Deleted node count: {len(df_nodes_deleted)}")
        print(f"Success: {case_id} Isolated nodes with no relationships have been removed.")


def combine_data(case_ids, clear_flag = False):
    if clear_flag:
        clear_directory(combination_path)

    for case_id in case_ids:
        # 存储所有要合并的 DataFrame
        df_list = []
        # 读取 gemini 文件（修复了读错文件的bug）
        gemini_file = f'{norm_path}{case_id}_gemini_nodes.csv'
        if os.path.exists(gemini_file):
            df = pd.read_csv(gemini_file)
            df_list.append(df)

        # 读取 deepseek 文件
        deepseek_file = f'{norm_path}{case_id}_deepseek_nodes.csv'
        if os.path.exists(deepseek_file):
            df = pd.read_csv(deepseek_file)
            df_list.append(df)

        # 只有有数据时才合并并保存
        if df_list:
            df_nodes = pd.concat(df_list, ignore_index=True)  # 正确合并
            df_nodes.to_csv(f'{combination_path}{case_id}_nodes.csv', index=False)

        df_relation_list = []
        # 读取 gemini 文件（修复了读错文件的bug）
        gemini_file = f'{norm_path}{case_id}_gemini_relations.csv'
        if os.path.exists(gemini_file):
            df = pd.read_csv(gemini_file)
            df_relation_list.append(df)

        # 读取 deepseek 文件
        deepseek_file = f'{norm_path}{case_id}_deepseek_relations.csv'
        if os.path.exists(deepseek_file):
            df = pd.read_csv(deepseek_file)
            df_relation_list.append(df)

        # 只有有数据时才合并并保存
        if df_relation_list:
            df_relations = pd.concat(df_relation_list, ignore_index=True)  # 正确合并
            df_relations.to_csv(f'{combination_path}{case_id}_relations.csv', index=False)

if __name__ == '__main__':

    # clear_directory(norm_path)

    case_ids = ['c103', 'c104', 'c105', 'c106', 'c107', 'c108', 'c109', 'c201', 'c202', 'c203', 'c204','c205',
                'c206','c207','c208','c209','c210','c211']
    transfer_nodes(case_ids)
    transfer_relations(case_ids)
    combine_data(case_ids)
    delete_isolated_nodes(case_ids)