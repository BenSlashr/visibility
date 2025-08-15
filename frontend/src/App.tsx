import { Routes, Route } from 'react-router-dom'
import { DashboardPage } from './pages/DashboardPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { PromptsPage } from './pages/PromptsPage'
import { AnalysesPage } from './pages/AnalysesPage'
import { SettingsPage } from './pages/SettingsPage'
import { DashboardV2Page } from './pages/DashboardV2Page'
import { DashboardV3Page } from './pages/DashboardV3Page'
import { SourcesPage } from './pages/SourcesPage'
import { Sidebar } from './components/Sidebar'
import { ProjectProvider } from './contexts/ProjectContext'

function App() {
  return (
    <ProjectProvider>
      <div className="flex h-screen bg-gray-50 dark:bg-[#0b1220] overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <div className="flex-1 ml-64 overflow-auto">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dashboard-v2" element={<DashboardV2Page />} />
            <Route path="/dashboard-v3" element={<DashboardV3Page />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/prompts" element={<PromptsPage />} />
            <Route path="/analyses" element={<AnalysesPage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </div>
    </ProjectProvider>
  )
}

// HomePage n'est plus utilisé; supprimé pour éviter les warnings linter

export default App 