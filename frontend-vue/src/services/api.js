import { config } from '../config'

const request = async (path, options = {}) => {
  const response = await fetch(config.api(path), { cache: 'no-store', ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || data.message || `Error ${response.status}`)
  return data
}

export const api = {
  projectStatus: () => request('/project-status'),
  projects: () => request('/projects'),
  projectDetail: () => request('/project-detail'),
  projectUnits: () => request('/project-units'),
  unitDetail: unit => request(`/unit-detail?unit=${encodeURIComponent(unit)}`),
  unitRender: (unit,page) => request(`/unit-render?unit=${encodeURIComponent(unit)}&page=${encodeURIComponent(page)}`),
  openProject: path => request('/open-project', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ path }) }),
  nimacTemplate: () => request('/nimac-template'),
  saveSetup: body => request('/save-project-setup', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) }),
  providerStatus: () => request('/provider-status'),
  generate: body => request('/generate-ai-proposal', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) }),
  validate: unit => request(`/proposal-validation?unit=${encodeURIComponent(unit)}`),
  approve: unit => request('/approve-ai-proposal', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ unit_id: unit }) }),
  approveLesson: lesson => request(`/approve-lesson?lesson=${encodeURIComponent(lesson)}`, { method: 'POST' }),
  pageDecision: body => request('/unit-page-decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
  approveUnit: unit => request('/approve-unit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:unit})}),
  preflight: () => request('/project-preflight')
  ,lessons: () => request('/lessons')
  ,job: () => request('/job')
  ,assets: () => request('/project-assets')
  ,pageImages: (lesson,page) => request(`/page-images?lesson=${encodeURIComponent(lesson)}&page=${encodeURIComponent(page)}`)
  ,renderLesson: lesson => request(`/render?lesson=${encodeURIComponent(lesson)}`)
  ,report: lesson => `${config.api('/report')}?lesson=${encodeURIComponent(lesson)}`
  ,editorialSections: () => request('/editorial-sections')
  ,editorialDetail: key => request(`/editorial-detail?section=${encodeURIComponent(key)}`)
  ,editorialImages: (key,page) => request(`/editorial-images?section=${encodeURIComponent(key)}&page=${encodeURIComponent(page)}`)
  ,renderEditorial: key => request(`/editorial-render?section=${encodeURIComponent(key)}`)
  ,generateEditorial: key => request(`/generate-editorial?section=${encodeURIComponent(key)}`,{method:'POST'})
  ,acceptEditorial: key => request(`/accept-editorial-proposal?section=${encodeURIComponent(key)}`,{method:'POST'})
  ,exportPackage: () => request('/export-package',{method:'POST'})
  ,assignImage: body => request('/assign-image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  ,analyzeAssets: () => request('/analyze-project-assets',{method:'POST'})
  ,requestAdjustment: body => request('/request-adjustment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
}

export async function uploadProject({ name, pdfs, zip }) {
  const form = new FormData(); form.append('name', name)
  for (const file of pdfs || []) form.append('pdfs', file, file.name)
  if (zip) form.append('zip', zip)
  return request(zip ? '/create-zip-project-upload' : '/create-project-upload', { method: 'POST', body: form })
}
