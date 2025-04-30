import { createRouter, createWebHistory } from 'vue-router'
import DataTable from '../components/DataTable.vue'
import Storage from '../components/Storage.vue'
import MessageList from '../components/MessageList.vue'
import MessageView from '../components/MessageView.vue'
import InvoicePrintDialog from '../components/InvoicePrintDialog.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/data_table/:endpoint(.+)',
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
    {
      path: '/message/list',
      name: 'list_messages',
      component: MessageList,
      props: false,
    },
    {
      path: '/message/view/:msgPath',
      name: 'view_message',
      component: MessageView,
      props: false,
    },
    {
      path: '/invoices',
      name: 'invoices',
      component: InvoicePrintDialog,
      props: false,
    },
  ],
})

export default router
