from neo4j import GraphDatabase
from src.utils.graph_tools.create_nodes import read_nodes_from_csv, create_nodes_with_apoc, create_nodes_fallback
from src.utils.graph_tools.create_relation import read_relations_from_csv,create_relationships

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "MyNewPass123!")
CSV_DIR = '../../data/graph/case_study/case_3_unite/'
DATABASE = "kggen"
case_id = 'c006'

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

def create_kg_by_case(case_id, path_dir=CSV_DIR, mid_seg='',):
    print("📥 Reading nodes from CSV...")
    try:
        nodes = read_nodes_from_csv(endswith=f'{case_id}{mid_seg}_nodes.csv', path_dir=path_dir)
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

        rels = read_relations_from_csv(endswith=f'{case_id}{mid_seg}_relations.csv',path_dir=path_dir)
        total_created = 0
        for i in range(0, len(rels), 500):
            batch = rels[i:i + 500]
            created = session.execute_write(create_relationships, batch)
            total_created += created
            print(f"✅ 批次 {i // 500 + 1}：创建 {created} 条")

        print(f"\n🎉 导入完成！成功关系：{total_created}")
    driver.close()

def create_kg_by_files(files, path_dir=CSV_DIR):
    print("📥 Reading nodes from CSV...")

    nodes_array = []
    rels_array = []
    for f in files:
        if f.endswith('nodes.csv'):
            try:
                nodes = read_nodes_from_csv(endswith=f, path_dir=path_dir)
                print(f"✅ Loaded {len(nodes)} nodes.")
                for i, n in enumerate(nodes[:3], 1):  # preview first 3
                    print(f"  {i}. Label: {n['Label']}, Props keys: {list(n['properties'].keys())}")
                if len(nodes) > 3:
                    print("  ...")
                nodes_array.extend(nodes)
            except Exception as e:
                print("❌ Failed to read CSV:", e)
                exit(1)
        elif f.endswith('relations.csv'):
            try:
                rels = read_relations_from_csv(endswith=f,path_dir=path_dir)
                print(f"✅ Loaded {len(rels)} relations.")
                rels_array.extend(rels)
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
            created = create_nodes_with_apoc(session, nodes_array)
        except Exception as e:
            print(f"⚠ APOC not available — using per-node creation...{e}")
            created = create_nodes_fallback(session, nodes_array)

        print(f"✅ Inserted {created} nodes into Neo4j.")


        total_created = 0
        for i in range(0, len(rels_array), 500):
            batch = rels_array[i:i + 500]
            created = session.execute_write(create_relationships, batch)
            total_created += created
            print(f"✅ 批次 {i // 500 + 1}：创建 {created} 条")

        print(f"\n🎉 导入完成！成功关系：{total_created}")
    driver.close()

# === MAIN ===
if __name__ == "__main__":

    create_kg_by_case(case_id)