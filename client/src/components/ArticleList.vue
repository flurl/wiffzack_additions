<script setup>

const props = defineProps({
    articles: {
        type: Object,
        default: () => []
    },
    articleUpdates: {
        type: Object,
        default: () => []
    }, enableRemovalFromStorage: {
        type: Boolean,
        default: false
    }
});

defineEmits(['articleRemoved']);

</script>

<template>
    <div class="article-list-container">
        <table class="article-list ">
            <template v-for="article in props.articles">
                <tr v-if="articleUpdates[article.id] || article.amount > 0">
                    <td class="amount">
                        <span class="relative-small-text">{{ article.amount.toFixed(2) }}<br></span>
                        +{{ articleUpdates[article.id]?.amount || 0 }}
                    </td>
                    <td class="name">{{ article.name }}</td>
                    <td class="buttons">
                        <button class="cancel" v-if="articleUpdates[article.id] || props.enableRemovalFromStorage"
                            @click="$emit('articleRemoved', article)">
                            <span class="icon">
                                <font-awesome-icon :icon="['fas', 'xmark']" />
                            </span>
                        </button>
                    </td>
                    <!--<td>
                        <button class="confirm" @click="">
                            <span class="icon">
                                <font-awesome-icon :icon="['fas', 'check']" />
                            </span>
                        </button>
                    </td>-->
                </tr>
            </template>
        </table>
    </div>
</template>

<style scoped>
button {
    padding: 0.5em;
    min-width: 0;
}
</style>