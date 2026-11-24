import { ref } from 'vue'
import { api, uploadProject } from '../services/api'

export function useProjects() {
  const projects = ref([]), loading = ref(false), error = ref('')
  async function load() { loading.value = true; error.value = ''; try { projects.value = (await api.projects()).projects || [] } catch (e) { error.value = e.message } finally { loading.value = false } }
  async function create(payload) { await uploadProject(payload); await load() }
  return { projects, loading, error, load, create }
}
