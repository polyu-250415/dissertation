import os, json

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

    def refresh_kg_schema(self):
        self.graph.refresh_schema()

    def build_customized_chain(self, question):

        CYPHER_TEMPLATE_EN = """
Task: You are a Neo4j Cypher query expert. Convert user question into a valid Neo4j Cypher query.
Graph Schema:
{schema}

Strict Mandatory Rules for Cypher Generation:
1. When writing the MATCH clause, always capture the full triple pattern: `(source)-[r:RELATION_TYPE]->(target)`.Explicitly define three variables: source node, relationship r, and target node.
2. The RETURN clause MUST explicitly return `source, r, target`.
- DO NOT return only a single node, DO NOT use `RETURN *`. 
- Always output the complete triple elements.
- **DO NOT manually list individual properties (e.g. source.node_name, r.xxx, target.evidence_statement). Return the whole node/relationship object directly to include ALL its properties.**
- Pay attention to graph relationship direction. `(source)-[r:REL]->(target)` means the relationship r originates from source and points to target. Do NOT swap source and target variables without reversing the arrow direction. Always keep full triple pattern in MATCH, return DISTINCT source, r, target, no partial returns, no RETURN *.
3. Add `DISTINCT` in the RETURN statement to eliminate duplicate records.
4. Do not add ORDER BY or LIMIT unless the user question explicitly requires sorting or limiting results.
5. Do not add extra comments, explanations or natural‑language text. Output only the final Cypher statement.
6. Always use directed arrow `->` for relationship pattern, never use undirected `-[r]-`.
7. Avoid UNION and UNION ALL as much as possible. Do NOT use UNION / UNION ALL to combine multiple triple patterns. Using UNION will trigger error: All sub queries in an UNION must have the same return column names.
- If multiple‑pattern logic is required, use `WITH` clause for logic splitting and variable passing instead of UNION / UNION ALL.
- Only use UNION when there is hard explicit user requirement.
8. Do NOT collect different triples into one RETURN clause to avoid cartesian product explosion.
9. For output context serialization:
- Escape inner single‑quote characters inside single‑quoted string literals, convert every inner `'` to `\'`.
- Do NOT use full‑width Chinese quotation marks (“ ” ‘ ’).
- Ensure every opening quote has a corresponding closing quote.
- Prevent parse error: `Unterminated string starting at`.
10. Never repeatedly output the same variable within one RETURN clause, avoid Multiple result columns with the same name syntax error.

Correct example 1:
MATCH (a:LabelA)-[r:SOME_RELATION]->(b:LabelB)
RETURN DISTINCT a, r, b

Correct example 2 (Use "WITH" to expand query conditions ,and allow partial valid results):
MATCH (kh:KnowledgeHolder)-[r:participate_in]->(p:TechnologyenablePractice)
WITH kh, r, p
OPTIONAL MATCH (kl:KnowledgeLearner)-[r2:participate_in]->(p:TechnologyenablePractice)
RETURN DISTINCT kh, r, p, kl, r2

Correct example 3 (If both r and b are not defined, return a with a certain label):
MATCH (a:LabelA)-[r]->(b)
RETURN DISTINCT a

Forbidden bad example 1 (Do not omit objectives in RETURN):
MATCH (a:LabelA)-[r:SOME_RELATION]->(b:LabelB)
RETURN b

Forbidden bad example 2 (Do not use UNION):
MATCH (kh:KnowledgeHolder)-[r:participate_in]->(p:TechnologyenablePractice)
RETURN DISTINCT kh, r, p
UNION
MATCH (kl:KnowledgeLearner)-[r2:participate_in]->(p:TechnologyenablePractice)
RETURN DISTINCT kl, r2, p

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
1. answer: Concise English summary, keep it short. If there is no answer, return 'Not Mentioned' directly
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

        cypher_gen_chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            allow_dangerous_requests=True,
            cypher_prompt=CYPHER_PROMPT_EN,
            return_intermediate_steps=True,
        )

        intermediate = cypher_gen_chain({"query": question})
        cypher_stmt = intermediate["intermediate_steps"][0]["query"]
        # 此处可以考虑对cypher语句进行优化
        # raw_context = self.graph.query(cypher_stmt)

        result= {"cypher": cypher_stmt}

        try:
            safe_context = json.dumps(intermediate["intermediate_steps"][1]["context"], ensure_ascii=False)

            print(f"\nsafe_context: {safe_context}")
            qa_prompt = QA_PROMPT_EN.format(context=safe_context, question=question)
            resp = self.llm.invoke(qa_prompt)
            print(f"\nresp: {resp}")

            result = result | json.loads(resp.content)
        except Exception as e:
            pass

        return result

    def build_customized_chain_with_cypher(self, question, cypher_stmt):
        QA_TEMPLATE_EN = """
You are an expert academic scholar with interdisciplinary expertise in knowledge management, emerging technologies for KM, and innovation.

***Task***
Analyze the knowledge graph extracted from a cases, generate a **strict, valid JSON object** in ENGLISH based on the 
Context and Question.
Follow the fixed JSON format below, NO extra explanation, NO extra characters.

Fixed JSON format ONLY:
{{"answer":"[your answer here]"}}

Rules:
1. answer: Concise English summary, keep it short. If there is no answer, return 'Not Mentioned' directly
2. DO NOT make up information.
3. Return ONLY JSON, nothing else.

***Input Data***
{context}

Question:
{question}

JSON Output:
    """

        try:
            QA_PROMPT_EN = PromptTemplate(
                input_variables=["context", "question"],
                template=QA_TEMPLATE_EN
            )

            cypher_rst = self.graph.query(cypher_stmt)

            safe_context = json.dumps(cypher_rst, ensure_ascii=False)

            print(f"\nsafe_context: {safe_context}")
            qa_prompt = QA_PROMPT_EN.format(context=safe_context, question=question)
            resp = self.llm.invoke(qa_prompt)
            print(f"\nresp: {resp}")

            result = json.loads(resp.content) | {"evidence": cypher_rst}

        except Exception as e:
            print(e)
            pass

        return result

    def query(self, question, cypher_stmt=''):

        # 4. 自然语言提问
        if len(cypher_stmt) == 0:
            response = self.build_customized_chain(question)
        else:
            response = self.build_customized_chain_with_cypher(question, cypher_stmt)
        return response

    def cypher_query(self, cypher_stmt):
        return self.graph.query(cypher_stmt)

if __name__ == '__main__':
    obj = KGRAGAuditor()

    sector_ids = ['s001M01TP01', 's001M01TP02', 's001M01TP03', 's001M01TP04', 's001M01TP05', 's001M01TP06',
                  's001M01TP07','s001M01TP08','s001M01TP09']
    cypher_stmt ="""
MATCH (tep:TechnologyenablePractice)-[r:adopt]->(dt:DigitalTechnology)
WHERE tep.node_id = "{sector_id}"
WITH tep, COLLECT({src_node:tep, rel: r, dst_node: dt}) AS adoptions

// 1. 捕获 TacitKnowledge (be_captured_by) -> 生成 tk_list
OPTIONAL MATCH (tk:TacitKnowledge)-[r:be_captured_by]->(tep)
WITH tep, adoptions, 
     COLLECT({src_node:tk, rel: r, dst_node: tep}) AS capturedBy,
     COLLECT(DISTINCT tk) AS tk_list

// 2. 捕获 KnowledgeHolder (participate_in) -> 生成 kh_list
OPTIONAL MATCH (kh:KnowledgeHolder)-[r:participate_in]->(tep)
WITH tep, adoptions, capturedBy, tk_list,
     COLLECT({src_node:kh, rel: r, dst_node: tep}) AS holders,
     COLLECT(DISTINCT kh) AS kh_list

// 3. 捕获 KnowledgeLearner (participate_in) -> 生成 kl_list
OPTIONAL MATCH (kl:KnowledgeLearner)-[r:participate_in]->(tep)
WITH tep, adoptions, capturedBy, tk_list, holders, kh_list,
     COLLECT({src_node:kl, rel: r, dst_node: tep}) AS learners,
     COLLECT(DISTINCT kl) AS kl_list

// 4. 捕获 OrganizationalDependency (depend_on) -> 生成 od_list
OPTIONAL MATCH (tep)-[r:depend_on]->(od:OrganizationalDependency)
WITH tep, adoptions, capturedBy, tk_list, holders, kh_list, learners, kl_list,
     COLLECT({src_node:tep, rel: r, dst_node: od}) AS dependORG,
     COLLECT(DISTINCT od) AS od_list

// 5. 捕获 Limitation (be_constrained_by) -> 生成 lim_list
OPTIONAL MATCH (tep)-[r:be_constrained_by]->(lim:Limitation)
WITH tep, adoptions, capturedBy, tk_list, holders, kh_list, learners, kl_list, dependORG, od_list,
     COLLECT({src_node:tep, rel: r, dst_node: lim}) AS constraints,
     COLLECT(DISTINCT lim) AS lim_list

// 6. 捕获 transfers (tk -[:be_transferred_by]-> tep) 
//    限定 tk_trans 必须在上一步收集的 tk_list 中
OPTIONAL MATCH (tk_trans:TacitKnowledge)-[r:be_transferred_by]->(tep)
WHERE tk_trans IN tk_list
WITH tep, adoptions, capturedBy, tk_list, holders, kh_list, learners, kl_list, dependORG, od_list, constraints, lim_list,
     COLLECT({src_node:tk_trans, rel: r, dst_node: tep}) AS transfers

// 7. 捕获 shared (tk -[:be_shared_by]-> kh) 
//    同时限定 tk_shared 在 tk_list 中，kh_shared 在 kh_list 中，精准避免笛卡尔积
OPTIONAL MATCH (tk_shared:TacitKnowledge)-[r:be_shared_by]->(kh_shared:KnowledgeHolder)
WHERE tk_shared IN tk_list AND kh_shared IN kh_list
WITH tep, adoptions, capturedBy, holders, kh_list, learners, kl_list, dependORG, od_list, constraints, lim_list, transfers,
     COLLECT({src_node:tk_shared, rel: r, dst_node: kh_shared}) AS shared

// 8. 捕获 mitigates (tep -[:mitigate]-> lim)
//    限定 lim_mit 必须在 lim_list 中
OPTIONAL MATCH (tep)-[r:mitigate]->(lim_mit:Limitation)
WHERE lim_mit IN lim_list
WITH tep, adoptions, capturedBy, holders, learners, dependORG, constraints, transfers, shared,
     COLLECT({src_node:tep, rel: r, dst_node: lim_mit}) AS mitigates

// 9. 捕获 environment dependency
OPTIONAL MATCH (tep)-[r:depend_on]->(env:EnvironmentalDependency)
WITH tep, adoptions, capturedBy, holders, learners, dependORG, constraints, transfers, shared, mitigates,
     COLLECT({src_node:tep, rel: r, dst_node: env}) AS dependENV

RETURN adoptions,
       capturedBy,
       holders,
       learners,
       dependORG,
       constraints,
       transfers,
       shared,
       mitigates,
       dependENV
"""

    rq_1_prompt = """
You are an expert academic scholar with interdisciplinary expertise in knowledge management, emerging technologies for KM, and innovation.

***Task***
Analyze the knowledge graph extracted from a range of cases, and code a conceptual framework for knowledge retention driven by emerging technologies to answer research questions.

***Input Data***
- the knowledge graph is described as a series of triplets (src_node, r, dst_node)

***CRITICAL REMINDER***
When answering the question, you must NOT rely solely on the text in the node_name. You are strictly required
to perform a semantic analysis of the evidence_statement for every single node. Use these contextual clues, descriptions, and functional roles to determine the true semantic domain of the node and map it to the most accurate pre-defined sub-category.

***Research questions***
What specific emerging technologies have been adopted to support tacit knowledge retention practices, and how do specific technologies facilitate the transformation of tacit knowledge?
 
Coding Rules:
1. You should conduct coding from one of the following two perspectives.
- Experience Amplification: This perspective focuses on digital tools that do not extract or externalize human
intuition but instead serve as an active sandbox to stabilize and transmit the empirical patterns in the human cognitive structure.
- Digital Coding: This perspective focuses on those that can intercept, model, and translate unstructured human
activities, spatial environments, or un-written heuristic rules into clear numerical parameters and recorded systems.
2. The layout of this section is recommended as follows: Map the primary mechanism of  this practice into 
"Experiential Amplification" or "Digital Codification"; Justify your opinion based on the types of tacit knowledge captured or transferred;Summarize the primary influences including positive or negative perspectives.
3. The answer should be in 500.
4. You should cite cases to support your viewpoints and suggest associating multiple cases for each practice to 
support your viewpoints. The format for citing evidence should be (Node ID: XXX - Parent ID: XXX).
5. You should explain the mechanism by combining case evidence, remembering not to merely list all case evidence.

output:
    """

    for sector_node_id in sector_ids:
        print(f'sector_id: {sector_node_id}')
        result = obj.graph.query(cypher_stmt.replace('{sector_node_id}', sector_node_id))
        print(f"{result}\n {rq_1_prompt}")
        print("test")