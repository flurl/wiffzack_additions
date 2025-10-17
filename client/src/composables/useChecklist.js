// src/composables/useChecklist.js
import { ref, inject, watch } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

export function useChecklist(options = {}) {
    const { mode, checklistCategory, currentChecklistMaster } = options;

    const { t } = useI18n();
    const config = inject('config');

    const checklistMasters = ref([]);
    const isLoading = ref(false);
    const error = ref(null);

    const checklistMasterQuestions = ref([]);
    const currentChecklistId = ref(null);
    const checklistAnswers = ref([]);

    const executeRequest = async (requestFunc) => {
        isLoading.value = true;
        error.value = null;
        try {
            await requestFunc();
        } catch (err) {
            error.value = err.message || 'An error occurred.';
            console.error(err);
        } finally {
            isLoading.value = false;
        }
    };

    const fetchChecklistMasters = async () => {
        await executeRequest(async () => {
            let url = checklistCategory?.value
                ? `${config.backendHost}/api/checklist/master/list/category/${checklistCategory.value}`
                : `${config.backendHost}/api/checklist/master/list`;
            const response = await axios.get(url);
            checklistMasters.value = response.data?.data && Array.isArray(response.data.data) ? response.data.data : [];
        });
    };

    const createNewChecklistMaster = async (name, category) => {
        await executeRequest(async () => {
            const response = await axios.post(`${config.backendHost}/api/checklist/master/new`, { name, category });
            if (response.data?.success) {
                await fetchChecklistMasters();
            }
        });
    };

    const updateChecklistMaster = async (master) => {
        await executeRequest(async () => {
            await axios.post(`${config.backendHost}/api/checklist/master/update/${master.id}`, {
                name: master.name,
                category: master.category
            });
        });
    };

    const deleteChecklistMaster = async (master) => {
        if (window.confirm(t('message.confirm_delete_checklist', { name: master.name }))) {
            await executeRequest(async () => {
                const response = await axios.get(`${config.backendHost}/api/checklist/master/delete/${master.id}`);
                if (response.data?.success) {
                    await fetchChecklistMasters();
                    if (currentChecklistMaster.value?.id === master.id) {
                        currentChecklistMaster.value = null;
                    }
                }
            });
        }
    };

    const fetchChecklistMasterQuestions = async () => {
        if (!currentChecklistMaster.value?.id) return;
        await executeRequest(async () => {
            const response = await axios.get(`${config.backendHost}/api/checklist/master/${currentChecklistMaster.value.id}/questions`);
            checklistMasterQuestions.value = response.data?.data && Array.isArray(response.data.data) ? response.data.data : [];
        });
    };

    const saveChecklistMasterQuestions = async () => {
        await executeRequest(async () => {
            let order = 0;
            for (const question of checklistMasterQuestions.value) {
                question.order = order++;
                if (question.text.trim() !== '') {
                    if (question.id !== undefined) {
                        await axios.post(`${config.backendHost}/api/checklist/question/update/${question.id}`, question);
                    } else {
                        await axios.post(`${config.backendHost}/api/checklist/question/new`, {
                            ...question,
                            master_id: currentChecklistMaster.value.id
                        });
                    }
                } else if (question.id !== undefined) {
                    await axios.get(`${config.backendHost}/api/checklist/question/delete/${question.id}`);
                }
            }
            await fetchChecklistMasterQuestions();
        });
    };

    const createNewChecklist = async () => {
        if (!currentChecklistMaster.value?.id) return;
        await executeRequest(async () => {
            await axios.get(`${config.backendHost}/api/checklist/new_from_master/${currentChecklistMaster.value.id}`);
            await fetchLatestChecklist();
        });
    };

    const fetchLatestChecklist = async () => {
        if (!currentChecklistMaster.value?.id) return;
        await executeRequest(async () => {
            const response = await axios.get(`${config.backendHost}/api/checklist/latest/${currentChecklistMaster.value.id}`);
            currentChecklistId.value = response.data?.success ? response.data.data.id : null;
        });
    };

    const closeChecklist = async () => {
        if (!currentChecklistId.value) {
            error.value = 'No checklist selected to close.';
            return false;
        }
        let success = false;
        await executeRequest(async () => {
            const response = await axios.get(`${config.backendHost}/api/checklist/close/${currentChecklistId.value}`);
            if (response.data?.success) {
                await fetchLatestChecklist();
                success = true;
            }
        });
        return success;
    };

    const fetchChecklistAnswers = async () => {
        if (!currentChecklistId.value) return;
        await executeRequest(async () => {
            const response = await axios.get(`${config.backendHost}/api/checklist/answers/${currentChecklistId.value}`);
            checklistAnswers.value = response.data?.data && Array.isArray(response.data.data) ? response.data.data : [];
        });
    };

    const updateChecklistAnswer = async (answer, choice) => {
        answer.choice = answer.choice !== choice ? choice : null;
        await executeRequest(async () => {
            const response = await axios.post(`${config.backendHost}/api/checklist/answer/update/${answer.id}`, {
                choice: answer.choice,
                checklist_id: answer.checklist_id,
                question_text: answer.question_text
            });
            if (response.data?.success) {
                await fetchChecklistAnswers();
            }
        });
    };

    watch(currentChecklistMaster, (newMaster) => {
        if (mode.value === 'edit') {
            if (newMaster?.id) {
                fetchChecklistMasterQuestions();
            } else {
                checklistMasterQuestions.value = [];
            }
        } else {
            if (newMaster?.id) {
                fetchLatestChecklist();
            } else {
                currentChecklistId.value = null;
            }
        }
    });

    watch(currentChecklistId, (newId) => {
        if (newId) {
            fetchChecklistAnswers();
        } else {
            checklistAnswers.value = [];
        }
    });

    return {
        // State
        checklistMasters,
        isLoading,
        error,
        checklistMasterQuestions,
        checklistAnswers,
        currentChecklistId,

        // Methods
        fetchChecklistMasters,
        createNewChecklistMaster,
        updateChecklistMaster,
        deleteChecklistMaster,
        fetchChecklistMasterQuestions,
        saveChecklistMasterQuestions,
        createNewChecklist,
        closeChecklist,
        updateChecklistAnswer,
    };
}
