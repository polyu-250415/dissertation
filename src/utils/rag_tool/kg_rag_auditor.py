import os
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from src.utils.llm_key import deepseek_key
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import PromptTemplate


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
        return response


if __name__ == '__main__':
    obj = KGRAGAuditor()
    questions = [
        "What are the knowledge retention mechanisms for these technology-driven practices? The introduction of the retention mechanisms covers the relationships among knowledge holders, tacit knowledge, constraints, organizational dependence, and resource dependence."
    ]
    for question in questions:
        rsp = obj.query(question)
        # rsp = obj.build_customized_chain().run(question)
        print(rsp)