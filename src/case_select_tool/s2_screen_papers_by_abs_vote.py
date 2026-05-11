import pandas as pd
import os
import ast
from concurrent.futures import ThreadPoolExecutor

from src.case_select_tool.llm_mgmt.deepseek_api_interface import DeepSeekAPI
from src.case_select_tool.llm_mgmt.qwen_api_interface import QwenAPI
from src.case_select_tool.llm_mgmt.kimi_api_interface import KimiAPI
from src.case_select_tool.llm_mgmt.ernie_api_interface import ErnieAPI

class ScreenPaperCraw:

    """use LLM to judge the relevance of the papers. The principles are as follows:
    - use Deepseek to assess the relevance between topics discussed in papers and knowledge retention
    - review the result, and make a thread to choose highly relevant papers.
    """

    def __init__(self, cmd = "Cmd_Ext_Relevance", count = 1):
        self.cmd = cmd
        self.count = count
        self.paper_screen_t1 = '../data/papers/midput/screening_by_abs_t1/'
        self.paper_screen_t2 = '../data/papers/midput/screening_by_abs_t2/'
        if not os.path.exists(self.paper_screen_t2):
            os.makedirs(self.paper_screen_t2, exist_ok=True)
        if not os.path.exists(self.paper_screen_t1):
            os.makedirs(self.paper_screen_t1, exist_ok=True)
        pass

    def assess_relevance_by_deepseek(self):
        input_file = "../data/papers/midput/semi_structured_papers.json"
        output_file = f"{self.paper_screen_t1}screening_by_abstract_deepseek"

        DeepSeekAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count)

    def assess_relevance_by_qwen(self):
        input_file = "../data/papers/midput/semi_structured_papers.json"
        output_file = f"{self.paper_screen_t1}screening_by_abstract_qwen"

        QwenAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count)

    def assess_relevance_by_kimi(self):
        input_file = "../data/papers/midput/semi_structured_papers.json"
        output_file = f"{self.paper_screen_t1}screening_by_abstract_kimi"

        KimiAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count)

    def assess_relevance_by_ernie(self):
        input_file = "../data/papers/midput/semi_structured_papers.json"
        output_file = f"{self.paper_screen_t1}screening_by_abstract_ernie"

        ErnieAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count)

    @staticmethod
    def split_column_by_tag(df, tag_name = 'knowledge_flows'):
        df[tag_name] = df[tag_name].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.strip() not in ['', 'nan', 'None'] else []
        )
        all_tags = sorted(set(tag for tags in df[tag_name] for tag in tags))
        # 创建 0/1 矩阵
        for tag in all_tags:
            df[tag] = df[tag_name].apply(lambda x: 1 if tag in x else 0)

        return df

    @staticmethod
    def rename_column(df, tag):
        rename_dict = {
            'challenges': f'{tag}_challenges',
            'methods': f'{tag}_methods',
            'findings': f'{tag}_findings',
            'style': f'{tag}_style',
            'knowledge_type': f'{tag}_knowledge_type',
            'tech_type': f'{tag}_tech_type',
            'industries': f'{tag}_industries'
        }

        df = df.rename(columns=rename_dict)

        return df

    def label_papers_by_inclusion_criteria(self):
        input_deepseek_file = f"{self.paper_screen_t1}screening_by_abstract_deepseek.csv"
        input_qwen_file = f"{self.paper_screen_t1}screening_by_abstract_qwen.csv"
        input_ernie_file = f"{self.paper_screen_t1}screening_by_abstract_ernie.csv"
        output_deepseek_file = f"{self.paper_screen_t1}screening_by_abstract_deepseek_ic.csv"
        output_qwen_file = f"{self.paper_screen_t1}screening_by_abstract_qwen_ic.csv"
        output_ernie_file = f"{self.paper_screen_t1}screening_by_abstract_ernie_ic.csv"

        df_deepseek = pd.read_csv(input_deepseek_file)
        df_qwen = pd.read_csv(input_qwen_file)
        df_ernie = pd.read_csv(input_ernie_file)

        deepseek_condition = (
                (df_deepseek['kr_flag'] == 'Yes') &
                (df_deepseek['DT_flag'] == 'Yes') &
                (df_deepseek['Doc_type'].isin(['Case Study','case study', 'Empirical Study',"empirical study"]))
        )
        # 满足条件赋值为 1/True，不满足为 0/False（可自定义）
        df_deepseek['ic_label'] = deepseek_condition
        df_deepseek.to_csv(output_deepseek_file, index=False)

        qwen_condition = (
                (df_qwen['kr_flag'] == 'Yes') &
                (df_qwen['DT_flag'] == 'Yes') &
                (df_qwen['Doc_type'].isin(['Case Study','case study', 'Empirical Study',"empirical study"]))
        )
        # 满足条件赋值为 1/True，不满足为 0/False（可自定义）
        df_qwen['ic_label'] = qwen_condition
        df_qwen.to_csv(output_qwen_file, index=False)

        ernie_condition = (
                (df_qwen['kr_flag'] == 'Yes') &
                (df_qwen['DT_flag'] == 'Yes') &
                (df_qwen['Doc_type'].isin(['Case Study','case study', 'Empirical Study',"empirical study"]))
        )
        # 满足条件赋值为 1/True，不满足为 0/False（可自定义）
        df_ernie['ic_label'] = ernie_condition
        df_ernie.to_csv(output_ernie_file, index=False)


    def select_papers_by_relevance(self):
        input_file = "../data/papers/midput/semi_structured_papers.csv"
        input_deepseek_file = f"{self.paper_screen_t1}screening_by_abstract_deepseek_ic.csv"
        input_qwen_file = f"{self.paper_screen_t1}screening_by_abstract_qwen_ic.csv"
        input_ernie_file = f"{self.paper_screen_t1}screening_by_abstract_ernie_ic.csv"
        output_file = f"{self.paper_screen_t1}screening_by_abstract"

        df_combined = pd.read_csv(input_file)[['uuid', 'Title', 'Abstract', 'DOI Link', 'Publication title']]
        df_deepseek = pd.read_csv(input_deepseek_file)
        df_qwen = pd.read_csv(input_qwen_file)
        df_ernie = pd.read_csv(input_ernie_file)

        df_deepseek = df_deepseek[["uuid", "kr_flag", "kr_evidence", "TK_normalized", "DT_flag", "DT_evidence", "DT_normalized", "ic_label"]]
        df_qwen = df_qwen[["uuid", "kr_flag", "kr_evidence", "TK_normalized", "DT_flag", "DT_evidence", "DT_normalized", "ic_label"]]
        df_ernie = df_ernie[["uuid", "kr_flag", "kr_evidence", "TK_normalized", "DT_flag", "DT_evidence", "DT_normalized", "ic_label"]]

        df_ernie = df_ernie.add_prefix('ernie_')
        df_ernie = df_ernie.rename(columns={'ernie_uuid': 'uuid'})  # 主键保留原名

        # 1. 给两个表的列统一添加前缀（排除主键Title）
        df_deepseek = df_deepseek.add_prefix('deepseek_')
        df_deepseek = df_deepseek.rename(columns={'deepseek_uuid': 'uuid'})  # 主键保留原名

        df_qwen = df_qwen.add_prefix('qwen_')
        df_qwen = df_qwen.rename(columns={'qwen_uuid': 'uuid'})

        # 2. 合并（和你原来逻辑一致）
        df_combined = pd.merge(df_combined, df_deepseek, on='uuid', how='left')
        df_combined = pd.merge(df_combined, df_qwen, on='uuid', how='left')
        df_combined = pd.merge(df_combined, df_ernie, on='uuid', how='left')

        # 3. 【关键】列交叉排序：chatgpt_xxx 和 gemini_xxx 成对相邻
        # 提取所有列名
        all_cols = df_combined.columns.tolist()
        # 分离出非对比列（如Title、原有列）和对比列
        base_cols = [c for c in all_cols if not c.startswith(('ernie_', 'deepseek_', 'qwen_'))]
        # 生成交叉排序的列
        sorted_cols = []
        # 遍历所有deepseek开头的列，配对qwen列
        for col in [c for c in all_cols if c.startswith('ernie_')]:
            suffix = col.replace('ernie_', '')
            deepseek_col = f'deepseek_{suffix}'
            if deepseek_col in all_cols:
                sorted_cols.extend([col, deepseek_col])

            qwen_col = f'qwen_{suffix}'
            if qwen_col in all_cols:
                sorted_cols.extend([qwen_col])

        # 最终列顺序：基础列 + 交叉对比列
        df_combined = df_combined[base_cols + sorted_cols]
        df_combined.to_csv(f"{output_file}.csv", index=False)

        cols = ["deepseek_ic_label",
                "qwen_ic_label",
                "ernie_ic_label"]
        filtered_df = df_combined[(df_combined[cols] == True).sum(axis=1) >= 2]
        audit_df = df_combined[(df_combined[cols] == True).sum(axis=1) >= 1]

        # filtered_df.to_csv(f"{output_file}_filtering.csv", index=False)

        filtered_df.to_csv(self.paper_screen_t2 + f"papers_combined_screening.csv",   index=False)

        audit_df = audit_df[~audit_df.apply(tuple, axis=1).isin(filtered_df.apply(tuple, axis=1))]
        audit_df.to_csv(self.paper_screen_t2 + f"papers_combined_auditing.csv", index=False)

    def assess_relevance_parallel(obj):
        """
        并行执行 Qwen 和 Kimi 相关性评估
        :param obj: ScreenPaperCraw 实例对象
        """

        def run_deepseek():
            print("Start evaluating by DeepSeek...")
            obj.assess_relevance_by_deepseek()

        def run_qwen():
            print("Start evaluating by Qwen...")
            obj.assess_relevance_by_qwen()

        def run_kimi():
            print("Start evaluating by Kimi...")
            obj.assess_relevance_by_kimi()

        def run_ernie():
            print("Start evaluating by Kimi...")
            obj.assess_relevance_by_kimi()

        # 并行执行
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(run_deepseek)
            executor.submit(run_qwen)
            executor.submit(run_ernie)

if __name__ == '__main__':
    obj = ScreenPaperCraw(cmd= 'Cmd_Screen_by_Abstract', count=10)
    # obj.assess_relevance_parallel()
    obj.label_papers_by_inclusion_criteria()
    obj.select_papers_by_relevance()