<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import { config } from '../config'

const route = useRoute()
const detail = ref(null)
const page = ref(1)
const image = ref('')
const status = ref('')
const note = ref('')
const cropStage = ref(null), drawing = ref(false), cropStart = ref(null), cropRect = ref(null), cropMode = ref(false)
const unit = computed(() => detail.value?.unit)
const isPdfProject = computed(() => detail.value?.mode === 'pdf_only')
const first = computed(() => Number(detail.value?.pages?.[0] || 1))
const last = computed(() => Number(detail.value?.pages?.[1] || 1))
const decision = computed(() => detail.value?.decisions?.[String(page.value)]?.status || 'pending')
const pageAssets = computed(() => detail.value?.assets?.filter(item => Number(item.display_page ?? item.page) === page.value) || [])

async function load() {
  detail.value = await api.unitDetail(route.params.unit, page.value)
  page.value = first.value
  await render()
}
async function render() {
  try {
    if (isPdfProject.value) detail.value = await api.unitDetail(route.params.unit, page.value)
    image.value = (await api.unitRender(route.params.unit, page.value)).url
    status.value = 'Página lista para auditoría.'
  } catch (error) { status.value = error.message }
}
async function decide(state) {
  try {
    status.value = (await api.pageDecision({ unit_id: route.params.unit, page: page.value, status: state, note: note.value })).message
    detail.value.decisions = { ...detail.value.decisions, [String(page.value)]: { status: state, note: note.value } }
  } catch (error) { status.value = error.message }
}
async function approve() {
  try { status.value = (await api.approveUnit(route.params.unit)).message; await load() }
  catch (error) { status.value = error.message }
}
async function adjust() {
  if (!note.value.trim()) { status.value = 'Escribe una solicitud antes de guardarla.'; return }
  try {
    status.value = (await api.requestAdjustment({ unit_id: route.params.unit, page: page.value, note: note.value })).message
    note.value = ''
    await load()
  } catch (error) { status.value = error.message }
}
function point(event) { const box = cropStage.value.getBoundingClientRect(); return { x: Math.max(0, Math.min(1, (event.clientX-box.left)/box.width)), y: Math.max(0, Math.min(1, (event.clientY-box.top)/box.height)) } }
function beginCrop(event) { if (!cropMode.value) return; drawing.value=true; cropStart.value=point(event); cropRect.value={...cropStart.value,x1:cropStart.value.x,y1:cropStart.value.y}; cropStage.value.setPointerCapture(event.pointerId) }
function moveCrop(event) { if (!drawing.value) return; const p=point(event); cropRect.value={x0:Math.min(cropStart.value.x,p.x),y0:Math.min(cropStart.value.y,p.y),x1:Math.max(cropStart.value.x,p.x),y1:Math.max(cropStart.value.y,p.y)} }
function endCrop() { drawing.value=false }
async function saveCrop() { if (!cropRect.value) return; try { status.value=(await api.manualImageCrop({unit_id:route.params.unit,page:page.value,...cropRect.value})).message; cropMode.value=false; cropRect.value=null; await load() } catch(error) { status.value=error.message } }
onMounted(load)
</script>

<template>
  <section class="hero"><span class="eyebrow">AUDITORÍA DE UNIDAD</span><h2>{{ unit?.name || route.params.unit }}</h2><p>Compara el PDF con el XML fuente, la propuesta DTBook y sus imágenes. La propuesta solo se instala después de aprobar todas las páginas.</p></section>
  <section class="audit-toolbar"><button class="secondary" :disabled="page <= first" @click="page--; render()">← Anterior</button><strong>Página {{ page }} de {{ last }}</strong><button class="secondary" :disabled="page >= last" @click="page++; render()">Siguiente →</button><span class="decision-badge" :class="decision">{{ decision }}</span><button class="secondary" @click="decide('correction')">Marcar corrección</button><button @click="decide('approved')">Aprobar página</button><button @click="approve">Aprobar unidad</button><span class="toolbar-status">{{ status }}</span></section>
  <section class="audit-grid" :class="{ 'pdf-audit-grid': isPdfProject }"><article class="audit-panel"><header><strong>PDF</strong><span>Página {{ page }}</span></header><div class="crop-tools" v-if="isPdfProject"><button class="secondary" @click="cropMode=!cropMode">{{ cropMode ? 'Cancelar rectángulo' : 'Señalar imagen faltante' }}</button><button v-if="cropRect" @click="saveCrop">Extraer recorte</button><small v-if="cropMode">Arrastra sobre la imagen para marcar el recurso.</small></div><div ref="cropStage" class="crop-stage" :class="{cropping:cropMode}" @pointerdown="beginCrop" @pointermove="moveCrop" @pointerup="endCrop"><img :src="image" alt="Página del PDF" /><span v-if="cropRect" class="crop-rect" :style="{left:(cropRect.x0*100)+'%',top:(cropRect.y0*100)+'%',width:((cropRect.x1-cropRect.x0)*100)+'%',height:((cropRect.y1-cropRect.y0)*100)+'%'}"></span></div></article><article v-if="!isPdfProject" class="audit-panel"><header><strong>XML fuente</strong><span>{{ detail?.source ? 'Solo lectura' : 'No disponible' }}</span></header><pre>{{ detail?.source || 'Este proyecto no contiene un XML fuente asociado a la unidad.' }}</pre></article><article class="audit-panel"><header><strong>{{ isPdfProject ? 'XML DTBook sugerido para esta página' : 'DTBook propuesto' }}</strong><span>{{ detail?.provider ? `Generado con ${detail.provider}` : (detail?.hasProposal ? 'Propuesta' : 'Pendiente') }}</span></header><pre>{{ isPdfProject ? (detail?.proposal_page || 'No hay propuesta para esta página.') : (detail?.proposal || 'Aún no hay propuesta.') }}</pre></article></section>
<section class="library-card"><h3>Imágenes de esta página <span class="count">{{ pageAssets.length }}</span></h3><div class="image-row"><figure v-for="asset in pageAssets" :key="asset.file"><img :src="config.static(asset.url)" :alt="asset.file" /><figcaption>{{ asset.file }}</figcaption></figure><p v-if="!pageAssets.length" class="empty-state">No hay imágenes detectadas para esta página.</p></div></section>
  <section class="correction-card"><h3>Solicitar corrección a la IA</h3><textarea v-model="note" placeholder="Describe el ajuste de esta página…"></textarea><button @click="adjust">Guardar solicitud</button></section>
</template>
