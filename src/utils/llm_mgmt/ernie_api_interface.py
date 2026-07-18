import json, re

import pandas as pd

from src.utils.llm_api import get_ernie_obj
from src.utils.llm_mgmt.prompt_generator import LiteratureReviewPrompt

class ErnieAPI:
    def __init__(self, model_name = 'Chat'):
        pass

    @staticmethod
    def clean_llm_json_raw(raw: str) -> str:
        s = raw.replace(chr(160), " ")
        s = s.replace(r"\xa0", " ")
        s = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', s)
        s = re.sub(r'\s+', ' ', s)
        return s

    def extract(self, prompt: str) -> dict:

        try:
            response = get_ernie_obj(prompt)
            result = json.loads(self.clean_llm_json_raw(response))
            return result
        except Exception as e:
            print(f"Error processing extract: {e}")
            return []


    def batch_extract(self, input_file, output_file, cmd, count = 5, max_count = 0):

        df = pd.read_csv(input_file)
        record_num = df.shape[0]

        enhanced_docs = []
        body = []

        if not max_count:
            max_count = record_num

        try:
            for i, item in df.iterrows():
                # 定义要提取的字段列表
                fields = ["uuid", "Title", "Abstract"]
                # 一行批量提取所有字段
                item = {field: item[field] for field in fields}
                body.append(item)
                print(f'ERNIE Processing abstract: {i + 1}/{record_num}')

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
            print(f"ERNIE Error processing abstract: {e}")
            pass

        (pd.DataFrame(enhanced_docs).fillna("Undisposed").to_csv(f'{output_file}.csv', index=None))

if __name__ == '__main__':

    input_file = "../../data/papers/midput/screening_by_abs_t2/papers_2.json"
    output_file = "../../data/papers/midput/screening_by_abs_t2/papers_2_qwen.csv"
    cmd = "Cmd_Screen_by_Abstract"

    print(get_ernie_obj("hello"))
