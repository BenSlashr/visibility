import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  FolderOpen, 
  MessageSquare, 
  BarChart3, 
  Settings,
  Eye,
  Link2
} from 'lucide-react'
import { clsx } from 'clsx'
import { ProjectSelector } from './ProjectSelector'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Dashboard V2', href: '/dashboard-v2', icon: Home },
  { name: 'Projets', href: '/projects', icon: FolderOpen },
  { name: 'Prompts', href: '/prompts', icon: MessageSquare },
  { name: 'Analyses', href: '/analyses', icon: BarChart3 },
  { name: 'Sources', href: '/sources', icon: Link2 },
  { name: 'Paramètres', href: '/settings', icon: Settings },
]

export const Sidebar: React.FC = () => {
  const location = useLocation()

  return (
    <div className="flex h-full bg-gray-900/95 backdrop-blur w-64 flex-col fixed left-0 top-0 z-20">
      {/* Logo */}
      <div className="flex items-center px-6 py-4 border-b border-gray-800/80">
        <Eye className="h-8 w-8 text-blue-400" />
        <span className="ml-3 text-white font-bold text-lg">
          Visibility
        </span>
      </div>

      {/* Sélecteur de projet */}
      <div className="px-4 py-4 border-b border-gray-800/80">
        <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
          Projet actuel
        </div>
        <ProjectSelector />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={clsx(
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800/70 hover:text-white'
              )}
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-medium">U</span>
          </div>
          <div className="text-sm">
            <p className="text-white font-medium">Utilisateur</p>
            <p className="text-gray-400">utilisateur@example.com</p>
          </div>
        </div>
      </div>
    </div>
  )
} 