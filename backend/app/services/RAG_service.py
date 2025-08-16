import os
from typing import List, Optional
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import google.generativeai as genai

class GeminiChat:
    """Adapter for using Gemini in the pipeline."""
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        genai.configure(api_key=api_key or os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name)

    def __call__(self, input_data: dict) -> str:
        if isinstance(input_data, dict) and "context" in input_data and "question" in input_data:
            prompt_text = input_data["context"] + "\n\nQuestion: " + input_data["question"]
        else:
            prompt_text = str(input_data)
        response = self.model.generate_content(prompt_text)
        return response.text

class RAGPipelineService:
    """Service to manage the RAG pipeline for web backend."""
    def __init__(self, text: str, embedding_model_name: str = 'BAAI/bge-m3', model_name: str = "gemini-2.5-flash", 
                 api_key: Optional[str] = None, chunk_size: int = 1000, chunk_overlap: int = 20, k: int = 2):
        """
        Initialize the RAG pipeline with input text and configuration parameters.

        Args:
            text: Input text to create the vector store.
            embedding_model_name: Name of the embedding model.
            model_name: Name of the LLM (Gemini).
            api_key: API key for Gemini.
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between chunks.
            k: Number of relevant documents to retrieve.
        """
        self.embedding_model_name: str = embedding_model_name
        self.model_name: str = model_name
        self.api_key: Optional[str] = api_key or os.getenv("GOOGLE_API_KEY")
        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap
        self.k: int = k
        self.vector_store: Optional[FAISS] = None
        self.embedding_model: Optional[HuggingFaceEmbeddings] = None
        self.llm: Optional[GeminiChat] = None
        self._initialize_pipeline(text)

    def _initialize_pipeline(self, text: str) -> None:
        """Initialize the pipeline: split text, create embeddings, and set up LLM."""
        documents = self._split_text(text)
        self.vector_store = self._create_vector_store(documents)
        self.llm = GeminiChat(model_name=self.model_name, api_key=self.api_key)

    def _split_text(self, text: str) -> List[Document]:
        """Split text into chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        chunks = text_splitter.split_text(text)
        return [Document(page_content=chunk) for chunk in chunks]

    def _create_vector_store(self, documents: List[Document]) -> FAISS:
        """Create vector store from documents."""
        if not self.embedding_model:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True}
            )
        return FAISS.from_documents(documents, self.embedding_model)

    def _embed_query(self, query: str) -> List[float]:
        """Embed a query string."""
        if not self.embedding_model:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True}
            )
        return self.embedding_model.embed_query(query)

    async def query_documents(self, query: str) -> str:
        """Embed query, retrieve relevant documents, and create a prompt."""
        query_embedding = self._embed_query(query)
        docs = self.vector_store.similarity_search_by_vector(query_embedding, k=self.k)
        context = "\n\n".join(doc.page_content for doc in docs)

        # New prompt template for better LLM understanding
        template = (
            "You are an assistant for question-answering tasks. Use the following pieces of "
            "retrieved context to answer the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the answer concise."
            "\n\nContext:\n{context}\n\nQuestion:\n{question}\n\n:"
        )
        prompt = ChatPromptTemplate.from_template(template)
        prompt_data = {"context": context, "question": query}
        return prompt.format(**prompt_data)

    async def generate_response(self, query: str) -> str:
        """Process query and return response from LLM."""
        prompt_data = await self.query_documents(query)
        response = self.llm(prompt_data)
        return response

rag_pipeline_service = RAGPipelineService
