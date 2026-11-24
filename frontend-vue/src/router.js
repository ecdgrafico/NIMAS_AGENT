import { createRouter, createWebHistory } from 'vue-router'
import ProjectLibraryView from './views/ProjectLibraryView.vue'
import ProjectWorkspaceView from './views/ProjectWorkspaceView.vue'
import LessonAuditView from './views/LessonAuditView.vue'
import VisualAuditView from './views/VisualAuditView.vue'
import MetadataView from './views/MetadataView.vue'
import StructureView from './views/StructureView.vue'
import EditorialAuditView from './views/EditorialAuditView.vue'
import AssetsView from './views/AssetsView.vue'
import PackageView from './views/PackageView.vue'
import UnitAuditView from './views/UnitAuditView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/projects' },
    { path: '/projects', component: ProjectLibraryView },
    { path: '/workspace', component: ProjectWorkspaceView },
    { path: '/lessons', component: LessonAuditView },
    { path: '/lessons/:lesson', component: VisualAuditView },
    { path: '/metadata', component: MetadataView },
    { path: '/structure', component: StructureView }
    ,{ path: '/editorial', component: EditorialAuditView }
    ,{ path: '/assets', component: AssetsView }
    ,{ path: '/package', component: PackageView }
    ,{ path: '/unit/:unit', component: UnitAuditView }
  ]
})
