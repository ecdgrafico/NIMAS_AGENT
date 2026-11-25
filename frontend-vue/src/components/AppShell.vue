<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../services/api'
const project = ref(null)
onMounted(async () => { try { project.value = await api.projectStatus() } catch (_) {} })
</script>
<template>
  <div class="app-shell"><header class="topbar"><div><span class="eyebrow">NIMAS · REMEDIACIÓN EDITORIAL</span><h1>NIMAS Agent <small v-if="project?.name">· {{ project.name }}</small></h1></div><nav><RouterLink to="/projects">Proyectos</RouterLink><RouterLink to="/lessons">Lecciones</RouterLink><RouterLink to="/editorial">FM / EM</RouterLink><RouterLink to="/assets">Imágenes</RouterLink><RouterLink to="/metadata">Metadata</RouterLink><RouterLink to="/structure">Estructura</RouterLink><RouterLink to="/package">ZIP</RouterLink></nav></header><main><slot /></main></div>
</template>
