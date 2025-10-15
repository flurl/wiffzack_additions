<script setup>
import { ref, onMounted, onUpdated } from 'vue';
import { useI18n } from 'vue-i18n';
import Header from './Header.vue';
import dragscroll from 'dragscroll';
import { useChecklist } from '../composables/useChecklist';

const { t } = useI18n();

const mode = ref('complete');
const checklistCategory = ref(null);
const currentChecklistMaster = ref(null);

const {
    checklistMasters,
    isLoading,
    error,
    checklistMasterQuestions,
    checklistAnswers,
    fetchChecklistMasters,
    createNewChecklistMaster: createNewChecklistMasterAction,
    updateChecklistMaster,
    deleteChecklistMaster,
    saveChecklistMasterQuestions,
    createNewChecklist,
    closeChecklist,
    updateChecklistAnswer,
} = useChecklist({ mode, checklistCategory, currentChecklistMaster });

onMounted(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const modeParam = urlParams.get('mode');
    if (modeParam) {
        mode.value = modeParam;
    }
    const checklistCategoryParam = urlParams.get('checklist_category');
    if (checklistCategoryParam) {
        checklistCategory.value = checklistCategoryParam;
    }
    fetchChecklistMasters();

    document.getElementsByTagName('body')[0].classList.add('dragscroll');
    dragscroll.reset();
});

onUpdated(() => {
    dragscroll.reset();
});


const createNewChecklistMaster = async () => {
    const category = window.prompt(t('message.enter_checklist_category'));
    if (!category) return;

    const name = window.prompt(t('message.enter_new_checklist_name'));
    if (name) {
        await createNewChecklistMasterAction(name, category);
    }
};

const createNewChecklistMasterQuestion = () => {
    checklistMasterQuestions.value.push({ text: '', order: 0, master_id: currentChecklistMaster.value.id });
};

const moveQuestionUp = (question) => {
    const index = checklistMasterQuestions.value.indexOf(question);
    if (index > 0) {
        [checklistMasterQuestions.value[index - 1], checklistMasterQuestions.value[index]] = [checklistMasterQuestions.value[index], checklistMasterQuestions.value[index - 1]];
    }
};

const moveQuestionDown = (question) => {
    const index = checklistMasterQuestions.value.indexOf(question);
    if (index < checklistMasterQuestions.value.length - 1) {
        [checklistMasterQuestions.value[index + 1], checklistMasterQuestions.value[index]] = [checklistMasterQuestions.value[index], checklistMasterQuestions.value[index + 1]];
    }
};
</script>

<template>
    <div class="wrapper">
        <Header :title="t('message.checklists')" :loading="isLoading" :error="error" />
        <div class="checklists-wrapper">
            <div class="checklist-list">
                <button v-if="mode === 'edit'" @click="createNewChecklistMaster">{{ t('message.new') }}…</button>
                <ul>
                    <li v-for="checklistMaster in checklistMasters" @click="currentChecklistMaster = checklistMaster"
                        :class="{ selected: currentChecklistMaster?.id === checklistMaster.id }">
                        <template v-if="mode === 'edit'">
                            <input type="text" v-model="checklistMaster.category"
                                @change="updateChecklistMaster(checklistMaster)"> :
                            <input type="text" v-model="checklistMaster.name"
                                @change="updateChecklistMaster(checklistMaster)">
                            <button class="delete delete-btn"
                                @click.stop="deleteChecklistMaster(checklistMaster)">🗑️</button>
                        </template>
                        <template v-else>
                            {{ checklistMaster.category }}: {{ checklistMaster.name }}
                        </template>
                    </li>
                </ul>
            </div>



            <div class="checklist-detail" v-if="currentChecklistMaster">
                <h2>{{ currentChecklistMaster.category }} : {{ currentChecklistMaster.name }}</h2>
                <template v-if="mode === 'complete'">
                    <button v-if="checklistAnswers.length === 0" @click="createNewChecklist">{{
                        t('message.new') }}</button>
                    <ul>
                        <li v-for="answer in checklistAnswers" :class="{ pending: answer.choice === null }">
                            <h3>{{ answer.question_text }}</h3>
                            <button class="btn_done" :class="{ selected: answer.choice === true }"
                                @click="updateChecklistAnswer(answer, true)">{{
                                    t('message.done') }}</button>
                            <button class="btn_skip" :class="{ selected: answer.choice === false }"
                                @click="updateChecklistAnswer(answer, false)">{{
                                    t('message.skip') }}</button>
                        </li>
                    </ul>
                    <button v-if="checklistAnswers.length >= 0" @click="closeChecklist">{{
                        t('message.close_checklist') }}</button>
                </template>
                <template v-if="mode === 'edit'">
                    <ul>
                        <li v-for="question in checklistMasterQuestions">
                            <template v-if="mode === 'edit'">
                                <input type="text" v-model="question.text"></input>
                                <button @click="moveQuestionUp(question)">↑</button>
                                <button @click="moveQuestionDown(question)">↓</button>
                            </template>
                            <template v-else>
                                {{ question.text }}
                            </template>
                        </li>
                    </ul>

                    <button @click="createNewChecklistMasterQuestion">{{ t('message.new') }}</button><br>
                    <button @click="saveChecklistMasterQuestions">{{ t('message.save') }}</button>
                </template>
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
    max-width: 50%;
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


.delete-btn {
    font-size: 3em;
    font-weight: bolder;
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
