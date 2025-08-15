import React, { useEffect, useMemo, useState } from 'react'
import { useCurrentProject } from '../contexts/ProjectContext'
import { Button, Input, Loading, Card, Select, Badge } from '../components/ui'
import { Link2, Globe2, List, Grid3X3, RefreshCw, X } from 'lucide-react'
import { ApiClient } from '../services/api'
import { PromptsAPI } from '../services/prompts'
import { Modal } from '../components/ui/Modal'
import { AnalysesAPI } from '../services/analyses'

interface SourceListItem {
  id: string
  analysis_id: string
  prompt_id: string
  prompt_name: string
  ai_model_used: string
  url: string
  domain?: string
  title?: string
  snippet?: string
  citation_label?: string
  created_at: string
}

interface SourceDomainSummary {
  id: string
  domain: string
  pages: number
  analyses: number
  me_mentions: number
  me_links: number
  competitor_mentions: number
  me_link_rate: number
  me_mention_rate: number
  first_seen?: string
  last_seen?: string
}

type Tab = 'list' | 'domains' | 'opportunities'

export const SourcesPage: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const [tab, setTab] = useState<Tab>('list')
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState<string>('')
  const [items, setItems] = useState<SourceListItem[]>([])
  const [domains, setDomains] = useState<SourceDomainSummary[]>([])
  const [opportunities, setOpportunities] = useState<SourceDomainSummary[]>([])
  const [hasLink, setHasLink] = useState<string>('')
  const [excludeCompetitors, setExcludeCompetitors] = useState<boolean>(true)
  const [uniqueByDomain, setUniqueByDomain] = useState<boolean>(false)
  const [sort, setSort] = useState<string>('date_desc')
  const [dateRange, setDateRange] = useState<string>('last30')
  const [domainView, setDomainView] = useState<'top' | 'me' | 'eco'>('top')
  const [domainSortKey, setDomainSortKey] = useState<'domain' | 'pages' | 'analyses' | 'me_links' | 'me_link_rate' | 'me_mentions' | 'eco'>('analyses')
  const [domainSortDir, setDomainSortDir] = useState<'asc' | 'desc'>('desc')
  const [tag, setTag] = useState<string>('')
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [debouncedSearch, setDebouncedSearch] = useState<string>('')
  const [domainFilter, setDomainFilter] = useState<string>('')
  const [brandMentioned, setBrandMentioned] = useState<string>('')
  const [openAnalysisId, setOpenAnalysisId] = useState<string>('')
  const [openAnalysis, setOpenAnalysis] = useState<any | null>(null)

  const projectId = currentProject?.id

  const fetchData = async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      if (tab === 'list') {
        const data = await ApiClient.get<SourceListItem[]>(`/sources/`, {
          project_id: projectId,
          search: debouncedSearch || undefined,
          has_link: hasLink || undefined,
          exclude_competitors: excludeCompetitors,
          unique_by_domain: uniqueByDomain,
          sort,
          date_range: dateRange,
          tag: tag || undefined,
          domain: domainFilter || undefined,
          brand_mentioned: brandMentioned ? (brandMentioned === 'true') : undefined,
        })
        setItems(data)
      } else if (tab === 'domains') {
        const data = await ApiClient.get<SourceDomainSummary[]>(`/sources/domains`, {
          project_id: projectId,
          search: debouncedSearch || undefined,
          exclude_competitors: excludeCompetitors,
          date_range: dateRange,
          tag: tag || undefined,
        })
        setDomains(data)
      } else {
        const data = await ApiClient.get<SourceDomainSummary[]>(`/sources/opportunities`, {
          project_id: projectId,
          exclude_competitors: excludeCompetitors,
          date_range: dateRange,
          tag: tag || undefined,
        })
        setOpportunities(data)
      }
    } catch (e: any) {
      setError(e?.message || 'Erreur inconnue')
    } finally {
      setLoading(false)
    }
  }

  // Charger une analyse pour la modale
  const openAnalysisModal = async (analysisId: string) => {
    try {
      setOpenAnalysisId(analysisId)
      const data = await AnalysesAPI.getById(analysisId)
      setOpenAnalysis(data)
    } catch (e) {
      setOpenAnalysis(null)
    }
  }

  // Débounce de la recherche pour éviter trop d'appels
  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search.trim()), 400)
    return () => clearTimeout(id)
  }, [search])

  // Rafraîchir automatiquement à chaque changement de filtre
  useEffect(() => {
    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, projectId, debouncedSearch, hasLink, excludeCompetitors, uniqueByDomain, sort, dateRange, tag, domainFilter, brandMentioned])

  // Charger les tags disponibles depuis les prompts du projet
  useEffect(() => {
    const loadTags = async () => {
      if (!projectId) { setAvailableTags([]); return }
      try {
        const prompts = await PromptsAPI.getAll({ project_id: projectId })
        const tagSet = new Set<string>()
        for (const p of prompts as any[]) {
          const tags: string[] = (p.tags || [])
          tags.forEach(t => tagSet.add(t))
        }
        setAvailableTags(Array.from(tagSet).sort((a,b)=>a.localeCompare(b)))
      } catch (e) {
        // ignore
      }
    }
    loadTags()
  }, [projectId])

  const onSearch = () => fetchData()
  const onReset = () => { setSearch(''); setHasLink(''); setUniqueByDomain(false); setSort('date_desc'); setDateRange('last30'); setTag(''); setExcludeCompetitors(true); setDomainFilter(''); setBrandMentioned(''); fetchData() }

  const segmentedDomains = useMemo(() => {
    const list = domains || []
    let filtered = [...list]
    if (domainView === 'me') {
      filtered = filtered.filter(d => (d.me_links || 0) > 0)
    }
    if (domainView === 'eco') {
      filtered = filtered.filter(d => (d.me_links === 0) && (d.me_mentions === 0))
    }

    const ecoOf = (d: any) => Math.max(0, (d.analyses || 0) - Math.max((d.me_links || 0), (d.me_mentions || 0)))
    const valueOf = (d: any) => {
      switch (domainSortKey) {
        case 'domain': return (d.domain || '').toString()
        case 'pages': return d.pages || 0
        case 'analyses': return d.analyses || 0
        case 'me_links': return d.me_links || 0
        case 'me_link_rate': return d.me_link_rate || 0
        case 'me_mentions': return d.me_mentions || 0
        case 'eco': return ecoOf(d)
        default: return 0
      }
    }

    const sorted = filtered.sort((a, b) => {
      const va = valueOf(a)
      const vb = valueOf(b)
      if (typeof va === 'string' || typeof vb === 'string') {
        const res = String(va).localeCompare(String(vb))
        return domainSortDir === 'asc' ? res : -res
      }
      if (va === vb) return 0
      return domainSortDir === 'asc' ? (va - vb) : (vb - va)
    })

    return sorted
  }, [domains, domainView, domainSortKey, domainSortDir])

  const handleDomainSort = (key: typeof domainSortKey) => {
    if (domainSortKey === key) {
      setDomainSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setDomainSortKey(key)
      setDomainSortDir('desc')
    }
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Sources</h1>
              {currentProject && (
                <p className="text-sm text-gray-600">Projet • {currentProject.name}</p>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Input placeholder="Rechercher domaine / url / titre" value={search} onChange={(e)=>setSearch(e.target.value)} className="w-72" />
              </div>
              {/* Bouton Réinitialiser plus visible, suppression du bouton Filtrer (refresh auto) */}
              <Button variant="ghost" onClick={onReset}><RefreshCw className="h-4 w-4 mr-2"/>Réinitialiser</Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Tabs */}
        <div className="inline-flex items-center rounded-md bg-gray-100 p-1">
          <button onClick={()=>setTab('list')} className={`px-4 py-2 text-sm font-medium rounded ${tab==='list' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-700 hover:text-gray-900'}`}>
            <span className="inline-flex items-center"><List className="h-4 w-4 mr-2"/>Liste</span>
          </button>
          <button onClick={()=>setTab('domains')} className={`px-4 py-2 text-sm font-medium rounded ${tab==='domains' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-700 hover:text-gray-900'}`}>
            <span className="inline-flex items-center"><Globe2 className="h-4 w-4 mr-2"/>Domaines</span>
          </button>
          <button onClick={()=>setTab('opportunities')} className={`px-4 py-2 text-sm font-medium rounded ${tab==='opportunities' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-700 hover:text-gray-900'}`}>
            <span className="inline-flex items-center"><Grid3X3 className="h-4 w-4 mr-2"/>Opportunités</span>
          </button>
        </div>

        {/* Filtres avancés */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            <div>
              <div className="text-xs text-gray-700 mb-1">Lien vers votre site</div>
              <Select
                value={hasLink || undefined}
                onChange={(v) => setHasLink(prev => (prev === (v || '') ? '' : (v || '')))}
                options={[
                  { value: '', label: 'Tous' },
                  { value: 'true', label: 'Avec lien' },
                  { value: 'false', label: 'Sans lien' },
                ]}
              />
            </div>
            <div>
              <div className="text-xs text-gray-700 mb-1">Tag</div>
              <Select
                value={tag || undefined}
                onChange={(v) => setTag(prev => (prev === (v || '') ? '' : (v || '')))}
                options={[{ value: '', label: 'Tous les tags' }, ...availableTags.map(t => ({ value: t, label: t }))]}
              />
            </div>
            <div>
              <div className="text-xs text-gray-700 mb-1">Filtre domaine</div>
              <div className="flex items-center gap-2">
                <Input placeholder="ex: wikipedia.org" value={domainFilter} onChange={(e)=>setDomainFilter(e.target.value)} className="w-full" />
                {domainFilter && (
                  <button className="text-gray-500 hover:text-gray-800" aria-label="Effacer" onClick={()=>setDomainFilter('')}>
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-700 mb-1">Période</div>
              <Select
                value={dateRange}
                onChange={(v) => setDateRange(v || 'last30')}
                options={[
                  { value: 'last7', label: '7 jours' },
                  { value: 'last30', label: '30 jours' },
                  { value: 'last90', label: '90 jours' },
                ]}
              />
            </div>
            <div>
              <div className="text-xs text-gray-700 mb-1">Tri</div>
              <Select
                value={sort}
                onChange={(v) => setSort(v || 'date_desc')}
                options={[
                  { value: 'date_desc', label: 'Plus récent' },
                  { value: 'date_asc', label: 'Plus ancien' },
                  { value: 'domain', label: 'Par domaine' },
                ]}
              />
            </div>
            <div className="flex items-center">
              <label className="inline-flex items-center space-x-2 cursor-pointer">
                <input type="checkbox" className="form-checkbox" checked={excludeCompetitors} onChange={(e)=>setExcludeCompetitors(e.target.checked)} />
                <span className="text-sm text-gray-700">Exclure concurrents</span>
              </label>
            </div>
            <div className="flex items-center">
              <label className="inline-flex items-center space-x-2 cursor-pointer">
                <input type="checkbox" className="form-checkbox" checked={uniqueByDomain} onChange={(e)=>setUniqueByDomain(e.target.checked)} />
                <span className="text-sm text-gray-700">1 source par domaine</span>
              </label>
            </div>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12"><Loading size="lg" text="Chargement..."/></div>
        )}
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded border border-red-200">{error}</div>
        )}

        {!loading && !error && tab === 'list' && (
          <div className="bg-white rounded-lg border border-gray-200 divide-y">
            {items.map(item => (
              <div key={item.id} className="p-4 flex items-start justify-between">
                <div className="min-w-0">
                  <a href={item.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline break-all inline-flex items-center">
                    <img src={`https://icons.duckduckgo.com/ip3/${item.domain}.ico`} alt="" className="h-4 w-4 mr-2 rounded-sm" onError={(e: any)=>{e.currentTarget.style.display='none'}} />
                    <Link2 className="h-4 w-4 mr-2"/>
                    <span className="truncate max-w-[680px] text-gray-900">{item.title || item.url}</span>
                  </a>
                  <div className="text-xs text-gray-700">
                    <span className="font-medium text-gray-800">{item.domain}</span>
                    <span className="mx-1 text-gray-400">•</span>
                    {item.ai_model_used}
                    <span className="mx-1 text-gray-400">•</span>
                    {new Date(item.created_at).toLocaleString('fr-FR')}
                  </div>
                  {item.snippet && <div className="text-sm text-gray-800 mt-1 line-clamp-2">{item.snippet}</div>}
                </div>
                <div className="text-right ml-4 whitespace-nowrap">
                  <div className="text-xs text-gray-700"><span className="text-gray-500">Prompt:</span> {item.prompt_name || item.prompt_id}</div>
                  <div className="mt-2 flex items-center justify-end gap-2">
                    {item.citation_label && <Badge variant="info">{item.citation_label}</Badge>}
                    <Button size="sm" variant="ghost" onClick={()=>openAnalysisModal(item.analysis_id)}>Ouvrir</Button>
                    <Button size="sm" variant="outline" onClick={()=>navigator.clipboard.writeText(item.url)}>Copier URL</Button>
                  </div>
                </div>
              </div>
            ))}
            {items.length === 0 && <div className="p-6 text-center text-gray-500">Aucune source trouvée</div>}
          </div>
        )}

        {!loading && !error && tab === 'domains' && (
          <div className="space-y-6">
            {/* Segmented control */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 bg-gray-50 p-1 rounded-lg">
                  <button onClick={()=>setDomainView('top')} className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${domainView==='top' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}>Top sources</button>
                  <button onClick={()=>setDomainView('me')} className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${domainView==='me' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}>Me sourcent</button>
                  <button onClick={()=>setDomainView('eco')} className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${domainView==='eco' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}>Écosystème (sans moi)</button>
                </div>
                <div className="text-sm text-gray-600 font-medium">
                  {domains.length} domaines • {segmentedDomains.reduce((s,d)=>s+d.analyses,0)} analyses
                </div>
              </div>
            </div>

            {/* Tableau des domaines */}
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th onClick={()=>handleDomainSort('domain')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">Domaine</th>
                      <th onClick={()=>handleDomainSort('pages')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">Pages</th>
                      <th onClick={()=>handleDomainSort('analyses')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">Analyses</th>
                      <th onClick={()=>handleDomainSort('me_links')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">Analyses avec lien <span title="Analyses citant ce domaine avec lien vers votre site">?</span></th>
                      <th onClick={()=>handleDomainSort('me_link_rate')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">Taux lien</th>
                      <th onClick={()=>handleDomainSort('me_mentions')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">Citations de ma marque</th>
                      <th onClick={()=>handleDomainSort('eco')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">Analyses sans ma marque</th>
                      <th className="px-4 py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {segmentedDomains.map((d) => (
                      <tr key={d.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2">
                          <div className="flex items-center gap-2">
                            <img src={`https://icons.duckduckgo.com/ip3/${d.domain}.ico`} className="h-4 w-4" onError={(e: any)=>{e.currentTarget.style.display='none'}} />
                            <div className="font-medium text-gray-900">{d.domain}</div>
                          </div>
                        </td>
                        <td className="px-4 py-2 text-gray-700">{d.pages}</td>
                        <td className="px-4 py-2 text-gray-700">
                          <button
                            className="underline decoration-dotted hover:decoration-solid hover:text-gray-900"
                            title="Voir les sources de ce domaine"
                            onClick={() => { setTab('list'); setDomainFilter(d.domain); setHasLink(''); }}
                          >
                            {d.analyses}
                          </button>
                        </td>
                        <td className="px-4 py-2 text-blue-600 font-semibold">
                          <button
                            className="underline decoration-dotted hover:decoration-solid hover:text-blue-800"
                            title="Voir les analyses avec lien vers votre site"
                            onClick={() => { setTab('list'); setDomainFilter(d.domain); setHasLink('true'); }}
                          >
                            {d.me_links}
                          </button>
                        </td>
                        <td className="px-4 py-2 text-emerald-600 font-semibold">{Math.round((d.me_link_rate||0)*100)}%</td>
                        <td className="px-4 py-2 text-purple-600 font-semibold">
                          <button
                            className="underline decoration-dotted hover:decoration-solid hover:text-purple-800"
                            title="Voir les analyses qui citent votre marque"
                            onClick={() => { setTab('list'); setDomainFilter(d.domain); /* pas de filtre direct 'brand', on reste sur le domaine */ }}
                          >
                            {d.me_mentions}
                          </button>
                        </td>
                        <td className="px-4 py-2 text-amber-600 font-semibold">
                          <button
                            className="underline decoration-dotted hover:decoration-solid hover:text-amber-800"
                            title="Voir les analyses sans mention de ma marque"
                            onClick={() => {
                              setTab('list');
                              setDomainFilter(d.domain);
                              // Filtre: sans marque
                              setBrandMentioned('false')
                              // Ne pas contraindre par hasLink : on laisse vide
                              setHasLink('')
                            }}
                          >
                            {Math.max(0, (d.analyses||0) - Math.max((d.me_links||0),(d.me_mentions||0)))}
                          </button>
                        </td>
                        <td className="px-4 py-2 text-right whitespace-nowrap">
                          <Button size="sm" variant="ghost" className="text-xs px-2 py-1">Voir URLs</Button>
                          <Button size="sm" variant="outline" className="text-xs px-2 py-1 ml-1" onClick={()=>window.open(`https://${d.domain}`, '_blank')}>Ouvrir</Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {segmentedDomains.length === 0 && (
                  <div className="p-6 text-center text-gray-500">Aucun domaine trouvé</div>
                )}
              </div>
            </div>
          </div>
        )}

        {!loading && !error && tab === 'opportunities' && (
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
              {opportunities.map(d => (
                <Card key={d.id}>
                  <div className="p-4">
                    <div className="font-semibold text-gray-900">{d.domain}</div>
                    <div className="text-sm text-gray-600">{d.pages} pages • {d.analyses} analyses (sans lien vers le site)</div>
                    <div className="text-xs text-gray-500 mt-1">{d.first_seen ? new Date(d.first_seen).toLocaleDateString('fr-FR') : ''} → {d.last_seen ? new Date(d.last_seen).toLocaleDateString('fr-FR') : ''}</div>
                  </div>
                </Card>
              ))}
            </div>
            {opportunities.length === 0 && <div className="p-6 text-center text-gray-500">Aucune opportunité détectée</div>}
          </div>
        )}

      </div>
      {/* Modale d'analyse */}
      <Modal isOpen={!!openAnalysisId} onClose={()=>{ setOpenAnalysisId(''); setOpenAnalysis(null) }} size="xl" title={openAnalysis ? `Analyse • ${openAnalysis.ai_model_used}` : 'Analyse'}>
        {!openAnalysis ? (
          <div className="text-gray-600">Chargement...</div>
        ) : (
          <div className="space-y-4">
            <div>
              <div className="text-xs text-gray-500 mb-1">Prompt exécuté</div>
              <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border border-gray-200">{openAnalysis.prompt_executed}</pre>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Réponse IA</div>
              <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border border-gray-200 max-h-[50vh] overflow-auto">{openAnalysis.ai_response}</pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}



