<script setup>
defineProps({ projects: { type: Array, default: () => [] } })
defineEmits(['open','rename','remove'])
</script>
<template><section class="library-card"><div class="card-title-row"><div><span class="eyebrow">BIBLIOTECA</span><h2>Proyectos</h2></div><span class="count">{{ projects.length }}</span></div><div v-if="!projects.length" class="empty-state">Todavía no hay proyectos en la biblioteca.</div><article v-for="item in projects" :key="item.path" class="project-row"><div><strong>{{ item.name }}</strong><span>{{ item.mode }} · {{ item.status }}</span><small>{{ item.path }}</small></div><div class="project-actions"><button type="button" @click="$emit('open', item)">Abrir</button><button type="button" class="secondary" @click="$emit('rename', item)">Renombrar</button><button type="button" class="danger" @click="$emit('remove', item)">Eliminar</button></div></article></section></template>
