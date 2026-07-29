import pandas as pd
import itertools, os, re
import ast

from src.taxonomy import RetentionTaxonomy
from collections import defaultdict


class SelectCases:
    def __init__(self):
        self.all_combination = list(itertools.product(RetentionTaxonomy.collins_based_tacit_knowledge_taxonomy, RetentionTaxonomy.digital_enum))

        self.annotation_path = "../data/papers/midput/screening_by_annotation/"
        self.selection_path = "../data/papers/midput/selection_cases/"
        self.conf_path = "../conf/coding_schema/"
        self.raw_pdf_path = "../data/graph/case_study/raw_pdf_m/"
        self.raw_kg_path = "../data/graph/case_study/case_1_raw_kg_m/"

        if not os.path.exists(self.selection_path):
            os.makedirs(self.selection_path, exist_ok=True)

    @staticmethod
    def safe_parse_list(value):
        try:
            return ast.literal_eval(str(value))
        except Exception as e:
            print(e)
            return []

    def load_and_filter_cases(self, input_file, target_sector_code):
        df = pd.read_excel(input_file, sheet_name="annotate_combined_addition")

        df["tacit_list"] = df["tacit_taxonomy"].apply(self.safe_parse_list)
        df["digital_list"] = df["digital_taxonomy"].apply(self.safe_parse_list)

        mask = df["Sector_Annotation_by_HR"].apply(lambda s: s == target_sector_code)
        df_filtered = df[mask].copy()

        cases = []
        combo_count = defaultdict(int)
        for _, row in df_filtered.iterrows():
            uuid = row["uuid"]
            title = row["Title"]
            tacit = row["tacit_list"]
            digital = row["digital_list"]

            valid_tacit = []
            for item in tacit:
                if item in RetentionTaxonomy.collins_based_tacit_knowledge_taxonomy:
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
                # print(f"❌ Drop this record | UUID: {uuid}")
                continue

            cases.append({
                "uuid": uuid,
                "Title": title,
                "tacit_taxonomy": valid_tacit,  # 只保留合法值
                "digital_taxonomy": valid_digital
            })

            for t in valid_tacit:
                for d in valid_digital:
                    combo_count[(t, d)] += 1

        print("\n" + "=" * 60)
        print(f"📊 SIC: {target_sector_code} tacit × digital 组合数量统计")
        print("=" * 60)
        if combo_count:
            for (tacit_val, digital_val), count in sorted(combo_count.items()):
                print(f"✅ {tacit_val:20} × {digital_val:20} : {count:2} 次")
        else:
            print("❌ 无任何有效组合")
        print("=" * 60 + "\n")

        df_temp = pd.DataFrame([(k[0], k[1], v) for k, v in combo_count.items()],
                               columns=['t', 'd', 'count'])
        df_temp.to_csv(f"{self.selection_path}{target_sector_code}_comb.csv", index=False)
        # ================================================================

        # print(f"\n✅ Valid case number: {len(cases)}")

        return cases


    def sort_cases_with_coverage_priority(self, objects_list):
        result = {comb: [] for comb in self.all_combination}

        for obj in objects_list:
            tacit_tags = obj["tacit_taxonomy"]
            digital_tags = obj["digital_taxonomy"]
            coverage_count = len(tacit_tags) * len(digital_tags)
            comb_list = list(itertools.product(tacit_tags, digital_tags))

            for comb in itertools.product(tacit_tags, digital_tags):
                if comb in result:
                    result[comb].append({
                        "uuid": obj["uuid"],
                        "Title": obj["Title"],
                        "coverage_count": coverage_count,
                        'comb_list': comb_list
                    })

        final = {}
        for comb, candidates in result.items():
            # 覆盖数降序
            candidates_sorted = sorted(candidates, key=lambda x: -x["coverage_count"])
            # 去重
            unique = list({c["uuid"]: c for c in candidates_sorted}.values())
            # 选3个
            final[comb] = unique[:5]

        return final

    def select_case_by_sector(self, input_file, sector_list):
        df_total = pd.DataFrame()
        for sector in sector_list:

            filtered_cases = self.load_and_filter_cases(input_file, sector)
            if not filtered_cases:
                print("No valid case，Exit")
                exit()

            final_result = self.sort_cases_with_coverage_priority(filtered_cases)

            case_list = []
            for comb in self.all_combination:
                for case in final_result[comb]:
                    case_list.append(case)

            df = pd.DataFrame(case_list)
            df_clean = df.drop_duplicates(subset=["uuid"], keep="first").reset_index(drop=True)
            df_clean.to_csv(f"{self.selection_path}{sector}_selected.csv",
                            index=False)
            df_total = pd.concat([df_total, df_clean])

        df_addition = pd.read_excel(input_file, sheet_name="annotate_combined_addition")
        df_total = pd.merge(df_total, df_addition, on=['uuid', 'Title'], how='inner')
        df_total.to_csv(f"{self.selection_path}case_selection_total.csv", index=False)

    def build_case_metadata(self, input_file, raw_pdf_dir):
        df_case = pd.read_excel(input_file, sheet_name="case_selection_total")

        file_array = []
        for root, dirs, files in os.walk(raw_pdf_dir):
            for file in files:
                file = os.path.join(root, file)
                file_array.append(file)

        def clean_string(s):
            return re.sub(r'[^a-zA-Z]', '', str(s)).lower()

        node_id_array = []
        case_title_array = []
        pdf_path_array = []
        for index, row in df_case.iterrows():
            node_id_array.append(row['node_id'])
            case_title_array.append(row['Title'])
            pdf_path_empty_flag = True
            for file in  file_array:
                if clean_string(row['Title']) in clean_string(file):
                    pdf_path_array.append(file)
                    pdf_path_empty_flag = False
                    break

            if pdf_path_empty_flag:
                pdf_path_array.append('unknown')

        pd.DataFrame({
            'node_id_prex': node_id_array,
            'case_title': case_title_array,
            'file_path': pdf_path_array
        }).to_csv(f"{self.conf_path}case_id_map.csv", index=False)

        node_headers = ['node_id','node_name','category','evidence_label','case_title','evidence_statement','object_definition','evidence_location']
        edge_headers = ['src_node_id','dst_node_id','relation_type','evidence_label','case_title','evidence_statement','evidence_location']
        # build empty files
        for idx in node_id_array:
            file_path = f"{self.raw_kg_path}{idx}_deepseek_nodes.csv"
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(",".join(node_headers) + "\n")

            file_path = f"{self.raw_kg_path}{idx}_chatgpt_nodes.csv"
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(",".join(node_headers) + "\n")

            file_path = f"{self.raw_kg_path}{idx}_deepseek_edges.csv"
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(",".join(edge_headers) + "\n")

            file_path = f"{self.raw_kg_path}{idx}_chatgpt_edges.csv"
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(",".join(edge_headers) + "\n")



if __name__ == "__main__":

    stage = 2
    obj = SelectCases()

    if stage == 1:

        sector_list = [
            'SIC15 Construction (Building Construction - General Contractors and Operative Builders)',
            'SIC35 Manufacturing (Industrial And Commercial Machinery And Computer Equipment)',
            'SIC80 Services (Health Services)'
        ]
        input_file = f'{obj.annotation_path}annotate_combined_addition.xlsx'
        obj.select_case_by_sector(input_file, sector_list)

    if stage == 2:
        input_file = f'{obj.selection_path}case_selection_total.xlsx'
        obj.build_case_metadata(input_file, obj.raw_pdf_path)
