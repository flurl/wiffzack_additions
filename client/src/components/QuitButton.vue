<script setup>

const exit = () => {
    window.close();
    alert('The window should be closed now. But if you can read this it propably didn\'t work as expected.')
}

</script>

<template>
    <button @click="exit">{{ $t('message.quit') }}</button>
</template>

<style scoped></style>
