from typing import List
from promptflow import tool, log_metric
import numpy as np


@tool
def aggregate_variants_results(similarity_score: str):
    # Split the similarity score string into individual scores
    aggregate_results = {'gpt_similarity': similarity_score}

    return aggregate_results