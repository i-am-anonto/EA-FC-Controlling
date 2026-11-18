import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from typing import Tuple

class HybridSearcher:
    def __init__(self, csv_path: str):
        """Initializes the in-memory hybrid search engine."""
        self.df = pd.read_csv(csv_path).fillna("")
        
        # Build enriched corpus
        self.df['search_corpus'] = (
            self.df['Action_Name'] + " " + 
            self.df['Description'] + " " + 
            self.df['Search_Intent_Tags']
        )
        
        # 1. Initialize Embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = self.model.encode(self.df['search_corpus'].tolist(), convert_to_tensor=True)
        
        # 2. Initialize BM25
        tokenized_corpus = [doc.lower().split() for doc in self.df['search_corpus']]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 3, min_stars: int = None) -> pd.DataFrame:
        """Executes the hybrid search and returns top_k results."""
        if not query.strip():
            return pd.DataFrame()

        # Semantic Score
        query_emb = self.model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_emb, self.embeddings)[0].cpu().numpy()
        
        # Keyword Score
        tokenized_query = query.lower().split()
        bm25_scores = np.array(self.bm25.get_scores(tokenized_query))
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()
            
        # Typo/Fuzzy Score
        fuzz_scores = np.array([
            fuzz.token_set_ratio(query.lower(), doc.lower()) / 100.0 
            for doc in self.df['search_corpus']
        ])
        
        # Weighted Hybrid Equation
        hybrid_scores = (0.5 * cos_scores) + (0.3 * bm25_scores) + (0.2 * fuzz_scores)
        
        # Filter by Star Rating if requested
        if min_stars:
            valid_mask = self.df['Skill_Star_Rating'].apply(
                lambda x: int(str(x)[0]) if str(x)[0].isdigit() else 0
            ) >= min_stars
            hybrid_scores = np.where(valid_mask, hybrid_scores, -1)
            
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        return self.df.iloc[top_indices]