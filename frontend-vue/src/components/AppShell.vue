<script setup>
import { RouterLink } from 'vue-router'
</script>
<template>
  <div class="app-shell"><header class="topbar"><div><span class="eyebrow">NIMAS · REMEDIACIÓN EDITORIAL</span><h1>NIMAS Agent</h1></div><nav><RouterLink to="/projects">Proyectos</RouterLink><RouterLink to="/lessons">Lecciones</RouterLink><RouterLink to="/editorial">FM / EM</RouterLink><RouterLink to="/metadata">Metadata</RouterLink><RouterLink to="/structure">Estructura</RouterLink></nav></header><main><slot /></main></div>
</template>
