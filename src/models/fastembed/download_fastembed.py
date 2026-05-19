import os
from fastembed import TextEmbedding

# ==================
# 配置（自己改）
# ==================
MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 你要用的模型
CACHE_DIR = "bge-small-en-v1.5"  # 缓存目录

# 创建缓存目录
os.makedirs(CACHE_DIR, exist_ok=True)

# ==============================================
# ✅ 这一行会自动联网下载模型 → 缓存到 CACHE_DIR
# ==============================================
embedder = TextEmbedding(
    model_name=MODEL_NAME,
    cache_dir=CACHE_DIR,
    local_files_only=False  # 允许联网下载
)

print(f"\n✅ 模型下载完成！")
print(f"📂 缓存路径：{CACHE_DIR}")