<script setup>
import { ref, onMounted, onUpdated, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import Header from './Header.vue';
import { useChecklist } from '../composables/useChecklist';
import dragscroll from 'dragscroll';

const { t } = useI18n();

const mode = ref('review');
const currentChecklistMaster = ref(null);
const selectedChecklist = ref(null);

const {
    checklistMasters,
    isLoading,
    error,
    checklistHistory,
    currentChecklistId,
    checklistAnswers,
    fetchChecklistMasters,
} = useChecklist({ mode, currentChecklistMaster });

onMounted(() => {
    fetchChecklistMasters();
    document.getElementsByTagName('body')[0].classList.add('dragscroll');
    dragscroll.reset();
});

onUpdated(() => {
    dragscroll.reset();
});

const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

watch(selectedChecklist, (newChecklist, oldChecklist) => {
    currentChecklistId.value = newChecklist?.id;
});

</script>

<template>
    <div class="wrapper">
        <Header :title="t('message.checklists')" :loading="isLoading" :error="error" />
        <div class="checklists-wrapper">
            <div class="checklist-list master-list">
                <ul>
                    <li v-for="checklistMaster in checklistMasters" @click="currentChecklistMaster = checklistMaster"
                        :class="{ selected: currentChecklistMaster?.id === checklistMaster.id }">
                        {{ checklistMaster.category }}: {{ checklistMaster.name }}
                    </li>
                </ul>
            </div>

            <div class="checklist-list history-list">
                <div v-if="currentChecklistMaster">
                    <ul>
                        <li v-for="checklist in checklistHistory" @click="selectedChecklist = checklist"
                            :class="{ selected: selectedChecklist?.id === checklist.id }">
                            {{ formatDate(checklist.datum) }}
                        </li>
                    </ul>
                </div>
            </div>

            <div class="checklist-detail" v-if="selectedChecklist">
                <h2>{{ formatDate(selectedChecklist.datum) }}</h2>
                <ul>
                    <li v-for="answer in checklistAnswers">
                        <h3>{{ answer.question_text }}</h3>
                        <button class="btn_done" :class="{ selected: answer.choice === true }" disabled>{{
                            t('message.done') }}</button>
                        <button class="btn_skip" :class="{ selected: answer.choice === false }" disabled>{{
                            t('message.skip') }}</button>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.wrapper {
    display: flex;
    flex-direction: column;
}

.checklists-wrapper {
    display: flex;
    flex-direction: row;
    flex-grow: 1;
    overflow: scroll;
}

.checklists-wrapper>* {
    flex: 1;
}

.checklist-list {
    max-width: 33%;
    overflow: auto;

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


.pending {
    background-color: color.scale($light-warning, $lightness: 50%);
}

.checklist-detail {
    background-color: $light-highlight;
    padding: 1rem;

    .btn_done.selected {
        background-color: $light-confirm;
    }

    .btn_skip.selected {
        background-color: $light-cancel;
    }
}
</style>