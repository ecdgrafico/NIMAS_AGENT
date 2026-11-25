<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
const project = ref(null)
const route = useRoute()
const showProjectName = computed(() => route.path !== '/projects')
async function refreshProject() { try { project.value = await api.projectStatus() } catch (_) { project.value = null } }
onMounted(refreshProject)
watch(() => route.path, refreshProject)
</script>
<template>
  <div class="app-shell"><header class="topbar"><div><span class="eyebrow">NIMAS · REMEDIACIÓN EDITORIAL</span><h1>NIMAS Agent <small v-if="showProjectName && project?.name">· {{ project.name }}</small></h1></div><nav><RouterLink to="/projects">Proyectos</RouterLink><RouterLink to="/lessons">Lecciones</RouterLink><RouterLink to="/editorial">FM / EM</RouterLink><RouterLink to="/assets">Imágenes</RouterLink><RouterLink to="/metadata">Metadata</RouterLink><RouterLink to="/structure">Estructura</RouterLink><RouterLink to="/package">ZIP</RouterLink></nav></header><main><slot /></main></div>
</template>
