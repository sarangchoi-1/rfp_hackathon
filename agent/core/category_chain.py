from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Dict
import numpy as np
from .category_matcher import CategoryMatcher

class CategoryChain:
    def __init__(self):
        # Keep existing TF-IDF for initial matching
        self.tfidf_matcher = CategoryMatcher()
        
        # Add LangChain components
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        
        # Initialize with default categories
        self._initialize_vectorstore()
        
    def _initialize_vectorstore(self):
        """Initialize the vector store with categories."""
        # Create text representations that combine keywords and patterns
        texts = []
        for category_id, cat in self.tfidf_matcher.categories.items():
            # Combine keywords and patterns for better matching
            keywords_text = " ".join(cat.get("keywords", []))
            patterns_text = " ".join(cat.get("patterns", []))
            
            # Create a rich text representation
            text = f"{category_id} - {keywords_text} {patterns_text}"
            texts.append(text)
            
        if texts:
            self.vectorstore = FAISS.from_texts(texts, self.embeddings)
        else:
            raise ValueError("No categories provided for vectorstore initialization")
        
    def match_categories(self, text: str) -> List[Dict]:
        """Match categories using both TF-IDF and embeddings."""
        # Get TF-IDF matches
        tfidf_results = self.tfidf_matcher.match_task_to_categories({"description": text})
        
        # Get embedding matches
        embedding_results = self.vectorstore.similarity_search_with_score(text, k=3)
        
        # Combine results
        return self._combine_results(tfidf_results, embedding_results)
        
    def _combine_results(self, tfidf_results: List[Dict], embedding_results: List[tuple]) -> List[Dict]:
        """Combine results from both matching methods."""
        # Convert embedding results to same format as TF-IDF
        embedding_matches = []
        for doc, score in embedding_results:
            category_id = doc.page_content.split(" - ")[0]
            # Create match in same format as TF-IDF results
            match = {
                "category_id": category_id,
                "score": score,
                "name": category_id,  # Use category_id as name for consistency
                "weighted_score": score  # No weight adjustment for embedding results
            }
            embedding_matches.append(match)
        
        # Combine and deduplicate results
        all_results = {r["category_id"]: r for r in tfidf_results}
        
        # Update with embedding results if they have higher scores
        for match in embedding_matches:
            category_id = match["category_id"]
            if category_id not in all_results or match["score"] > all_results[category_id]["score"]:
                all_results[category_id] = match
        
        # Convert back to list and sort by weighted score
        results = list(all_results.values())
        results.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        return results

def create_category_chain() -> CategoryChain:
    """Create a new CategoryChain instance."""
    return CategoryChain()