<script setup>
defineProps({job:{type:Object,default:null}})
</script>
<template><section v-if="job?.running" class="job-card" aria-live="polite"><span class="pulse"></span><div><strong>{{job.stage||'Trabajo en curso'}}</strong><small>{{job.lesson||'Procesando proyecto'}} · {{job.queue?.length||0}} pendientes</small></div></section><section v-else-if="job?.events?.length" class="job-card done"><strong>Último resultado</strong><small>{{job.events[job.events.length-1].message}}</small></section></template>
