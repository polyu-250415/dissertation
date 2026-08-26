import csv
import os
import pandas as pd
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "MyNewPass123!")
CSV_DIR = '../../data/graph/case_study/case_6_v_ds/'
DATABASE = "kggen"


# 匹配 字符串业务ID 创建关系
def create_edges(tx, batch):
    query = """
    UNWIND $batch AS rel
    // 按 字符串ID 匹配节点（假设节点属性叫 id，你可以改成 node_id）
    MATCH (a {node_id: rel.src_node_id})
    MATCH (b {node_id: rel.dst_node_id})
    WHERE a IS NOT NULL AND b IS NOT NULL

    // 创建动态关系
    CALL apoc.create.relationship(a, rel.relation_type, rel.properties, b)
    YIELD rel AS r

    RETURN count(r) AS created
    """
    result = tx.run(query, batch=batch)
    return result.single()["created"]


# ==================== 加载 CSV ====================

def read_edges_from_csv(endswith="relations.csv", path_dir=CSV_DIR, excluded_properties=[]):

    rels = []
    for root, dirs, files in os.walk(path_dir):
        for file in files:
            if not file.endswith(endswith):
                continue

            file_path = os.path.join(root, file)
            print("📂 读取文件:", file_path)

            df = pd.read_csv(file_path)
            df = df.astype(str)

            for index, item in df.iterrows():

                # 直接读取字符串，不用转 int！
                src_node_id = item["src_node_id"]
                dst_node_id = item["dst_node_id"]
                relation_type = item["relation_type"]
                props = {}
                for prop_title in item.keys():
                    if item[prop_title] != 'nan' and prop_title not in (['src_node_id','dst_node_id', 'relation_type'] + excluded_properties):
                            props[prop_title] = item[prop_title]

                rels.append({
                    "src_node_id": src_node_id,
                    "dst_node_id": dst_node_id,
                    "relation_type": relation_type,
                    "properties": props
                })

    print(f"✅ 准备导入 {len(rels)} 条关系")
    return rels

if __name__ == '__main__':
    rels = read_edges_from_csv()
    # ==================== 执行导入 ====================
    driver = GraphDatabase.driver(URI, auth=AUTH)
    total_created = 0

    with driver.session(database=DATABASE) as session:
        for i in range(0, len(rels), 500):
            batch = rels[i:i + 500]
            created = session.execute_write(create_edges, batch)
            total_created += created
            print(f"✅ 批次 {i // 500 + 1}：创建 {created} 条")

    driver.close()
    print(f"\n🎉 导入完成！成功关系：{total_created}")