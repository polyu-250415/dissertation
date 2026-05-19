import csv
import os
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "MyNewPass123!")
CSV_DIR = '../../data/graph/case_study/'
DATABASE = "kggen"


# 匹配 字符串业务ID 创建关系
def create_relationships(tx, batch):
    query = """
    UNWIND $batch AS rel
    // 按 字符串ID 匹配节点（假设节点属性叫 id，你可以改成 node_id）
    MATCH (a {id: rel.start_id})
    MATCH (b {id: rel.end_id})
    WHERE a IS NOT NULL AND b IS NOT NULL

    // 创建动态关系
    CALL apoc.create.relationship(a, rel.type, {case_id: rel.case_id}, b)
    YIELD rel AS r

    RETURN count(r) AS created
    """
    result = tx.run(query, batch=batch)
    return result.single()["created"]


# ==================== 加载 CSV ====================

def read_relations_from_csv(endswith="relations.csv", path_dir=CSV_DIR):
    rels = []

    for root, dirs, files in os.walk(path_dir):
        for file in files:
            if not file.endswith(endswith):
                continue

            file_path = os.path.join(root, file)
            print("📂 读取文件:", file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 直接读取字符串，不用转 int！
                    start_id = row["start_id"].strip()
                    end_id = row["end_id"].strip()
                    rel_type = row["type"].strip()
                    case_id = row.get("case_id", "").strip()

                    rels.append({
                        "start_id": start_id,
                        "end_id": end_id,
                        "type": rel_type,
                        "case_id": case_id
                    })

    print(f"✅ 准备导入 {len(rels)} 条关系")
    return rels

if __name__ == '__main__':
    rels = read_relations_from_csv()
    # ==================== 执行导入 ====================
    driver = GraphDatabase.driver(URI, auth=AUTH)
    total_created = 0

    with driver.session(database=DATABASE) as session:
        for i in range(0, len(rels), 500):
            batch = rels[i:i + 500]
            created = session.execute_write(create_relationships, batch)
            total_created += created
            print(f"✅ 批次 {i // 500 + 1}：创建 {created} 条")

    driver.close()
    print(f"\n🎉 导入完成！成功关系：{total_created}")