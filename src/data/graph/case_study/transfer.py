import os
import pandas as pd
from dashscope.tokenizers.tokenizer import current_path

current_path = os.path.abspath('./') + '/cases'

def transfer_nodes():

    df_map = pd.read_csv('../../../conf/case_id_map')
    map_dict = dict(zip(df_map['case_title'], df_map['node_id_prex']))

    for root, dirs, files in os.walk('raw'):
        for file in files:
            if not file.endswith("nodes.csv"):
                continue

            file = os.path.join(root, file)
            df = pd.read_csv(file)
            df = df.astype(str)
            df['id'] = df['case_title'].map(map_dict) + df['id']

            file_name = map_dict[df['case_title'].iloc[0]]
            df.to_csv(f'{current_path}/{file_name}_nodes.csv', index=False)


def transfer_relations():
    df_map = pd.read_csv('../../../conf/case_id_map')
    map_dict = dict(zip(df_map['case_title'], df_map['node_id_prex']))

    for root, dirs, files in os.walk('raw'):
        for file in files:
            if not file.endswith("relations.csv"):
                continue

            file = os.path.join(root, file)
            df = pd.read_csv(file)
            df = df.astype(str)
            df['start_id'] = df['case_title'].map(map_dict) + df['start_id']
            df['end_id'] = df['case_title'].map(map_dict) + df['end_id']

            file_name = map_dict[df['case_title'].iloc[0]]
            df.to_csv(f'{current_path}/{file_name}_relations.csv', index=False)

if __name__ == '__main__':
    transfer_nodes()
    transfer_relations()