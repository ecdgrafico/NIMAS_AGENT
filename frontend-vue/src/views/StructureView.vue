<script setup>
import { onMounted, ref } from 'vue'; import { api } from '../services/api'; const detail = ref({ structure: { units: [] } }), status = ref(''), dragged = ref(null); const sections = [['frontmatter', 'Frontmatter'], ['bodymatter', 'Bodymatter'], ['rearmatter', 'Rearmatter']]; onMounted(async () => { detail.value = await api.projectDetail() }); function move(unit, section) { unit.section = section } function dragStart(unit) { dragged.value = unit } function drop(section, target=null) { if (!dragged.value) return; const unit = dragged.value; const units = detail.value.structure.units; unit.section = section; const from = units.indexOf(unit); if (from >= 0) units.splice(from, 1); const same = units.filter(item => item.section === section); const index = target ? units.indexOf(target) : -1; if (index >= 0) units.splice(index, 0, unit); else { const last = units.reduceRight((found, item, position) => found >= 0 ? found : item.section === section ? position : -1, -1); units.splice(last >= 0 ? last + 1 : units.length, 0, unit) } dragged.value = null } async function save() { await api.saveSetup({ metadata: detail.value.metadata, structure: detail.value.structure }); status.value = 'Estructura guardada.' } async function preflight() { status.value = JSON.stringify(await api.preflight()) } async function exportPackage() { status.value = (await api.exportPackage()).message || 'Exportación iniciada.' }
</script>
<template>
    <section class="hero"><span class="eyebrow">PASO 3 · ESTRUCTURA</span>
        <h2>Ensamblar el paquete</h2>
        <p>Esta etapa solo define cómo se unirán las unidades aprobadas.</p>
    </section>
    <div class="structure-lanes-vue">
        <section v-for="[key, title] in sections" :key="key" class="structure-lane">
            <header><strong>{{ title }}</strong><small>{{detail.structure.units.filter(u => u.section === key).length}}
                    unidades</small></header>
            <div class="structure-dropzone" @dragover.prevent @drop="drop(key)">
                <article v-for="unit in detail.structure.units.filter(u => u.section === key)" :key="unit.id"
                    class="structure-block" draggable="true" @dragstart="dragStart(unit)" @dragover.prevent @drop.stop="drop(key, unit)"><span class="drag-handle" title="Arrastrar para ordenar">⋮⋮</span><span
                        class="unit-file-label">{{ unit.file || unit.name }}</span><select :value="unit.section"
                        @change="move(unit, $event.target.value)">
                        <option v-for="[section, label] in sections" :value="section">{{ label }}</option>
                    </select></article>
            </div>
        </section>
    </div><div class="button-row"><button @click="save">Guardar estructura</button><button class="secondary" @click="preflight">Ejecutar preflight</button><button @click="exportPackage">Crear ZIP validado</button></div><span class="hint">{{ status }}</span>
</template>
