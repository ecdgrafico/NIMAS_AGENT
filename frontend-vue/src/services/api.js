const request = async (path, options = {}) => {
  const response = await fetch(path, { cache: 'no-store', ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || data.message || `Error ${response.status}`)
  return data
}

export const api = {
  projectStatus: () => request('/api/project-status'),
  projects: () => request('/api/projects'),
  projectDetail: () => request('/api/project-detail'),
  openProject: path => request('/api/open-project', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ path }) }),
  nimacTemplate: () => request('/api/nimac-template'),
  saveSetup: body => request('/api/save-project-setup', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) }),
  providerStatus: () => request('/api/provider-status'),
  generate: body => request('/api/generate-ai-proposal', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) }),
  validate: unit => request(`/api/proposal-validation?unit=${encodeURIComponent(unit)}`),
  approve: unit => request('/api/approve-ai-proposal', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ unit_id: unit }) }),
  preflight: () => request('/api/project-preflight')
}

export async function uploadProject({ name, pdfs, zip }) {
  const form = new FormData()
  form.append('name', name)
  for (const file of pdfs || []) form.append('pdfs', file, file.name)
  if (zip) form.append('zip', zip)
  const path = zip ? '/api/create-zip-project-upload' : '/api/create-project-upload'
  return request(path, { method: 'POST', body: form })
}
