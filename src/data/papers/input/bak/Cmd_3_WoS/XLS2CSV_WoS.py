import pandas as pd
import os


def xls_to_csv_filter_empty_cols(input_path, output_path=None):
    """
    将 .xls 文件转换为 .csv，并移除全为空值的列

    参数:
        input_path (str): 输入 .xls 文件路径
        output_path (str, optional): 输出 .csv 文件路径，默认为同名 .csv
    """
    # 自动设置输出路径
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.csv'

    # 读取 .xls 文件（xlrd 引擎）
    try:
        df = pd.read_excel(input_path, engine='xlrd')
        print(f"✓ 成功读取文件: {input_path}")
        print(f"  原始形状: {df.shape} (行×列)")
    except Exception as e:
        raise RuntimeError(f"读取文件失败: {e}")

    # 定义“空值”：包括 NaN、None、空字符串、仅空白字符
    def is_empty_col(series):
        return series.fillna('').astype(str).str.strip().eq('').all()

    # 识别非空列
    non_empty_cols = [col for col in df.columns if not is_empty_col(df[col])]
    removed_cols = set(df.columns) - set(non_empty_cols)

    # 过滤列
    df_filtered = df[non_empty_cols].copy()

    # 输出统计信息
    print(f"  移除空列: {len(removed_cols)} 列")
    if removed_cols:
        print(f"    被移除列名: {list(removed_cols)}")
    print(f"  保留列数: {len(non_empty_cols)}")
    print(f"  新形状: {df_filtered.shape}")

    # 保存为 CSV
    try:
        df_filtered.to_csv(output_path, index=False, encoding='utf-8-sig')  # utf-8-sig 支持 Excel 正确显示中文
        print(f"✓ 转换成功: {output_path}")
    except Exception as e:
        raise RuntimeError(f"保存 CSV 失败: {e}")


# ============ 使用示例 ============
if __name__ == "__main__":
    # 单文件转换
    xls_to_csv_filter_empty_cols("WoS-Cmd3-20260206.xls", "WoS-Cmd3-20260206.csv")

    # 批量转换当前目录下所有 .xls 文件
    # import glob
    # for xls_file in glob.glob("*.xls"):
    #     xls_to_csv_filter_empty_cols(xls_file)