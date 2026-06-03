import os
from neo4j import GraphDatabase

import  pandas as pd
import re

# === CONFIG ===
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "MyNewPass123!")
CSV_DIR = "../../data/graph/case_study/case_6_v_ds"

def read_nodes_from_csv(endswith='nodes.csv', path_dir=CSV_DIR):
    nodes = []
    for root, dirs, files in os.walk(path_dir):
        for file in files:
            if not file.endswith(endswith):
                continue

            file = os.path.join(root, file)
            df = pd.read_csv(file)
            df = df.astype(str)

            for index, item in df.iterrows():
                if not len(item['category']):
                    continue
                props={}
                Label = re.sub(r'[^a-zA-Z]', '', item['category'])
                for prop_title in item.keys():
                    if item[prop_title] != 'nan':
                        props[prop_title] = item[prop_title]

                nodes.append({
                    "Label": Label,
                    "properties": props
                })

    return nodes

def create_nodes_with_apoc(session, nodes_data):
    query = """
    UNWIND $nodes AS node
    CREATE (n)
    SET n = node.properties
    WITH n, node.Label AS Label
    CALL apoc.create.addLabel(id(n), Label) YIELD node AS _
    RETURN count(*) AS created
    """
    result = session.run(query, nodes=nodes_data)
    return result.single()["created"]


def create_nodes_fallback(session, nodes_data):
    count = 0
    for node in nodes_data:
        if not node["Label"]:
            # Skip or assign generic label? Here we skip.
            continue
        Label_str = node["Label"]
        props = node["properties"]
        cypher = f"CREATE (n:{Label_str} $props)"
        session.run(cypher, props=props)
        count += 1
    return count


# === MAIN ===
if __name__ == "__main__":

    print("📥 Reading nodes from CSV...")
    try:
        nodes = read_nodes_from_csv()
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
        try:
            # Test APOC availability
            session.run("RETURN apoc.version()").single()
            print("⚡ Using APOC for efficient batch insert...")
            created = create_nodes_with_apoc(session, nodes)
        except Exception:
            print("⚠ APOC not available — using per-node creation...")
            created = create_nodes_fallback(session, nodes)

        print(f"✅ Inserted {created} nodes into Neo4j.")

    driver.close()