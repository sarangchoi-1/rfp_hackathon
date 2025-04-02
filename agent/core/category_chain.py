from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
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
        
    def initialize_vectorstore(self, categories: Dict):
        # Create vector store from category keywords
        texts = [f"{cat['keywords']} {cat['patterns']}" for cat in categories.values()]
        self.vectorstore = FAISS.from_texts(texts, self.embeddings)
    
    def match_categories(self, text: str) -> List[Dict]:
        # Get TF-IDF results
        tfidf_results = self.tfidf_matcher.match_task_to_categories({'description': text})
        
        # Get embedding results
        embedding_results = self.vectorstore.similarity_search_with_score(text)
        
        # Combine results with weighted scoring
        combined_results = self._combine_results(tfidf_results, embedding_results)
        
        return combined_results