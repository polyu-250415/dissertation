import pandas as pd
import os
import ast
from concurrent.futures import ThreadPoolExecutor
from statsmodels.stats.inter_rater import fleiss_kappa
from sklearn.metrics import cohen_kappa_score
import numpy as np
from irrCAC.raw import CAC

from src.utils.llm_mgmt.deepseek_api_interface import DeepSeekAPI
from src.utils.llm_mgmt.qwen_api_interface import QwenAPI
from src.utils.llm_mgmt.kimi_api_interface import KimiAPI
from src.utils.llm_mgmt.ernie_api_interface import ErnieAPI

class ScreenPaperCraw:

    """use LLM to judge the relevance of the papers. The principles are as follows:
    - use Deepseek to assess the relevance between topics discussed in papers and knowledge retention
    - review the result, and make a thread to choose highly relevant papers.
    """

    def __init__(self, cmd = "Cmd_Ext_Relevance", count = 1, max_count = 0):
        self.cmd = cmd
        self.count = count
        self.max_count = max_count
        self.paper_screen_t1 = '../data/papers/midput/screening_by_abs_t1/'
        self.paper_screen_t2 = '../data/papers/midput/screening_by_abs_t2/'
        if not os.path.exists(self.paper_screen_t2):
            os.makedirs(self.paper_screen_t2, exist_ok=True)
        if not os.path.exists(self.paper_screen_t1):
            os.makedirs(self.paper_screen_t1, exist_ok=True)
        pass

    def assess_relevance_by_deepseek(self, input_file,
                                     output_file_name = 'screening_by_abstract_deepseek_initial.csv',):
        output_file = f"{self.paper_screen_t1}{output_file_name}"

        DeepSeekAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count,
                                    max_count=self.max_count)

    def assess_relevance_by_qwen(self, input_file,
                                output_file_name='screening_by_abstract_qwen_initial.csv'):
        output_file = f"{self.paper_screen_t1}{output_file_name}"

        QwenAPI().batch_extract(input_file,
                                output_file,
                                self.cmd,
                                count=self.count,
                                max_count=self.max_count)

    def assess_relevance_by_kimi(self, input_file,
                                 output_file_name='screening_by_abstract_kimi_initial.csv'):
        output_file = f"{self.paper_screen_t1}{output_file_name}"

        KimiAPI().batch_extract(input_file,
                                    output_file,
                                    self.cmd,
                                    count=self.count)

    def assess_relevance_by_ernie(self, input_file,
                                  output_file_name = 'screening_by_abstract_ernie_initial.csv'):
        output_file = f"{self.paper_screen_t1}{output_file_name}"

        ErnieAPI().batch_extract(input_file,
                                 output_file,
                                 self.cmd,
                                 count=self.count,
                                 max_count=self.max_count)

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
                (df_deepseek['article_type'].isin(['Case Study','case_study', 'Empirical Study',"empirical study"]))
        )
        # 满足条件赋值为 1/True，不满足为 0/False（可自定义）
        df_deepseek['ic_label'] = deepseek_condition
        df_deepseek = df_deepseek.sort_values(by="uuid", ascending=True).reset_index(drop=True)
        df_deepseek.to_csv(output_deepseek_file, index=False)

        qwen_condition = (
                (df_qwen['kr_flag'] == 'Yes') &
                (df_qwen['DT_flag'] == 'Yes') &
                (df_qwen['article_type'].isin(['Case Study','case_study', 'Empirical Study',"empirical study"]))
        )
        # 满足条件赋值为 1/True，不满足为 0/False（可自定义）
        df_qwen['ic_label'] = qwen_condition
        df_qwen = df_qwen.sort_values(by="uuid", ascending=True).reset_index(drop=True)
        df_qwen.to_csv(output_qwen_file, index=False)

        ernie_condition = (
                (df_ernie['kr_flag'] == 'Yes') &
                (df_ernie['DT_flag'] == 'Yes') &
                (df_ernie['article_type'].isin(['Case Study','case_study', 'Empirical Study',"empirical study"]))
        )
        # 满足条件赋值为 1/True，不满足为 0/False（可自定义）
        df_ernie['ic_label'] = ernie_condition
        df_ernie = df_ernie.sort_values(by="uuid", ascending=True).reset_index(drop=True)
        df_ernie.to_csv(output_ernie_file, index=False)


    def select_papers_by_relevance(self):
        input_file = "../data/papers/midput/semi_structured_papers.csv"
        input_deepseek_file = f"{self.paper_screen_t1}screening_by_abstract_deepseek_ic.csv"
        input_qwen_file = f"{self.paper_screen_t1}screening_by_abstract_qwen_ic.csv"
        input_ernie_file = f"{self.paper_screen_t1}screening_by_abstract_ernie_ic.csv"
        output_file = f"{self.paper_screen_t1}screening_by_abstract.csv"

        df_combined = pd.read_csv(input_file)[['uuid', 'Title', 'Abstract', 'DOI Link', 'Publication title']]
        df_deepseek = pd.read_csv(input_deepseek_file)
        df_qwen = pd.read_csv(input_qwen_file)
        df_ernie = pd.read_csv(input_ernie_file)

        df_deepseek = df_deepseek[["uuid", "kr_flag", "kr_evidence", "TK_normalized", "DT_flag", "DT_evidence", "DT_normalized", "article_type","ic_label"]]
        df_qwen = df_qwen[["uuid", "kr_flag", "kr_evidence", "TK_normalized", "DT_flag", "DT_evidence", "DT_normalized", "article_type","ic_label"]]
        df_ernie = df_ernie[["uuid", "kr_flag", "kr_evidence", "TK_normalized", "DT_flag", "DT_evidence", "DT_normalized", "article_type","ic_label"]]

        df_ernie = df_ernie.add_prefix('ernie_')
        df_ernie = df_ernie.rename(columns={'ernie_uuid': 'uuid'})

        df_deepseek = df_deepseek.add_prefix('deepseek_')
        df_deepseek = df_deepseek.rename(columns={'deepseek_uuid': 'uuid'})

        df_qwen = df_qwen.add_prefix('qwen_')
        df_qwen = df_qwen.rename(columns={'qwen_uuid': 'uuid'})

        df_combined = pd.merge(df_combined, df_deepseek, on='uuid', how='left')
        df_combined = pd.merge(df_combined, df_qwen, on='uuid', how='left')
        df_combined = pd.merge(df_combined, df_ernie, on='uuid', how='left')

        all_cols = df_combined.columns.tolist()
        base_cols = [c for c in all_cols if not c.startswith(('ernie_', 'deepseek_', 'qwen_'))]

        sorted_cols = []

        for col in [c for c in all_cols if c.startswith('deepseek_')]:
            suffix = col.replace('deepseek_', '')

            qwen_col = f'qwen_{suffix}'
            if qwen_col in all_cols:
                sorted_cols.extend([col, qwen_col])

        df_combined = df_combined[base_cols + sorted_cols]
        df_combined.to_csv(f"{output_file}", index=False)

        cols = ["deepseek_ic_label",
                "qwen_ic_label"]
        filtered_df = df_combined[(df_combined[cols] == True).sum(axis=1) == 2]
        audit_df = df_combined[(df_combined[cols] == True).sum(axis=1) >= 1]
        removed_df = df_combined[(df_combined[cols] == True).sum(axis=1) == 0]

        filtered_df.to_csv(self.paper_screen_t2 + f"waiting_for_accept_papers.csv",   index=False)

        audit_df = audit_df[~audit_df.apply(tuple, axis=1).isin(filtered_df.apply(tuple, axis=1))]
        audit_df.to_csv(self.paper_screen_t2 + f"waiting_for_audit_papers.csv", index=False)

        removed_df.to_csv(self.paper_screen_t2 + f"waiting_for_removed_papers.csv", index=False)

    def assess_relevance_parallel(obj, input_file):
        """
        并行执行 DeepSeek, Qwen 和 ERNIE 相关性评估
        :param obj: ScreenPaperCraw 实例对象
        """

        def run_deepseek():
            print("Start evaluating by DeepSeek...")
            obj.assess_relevance_by_deepseek(input_file)

        def run_qwen():
            print("Start evaluating by Qwen...")
            obj.assess_relevance_by_qwen(input_file)

        def run_ernie():
            print("Start evaluating by ERNIE...")
            obj.assess_relevance_by_ernie(input_file)

        # 并行执行
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(run_deepseek)
            executor.submit(run_qwen)
            executor.submit(run_ernie)

    def check_missed_records(self):

        input_file = "../data/papers/midput/semi_structured_papers.csv"
        input_deepseek_file = f"{self.paper_screen_t1}screening_by_abstract_deepseek_initial.csv"
        input_qwen_file = f"{self.paper_screen_t1}screening_by_abstract_qwen_initial.csv"
        input_ernie_file = f"{self.paper_screen_t1}screening_by_abstract_ernie_initial.csv"

        df_combined = pd.read_csv(input_file)
        df_deepseek = pd.read_csv(input_deepseek_file)
        df_qwen = pd.read_csv(input_qwen_file)
        df_ernie = pd.read_csv(input_ernie_file)

        uuid_df_deepseek = df_deepseek["uuid"].unique()
        df_deepseek_missed = df_combined[~df_combined["uuid"].isin(uuid_df_deepseek)]
        if df_deepseek_missed.shape[0]:
            df_deepseek_missed.to_csv(f"{self.paper_screen_t1}deepseek_missed.csv", index=False)
            obj.assess_relevance_by_deepseek(f"{self.paper_screen_t1}deepseek_missed.csv",
                                         output_file_name="screening_by_abstract_deepseek_missed.csv")
            df_tmp = pd.read_csv(self.paper_screen_t1 + "screening_by_abstract_deepseek_missed.csv")
            df_deepseek = pd.concat([df_deepseek, df_tmp], axis=0)
            df_deepseek.drop_duplicates(subset=["uuid"], keep="first", inplace=True)
        df_deepseek.to_csv(self.paper_screen_t1 + "screening_by_abstract_deepseek.csv", index=False)

        uuid_df_qwen = df_qwen["uuid"].unique()
        df_qwen_missed = df_combined[~df_combined["uuid"].isin(uuid_df_qwen)]
        if df_qwen_missed.shape[0]:
            df_qwen_missed.to_csv(f"{self.paper_screen_t1}qwen_missed.csv", index=False)
            obj.assess_relevance_by_qwen(f"{self.paper_screen_t1}qwen_missed.csv",
                                         output_file_name="screening_by_abstract_qwen_missed.csv")
            df_tmp = pd.read_csv(self.paper_screen_t1 + "screening_by_abstract_qwen_missed.csv")
            df_qwen = pd.concat([df_qwen, df_tmp], axis=0)
            df_qwen.drop_duplicates(subset=["uuid"], keep="first", inplace=True)
        df_qwen.to_csv(self.paper_screen_t1 + "screening_by_abstract_qwen.csv", index=False)

        """uuid_df_ernie = df_ernie["uuid"].unique()
        df_ernie_missed = df_combined[~df_combined["uuid"].isin(uuid_df_ernie)]
        if df_ernie_missed.shape[0]:
            df_ernie_missed.to_csv(f"{self.paper_screen_t1}ernie_missed.csv", index=False)
            obj.assess_relevance_by_ernie(f"{self.paper_screen_t1}ernie_missed.csv",
                                         output_file_name="screening_by_abstract_ernie_missed.csv")
            df_tmp = pd.read_csv(self.paper_screen_t1 + "screening_by_abstract_ernie_missed.csv")
            df_ernie = pd.concat([df_ernie, df_tmp], axis=0)
            df_ernie.drop_duplicates(subset=["uuid"], keep="first", inplace=True)
        df_ernie.to_csv(self.paper_screen_t1 + "screening_by_abstract_ernie.csv", index=False)"""

    def pairwise_cohen_kappa(self, label_col='ic_label'):
        file1 = f"{self.paper_screen_t1}screening_by_abstract_deepseek_ic.csv"
        file2 = f"{self.paper_screen_t1}screening_by_abstract_qwen_ic.csv"

        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        for index in range(len(df1)):
            if df1.loc[index]['uuid'] != df2.loc[index]['uuid']:
                print(f"序列错误 {index}")
                return

        y1 = df1[label_col].values
        y2 = df2[label_col].values
        kappa_12 = cohen_kappa_score(y1, y2)

        # 返回结果
        result = {
            ('cohen_kappa', 'DeepSeek', 'Qwen'): kappa_12
        }

        for pair, kappa in result.items():
            print(f"{pair}: {kappa:.4f}")

    @staticmethod
    def scott_pi_from_labels(label_a, label_b):
        """
        根据两个评估者的标签列表计算 Scott's Pi。
        参数:
            label_a, label_b: 列表或 Series，长度相同，包含类别标签（可以是数字或字符串）
        返回:
            float: Scott's Pi 系数
        """
        if len(label_a) != len(label_b):
            raise ValueError("两个标签列表长度不一致")

        # 获取所有可能的类别（取两个列表的并集）
        categories = sorted(set(label_a) | set(label_b))
        n_cat = len(categories)

        # 构建混淆矩阵
        # 行: label_a, 列: label_b
        cat_to_idx = {cat: i for i, cat in enumerate(categories)}
        confusion = np.zeros((n_cat, n_cat), dtype=float)
        for a, b in zip(label_a, label_b):
            i = cat_to_idx[a]
            j = cat_to_idx[b]
            confusion[i, j] += 1

        total = np.sum(confusion)

        # 观察一致性 (P_o)
        po = np.trace(confusion) / total

        # 期望一致性 (P_e) - Scott's Pi 使用边际平均
        row_sums = np.sum(confusion, axis=1)
        col_sums = np.sum(confusion, axis=0)
        # 每个类别的总体比例 = (行边际 + 列边际) / (2 * total)
        category_proportions = (row_sums + col_sums) / (2 * total)
        pe = np.sum(category_proportions ** 2)

        # 处理边界情况
        if pe == 1.0:
            return 1.0
        pi = (po - pe) / (1 - pe)
        return pi

    def pairwise_scott_pi(self, label_col='ic_label'):
        """
        计算三个模型（DeepSeek, Qwen, ERNIE）两两之间的 Scott's Pi。
        用法与您原来的 pairwise_cohen_kappa 完全一致。
        """
        file1 = f"{self.paper_screen_t1}screening_by_abstract_deepseek_ic.csv"
        file2 = f"{self.paper_screen_t1}screening_by_abstract_qwen_ic.csv"

        df1 = pd.read_csv(file1)[label_col]
        df2 = pd.read_csv(file2)[label_col]

        if not (len(df1) == len(df2)):
            raise ValueError("文件的行数不一致，请检查记录是否对齐。")

        # 计算两两 Scott's Pi
        pi_12 = self.scott_pi_from_labels(df1, df2)

        result = {
            ('Scott\'s Pi', 'DeepSeek', 'Qwen'): pi_12
        }

        for pair, value in result.items():
            print(f"{pair}: {value:.4f}")

        return result

    def evaluate_consistent(self, label_col='ic_label'):
        file1 = f"{self.paper_screen_t1}screening_by_abstract_deepseek_ic.csv"
        file2 = f"{self.paper_screen_t1}screening_by_abstract_qwen_ic.csv"

        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        for index in range(len(df1)):
            if df1.loc[index]['uuid'] != df2.loc[index]['uuid']:
                print(f"序列错误 {index}")
                return

        y1 = df1[label_col].values
        y2 = df2[label_col].values

        positive_count = 0
        negative_count = 0
        confusion_count = 0
        for index in range(len(y1)):
            if (y1[index] == 1
                    and y2[index] == 1):
                positive_count += 1
                continue

            if (y1[index] == 0
                    and y2[index] == 0):
                negative_count += 1
                continue

            confusion_count += 1

        print(f"DeepSeek Positive Rate: {sum(y1)} / {len(y1)} = {sum(y1) / len(y1) :.2f}")
        print(f"Qwen Positive Rate: {sum(y2)} / {len(y1)} = {sum(y2) / len(y1) :.2f}")
        print(f"Total Confused Rate: {confusion_count} / {len(y1)} = {confusion_count / len(y1) :.2f}")
        print(f"Total Consistency Rate: {positive_count + negative_count} / {len(y1)} = {(positive_count + negative_count) / len(y1) :.2f}")

    def random_choice_hr_sample(self, input_file, output_file, ratio=0.1):
        df = pd.read_csv(input_file)
        df_sample = df.sample(frac=ratio, random_state=42)
        df_sample.to_csv(output_file, index=False)


if __name__ == '__main__':
    stage = 5
    obj = ScreenPaperCraw(cmd= 'Cmd_Screen_by_Abstract', count=6, max_count=2000)

    if stage <= 1:
        input_file = "../data/papers/midput/semi_structured_papers.json"
        obj.assess_relevance_parallel(input_file)

    if stage <= 2:
        obj.check_missed_records()

    if stage <= 3:
        obj.label_papers_by_inclusion_criteria()
        obj.select_papers_by_relevance()

    if stage <= 4:
        obj.pairwise_scott_pi(label_col='ic_label')
        obj.pairwise_cohen_kappa(label_col='ic_label')
        obj.evaluate_consistent(label_col='ic_label')

    if stage <= 5:
        input_file = obj.paper_screen_t2 + "waiting_for_removed_papers.csv"
        output_file = obj.paper_screen_t2 + "waiting_for_human_review.csv"
        obj.random_choice_hr_sample(input_file, output_file, ratio=0.1)

