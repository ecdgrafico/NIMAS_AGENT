import { onBeforeUnmount, ref } from 'vue'
import { api } from '../services/api'
export function useJob(){const job=ref(null),timer=ref(null);async function refresh(){job.value=await api.job();if(job.value.running)timer.value=setTimeout(refresh,1500)}onBeforeUnmount(()=>clearTimeout(timer.value));return{job,refresh}}
