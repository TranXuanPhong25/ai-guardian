import logging
import os
from typing import List, Dict, Any, Tuple, Optional
from uuid import uuid4
from weaviate.classes.init import Auth
from weaviate.classes.data import DataObject

import weaviate
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings  # Giả sử embedding model từ config
from weaviate.collections.classes.config import Configure
from weaviate.util import generate_uuid5


class VectorStore:
    """
    Tạo vector store với Weaviate, ingest chunks text đã sẵn, retrieve relevant documents.
    """
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config  # Store config for later use
        self.collection_name = config.rag.collection_name  # Class name trong Weaviate
        self.embedding_model = config.rag.embedding_model  # Ví dụ: AzureOpenAIEmbeddings
        self.retrieval_top_k = config.rag.top_k
        self.weaviate_url = config.rag.weaviate_url  # Từ config, ví dụ: "http://localhost:8080"
        self.weaviate_api_key = config.rag.weaviate_api_key  # Từ config
        
        # Kết nối Weaviate client
        self.client = weaviate.connect_to_weaviate_cloud(
            auth_credentials=Auth.api_key(api_key=self.weaviate_api_key) if self.weaviate_api_key else None,
            cluster_url=self.weaviate_url
        )
        
        # Tạo schema nếu chưa tồn tại
        if not self.client.collections.exists(self.collection_name):
            self.client.collections.create(
                name=self.collection_name,
                vectorizer_config=Configure.Vectorizer.none(),  # Sử dụng external embeddings
                properties=[
                    weaviate.classes.config.Property(
                        name="content",
                        data_type=weaviate.classes.config.DataType.TEXT
                    ),
                    weaviate.classes.config.Property(
                        name="source",
                        data_type=weaviate.classes.config.DataType.TEXT
                    ),
                    weaviate.classes.config.Property(
                        name="doc_id",
                        data_type=weaviate.classes.config.DataType.TEXT
                    ),
                    weaviate.classes.config.Property(
                        name="user_id",
                        data_type=weaviate.classes.config.DataType.TEXT
                    ),
                ]
            )
            self.logger.info(f"Tạo class mới trong Weaviate: {self.collection_name}")
    def close_conn(self):
        self.client.close()
    def chunk_document(self, formatted_document: str) -> List[str]:
        """
        Chunk text đã sẵn thành các đoạn nhỏ (di chuyển từ content_processor.py).
        """
        # Logic chunking giống cũ: split by sections, then LLM-based semantic chunking
        # (Copy logic từ content_processor.chunk_document, bỏ phần image)
        SPLIT_PATTERN = "\n#"
        chunks = formatted_document.split(SPLIT_PATTERN)
        
        chunked_text = ""
        for i, chunk in enumerate(chunks):
            if chunk.startswith("#"):
                chunk = f"#{chunk}"
            chunked_text += f"<|start_chunk_{i}|>\n{chunk}\n<|end_chunk_{i}|>\n"
        
        CHUNKING_PROMPT = """
        # Prompt giống cũ, bỏ phần image
        """.strip()  # Copy prompt từ content_processor.py
        
        formatted_chunking_prompt = CHUNKING_PROMPT.format(document_text=chunked_text)
        chunking_response = self.config.rag.chunker_model.invoke(formatted_chunking_prompt).content
        
        # Split logic giống cũ
        # (Copy _split_text_by_llm_suggestions từ content_processor.py)
        # Trả về list chunks
        
        return chunks  # Thay bằng kết quả thực tế

    def create_vectorstore(self, document_chunks: List[str], document_path: str) -> Tuple[Any, List[str]]:
        """
        Ingest chunks text đã sẵn vào Weaviate.
        """
        doc_ids = [str(uuid4()) for _ in range(len(document_chunks))]
        
        langchain_documents = []
        for id_idx, chunk in enumerate(document_chunks):
            langchain_documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": os.path.basename(document_path),
                        "doc_id": doc_ids[id_idx],
                    }
                )
            )
        
        # Tạo embeddings
        embeddings = self.embedding_model.embed_documents([doc.page_content for doc in langchain_documents])
        
        # Upsert vào Weaviate using v4 API
        collection = self.client.collections.get(self.collection_name)
        
        data_objects = []
        for i, doc in enumerate(langchain_documents):
            # Use DataObject class for custom vectors
            data_objects.append(
                DataObject(
                    properties={
                        "content": doc.page_content,
                        "source": doc.metadata["source"],
                        "doc_id": doc.metadata["doc_id"],
                    },
                    vector=embeddings[i]
                )
            )
        
        collection.data.insert_many(data_objects)
        
        self.logger.info(f"Đã ingest {len(document_chunks)} chunks vào Weaviate")
        return self.client, doc_ids

    def retrieve_relevant_chunks(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve từ Weaviate dựa trên query.
        """
        query_embedding = self.embedding_model.embed_query(query)
        
        # Use Weaviate v4 API
        collection = self.client.collections.get(self.collection_name)
        response = collection.query.near_vector(
            near_vector=query_embedding,
            limit=self.retrieval_top_k,
            return_metadata=['distance']
        )
        
        retrieved_docs = []
        for hit in response.objects:
            doc_dict = {
                "id": hit.properties.get("doc_id", ""),
                "content": hit.properties.get("content", ""),
                "source": hit.properties.get("source", ""),
                "score": hit.metadata.distance if hit.metadata and hasattr(hit.metadata, 'distance') else 0.0,  # Distance làm score
            }
            retrieved_docs.append(doc_dict)
        
        return retrieved_docs