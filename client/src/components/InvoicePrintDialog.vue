<script setup>
import { inject, ref, getCurrentInstance } from 'vue'
import { useI18n } from 'vue-i18n'

import { computed } from 'vue';
import Header from './Header.vue';
import ToggleSwitch from './ToggleSwitch.vue';
import { useApiData } from '@/composables/useApiData';
import axios from 'axios';

const { t } = useI18n();
const config = inject('config');

// get the current instance
const instance = getCurrentInstance();
// get the global properties.
const $terminalConfig = instance.appContext.config.globalProperties.$terminalConfig;

const currentInvoiceId = ref(null);
const invoiceSrc = computed(() => {
    return `${config.backendHost}/api/invoice/html/${currentInvoiceId.value}`;
});

const selectedInvoiceType = ref(null);
const showAllInvoices = ref(false);
const invoiceListUrl = computed(() => {
    let url = `/api/invoice/list`;
    if (!showAllInvoices.value) {
        url += `/${$terminalConfig.name}`;
    }
    if (selectedInvoiceType.value && selectedInvoiceType.value !== 'all') {
        url += `?invoice_type=${selectedInvoiceType.value}`;
    }
    return url;
});

// Use the composable
const {
    data: invoices, // Rename data to invoices
    isLoading,
    error,
    fetchData // Optional: if you need to manually refresh
} = useApiData(invoiceListUrl, { // Pass the static API path
    initialData: [], // Set initial data to an empty array
    transformResponse: (responseData) => {
        // Extract the messages array based on your API structure
        return responseData?.success ? responseData.data : [];
    }
});

// --- Invoice Types Data Fetching ---
const invoiceTypesApiUrl = '/api/invoice_type'; // Correct API endpoint for all invoice types

// Use the composable
const {
    data: invoiceTypes,
    isLoading: isLoadingInvoiceTypes, // Using a distinct loading state
    error: errorInvoiceTypes,         // Using a distinct error state
    fetchData: fetchDataInvoiceTypes // Optional, if manual refresh is needed
} = useApiData(invoiceTypesApiUrl, {
    initialData: [], // Set initial data to an empty array
    transformResponse: (responseData) => {
        // The backend returns an array of arrays/tuples:
        // [rechnung_typ_id, rechnung_typ_kurz, rechnung_typ_bezeichnung, ...]
        if (responseData?.success && Array.isArray(responseData.data)) {
            return responseData.data;
        }
        console.warn(`Failed to fetch or transform invoice types from ${invoiceTypesApiUrl}.`);
        return [];
    }
});


const invoiceTypesOptions = computed(() => {
    const options = { [t('message.all')]: 'all' }; // Use translation for "All"
    if (invoiceTypes.value && invoiceTypes.value.length > 0) {
        invoiceTypes.value.forEach(typeArray => {
            // typeArray[0] is rechnung_typ_bezeichnung (name/key for the option)
            // typeArray[2] is rechnung_typ_id (value for the option)
            if (typeArray && typeArray.length > 2) { // Basic check for data integrity
                options[typeArray[0]] = typeArray[2];
            }
        });
    }
    return options;
});

const printInvoice = () => {
    axios.get(`${config.backendHost}/api/invoice/print/${currentInvoiceId.value}`);
}


</script>

<template>
    <div class="wrapper">
        <Header :title="t('message.invoices')" :loading="isLoading" :error="error" />
        <div class="invoices-wrapper">
            <div class="invoice-list">
                <ToggleSwitch :checked="showAllInvoices" @toggled="showAllInvoices = !showAllInvoices"></ToggleSwitch>
                {{ t('message.show_all_invoices') }}
                <select class="invoice-types" v-model="selectedInvoiceType" @change="fetchData()">
                    <option v-for="(name, id) in invoiceTypesOptions" :value="id">{{ name }}</option>
                </select>
                <ul>
                    <li v-for="invoice in invoices" @click="currentInvoiceId = invoice[0]"
                        :class="{ selected: currentInvoiceId === invoice[0] }">
                        {{ new Date(invoice[2]).toISOString().slice(0, 16).replace('T', ' ') }}<br>{{ invoice[4] }} - {{
                            invoice[3] }}
                    </li>
                </ul>
            </div>
            <div class="invoice-preview" v-if="currentInvoiceId">
                <object class="invoice-preview-element" :data="invoiceSrc" type="text/html"></object>
                <button class="print-invoice-btn" @click="printInvoice">{{ t('message.print') }}</button>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.wrapper {
    height: 100vh;
    display: flex;
    flex-direction: column;
}

.invoices-wrapper {
    display: flex;
    flex-direction: row;
    flex-grow: 1;
    overflow: scroll;
}

.invoices-wrapper>* {
    flex: 1;
}

.invoice-preview {
    display: flex;
    flex-direction: column;
}

.invoice-preview-element {
    width: 100%;
    height: 100%;
}

// format the invoice list rows with alternating colors
.invoice-list {
    max-width: 50%;
    overflow: scroll;

    ul {
        list-style: none;
        padding: 0;
        margin: 0;

        li {
            padding: 0.5rem;
            border-bottom: 1px solid $light-border;
            background-color: $light-button-background;

            &:nth-child(odd) {
                background-color: color.scale($light-button-background, $lightness: +30%);
            }

            &.selected {
                border-color: $light-highlight;
                background-color: $light-highlight;
            }
        }
    }
}
</style>
