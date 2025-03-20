import os
from azure.search.documents import (
    SearchClient,
)  # For document operations (upload/search)
from azure.identity import DefaultAzureCredential  # For Azure authentication
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool, ConnectionType
from dotenv import load_dotenv

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
    # include_credentials=True means we'll get the full connection info including auth keys
    include_credentials=True,
)


def create_rag_agent(model_name: str, index_name: str, search_conn: ConnectionType):

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
    print(f"🎉 Created agent, ID: {agent.id}")

    return agent


def run_agent_query(agent: str, question: str):
    # Step 1: Create a new conversation thread
    # In Azure AI Agent service, conversations happen in threads, similar to chat conversations
    # Each thread can contain multiple back-and-forth messages
    thread = project_client.agents.create_thread()
    print(f"📝 Created thread, ID: {thread.id}")

    # Step 2: Add the user's question as a message in the thread
    # Messages have roles ("user" or "assistant") and content (the actual text)
    message = project_client.agents.create_message(
        thread_id=thread.id, role="user", content=question
    )
    print(f"💬 Created user message, ID: {message.id}")

    # Step 3: Create and start an agent run
    # This tells the agent to:
    # - Read the user's message
    # - Use its AI Search tool to find relevant products
    # - Generate a helpful response
    run = project_client.agents.create_and_process_run(
        thread_id=thread.id, agent_id=agent.id
    )
    print(f"🤖 Agent run status: {run.status}")

    # Check for any errors during the agent's processing
    if run.last_error:
        print("⚠️ Run error:", run.last_error)

    # Step 4: Get the agent's response
    # Retrieve all messages and find the most recent assistant response
    # The response might contain multiple content blocks (text, images, etc.)
    msg_list = project_client.agents.list_messages(thread_id=thread.id)
    for m in reversed(msg_list.data):
        if m.role == "assistant" and m.content:
            print("\nAssistant says:")
            for c in m.content:
                if hasattr(c, "text"):
                    print(c.text.value)
            break


if __name__ == "__main__":
    # Create the RAG agent
    agent = create_rag_agent(model_name, index_name, search_conn)

    # Run a query against the RAG agent
    run_agent_query(agent, "Tem curso Profissional de Data Science?")
