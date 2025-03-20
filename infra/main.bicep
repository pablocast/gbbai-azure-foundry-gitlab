// ------------------
//    PARAMETERS
// ------------------

// Typically, parameters would be decorated with appropriate metadata and attributes, but as they are very repetetive in these labs we omit them for brevity.
@description('Configuration array for Inference Models')
param modelsConfig array = []

@description('The tags for the resources')
param tagValues object = {
}

// Creates Azure dependent resources for Azure AI studio

@description('Azure region of the deployment')
param location string = resourceGroup().location

@description('AI Search service name')
@minLength(2)
@maxLength(60)
param searchServiceName string = 'search'

@description('AI Search service location')
param searchServiceLocation string = resourceGroup().location

@description('AI Search service SKU')
param searchServiceSku string = 'standard'

@description('Replicas distribute search workloads across the service. You need at least two replicas to support high availability of query workloads (not applicable to the free tier).')
@minValue(1)
@maxValue(12)
param searchServiceReplicaCount int = 1

@description('Partitions allow for scaling of document count as well as faster indexing by sharding your index over multiple search units.')
@allowed([
  1
  2
  3
  4
  6
  12
])
param searchServicePartitionCount int = 1

// ------------------
//    VARIABLES
// ------------------

var resourceSuffix = uniqueString(subscription().id, resourceGroup().id)

// ------------------
//    RESOURCES
// ------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'law-${resourceSuffix}'
  location: location
  properties: any({
    retentionInDays: 30
    features: {
      searchVersion: 1
    }
    sku: {
      name: 'PerGB2018'
    }
  })
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'insights-${resourceSuffix}'
  location: location
  tags: tagValues
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    // BCP037: Not yet added to latest API: https://github.com/Azure/bicep-types-az/issues/2048
    #disable-next-line BCP037
    CustomMetricsOptedInType: 'WithDimensions'

  }
}

resource account 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'aiservices-${resourceSuffix}'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    customSubDomainName: toLower('aiservices-${resourceSuffix}')
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    disableLocalAuth: false
  }
}

@batchSize(1)
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = [for model in modelsConfig: if(length(modelsConfig) > 0) {
  name: model.name
  parent: account
  sku: {
    name: model.sku
    capacity: model.capacity
  }
  properties: {
    model: {
      format: model.publisher
      name: model.name
      version: model.version
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}]

resource storageAccount 'Microsoft.Storage/storageAccounts@2019-04-01' = {
  name: 'storage${resourceSuffix}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  identity: {
    type: 'SystemAssigned'
  }
  kind: 'StorageV2'
  properties: {
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    supportsHttpsTrafficOnly: true
  }
  tags: tagValues
}

resource keyVault 'Microsoft.KeyVault/vaults@2019-09-01' = {
  name: 'vault-${resourceSuffix}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      name: 'standard'
      family: 'A'
    }
    enableRbacAuthorization: true
    accessPolicies: []
  }
  tags: tagValues
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2019-05-01' = {
  name: 'acr${resourceSuffix}'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: true
  }
  tags: tagValues
}


resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: '${searchServiceName}-${resourceSuffix}'
  location: searchServiceLocation
  sku: {
    name: searchServiceSku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    replicaCount: searchServiceReplicaCount
    partitionCount: searchServicePartitionCount
  }
}

resource hub 'Microsoft.MachineLearningServices/workspaces@2024-07-01-preview' = {
  name: 'aihub-${resourceSuffix}'
  kind: 'Hub'
  location: location
  identity: {
    type: 'systemAssigned'
  }
  sku: {
    tier: 'Standard'
    name: 'standard'
  }
  properties: {
    description: 'Azure AI hub'
    friendlyName: 'AIHub'
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: applicationInsights.id
    containerRegistry: containerRegistry.id
    hbiWorkspace: false
  }
  tags: tagValues
}

resource project 'Microsoft.MachineLearningServices/workspaces@2024-07-01-preview' = {
  name: 'project-${resourceSuffix}'
  kind: 'Project'
  location: location
  identity: {
    type: 'systemAssigned'
  }
  sku: {
    tier: 'Standard'
    name: 'standard'
  }
  properties: {
    description: 'Azure AI project'
    friendlyName: 'AIProject'
    hbiWorkspace: false
    hubResourceId: hub.id
  }
  tags: tagValues
}


resource connection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01-preview' = {
  name:  account.name
  parent: hub
  properties: {
    category: 'AIServices'
    target: account.properties.endpoints['Azure AI Model Inference API']
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: account.id
    }
  }
}

resource hub_connection_azureai_search 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01-preview' = {
  name: searchService.name
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${searchService.name}.search.windows.net'
    authType: 'AAD'
    //useWorkspaceManagedIdentity: false
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: searchService.id
    }
  }
}

// Role assignments

// Search roles for project
resource searchIndexDataContributorRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  scope: resourceGroup()
}

resource searchIndexDataContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(project.id, searchIndexDataContributorRole.id, searchService.id)
  properties: {
    principalId: project.identity.principalId
    roleDefinitionId: searchIndexDataContributorRole.id
    principalType: 'ServicePrincipal'
  }
}

resource searchServiceContributorRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  scope: resourceGroup()
}

resource searchServiceContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: searchService
  name: guid(project.id, searchServiceContributorRole.id, searchService.id)
  properties: {
    principalId: project.identity.principalId
    roleDefinitionId: searchServiceContributorRole.id
    principalType: 'ServicePrincipal'
  }
}

// OpenAI roles for project
resource cognitiveServicesOpenAIUserRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  scope: resourceGroup()
}

resource cognitiveServicesOpenAIUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: account
  name: guid(project.id, cognitiveServicesOpenAIUserRole.id, account.id)
  properties: {
    principalId: project.identity.principalId
    roleDefinitionId: cognitiveServicesOpenAIUserRole.id
    principalType: 'ServicePrincipal'
  }
}

resource cognitiveServicesRoleSearch 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: account
  name: guid(account.id, cognitiveServicesOpenAIUserRole.id, searchService.id)
  properties: {
    principalId: searchService.identity.principalId
    roleDefinitionId: cognitiveServicesOpenAIUserRole.id
    principalType: 'ServicePrincipal'
  }
}


output projectName string = project.name
output projectId string = project.id
var projectEndoint = replace(replace(project.properties.discoveryUrl, 'https://', ''), '/discovery', '')
output projectConnectionString string = '${projectEndoint};${subscription().subscriptionId};${resourceGroup().name};${project.name}'
