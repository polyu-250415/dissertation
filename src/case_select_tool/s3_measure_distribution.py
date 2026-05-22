import re, os
from collections import Counter

import pandas as pd
import ast

from src.taxonomy import IndustryTaxonomy


class MeasureDistribution(object):

    def __init__(self):
        self.annotation_path = "../data/papers/midput/screening_by_annotation/"
        self.selection_path = "../data/papers/midput/selection_cases/"

        if not os.path.exists(self.selection_path):
            os.makedirs(self.selection_path, exist_ok=True)

        pass

    def illustrate_sector_distribution(self):
        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_sector_statistics.csv'

        df = pd.read_csv(input_file)

        # Initialize counter
        counter = Counter()

        # Process each non-null cell in the 'sector_taxonomy' column
        for cell in df['sector_taxonomy'].dropna():
            # Convert string representation of list (e.g., "['84']") to actual list
            codes = ast.literal_eval(cell)
            counter.update(str(code) for code in codes)

        sic_desc = []
        sic_id = []
        counts = []
        for code, count in sorted(counter.items(), key=lambda x: x[1], reverse=False):
            if code in IndustryTaxonomy.sic_dict:
                raw_desc = IndustryTaxonomy.sic_dict[code]
            else:
                code = '0099'
                raw_desc = f"SIC {code}"
            sic_desc.append(raw_desc)
            sic_id.append(code)
            counts.append(count)

        df = pd.DataFrame({
            'sic_desc': sic_desc,
            'sic_id': sic_id,
            'count': counts
        })

        df.to_csv(statistic_file, index=False, encoding='utf-8')

    def illustrate_tacit_knowledge_type_distribution(self):
        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_tacit_knowledge_statistics.csv'

        df = pd.read_csv(input_file)

        # Initialize counter
        counter = Counter()

        # Process each non-null cell in the 'sector_taxonomy' column
        for cell in df['tacit_taxonomy'].dropna():
            # Convert string representation of list (e.g., "['84']") to actual list
            tks = ast.literal_eval(cell)
            counter.update(re.sub(r'\([^()]*\)', '', tk) for tk in tks)

        tk_type = []
        counts = []
        for tk, count in sorted(counter.items(), key=lambda x: x[1], reverse=False):
            tk_type.append(tk)
            counts.append(count)

        df = pd.DataFrame({
            'tk_type': tk_type,
            'count': counts
        })

        df.to_csv(statistic_file, index=False, encoding='utf-8')
        pass

    def illustrate_digital_technologies_distribution(self):
        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_digital_technology_statistics.csv'

        df = pd.read_csv(input_file)

        # Initialize counter
        counter = Counter()

        # Process each non-null cell in the 'sector_taxonomy' column
        for cell in df['digital_taxonomy'].dropna():
            # Convert string representation of list (e.g., "['84']") to actual list
            tks = ast.literal_eval(cell)
            counter.update(re.sub(r'\([^()]*\)', '', tk) for tk in tks)

        dt_type = []
        counts = []
        for tk, count in sorted(counter.items(), key=lambda x: x[1], reverse=False):
            dt_type.append(tk)
            counts.append(count)

        df = pd.DataFrame({
            'dt_type': dt_type,
            'count': counts
        })

        df.to_csv(statistic_file, index=False, encoding='utf-8')
        pass

    def illustrate_cross_distribution(self):

        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_cross_sector_statistics.csv'

        def parse_sector_list(sector_str):
            try:
                lst = ast.literal_eval(str(sector_str))
                if not isinstance(lst, list):
                    return []
                return [str(s).strip() for s in lst if str(s).strip()]
            except:
                return []

        # ---------------------- 1. 读取数据 ----------------------
        df = pd.read_csv(input_file, encoding="utf-8")
        df["sector_parsed"] = df["sector_taxonomy"].apply(parse_sector_list)

        # 只保留非空行
        df_valid = df[df["sector_parsed"].str.len() > 0].copy()

        # ---------------------- 2. 提取所有唯一行业key ----------------------
        all_sectors = []
        for sectors in df_valid["sector_parsed"]:
            all_sectors += sectors
        unique_sectors = sorted(list(set(all_sectors)))

        # ---------------------- 3. 初始化统计 ----------------------
        sector_cross_count = {key: 0 for key in unique_sectors}  # 跨行业数量
        sector_single_count = {key: 0 for key in unique_sectors}  # 不跨行业数量

        # ---------------------- 4. 逐行统计 ----------------------
        for sectors in df_valid["sector_parsed"]:
            if len(sectors) == 1:
                # 不跨行业：给唯一的那个key +1
                key = sectors[0]
                if key in sector_single_count:
                    sector_single_count[key] += 1
            elif len(sectors) >= 2:
                # 跨行业：给所有key +1
                for key in sectors:
                    if key in sector_cross_count:
                        sector_cross_count[key] += 1

        # ---------------------- 5. 构建结果DataFrame ----------------------
        result_df = pd.DataFrame({"SIC": unique_sectors})
        result_df['sector_name'] = result_df['SIC'].map(IndustryTaxonomy.sic_dict)
        result_df['single_sector_count'] = [sector_single_count[k] for k in unique_sectors]
        result_df['cross_sector_count'] = [sector_cross_count[k] for k in unique_sectors]
        result_df['total_count'] = [sector_single_count[k] + sector_cross_count[k] for k in unique_sectors]
        result_df['rate'] = (result_df['cross_sector_count'] / result_df['total_count']).map(lambda x: f"{x:.2f}")
        result_df.sort_values(["total_count"], ascending=False, inplace=True)

        result_df.to_csv(statistic_file, index=False, encoding='utf-8')



if __name__ == '__main__':
    obj = MeasureDistribution()
    """
    obj.illustrate_sector_distribution()
    obj.illustrate_tacit_knowledge_type_distribution()
    obj.illustrate_digital_technologies_distribution()"""
    obj.illustrate_cross_distribution()