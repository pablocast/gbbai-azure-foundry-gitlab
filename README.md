# <img src="./utils/media/ai_foundry.png" alt="Azure Foundry" style="width:80px;height:30px;"/> Gitlab Integation with Azure AI Foundry

This directory exemplifies the integration between Gitlab and Azure AI Foundry

## Instructions

1. **Python Environment Setup**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create the infrastructure**
This sample uses [`azd`](https://learn.microsoft.com/azure/developer/azure-developer-cli/) and a bicep template to deploy all Azure resources:

   - Login to your Azure account: `azd auth login`

   - Create an environment: `azd env new`

   - Run `azd up`.

      + Choose your Azure subscription.
      + Enter a region for the resources.

      The deployment creates multiple Azure resources and runs multiple jobs. It takes several minutes to complete. The deployment is complete when you get a command line notification stating "SUCCESS: Your up workflow to provision and deploy to Azure completed."

3. **Indexing Documents**
   - Run the  [indexing-aisearch notebook](notebooks/indexing-aisearch.ipynb) to create an index for the agent


4. **Trigger an evaluation pipeline from GitLab**


4. **Delete the Resources**
  

