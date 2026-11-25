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
async function rename(item){const name=window.prompt('Nuevo nombre del proyecto:',item.name);if(!name||name.trim()===item.name)return;try{await api.renameProject({path:item.path,name:name.trim()});await load()}catch(e){window.alert(e.message)}}
async function remove(item){if(!window.confirm(`¿Eliminar completamente “${item.name}” y todos sus archivos? Esta acción no se puede deshacer.`))return;try{await api.deleteProject(item.path);await load()}catch(e){window.alert(e.message)}}
</script>
<template><section class="hero"><span class="eyebrow">ESPACIO DE TRABAJO</span><h2>Biblioteca de proyectos NIMAS</h2><p>Conserva cada proyecto separado y trabaja sobre propuestas no destructivas.</p></section><p v-if="loading" class="notice">Cargando proyectos…</p><p v-if="error" class="notice error">{{error}}</p><ProjectList :projects="projects" @open="open" @rename="rename" @remove="remove"/><ProjectCreateForm @created="created"/></template>
