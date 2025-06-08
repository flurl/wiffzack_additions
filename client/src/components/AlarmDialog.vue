<script setup>
import { ref, computed, inject, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useApiData } from '../composables/useApiData';
import Header from './Header.vue';
import ModalDialog from './ModalDialog.vue';

const { t } = useI18n();
const appConfig = inject('config');

const clientNameFromUrl = ref(null);

const alarmUrlPath = computed(() => {
    if (clientNameFromUrl.value && appConfig.backendHost) {
        return `/api/alarm/trigger/${clientNameFromUrl.value}`;
    }
    return null;
});

const { fetchData: triggerAlarmRequest, error: alarmError } = useApiData(
    alarmUrlPath,
    {
        immediate: false, // We will call fetchData manually
    }
);

const modalConf = ref({
    show: false,
    title: "",
    body: "",
    type: "info",
    buttons: { ok: true, cancel: true },
    currentOkCallback: null,
    currentCancelCallback: null,
});

const displayModal = (config) => {
    modalConf.value.title = config.title;
    modalConf.value.body = config.body || "";
    modalConf.value.type = config.type || "info";
    modalConf.value.buttons = config.buttons || { ok: true, cancel: true };
    modalConf.value.currentOkCallback = config.okCallback;
    modalConf.value.currentCancelCallback = config.cancelCallback;
    modalConf.value.show = true;
};

const handleModalOK = () => {
    if (modalConf.value.currentOkCallback) {
        modalConf.value.currentOkCallback();
    }
};

const handleModalCancel = () => {
    if (modalConf.value.currentCancelCallback) {
        modalConf.value.currentCancelCallback();
    }
};

const performAlarmTrigger = async () => {
    if (!alarmUrlPath.value) {
        displayModal({
            title: t('message.error'),
            body: t('message.alarm_url_construction_error'),
            type: 'error',
            buttons: { ok: true, cancel: false },
            okCallback: () => { modalConf.value.show = false; window.close(); }
        });
        return;
    }

    displayModal({
        title: t('message.alarm') + "...",
        body: t('message.sending_alarm_signal'),
        type: 'info',
        buttons: { ok: false, cancel: false }
    });

    await triggerAlarmRequest();

    if (alarmError.value) {
        displayModal({
            title: t('message.error'),
            body: alarmError.value,
            type: 'error',
            buttons: { ok: true, cancel: false },
            okCallback: () => { modalConf.value.show = false; } // Keep window open on error for user to see
        });
    } else {
        displayModal({
            title: t('message.success'),
            body: t('message.trigger_alarm_success'),
            type: 'success',
            buttons: { ok: true, cancel: false },
            okCallback: () => {
                modalConf.value.show = false;
                window.close(); // Close after successful alarm trigger and OK
            }
        });
    }
};

const initialDialogCancelCallback = () => {
    modalConf.value.show = false;
    window.close();
};

onMounted(() => {
    const urlParams = new URLSearchParams(window.location.search);
    clientNameFromUrl.value = urlParams.get('terminal');

    if (!clientNameFromUrl.value) {
        displayModal({
            title: t('message.error'),
            body: t('message.terminal_id_not_found_error'),
            type: 'error',
            buttons: { ok: true, cancel: false },
            okCallback: () => { modalConf.value.show = false; window.close(); }
        });
    } else {
        displayModal({
            title: t('message.trigger_alarm'),
            type: 'question',
            buttons: { ok: true, cancel: true },
            okCallback: performAlarmTrigger,
            cancelCallback: initialDialogCancelCallback
        });
    }
});
</script>

<template>
    <Header :title="$t('message.alarm')" />
    <ModalDialog :title="modalConf.title" :show="modalConf.show" :buttons="modalConf.buttons" :type="modalConf.type"
        @ok="handleModalOK" @cancel="handleModalCancel">
        <p v-if="modalConf.body">{{ modalConf.body }}</p>
    </ModalDialog>
</template>

<style scoped>
/* Styles for AlarmDialog if any specific ones are needed */
</style>
