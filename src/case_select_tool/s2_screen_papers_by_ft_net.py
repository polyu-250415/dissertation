import os.path

import pandas as pd
import numpy as np

class ScreenPapersFT(object):
    def __init__(self):
        self.work_dir = '../data/papers/midput/'
        self.paper_screen_t2 = '../data/papers/midput/screening_by_abs_t2/'
        self.paper_screen_t3 = '../data/papers/midput/screening_by_abs_t3/'
        self.paper_screen_ft_t1 = '../data/papers/midput/screening_by_ft_t1/'
        self.Screening_papers_name_prefix = self.paper_screen_t3 + 'Screening_papers_by_'
        if not os.path.exists(self.paper_screen_ft_t1):
            os.makedirs(self.paper_screen_ft_t1, exist_ok=True)
        pass

    def split_papers_by_batch(self, task, batch_num=3):
        df_paper = pd.read_csv(self.paper_screen_t2 + 'papers_combined_screening.csv')
        df_paper = df_paper[['uuid', 'Title', 'DOI Link']]
        batches = np.array_split(df_paper, batch_num)

        # 5. 逐个写入 CSV
        for i, df_output in enumerate(batches):

            # 保存 CSV
            filename = f"{self.paper_screen_ft_t1}audit_materials_{task}_{i}.csv"
            df_output.to_csv(filename, index=False)

        print("已按批次 + 指定列 写入完成！")
        pass

    def split_papers_by_batch_1(self, task, batch_num=3):
        df_paper = pd.read_csv(self.paper_screen_t3 + 'papers_combined_auditing_kr_flag.csv')
        df_paper = df_paper[['uuid', 'Title', 'DOI Link']]
        batches = np.array_split(df_paper, batch_num)

        # 5. 逐个写入 CSV
        for i, df_output in enumerate(batches):

            # 保存 CSV
            filename = f"{self.paper_screen_ft_t1}audit_materials_{task}_{i}.csv"
            df_output.to_csv(filename, index=False)

        print("已按批次 + 指定列 写入完成！")
        pass

    def combine_papers_by_batch(self, task, batch_num=3):

        df_voting = pd.DataFrame()
        df_auditing = pd.DataFrame()

        for index in range(batch_num):

            if os.path.exists(self.paper_screen_ft_t1 + f'audit_materials_{task}_{index}_Gemini.csv'):
                df_voting_segment = pd.read_csv(self.paper_screen_ft_t1 + f'audit_materials_{task}_{index}_Gemini.csv')
                df_voting = pd.concat([df_voting, df_voting_segment])

            if os.path.exists(self.paper_screen_ft_t1 + f'audit_materials_{task}_audit_{index}_Gemini.csv'):
                df_auditing_segment = pd.read_csv(self.paper_screen_ft_t1 + f'audit_materials_{task}_audit_{index}_Gemini.csv')
                df_auditing = pd.concat([df_auditing, df_auditing_segment])

        df_combined = pd.concat([df_voting, df_auditing])

        df_combined.to_csv(self.paper_screen_ft_t1 + f'audit_materials_{task}_combined.csv', index=False)
        print(f"Total number: {len(df_combined)}")

        cols = ["Knowledge_capture_retention_discussed",
                "Digital_technology_used_for_capture_retention"]
        df_combined = df_combined[(df_combined[cols] == "Yes").sum(axis=1) >= 2]
        print(f"After screening flag: {len(df_combined)}")

        df_combined = df_combined[df_combined['Doc_Type'].isin(['empirical study', 'case study'])]
        print(f"After screening doctype: {len(df_combined)}")

        df_combined.to_csv(self.paper_screen_ft_t1 + f'papers_{task}_waitlist.csv', index=False)


if __name__ == '__main__':
    obj = ScreenPapersFT()

    # task = 'doctype'
    # obj.split_papers_by_batch(task, batch_num=2)

    # task = 'doctype_audit'
    # obj.split_papers_by_batch_1(task, batch_num=1)

    task = 'doctype'
    obj.combine_papers_by_batch(task, batch_num=2)