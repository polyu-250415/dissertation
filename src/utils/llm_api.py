from llama_index.llms.deepseek import DeepSeek
from openai import OpenAI
from src.utils.llm_key import deepseek_key, gemini_key, qwen_key,kimi_key,ernie_api_k

deepseek_llm = DeepSeek(model="deepseek-chat", api_key=deepseek_key)

def get_deepseek_chat_obj(prompt):
    response = deepseek_llm.complete(prompt)
    return response.text

deepseek_client = OpenAI(
        api_key=deepseek_key,
        base_url="https://api.deepseek.com"
    )

def get_deepseek_r1_obj(prompt):

    messages = [{"role": "user", "content": prompt}]

    response = deepseek_client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages
    )

    # 获取思考过程和最终答案
    reasoning_content = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    return content

import google.generativeai as genai

genai.configure(api_key=gemini_key)
def get_gemini_obj():
    llm = genai.GenerativeModel("gemini-2.5-flash")
    return llm


qwen_client = OpenAI(
    api_key=qwen_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def get_qwen_obj(final_prompt):
    response = qwen_client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": final_prompt}],
                max_tokens=5000
            )

    return response.choices[0].message.content

kimi_client = OpenAI(
    api_key=kimi_key,
    base_url="https://api.moonshot.cn/v1"
)

def get_kimi_obj(final_prompt):
    resp = kimi_client.chat.completions.create(
        model="kimi-k2.6",
        messages=[{"role": "user", "content": final_prompt}]
    )

    return resp.choices[0].message.content



ernie_client = OpenAI(
    base_url='https://qianfan.baidubce.com/v2',
    api_key= ernie_api_k
)
def get_ernie_obj(final_prompt):
    resp = ernie_client.chat.completions.create(
        model="ernie-4.5-turbo-128k",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.8,
        top_p=0.8,
        extra_body={
            "penalty_score":1,
            "stop":[],
            "web_search":{
                "enable": False,
                "enable_trace": False
            }
        }
    )
    return resp.choices[0].message.content
