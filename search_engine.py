import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from typing import Optional


def _parse_star_rating(val) -> int:
    """Safely extracts an integer star rating (0 if missing/non-skill)."""
    match = re.search(r"\d+", str(val))
    return int(match.group()) if match else 0


class HybridSearcher:
    def __init__(self, csv_path: str):
        """Initializes the in-memory hybrid search engine."""
        self.df = pd.read_csv(csv_path).fillna("")
        self.df["star_int"] = self.df["Skill_Star_Rating"].apply(_parse_star_rating)

        self.df["search_corpus"] = (
            self.df["Action_Name"].astype(str)
            + " "
            + self.df["Description"].astype(str)
            + " "
            + self.df["Search_Intent_Tags"].astype(str)
        )

        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = self.model.encode(
            self.df["search_corpus"].tolist(), convert_to_tensor=True
        )

        tokenized_corpus = [doc.lower().split() for doc in self.df["search_corpus"]]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(
        self, query: str, top_k: int = 3, max_stars: Optional[int] = None
    ) -> pd.DataFrame:
        """Executes hybrid search (Embeddings + BM25 + RapidFuzz) and returns top_k rows."""
        if not query or not query.strip():
            return pd.DataFrame()

        query_emb = self.model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_emb, self.embeddings)[0].cpu().numpy()

        tokenized_query = query.lower().split()
        bm25_scores = np.array(self.bm25.get_scores(tokenized_query))
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        fuzz_scores = np.array(
            [
                fuzz.token_set_ratio(query.lower(), doc.lower()) / 100.0
                for doc in self.df["search_corpus"]
            ]
        )

        hybrid_scores = (0.5 * cos_scores) + (0.3 * bm25_scores) + (0.2 * fuzz_scores)

        # Optional star-rating filter (off by default): keeps non-skill moves OR skills <= player's star rating
        if max_stars is not None:
            valid_mask = (self.df["star_int"] > 0) & (self.df["star_int"] <= max_stars)
            hybrid_scores = np.where(valid_mask, hybrid_scores, -1.0)

        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        valid_indices = [i for i in top_indices if hybrid_scores[i] > 0]
        return self.df.iloc[valid_indices]
