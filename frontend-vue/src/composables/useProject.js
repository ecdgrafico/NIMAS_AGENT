import { ref } from 'vue'
import { api } from '../services/api'

export function useProject() {
  const detail = ref(null), status = ref(null), loading = ref(false), error = ref('')
  async function load() { loading.value = true; try { [status.value, detail.value] = await Promise.all([api.projectStatus(), api.projectDetail()]) } catch (e) { error.value = e.message } finally { loading.value = false } }
  return { detail, status, loading, error, load }
}
