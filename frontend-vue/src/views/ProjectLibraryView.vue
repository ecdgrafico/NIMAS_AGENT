<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjects } from '../composables/useProjects'
import ProjectList from '../components/ProjectList.vue'
import ProjectCreateForm from '../components/ProjectCreateForm.vue'
import { api } from '../services/api'
const router=useRouter();const {projects,loading,error,load,create}=useProjects();onMounted(load)
async function created(){await load()}
async function open(item){await api.openProject(item.path);router.push('/workspace')}
</script>
<template><section class="hero"><span class="eyebrow">ESPACIO DE TRABAJO</span><h2>Biblioteca de proyectos NIMAS</h2><p>Conserva cada proyecto separado y trabaja sobre propuestas no destructivas.</p></section><p v-if="loading" class="notice">Cargando proyectos…</p><p v-if="error" class="notice error">{{error}}</p><ProjectList :projects="projects" @open="open"/><ProjectCreateForm @created="created"/></template>
