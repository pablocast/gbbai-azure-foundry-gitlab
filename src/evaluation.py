import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    Dataset,
    EvaluatorConfiguration,
    ConnectionType,
)
from azure.ai.evaluation import (
    evaluate,
    F1ScoreEvaluator,
    RelevanceEvaluator,
    ViolenceEvaluator,
)
from azure.identity import DefaultAzureCredential
import json
from pathlib import Path
import os
from azure.ai.projects import AIProjectClient
import os
from azure.ai.projects.models import (
    EvaluatorConfiguration,
    ConnectionType,
)
from azure.ai.evaluation._model_configurations import AzureOpenAIModelConfiguration
from app import create_rag_agent, run_agent_query
import logging

def create_project_client():
    project_conn_str = os.environ.get("PROJECT_CONNECTION_STRING")
    credential = DefaultAzureCredential()
    project_client = AIProjectClient.from_connection_string(
        credential=credential, conn_str=project_conn_str
    )
    print("✅ Created AIProjectClient.")
    return project_client


def get_response(query: str) -> str:

    project_client = create_project_client()

    search_conn = project_client.connections.get_default(
        # Specify we want an Azure AI Search connection type
        connection_type=ConnectionType.AZURE_AI_SEARCH,
    )

    agent = create_rag_agent(
        model_name=os.environ["AZURE_OPENAI_GPT_MODEL_NAME"],
        index_name="courses",
        search_conn=search_conn,
    )

    answer = run_agent_query(agent=agent, question=query)
    logging.info(f"Answer: {answer}")
    return dict(response=answer)


def create_synthetic_eval_file(file_path):
    synthetic_eval_data = [
        {
            "query": "Quais tópicos são abordados no Curso Profissional de Data Science?",
            "context": "Curso Profissional de Data Science é um curso intensivo desenhado para profissionais que buscam aprofundar seus conhecimentos em análise de dados e aprendizado de máquina.",
            "ground_truth": "O curso aborda tópicos avançados como aprendizado de máquina, visualização de dados, análise estatística e aplicações práticas de dados.",
        },
        {
            "query": "O curso de Desenvolvimento Web ensina tecnologias web modernas?",
            "context": "Curso Profissional de Desenvolvimento Web foca no desenvolvimento web moderno em um ambiente profissional.",
            "ground_truth": "O curso enfatiza frameworks modernos, técnicas de design responsivo e as práticas atuais de desenvolvimento web.",
        },
        {
            "query": "O curso de Cibersegurança inclui estratégias de prevenção contra ameaças?",
            "context": "Curso Profissional de Cibersegurança oferece um currículo abrangente para dominar a segurança da informação e métodos de prevenção contra ameaças.",
            "ground_truth": "Sim, o curso inclui módulos detalhados sobre detecção de ameaças, prevenção e melhores práticas de cibersegurança.",
        },
        {
            "query": "Quais habilidades de gestão são desenvolvidas no curso de Gestão de Projetos?",
            "context": "Curso Profissional de Gestão de Projetos é desenhado para equipar profissionais com habilidades eficazes de gestão de projetos para ambientes corporativos.",
            "ground_truth": "O curso desenvolve habilidades em planejamento, execução, monitoramento e fechamento de projetos, além de técnicas de liderança.",
        },
    ]

    with file_path.open("w", encoding="utf-8") as f:
        for row in synthetic_eval_data:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Sample evaluation data written to {file_path.resolve()}")

    return file_path


def upload_eval_data(project_client, data_path):
    uploaded_data_id, _ = project_client.upload_file(str(data_path))
    print("✅ Uploaded JSONL to project. Data asset ID:", uploaded_data_id)

    return uploaded_data_id


def create_evaluation(project_client, uploaded_data_path):

    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-04-01-preview",
        azure_deployment=os.environ["AZURE_OPENAI_GPT_MODEL_NAME"],
    )

    f1_score = F1ScoreEvaluator()
    relevance = RelevanceEvaluator(model_config)
    violence = ViolenceEvaluator(
        credential=DefaultAzureCredential(), azure_ai_project=project_client.scope
    )

    evaluation = evaluate(
        target=get_response,
        evaluation_name="evaluate_rag_agent",
        description="Evaluating dataset for correctness.",
        data=uploaded_data_path,
        evaluators={
            "f1_score": f1_score,
            "relevance": relevance,
            "violence": violence,
        },
        evaluator_config={
            "default": {
                "query": {"${data.query}"},
                "context": {"${target.context}"},
                "ground_truth": "${data.ground_truth}",
            }
        },
        azure_ai_project=project_client.scope,
    )
    return evaluation


def main():
    eval_data_path = Path("./data/eval_data.jsonl")
    create_synthetic_eval_file(eval_data_path)
    project_client = create_project_client()
    uploaded_data_id = upload_eval_data(project_client, eval_data_path)
    evaluation = create_evaluation(project_client, eval_data_path)
    print("✅ Evaluation object created.")

if __name__ == "__main__":
    main()
