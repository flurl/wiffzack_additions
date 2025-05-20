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


let sourceStorageId = null;
let destinationStorageId = null;
if (props.mode === "request") {
    sourceStorageId = null;
    destinationStorageId = $terminalConfig.request_storage_id;
} else if (props.mode === "distribute") {
    sourceStorageId = $destTerminalConfig.request_storage_id;
    destinationStorageId = $destTerminalConfig.transfer_storage_id;
} else if (props.mode === "transfer") {
    sourceStorageId = $terminalConfig.transfer_storage_id;
    destinationStorageId = $terminalConfig.storage_id;
} else if (props.mode === "stock") {
    sourceStorageId = $terminalConfig.storage_id;
    destinationStorageId = $terminalConfig.transfer_storage_id;
}
// check if the source and/or destination storage is overwritten manually
const urlParams = new URLSearchParams(window.location.search);
sourceStorageId = urlParams.has('sourceStorageId') ? urlParams.get('sourceStorageId') : sourceStorageId;
destinationStorageId = urlParams.has('destinationStorageId') ? urlParams.get('destinationStorageId') : destinationStorageId;


const {
    sourceStorage,
    destinationStorage,
    articles,
    articleGroups,
    destStorageArticles,
    activeArticleGroup,
    selectedArticles,
    getArticlesInDestinationStorage,
    getArticlesInSourceStorage,
    putIntoStorage,
    setInitInventory,
    loading,
    error
} = useStorageData(sourceStorageId, destinationStorageId, props.mode);
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
    callback: null
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
const showModal = (title, body, buttons, OKCallback, cancelCallback) => {
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

    modalConf.value.show = true;
}


// sets the initial inventory for the current source storage
const onInitClicked = () => {
    showModal(t('message.init_stock'),
        "",
        { ok: true, cancel: true },
        async () => {
            if (await setInitInventory()) {
                showModal(t('message.init_stock_success'),
                    "",
                    { ok: true, cancel: false },
                );
            } else {
                showModal(t('message.init_stock_error'),
                    error.value,
                    { ok: true, cancel: false },
                );
            };
        },
    );
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
            exit(await putIntoStorage());
        },
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
        window.setTimeout(() => {
            try {
                //window.close();
            } catch (e) {
                alert("Close window now");
                window.location.reload();
            }
        }, 3000);
    }
    showModal(title, body, buttons, cb);
}

</script>

<template>
    <div class="wrapper">
        <ModalDialog :title="modalConf.title" :show="modalConf.show" :buttons="modalConf.buttons"
            @ok="modalConf.OKCallback" @cancel="modalConf.cancelCallback">
            <p v-if="modalConf.rawHTML === false">{{ modalConf.body }}</p>
            <span v-else v-html="modalConf.body"></span>
        </ModalDialog>

        <header class="header">
            <h1 class="left">{{ sourceStorage.name }} -> {{ destinationStorage.name }}</h1>
            <a class="button left"
                :href="`?terminal=${$terminalConfig.name}&sourceStorageId=${destinationStorage.id}&destinationStorageId=${sourceStorage.id}`">⇄</a>
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
                        <p>{{ article.amount ? article.amount : '-' }}</p>
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
    }
}

button.article,
button.article-group {
    width: 5em;
    white-space: normal;
    word-break: break-all;
    height: 3lh;
    padding: 0.5em;
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

    table {
        tr:nth-child(odd) {
            background-color: color.scale($light-button-background, $lightness: -30%);
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
