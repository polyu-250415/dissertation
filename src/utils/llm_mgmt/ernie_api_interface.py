import json, os

import pandas as pd

from src.utils.llm_api import get_ernie_obj
from src.utils.llm_mgmt.prompt_generator import LiteratureReviewPrompt

class ErnieAPI:
    def __init__(self, model_name = 'Chat'):
        pass

    @staticmethod
    def extract(prompt: str) -> dict:

        try:
            response = get_ernie_obj(prompt)
            result = json.loads(response)
            return result
        except Exception as e:
            print(f"Error processing extract: {e}")
            return []


    def batch_extract(self, input_file, output_file, cmd, count = 5, existing_flag='', max_count = 0):

        exist_record_dict = {}
        if os.path.exists(f'{output_file}.csv') and len(existing_flag):
            try:
                df_exist = pd.read_csv(f'{output_file}.csv')
                for i, row in df_exist.iterrows():
                    if row[existing_flag] != "Undisposed":
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

        if not max_count:
            max_count = len(documents)

        try:
            for i, doc in enumerate(documents):
                uuid = doc.get("uuid", "")
                if uuid not in exist_record_dict.keys():
                    # 定义要提取的字段列表
                    fields = ["uuid", "Title", "Abstract"]
                    # 一行批量提取所有字段
                    item = {field: doc.get(field, "") for field in fields}
                    body.append(item)
                    print(f'Ernie Processing abstract: {i + 1}/{len(documents)}')
                else:
                    print(f'Ernie Processing existed: {i + 1}/{len(documents)}')

                if ((i + 1) % count) == 0:
                    body_answer = self.extract(LiteratureReviewPrompt(body=body).get_prompt(cmd))
                    if isinstance(body_answer, list):
                        enhanced_docs.extend(body_answer)
                    body = []

                    if max_count <= count:
                        break
                    else:
                        max_count = max_count - count

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

    print(get_ernie_obj("hello"))
