import logging
from typing import List, Dict, Any

class QueryExpander:
    """
    Expands user queries with relevant terminology to improve retrieval.
    """
    def __init__(self, config):
        self.logger = logging.getLogger(f"{self.__module__}")
        self.config = config
        self.model = config.rag.llm
        
    def expand_query(self, original_query: str) -> Dict[str, Any]:
        """
        Expand the original query with relevant terms and synonyms.

        Args:
            original_query: The user's original query

        Returns:
            Dictionary with original and expanded queries
        """
        self.logger.info(f"Expanding query: {original_query}")
        
        # Generate expansions - implement one of the strategies below
        expanded_query = self._generate_expansions(original_query)
        
        return {
            "original_query": original_query,
            "expanded_query": expanded_query.content
        }
    
    def _generate_expansions(self, query: str) -> str:
        """Use LLM to expand query with relevant terminology."""
        prompt = f"""
        Expand the following query with relevant terminology, synonyms, and related concepts that would help in retrieving relevant information:

        User Query: {query}

        Expand the query only if you feel like it is required, otherwise keep the user query intact.
        Be specific to the domain mentioned in the user query, do not add unrelated domains.
        If the user query asks about answering in tabular format, include that in the expanded query and do not answer in tabular format yourself.
        Provide only the expanded query without explanations.
        """
        expansion = self.model.invoke(prompt)
        
        return expansion