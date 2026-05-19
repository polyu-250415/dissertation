import json, os, re

import pandas as pd

from src.utils.llm_api import get_deepseek_chat_obj,get_deepseek_r1_obj
from src.utils.llm_mgmt.prompt_generator import LiteratureReviewPrompt
from src.utils.llm_mgmt.deepseek_local_api import chat_with_deepseek

class DeepSeekAPI:
    def __init__(self, model_name = 'Chat'):
        if model_name == "Chat":
            self.model_func = get_deepseek_chat_obj
        else:
            self.model_func = get_deepseek_r1_obj

    @staticmethod
    def r1_infer(prompt):
        return get_deepseek_r1_obj(prompt)

    @staticmethod
    def r1_local_infer(prompt):
        return chat_with_deepseek(prompt)

    def extract(self, prompt: str) -> dict:

        try:
            response = self.model_func(prompt)
            response = re.sub(r'^```(?:json)?\s*\n?', '', response, flags=re.IGNORECASE)
            response = re.sub(r'\n?```\s*$', '', response)
            result = json.loads(response.strip())
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
                    print(f'Deepseek Processing abstract: {i + 1}/{len(documents)}')
                else:
                    print(f'Deepseek Processing existed: {i + 1}/{len(documents)}')

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

    input_file = "../../data/papers/midput//screening_by_abs_t2/papers_2.json"
    output_file = "../../data/papers/midput/screening_by_abs_t2/papers_2_deepseek.csv"
    cmd = "Cmd_Screen_by_Abstract"

    print(get_deepseek_r1_obj("hello"))

