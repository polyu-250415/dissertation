import os

import pandas as pd
import numpy as np


class ScreenPapersAuditor:
    def __init__(self):
        self.work_dir = '../data/papers/midput/'
        self.paper_screen_t2 = '../data/papers/midput/screening_by_abs_t2/'
        self.paper_screen_t3 = '../data/papers/midput/screening_by_abs_t3/'
        self.Screening_papers_name_prefix = self.paper_screen_t3 + 'Screening_papers_by_'
        pass


    @staticmethod
    def hide_model_name(col_name):
        col_name = col_name.replace('chatgpt', 'A')
        col_name = col_name.replace('deepseek', 'B')
        col_name = col_name.replace('gemini', 'C')
        col_name = col_name.replace('qwen', 'D')
        return col_name

    @staticmethod
    def rename_column(df, tag):
        rename_dict = {"uuid":"uuid"
        }

        for item in df.columns:
            if item not in rename_dict.keys():
                rename_dict[item] = item+'_' + tag

        df = df.rename(columns=rename_dict)

        return df

    def split_papers_by_batch(self, task, batch_num=50):

        df_paper = pd.read_csv(self.paper_screen_t3 + 'audit_materials.csv')
        batches = np.array_split(df_paper, batch_num)

        # 5. 逐个写入 CSV
        for i, df_output in enumerate(batches):

            # 保存 CSV
            filename = f"{self.paper_screen_t3}audit_materials_{task}_{i}.csv"
            df_output.to_csv(filename, index=False)

        print("已按批次 + 指定列 写入完成！")

    def prepare_audit_materials(self,
                                input_file,
                                context_cols,
                                opinion_clos,
                                task,
                                uuid_list):

        df = pd.read_csv(input_file)

        if len(uuid_list):
            df = df[df['uuid'].isin(uuid_list)]

        df_audit = pd.DataFrame()
        df_audit['uuid'] = df["uuid"].tolist()

        df_audit['combined_text'] = df.apply(
            lambda row: ' '.join([f'{c}：{row[c]}' for c in context_cols]),
            axis=1
        )

        for name in opinion_clos:
            df_audit[self.hide_model_name(name)] = df[name]


        df_audit.to_csv(self.paper_screen_t3 + f'audit_materials_{task}.csv', index=False)


    def combine_papers_by_batch(self, task, batch_num=50):

        df_audit= pd.DataFrame()
        for i in range(0, batch_num):
            df_audit_segment = pd.read_csv(self.paper_screen_t3 + f'audit_materials_{task}_{i}_chatgpt.csv')
            df_audit = pd.concat([df_audit, df_audit_segment],ignore_index=True)


        uuid_list = df_audit.loc[df_audit['Audited_Answer'] == 'Yes', 'uuid'].tolist()

        df_audit_paper = pd.read_csv(self.paper_screen_t2 + f"papers_combined_auditing.csv")

        df_audit_paper = df_audit_paper[df_audit_paper['uuid'].isin(uuid_list)]
        df_audit_paper.to_csv(self.paper_screen_t3 + f"papers_combined_auditing_{task}.csv", index=False)
        return df_audit_paper['uuid'].tolist()



if __name__ == '__main__':
    input_file = "../data/papers/midput/screening_by_abs_t2/papers_combined_auditing.csv"
    screen_papers = ScreenPapersAuditor()

    context_cols = ['Title', 'Abstract']
    opinion_clos_dict = [
        'kr_flag_chatgpt',
        'kr_evidence_chatgpt',
        'kr_flag_deepseek',
        'kr_evidence_deepseek',
        'kr_flag_gemini',
        'kr_evidence_gemini',
        'kr_flag_qwen',
        'kr_evidence_qwen']

    task = 'kr_flag'
    uuid_list = []
    screen_papers.prepare_audit_materials(input_file, context_cols, opinion_clos_dict, task, uuid_list)
    screen_papers.split_papers_by_batch(task, batch_num=3)
    uuid_list = screen_papers.combine_papers_by_batch(task, batch_num=3)

    opinion_clos_dict = [
        'DT_flag_chatgpt',
        'DT_evidence_chatgpt',
        'DT_flag_deepseek',
        'DT_evidence_deepseek',
        'DT_flag_gemini',
        'DT_evidence_gemini',
        'DT_flag_qwen',
        'DT_evidence_qwen']

    task = 'DT_flag'

    screen_papers.prepare_audit_materials(input_file, context_cols, opinion_clos_dict, task, uuid_list)
    screen_papers.split_papers_by_batch(task, batch_num=1)
    screen_papers.combine_papers_by_batch(task, batch_num=1)