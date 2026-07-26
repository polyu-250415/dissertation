import os, json, re
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

import pandas as pd
import ast
import numpy as np
from poetry.console.commands import self

from src.utils.llm_mgmt.deepseek_api_interface import DeepSeekAPI
from src.utils.llm_mgmt.qwen_api_interface import QwenAPI
from src.utils.llm_mgmt.ernie_api_interface import ErnieAPI


class ScreenPapersAnnotation:
    def __init__(self, count=10, max_count=0):
        self.annotation_path = "../data/papers/midput/screening_by_annotation/"
        self.paper_screen_t3 = '../data/papers/midput/screening_by_abs_t3/'
        self.annotation_turn_1 = '../data/papers/midput/screening_by_annotation/turn_1'
        self.annotation_turn_2 = '../data/papers/midput/screening_by_annotation/turn_2'
        self.count = count
        self.max_count = max_count
        self.cmd = "cmd_annotate_by_abstract"
        self.infer_interface = 'r1_infer'

        if not os.path.exists(self.annotation_path):
            os.makedirs(self.annotation_path, exist_ok=True)

    def infer_api(self, prompt):
        if self.infer_interface == 'r1_infer':
            return DeepSeekAPI.r1_infer(prompt)
        elif self.infer_interface == 'r1_local_infer':
            return DeepSeekAPI.r1_local_infer(prompt)
        else:
            return DeepSeekAPI.r1_infer(prompt)

    def annotate_by_qwen(self, input_file, sub_dir_path):
        output_file = f"{self.annotation_path}/{sub_dir_path}/annotate_by_qwen.csv"

        QwenAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count,
                                max_count=self.max_count)

    def annotate_by_deepseek(self, input_file, sub_dir_path):
        output_file = f"{self.annotation_path}/{sub_dir_path}/annotate_by_deepseek.csv"

        DeepSeekAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count,
                                    max_count=self.max_count)

    def annotate_by_ernie(self, input_file, sub_dir_path):
        output_file = f"{self.annotation_path}/{sub_dir_path}/annotate_by_ernie.csv"

        ErnieAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count,
                                 max_count=self.max_count)


    def annotate_parallel(obj, input_file, sub_dir_path):
        """
        并行执行 Qwen 和 Kimi 相关性评估
        :param obj: ScreenPaperCraw 实例对象
        """

        def run_deepseek():
            print("Start evaluating by DeepSeek...")
            obj.annotate_by_deepseek(input_file, sub_dir_path)

        def run_qwen():
            print("Start evaluating by Qwen...")
            obj.annotate_by_qwen(input_file, sub_dir_path)

        def run_ernie():
            print("Start evaluating by ernie...")
            obj.annotate_by_ernie(input_file, sub_dir_path)

        # 并行执行
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(run_deepseek)
            executor.submit(run_qwen)
            executor.submit(run_ernie)

    def combine_annotation(self):
        df_deepseek = pd.read_csv(f"{self.annotation_path}annotate_by_deepseek.csv")
        df_ernie = pd.read_csv(f"{self.annotation_path}annotate_by_ernie.csv")
        df_qwen = pd.read_csv(f"{self.annotation_path}annotate_by_qwen.csv")

        df_ernie = df_ernie.add_prefix('ernie_')
        df_ernie = df_ernie.rename(columns={'ernie_uuid': 'uuid', 'ernie_Title': 'Title'})

        df_deepseek = df_deepseek.add_prefix('deepseek_')
        df_deepseek = df_deepseek.rename(columns={'deepseek_uuid': 'uuid', 'deepseek_Title': 'Title'})

        df_qwen = df_qwen.add_prefix('qwen_')
        df_qwen = df_qwen.rename(columns={'qwen_uuid': 'uuid', 'qwen_Title': 'Title'})

        df_combined = pd.merge(df_qwen, df_deepseek, on=['uuid', 'Title'], how='left')
        df_combined = pd.merge(df_combined, df_ernie, on=['uuid', 'Title'], how='left')

        df_combined.to_csv(f"{self.annotation_path}annotate_combined.csv", index=False)

    @staticmethod
    def deduplicate_objects(obj_list):
        seen = set()
        result = []
        for obj in obj_list:
            key = json.dumps(obj, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                result.append(obj)
        return result

    def merge_csv_files(self,input_file, sub_dir_path):

        csv_list = [
            f'{self.annotation_path}/{sub_dir_path}/annotate_by_deepseek.csv',
            f'{self.annotation_path}/{sub_dir_path}/annotate_by_ernie.csv',
            f'{self.annotation_path}/{sub_dir_path}/annotate_by_qwen.csv',
        ]
        output = f'{self.annotation_path}/{sub_dir_path}/annotate_combined.csv'

        key_data = defaultdict(lambda: {'tacit': [], 'digital': [], 'sector': []})

        for file_path in csv_list:
            df = pd.read_csv(file_path, dtype=str)
            required = ['uuid', 'Title', 'tacit_knowledge_array', 'digital_technology_array', 'sector']
            for col in required:
                if col not in df.columns:
                    raise ValueError(f"File  {file_path} lack {col}")

            for _, row in df.iterrows():
                uuid = str(row['uuid']).strip()
                title = str(row['Title']).strip()
                key = (uuid, title)

                tacit_str = row['tacit_knowledge_array']
                if pd.notna(tacit_str) and tacit_str.strip():
                    try:
                        tacit_list = ast.literal_eval(tacit_str)
                        if isinstance(tacit_list, list):
                            key_data[key]['tacit'].extend(tacit_list)
                    except json.JSONDecodeError:
                        pass

                digital_str = row['digital_technology_array']
                if pd.notna(digital_str) and digital_str.strip():
                    try:
                        digital_list = ast.literal_eval(digital_str)
                        if isinstance(digital_list, list):
                            key_data[key]['digital'].extend(digital_list)
                    except json.JSONDecodeError:
                        pass

                sector_str = row['sector']
                if pd.notna(sector_str) and sector_str.strip():
                    try:
                        sector_obj = ast.literal_eval(sector_str)
                        key_data[key]['sector'].append(sector_obj)
                    except json.JSONDecodeError:
                        pass

        for data in key_data.values():
            data['tacit'] = self.deduplicate_objects(data['tacit'])
            data['digital'] = self.deduplicate_objects(data['digital'])
            data['sector'] = self.deduplicate_objects(data['sector'])

        rows = []
        for (uuid, title), data in key_data.items():
            rows.append({
                'uuid': uuid,
                'Title': title,
                'tacit_knowledge_array': json.dumps(data['tacit'], ensure_ascii=False),
                'digital_technology_array': json.dumps(data['digital'], ensure_ascii=False),
                'sector': json.dumps(data['sector'], ensure_ascii=False)
            })
        output_df = pd.DataFrame(rows)
        input_df = pd.read_csv(input_file)
        pd.merge(input_df, output_df, on=['uuid', 'Title'], how='left').to_csv(output, index=False, encoding='utf-8')

    def validate_annotation(self, sub_dir_path):

        input_file = f'{self.annotation_path}/{sub_dir_path}/annotate_combined.csv'
        output_file = f'{self.annotation_path}/{sub_dir_path}/annotate_combined_validated.csv'

        key_data = defaultdict(lambda: {'tacit': [],
                                        'digital': [],
                                        'sector': [],
                                        'tacit_taxonomy': [],
                                        'digital_taxonomy': [],
                                        'sector_taxonomy': [], })

        df = pd.read_csv(input_file, dtype=str)

        validation_prompt = """
### Context: 
{{context}}

### Instructions:
1. Judge each claim ONLY based on the given context. Do NOT use any external knowledge, common sense, or your own knowledge.
2. For each claim in the claim list, output 1 if true, 0 if false.
3. Output exactly one result per claim, same quantity as claims.
4. Separate results with semicolons.
5. Return ONLY the 1/0 sequence with semicolons, no explanations, no extra text.

### Claim list:
{{claim_list}}

### Critical Self-Correction & Verification Step
Before generating the final result, I must perform a silent, internal compliance check. Verify the following:
1. **Evidence Verification:** Is my judgment solely based on the background information provided for each argument? If not, please rephrase it. 
2. **Format Validation:** Dose the number of questions answered matches the number of presented questions. If there are any inconsistencies, make the necessary corrections.

If any check fails during your internal processing, correct it instantly before writing the output.
        """

        for _, row in df.iterrows():
            try:
                uuid = str(row['uuid']).strip()
                title = str(row['Title']).strip()
                key = (uuid, title)

                print(f"validating claim uuid:{uuid}; title:{title}")
                claim_list = []
                tacit_str = row['tacit_knowledge_array']
                if pd.notna(tacit_str) and tacit_str.strip():
                    try:
                        tacit_list = ast.literal_eval(tacit_str)
                        key_data[key]['tacit'] = tacit_list
                        if isinstance(tacit_list, list):

                            tacit_list_len = len(tacit_list)

                            if not tacit_list_len:
                                continue

                            for index in range(tacit_list_len):
                                claim = f"{index}. [{tacit_list[index]['tacit_knowledge']}] has been discussed"
                                claim_list.append(claim)

                            claim_list_str = '\n'.join(claim_list)
                            prompt = validation_prompt.replace('{{context}}',
                                                                row['Abstract']).replace('{{claim_list}}', claim_list_str)
                            response = self.infer_api(prompt)
                            print(f'prompt:\n {prompt} \n response: {response} \n claim_list:\n {claim_list_str}')

                            result_array = response.split(';')

                            for index in range(tacit_list_len):
                                if result_array[index] == '1':
                                    key_data[key]['tacit_taxonomy'].append(re.sub(r'\([^()]*\)', '',
                                                                                  tacit_list[index]['tacit_knowledge_normalized']).strip())

                    except Exception as e:
                        print(e)
                        pass

                digital_str = row['digital_technology_array']
                if pd.notna(digital_str) and digital_str.strip():
                    try:
                        digital_list = ast.literal_eval(digital_str)
                        key_data[key]['digital'] = digital_list

                        claim_list = []
                        if isinstance(digital_list, list):

                            digital_list_len = len(digital_list)

                            if not digital_list_len:
                                continue

                            for index in range(digital_list_len):
                                claim = (f"{index}. The application of [{digital_list[index]['digital_technology']}] "
                                         f"has been discussed.")
                                claim_list.append(claim)

                            claim_list_str = '\n'.join(claim_list)
                            prompt = validation_prompt.replace('{{context}}',
                                            row['Abstract']).replace('{{claim_list}}',claim_list_str)
                            # response = chat_with_deepseek(prompt)
                            response = self.infer_api(prompt)
                            print(f'prompt:\n {prompt} \n response: {response} \n claim_list:\n {claim_list_str}')

                            result_array = response.split(';')

                            for index in range(digital_list_len):
                                if result_array[index] == '1':
                                    key_data[key]['digital_taxonomy'].append(digital_list[index]['digital_technology_normalized'])

                    except Exception as e:
                        print(e)
                        pass

                sector_str = row['sector']
                if pd.notna(sector_str) and sector_str.strip():
                    try:
                        sector_list = ast.literal_eval(sector_str)
                        key_data[key]['sector'] = sector_list
                        if isinstance(sector_list, list):
                            for item in sector_list:
                                if item['sector_confidence'] == 'low':
                                    continue

                                key_data[key]['sector_taxonomy'].append(re.sub(r'\D', '', item['sector_id']).strip())

                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(e)
                pass

        for data in key_data.values():
            data['tacit_taxonomy'] = self.deduplicate_objects(data['tacit_taxonomy'])
            data['digital_taxonomy'] = self.deduplicate_objects(data['digital_taxonomy'])
            data['sector_taxonomy'] = self.deduplicate_objects(data['sector_taxonomy'])

        rows = []
        for (uuid, title), data in key_data.items():
            rows.append({
                'uuid': uuid,
                'Title': title,
                'tacit_knowledge_array': json.dumps(data['tacit'], ensure_ascii=False),
                'digital_technology_array': json.dumps(data['digital'], ensure_ascii=False),
                'sector': json.dumps(data['sector'], ensure_ascii=False),
                'tacit_taxonomy': json.dumps(data['tacit_taxonomy'], ensure_ascii=False),
                'digital_taxonomy': json.dumps(data['digital_taxonomy'], ensure_ascii=False),
                'sector_taxonomy': json.dumps(data['sector_taxonomy'], ensure_ascii=False)
            })

        output_df = pd.DataFrame(rows)
        output_df.to_csv(output_file, index=False)

    def supplement_annotation(self,raw_input_file, input_file, sub_dir_path):
        output_accepted = f'{self.annotation_path}/{sub_dir_path}/annotate_waiting_for_accepted.csv'
        output_audited = f'{self.annotation_path}/{sub_dir_path}/annotate_waiting_for_recheck.csv'

        output_df = pd.read_csv(input_file)

        check_columns = [
            "tacit_knowledge_array",
            "digital_technology_array",
            "sector",
            "tacit_taxonomy",
            "digital_taxonomy",
            "sector_taxonomy"
        ]

        annotation_flag_arr = [True] * output_df.shape[0]
        for idx, row in output_df.iterrows():
            for col in check_columns:
                if row[col] == '[]':
                    annotation_flag_arr[idx] = False
                    continue

        output_df[annotation_flag_arr].to_csv(output_accepted, index=False, encoding='utf-8')
        accepted_uuid_list = output_df[annotation_flag_arr]['uuid'].tolist()

        df_annotated = pd.read_csv(raw_input_file)
        df_annotated[~df_annotated['uuid'].isin(accepted_uuid_list)].to_csv(output_audited, index=False,
                                                                            encoding='utf-8')
    def combine_accepted_papers(self, turn_num=3):

        df = pd.DataFrame()
        for i in range(turn_num):
            df = pd.concat([df,
                            pd.read_csv(f"{self.annotation_path}/turn_{i+1}/annotate_waiting_for_accepted.csv")],
                           ignore_index=True)
        df.to_csv(f"{self.annotation_path}/annotate_accepted.csv", index=False)


if __name__ == '__main__':
    stage = 4
    obj = ScreenPapersAnnotation(count=6, max_count=500)

    if stage == 1:
        input_file = f"{obj.annotation_path}waiting_for_annotation.csv"
        sub_dir_path = f"turn_{stage}"
        obj.annotate_parallel(input_file, sub_dir_path)
        obj.merge_csv_files(input_file, sub_dir_path)
        obj.validate_annotation(sub_dir_path)
        validated_input_file = f'{obj.annotation_path}/{sub_dir_path}/annotate_combined_validated.csv'
        obj.supplement_annotation(input_file, validated_input_file, sub_dir_path)

    if stage == 2:
        input_file = f"{obj.annotation_path}/turn_{stage-1}/annotate_waiting_for_recheck.csv"
        sub_dir_path = f"turn_{stage}"
        obj.annotate_parallel(input_file, sub_dir_path)
        obj.merge_csv_files(input_file, sub_dir_path)
        obj.validate_annotation(sub_dir_path)
        validated_input_file = f'{obj.annotation_path}/{sub_dir_path}/annotate_combined_validated.csv'
        obj.supplement_annotation(input_file, validated_input_file, sub_dir_path)

    if stage == 3:
        input_file = f"{obj.annotation_path}/turn_{stage - 1}/annotate_waiting_for_recheck.csv"
        sub_dir_path = f"turn_{stage}"
        obj.annotate_parallel(input_file, sub_dir_path)
        obj.merge_csv_files(input_file, sub_dir_path)
        obj.validate_annotation(sub_dir_path)
        validated_input_file = f'{obj.annotation_path}/{sub_dir_path}/annotate_combined_validated.csv'
        obj.supplement_annotation(input_file, validated_input_file, sub_dir_path)

    if stage == 4:
        obj.combine_accepted_papers()

