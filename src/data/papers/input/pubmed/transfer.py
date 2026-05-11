import csv
import pandas as pd


def parse_pubmed_to_csv(input_txt, output_csv):
    """
    专门解析 PubMed 官网导出的 PubMed 格式文本文件
    自动转成标准 CSV，支持多条记录
    """
    records = []
    current = {}
    current_tag = None
    current_data = []

    with open(input_txt, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')  # 去掉换行

            # 空行 = 一条记录结束
            if not line.strip():
                if current_tag:
                    current[current_tag] = ' '.join(current_data).strip()

                if current:
                    records.append(current)
                    current = {}

                current_tag = None
                current_data = []
                continue

            # 匹配 PubMed 格式行：前6个字符是标签
            if line[:6].strip():
                tag = line[:6].strip()
                content = line[6:].strip()

                # 保存上一个字段
                if current_tag:
                    current[current_tag] = ' '.join(current_data).strip()

                # 开始新字段
                current_tag = tag
                current_data = [content]
            else:
                # 续行（缩进行）
                if current_tag:
                    current_data.append(line.strip())

        # 最后一条记录
        if current_tag:
            current[current_tag] = ' '.join(current_data).strip()
        if current:
            records.append(current)

    # 所有出现过的字段（保证 CSV 列完整）
    all_fields = set()
    for rec in records:
        all_fields.update(rec.keys())
    fieldnames = sorted(all_fields)

    # 写入 CSV
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ 转换成功！共 {len(records)} 条文献")
    print(f"📄 输出文件：{output_csv}")


def combine_pubmed_to_csv(input_txt,input_csv, output_csv):

    df_txt = pd.read_csv(input_txt).sort_values(by=['PMID-'], ascending=True)
    df_csv = pd.read_csv(input_csv).sort_values(by=['PMID'], ascending=True)

    df_combine = pd.DataFrame()
    df_combine['Title'] = df_csv['Title']
    df_combine['Author'] = df_csv['Authors']
    df_combine['Abstract'] = df_txt['AB  -']
    df_combine['Keywords'] = df_txt['OT  -']
    df_combine['Publication title'] = df_csv['Journal/Book']
    df_combine['Country of publication'] = df_txt['PL  -']
    df_combine['Publication year'] = df_csv['Publication Year']
    df_combine['Source type'] = df_txt['PT  -']
    df_combine['Language of publication'] = "unknown"
    df_combine['DOI Link'] = df_csv['DOI']

    df_combine.to_csv(output_csv, index=False)

if __name__ == "__main__":
    # 你从 PubMed 导出的 txt 文件
    INPUT_FILE = "knowledge_capture_plus_retention.txt"
    # 要输出的 CSV 文件名
    TXT_FILE = "knowledge_capture_plus_retention_txt_format.csv"
    CSV_FILE = "knowledge_capture_plus_retention_csv_format.csv"

    OUTPUT_CSV = "knowledge_capture_plus_retention.csv"

    parse_pubmed_to_csv(INPUT_FILE, TXT_FILE)
    combine_pubmed_to_csv(TXT_FILE, CSV_FILE, OUTPUT_CSV)