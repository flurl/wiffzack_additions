<script setup>
import { computed } from 'vue';
import QuitButton from './QuitButton.vue';

const props = defineProps({
    title: {
        type: String,
    },
    loading: {
        type: Boolean,
        default: false,
    },
    error: {
        type: String,
        default: null,
    },
});


const loadingClass = computed(() => {
    return props.loading ? 'loading' : '';
});

</script>

<template>
    <header>
        <h1>{{ title }}</h1>
        <QuitButton />
    </header>
    <div class="spinner-container">
        <div class="spinner" :class="loadingClass"></div>
    </div>
    <div v-if="error" class="error-message">
        {{ error }}
    </div>
</template>

<style lang="scss" scoped>
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    left: 0;
    right: 0;
    background-color: $light-background;

    h1 {
        align-self: flex-end;
        font-size: 140%;
    }

}

.spinner-container {
    display: flex;
    justify-content: center;
    align-items: center;
    // height: 100%;

    .spinner {
        display: none;
        border: 4px solid rgba(0, 0, 0, 0.1);
        border-left-color: #09f;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;

        &.loading {
            display: block;
        }
    }
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

.error-message {
    color: red;
    margin-top: 1rem;
    font-weight: bold;
}
</style>
