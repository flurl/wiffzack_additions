<script setup>
import { inject } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'


import Header from './Header.vue';
import { useApiData } from '@/composables/useApiData';

const { t } = useI18n();
const config = inject('config');
const route = useRoute();
const msgPath = route.params.msgPath;

const apiUrl = `/api/message/${msgPath}`;

// Use the composable
const {
    data: message, // Rename data to message
    isLoading,
    error,
    fetchData // Optional: if you need to manually refresh
} = useApiData(apiUrl, { // Pass the static API path
    initialData: null,
    transformResponse: (responseData) => {
        // Extract the single message object
        return responseData?.success ? responseData.data.message : null;
    }
});

</script>

<template>
    <div class="wrapper">
        <template v-if="message">
            <template v-if="message.type === 'txt'">
                <Header :title="message.name" :loading="false" />
                <pre>{{ message.content }}</pre>
            </template>
            <template v-else-if="message.type === 'html'">
                <Header :title="message.name" :loading="false" />
                <iframe class="message-iframe" :src="`${config.backendHost}/message/html/${message.path}/`"></iframe>
            </template>
        </template>
    </div>
</template>

<style lang="scss" scoped>
.wrapper {
    height: 100vh;
    display: flex;
    flex-direction: column;
}

.message-iframe {
    width: 100%;
    height: 100%;
}
</style>
