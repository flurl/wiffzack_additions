<script setup>
import { ref, onMounted, watch } from 'vue';

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
        type: Object,
        default: () => ({ ok: true, cancel: true })
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

const modalCancel = () => {
    //modal.value.classList.remove('is-active');
    emit('cancel');
};
const modalOK = () => {
    //modal.value.classList.remove('is-active');
    emit('ok');
};
const modalYes = () => {
    emit('yes');
};
const modalNo = () => {
    emit('no');
};
</script>

<template>
    <dialog ref="modal" :class="props.type">
        <div class="modal-content">
            <header>
                <h2 class="modal-title">{{ title }}</h2>
            </header>
            <section>
                <slot></slot>
            </section>
            <button class="cancel" v-if="buttons.no" @click="modalNo">
                <span class="icon">
                    <font-awesome-icon :icon="['fas', 'xmark']" />
                </span>
                <span>{{ $t('message.no') }}</span>
            </button>
            <button class="confirm" v-if="buttons.yes" @click="modalYes">
                <span class="icon">
                    <font-awesome-icon :icon="['fas', 'check']" />
                </span>
                <span>{{ $t('message.yes') }}</span>
            </button>
            <button class="cancel" v-if="buttons.cancel" @click="modalCancel">
                <span class="icon">
                    <font-awesome-icon :icon="['fas', 'xmark']" />
                </span>
                <span>{{ $t('message.cancel') }}</span>
            </button>
            <button class="confirm" v-if="buttons.ok" @click="modalOK">
                <span class="icon">
                    <font-awesome-icon :icon="['fas', 'check']" />
                </span>
                <span>{{ $t('message.OK') }}</span>
            </button>
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
}
</style>
