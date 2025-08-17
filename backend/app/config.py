"""
Configuration file for the General Document Q&A System

This file contains all the configuration parameters for the project.

If you want to change the LLM and Embedding model:
you can do it by changing all 'llm' and 'embedding_model' variables present in multiple classes below.
Each llm definition has unique temperature value relevant to the specific class.
"""

import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

# Load environment variables from .env file
load_dotenv()

class AgentDecisionConfig:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("deployment_name"),
            model_name=os.getenv("model_name"),
            azure_endpoint=os.getenv("azure_endpoint"),
            openai_api_key=os.getenv("openai_api_key"),
            openai_api_version=os.getenv("openai_api_version"),
            temperature=0.1  # Deterministic for factual accuracy
        )

class ConversationConfig:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("deployment_name"),
            model_name=os.getenv("model_name"),
            azure_endpoint=os.getenv("azure_endpoint"),
            openai_api_key=os.getenv("openai_api_key"),
            openai_api_version=os.getenv("openai_api_version"),
            temperature=0.7  # Creative but factual for general Q&A
        )

class RAGConfig:
    def __init__(self):
        self.vector_db_type = "weaviate"  # Cập nhật sang Weaviate
        self.embedding_dim = 1536
        self.distance_metric = "Cosine"
        self.weaviate_url = os.getenv("WEAVIATE_URL")  # Thêm URL cho Weaviate
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY")  # Thêm API key cho Weaviate
        self.collection_name = "document_assistance_rag"
        self.chunk_size = 512
        self.chunk_overlap = 50
        self.embedding_model = AzureOpenAIEmbeddings(
            deployment=os.getenv("embedding_deployment_name"),
            model=os.getenv("embedding_model_name"),
            azure_endpoint=os.getenv("embedding_azure_endpoint"),
            openai_api_key=os.getenv("embedding_openai_api_key"),
            openai_api_version=os.getenv("embedding_openai_api_version")
        )
        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("deployment_name"),
            model_name=os.getenv("model_name"),
            azure_endpoint=os.getenv("azure_endpoint"),
            openai_api_key=os.getenv("openai_api_key"),
            openai_api_version=os.getenv("openai_api_version"),
            temperature=0.3
        )
        self.summarizer_model = AzureChatOpenAI(
            deployment_name=os.getenv("deployment_name"),
            model_name=os.getenv("model_name"),
            azure_endpoint=os.getenv("azure_endpoint"),
            openai_api_key=os.getenv("openai_api_key"),
            openai_api_version=os.getenv("openai_api_version"),
            temperature=0.5
        )
        self.chunker_model = AzureChatOpenAI(
            deployment_name=os.getenv("deployment_name"),
            model_name=os.getenv("model_name"),
            azure_endpoint=os.getenv("azure_endpoint"),
            openai_api_key=os.getenv("openai_api_key"),
            openai_api_version=os.getenv("openai_api_version"),
            temperature=0.0
        )
        self.response_generator_model = AzureChatOpenAI(
            deployment_name=os.getenv("deployment_name"),
            model_name=os.getenv("model_name"),
            azure_endpoint=os.getenv("azure_endpoint"),
            openai_api_key=os.getenv("openai_api_key"),
            openai_api_version=os.getenv("openai_api_version"),
            temperature=0.3
        )
        self.top_k = 8
        self.vector_search_type = 'similarity'
        self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        self.reranker_model = "cross-encoder/ms-marco-TinyBERT-L-6"
        self.reranker_top_k = 5
        self.max_context_length = 8192
        self.include_sources = True
        self.min_retrieval_confidence = 0.7  # Điều chỉnh cho Weaviate (distance-based)
        self.context_limit = 20  # Last 20 messages (10 Q&A pairs) in history

class APIConfig:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 8000
        self.debug = True
        self.rate_limit = 10

class UIConfig:
    def __init__(self):
        self.theme = "light"

class Config:
    def __init__(self):
        self.agent_decision = AgentDecisionConfig()
        self.conversation = ConversationConfig()
        self.rag = RAGConfig()
        self.api = APIConfig()
        self.ui = UIConfig()
        self.max_conversation_history = 20