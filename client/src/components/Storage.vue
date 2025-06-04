<script setup>
import { ref, watch, getCurrentInstance, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import ArticleList from './ArticleList.vue'
import ModalDialog from './ModalDialog.vue'
import ToggleSwitch from './ToggleSwitch.vue'
import QuitButton from './QuitButton.vue'
import { useStorageData } from '../composables/useStorageData';
import { useColor } from '../utils/useColor';
const { stringToColor, colorIsDarkSimple } = useColor();


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
    const tmp = sourceStorageId.value;
    sourceStorageId.value = destinationStorageId.value;
    destinationStorageId.value = tmp;
    // These calls might become redundant if useStorageData internally watches the ID refs
    // and re-fetches data automatically. If not, they are an attempt to manually refresh.
    getArticlesInSourceStorage();
    getArticlesInDestinationStorage();
}


const destDisplayArticles = computed(() => {
    if (!showDestInventory.value) {
        return selectedArticles.value;
    }

    const displayArticles = JSON.parse(JSON.stringify(destStorageArticles.value)); // Start with a copy of the first object
    // Iterate over the keys in the second object
    for (const id in selectedArticles.value) {
        if (displayArticles[id]) {
            // If the ID exists in both objects, sum the amounts
            displayArticles[id].amount += selectedArticles.value[id].amount;
        } else {
            // If the ID is unique to the second object, add it to the result
            displayArticles[id] = { ...selectedArticles.value[id] };
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
    articles.value[article.id].amount += selectedArticles.value[article.id].amount;
    selectedArticles.value[article.id].amount = 0;
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
    body: "",
    rawHTML: false,
    type: "info",
});
/**
 * Displays a modal dialog with the given title, body, and buttons.
 *
 * @param {string} title - The title of the modal.
 * @param {string|object} body - The body content of the modal. Can be a string or an object with 'body' and 'rawHTML' properties.
 * @param {object} buttons - An object specifying which buttons to show (e.g., { ok: true, cancel: true }).
 * @param {function} OKCallback - The callback function to execute when the OK button is clicked.
 * @param {function} cancelCallback - The callback function to execute when the Cancel button is clicked.
 */
const showModal = (title, body, buttons, OKCallback, cancelCallback, type = "info") => {
    modalConf.value.title = title;

    // when rawHTML is set, the modal's body will not be cleaned
    if (typeof body === 'string') {
        modalConf.value.body = body;
        modalConf.value.rawHTML = false;
    } else if (typeof body === 'object' && body.hasOwnProperty('body') && body.hasOwnProperty('rawHTML')) {
        modalConf.value.body = body.body;
        modalConf.value.rawHTML = body.rawHTML;
    } else {
        modalConf.value.body = '';
    }

    modalConf.value.buttons = buttons;
    if (buttons.ok) {
        modalConf.value.OKCallback = () => {
            modalConf.value.show = false;
            if (OKCallback !== undefined) {
                OKCallback();
            }
        }
    }

    if (buttons.cancel) {
        modalConf.value.cancelCallback = () => {
            modalConf.value.show = false;
            if (cancelCallback !== undefined) {
                cancelCallback();
            }
        }
    }

    modalConf.value.type = type;

    modalConf.value.show = true;
}


// sets the initial inventory for the current source storage
const onInitClicked = () => {
    showModal(t('message.init_stock'),
        "",
        { ok: true, cancel: true },
        async () => {
            showModal(t('message.init_stock'),
                "",
                { ok: false, cancel: false },
            )
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
                    showModal(t('message.init_stock_success'),
                        { body: t('message.transfer_storage_not_empty') + articlesDetailHtml, rawHTML: true },
                        { ok: true, cancel: true },
                        async () => {
                            await emptyTransferStorage();
                            showModal(t('message.transfer_storage_empty_success'),
                                "",
                                { ok: true, cancel: false },
                                async () => {
                                    window.location.reload();
                                },
                                null,
                                'success'
                            );
                        },
                        async () => {
                            window.location.reload();
                        },
                        'question'
                    );
                } else {
                    showModal(t('message.init_stock_success'),
                        '',
                        { ok: true, cancel: false },
                        async () => {
                            window.location.reload();
                        },
                        null,
                        'success'
                    );
                }

            } else {
                showModal(t('message.init_stock_error'),
                    error.value,
                    { ok: true, cancel: false },
                    null, null, 'error'
                );
            };
        },
        null,
        'question');
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

    showModal(title,
        { body: body, rawHTML: true },
        { ok: true, cancel: true },
        async () => {
            showModal(title,
                "",
                { ok: false, cancel: false },
            )
            exit(await putIntoStorage());
        },
        null,
        'question'
    );
}


const showDestInventory = ref(false);
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
    showModal(title, body, buttons, cb, null, success ? 'success' : 'error');
}

</script>

<template>
    <div class="wrapper">
        <ModalDialog :title="modalConf.title" :show="modalConf.show" :buttons="modalConf.buttons" :type="modalConf.type"
            @ok="modalConf.OKCallback" @cancel="modalConf.cancelCallback">
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

            <div class="right-col">
                <ArticleList :articles="destDisplayArticles" @article-removed="removeArticleFromSelected"></ArticleList>
                <div class="dest-storage-switch">
                    <ToggleSwitch :checked="showDestInventory" @toggled="onShowDestInventorySwitchToggled">
                    </ToggleSwitch>
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
    font-size: 2em;
}

button.article-amount {
    width: 3em;
    padding: 0.5em 0;
    font-size: 1.5em;
}

button.confirm {
    margin-left: auto;
}


.right-col:deep() .article-list-container {
    height: calc(100% - 4rem);
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

.dest-storage-switch {
    padding: 0.5rem;
}
</style>
