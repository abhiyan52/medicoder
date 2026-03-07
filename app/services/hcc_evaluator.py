"""
    author: @abhiyanhaze
    description: Simple HCC relevance checker
"""

import polars as pl
from app.utils.text import normalize_icd

class HCCRelevanceEvaluator:

    def __init__(self, csv_path):
        df = pl.read_csv(csv_path)
        self.df = df.with_columns(
            pl.col("ICD-10-CM Codes")
            .str.strip_chars()
            .str.to_uppercase()
            .str.replace_all(".", "", literal=True)
            .alias("normalised code")
        )
        self.hcc_codes = set(self.df["normalised code"].drop_nulls())

    def evaluate(self, conditions: list[dict]) -> list[dict]:
        results = []

        for c in conditions:
            raw_code = c.get("code")
            if raw_code:
                code = normalize_icd(raw_code)
                hcc_relevant = code in self.hcc_codes
            else:
                hcc_relevant = False

            results.append({
                **c,
                "hcc_relevant": hcc_relevant
            })

        return results 
