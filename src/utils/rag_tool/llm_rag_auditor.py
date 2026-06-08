import os
import logging
from pathlib import Path
import pandas as pd

# Assuming these are accessible imports from your local source tree
from src.utils.llm_key import deepseek_key, qwen_key, ernie_api_k
from src.utils.llm_mgmt.deepseek_local_api import chat_with_deepseek

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

os.environ["DEEPSEEK_API_KEY"] = deepseek_key
os.environ["QWEN_API_KEY"] = qwen_key
os.environ["ERNIE_API_KEY"] = ernie_api_k

from haystack import Document, Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

from haystack_integrations.components.embedders.fastembed import FastembedDocumentEmbedder, FastembedTextEmbedder


class RAGAuditor:
    def __init__(self,
                 model_name: str = "BAAI/bge-small-en-v1.5",
                 prompt_index = 0,
                 debug: bool = True):
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                filename='/Users/meimei/work/coding/dissertation/src/log/haystack_debug.log',
                filemode='a'
            )
            logging.getLogger("haystack").setLevel(logging.DEBUG)

        self.document_store = InMemoryDocumentStore()
        self.model_name = model_name
        self.embedding_model_cache_path = "/Users/meimei/work/coding/dissertation/src/models/fastembed/bge-small-en-v1.5"
        self.indexing_pipeline = self._build_indexing_pipeline()
        self.query_pipeline = self._build_triplet_query_pipeline()

    def _build_indexing_pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        pipeline.add_component("converter", PyPDFToDocument())
        pipeline.add_component("cleaner", DocumentCleaner())
        pipeline.add_component("splitter", DocumentSplitter(split_by="word", split_length=128))

        # FastEmbed Document Embedder
        pipeline.add_component("embedder", FastembedDocumentEmbedder(
            model=self.model_name,
            cache_dir=self.embedding_model_cache_path,
            local_files_only=True,
            parallel=0
        ))

        # Explicitly connect with explicit sockets to prevent validation errors
        pipeline.connect("converter.documents", "cleaner.documents")
        pipeline.connect("cleaner.documents", "splitter.documents")
        pipeline.connect("splitter.documents", "embedder.documents")
        return pipeline

    def _build_verification_claim_pipeline(self) -> Pipeline:
            rag_template = """
    Context: {% for doc in documents %} {{ doc.content }} {% endfor %}

    Claim: {{ query }}

    Task:
    You are a strict data auditor. Evaluate the claim strictly against the provided context only. Do not use external knowledge.

    Rate the claim using one of the following categories:
    - Supported (output 5): The claim is directly stated or explicitly affirmed in the context.
    - Strongly implied (output 4): The claim is not stated word‑for‑word, but can be logically and clearly inferred from multiple explicit statements in the context.
    - Not mentioned (output 3): The context does not contain enough information to determine whether the claim is true or false.
    - Contradicted (output 2): The context contains information that directly opposes the claim.
    - Unclear (output 1): The evidence is ambiguous, contradictory within the context, or requires human judgment to resolve.

    Instructions:
    - Output only a single digit: 5,4,3,2,or 1.
    - Do not include any explanation, punctuation, or extra text.

    Your output:"""

            pipeline = Pipeline()

            pipeline.add_component("text_embedder",
                                   FastembedTextEmbedder(model=self.model_name,
                                                         cache_dir=self.embedding_model_cache_path,
                                                         local_files_only=True,
                                                         parallel=0))
            pipeline.add_component("retriever", InMemoryEmbeddingRetriever(document_store=self.document_store, top_k=3))

            pipeline.add_component("llm_deepseek", OpenAIGenerator(
                api_base_url="https://api.deepseek.com/v1",
                model="deepseek-reasoner",
                api_key=Secret.from_env_var("DEEPSEEK_API_KEY")
            ))

            pipeline.add_component("prompt_deepseek", PromptBuilder(template=rag_template))

            # Explicitly declare output and input slots to maintain stability in Haystack v2
            pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
            pipeline.connect("retriever.documents", "prompt_deepseek.documents")
            pipeline.connect("prompt_deepseek.prompt", "llm_deepseek.prompt")

            return pipeline

    def _build_triplet_query_pipeline(self) -> Pipeline:
        rag_template = """
Context: {% for doc in documents %} {{ doc.content }} {% endfor %}

Statement: {{ query }}

Task:
You are a data auditor and need to determine if this statement is correct. Evaluate this statement strictly based on the provided background information. Do not use external knowledge.

Instructions:
- Output only a single digit: 5 or 1, 5 for True, 1 for False.
- Do not include any explanation, punctuation, or extra text.

Your output:"""

        pipeline = Pipeline()

        pipeline.add_component("text_embedder",
                               FastembedTextEmbedder(model=self.model_name,
                                                     cache_dir=self.embedding_model_cache_path,
                                                     local_files_only=True,
                                                     parallel=0))
        pipeline.add_component("retriever", InMemoryEmbeddingRetriever(document_store=self.document_store, top_k=3))

        pipeline.add_component("llm_deepseek", OpenAIGenerator(
            api_base_url="https://api.deepseek.com/v1",
            model="deepseek-reasoner",
            api_key=Secret.from_env_var("DEEPSEEK_API_KEY")
        ))

        pipeline.add_component("prompt_deepseek", PromptBuilder(template=rag_template))

        # Explicitly declare output and input slots to maintain stability in Haystack v2
        pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        pipeline.connect("retriever.documents", "prompt_deepseek.documents")
        pipeline.connect("prompt_deepseek.prompt", "llm_deepseek.prompt")

        return pipeline

    def _build_query_pipeline(self) -> Pipeline:
            rag_template = """
    Context: {% for doc in documents %} {{ doc.content }} {% endfor %}

    Question: {{ query }}

    Task:
    Given the context, answer the above question.If there is no answer in the context, you just need return "Not 
    Mentioned".

    Your output:"""

            pipeline = Pipeline()

            pipeline.add_component("text_embedder",
                                   FastembedTextEmbedder(model=self.model_name,
                                                         cache_dir=self.embedding_model_cache_path,
                                                         local_files_only=True,
                                                         parallel=0))
            pipeline.add_component("retriever", InMemoryEmbeddingRetriever(document_store=self.document_store, top_k=3))

            pipeline.add_component("llm_deepseek", OpenAIGenerator(
                api_base_url="https://api.deepseek.com/v1",
                model="deepseek-reasoner",
                api_key=Secret.from_env_var("DEEPSEEK_API_KEY")
            ))

            pipeline.add_component("prompt_deepseek", PromptBuilder(template=rag_template))

            # Explicitly declare output and input slots to maintain stability in Haystack v2
            pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
            pipeline.connect("retriever.documents", "prompt_deepseek.documents")
            pipeline.connect("prompt_deepseek.prompt", "llm_deepseek.prompt")

            return pipeline

    def _build_retrieval_pipeline(self, top_k = 5) -> Pipeline:

            pipeline = Pipeline()

            pipeline.add_component("text_embedder",
                                   FastembedTextEmbedder(model=self.model_name,
                                                         cache_dir=self.embedding_model_cache_path,
                                                         local_files_only=True,
                                                         parallel=0))
            pipeline.add_component("retriever", InMemoryEmbeddingRetriever(document_store=self.document_store,
                                                                           top_k=top_k))

            # Explicitly declare output and input slots to maintain stability in Haystack v2
            pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

            return pipeline

    def ingest(self, pdf_path: str, custom_meta: dict = None):
        path = Path(pdf_path)
        pdf_files = list(path.glob("*.pdf"))

        if not pdf_files:
            print(f"No PDFs found in {pdf_path}")
            return

        for pdf in pdf_files:
            print(f"Ingesting: {pdf.name}")
            result = self.indexing_pipeline.run({
                "converter": {"sources": [str(pdf)]}
            })

            docs_to_write = []
            # Extract out of the "embedder" component dictionary block
            for doc in result["embedder"]["documents"]:
                # Keep any existing metadata parsing extracted by PyPDF (e.g., page numbers)
                new_meta = doc.meta.copy() if doc.meta else {}
                new_meta.update({
                    "filename": pdf.name,
                    "file_path": str(pdf),
                    "file_type": "pdf",
                    "category": "education"
                })

                if custom_meta:
                    new_meta.update(custom_meta)

                new_doc = Document(
                    content=doc.content,
                    meta=new_meta,
                    embedding=doc.embedding
                )
                docs_to_write.append(new_doc)

            self.document_store.write_documents(docs_to_write)


    def query(self, question_list, filters: dict = None):
        resp_list = []
        for question in question_list:
            try:
                run_input = {
                    "text_embedder": {"text": question},
                    "prompt_deepseek": {"query": question}
                }

                if filters:
                    run_input["retriever"] = {"filters": filters}

                results = self._build_query_pipeline().run(run_input)

                resp_list.append(results["llm_deepseek"]["replies"][0])

            except Exception as e:
                print(e)
                resp_list.append("E")
        return resp_list

    def ask(self, question_list:list[dict], filters: dict = None):

        resp_list = []

        for item in question_list:
            try:
                run_input = {
                    "text_embedder": {"text": item['question']},
                    "prompt_deepseek": {"query": item['question']}
                }

                if filters:
                    run_input["retriever"] = {"filters": filters}
                if item['sample_type'] == 'evidence':
                    results = self._build_verification_claim_pipeline().run(run_input)
                else:
                    results = self._build_triplet_query_pipeline().run(run_input)

                print(f'Q: {item["question"]}\n R: {results["llm_deepseek"]["replies"][0]}')

                resp_list.append(results["llm_deepseek"]["replies"][0])
            except Exception as e:
                resp_list.append("E")
                print(e)

        return resp_list

    def query_related_docs(self, question):
        docs = []
        run_input = {
            "text_embedder": {"text": question}
        }

        if filters:
            run_input["retriever"] = {"filters": filters}
        results = self._build_retrieval_pipeline().run(run_input)

        for doc in results["retriever"]["documents"]:
            if doc.score > 0.5:
                docs.append(doc.content.replace("\n", " "))

        context = "\n".join(docs)

        return context

    def ask_by_local_llm(self, question_list:list[dict], filters: dict = None):

        resp_list = []

        for item in question_list:
            try:
                context = self.query_related_docs(item['question'])

                prompt_template = {
                    "assemble":
f"""
    Base on the below context, try to judge whether the claim is True or False:
                            
    context: {context}
                            
    claim: {item['question']}
    
    Rate the claim using one of the following categories:
    - True (output 1): The claim is directly stated or explicitly affirmed in the context.
    - Not mentioned (output 0): The context does not contain enough information to determine whether the claim is 
    true or false.
    - False (output -1): The context contains information that directly opposes the claim.
    explicit statements in the context.
                            
    Instructions:
    - Output only a single digit: 1, 0 or -1.
    - Do not include any explanation, punctuation, or extra text.""",
                    "evidence":
f"""
    Context: {context}

    Claim: {item['question']}

    Task:
    You are a strict data auditor. Evaluate the claim strictly against the provided context only. Do not use external knowledge.

    Rate the claim using one of the following categories:
    - Supported (output 5): The claim is directly stated or explicitly affirmed in the context.
    - Strongly implied (output 4): The claim is not stated word‑for‑word, but can be logically and clearly inferred from multiple explicit statements in the context.
    - Not mentioned (output 3): The context does not contain enough information to determine whether the claim is true or false.
    - Contradicted (output 2): The context contains information that directly opposes the claim.
    - Unclear (output 1): The evidence is ambiguous, contradictory within the context, or requires human judgment to resolve.

    Instructions:
    - Output only a single digit: 5,4,3,2,or 1.
    - Do not include any explanation, punctuation, or extra text.

    Your output:"""
                }

                resp = chat_with_deepseek(prompt_template[item['sample_type']])
                resp_list.append(resp)

                print(f'C:{context} \n Q: {item["question"]}\n R: {resp}')
            except Exception as e:
                resp_list.append("E")
                print(e)

        return resp_list


if __name__ == '__main__':
    obj = RAGAuditor()

    case_id = "c001"
    custom_meta_data: dict = {
        "case_id": case_id
    }

    path = "../../data/graph/case_study/raw_pdf_m/c001/"

    # FIX: Pass the custom_meta dictionary explicitly here
    obj.ingest(path, custom_meta=custom_meta_data)
    """

    df_nodes = pd.read_csv("../../data/graph/case_study/case_6_v_ds/c001_ds_rag.csv")

    question_list = df_nodes[['sample_type', 'question']].to_dict(orient='records')
    filters = {"field": "meta.case_id", "operator": "==", "value": case_id}

    try:
        # response = obj.ask(question_list, filters=filters)
        response = obj.query_related_docs(question_list, filters=filters)
        df_nodes['r'] = response

        df_nodes.to_csv('just_new.csv', index=False)

    except FileNotFoundError:
        print("Metadata ingestion complete. CSV path not found, skipping evaluation loops.")
    """
    filters = {"field": "meta.case_id", "operator": "==", "value": case_id}
    question_list = [
        "Which tacit knowledge is described?",
        "What organizational culture influence the effectiveness of the technology-enabled practices?",
        "Does the organization adopt incentive or reward measures to encourage knowledge holders to actively "
        "participate in technology-enable practices?",
        "Does the organization adopt interpersonal trust and a psychological safety climate to encourage knowledge holders to actively participate in technology-enable practices?"
        "Does the organization cultivate intrinsic identity, cultural knowledge-sharing values, and institutional governance/ethics clearances to encourage knowledge holders to actively participate in technology-enable practices?"
    ]
    for question in question_list:
        obj.query(question)


