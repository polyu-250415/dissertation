import os

# Critical Environment setup for macOS stability
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
from typing import List

from haystack import Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

# Using FastEmbed instead of SentenceTransformers
from haystack_integrations.components.embedders.fastembed import FastembedDocumentEmbedder, FastembedTextEmbedder

from src.utils.llm_key import deepseek_key, qwen_key, ernie_api_k

import logging

class EnsembleRAG:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", debug: bool = True):
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                filename='haystack_debug.log',  # 保存到文件
                filemode='w'
            )
            logging.getLogger("haystack").setLevel(logging.DEBUG)

        self.document_store = InMemoryDocumentStore()
        self.model_name = model_name
        self.indexing_pipeline = self._build_indexing_pipeline()
        self.query_pipeline = self._build_query_pipeline()

    def _build_indexing_pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        pipeline.add_component("converter", PyPDFToDocument())
        pipeline.add_component("cleaner", DocumentCleaner())
        pipeline.add_component("splitter", DocumentSplitter(split_by="word", split_length=200))

        # FastEmbed Document Embedder (Much faster for PDF ingestion)
        pipeline.add_component("embedder", FastembedDocumentEmbedder(
            model=self.model_name,
            parallel=0  # Uses all available CPU cores via ONNX
        ))

        pipeline.add_component("writer", DocumentWriter(document_store=self.document_store))

        pipeline.connect("converter", "cleaner")
        pipeline.connect("cleaner", "splitter")
        pipeline.connect("splitter", "embedder")
        pipeline.connect("embedder", "writer")
        return pipeline

    def _build_query_pipeline(self) -> Pipeline:
        rag_template = "Context: {% for doc in documents %} {{ doc.content }} {% endfor %}\nQuestion: {{ query }}\nAnswer:"
        synthesis_template = """
        User Question: {{ query }}
        Context: {% for doc in documents %} {{ doc.content }} {% endfor %}
        Answer from DeepSeek: {{ answer_1 }}
        Answer from Qwen: {{ answer_2 }}
        Final Synthesized Answer:"""

        pipeline = Pipeline()

        # 1. FastEmbed Text Embedder for Queries
        pipeline.add_component("text_embedder", FastembedTextEmbedder(model=self.model_name))
        pipeline.add_component("retriever", InMemoryEmbeddingRetriever(document_store=self.document_store))

        # 2. Ensemble Layer
        pipeline.add_component("llm_deepseek", OpenAIGenerator(
            api_base_url="https://api.deepseek.com/v1",
            model="deepseek-reasoner",
            api_key=Secret.from_env_var("DEEPSEEK_API_KEY")
        ))

        pipeline.add_component("llm_qwen", OpenAIGenerator(
            api_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-max",
            api_key=Secret.from_env_var("DASHSCOPE_API_KEY")
        ))

        # 3. Final Synthesis
        pipeline.add_component("final_ernie", OpenAIGenerator(
            api_base_url="https://qianfan.baidubce.com/v2",
            model="ernie-4.0-turbo-8k",
            api_key=Secret.from_env_var("ERNIE_API_KEY")
        ))

        pipeline.add_component("prompt_deepseek", PromptBuilder(template=rag_template))
        pipeline.add_component("prompt_qwen", PromptBuilder(template=rag_template))
        pipeline.add_component("synthesis_prompt", PromptBuilder(template=synthesis_template))

        # Connections
        pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        pipeline.connect("retriever.documents", "prompt_deepseek.documents")
        pipeline.connect("retriever.documents", "prompt_qwen.documents")
        pipeline.connect("retriever.documents", "synthesis_prompt.documents")
        pipeline.connect("prompt_deepseek", "llm_deepseek")
        pipeline.connect("prompt_qwen", "llm_qwen")
        pipeline.connect("llm_deepseek.replies", "synthesis_prompt.answer_1")
        pipeline.connect("llm_qwen.replies", "synthesis_prompt.answer_2")
        pipeline.connect("synthesis_prompt", "final_ernie")

        return pipeline

    def ingest(self, pdf_path: str):
        path = Path(pdf_path)
        pdf_files = [str(f) for f in path.glob("*.pdf")]
        if not pdf_files:
            print(f"No PDFs found in {pdf_path}")
            return
        self.indexing_pipeline.run({"converter": {"sources": pdf_files}})

    def ask(self, question: str):
        results = self.query_pipeline.run({
            "text_embedder": {"text": question},
            "prompt_deepseek": {"query": question},
            "prompt_qwen": {"query": question},
            "synthesis_prompt": {"query": question}
        })
        return results["final_ernie"]["replies"][0]


if __name__ == '__main__':
    # Set Keys
    os.environ["DEEPSEEK_API_KEY"] = deepseek_key
    os.environ["DASHSCOPE_API_KEY"] = qwen_key
    os.environ["ERNIE_API_KEY"] = ernie_api_k

    rag = EnsembleRAG()
    rag.ingest("./pdf")

    response = rag.ask("Is it essential for multiple-case analysis to collect data from multiple datasets?")
    print(response)
