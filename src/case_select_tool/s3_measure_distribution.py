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


if __name__ == '__main__':
    obj = MeasureDistribution()
    obj.illustrate_sector_distribution()
    obj.illustrate_tacit_knowledge_type_distribution()
    obj.illustrate_digital_technologies_distribution()