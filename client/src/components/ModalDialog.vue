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
        default: () => ({ok: true, cancel: true})
    }
});

const emit = defineEmits(['cancel', 'ok']);

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
</script>

<template>
    <dialog ref="modal">
        <div class="modal-content">
                <header>
                    <h2 class="modal-title">{{ title }}</h2>
                </header>
                <section>
                    <slot></slot>
                </section>
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

<style scoped>

</style>
