from promptflow.client import load_run, PFClient
from azure.identity import InteractiveBrowserCredential
import os
from dotenv import load_dotenv

load_dotenv(override=True)

credential = InteractiveBrowserCredential()

run = load_run(source="src/evaluation_flow/run.yml")

pf = PFClient(
    credential=credential,
    subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),  
    resource_group_name=os.getenv("AZURE_RESOURCE_GROUP"),
    workspace_name=os.getenv("AZURE_AML_WORKSPACE"),
)
pf.runs.create_or_update(
    run=run
)