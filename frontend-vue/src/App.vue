<script setup>
import { onMounted, ref } from 'vue'

const project = ref(null)
const loading = ref(true)
const error = ref('')

async function loadProject() {
  loading.value = true
  try {
    const response = await fetch('/api/project-status', { cache: 'no-store' })
    if (!response.ok) throw new Error('No se pudo consultar el proyecto')
    project.value = await response.json()
  } catch (reason) {
    error.value = reason.message
  } finally {
    loading.value = false
  }
}

onMounted(loadProject)
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div><span class="eyebrow">NIMAS · REMEDIACIÓN EDITORIAL</span><h1>NIMAS Agent</h1></div>
      <nav><a href="#lessons">Lecciones</a><a href="#metadata">Metadata</a><a href="#structure">Estructura</a></nav>
    </header>
    <main>
      <section class="hero"><span class="eyebrow">FLUJO DE TRABAJO</span><h2>Convierte, revisa y ensambla tu proyecto NIMAS.</h2><p>El frontend Vue se está migrando por etapas sobre las APIs existentes del servidor Python.</p></section>
      <p v-if="loading" class="notice">Consultando proyecto…</p>
      <p v-else-if="error" class="notice error">{{ error }}</p>
      <section v-else class="status-card"><span class="eyebrow">PROYECTO ACTUAL</span><strong>{{ project?.name || 'Sin proyecto cargado' }}</strong><span>{{ project?.mode || 'Listo para comenzar' }}</span></section>
      <section id="lessons" class="work-card"><span class="step">01</span><div><h3>Generar y auditar lecciones</h3><p>Crear propuestas DTBook y revisarlas página por página.</p><button type="button">Abrir lecciones</button></div></section>
      <section id="metadata" class="work-card"><span class="step">02</span><div><h3>Completar metadata NIMAC</h3><p>Registrar los datos editoriales después de aprobar el contenido.</p><button type="button" class="secondary">Abrir metadata</button></div></section>
      <section id="structure" class="work-card"><span class="step">03</span><div><h3>Definir estructura y ensamblar</h3><p>Ordenar Frontmatter, Bodymatter y Rearmatter para crear el paquete final.</p><button type="button" class="secondary">Abrir estructura</button></div></section>
    </main>
  </div>
</template>
