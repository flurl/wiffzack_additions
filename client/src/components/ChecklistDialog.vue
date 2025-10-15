<script setup>
import { inject, ref, getCurrentInstance, onMounted, onUpdated, watch } from 'vue'
import { useI18n } from 'vue-i18n'

// import { computed } from 'vue';
import Header from './Header.vue';
import axios from 'axios';

import dragscroll from 'dragscroll';

const { t } = useI18n();
const config = inject('config');

// get the current instance
const instance = getCurrentInstance();
// get the global properties.
const $terminalConfig = instance.appContext.config.globalProperties.$terminalConfig;

const mode = ref('complete');
const checklistCategory = ref(null);

const currentChecklistMaster = ref(null);
const checklistMasters = ref([]);
const isLoading = ref(false);
const error = ref(null);

const fetchChecklistMasters = async () => {
    isLoading.value = true;
    error.value = null;

    let url;
    if (checklistCategory.value !== null) {
        url = `${config.backendHost}/api/checklist/master/list/category/${checklistCategory.value}`;
    } else {
        url = `${config.backendHost}/api/checklist/master/list`;
    }

    try {
        const response = await axios.get(url);
        if (response.data && Array.isArray(response.data.data)) {
            checklistMasters.value = response.data.data;
        } else {
            checklistMasters.value = [];
            console.warn('Unexpected data structure for checklist masters:', response.data);
        }
    } catch (err) {
        error.value = t('message.error_fetching_checklists') + ': ' + err.message;
        console.error('Error fetching checklist masters:', err);
    } finally {
        isLoading.value = false;
    }
};

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

    // Dragscroll initialization
    //document.querySelector('.checklist-detail').classList.add('dragscroll');
    //dragscroll.reset();
});

onUpdated(() => {
    dragscroll.reset();
});




const createNewChecklistMaster = async () => {
    const category = window.prompt(t('message.enter_checklist_category'));
    if (!category) {
        return; // User cancelled the first prompt
    }

    const name = window.prompt(t('message.enter_new_checklist_name'));
    if (name) { // Checks for non-empty string, as prompt returns null on cancel.
        isLoading.value = true;
        error.value = null;
        try {
            const response = await axios.post(`${config.backendHost}/api/checklist/master/new`, {
                name: name,
                category: category
            });
            if (response.data && response.data.success) {
                fetchChecklistMasters(); // Refresh the list on success
            }
        } catch (err) {
            console.error('Error creating new checklist master:', err);
            error.value = t('message.error_creating_checklist') + ': ' + err.message;
        } finally {
            isLoading.value = false;
        }
    }
};

const updateChecklistMaster = async (master) => {
    isLoading.value = true;
    error.value = null;
    try {
        await axios.post(`${config.backendHost}/api/checklist/master/update/${master.id}`, {
            name: master.name,
            category: master.category
        });
        // Optionally, you can add success feedback here
    } catch (err) {
        console.error('Error updating checklist master:', err);
        error.value = t('message.error_updating_checklist') + ': ' + err.message; // You'll need to add this translation
    } finally {
        isLoading.value = false;
    }
};

const deleteChecklistMaster = async (master) => {
    // Use translation for the confirmation message
    if (window.confirm(t('message.confirm_delete_checklist', { name: master.name }))) {
        isLoading.value = true;
        error.value = null;
        try {
            const response = await axios.get(`${config.backendHost}/api/checklist/master/delete/${master.id}`);
            if (response.data && response.data.success) {
                fetchChecklistMasters(); // Refresh the list on success
            }
        } catch (err) {
            console.error('Error deleting checklist master:', err);
            error.value = t('message.error_deleting_checklist') + ': ' + err.message;
        } finally {
            isLoading.value = false;
        }
    }
};

const checklistMasterQuestions = ref([]);

const createNewChecklistMasterQuestion = async () => {
    checklistMasterQuestions.value.push({ text: '', order: 0, master_id: currentChecklistMaster.value.id });
};

const fetchChecklistMasterQuestions = async () => {
    isLoading.value = true;
    error.value = null;
    try {
        const response = await axios.get(`${config.backendHost}/api/checklist/master/${currentChecklistMaster.value.id}/questions`);
        if (response.data && Array.isArray(response.data.data)) {
            checklistMasterQuestions.value = response.data.data;
        } else {
            checklistMasterQuestions.value = [];
            console.warn('Unexpected data structure for checklist questions:', response.data);
        }
    } catch (err) {
        error.value = t('message.error_fetching_checklists') + ': ' + err.message;
        console.error('Error fetching checklist questions:', err);
    } finally {
        isLoading.value = false;
    }
};

const saveChecklistMasterQuestions = async () => {
    let i = 0;
    checklistMasterQuestions.value.forEach(question => {
        question.order = i++;
    });
    for (const question of checklistMasterQuestions.value) {
        if (question.text.trim() !== '') {
            if (question.id !== undefined) {
                // update the question using the api endpoint /api/checklist/question/update/<int:question_id>
                const response = await axios.post(`${config.backendHost}/api/checklist/question/update/${question.id}`, {
                    text: question.text,
                    order: question.order,
                    master_id: question.master_id
                });
            } else {
                // create the question
                const response = await axios.post(`${config.backendHost}/api/checklist/question/new`, {
                    text: question.text,
                    order: question.order,
                    master_id: currentChecklistMaster.value.id
                });
            }
        } else {
            // if the question is empty and already has an id, delete it in the database
            if (question.id !== undefined) {
                const response = await axios.get(`${config.backendHost}/api/checklist/question/delete/${question.id}`);
            }
        }
    }
    fetchChecklistMasterQuestions(); // Refresh the list after saving
};

const moveQuestionUp = (question) => {
    const index = checklistMasterQuestions.value.indexOf(question);
    if (index > 0) {
        const temp = checklistMasterQuestions.value[index - 1];
        checklistMasterQuestions.value[index - 1] = question;
        checklistMasterQuestions.value[index] = temp;
    }
}

const moveQuestionDown = (question) => {
    const index = checklistMasterQuestions.value.indexOf(question);
    if (index < checklistMasterQuestions.value.length - 1) {
        const temp = checklistMasterQuestions.value[index + 1];
        checklistMasterQuestions.value[index + 1] = question;
        checklistMasterQuestions.value[index] = temp;
    }
}

watch(currentChecklistMaster, (newMaster) => {
    if (mode.value === 'edit') {
        if (newMaster.id !== undefined) {
            fetchChecklistMasterQuestions();
        } else {
            // Clear the questions list if no master is selected
            checklistMasterQuestions.value = [];
        }
    } else {
        if (newMaster.id !== undefined) {
            fetchLatestChecklist();
        }
    }
});


const currentChecklistId = ref(null);
const checklistAnswers = ref([]);

const createNewChecklist = async () => {
    // pass the currentChecklistMasterId to the backend endpoint /api/checklist/new_from_master/<int:master_id>
    isLoading.value = true;
    error.value = null;
    try {
        const response = await axios.get(`${config.backendHost}/api/checklist/new_from_master/${currentChecklistMaster.value.id}`);
        if (response.data && response.data.success) {
            // Assuming the response contains the newly created checklist's questions
            // checklistQuestions.value = response.data.data;
        }
    } catch (err) {
        console.error('Error creating new checklist from master:', err);
        error.value = t('message.error_creating_checklist') + ': ' + err.message;
    } finally {
        isLoading.value = false;
    }
    fetchLatestChecklist();
};

const fetchLatestChecklist = async () => {
    isLoading.value = true;
    error.value = null;
    try {
        const response = await axios.get(`${config.backendHost}/api/checklist/latest/${currentChecklistMaster.value.id}`);
        if (response.data && response.data.success) {
            currentChecklistId.value = response.data.data.id;
        } else {
            currentChecklistId.value = null;
        }
    } catch (err) {
        console.error('Error fetching latest checklist:', err);
        error.value = t('message.error_fetching_checklists') + ': ' + err.message;
    } finally {
        isLoading.value = false;
    }
};


const closeChecklist = async () => {
    isLoading.value = true;
    error.value = null;
    try {
        const response = await axios.get(`${config.backendHost}/api/checklist/close/${currentChecklistId.value}`);
        if (response.data && response.data.success) {
            fetchLatestChecklist();
        }
    } catch (err) {
        console.error('Error closing checklist:', err);
        error.value = t('message.error_closing_checklist') + ': ' + err.message;
    } finally {
        isLoading.value = false;
    }
}


const fetchChecklistAnswers = async () => {
    isLoading.value = true;
    error.value = null;
    try {
        const response = await axios.get(`${config.backendHost}/api/checklist/answers/${currentChecklistId.value}`);
        if (response.data && Array.isArray(response.data.data)) {
            checklistAnswers.value = response.data.data;
        } else {
            checklistAnswers.value = [];
            console.warn('Unexpected data structure for checklist answers:', response.data);
        }
    } catch (err) {
        console.error('Error fetching checklist answers:', err);
        error.value = t('message.error_fetching_checklist_answers') + ': ' + err.message;
    } finally {
        isLoading.value = false;
    }
};


const updateChecklistAnswer = async (answer, choice) => {
    answer.choice = answer.choice !== choice ? choice : null;

    try {
        const response = await axios.post(`${config.backendHost}/api/checklist/answer/update/${answer.id}`, {
            choice: answer.choice,
            checklist_id: answer.checklist_id,
            question_text: answer.question_text

        });
        if (response.data && response.data.success) {
            fetchChecklistAnswers();
        }
    } catch (err) {
        console.error('Error updating checklist answer:', err);
    }
};


watch(currentChecklistId, (newChecklistId) => {
    if (newChecklistId !== null) {
        fetchChecklistAnswers();
    } else {
        // Clear the questions list if no checklist is selected
        checklistAnswers.value = [];
    }
});



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



            <div class="checklist-detail dragscroll" v-if="currentChecklistMaster">
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
    height: 100vh;
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
    overflow: scroll;

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
    .btn_done.selected {
        background-color: $light-confirm;
    }

    .btn_skip.selected {
        background-color: $light-cancel;
    }
}
</style>
