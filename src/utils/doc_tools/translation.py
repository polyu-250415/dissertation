from kreuzberg import batch_extract_file_sync
from src.utils.llm_mgmt.deepseek_local_api import chat_with_deepseek
import os

path_dir = "/Users/meimei/Documents/Assignment/Dissertation/Reference doc"
for root, dirs, files in os.walk(path_dir):
    for file in files:
        if not file.endswith('.pdf'):
            continue

        file = os.path.join(root, file)
        results = batch_extract_file_sync([file])

        for result in results:
            file_txt = file.replace(".pdf", ".txt")
            with open(file_txt, 'w', encoding='utf-8') as f:
                f.write(result.content)

            prompt = f"请从文章中挖掘出知识留存相关的知识，知识持有者，技术实践，组织依赖，面临的挑战和限制：{result.content} 仅返回中文"
            ch = chat_with_deepseek(prompt)
            file_txt = file.replace(".pdf", "_ab_zh.txt")
            with open(file_txt, 'w', encoding='utf-8') as f:
                f.write(ch)

