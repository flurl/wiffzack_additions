import { createRouter, createWebHistory } from 'vue-router'
import DataTable from '../components/DataTable.vue'
import Storage from '../components/Storage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/data_table/:endpoint',
      name: 'data_table',
      component: DataTable,
      props: true,
    },
    {
      path: '/storage/:mode',
      name: 'storage',
      component: Storage,
      props: true,
    },
  ],
})

export default router
