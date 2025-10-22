import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'
import DataTable from '../components/DataTable.vue'
import Storage from '../components/Storage.vue'
import StorageSelection from '@/components/StorageSelection.vue'
import MessageList from '../components/MessageList.vue'
import MessageView from '../components/MessageView.vue'
import InvoicePrintDialog from '../components/InvoicePrintDialog.vue'
import AlarmDialog from '@/components/AlarmDialog.vue'
import JOTD from '@/components/JOTD.vue'
import ChecklistDialog from '@/components/ChecklistDialog.vue'
import ChecklistReviewDialog from '@/components/ChecklistReviewDialog.vue'

const router = createRouter({
  // we need memory history mode to make window.close() work
  // it only works in windows created by the script or having
  // only one history entry. Memory History doesn't interact 
  // with the browser's history at all
  history: createMemoryHistory(),
  routes: [
    {
      path: '/data_table/:endpoint(.+)',
      name: 'data_table',
      component: DataTable,
      props: true,
    },
    {
      path: '/storage/selection',
      name: 'storage_selection',
      component: StorageSelection,
      props: false,
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
    {
      path: '/alarm',
      name: 'alarm',
      component: AlarmDialog,
      props: false,
    },
    {
      path: '/jotd',
      name: 'jotd',
      component: JOTD,
      props: false,
    },
    {
      path: '/checklist',
      name: 'checklist',
      component: ChecklistDialog,
      props: false,
    },
    {
      path: '/checklist/review',
      name: 'checklist_review',
      component: ChecklistReviewDialog,
      props: false,
    },
  ],
})

// The memory history mode doesn't assume a browser environment and therefore 
// doesn't interact with the URL nor automatically triggers the initial navigation.
// It is created with createMemoryHistory() and requires
// to push the initial navigation
router.push(window.location.pathname)

export default router
