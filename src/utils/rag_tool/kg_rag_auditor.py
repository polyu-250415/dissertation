import os

import pandas as pd
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

        CYPHER_TEMPLATE_EN = """
        You are a Neo4j Cypher query expert.

        Task:
        Convert the user's QUESTION into a **valid, executable Cypher query** that returns **ALL matching triples (subject, predicate, object)** from the knowledge graph.

        Rules:
        1. Return ONLY full triples in form: (s)-[r]->(o)
        2. DO NOT use LIMIT, DO NOT truncate results.
        3. Return ALL matching results, no missing data.
        4. Only use existing node labels, relationship types, and properties.
        5. Output ONLY Cypher code, no extra text.

        Schema:
        {schema}

        Question:
        {question}

        Cypher Query:
        """

        CYPHER_PROMPT_EN = PromptTemplate(
            input_variables=["schema", "question"],
            template=CYPHER_TEMPLATE_EN
        )

        # ==============================================
        # 2. QA PROMPT：强制返回【英文固定JSON结构】
        # ==============================================
        QA_TEMPLATE_EN = """
        You are a precise answer generator.

        Task:
        Generate a **strict, valid JSON object** in ENGLISH based on the Context and Question.
        Follow the fixed JSON format below, NO extra explanation, NO extra characters.

        Fixed JSON format ONLY:
        {{"answer":"[your answer here]", "evidence":"[all triples found in context as supporting evidence]"}}

        Rules:
        1. answer: Concise English summary, keep it short.
        2. evidence: List ALL TRIPLES (subject, predicate, object) from context.
        3. DO NOT make up information.
        4. Return ONLY JSON, nothing else.

        Context:
        {context}

        Question:
        {question}

        JSON Output:
        """

        QA_PROMPT_EN = PromptTemplate(
            input_variables=["context", "question"],
            template=QA_TEMPLATE_EN
        )

        return GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            allow_dangerous_requests=True,
            cypher_prompt=CYPHER_PROMPT_EN,
            qa_prompt=QA_PROMPT_EN
        )

    def query(self, question):

        # 4. 自然语言提问
        response = self.build_customized_chain().run(question)
        return response

if __name__ == '__main__':
    obj = KGRAGAuditor()

    questions = [
        "What's the mechanism of each technology-enable practice? introduce this from relations among knowledge holders, tacit knowledge, digital technology, organizational dependency, resource dependency, and limitation perspectives",
        "Which uncodified skills, intuitions or behavioral routines are described?",
        "What evidence shows that technology-enable practice  still relies on human baselines or that Traditional Practice remains legally/operationally mandatory?"
    ]

    df =pd.read_csv('question.csv')
    # questions = df['Validation Question'].tolist()
    rsp_list= []
    for question in questions:
        # rsp = obj.query(question)
        rsp = obj.build_customized_chain().run(question)
        print(rsp)
        rsp_list.append(rsp)

    # df['rsp'] = rsp_list
    # df.to_csv("question_rsp.csv", index=False)