from neo4j import GraphDatabase
from src.Dissertation.graphy_tools.create_nodes import read_nodes_from_csv, create_nodes_with_apoc, create_nodes_fallback
from src.Dissertation.graphy_tools.create_relation import read_relations_from_csv,create_relationships

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "MyNewPass123!")
CSV_DIR = '../data/graph/case study/'
DATABASE = "kggen"

case_id = 'c003'

def clear_whole_database(session):
    """
    清空 Neo4j 整个库的所有节点、关系、属性
    无 case_id 过滤，直接全删
    """
    print("⚠️  正在清空整个数据库...")
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    session.run(query)
    print("✅ 数据库已清空！")

def create_paper_graph(case_id, path_dir=CSV_DIR):
    print("📥 Reading nodes from CSV...")
    try:
        nodes = read_nodes_from_csv(endswith=f'{case_id}_nodes.csv', path_dir=path_dir)
        print(f"✅ Loaded {len(nodes)} nodes.")
        for i, n in enumerate(nodes[:3], 1):  # preview first 3
            print(f"  {i}. Label: {n['Label']}, Props keys: {list(n['properties'].keys())}")
        if len(nodes) > 3:
            print("  ...")
    except Exception as e:
        print("❌ Failed to read CSV:", e)
        exit(1)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session(database='kggen') as session:

        clear_whole_database(session)

        try:
            # Test APOC availability
            session.run("RETURN apoc.version()").single()
            print("⚡ Using APOC for efficient batch insert...")
            created = create_nodes_with_apoc(session, nodes)
        except Exception:
            print("⚠ APOC not available — using per-node creation...")
            created = create_nodes_fallback(session, nodes)

        print(f"✅ Inserted {created} nodes into Neo4j.")

        rels = read_relations_from_csv(endswith=f'{case_id}_relations.csv',path_dir=path_dir)
        total_created = 0
        for i in range(0, len(rels), 500):
            batch = rels[i:i + 500]
            created = session.execute_write(create_relationships, batch)
            total_created += created
            print(f"✅ 批次 {i // 500 + 1}：创建 {created} 条")

        print(f"\n🎉 导入完成！成功关系：{total_created}")
    driver.close()

# === MAIN ===
if __name__ == "__main__":

    create_paper_graph(case_id)