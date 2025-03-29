<template>
    <table>
        <tbody>
            <tr v-for="(row, index) in data" :key="index">
                <td v-for="(col, index) in row" :key="index">{{ col }}</td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import axios from 'axios';

export default {
    name: 'DataTable',
    props: {
        endpoint: String,
    },
    data() {
        return {
            data: [],
        };
    },
    methods: {
        getData() {
            axios
                .get(`http://localhost:5000/api/${this.$props.endpoint}`)
                .then((response) => {
                    this.data = response.data;
                })
                .catch((error) => {
                    console.log(error);
                });
        },
    },
    created() {
        this.getData();
    },
};
</script>
