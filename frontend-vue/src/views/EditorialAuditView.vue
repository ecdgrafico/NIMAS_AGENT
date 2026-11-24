<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../services/api'
import { config } from '../config'
const sections=ref([]),selected=ref(null),page=ref(null),status=ref(''),busy=ref(false),images=ref([])
async function load(){sections.value=(await api.editorialSections()).sections||[];if(sections.value[0])await open(sections.value[0].key)}
async function open(key){selected.value=await api.editorialDetail(key);page.value=selected.value.pageIds?.[0];await refreshPage()}
async function refreshPage(){if(!selected.value||page.value==null)return;await api.renderEditorial(selected.value.key);images.value=(await api.editorialImages(selected.value.key,page.value)).images||[]}
async function generate(){busy.value=true;try{status.value=(await api.generateEditorial(selected.value.key)).message||'Reconstrucción iniciada.'}catch(error){status.value=error.message}finally{busy.value=false}}
async function accept(){try{status.value=(await api.acceptEditorial(selected.value.key)).message||'Sección aprobada.';await open(selected.value.key)}catch(error){status.value=error.message}}
onMounted(load)
</script>
<template>
<section class="hero"><span class="eyebrow">FRONTMATTER Y REARMATTER</span><h2>Auditoría editorial</h2><p>Genera, revisa y aprueba FM y EM antes del ensamblaje final.</p></section>
<div class="editorial-layout"><aside class="section-list"><button v-for="item in sections" :key="item.key" :class="{active:selected?.key===item.key}" @click="open(item.key)">{{item.key}} · {{item.name}}<small>{{item.status}}</small></button></aside>
<section v-if="selected" class="editorial-audit-vue"><div class="audit-toolbar"><strong>{{selected.name}}</strong><select v-model="page" @change="refreshPage"><option v-for="item in selected.pageIds" :key="item" :value="item">Página {{item}}</option></select><button class="secondary" :disabled="busy" @click="generate">Generar propuesta</button><button :disabled="!selected.proposal" @click="accept">Aprobar propuesta</button></div>
<div class="audit-grid"><article class="audit-panel"><header><strong>PDF</strong></header><img :src="config.static('/auditoria-lecciones/assets/'+selected.key+'/page-'+String(selected.pageIds.indexOf(page)+1).padStart(2,'0')+'.png')" alt="Página editorial"/></article><article class="audit-panel"><header><strong>XML fuente</strong></header><pre>{{selected.source}}</pre></article><article class="audit-panel"><header><strong>Propuesta</strong></header><pre>{{selected.proposal||'Pendiente de reconstrucción.'}}</pre></article></div>
<section class="library-card"><h3>Imágenes de la página <span class="count">{{images.length}}</span></h3><div class="image-row"><figure v-for="item in images" :key="item.id||item.src"><img :src="item.url" :alt="item.id||item.src"/><figcaption>{{item.id||item.src}}</figcaption></figure><p v-if="!images.length" class="empty-state">No hay imágenes referenciadas.</p></div></section></section></div><p class="notice">{{status}}</p>
</template>
