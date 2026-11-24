<script setup>
import { ref } from 'vue'
const emit = defineEmits(['created'])
const mode = ref('pdf'), name = ref(''), pdfs = ref([]), zip = ref(null), message = ref(''), busy = ref(false)
async function submit() { busy.value = true; message.value = ''; try { await emit('created', { name: name.value.trim(), pdfs: pdfs.value, zip: mode.value === 'zip' ? zip.value : null }); name.value = ''; pdfs.value = []; zip.value = null; message.value = 'Proyecto creado.' } catch (e) { message.value = e.message } finally { busy.value = false } }
</script>
<template>
    <section class="library-card">
        <div class="card-title-row">
            <div><span class="eyebrow">NUEVO PROYECTO</span>
                <h2>Crear espacio de trabajo</h2>
            </div>
            <div class="mode-switch"><button :class="{ active: mode === 'pdf' }" type="button" @click="mode = 'pdf'">Desde
                    PDF</button><button :class="{ active: mode === 'zip' }" type="button" @click="mode = 'zip'">Desde ZIP
                    NIMAS</button></div>
        </div>
        <form class="create-form" @submit.prevent="submit"><label>Nombre del proyecto<input v-model="name" required
                    placeholder="Ej. Ciencias 2026" /></label><label v-if="mode === 'zip'">ZIP original<input type="file"
                    accept=".zip" required @change="zip = $event.target.files[0]" /></label><label>PDF de referencia<input
                    type="file" accept="application/pdf,.pdf" multiple required
                    @change="pdfs = [...$event.target.files]" /></label><button type="submit" :disabled="busy">{{ busy ?
                        'Creando…' : 'Crear proyecto' }}</button></form>
        <p v-if="message" class="notice">{{ message }}</p>
    </section>
</template>
