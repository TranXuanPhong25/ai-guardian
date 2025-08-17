import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import CrossEncoder

class Reranker:
    """
    Reranks retrieved documents using a cross-encoder model for more accurate results.
    """
    def __init__(self, config):
        """
        Initialize the reranker with configuration.
        
        Args:
            config: Configuration object containing reranker settings
        """
        self.logger = logging.getLogger(__name__)
        try:
            self.model_name = config.rag.reranker_model
            self.logger.info(f"Loading reranker model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            self.top_k = config.rag.reranker_top_k
        except Exception as e:
            self.logger.error(f"Error loading reranker model: {e}")
            raise
    
    def rerank(self, query: str, documents: Union[List[Dict[str, Any]], List[str]], parsed_content_dir: str) -> List[Dict[str, Any]]:
        """
        Rerank documents based on query relevance using cross-encoder.
        
        Args:
            query: User query
            documents: Either a list of documents (dictionaries) or a list of strings
            
        Returns:
            Reranked list of documents with updated scores
        """
        try:
            if not documents:
                return []
            
            if documents:
                if isinstance(documents[0], str):
                    docs_list = []
                    for i, doc_text in enumerate(documents):
                        docs_list.append({
                            "id": i,
                            "content": doc_text,
                            "score": 1.0,
                            "search_type": "unknown"
                        })
                    documents = docs_list
                elif isinstance(documents[0], dict):
                    for i, doc in enumerate(documents):
                        if "id" not in doc:
                            doc["id"] = i
                        if "score" not in doc:
                            doc["score"] = 1.0
                        if "content" not in doc:
                            if "text" in doc:
                                doc["content"] = doc["text"]
                            else:
                                doc["content"] = f"Document {i}"
                        if "search_type" not in doc:
                            doc["search_type"] = "semantic"
            
            pairs = [(query, doc["content"]) for doc in documents]
            scores = self.model.predict(pairs)
            
            for i, score in enumerate(scores):
                documents[i]["rerank_score"] = float(score)
                documents[i]["combined_score"] = (documents[i]["score"] + float(score)) / 2
            
            reranked_docs = sorted(documents, key=lambda x: x["combined_score"], reverse=True)
            
            if self.top_k and len(reranked_docs) > self.top_k:
                reranked_docs = reranked_docs[:self.top_k]
            
            picture_reference_paths = []
            for doc in reranked_docs:
                matches = re.finditer(r"picture_counter_(\d+)", doc["content"])
                for match in matches:
                    counter_value = int(match.group(1))
                    doc_basename = os.path.splitext(doc['source'])[0]
                    picture_path = os.path.join("http://localhost:8000/", parsed_content_dir + "/" + f"{doc_basename}-picture-{counter_value}.png")
                    picture_reference_paths.append(picture_path)
            
            return reranked_docs, picture_reference_paths
            
        except Exception as e:
            self.logger.error(f"Error during reranking: {e}")
            self.logger.warning("Falling back to original ranking")
            return documents