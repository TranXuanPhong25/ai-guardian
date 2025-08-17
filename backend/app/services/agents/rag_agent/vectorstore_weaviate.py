import logging
import os
from typing import List, Dict, Any, Tuple, Optional
from uuid import uuid4
from weaviate.classes.init import Auth
from weaviate.classes.data import DataObject

import weaviate
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from weaviate.collections.classes.config import Configure
from weaviate.util import generate_uuid5


class VectorStore:
    """
    Tạo vector store với Weaviate, ingest chunks text đã sẵn, retrieve relevant documents.
    """
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.collection_name = config.rag.collection_name
        self.embedding_model = config.rag.embedding_model
        self.retrieval_top_k = config.rag.top_k
        self.weaviate_url = config.rag.weaviate_url
        self.weaviate_api_key = config.rag.weaviate_api_key
        self.use_hybrid_search = getattr(config.rag, "use_hybrid_search", True)  # Thêm cấu hình hybrid search
        self.hybrid_alpha = getattr(config.rag, "hybrid_alpha", 0.5)  # Trọng số giữa BM25 và semantic (0: chỉ BM25, 1: chỉ semantic)

        # Kết nối Weaviate client
        self.client = weaviate.connect_to_weaviate_cloud(
            auth_credentials=Auth.api_key(api_key=self.weaviate_api_key) if self.weaviate_api_key else None,
            cluster_url=self.weaviate_url
        )
        
        # Tạo schema nếu chưa tồn tại
        if not self.client.collections.exists(self.collection_name):
            self.client.collections.create(
                name=self.collection_name,
                vectorizer_config=Configure.Vectorizer.none(),
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
        SPLIT_PATTERN = "\n#"
        chunks = formatted_document.split(SPLIT_PATTERN)
        
        chunked_text = ""
        for i, chunk in enumerate(chunks):
            if chunk.startswith("#"):
                chunk = f"#{chunk}"
            chunked_text += f"<|start_chunk_{i}|>\n{chunk}\n<|end_chunk_{i}|>\n"
        
        CHUNKING_PROMPT = """
        # Prompt giống cũ, bỏ phần image
        """.strip()
        
        formatted_chunking_prompt = CHUNKING_PROMPT.format(document_text=chunked_text)
        chunking_response = self.config.rag.chunker_model.invoke(formatted_chunking_prompt).content
        
        return chunks

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
        
        embeddings = self.embedding_model.embed_documents([doc.page_content for doc in langchain_documents])
        
        collection = self.client.collections.get(self.collection_name)
        
        data_objects = []
        for i, doc in enumerate(langchain_documents):
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
        Retrieve từ Weaviate dựa trên query, hỗ trợ hybrid search (BM25 + semantic).
        """
        query_embedding = self.embedding_model.embed_query(query)
        collection = self.client.collections.get(self.collection_name)
        
        retrieved_docs = []
        
        if self.use_hybrid_search:
            # Thực hiện hybrid search (kết hợp BM25 và semantic)
            response = collection.query.hybrid(
                query=query,
                vector=query_embedding,
                alpha=self.hybrid_alpha,  # Trọng số giữa BM25 (0) và semantic (1)
                limit=self.retrieval_top_k,
                return_metadata=['distance', 'score']
            )
            for hit in response.objects:
                doc_dict = {
                    "id": hit.properties.get("doc_id", ""),
                    "content": hit.properties.get("content", ""),
                    "source": hit.properties.get("source", ""),
                    "score": hit.metadata.score if hit.metadata and hasattr(hit.metadata, 'score') else 0.0,
                    "search_type": "hybrid"  # Ghi nhận loại tìm kiếm
                }
                retrieved_docs.append(doc_dict)
        else:
            # Chỉ sử dụng semantic search (như cũ)
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=self.retrieval_top_k,
                return_metadata=['distance']
            )
            for hit in response.objects:
                doc_dict = {
                    "id": hit.properties.get("doc_id", ""),
                    "content": hit.properties.get("content", ""),
                    "source": hit.properties.get("source", ""),
                    "score": hit.metadata.distance if hit.metadata and hasattr(hit.metadata, 'distance') else 0.0,
                    "search_type": "semantic"
                }
                retrieved_docs.append(doc_dict)
        
        self.logger.info(f"Retrieved {len(retrieved_docs)} documents using {'hybrid' if self.use_hybrid_search else 'semantic'} search")
        return retrieved_docs