<script setup>
import { ref, watch, getCurrentInstance, computed, onMounted, onUpdated } from 'vue'
import { useI18n } from 'vue-i18n'
import ArticleList from './ArticleList.vue'
import ModalDialog from './ModalDialog.vue'
import ToggleSwitch from './ToggleSwitch.vue'
import QuitButton from './QuitButton.vue'
import { useStorageData } from '../composables/useStorageData';
import { useColor } from '../utils/useColor';
const { stringToColor, colorIsDarkSimple } = useColor();
import dragscroll from 'dragscroll';


const { t } = useI18n()

// get the current instance
const instance = getCurrentInstance();
// get the global properties.
const $terminalConfig = instance.appContext.config.globalProperties.$terminalConfig;
const $destTerminalConfig = instance.appContext.config.globalProperties.$destTerminalConfig;

const props = defineProps({
    // from router
    mode: String
});

const SABSMode = ref(false);


const sourceStorageId = ref(null);
const destinationStorageId = ref(null);
const transferStorageId = ref(null);

if (props.mode === "request") {
    sourceStorageId.value = null;
    destinationStorageId.value = $terminalConfig.request_storage_id;
} else if (props.mode === "distribute") {
    sourceStorageId.value = $destTerminalConfig.request_storage_id;
    destinationStorageId.value = $destTerminalConfig.transfer_storage_id;
} else if (props.mode === "transfer") {
    sourceStorageId.value = $terminalConfig.transfer_storage_id;
    destinationStorageId.value = $terminalConfig.storage_id;
} else if (props.mode === "stock") {
    sourceStorageId.value = $terminalConfig.storage_id;
    destinationStorageId.value = $terminalConfig.transfer_storage_id;
}
transferStorageId.value = $terminalConfig.transfer_storage_id;

// check if the source and/or destination storage is overwritten manually
const urlParams = new URLSearchParams(window.location.search);
sourceStorageId.value = urlParams.has('sourceStorageId') ? urlParams.get('sourceStorageId') : sourceStorageId.value;
destinationStorageId.value = urlParams.has('destinationStorageId') ? urlParams.get('destinationStorageId') : destinationStorageId.value;


const {
    sourceStorage,
    destinationStorage,
    articles,
    articleGroups,
    destStorageArticles,
    transferStorageArticles,
    activeArticleGroup,
    selectedArticles,
    getArticlesInDestinationStorage,
    getArticlesInSourceStorage,
    getArticlesInTransferStorage,
    putIntoStorage,
    setArticleAmountInStorage,
    setInitInventory,
    emptyTransferStorage,
    loading,
    error
} = useStorageData(sourceStorageId, destinationStorageId, transferStorageId, props.mode);
watch(activeArticleGroup, getArticlesInSourceStorage);


const _amount = ref(1);
if (props.mode === "distribute" || props.mode === "transfer") {
    // null is the value for amount equals all articles in source storage
    _amount.value = null;
}
const increment = () => {
    _amount.value++;
}
const decrement = () => {
    _amount.value--;
}
const amount = computed(() => {
    if (_amount.value === null) {
        return null;
    }
    if (_amount.value < 1) {
        _amount.value = 1;
    }
    return _amount.value;
});


const swapStorage = () => {
    if (sourceStorageId.value === null || destinationStorageId.value === null) {
        showModal({
            title: t('message.storage_swap_not_possible'),
            buttons: { ok: true, cancel: false },
            type: 'info'
        })
        return;
    }
    const tmp = sourceStorageId.value;
    sourceStorageId.value = destinationStorageId.value;
    destinationStorageId.value = tmp;
    // These calls might become redundant if useStorageData internally watches the ID refs
    // and re-fetches data automatically. If not, they are an attempt to manually refresh.
    getArticlesInSourceStorage();
    getArticlesInDestinationStorage();
}


const destDisplayArticles = computed(() => {

    const displayArticles = JSON.parse(JSON.stringify(destStorageArticles.value)); // Start with a copy of the first object

    // If showDestInventory is false, only show articles that are in selectedArticles
    if (!showDestInventory.value) {
        for (const id in displayArticles) {
            if (!selectedArticles.value[id]) {
                // remove the entry for id from displayArticles
                delete displayArticles[id];
            }
        }
    }

    // Iterate over the keys in the second object
    for (const id in selectedArticles.value) {
        if (!displayArticles[id]) {
            // If the ID is unique to the second object, add it to the result
            displayArticles[id] = { ...selectedArticles.value[id], amount: 0 };
        }
    }
    return displayArticles;
});


const addArticleToSelected = (article) => {
    let a = amount.value;
    // if no amount is set => set amount to all
    if (a === null) {
        a = article.amount;
    }
    if (selectedArticles.value[article.id]) {
        selectedArticles.value[article.id].amount += a;
    } else {
        selectedArticles.value[article.id] = { ...article, amount: a };
    }
    article.amount -= a;
};
const removeArticleFromSelected = (article) => {
    // The article object passed here is from the destDisplayArticles list.
    // It might be from selectedArticles or destStorageArticles.
    const articleId = article.id;
    const selectedAmount = selectedArticles.value[articleId]?.amount || 0;

    const justRemoveSelection = () => {
        if (articles.value[articleId]) {
            articles.value[articleId].amount += selectedAmount;
        }
        if (selectedArticles.value[articleId]) {
            delete selectedArticles.value[articleId];
        }
    };

    // If the article is in destStorageArticles (meaning it's already in the destination storage),
    // we need to ask the user if they want to remove it from the actual storage or just from the current selection.
    if (props.mode === 'request' && showDestInventory.value && !selectedArticles.value[articleId]) {
        showModal({
            title: t('message.remove_article_title'),
            body: t('message.remove_article_body', { articleName: article.name }),
            type: 'question',
            buttons: { ok: false, cancel: false, yes: true, no: true },
            noCallback: justRemoveSelection,
            yesCallback: removeAllFromDestination,
        });

        async function removeAllFromDestination() {
            showModal({ title: t('message.updating'), buttons: {} });
            const success = await setArticleAmountInStorage(destinationStorageId.value, article, 0);
            if (success) {
                // Update local state
                if (destStorageArticles.value[articleId]) {
                    destStorageArticles.value[articleId].amount = 0;
                }
                justRemoveSelection(); // Also remove it from the current selection
                modalConf.value.show = false; // Close the "updating" modal
            } else {
                showModal({ title: t('message.error'), body: error.value, type: 'error', buttons: { ok: true } });
            }
        }

    } else {
        justRemoveSelection();
    }
};


const modalConf = ref({
    buttons: {
        ok: true,
        cancel: true
    },
    title: "",
    show: false,
    OKCallback: null,
    cancelCallback: null,
    yesCallback: null,
    noCallback: null,
    body: "",
    rawHTML: false,
    type: "info",
});
/**
 * Displays a modal dialog with the given configuration.
 *
 * @param {object} [config={}] - The configuration object for the modal.
 * @param {string} [config.title=""] - The title of the modal.
 * @param {string|object} [config.body=""] - The body content. Can be a string for plain text,
 *                                       or an object { body: string, rawHTML: boolean } for HTML content.
 * @param {object} [config.buttons={ok: true, cancel: true}] - Specifies which buttons to show.
 * @param {boolean} [config.buttons.ok=true] - Show OK button.
 * @param {boolean} [config.buttons.cancel=true] - Show Cancel button.
 * @param {function} [config.OKCallback=null] - Callback for the OK button.
 * @param {function} [config.cancelCallback=null] - Callback for the Cancel button.
 * @param {string} [config.type="info"] - The type of the modal (e.g., 'info', 'success', 'error', 'question').
 */
const showModal = (config = {}) => {
    // Default values
    const defaults = {
        title: "",
        body: "", // string or { body: string, rawHTML: boolean }
        buttons: { ok: true, cancel: true },
        OKCallback: null,
        cancelCallback: null,
        type: "info",
    };

    // Merge provided config with defaults
    const mergedConfig = {
        ...defaults,
        ...config,
        buttons: { // Ensure 'buttons' is always an object with 'ok' and 'cancel'
            ...defaults.buttons,
            ...(config.buttons || {}),
        },
    };

    modalConf.value.title = mergedConfig.title;

    // when rawHTML is set, the modal's body will not be cleaned
    if (typeof mergedConfig.body === 'string') {
        modalConf.value.body = mergedConfig.body;
        modalConf.value.rawHTML = false;
    } else if (typeof mergedConfig.body === 'object' && mergedConfig.body !== null && 'body' in mergedConfig.body && 'rawHTML' in mergedConfig.body) {
        modalConf.value.body = mergedConfig.body.body;
        modalConf.value.rawHTML = mergedConfig.body.rawHTML;
    } else {
        modalConf.value.body = ""; // Default to empty string if body is not string or expected object
        modalConf.value.rawHTML = false;
    }

    modalConf.value.buttons = mergedConfig.buttons;
    if (mergedConfig.buttons.ok) {
        modalConf.value.OKCallback = () => {
            modalConf.value.show = false;
            if (mergedConfig.OKCallback) {
                mergedConfig.OKCallback();
            }
        };
    } else {
        modalConf.value.OKCallback = null;
    }

    if (mergedConfig.buttons.cancel) {
        modalConf.value.cancelCallback = () => {
            modalConf.value.show = false;
            if (mergedConfig.cancelCallback) {
                mergedConfig.cancelCallback();
            }
        };
    } else {
        modalConf.value.cancelCallback = null;
    }

    if (mergedConfig.buttons.yes) {
        modalConf.value.yesCallback = () => {
            modalConf.value.show = false;
            if (mergedConfig.yesCallback) {
                mergedConfig.yesCallback();
            }
        };
    } else {
        modalConf.value.yesCallback = null;
    }

    if (mergedConfig.buttons.no) {
        modalConf.value.noCallback = () => {
            modalConf.value.show = false;
            if (mergedConfig.noCallback) {
                mergedConfig.noCallback();
            }
        };
    } else {
        modalConf.value.noCallback = null;
    }

    modalConf.value.type = mergedConfig.type;
    modalConf.value.show = true;
}


// sets the initial inventory for the current source storage
const onInitClicked = () => {
    showModal({
        title: t('message.init_stock'),
        type: 'question',
        OKCallback: async () => {
            showModal({
                title: t('message.init_stock'),
                buttons: { ok: false, cancel: false }
            });
            if (await setInitInventory()) {

                // check if there are any articles in the transfer storage
                await getArticlesInTransferStorage();
                let articlesDetailHtml = "";
                const articlesToDisplay = [];

                // Ensure transferStorageArticles.value is an object and has keys
                if (transferStorageArticles.value && Object.keys(transferStorageArticles.value).length > 0) {
                    for (const articleId in transferStorageArticles.value) {
                        const article = transferStorageArticles.value[articleId];
                        // Only list articles with a positive amount
                        if (article.amount > 0.001) { // Using a small epsilon for float comparison
                            articlesToDisplay.push({
                                // Using toFixed(2) for amount, similar to other UI parts
                                amount: article.amount.toFixed(2),
                                name: article.name
                            });
                        }
                    }
                }

                // if there were any articles found in the transfer storage, 
                // ask the user if they want to remove them
                if (articlesToDisplay.length > 0) {
                    // You'll want to add these i18n keys to your translation files
                    articlesDetailHtml = "<br><br>" + t('message.articles_in_transfer_storage_list_header') + "<table>";
                    articlesToDisplay.forEach(article => {
                        articlesDetailHtml += `<tr><td style="padding-right: 5px;">${article.amount}</td><td style="padding-right: 5px;">x</td><td>${article.name}</td></tr>`;
                    });
                    articlesDetailHtml += "</table>";
                    showModal({
                        title: t('message.init_stock_success'),
                        body: { body: t('message.transfer_storage_not_empty') + articlesDetailHtml, rawHTML: true },
                        type: 'question',
                        OKCallback: async () => {
                            await emptyTransferStorage();
                            showModal({
                                title: t('message.transfer_storage_empty_success'),
                                buttons: { ok: true, cancel: false },
                                type: 'success',
                                OKCallback: async () => {
                                    window.location.reload();
                                }
                            });
                        },
                        cancelCallback: async () => {
                            window.location.reload();
                        }
                    });
                } else {
                    showModal({
                        title: t('message.init_stock_success'),
                        buttons: { ok: true, cancel: false },
                        type: 'success',
                        OKCallback: async () => {
                            window.location.reload();
                        }
                    });
                }

            } else {
                showModal({
                    title: t('message.init_stock_error'),
                    body: error.value,
                    buttons: { ok: true, cancel: false },
                    type: 'error'
                });
            };
        }
    });
}


// transfer the selected articles (if any) to the destination storage
// and close the window after the modal is closed
const onOKClicked = () => {
    let title = "";

    if (props.mode === "request") {
        title = t('message.request_articles')
    } else if (props.mode === "distribute") {
        title = t('message.distribute_articles');
    } else if (props.mode === "transfer") {
        title = t('message.transfer_articles')
    } else if (props.mode === "stock") {
        title = t('message.transfer_articles')
    }

    let body = "";
    body += "<table>";
    for (const articleId in selectedArticles.value) {
        const article = selectedArticles.value[articleId];
        if (article.amount > 0) {
            body += "<tr>";
            body += `<td>${article.amount}</td>`;
            body += `<td>${article.name}</td>`;
            body += "</tr>";
        }
    }
    body += "</table>";

    showModal({
        title: title,
        body: { body: body, rawHTML: true },
        type: 'question',
        OKCallback: async () => {
            showModal({
                title: title,
                buttons: { ok: false, cancel: false }
            });
            exit(await putIntoStorage());
        }
    });
}


const showDestInventory = ref(props.mode === 'request');
const onShowDestInventorySwitchToggled = () => {
    showDestInventory.value = !showDestInventory.value;;
}
watch(showDestInventory, getArticlesInDestinationStorage);


const exit = (success) => {
    let title = success ? t('message.success') : t('message.error');
    let body = "";
    let buttons = { ok: true, cancel: false };
    let cb = () => {
        try {
            console.log("Closing window now");
            window.close();
        } catch (e) {
            alert("Close window now");
            window.location.reload();
        }
    }
    showModal({
        title: title,
        body: body,
        buttons: buttons,
        OKCallback: cb,
        type: success ? 'success' : 'error'
    });
}

onMounted(() => {
    document.querySelectorAll('.article-list-container')[0].classList.add('dragscroll');
    dragscroll.reset();
});

onUpdated(() => {
    dragscroll.reset();
});


</script>

<template>
    <div class="wrapper">
        <ModalDialog :title="modalConf.title" :show="modalConf.show" :buttons="modalConf.buttons" :type="modalConf.type"
            @ok="modalConf.OKCallback" @cancel="modalConf.cancelCallback" @yes="modalConf.yesCallback"
            @no="modalConf.noCallback">
            <p v-if="modalConf.rawHTML === false">{{ modalConf.body }}</p>
            <span v-else v-html="modalConf.body"></span>
        </ModalDialog>

        <header class="header">
            <h1 class="left">{{ sourceStorage.name }} -> {{ destinationStorage.name }}</h1>
            <a class="button left" @click="swapStorage">⇄</a>
            <button class="button right" v-if="props.mode === 'stock'" @click="onInitClicked">Init</button>
            <QuitButton />
        </header>

        <div class="amount-selector">
            <button class="article-amount" @click="decrement">-</button>
            <input class="article-amount" type="text" :value="amount ? amount : $t('message.all')">
            <button class="article-amount" @click="increment">+</button>
            <button class="article-amount" :class="[_amount === 1 ? 'active' : '']" @click="_amount = 1">x1</button>
            <button class="article-amount" :class="[_amount === 6 ? 'active' : '']" @click="_amount = 6">x6</button>
            <button class="article-amount" :class="[_amount === 10 ? 'active' : '']" @click="_amount = 10">x10</button>
            <button class="article-amount" :class="[_amount === 12 ? 'active' : '']" @click="_amount = 12">x12</button>
            <button class="article-amount" :class="[_amount === 24 ? 'active' : '']" @click="_amount = 24">x24</button>
            <button class="article-amount" :class="[_amount === null ? 'active' : '']"
                @click="_amount = null">Alle</button>
            <button class="confirm" @click="onOKClicked">OK</button>
        </div>

        <div class="three-columns-grid">
            <div class="">
                <button class="article-group" v-for="group in articleGroups" @click="activeArticleGroup = group"
                    :style="{ backgroundColor: stringToColor(group[1]).bg, color: stringToColor(group[1]).fg }">{{
                        group[1]
                    }}</button>
            </div>

            <div class="">
                <template v-for="article in articles">
                    <div class="article-button">
                        <button class="article" @click="addArticleToSelected(article)"
                            :style="{ backgroundColor: stringToColor(activeArticleGroup[1]).bg, color: stringToColor(activeArticleGroup[1]).fg }">
                            {{ article.name }}
                        </button>
                        <p :class="[article.amount < 0 ? 'negative' : 'positive']">{{ Math.abs(article.amount) > 0.001 ?
                            article.amount.toFixed(2) : '-' }}</p>
                    </div>
                </template>
            </div>

            <div class="right-col" :class="{ 'SABS-mode': SABSMode }">
                <ArticleList :articles="destDisplayArticles" :article-updates="selectedArticles"
                    :enable-removal-from-storage="mode === 'request'" @article-removed="removeArticleFromSelected">
                </ArticleList>
                <div class="switch-wrapper">
                    <div class="dest-storage-switch">
                        <ToggleSwitch :checked="showDestInventory" label-position="bottom"
                            @toggled="onShowDestInventorySwitchToggled">
                            {{ t('message.show_dest_inventory_abbreviation') }}
                        </ToggleSwitch>
                    </div>
                    <div class="SABS-mode-switch">
                        <ToggleSwitch :checked="SABSMode" label-position="bottom" @toggled="SABSMode = !SABSMode">
                            SABS
                        </ToggleSwitch>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<style lang="scss" scoped>
.wrapper {
    height: 100vh;
    position: relative;
    display: flex;
    flex-direction: column;
}

.header {
    display: flex;
    /* justify-content: space-between; */
    align-items: center;

    .right {
        margin-left: auto;
    }

    h1 {
        font-size: 140%
    }
}

.amount-selector {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.three-columns-grid {
    overflow: hidden;
    height: 100%;
}

.three-columns-grid>* {
    height: 100%;
    overflow: scroll;
}

div.article-button {
    display: inline-block;

    p {
        text-align: center;

        &.negative {
            color: red;
            font-weight: bold;
        }

        &.positive {
            color: green;
        }
    }
}

button.article,
button.article-group {
    width: 5em;
    white-space: normal;
    word-break: break-all;
    height: 3lh;
    padding: 0 0.5em;
    overflow: hidden;
    vertical-align: top;
    /* needed to align buttons when text overflows */
}

input.article-amount {
    max-width: 2em;
    font-size: 1.8em;
    padding: 0.2em 15px;
}

button.article-amount {
    width: 3em;
    padding: 0.4em 0;
    font-size: 1.4em;
}

button.confirm {
    padding-top: 0.7em;
    padding-bottom: 0.7em;
    margin-left: auto;
}


.right-col:deep() .article-list-container {
    height: calc(100% - 5em);
    width: 100%;
    overflow: scroll;
    font-weight: bold;

    table {
        tr:nth-child(odd) {
            background-color: color.scale($light-button-background, $lightness: +30%);
            ;
        }

        .name {
            word-break: break-all;
        }
    }
}

.switch-wrapper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
}

.SABS-mode {
    font-size: 200%;
}
</style>
