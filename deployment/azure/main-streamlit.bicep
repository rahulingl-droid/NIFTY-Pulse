// ==============================================================================
// Azure Bicep Infrastructure Deployment for NIFTY-Pulse Streamlit Dashboard
// Provisions: Log Analytics, Container Apps Environment, Container App (Port 8501)
// ==============================================================================

@description('Azure Region for NIFTY-Pulse Streamlit deployment')
param location string = 'centralindia'

@description('Application environment (e.g. production, staging)')
param environmentName string = 'production'

@description('Container Image Tag to deploy (e.g. acrniftypulse.azurecr.io/nifty-pulse-streamlit:latest)')
param containerImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

@description('Unique suffix for resource naming')
param appSuffix string = uniqueString(resourceGroup().id)

var logAnalyticsWorkspaceName = 'law-nifty-st-${appSuffix}'
var containerAppEnvName = 'cae-nifty-st-${appSuffix}'
var containerAppName = 'ca-nifty-st-${appSuffix}'
var keyVaultName = 'kv-np-st-${take(appSuffix, 15)}'

// 1. Azure Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// 2. Azure Container Apps Managed Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// 3. Azure Key Vault for Secure Secrets
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// 4. Azure Container App (Streamlit Dashboard on Port 8501)
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8501
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'nifty-pulse-streamlit'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2.0Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: environmentName
            }
            {
              name: 'PORT'
              value: '8501'
            }
            {
              name: 'AZURE_REGION'
              value: location
            }
            {
              name: 'AZURE_KEY_VAULT_NAME'
              value: keyVaultName
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/_stcore/health'
                port: 8501
              }
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/_stcore/health'
                port: 8501
              }
              periodSeconds: 15
              failureThreshold: 2
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '40'
              }
            }
          }
        ]
      }
    }
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output keyVaultNameOutput string = keyVault.name
