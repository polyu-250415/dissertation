import os
import logging
from pathlib import Path
import pandas as pd

# Assuming these are accessible imports from your local source tree
from src.utils.llm_key import deepseek_key, qwen_key, ernie_api_k

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
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", debug: bool = True):
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                filename='haystack_debug.log',
                filemode='w'
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

    def _build_triplet_query_pipeline(self) -> Pipeline:
        rag_template = """
Context: {% for doc in documents %} {{ doc.content }} {% endfor %}

Claim: {{ query }}

Task: Act as a strict data auditor. Rate the confidence of the claim on a scale of 1-5, 1 means the lowest; 5 means 
the highest. Only return the rate."""

        pipeline = Pipeline()

        pipeline.add_component("text_embedder",
                               FastembedTextEmbedder(model=self.model_name,
                                                     cache_dir=self.embedding_model_cache_path,
                                                     local_files_only=True,
                                                     parallel=0))
        pipeline.add_component("retriever", InMemoryEmbeddingRetriever(document_store=self.document_store, top_k=5))

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

    def ask(self, question_list: list, filters: dict = None):

        resp_list = []

        for question in question_list:
            try:
                run_input = {
                    "text_embedder": {"text": question},
                    "prompt_deepseek": {"query": question}
                }

                if filters:
                    run_input["retriever"] = {"filters": filters}

                results = self.query_pipeline.run(run_input)
                resp_list.append(results["llm_deepseek"]["replies"][0])
            except Exception as e:
                resp_list.append("E")
                print(e)

        return resp_list




if __name__ == '__main__':
    obj = RAGAuditor()

    custom_meta_data: dict = {
        "call_id": "c001"
    }

    path = "../data/graph/case_study/original_papers/construction"

    # FIX: Pass the custom_meta dictionary explicitly here
    obj.ingest(path, custom_meta=custom_meta_data)

    # Simple mock framework for testing execution path if the CSV isn't found immediately
    try:
        df = pd.read_csv("../../data/graph/case_study/case_4_v_kg/c001_nodes_vq.csv")
        response_list = []
        for _, row in df.iterrows():
            try:
                response = obj.ask(row['question'])
                response_list.append(response)
                print(f"Claim: {row['question']} \nLabel: {row['verification_label']}, \nResponse: {response}")
            except Exception as e:
                print(e)
                response_list.append('exception')

        df['assessment'] = response_list
        df.to_csv("../../data/graph/case_study/case_4_v_kg/c001_nodes_vq_result.csv", index=False)
    except FileNotFoundError:
        print("Metadata ingestion complete. CSV path not found, skipping evaluation loops.")


