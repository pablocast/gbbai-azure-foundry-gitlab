using './main.bicep'

param principalId = readEnvironmentVariable('AZURE_PRINCIPAL_ID', 'principalId')
param modelsConfig = [
  {
    name: 'gpt-4o'
    publisher: 'OpenAI'
    version: '2024-08-06'
    sku: 'GlobalStandard'
    capacity: 30
  }
  {
    name: 'text-embedding-ada-002'
    publisher: 'OpenAI'
    version: '2'
    sku: 'Standard'
    capacity: 30
  }
]

param embedingsDimension = 1536
