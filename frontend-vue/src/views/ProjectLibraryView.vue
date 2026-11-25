<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProjects } from '../composables/useProjects'
import ProjectList from '../components/ProjectList.vue'
import ProjectCreateForm from '../components/ProjectCreateForm.vue'
import { api } from '../services/api'
const router=useRouter();const {projects,loading,error,load,create}=useProjects();const closing=ref(true);onMounted(async()=>{try{await api.closeProject()}finally{closing.value=false;await load()}})
async function created(){await load()}
async function open(item){await api.openProject(item.path);router.push('/workspace')}
async function rename(item){const name=window.prompt('Nuevo nombre del proyecto:',item.name);if(!name||name.trim()===item.name)return;try{await api.renameProject({path:item.path,name:name.trim()});await load()}catch(e){window.alert(e.message)}}
async function remove(item){if(!window.confirm(`¿Eliminar completamente “${item.name}” y todos sus archivos? Esta acción no se puede deshacer.`))return;try{await api.deleteProject(item.path);await load()}catch(e){window.alert(e.message)}}
</script>
<template><section class="hero"><span class="eyebrow">ESPACIO DE TRABAJO</span><h2>Biblioteca de proyectos NIMAS</h2><p>La biblioteca es independiente del proyecto activo. Abre uno para entrar a su espacio de trabajo.</p></section><p v-if="closing" class="notice">Cerrando el proyecto anterior…</p><p v-else-if="loading" class="notice">Cargando proyectos…</p><p v-if="error" class="notice error">{{error}}</p><ProjectList v-if="!closing" :projects="projects" :disabled="closing" @open="open" @rename="rename" @remove="remove"/><ProjectCreateForm v-if="!closing" @created="created"/></template>
