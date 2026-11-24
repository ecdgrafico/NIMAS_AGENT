<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../services/api'
import { config } from '../config'
const data=ref({assets:[]}),units=ref([]),status=ref('')
onMounted(async()=>{data.value=await api.assets();units.value=(await api.projectDetail()).structure?.units||[]})
async function analyze(){status.value='Análisis iniciado…';await api.analyzeAssets();status.value='Análisis iniciado. Actualiza la galería cuando termine.'}
async function decide(asset,state){status.value=(await api.assignImage({file:asset.file,unit_id:asset.unit_id||'',status:state})).message||'Decisión guardada.'}
</script>
<template><section class="hero"><span class="eyebrow">RECURSOS VISUALES</span><h2>Galería y asociación de imágenes</h2><p>Revisa las candidatas extraídas del PDF y decide si se usan o se descartan.</p><button @click="analyze">Analizar imágenes del proyecto</button></section><p class="notice">{{data.count||0}} imágenes detectadas. {{status}}</p><div class="asset-gallery-vue"><figure v-for="asset in data.assets" :key="asset.file"><img :src="config.static('/working/detected-images/'+encodeURIComponent(asset.file))" :alt="asset.file"/><figcaption><strong>{{asset.file}}</strong><small>Página {{asset.page||'—'}}</small><select v-model="asset.unit_id"><option value="">Sin asociar</option><option v-for="unit in units" :value="unit.id">{{unit.name}}</option></select><button @click="decide(asset,'reviewed')">Asociar</button><button class="secondary" @click="decide(asset,'discarded')">Descartar</button></figcaption></figure></div></template>
