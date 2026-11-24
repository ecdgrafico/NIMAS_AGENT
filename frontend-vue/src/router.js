import { createRouter, createWebHistory } from 'vue-router'
import ProjectLibraryView from './views/ProjectLibraryView.vue'
import ProjectWorkspaceView from './views/ProjectWorkspaceView.vue'
import LessonAuditView from './views/LessonAuditView.vue'
import MetadataView from './views/MetadataView.vue'
import StructureView from './views/StructureView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/projects' },
    { path: '/projects', component: ProjectLibraryView },
    { path: '/workspace', component: ProjectWorkspaceView },
    { path: '/lessons', component: LessonAuditView },
    { path: '/metadata', component: MetadataView },
    { path: '/structure', component: StructureView }
  ]
})
