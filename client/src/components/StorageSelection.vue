<script setup>
import { ref, onMounted, onUnmounted, watch, onUpdated, inject } from 'vue';
import { useApiData } from '@/composables/useApiData'; // Adjust path if needed
import Header from './Header.vue';

import dragscroll from 'dragscroll';

const config = inject('config');

const apiUrlPath = '/api/get_config';

// Use the composable
const {
    data: terminalConfigData, // Use data directly
    isLoading,
    error,
    // fetchData // Assuming useApiData fetches on init or if apiUrlPath were reactive
} = useApiData(apiUrlPath, {
    initialData: {}, // Ensure initialData is an object
    transformResponse: (responseData) => {
        console.log('Received data for config:', responseData);
        // Ensure config is a non-array object
        if (responseData?.success && responseData.config && typeof responseData.config === 'object' && !Array.isArray(responseData.config)) {
            return responseData.config;
        }
        console.warn(`Expected 'config' to be a non-array object in response from '${apiUrlPath}', or request failed. Returning empty object.`);
        return {}; // Return empty object for consistency
    }
});

const highlightStatus = ref({});
const intervalIds = ref({}); // Stores interval IDs: { terminalName: id }

async function checkRequestStorage(terminalName, requestStorageId) {
    if (requestStorageId === undefined || requestStorageId === null) {
        highlightStatus.value[terminalName] = false;
        return;
    }
    try {
        const response = await fetch(`${config.backendHost}/api/storage_article_groups/${requestStorageId}`);
        if (!response.ok) {
            console.error(`Error fetching article groups for ${terminalName} (storage ${requestStorageId}): ${response.statusText}`);
            highlightStatus.value[terminalName] = false;
            return;
        }
        const result = await response.json();
        highlightStatus.value[terminalName] = !!(result.success && Array.isArray(result.data) && result.data.length > 0);
    } catch (err) {
        console.error(`Exception fetching/processing article groups for ${terminalName} (storage ${requestStorageId}):`, err);
        highlightStatus.value[terminalName] = false;
    }
}

function clearAllIntervals() {
    Object.values(intervalIds.value).forEach(clearInterval);
    intervalIds.value = {};
}

watch(terminalConfigData, (newConfig) => {
    clearAllIntervals();
    highlightStatus.value = {}; // Reset statuses

    if (newConfig && typeof newConfig === 'object' && Object.keys(newConfig).length > 0) {
        Object.entries(newConfig).forEach(([name, config]) => {
            checkRequestStorage(name, config.request_storage_id); // Initial check

            if (config.request_storage_id !== undefined && config.request_storage_id !== null) {
                intervalIds.value[name] = setInterval(() => {
                    checkRequestStorage(name, config.request_storage_id);
                }, 10000); // Check every 10 seconds (adjust as needed)
            }
        });
    }
}, { deep: true, immediate: true }); // immediate to run when terminalConfigData is first populated

onMounted(() => {
    document.body.classList.add('dragscroll');
    dragscroll.reset(); // Initial reset
});

onUpdated(() => {
    dragscroll.reset(); // Reset if the list of terminals changes and affects scrollable area
});

onUnmounted(() => {
    clearAllIntervals();
    document.body.classList.remove('dragscroll');
});

</script>

<template>
    <Header title="Storage Selection" :loading="isLoading" :error="error" />
    <div v-if="isLoading" class="loading-message">Loading terminal configurations...</div>
    <div v-else-if="error" class="error-message">Error loading configurations: {{ error.message }}</div>
    <table v-else-if="terminalConfigData && Object.keys(terminalConfigData).length > 0" class="terminal-table">
        <thead>
            <tr>
                <th>Terminal Name</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(conf, name) in terminalConfigData" :key="name"
                :class="{ 'highlight-request': highlightStatus[name] }">
                <td>
                    <a :href="`/storage/distribute?terminal=lager&destTerminal=${name}`" target="_blank">
                        {{ name }}
                        <span v-if="highlightStatus[name]" class="highlight-indicator"
                            title="Items in request storage">⚠️</span>
                    </a>&nbsp;&nbsp;&nbsp;
                    <a :href="`/storage/stock?terminal=lager&sourceStorageId=0&destinationStorageId=${conf.transfer_storage_id}`"
                        target="_blank`"> ==></a>
                </td>
            </tr>
        </tbody>
    </table>
    <div v-else class="no-data-message">
        No terminal configurations available from "{{ apiUrlPath }}".
    </div>
</template>

<style scoped>
/* Add some basic styling */
table {
    font-size: 300%;
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
    table-layout: fixed;
    /* Helps with consistent column widths */
}

th,
td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    word-wrap: break-word;
    /* Prevent long names from breaking layout */
}

th {
    background-color: #f2f2f2;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

tr.highlight-request td {
    background-color: #fff3cd;
    /* A light yellow, similar to Bootstrap's warning */
    font-weight: bold;
}

.highlight-indicator {
    margin-left: 8px;
    color: orange;
}

.loading-message,
.error-message,
.no-data-message {
    margin-top: 1rem;
    padding: 1rem;
    border: 1px solid #ddd;
    background-color: #f9f9f9;
}
</style>
