import os
from azure.identity import DefaultAzureCredential  # For Azure authentication
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool, ConnectionType, MessageRole
from dotenv import load_dotenv
from typing import List
from handler import MyEventHandler


load_dotenv(override=True)

model_name = os.environ["AZURE_OPENAI_GPT_MODEL_NAME"]
index_name = "courses"

# Project connection string
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["PROJECT_CONNECTION_STRING"],
)

# Search connection
search_conn = project_client.connections.get_default(
    # Specify we want an Azure AI Search connection type
    connection_type=ConnectionType.AZURE_AI_SEARCH,
)

ai_search_tool = AzureAISearchTool(
    index_connection_id=search_conn.id, index_name=index_name
)
# Create an AI agent that can understand natural language and search our index
# - The agent uses our Azure OpenAI model for natural language understanding
# - We give it instructions to act as a fitness shopping assistant
# - We attach the search tool so it can look up products
# - tool_resources provides the connection details the tool needs
agent = project_client.agents.create_agent(
    model=model_name,
    name="agent-search",
    instructions="""
    Você é Virtual com acesso às buscas no Azure Search, um assessor virtual amigável especializado em recomendar cursos virtuais.
    **Sempre use o Azure Search para recomendar cursos**
    **Não use seu conhecimento prévio.**
    Lembre sempre os usuários: Não sou um assessor acadêmico oficial.
    Forneça recomendações claras de cursos, explique brevemente cada um e incentive os usuários a explorar oportunidades de aprendizagem virtual.
    
    Sempre:
    1. Forneça um aviso de isenção, indicando que você não é um profissional academico.
    2. Incentive a consulta com um profissional.
    3. Sempre use o Azure Search.
    4. Ofereça respostas breves e úteis.
    """,
    tools=ai_search_tool.definitions,
    tool_resources=ai_search_tool.resources,
    headers={"x-ms-enable-preview": "true"},  # Habilitar recursos de preview
)

global thread
thread = project_client.agents.create_thread()

print(f"🎉 Created agent, ID: {agent.id}")


def azure_enterprise_chat(question: str, chat_history=[]) -> str:
    """
    Accumulates partial function arguments into ChatMessage['content'], sets the
    corresponding tool bubble status from "pending" to "done" on completion,
    and also handles non-function calls like bing_grounding or file_search by appending a
    "pending" bubble. Then it moves them to "done" once tool calls complete.

    This function returns a list of ChatMessage objects directly (no dict conversion).
    Your Gradio Chatbot should be type="messages" to handle them properly.
    """
    print(f"User message: {question}")
    # Convert existing history from dict to ChatMessage
    conversation = []
    for msg_dict in chat_history:
        conversation.append(msg_dict)

    # Append the user's new message
    conversation.append(dict(role="user", content=question))
    
    # Post user message to the thread (for your back-end logic)
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=question
    )

    print(f"Created message, message ID {message.id}")

    with project_client.agents.create_stream(
        thread_id=thread.id, agent_id=agent.id, event_handler=MyEventHandler()
    ) as stream:
        stream.until_done()

    response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
        MessageRole.AGENT
    )
    # Print the agent's response
    if response_message:
        for text_message in response_message.text_messages:
            print(f"Agent response: {text_message.text.value}")
    
        return text_message.text.value


     
if __name__ == "__main__":
    # Run a query against the RAG agent
    azure_enterprise_chat(
        agent, "Tem curso Profissional de Data Science?", []
    )

  
