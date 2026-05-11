import json, os
import time

import pandas as pd

from src.utils.llm_api import get_qwen_obj
from src.case_select_tool.llm_mgmt.prompt_generator import LiteratureReviewPrompt

class QwenAPI:
    def __init__(self, model_name = 'Chat'):
        pass

    @staticmethod
    def extract(prompt: str) -> dict:

        try:
            response = get_qwen_obj(prompt)
            result = json.loads(response)
            return result
        except Exception as e:
            print(f"Error processing extract: {e}")
            return []


    def batch_extract(self, input_file, output_file, cmd, count = 5):

        exist_record_dict = {}
        if os.path.exists(f'{output_file}.csv'):
            try:
                df_exist = pd.read_csv(f'{output_file}.csv')
                for i, row in df_exist.iterrows():
                    if row['kr_flag'] != "Undisposed":
                        row_dict = df_exist.iloc[i].to_dict()
                        exist_record_dict[row['uuid']] = row_dict
            except Exception as e:
                print(f"Error processing abstract: {e}")
                pass

        with open(input_file,
                  'r',
                  encoding='utf-8') as f:
            documents = json.load(f)

        enhanced_docs = []
        body = []

        try:
            for i, doc in enumerate(documents):
                uuid = doc.get("uuid", "")
                if uuid not in exist_record_dict.keys():
                    # 定义要提取的字段列表
                    fields = ["uuid", "Title", "Abstract", "DOI Link"]
                    # 一行批量提取所有字段
                    item = {field: doc.get(field, "") for field in fields}
                    body.append(item)
                    print(f'Qwen Processing abstract: {i + 1}/{len(documents)}')
                else:
                    print(f'Qwen Processing existed: {i + 1}/{len(documents)}')

                if ((i + 1) % count) == 0:
                    body_answer = self.extract(LiteratureReviewPrompt(body=body).get_prompt(cmd))
                    if isinstance(body_answer, list):
                        enhanced_docs.extend(body_answer)
                    body = []

            if len(body):
                body_answer = self.extract(LiteratureReviewPrompt(body=body).get_prompt(cmd))
                if isinstance(body_answer, list):
                    enhanced_docs.extend(body_answer)

        except Exception as e:
            print(f"Error processing abstract: {e}")
            pass

        (pd.DataFrame(enhanced_docs).fillna("Undisposed").to_csv(f'{output_file}.csv', index=None))

if __name__ == '__main__':

    input_file = "../../data/papers/midput/screening_by_abs_t2/papers_2.json"
    output_file = "../../data/papers/midput/screening_by_abs_t2/papers_2_qwen.csv"
    cmd = "Cmd_Screen_by_Abstract"

    QwenAPI().batch_extract(input_file, output_file, cmd,count=3)
