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
Read the records with the category named "Technology-enable Retention Mechanism", answer the RQ1 based on the insight column. The results should be presented in the Results section with a 600-word narrative, structured as follows:
RQ1: What specific emerging technologies have been adopted to support tacit knowledge retention practices, and how do specific technologies facilitate the transformation of tacit knowledge?
Experience Amplification
...
Digital Coding
...

***Coding Rule***
Technology-enable Retention Mechanism should be analyzed based on the explicit evidence chain following the bellow structure:
Object: Treat technology-enable practice as the basic unit of analysis. 
Mechanism: Explain the core mechanism of how the objective support tacit knowledge retention.
Knowledge target: Introduce the tacit knowledge retained.
Evidence chain: technology nodes → practice node → tacit-knowledge nodes.
Interpretive summary: Concisely summarize this in 20 words.

For Example:
Multimedia and blended knowledge internalization. This integrated interactive interfaces, data and knowledge systems, and mobile and communication technologies to present demonstrations, narratives, videos, and socially mediated learning materials. Its mechanism combined repeated exposure to representations of practice with opportunities for discussion, imitation, and application. It principally supported the internalization of practised motor and tool-operation skills and informal coordination, communication, and escalation know-how. The evidence-supported chain was digital technologies (s001M01TE02;TE04;TE07) → multimedia and blended knowledge internalization (s001M01TP12) → practical and coordinative tacit knowledge (s001M01TK05;TK11) → sociocultural, leadership, scheduling, participation, and organizational-process conditions (s001M01ED03; s001M01OD02;OD04–OD05;OD08). Cognitive and demographic differences, workload, limited expertise, and cultural or leadership barriers could prevent accessible content from becoming competent practice (s001M01LI03;LI08–LI09). Thus, multimedia retained tacit knowledge primarily when learners actively internalized demonstrated practice rather than merely consumed stored information.
        """)

    def develop_insight_kg(self):
        sector_ids = ['s001', 's002', 's003']

if __name__ == '__main__':
    obj = L2SectorAnalysis()
    obj.generate_downstream_task()
