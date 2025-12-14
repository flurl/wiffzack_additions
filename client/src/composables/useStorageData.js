// useStorageData.js
import { ref, onMounted, inject, watch } from 'vue';
import axios from 'axios';

export function useStorageData(sourceStorageId, destinationStorageId, transferStorageId, mode) {
    const config = inject('config');
    // Initialize internal storage refs with the .value of the passed-in refs
    const sourceStorage = ref({ id: sourceStorageId.value, name: null });
    const destinationStorage = ref({ id: destinationStorageId.value, name: null });
    const transferStorage = ref({ id: transferStorageId.value, name: null });
    const articles = ref({});
    const articleGroups = ref([]);
    const destStorageArticles = ref({});
    const transferStorageArticles = ref({});
    const activeArticleGroup = ref(null);
    const selectedArticles = ref({});
    const loading = ref(false);
    const error = ref(null);

    const getStorageName = async (storage, storageId) => {
        try {
            const response = await axios.get(`${config.backendHost}/api/get_storage_name/${storageId}`);
            storage.value.name = response.data.data[0][0];
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
            articleGroups.value = response.data.data;
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
        destStorageArticles.value = {}; // Clear previous articles
        try {
            const response = await axios.get(`${config.backendHost}/api/get_articles_in_storage/${destinationStorage.value.id}`);
            response.data.data.forEach(art => {
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
        if (mode === "stock") {
            url = url + "?show_not_in_stock=1";
        }

        try {
            const response = await axios.get(url);
            articles.value = {};
            response.data.data.forEach(art => {
                articles.value[art[0]] = { id: art[0], name: art[1], amount: art[2] };
            });
        } catch (err) {
            error.value = err;
        } finally {
            loading.value = false;
        }
    };

    const getArticlesInTransferStorage = async () => {
        loading.value = true;
        error.value = null;

        let url = "";
        url = `${config.backendHost}/api/get_articles_in_storage/${transferStorage.value.id}`;

        try {
            const response = await axios.get(url);
            transferStorageArticles.value = {};
            response.data.data.forEach(art => {
                transferStorageArticles.value[art[0]] = { id: art[0], name: art[1], amount: art[2] };
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

    const setArticleAmountInStorage = async (storageId, article, amount) => {
        loading.value = true;
        error.value = null;
        const url = `${config.backendHost}/api/set_article_amount_in_storage/${storageId}`;
        const data = { ...article, amount: amount };

        try {
            const response = await axios.post(url, data);
            if (response.data.success) {
                console.log("Article amount update succeeded");
                return true;
            } else {
                console.log("Article amount update did not succeed");
                error.value = response.data.message || "Unknown error";
                return false;
            }
        } catch (err) {
            error.value = err;
            return false;
        } finally {
            loading.value = false;
        }
    };

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

    const emptyTransferStorage = async () => {
        loading.value = true;
        error.value = null;
        let url = "";
        url = `${config.backendHost}/api/empty_storage/${transferStorage.value.id}`

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

    // Watch for changes in the passed-in sourceStorageId reference
    watch(sourceStorageId, async (newId) => {
        sourceStorage.value.id = newId; // Update internal id
        await getStorageName(sourceStorage, newId);
        await getArticleGroups(); // Re-fetch article groups as they might depend on the source
        await getArticlesInSourceStorage(); // Re-fetch articles for the new source
    });

    // Watch for changes in the passed-in destinationStorageId reference
    watch(destinationStorageId, async (newId) => {
        destinationStorage.value.id = newId; // Update internal id
        await getStorageName(destinationStorage, newId);
        await getArticlesInDestinationStorage(); // Re-fetch articles/details for the new destination
    });

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
        transferStorageArticles,
        activeArticleGroup,
        selectedArticles,
        // getArticleGroups,
        getArticlesInDestinationStorage,
        getArticlesInSourceStorage,
        getArticlesInTransferStorage,
        putIntoStorage,
        setArticleAmountInStorage,
        setInitInventory,
        emptyTransferStorage,
        loading,
        error
    };
}
