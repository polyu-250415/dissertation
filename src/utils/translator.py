from transformers import MarianMTModel, MarianTokenizer
import pandas as pd

# 加载模型（首次自动下载）
model_name = "Helsinki-NLP/opus-mt-en-zh"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

def translate(text: str) -> str:
    inputs = tokenizer(text, return_tensors="pt", padding=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)


def translate_with_truncation(text):
    """
    自动截断超出部分（简单快速）
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,  # 启用截断
            max_length=512  # 明确指定最大长度
        )
        translated = model.generate(**inputs)
        return tokenizer.decode(translated[0], skip_special_tokens=True)
    except Exception as e:
        print(f"翻译失败: {e}")
        return ""