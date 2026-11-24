const runtime = window.NIMAS_CONFIG || {}
const apiBase = import.meta.env.VITE_API_BASE || runtime.apiBase || window.location.origin
const paths = runtime.paths || { api: '/api', working: '/working', legacy: '/auditoria-lecciones' }
export const config = { apiBase: apiBase.replace(/\/$/, ''), paths, api(path) { return `${this.apiBase}${paths.api}${path}` }, static(path) { return `${this.apiBase}${path.startsWith('/') ? path : `/${path}`}` } }
