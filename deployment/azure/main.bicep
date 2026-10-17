// ==============================================================================
// Azure Bicep Infrastructure Deployment for NIFTY-Pulse Platform
// Provisions: Log Analytics, Container Apps Environment, Container App, Key Vault
// ==============================================================================

@description('Azure Region for NIFTY-Pulse deployment')
param location string = 'centralindia'

@description('Application environment (e.g. production, staging)')
param environmentName string = 'production'

@description('Container Image Tag to deploy (e.g. acrniftypulse.azurecr.io/nifty-pulse:latest)')
param containerImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

@description('Unique suffix for resource naming')
param appSuffix string = uniqueString(resourceGroup().id)

var logAnalyticsWorkspaceName = 'law-niftypulse-${appSuffix}'
var containerAppEnvName = 'cae-niftypulse-${appSuffix}'
var containerAppName = 'ca-niftypulse-${appSuffix}'
var keyVaultName = 'kv-np-${take(appSuffix, 18)}'

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

// 3. Azure Key Vault for Secure API Secrets
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

// 4. Azure Container App (NIFTY-Pulse Backend & Dashboard)
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'nifty-pulse'
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
              value: '8000'
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
                path: '/api/health'
                port: 8000
              }
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/api/ready'
                port: 8000
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
                concurrentRequests: '50'
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
