import os

import pandas as pd
import numpy as np

class RevealRelations(object):
    def __init__(self, ):
        self.paper_set_dir = '../data/papers/midput/screening_by_abs_t1/'
        self.screening_paper_set = self.paper_set_dir + 'semi_structural_papers_combined_screening.csv'
        self.paper_extraction_dir = '../data/papers/midput/screening_by_abs_t2/'
        self.paper_extraction_t2_dir = '../data/papers/midput/paper_extraction_turn2/'
        pass

    @staticmethod
    def split_papers(file_path, output_dir, batch_size = 10):
        df = pd.read_csv(file_path)

        selected_columns = ["uuid", "Title","Abstract","DOI Link"]
        batches = np.array_split(df[selected_columns], batch_size)

        #逐个写入 CSV
        for i, df_output in enumerate(batches):
            # 保存 CSV
            filename = f"{output_dir}papers_{i}.csv"
            df_output.to_csv(filename, index=False)

        print("已按批次 + 指定列 写入完成！")

    @staticmethod
    def rename_column(df, tag):
        rename_dict = {"uuid":"uuid",
                       "Title": "Title"
        }

        for item in df.columns:
            if item not in rename_dict.keys():
                rename_dict[item] = item+'_' + tag

        df = df.rename(columns=rename_dict)

        return df

    def combine_papers_t1(self, batch_num=10):

        df_combined = pd.DataFrame()
        df_chatgpt = pd.DataFrame()
        df_gemini = pd.DataFrame()

        for i in range(0, batch_num):

            if not os.path.exists(self.paper_extraction_dir + f"papers_{i}.csv"):
                continue

            df_paper = pd.read_csv(self.paper_extraction_dir + f"papers_{i}.csv")
            df_combined = pd.concat([df_combined, df_paper], ignore_index=True)

            try:
                if os.path.exists(self.paper_extraction_dir + f"papers_{i}_gpt-5.2-thinking.csv"):
                    df_paper_chatgpt = pd.read_csv(self.paper_extraction_dir + f"papers_{i}_gpt-5.2-thinking.csv")
                    df_chatgpt = pd.concat([df_chatgpt, df_paper_chatgpt], ignore_index=True)

                if os.path.exists(self.paper_extraction_dir + f"papers_{i}_Gemini.csv"):
                    df_paper_gemini = pd.read_csv(self.paper_extraction_dir + f"papers_{i}_Gemini.csv")
                    df_gemini = pd.concat([df_gemini, df_paper_gemini], ignore_index=True)

            except Exception as e:
                print(f"  - Error reading batch no {i}: {e}")
                continue

        # 1. 给两个表的列统一添加前缀（排除主键Title）
        df_chatgpt = df_chatgpt.add_prefix('chatgpt_')
        df_chatgpt = df_chatgpt.rename(columns={'chatgpt_Title': 'Title'})  # 主键保留原名

        df_gemini = df_gemini.add_prefix('gemini_')
        df_gemini = df_gemini.rename(columns={'gemini_Title': 'Title'})

        # 2. 合并（和你原来逻辑一致）
        df_combined = pd.merge(df_combined, df_gemini, on='Title', how='left')
        df_combined = pd.merge(df_combined, df_chatgpt, on='Title', how='left')

        # 3. 【关键】列交叉排序：chatgpt_xxx 和 gemini_xxx 成对相邻
        # 提取所有列名
        all_cols = df_combined.columns.tolist()
        # 分离出非对比列（如Title、原有列）和对比列
        base_cols = [c for c in all_cols if not c.startswith(('chatgpt_', 'gemini_'))]
        # 生成交叉排序的列
        sorted_cols = []
        # 遍历所有chatgpt开头的列，配对gemini列
        for col in [c for c in all_cols if c.startswith('gemini_')]:
            suffix = col.replace('gemini_', '')
            chatgpt_col = f'chatgpt_{suffix}'
            if chatgpt_col in all_cols:
                sorted_cols.extend([col, chatgpt_col])

        # 最终列顺序：基础列 + 交叉对比列
        df_combined = df_combined[base_cols + sorted_cols]
        df_combined.to_csv(self.paper_extraction_dir + f"papers_combined.csv", index=False)

        cols = ["chatgpt_Knowledge_capture_retention_discussed",
                "gemini_Knowledge_capture_retention_discussed"]
        filtered_df = df_combined[(df_combined[cols] == "Yes").sum(axis=1) >= 1]

        cols = ["chatgpt_Digital_technology_used_for_capture_retention",
                "gemini_Digital_technology_used_for_capture_retention"]
        filtered_df = filtered_df[(filtered_df[cols] == "Yes").sum(axis=1) >= 1]

        filtered_df.to_csv(self.paper_extraction_dir + "papers_combined_screening.csv",   index=False)


    def combine_papers_t2(self, batch_num=10):

        df_combined = pd.DataFrame()
        df_chatgpt = pd.DataFrame()
        df_gemini = pd.DataFrame()

        for i in range(0, batch_num):

            if not os.path.exists(self.paper_extraction_t2_dir + f"papers_{i}.csv"):
                continue

            df_paper = pd.read_csv(self.paper_extraction_t2_dir + f"papers_{i}.csv")
            df_combined = pd.concat([df_combined, df_paper], ignore_index=True)

            try:
                if os.path.exists(self.paper_extraction_t2_dir + f"papers_{i}_chatgpt.csv"):
                    df_paper_chatgpt = pd.read_csv(self.paper_extraction_t2_dir + f"papers_{i}_chatgpt.csv")
                    df_chatgpt = pd.concat([df_chatgpt, df_paper_chatgpt], ignore_index=True)

                if os.path.exists(self.paper_extraction_t2_dir + f"papers_{i}_Gemini.csv"):
                    df_paper_gemini = pd.read_csv(self.paper_extraction_t2_dir + f"papers_{i}_Gemini.csv")
                    df_gemini = pd.concat([df_gemini, df_paper_gemini], ignore_index=True)

            except Exception as e:
                print(f"  - Error reading batch no {i}: {e}")
                continue

        # 1. 给两个表的列统一添加前缀（排除主键Title）
        df_chatgpt = df_chatgpt.add_prefix('chatgpt_')
        df_chatgpt = df_chatgpt.rename(columns={'chatgpt_Title': 'Title'})  # 主键保留原名

        df_gemini = df_gemini.add_prefix('gemini_')
        df_gemini = df_gemini.rename(columns={'gemini_Title': 'Title'})

        # 2. 合并（和你原来逻辑一致）
        df_combined = pd.merge(df_combined, df_chatgpt, on='Title', how='left')
        df_combined = pd.merge(df_combined, df_gemini, on='Title', how='left')

        df_combined.to_csv(self.paper_extraction_t2_dir + f"papers_combined.csv", index=False)

        cols = ["chatgpt_Knowledge_capture_retention_discussed",
                "gemini_Knowledge_capture_retention_discussed"]
        filtered_df = df_combined[(df_combined[cols] == "Yes").sum(axis=1) >= 1]

        cols = ["chatgpt_Digital_technology_used_for_capture_retention",
                "gemini_Digital_technology_used_for_capture_retention"]
        filtered_df = filtered_df[(filtered_df[cols] == "Yes").sum(axis=1) >= 1]

        filtered_df.to_csv(self.paper_extraction_t2_dir + "papers_combined_screening.csv",   index=False)


if __name__ == '__main__':
    obj = RevealRelations()
    input_file = "../data/papers/midput/screening_by_abstract_filtering.csv"
    obj.split_papers(input_file, obj.paper_extraction_dir, batch_size=3)