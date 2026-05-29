import os
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from src.utils.llm_key import deepseek_key
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import PromptTemplate

# 方式1：环境变量设置（推荐）
os.environ["DEEPSEEK_API_KEY"] = deepseek_key

class KGRAGAuditor:

    def __init__(self):

        self.llm = ChatDeepSeek(
            model="deepseek-chat",  # 通用对话模型
            temperature=0,
            # max_tokens=2048,  # 可选
            # api_key="你的 DeepSeek API Key"  # 也可以直接写在这里
        )

        # 1. 连接 Neo4j
        self.graph = Neo4jGraph(url="bolt://localhost:7687",
                           username="neo4j",
                           password="MyNewPass123!",
                           database="kggen")

        # 3. 创建 Cypher 问答链
        self.chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            allow_dangerous_requests=True
        )

    def build_customized_chain(self):

        CYPHER_GENERATION_PROMPT = PromptTemplate.from_template(
            """
            You are a professional Neo4j Cypher query generator.
            Generate a valid Cypher query for the user's question, and STRICTLY FOLLOW the retrieval scope rules below:

            [STRICT FILTER RULES - MUST APPLY]
            1. Only query nodes with label: Node
            2. Only return nodes that match ALL these property conditions:
               - case_title = "Game-based learning as training to use a chemotherapy preparation robot"
            3. DO NOT query nodes/relationships that do not meet the above rules
            4. Always add WHERE clause for filtering

            Graph Schema:
            {schema}

            Question:
            {question}

            Return ONLY the runnable Cypher query, no extra text.
            """
        )

        return GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            allow_dangerous_requests=True,
            cypher_prompt=CYPHER_GENERATION_PROMPT
        )

    def query(self, question):

        # 4. 自然语言提问
        response = self.chain.run(question)
        print(response)


if __name__ == '__main__':
    obj = KGRAGAuditor()
    questions = [
        "What’s the knowledge retention mechanism of these technology-enabled practices? the type to introduce "
        "mechanism should include relation types covering knowledge holder, tacit knowledge, limitation, "
        "organizational dependency, resource dependency"
    ]
    for question in questions:
        obj.query(question)