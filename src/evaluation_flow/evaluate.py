import os
from azure.ai.evaluation import RelevanceEvaluator, F1ScoreEvaluator, GroundednessEvaluator
from azure.ai.evaluation._model_configurations import AzureOpenAIModelConfiguration
from dotenv import load_dotenv

load_dotenv()

model_config = AzureOpenAIModelConfiguration(
        api_key=os.environ["AZURE_OPENAI_API_KEY"], 
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-04-01-preview",
        azure_deployment=os.environ["AZURE_OPENAI_GPT_MODEL_NAME"],
    )

class Evaluator:
    def __init__(self):
        self.relevance_evaluator = RelevanceEvaluator(model_config=model_config)
        self.f1_evaluator = F1ScoreEvaluator()
        self.groundedness_evaluator = GroundednessEvaluator(model_config=model_config)

    def __call__(self, query:str, response:str, ground_truth:str, context:str):
        """Evaluate the code based on correctness, readability."""
        relevance_result = self.relevance_evaluator(
            query=query,
            response=response,
        ) 

        f1_result = self.f1_evaluator(
            response=response,
            ground_truth=ground_truth,
        )

        groundedness_result = self.groundedness_evaluator(
            response=response,
            context=(context),
        )

        output = {
            "f1_score": f1_result,
            "relevance": relevance_result["relevance"],
            "relevance_reason": relevance_result["relevance_reason"],
            "groundedness": groundedness_result["groundedness"],
            "groundedness_reason": groundedness_result["groundedness_reason"],
        }

        return output

    def __aggregate__(self, line_results: list) -> dict:
        """Aggregate the results."""
        total = len(line_results)
        avg_groundedness = sum(int(r["groundedness"]) for r in line_results) / total
        avg_relevance = sum(int(r["relevance"]) for r in line_results) / total
        avg_f1_score = sum(int(r["f1_score"]) for r in line_results) / total
        
        return {
            "avg_f1_score": avg_f1_score,
            "avg_relevance": avg_relevance,
            "avg_groundedness": avg_groundedness,
            "total": total,
        }