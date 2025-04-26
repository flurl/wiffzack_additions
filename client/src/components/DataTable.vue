<script setup>
import { computed } from 'vue'; // Removed ref, onMounted, inject
import { useApiData } from '@/composables/useApiData'; // Adjust path if needed
import Header from './Header.vue';


// --- Props ---
// Define props using defineProps
const props = defineProps({
    endpoint: {
        type: String,
        required: true, // Make endpoint required for clarity
    },
});

const apiUrlPath = computed(() => `/api/${props.endpoint}`);

// Use the composable
const {
    data, // Use data directly
    isLoading,
    error,
    fetchData
} = useApiData(apiUrlPath, { // Pass the computed property
    initialData: [], // Default to empty array for tables
    transformResponse: (responseData) => {
        // Handle different possible structures (direct array or nested under 'data')
        if (responseData?.success && Array.isArray(responseData?.data)) {
            return responseData.data;
        }
        // Return empty array if structure is unexpected but request succeeded
        console.warn(`Unexpected data structure for ${apiUrlPath.value}, returning empty array.`);
        return [];
    }
});


</script>

<template>
    <Header :title="props.endpoint" :loading="isLoading" :error="error" />

    <!-- Data Table -->
    <table v-if="data.length > 0">
        <tbody>
            <tr v-for="(row, rowIndex) in data" :key="`row-${rowIndex}`">
                <td v-for="(col, colIndex) in row" :key="`col-${rowIndex}-${colIndex}`">{{ col }}</td>
            </tr>
        </tbody>
    </table>

    <!-- Message when no data is available -->
    <div v-else>
        No data available for "{{ props.endpoint }}".
    </div>
</template>

<style scoped>
/* Add some basic styling */
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th,
td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

th {
    background-color: #f2f2f2;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}
</style>
