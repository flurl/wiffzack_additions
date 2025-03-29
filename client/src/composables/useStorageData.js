// useStorageData.js
import { ref, onMounted, inject } from 'vue';
import axios from 'axios';

export function useStorageData(sourceStorageId, destinationStorageId, mode) {
    const config = inject('config');
    const sourceStorage = ref({ id: sourceStorageId, name: null });
    const destinationStorage = ref({ id: destinationStorageId, name: null });
    const articles = ref({});
    const articleGroups = ref([]);
    const destStorageArticles = ref({});
    const activeArticleGroup = ref(null);
    const selectedArticles = ref({});
    const loading = ref(false);
    const error = ref(null);

    const getStorageName = async (storage, storageId) => {
        try {
            const response = await axios.get(`${config.backendHost}/api/get_storage_name/${storageId}`);
            storage.value.name = response.data[0][0];
        } catch (err) {
            error.value = err;
        }
    };

    const getArticleGroups = async () => {
        loading.value = true;
        error.value = null;
        let sourceStorageURL = `${config.backendHost}/api/storage_article_groups`;
        if (mode === "distribute" || mode === "transfer") {
            sourceStorageURL += `/${sourceStorage.value.id}`;
        }
        try {
            const response = await axios.get(sourceStorageURL);
            articleGroups.value = response.data;
            activeArticleGroup.value = articleGroups.value[0];
        } catch (err) {
            error.value = err;
        } finally {
            loading.value = false;
        }
    };

    const getArticlesInDestinationStorage = async () => {
        loading.value = true;
        error.value = null;
        try {
            const response = await axios.get(`${config.backendHost}/api/get_articles_in_storage/${destinationStorage.value.id}`);
            response.data.forEach(art => {
                destStorageArticles.value[art[0]] = { id: art[0], name: art[1], amount: art[2] };
            });
        } catch (err) {
            error.value = err;
        } finally {
            loading.value = false;
        }
    };

    const getArticlesInSourceStorage = async () => {
        if (!activeArticleGroup.value) {
            articles.value = {};
            return;
        }
        loading.value = true;
        error.value = null;
        let url = "";
        if (mode === "request") {
            url = `${config.backendHost}/api/storage_article_by_group/${activeArticleGroup.value[0]}`;
        } else if (mode === "distribute" || mode === "transfer" || mode === "stock") {
            url = `${config.backendHost}/api/get_articles_in_storage/${sourceStorage.value.id}/article_group/${activeArticleGroup.value[0]}`;
        } 
        try {
            const response = await axios.get(url);
            articles.value = {};
            response.data.forEach(art => {
                articles.value[art[0]] = { id: art[0], name: art[1], amount: art[2] };
            });
        } catch (err) {
            error.value = err;
        } finally {
            loading.value = false;
        }
    };

    const putIntoStorage = async () => {
        loading.value = true;
        error.value = null;
        let url = `${config.backendHost}/api/update_storage`
        if (mode === "request") {
            url += `/to/${destinationStorage.value.id}?method=absolute`;
        } else if (mode === "distribute" ||
            mode === "transfer" ||
            mode === "stock") {
            url += `/from/${sourceStorage.value.id}/to/${destinationStorage.value.id}?method=relative`;
        }
    
        let data = selectedArticles.value

        try {
            const response = await axios.post(url, data);
            if (response.data.success) {
                console.log("Storage update succeded")
                selectedArticles.value = {};
                loading.value = false;
                return true;
            } else {
                console.log("Storage update did not succeded")
                loading.value = false;
                return false;
            }
        } catch (err) {
            error.value = err;
        } finally {
            loading.value = false;
        }
    }

    const setInitInventory = async () => {
        loading.value = true;
        error.value = null;
        let url = "";
        url = `${config.backendHost}/api/set_init_inventory/storage/${sourceStorage.value.id}`;

        try {
            const response = await axios.get(url);
            console.log(response);
        } catch (err) {
            console.log(err);
            error.value = err;
        } finally {
            loading.value = false;
        }

        if (error.value) {
            return false;
        } else {
            return true;
        }
    }

    onMounted(async () => {
        if (sourceStorage.value.id) {
            await getStorageName(sourceStorage, sourceStorage.value.id);
        }
        if (destinationStorage.value.id) {
            await getStorageName(destinationStorage, destinationStorage.value.id);
        }
        await getArticleGroups();
        await getArticlesInDestinationStorage();
        await getArticlesInSourceStorage();
    });

    return {
        sourceStorage,
        destinationStorage,
        articles,
        articleGroups,
        destStorageArticles,
        activeArticleGroup,
        selectedArticles,
        // getArticleGroups,
        getArticlesInDestinationStorage,
        getArticlesInSourceStorage,
        putIntoStorage,
        setInitInventory,
        loading,
        error
    };
}
