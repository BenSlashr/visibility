import { ApiClient } from '../services/api'
import { ProjectsAPI } from '../services/projects'
import { AnalysesAPI } from '../services/analyses'
import { AIModelsAPI } from '../services/aiModels'
import { PromptsAPI } from '../services/prompts'

interface TestResult {
  name: string
  success: boolean
  responseTime: number
  error?: string
  data?: any
}

export const testAPI = async (): Promise<TestResult[]> => {
  console.log('🧪 Démarrage des tests de connexion API...')
  
  const results: TestResult[] = []
  
  // Test 1: Connexion de base
  console.log('🔍 Test 1: Connexion de base')
  const connectionTest = await testEndpoint(
    'Connexion de base',
    () => ApiClient.testConnection()
  )
  results.push(connectionTest)
  
  // Test 2: Récupération des projets
  console.log('🔍 Test 2: API Projets')
  const projectsTest = await testEndpoint(
    'API Projets - Liste',
    () => ProjectsAPI.getAll({ limit: 5 })
  )
  results.push(projectsTest)
  
  // Test 3: Récupération des modèles IA actifs
  console.log('🔍 Test 3: API Modèles IA')
  const aiModelsTest = await testEndpoint(
    'API Modèles IA - Actifs',
    () => AIModelsAPI.getActive()
  )
  results.push(aiModelsTest)
  
  // Test 4: Statistiques globales
  console.log('🔍 Test 4: API Analyses - Stats')
  const statsTest = await testEndpoint(
    'API Analyses - Stats globales',
    () => AnalysesAPI.getGlobalStats()
  )
  results.push(statsTest)
  
  // Test 5: Analyses récentes
  console.log('🔍 Test 5: API Analyses - Récentes')
  const recentTest = await testEndpoint(
    'API Analyses - Récentes',
    () => AnalysesAPI.getRecent(7, 5)
  )
  results.push(recentTest)
  
  // Test 6: Prompts
  console.log('🔍 Test 6: API Prompts')
  const promptsTest = await testEndpoint(
    'API Prompts - Liste',
    () => PromptsAPI.getAll({ limit: 5 })
  )
  results.push(promptsTest)
  
  // Affichage du résumé
  const successCount = results.filter(r => r.success).length
  const totalCount = results.length
  
  console.log(`\n📊 Résumé des tests: ${successCount}/${totalCount} réussis`)
  
  results.forEach(result => {
    const status = result.success ? '✅' : '❌'
    const time = `${result.responseTime}ms`
    console.log(`${status} ${result.name} (${time})`)
    
    if (!result.success && result.error) {
      console.log(`   Erreur: ${result.error}`)
    }
  })
  
  return results
}

// Fonction utilitaire pour tester un endpoint
async function testEndpoint(
  name: string,
  testFunction: () => Promise<any>
): Promise<TestResult> {
  const startTime = Date.now()
  
  try {
    const data = await testFunction()
    const responseTime = Date.now() - startTime
    
    return {
      name,
      success: true,
      responseTime,
      data
    }
  } catch (error) {
    const responseTime = Date.now() - startTime
    const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue'
    
    return {
      name,
      success: false,
      responseTime,
      error: errorMessage
    }
  }
}

// Fonction pour afficher les résultats dans une modal (mode dev)
export const showTestResults = async (): Promise<void> => {
  const results = await testAPI()
  
  // Créer une modal simple pour afficher les résultats
  const modal = document.createElement('div')
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    font-family: monospace;
  `
  
  const content = document.createElement('div')
  content.style.cssText = `
    background: white;
    padding: 20px;
    border-radius: 8px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
  `
  
  const successCount = results.filter(r => r.success).length
  const totalCount = results.length
  
  content.innerHTML = `
    <h2>🧪 Tests de connexion API</h2>
    <p><strong>Résumé:</strong> ${successCount}/${totalCount} tests réussis</p>
    <hr>
    ${results.map(result => `
      <div style="margin: 10px 0; padding: 10px; background: ${result.success ? '#f0f9ff' : '#fef2f2'}; border-radius: 4px;">
        <div style="font-weight: bold; color: ${result.success ? '#059669' : '#dc2626'};">
          ${result.success ? '✅' : '❌'} ${result.name}
        </div>
        <div style="font-size: 12px; color: #666;">
          Temps de réponse: ${result.responseTime}ms
        </div>
        ${result.error ? `<div style="color: #dc2626; font-size: 12px;">Erreur: ${result.error}</div>` : ''}
      </div>
    `).join('')}
    <hr>
    <button onclick="this.parentElement.parentElement.remove()" style="
      background: #3b82f6;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
    ">Fermer</button>
  `
  
  modal.appendChild(content)
  document.body.appendChild(modal)
  
  // Fermer en cliquant sur l'overlay
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove()
    }
  })
} 