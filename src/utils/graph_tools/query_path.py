from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "MyNewPass123!"

class KGRAG:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query_triple_paths(self, start_id, start_distance, end_distance):
        """Query paths in [node, relationship, node...] format"""
        with self.driver.session(database='kggen') as session:
            result = session.run(
                """
                MATCH path=(n)-[*%d..%d]-(m)
                WHERE n.id = $start_id
                RETURN path AS triple_path, length(path) AS hop
                """ % (start_distance, end_distance),
                start_id=start_id
            )

            return [record.data() for record in result]

    def triple_path_to_text(self, triple_path):
        """Convert path to text, only keep entity names"""
        text_parts = []
        i = 0
        while i < len(triple_path):
            # Extract entity name only (ignore other attributes)
            node = triple_path[i]
            text_parts.append(";")
            entity_name = node.get("name", "Unknown Entity")
            text_parts.append(entity_name)

            # Add relationship if exists
            i += 1
            if i < len(triple_path):
                rel = triple_path[i]
                rel_clean = rel.replace("_", " ").lower()
                text_parts.append(f" {rel_clean} ")
                i += 1

        return "".join(text_parts)

    def build_rag_context(self, start_id, start_distance, end_distance):
        paths = self.query_triple_paths(start_id, start_distance, end_distance)
        if not paths:
            return "No relevant knowledge graph paths found."

        context_list = []
        for item in paths:
            path_text = self.triple_path_to_text(item["triple_path"])
            hop = item["hop"]
            context_list.append(f"({hop}-hop path): {path_text}")

        return "\n".join(context_list)

if __name__ == "__main__":
    # ===================== 你只需要改这里 =====================

    START_NODE_ID = "c003N11"  # 你的起始节点
    start_distance = 3
    end_distance = 3

    kgrag = KGRAG(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    rag_text = kgrag.build_rag_context(START_NODE_ID, start_distance, end_distance)

    print("===== KG‑RAG Retrieved Context =====")
    print(rag_text)
    print("\n===== Prompt for Large Language Model =====")

    prompt = f"""
    Answer the user's question strictly based on the following knowledge graph facts. Do NOT fabricate any information.
    Knowledge Graph Facts:
    {rag_text}
    User Question: Summarize the relational connections from the given paths.
    """
    print(prompt)

    kgrag.close()
