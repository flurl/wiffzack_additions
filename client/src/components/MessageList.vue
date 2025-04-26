<script setup>
import { useI18n } from 'vue-i18n'

import Header from './Header.vue';
import { useApiData } from '@/composables/useApiData';

const { t } = useI18n();

// Use the composable
const {
    data: availableMessages, // Rename data to availableMessages
    isLoading,
    error,
    fetchData // Optional: if you need to manually refresh
} = useApiData('/api/message/list', { // Pass the static API path
    initialData: [], // Set initial data to an empty array
    transformResponse: (responseData) => {
        // Extract the messages array based on your API structure
        return responseData?.success ? responseData.messages : [];
    }
});

</script>

<template>
    <Header :title="t('message.messages')" :loading="isLoading" :error="error" />
    <table>
        <tr v-for="message in availableMessages">
            <td>
                <RouterLink :to="{ name: 'view_message', params: { msgPath: message.path } }">{{ message.name }}
                </RouterLink>
            </td>
        </tr>
    </table>
</template>

<style lang="scss" scoped></style>