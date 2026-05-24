import os
import pandas as pd
from dashscope.tokenizers.tokenizer import current_path

norm_path = os.path.abspath('./') + '/case_2_norm_id/'
combination_path = os.path.abspath('./') + '/case_3_unite/'

def get_model_flag(file_name):
    if "deepseek" in file_name:
        return "M01"
    elif "gemini" in file_name:
        return "M02"
    else:
        return "M00"

def transfer_nodes():

    df_map = pd.read_csv('../../../conf/case_id_map')
    map_dict = dict(zip(df_map['case_title'], df_map['node_id_prex']))

    for root, dirs, files in os.walk('case_1_raw_kg'):
        for file in files:
            print(f"Processing {file}")
            try:
                if not file.endswith("nodes.csv"):
                    continue

                model_flag = get_model_flag(file)
                file = os.path.join(root, file)
                df = pd.read_csv(file)
                df = df.astype(str)
                df['node_id'] = df['case_title'].map(map_dict) + model_flag + df['node_id']

                file_name = file.split('/')[1]
                df.to_csv(f'{norm_path}{file_name}', index=False)
            except Exception as e:
                print(e)


def transfer_relations():
    df_map = pd.read_csv('../../../conf/case_id_map')
    map_dict = dict(zip(df_map['case_title'], df_map['node_id_prex']))

    for root, dirs, files in os.walk('case_1_raw_kg'):
        for file in files:
            try:
                print(f"Processing {file}")
                if not file.endswith("relations.csv"):
                    continue

                model_flag = get_model_flag(file)

                file = os.path.join(root, file)
                df = pd.read_csv(file)
                df = df.astype(str)
                df['src_node_id'] = df['case_title'].map(map_dict) + model_flag + df['src_node_id']
                df['dst_node_id'] = df['case_title'].map(map_dict) + model_flag + df['dst_node_id']

                file_name = file.split('/')[1]
                df.to_csv(f'{norm_path}{file_name}', index=False)
            except Exception as e:
                print(e)


def combine_data(case_ids):
    for case_id in case_ids:
        # 存储所有要合并的 DataFrame
        df_list = []
        # 读取 deepseek 文件
        deepseek_file = f'{norm_path}{case_id}_deepseek_nodes.csv'
        if os.path.exists(deepseek_file):
            df = pd.read_csv(deepseek_file)
            df_list.append(df)

        # 读取 gemini 文件（修复了读错文件的bug）
        gemini_file = f'{norm_path}{case_id}_gemini_nodes.csv'
        if os.path.exists(gemini_file):
            df = pd.read_csv(gemini_file)
            df_list.append(df)

        # 只有有数据时才合并并保存
        if df_list:
            df_nodes = pd.concat(df_list, ignore_index=True)  # 正确合并
            df_nodes.to_csv(f'{combination_path}{case_id}_nodes.csv', index=False)

        df_relation_list = []
        # 读取 deepseek 文件
        deepseek_file = f'{norm_path}{case_id}_deepseek_relations.csv'
        if os.path.exists(deepseek_file):
            df = pd.read_csv(deepseek_file)
            df_relation_list.append(df)

        # 读取 gemini 文件（修复了读错文件的bug）
        gemini_file = f'{norm_path}{case_id}_gemini_relations.csv'
        if os.path.exists(gemini_file):
            df = pd.read_csv(gemini_file)
            df_relation_list.append(df)

        # 只有有数据时才合并并保存
        if df_relation_list:
            df_relations = pd.concat(df_relation_list, ignore_index=True)  # 正确合并
            df_relations.to_csv(f'{combination_path}{case_id}_relations.csv', index=False)

if __name__ == '__main__':
    transfer_nodes()
    transfer_relations()

    combine_data(['c005','c006'])