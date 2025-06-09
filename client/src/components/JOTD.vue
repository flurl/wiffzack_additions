<script setup>
import { inject } from 'vue'
import { useI18n } from 'vue-i18n'

import Header from './Header.vue';
import { useApiData } from '@/composables/useApiData';

const { t } = useI18n();
const config = inject('config');

const apiUrl = `/api/jotd`;

// Use the composable
const {
    data: jotd, // Rename data to jodt
    isLoading,
    error,
    fetchData // Optional: if you need to manually refresh
} = useApiData(apiUrl, { // Pass the static API path
    initialData: true,
    transformResponse: (responseData) => {
        // Extract the single message object
        return responseData?.success ? responseData.data : null;
    }
});

</script>

<template>
    <Header title="JOTD" :loading="isLoading" :error="error" />
    <pre>{{ jotd }}</pre>
</template>

<style lang="scss" scoped>
pre {
    white-space: pre-wrap;
}
</style>
