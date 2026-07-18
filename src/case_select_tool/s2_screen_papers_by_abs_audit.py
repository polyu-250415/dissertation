import os
import json
import pandas as pd
import numpy as np
from src.utils.llm_mgmt.kimi_api_interface import KimiAPI
from src.utils.llm_mgmt.ernie_api_interface import get_ernie_obj

class ScreenPapersAuditor:
    def __init__(self):
        self.work_dir = '../data/papers/midput/'
        self.paper_screen_t2 = '../data/papers/midput/screening_by_abs_t2/'
        self.paper_screen_t3 = '../data/papers/midput/screening_by_abs_t3/'
        self.annotation_path = "../data/papers/midput/screening_by_annotation/"
        self.Screening_papers_name_prefix = self.paper_screen_t3 + 'Screening_papers_by_'

        if not os.path.exists(self.paper_screen_t3):
            os.makedirs(self.paper_screen_t3, exist_ok=True)

        if not os.path.exists(self.annotation_path):
            os.makedirs(self.annotation_path, exist_ok=True)


        pass


    @staticmethod
    def hide_model_name(col_name):
        col_name = col_name.replace('qwen', 'A')
        col_name = col_name.replace('ernie', 'B')
        col_name = col_name.replace('deepseek', 'C')

        return col_name

    @staticmethod
    def unhide_model_name(col_name):
        col_name = col_name.replace('A','qwen')
        col_name = col_name.replace('B','ernie')
        col_name = col_name.replace('C','deepseek')

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

        df_paper = pd.read_csv(self.paper_screen_t3 + f'audit_materials_{task}.csv')
        batches = np.array_split(df_paper, batch_num)

        # 5. 逐个写入 CSV
        for i, df_output in enumerate(batches):

            # 保存 CSV
            filename = f"{self.paper_screen_t3}audit_materials_{task}_{i}.csv"
            df_output.to_csv(filename, index=False)

        print("已按批次 + 指定列 写入完成！")

    @staticmethod
    def generate_audit_prompt_from_row(row,
                                       question1="Whether the article explicitly discussed or strongly implied how to "
                                                 "capture or retain knowledge from individuals or organization environment?",
                                       question2="Whether digital technologies are explicitly used to capture or retain tacit knowledge？",
                                       question3="What's the article type of this paper？"):
        """
        从CSV的一行数据生成完整学术审计Prompt
        """

        # 从CSV行提取数据
        uuid = row["uuid"]
        Title = row["Title"]
        combined_text = str(row["Abstract"]).replace('"', '\\"').replace("\n", " ")

        # 三位专家数据
        expert_A_ans_for_q1 = str(row["A_kr_flag"]).replace('"', '\\"')
        expert_A_ev_for_q1 = str(row["A_kr_evidence"]).replace('"', '\\"')

        expert_C_ans_for_q1 = str(row["C_kr_flag"]).replace('"', '\\"')
        expert_C_ev_for_q1 = str(row["C_kr_evidence"]).replace('"', '\\"')
        # 三位专家数据
        expert_A_ans_for_q2 = str(row["A_DT_flag"]).replace('"', '\\"')
        expert_A_ev_for_q2 = str(row["A_DT_evidence"]).replace('"', '\\"')

        expert_C_ans_for_q2 = str(row["C_DT_flag"]).replace('"', '\\"')
        expert_C_ev_for_q2 = str(row["C_DT_evidence"]).replace('"', '\\"')

        # 三位专家数据
        expert_A_ans_for_q3 = str(row["A_article_type"]).replace('"', '\\"')
        expert_C_ans_for_q3 = str(row["C_article_type"]).replace('"', '\\"')

        # 你完整的英文审计prompt模板（已优化占位符）
        prompt = f"""
    You are an expert academic audit assistant acting as a rigorous peer reviewer and evidence auditor. You have interdisciplinary expertise in knowledge management, emerging technologies for knowledge management, and computer science research classification.

    Task:
    Analyze the opinions from multiple experts, audit them against the factual information in the Context, 
    code each entry into a single JSON object within a unified output JSON structure, using a unified, conservative, evidence-based standard.

    Input dataset format:
    The input will be a JSON object.
    {{
      'uuid': {uuid},
      'Title': {Title},
      'Context': {combined_text},
      'questions': [
        {{
          'question_id': 1,
          'question_text': {question1},
          'expert_opinions': {{
            'expert_A': {expert_A_ans_for_q1}. {expert_A_ev_for_q1},
            'expert_C': {expert_C_ans_for_q1}. {expert_C_ev_for_q1}
          }}
        }},
        {{
          'question_id': 2,
          'question_text': {question2},
          'expert_opinions': {{
            'expert_A': {expert_A_ans_for_q2}. {expert_A_ev_for_q2},
            'expert_C': {expert_C_ans_for_q2}. {expert_C_ev_for_q2}
            }}
          }}
        }},
        {{
          'question_id': 3,
          'question_text': {question3},
          'expert_opinions': {{
            'expert_A': {expert_A_ans_for_q3},
            'expert_C': {expert_C_ans_for_q3}
          }}
        }}
      ]
    }}

    Core audit principles:
    1. Use only information supported by the Context. Treat the Context as the ground truth.Never infer facts not 
    clearly stated in the Context.
    2. Distinguish carefully between directly supported, partially supported, unsupported, contradicted, 
    and insufficient-context claims.
    3. If the Context is insufficient to verify a claim, mark it as 'Insufficient context'.
    4. Do not reward plausible reasoning if it is not supported by the Context.
    5. Be conservative. When uncertain, choose the less certain judgment.
    6. Evaluate both the answer and the evidence used to justify it.
    7. A correct conclusion with weak or unsupported evidence is not fully correct.

    Audit procedure:
    Step 1: Read the Context and identify the facts relevant to the fixed question.
    Step 2: Read each expert opinion separately.
    Step 3: For each expert, determine:
    - the main answer or claim
    - the evidence cited or implied
        - whether the answer is supported by the Context
        - whether the evidence is supported by the Context
        - whether the reasoning overreaches beyond the Context
    Step 4: Compare all experts only after determining the answer from the Context; do not use agreement among experts as evidence of correctness.
    Step 5: Produce one JSON structure recording the audit result.

    Audit Process Coding rule:
    expert_compliance: Coding for each expert; Use only one of the following categories to label each expert
    - Fully supported: the answer and evidence are clearly supported by the Context
    - Partially supported: the answer is partly correct, too broad, or supported by incomplete evidence
    - Unsupported: the claim or evidence is not found in the Context
    - Contradicted: the claim conflicts with the Context
    audit_evidence: Clearly state the reasons for your assessment of each expert's compliance, with a particular focus on the options you do not support; provide relevant background evidence that is closely aligned with your viewpoint, either in its original form or with appropriate paraphrasing.
    
    Audit Result Conding Rules:
    Audit Result: Summarize the auditing process for each expert, covering all three questions; use one of the following categories to label each expert
    - Fully Support: All answers and evidence are clearly supported by the context
    - Partial Support: The answers are partially correct, the expression is overly broad, or the evidence is incomplete
    - Not Support: Some or all claims or evidence are not found in the context;Some or all answers are unsupported or Contradicted

    Fixed output JSON structure:
    {{
      'uuid': 'string',
      'Title': 'string',
      'audit_processes': [
        {{
          'question_id': 1,
          'expert_compliance': {{
            'expert_A': 'string',
            'expert_C': 'string'
          }},
          'audit_evidence': 'string'
        }},
        {{
          'question_id': 2,
          'expert_compliance': {{
            'expert_A': 'string',
            'expert_C': 'string'
          }},
          'audit_evidence': 'string'
        }},
        {{
          'question_id': 3,
          'expert_compliance': {{
            'expert_A': 'string',
            'expert_C': 'string'
          }},
          'audit_evidence': 'string'
        }}
      ],
      'audit_results':{{
        'expert_A_audit_result': 'string',
        'expert_C_audit_result': 'string'
      }}
    }}
    
    Anti-bias rule:
    - Never use majority agreement as a reason to approve an opinion.
    - Do not reward an answer because multiple experts gave the same conclusion.
    - Consensus may be mentioned only as a descriptive comparison, not as evidence.
    - Determine the audited answer from the Context first, before comparing experts.
    - Then judge each expert only by alignment with the Context and by the quality of their cited evidence.
    - A minority opinion must be selected if it is better supported by the Context.
    - If multiple experts agree but none are well supported by the Context, mark them as unsupported or partially supported as appropriate.

    Output instructions:
    - Return ONLY a valid JSON object.
    - Do not wrap the output in markdown code blocks (e.g., ```json).
    - Do not include explanations, notes, or additional text outside the JSON object.
    """

        return prompt

    def audit_preprocessing(self, input_file):

        df = pd.read_csv(input_file)

        df_audit = pd.DataFrame()

        clos_dict = [
            'uuid',
            'Title',
            'Abstract',
            'deepseek_kr_flag',
            'deepseek_kr_evidence',
            'qwen_kr_flag',
            'qwen_kr_evidence',
            'deepseek_DT_flag',
            'deepseek_DT_evidence',
            'qwen_DT_flag',
            'qwen_DT_evidence',
            'deepseek_article_type',
            'qwen_article_type',
            'deepseek_ic_label',
            'qwen_ic_label'
        ]

        for name in clos_dict:
            df_audit[self.hide_model_name(name)] = df[name]

        audit_prompt = []
        audit_result = []
        for idx, row in df_audit.iterrows():
            prompt = self.generate_audit_prompt_from_row(row)
            audit_prompt.append(prompt)
            try:
                review = get_ernie_obj(prompt)
                print(review)
                audit_result.append(review)
            except Exception as e:
                audit_result.append(e)
                pass

        df_audit["audit_prompt"] = audit_prompt
        df_audit["audit_result"] = audit_result
        df_audit[['uuid','Title','audit_prompt', 'audit_result']].to_csv(self.paper_screen_t3 +
                                                                         f'audit_by_llm.csv',  index=False)

    def audit_conflict_items(self, input_file):
        df_audit = pd.read_csv(input_file)
        audit_answer = []
        for idx, row in df_audit.iterrows():
            result = "{}"
            try:
                result = KimiAPI.extract(row["audit_prompt"], result=result)
                print(result)
            except Exception as e:
                print(f"Error processing audit material: {e}")
                pass

            audit_answer.append(result)

        df_audit["audit_answer"] = audit_answer

        df_audit.to_csv(self.paper_screen_t3 + f'audit_results.csv', index=False)

    def audit_postprocessing(self, audit_materials_file,
                             audit_results_file):
        df_audit_materials = pd.read_csv(audit_materials_file)
        df_audit_results = pd.read_csv(audit_results_file)

        def extract_audit_results(json_str):

            try:
                data = json.loads(json_str)  # 解析 JSON
                audit_results = data.get('audit_results', {})
                # 提取三个结果，不存在则返回 None
                return pd.Series([
                    audit_results.get('expert_A_audit_result'),
                    audit_results.get('expert_C_audit_result')
                ])
            except (json.JSONDecodeError, TypeError, AttributeError):
                # 如果解析失败或值为空，返回三个 None
                return pd.Series([None, None, None])

        # 3. 应用到目标列，生成三个新列
        df_audit_results[['expert_A_audit_result', 'expert_C_audit_result']] \
            = df_audit_results['audit_result'].apply(extract_audit_results)

        df_audit_combined = pd.merge(df_audit_materials, df_audit_results, on=['uuid', 'Title'], how='left')

        df_audit = pd.DataFrame()

        gathering_clos_dict = [
            'expert_A_audit_result',
            'expert_C_audit_result'
        ]

        for name in df_audit_combined.columns:
            if name in gathering_clos_dict:
                df_audit[self.unhide_model_name(name)] = df_audit_combined[name]
            else:
                df_audit[name] = df_audit_combined[name]

        pass_uuid_list = []
        audit_by_llm = []
        for idx, row in df_audit.iterrows():
            audit_by_llm.append(False)
            for model in ['deepseek', 'qwen']:
                if row[f'{model}_ic_label'] and row[f'expert_{model}_audit_result'] == 'Fully Support':
                    pass_uuid_list.append(row['uuid'])
                    audit_by_llm[-1] = True
                    break
        df_audit['audit_by_llm'] = audit_by_llm
        df_audit.drop(['audit_prompt'], axis=1, inplace=True)
        df_audit.to_csv(self.paper_screen_t3 + f'audit_waiting_for_hr.csv', index=False)
        df_audit[df_audit['uuid'].isin(pass_uuid_list)].to_csv(self.paper_screen_t3 + f'audit_final_results.csv',index=False)

        accepted_file = self.paper_screen_t2 + "waiting_for_accept_papers.csv"
        waiting_audit_file = self.paper_screen_t2 + "waiting_for_audit_papers.csv"
        df_accepted  = pd.read_csv(accepted_file)
        df_waiting_audit = pd.read_csv(waiting_audit_file)

        df_accepted_all = pd.concat([df_accepted, df_waiting_audit[df_waiting_audit['uuid'].isin(pass_uuid_list)]],
                                    ignore_index=True)[['uuid', 'Title','Abstract']]
        df_accepted_all.to_csv(f"{self.annotation_path}waiting_for_annotation.csv",index=False)


if __name__ == '__main__':

    stage = 2
    screen_papers = ScreenPapersAuditor()

    input_file = "../data/papers/midput/screening_by_abs_t2/waiting_for_audit_papers.csv"
    if stage == 1:
        screen_papers.audit_preprocessing(input_file)

    if stage == 2:
        audit_materials_file = "../data/papers/midput/screening_by_abs_t2/waiting_for_audit_papers.csv"
        audit_results_file = "../data/papers/midput/screening_by_abs_t3/audit_by_llm.csv"
        screen_papers.audit_postprocessing(audit_materials_file, audit_results_file)
