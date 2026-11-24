<script setup>
import { onMounted, ref } from 'vue'

const project = ref(null)
const projects = ref([])
const loading = ref(true)
const error = ref('')
const message = ref('')
const mode = ref('pdf')
const name = ref('')
const pdfs = ref([])
const zip = ref(null)

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

async function loadProjects() {
  const response = await fetch('/api/projects', { cache: 'no-store' })
  if (response.ok) projects.value = (await response.json()).projects || []
}

async function createProject() {
  message.value = 'Creando proyecto…'
  const data = new FormData()
  data.append('name', name.value.trim())
  if (mode.value === 'zip') data.append('zip', zip.value)
  for (const file of pdfs.value) data.append('pdfs', file, file.name)
  const endpoint = mode.value === 'zip' ? '/api/create-zip-project-upload' : '/api/create-project-upload'
  try {
    const response = await fetch(endpoint, { method: 'POST', body: data })
    const result = await response.json()
    if (!response.ok) throw new Error(result.error || 'No se pudo crear el proyecto')
    message.value = result.message || 'Proyecto creado.'
    name.value = ''; pdfs.value = []; zip.value = null
    await loadProjects()
  } catch (reason) { message.value = reason.message }
}

async function openProject(item) {
  const response = await fetch('/api/open-project', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({path: item.path}) })
  if (!response.ok) { message.value = (await response.json()).error || 'No se pudo abrir el proyecto'; return }
  project.value = item
  message.value = `Proyecto abierto: ${item.name}`
}

onMounted(async () => { await Promise.all([loadProject(), loadProjects()]); loading.value = false })
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div><span class="eyebrow">NIMAS · REMEDIACIÓN EDITORIAL</span><h1>NIMAS Agent</h1></div>
      <nav><a href="#lessons">Lecciones</a><a href="#metadata">Metadata</a><a href="#structure">Estructura</a></nav>
    </header>
    <main>
      <section class="hero"><span class="eyebrow">FLUJO DE TRABAJO</span><h2>Convierte, revisa y ensambla tu proyecto NIMAS.</h2><p>El frontend Vue se está migrando por etapas sobre las APIs existentes del servidor Python.</p></section>
      <p v-if="loading" class="notice">Consultando biblioteca…</p>
      <p v-else-if="error" class="notice error">{{ error }}</p>
      <section v-else class="status-card"><span class="eyebrow">PROYECTO ACTUAL</span><strong>{{ project?.name || 'Sin proyecto cargado' }}</strong><span>{{ project?.mode || 'Selecciona o crea un proyecto para comenzar' }}</span></section>
      <section class="library-card"><div class="card-title-row"><div><span class="eyebrow">BIBLIOTECA</span><h2>Proyectos</h2></div><span class="count">{{ projects.length }}</span></div><div v-if="!projects.length" class="empty-state">Todavía no hay proyectos en la biblioteca.</div><article v-for="item in projects" :key="item.path" class="project-row"><div><strong>{{ item.name }}</strong><span>{{ item.mode }} · {{ item.status }}</span><small>{{ item.path }}</small></div><button type="button" @click="openProject(item)">Abrir proyecto</button></article></section>
      <section class="library-card"><div class="card-title-row"><div><span class="eyebrow">NUEVO PROYECTO</span><h2>Crear espacio de trabajo</h2></div><div class="mode-switch"><button :class="{active: mode === 'pdf'}" type="button" @click="mode='pdf'">Desde PDF</button><button :class="{active: mode === 'zip'}" type="button" @click="mode='zip'">Desde ZIP NIMAS</button></div></div><form class="create-form" @submit.prevent="createProject"><label>Nombre del proyecto<input v-model="name" required placeholder="Ej. Ciencias 2026" /></label><label v-if="mode === 'zip'">ZIP original NIMAS<input type="file" accept=".zip" required @change="zip=$event.target.files[0]" /></label><label>PDF de referencia<input type="file" accept="application/pdf,.pdf" multiple required @change="pdfs=[...$event.target.files]" /></label><button type="submit">Crear proyecto</button></form><p v-if="message" class="notice">{{ message }}</p></section>
      <section id="lessons" class="work-card"><span class="step">01</span><div><h3>Generar y auditar lecciones</h3><p>Crear propuestas DTBook y revisarlas página por página.</p></div></section>
      <section id="metadata" class="work-card"><span class="step">02</span><div><h3>Completar metadata NIMAC</h3><p>Registrar los datos editoriales después de aprobar el contenido.</p></div></section>
      <section id="structure" class="work-card"><span class="step">03</span><div><h3>Definir estructura y ensamblar</h3><p>Ordenar Frontmatter, Bodymatter y Rearmatter para crear el paquete final.</p></div></section>
    </main>
  </div>
</template>
