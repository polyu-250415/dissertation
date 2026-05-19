import pandas as pd
import itertools, os
import ast

from src.taxonomy import RetentionTaxonomy


class SelectCases:
    def __init__(self):
        self.all_combination = list(itertools.product(RetentionTaxonomy.tacit_enum, RetentionTaxonomy.digital_enum))

        self.annotation_path = "../data/papers/midput/screening_by_annotation/"
        self.selection_path = "../data/papers/midput/selection_cases/"

        if not os.path.exists(self.selection_path):
            os.makedirs(self.selection_path, exist_ok=True)

    @staticmethod
    def safe_parse_list(value):
        try:
            return ast.literal_eval(str(value))
        except:
            return []

    def load_and_filter_cases(self, input_file, target_sector_code):
        df = pd.read_csv(input_file, encoding="utf-8")

        df["tacit_list"] = df["tacit_taxonomy"].apply(self.safe_parse_list)
        df["digital_list"] = df["digital_taxonomy"].apply(self.safe_parse_list)
        df["sector_list"] = df["sector_taxonomy"].apply(self.safe_parse_list)

        mask = df["sector_list"].apply(lambda s: target_sector_code in s)
        df_filtered = df[mask].copy()

        cases = []
        for _, row in df_filtered.iterrows():
            uuid = row["uuid"]
            title = row["Title"]
            tacit = row["tacit_list"]
            digital = row["digital_list"]

            valid_tacit = []
            for item in tacit:
                if item in RetentionTaxonomy.tacit_enum:
                    valid_tacit.append(item)
                else:
                    print(f"⚠️  Drop invalid tacit enum | UUID: {uuid} | Invalid value: {item}")

            valid_digital = []
            for item in digital:
                if item in RetentionTaxonomy.digital_enum:
                    valid_digital.append(item)
                else:
                    # 不符合枚举，打印日志
                    print(f"⚠️  Drop invalid digital enum | UUID: {uuid} | Invalid value: {item}")

            # 清洗后为空，跳过整个case
            if not valid_tacit or not valid_digital:
                print(f"❌ Drop this record | UUID: {uuid}")
                continue

            cases.append({
                "uuid": uuid,
                "title": title,
                "tacit_taxonomy": valid_tacit,  # 只保留合法值
                "digital_taxonomy": valid_digital
            })

        print(f"\n✅ Valid case number: {len(cases)}")
        return cases


    def sort_cases_with_coverage_priority(self, objects_list):
        result = {comb: [] for comb in self.all_combination}

        for obj in objects_list:
            tacit_tags = obj["tacit_taxonomy"]
            digital_tags = obj["digital_taxonomy"]
            coverage_count = len(tacit_tags) * len(digital_tags)

            for comb in itertools.product(tacit_tags, digital_tags):
                if comb in result:
                    result[comb].append({
                        "uuid": obj["uuid"],
                        "title": obj["title"],
                        "coverage_count": coverage_count
                    })

        final = {}
        for comb, candidates in result.items():
            # 覆盖数降序
            candidates_sorted = sorted(candidates, key=lambda x: -x["coverage_count"])
            # 去重
            unique = list({c["uuid"]: c for c in candidates_sorted}.values())
            # 选2个
            final[comb] = unique[:2]

        return final

    def select_case_by_sector(self, sector_list):
        input_file = f"{self.annotation_path}annotate_combined_statistics.csv"

        for sector in sector_list:

            filtered_cases = self.load_and_filter_cases(input_file, sector)
            if not filtered_cases:
                print("No valid case，Exit")
                exit()

            final_result = self.sort_cases_with_coverage_priority(filtered_cases)

            case_list = []
            for comb in self.all_combination:
                for case in final_result[comb]:
                    print(f'Sector : {sector}\n Combination: {comb}:\n {case}')
                    case_list.append(case)

            df = pd.DataFrame(case_list)
            df_clean = df.drop_duplicates(subset=["uuid"], keep="first").reset_index(drop=True)
            df_clean.to_csv(f"{self.selection_path}case_selection_{sector}.csv",
                            index=False)


if __name__ == "__main__":
    obj = SelectCases()

    sector_list = ['82', '80', '73', '87', '35', '15']
    obj.select_case_by_sector(sector_list)