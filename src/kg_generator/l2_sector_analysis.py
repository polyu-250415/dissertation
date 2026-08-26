import pandas as pd


class L2SectorAnalysis:
    def __init__(self):

        self.schema_file = "../conf/coding_schema/coding_schema.xlsx"
        self.v_ds_path = "../data/graph/case_study/sector_4_v_ds/"
        self.sector_norm_path = "../data/graph/case_study/sector_3_norm_nodes/"

    def generate_prompt(self, sector_node_id, rq_value):
        try:
            df = pd.read_excel(self.schema_file, sheet_name='RQ_Coding_Rule')
        except Exception as e:
            raise ValueError(f"读取 Excel 文件失败: {e}")

        # 验证所需列是否存在
        required_cols = ['RQ', 'Cypher', 'Prompt Template']
        for col in required_cols:
            if col not in df.columns:
                raise KeyError(f"页签 'RQ_Coding_Rule' 中缺少列: '{col}'")

        # 查找匹配的行（假设 RQ 唯一，取第一个匹配）
        mask = df['RQ'] == rq_value
        matched = df.loc[mask]

        if matched.empty:
            return ""

        row = matched.iloc[0]
        cypher = row['Cypher']
        prompt = row['Prompt Template']

        cypher = None if pd.isna(cypher) else str(cypher)
        prompt = None if pd.isna(prompt) else str(prompt)

        cypher_stat = cypher.replace('{sector_node_id}', sector_node_id)

        return cypher_stat, prompt.replace('{graph}', cypher_stat)

    def generate_downstream_task(self):
        sector_ids = ['s001', 's002', 's003']
        rq_dict = {'RQ1':'Technology-enable Retention Mechanism',
                   'RQ2':'Environmental Dependencies',
                   'RQ3':'Organizational Culture Dependencies',}

        for sector_id in sector_ids:
            node_ids = []
            categories = []
            tasks = []
            cyphers = []

            for rq in rq_dict.keys():

                if rq == 'RQ1':
                    df_nodes = pd.read_csv(self.sector_norm_path + sector_id + '_l2_nodes.csv')
                    tp_ids = df_nodes[df_nodes["category"] == "Technology-enable Practice"][
                        "node_id"].drop_duplicates().tolist()
                    for sector_node_id in tp_ids:
                        node_ids.append(sector_node_id)
                        cypher, task = self.generate_prompt(sector_node_id, rq)
                        cyphers.append(cypher)
                        tasks.append(task)
                        categories.append(rq_dict[rq])
                    continue

                node_ids.append(sector_id + "M01R" + rq)
                cypher, task = self.generate_prompt(sector_id, rq)
                cyphers.append(cypher)
                tasks.append(task)
                categories.append(rq_dict[rq])

            pd.DataFrame({"node_id": node_ids, "category":categories, "cypher":cyphers,"task": tasks}).to_csv(
                self.v_ds_path + f'{sector_id}_v_ds.csv', index=False)

        print("\n\nPractice Insights:\n")
        print("Read the data in the attached file. This file contains the following columns: node_id, category,task. Execute the records in the column named 'task' , store the result in the 'insight' column, and output a CSV file with the headers: node_id, category, task, insight.")

        print("\n\nSector Insights:\n")
        print("""
RQ1: What specific emerging technologies have been adopted to support tacit knowledge retention practices, and how do specific technologies facilitate the transformation of tacit knowledge?
Experience Amplification
...
Digital Coding
...


RQ2: What organizational resources and capabilities (e.g., data infrastructure, expert participation, and environmental factors ) are required to deploy these technologies?
Digital-Era Specific Dependencies
...
Classic Industry & Institutional Dependencies
...


RQ3: How does organizational culture (e.g., trust, psychological safety, leadership support, and motivation) influence the effectiveness of technology-enabled tacit knowledge retention?
Digital-Era Specific Dependencies
...
Classic Industry & Institutional Dependencies
...

***Coding Rule***
RQ1 Coding Rule: Technology-enable Retention Mechanism should be analyzed based on the explicit evidence chain(e.g., digital technologies-> technology-enable practice -> tacit knowledge -> Conditions and constraints) in which each node can be supported by node_id (sXXX).
RQ2 Coding Rule: directly reuse s001M01RRQ2
RQ3 Coding Rule: directly reuse s001M01RRQ3
        """)

    def develop_insight_kg(self):
        sector_ids = ['s001', 's002', 's003']

if __name__ == '__main__':
    obj = L2SectorAnalysis()
    obj.generate_downstream_task()
