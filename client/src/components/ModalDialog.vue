<script setup>
import { ref, onMounted, watch, computed } from 'vue';

const props = defineProps({
    show: {
        type: Boolean,
        default: false,
    },
    title: {
        type: String,
        default: 'Modal Title',
    },
    buttons: {
        type: [Object, Array],
        default: () => ({ ok: true, cancel: true }),
    },
    type: {
        type: String,
        default: 'info'
    }
});

const emit = defineEmits(['cancel', 'ok', 'yes', 'no']);

const modal = ref(null);

const showModal = () => {
    modal.value.showModal();
};
const hideModal = () => {
    modal.value.close();
};

const normalizedButtons = computed(() => {
    if (Array.isArray(props.buttons)) {
        return props.buttons;
    }

    const buttonList = [];
    if (props.buttons.no) {
        buttonList.push({ text: 'message.no', event: 'no', class: 'cancel', icon: ['fas', 'xmark'] });
    }
    if (props.buttons.yes) {
        buttonList.push({ text: 'message.yes', event: 'yes', class: 'confirm', icon: ['fas', 'check'] });
    }
    if (props.buttons.cancel) {
        buttonList.push({ text: 'message.cancel', event: 'cancel', class: 'cancel', icon: ['fas', 'xmark'] });
    }
    if (props.buttons.ok) {
        buttonList.push({ text: 'message.OK', event: 'ok', class: 'confirm', icon: ['fas', 'check'] });
    }
    return buttonList;
});

const handleButtonClick = (eventToEmit) => {
    if (eventToEmit) {
        emit(eventToEmit);
    }
};

const onDialogCancel = (event) => {
    // This event is fired when the user presses the ESC key.
    // We emit a 'cancel' event to allow the parent to handle it,
    // for example, by setting the `show` prop to false.
    emit('cancel');
}


const showOrHideModal = () => {
    if (props.show) {
        showModal();
    } else {
        hideModal();
    }
};
watch(() => props.show, showOrHideModal);


onMounted(() => {
    showOrHideModal();
});
</script>

<template>
    <dialog ref="modal" :class="props.type" @cancel="onDialogCancel">
        <div class="modal-content">
            <header>
                <h2 class="modal-title">{{ title }}</h2>
            </header>
            <section>
                <slot></slot>
            </section>
            <div class="modal-buttons">
                <button v-for="(button, index) in normalizedButtons" :key="index" :class="button.class"
                    @click="handleButtonClick(button.event)">
                    <span class="icon" v-if="button.icon">
                        <font-awesome-icon :icon="button.icon" />
                    </span>
                    <span>{{ $t(button.text) }}</span>
                </button>
            </div>
        </div>
    </dialog>
</template>

<style lang="scss" scoped>
dialog {
    &.success {
        border: 1rem solid $light-success;
    }

    &.warning {
        border: 1rem solid $light-warning;
    }

    &.error {
        border: 1rem solid $light-error;
    }

    &.info {
        border: 1rem solid $light-info;
    }

    &.question {
        border: 1rem solid $light-question;
    }

    .modal-title {
        &::before {
            display: inline-block; // Ensures proper spacing and alignment
            margin-right: 0.5em; // Space between icon and title text
            font-weight: normal; // Or bold, depending on preference
            font-size: 2em; // Relative to the title's font size
        }
    }

    &.success .modal-title::before {
        content: '✔'; // Unicode check mark
        color: $light-success;
    }

    &.warning .modal-title::before {
        content: '⚠'; // Unicode warning sign
        color: $light-warning;
    }

    &.error .modal-title::before {
        content: '✖'; // Unicode multiplication X (heavy X)
        color: $light-error;
    }

    &.info .modal-title::before {
        content: 'ℹ'; // Unicode information source
        color: $light-info;
    }

    &.question .modal-title::before {
        content: '❓'; // Unicode question mark
        color: $light-question;
    }

    .modal-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        padding-top: 1rem;
    }

    .modal-content {
        position: relative;

        header {
            padding-right: 2rem; // Space for the close button
        }
    }
}
</style>
