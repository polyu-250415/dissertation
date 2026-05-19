import pandas as pd


def compare_deepseek_results():
    input_final = "/Users/meimei/work/coding/mei-factory/src/src/data/papers/backup/midput_04_05/paper_extraction_turn2/waiting_for_accept_papers.csv"

    input_mid = "../data/papers/midput/screening_by_abs_t2/waiting_for_accept_papers.csv"

    df_final = pd.read_csv(input_final)
    df_mid = pd.read_csv(input_mid)

    duplicate_records = df_final[df_final['uuid'].isin(df_mid['uuid'])]
    print(f"df_final记录数{len(df_final)}")
    print("df_final中在df_mid里重复的记录：")
    print(duplicate_records)


import csv
import json


def csv_to_json_array(csv_file_path, json_file_path, encoding='utf-8'):
    """
    读取 CSV 文件，转换为 JSON 数组并写入文件。

    参数:
        csv_file_path (str): 输入的 CSV 文件路径
        json_file_path (str): 输出的 JSON 文件路径
        encoding (str): 文件编码，默认 utf-8
    """
    data = []

    with open(csv_file_path, 'r', encoding=encoding) as csv_file:
        # 使用 DictReader 自动将第一行作为键，每行转为字典
        reader = csv.DictReader(csv_file)
        for row in reader:
            data.append(row)

    with open(json_file_path, 'w', encoding=encoding) as json_file:
        # 写入 JSON 数组，indent 参数使输出可读，可设为 None 压缩输出
        json.dump(data, json_file, indent=2, ensure_ascii=False)

    print(f"成功将 {csv_file_path} 转换为 {json_file_path}，共 {len(data)} 条记录。")


# 使用示例
if __name__ == "__main__":
    # csv_to_json_array("../data/papers/midput/screening_by_abs_t2/papers_0.csv", "../data/papers/midput//screening_by_abs_t2/papers_0.json")
    compare_deepseek_results()
