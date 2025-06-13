<script setup>
import { computed } from 'vue';

const props = defineProps({
    modelValue: {
        type: String,
        required: true
    },
    searchMode: {
        type: String,
        required: true,
        validator: (value) => ['includes', 'startsWith'].includes(value)
    }
});

const emit = defineEmits(['update:modelValue', 'toggle-search-mode', 'reset-filter']);

const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split('');

const appendToFilter = (char) => {
    emit('update:modelValue', props.modelValue + char);
};

const backspaceFilter = () => {
    if (props.modelValue.length > 0) {
        emit('update:modelValue', props.modelValue.slice(0, -1));
    }
};

const handleToggleSearchMode = () => {
    emit('toggle-search-mode');
};

const handleResetFilter = () => {
    emit('reset-filter');
};

const searchModeDisplay = computed(() => {
    return props.searchMode === 'includes' ? 'Contains' : 'Starts With';
});

</script>

<template>
    <div class="keyboard-buttons">
        <button v-for="char in alphabet" :key="char" @click="appendToFilter(char)">
            {{ char }}
        </button>
        <button @click="appendToFilter(' ')" class="space-button">Space</button>
        <button @click="backspaceFilter" class="backspace-button">⌫</button>
        <br>
        <button @click="handleToggleSearchMode" class="search-mode-button">
            Mode: {{ searchModeDisplay }}
        </button>
        <button @click="handleResetFilter" class="reset-button">Reset</button>
    </div>
</template>

<style lang="scss" scoped>
.keyboard-buttons {
    display: flex;
    flex-wrap: wrap; // Allow buttons to wrap if not enough space
    gap: 5px; // Spacing between buttons
    justify-content: center; // Center buttons if they wrap
}

.keyboard-buttons button {
    margin: 2px; // Keep individual margin for finer control if needed
    padding: 10px 10px;
    min-width: 40px; // Ensure buttons have a decent minimum width
    text-align: center;
}

.reset-button {
    background-color: #f44336;
    /* Example danger color */
    color: white;
}

.search-mode-button {
    background-color: #2196F3;
    /* Example info color */
    color: white;
}

.backspace-button {
    background-color: #ff9800;
    /* Example warning/orange color */
    color: white;
    font-weight: bold;
}

.space-button {
    min-width: 80px; // Make the space button a bit wider
    background-color: #607d8b; // Example neutral color (blue grey)
    color: white; // Ensure text is visible
}
</style>
