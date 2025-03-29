<script setup>

const props = defineProps(['articles']);
defineEmits(['articleRemoved']);

</script>

<template>
    <div class="article-list-container">
        <table class="article-list ">
            <template v-for="article in props.articles">
                <tr v-if="article.amount > 0">
                    <td class="amount">{{ article.amount }}</td>
                    <td class="name">{{ article.name }}</td>
                    <td class="buttons"><button class="cancel" @click="$emit('articleRemoved', article)">
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