<script setup>
const props = defineProps({
    checked: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(['toggled']);

const toggled = () => {
    emit('toggled');
};

</script>

<template>
    <div class="toggle-switch">
        <label class="switch">
            <input type="checkbox" :checked="props.checked" @change="toggled">
            <span class="slider round"></span>
        </label>
        <label v-if="$slots.default">
            <slot />
        </label>
    </div>
</template>


<style lang="scss" scoped>
.toggle-switch {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.switch {
    position: relative;
    display: inline-block;
    width: 5.9rem;
    height: 3rem;
}

/* Hide default HTML checkbox */
.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

/* The slider */
.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    -webkit-transition: .4s;
    transition: .4s;
}

.slider:before {
    position: absolute;
    content: "";
    height: 2.8rem;
    width: 2.8rem;
    left: 0.1rem;
    bottom: 0.1rem;
    background-color: white;
    -webkit-transition: .4s;
    transition: .4s;
}

input:checked+.slider {
    background-color: #2196F3;
}

input:focus+.slider {
    box-shadow: 0 0 1px #2196F3;
}

input:checked+.slider:before {
    transform: translateX(2.9rem);
}

/* Rounded sliders */
.slider.round {
    border-radius: 3rem;
}

.slider.round:before {
    border-radius: 50%;
}
</style>