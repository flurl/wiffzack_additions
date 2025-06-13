<script setup>
import { computed, onMounted, onUpdated, ref, nextTick, watch } from 'vue';
import { useApiData } from '@/composables/useApiData'; // Adjust path if needed
import OnScreenKeyboard from './OnScreenKeyboard.vue';
import Header from './Header.vue';

import dragscroll from 'dragscroll';


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

const filterString = ref('');
const searchMode = ref('startsWith'); // 'includes' or 'startsWith'

const showFilterControls = ref(false);
const filterControlsRef = ref(null);
const filterControlsHeight = ref(0);
const tableScrollContainerRef = ref(null); // Add a ref for the scroll container
const groupByColumnIndex = ref(null);


const toggleSearchMode = () => {
    searchMode.value = searchMode.value === 'includes' ? 'startsWith' : 'includes';
};

const isRowVisible = (row) => {
    if (filterString.value === '') {
        return true;
    }
    // filterString.value is already uppercase due to the @input handler and alphabet buttons
    const upperCaseFilter = filterString.value;

    return row.some(col => {
        const colAsString = String(col).toUpperCase(); // Convert col to string and then to uppercase
        if (searchMode.value === 'includes') {
            return colAsString.includes(upperCaseFilter);
        } else { // 'startsWith'
            return colAsString.startsWith(upperCaseFilter);
        }
    });
};

const displayedRows = computed(() => {
    if (!data.value || data.value.length === 0) return [];

    const filteredData = data.value.filter(row => isRowVisible(row));
    if (filteredData.length === 0) return [];

    let currentBgShouldBeAlt = false; // Start with the first group/row having normal background

    return filteredData.map((row, visibleIndex) => {
        let rowClass = 'row-bg-normal'; // Default to normal background

        if (groupByColumnIndex.value !== null &&
            groupByColumnIndex.value >= 0 && // Ensure it's a valid non-negative index
            row && groupByColumnIndex.value < row.length) { // Ensure it's within bounds for the current row

            if (visibleIndex > 0) {
                const prevVisibleRow = filteredData[visibleIndex - 1];
                // Ensure previous row also has the column
                if (prevVisibleRow && groupByColumnIndex.value < prevVisibleRow.length) {
                    const currentGroupValue = row[groupByColumnIndex.value];
                    const prevGroupValue = prevVisibleRow[groupByColumnIndex.value];

                    if (currentGroupValue !== prevGroupValue) {
                        currentBgShouldBeAlt = !currentBgShouldBeAlt;
                    }
                } else {
                    // Previous row didn't exist or didn't have the group column, treat as a new group boundary
                    currentBgShouldBeAlt = !currentBgShouldBeAlt;
                }
            }
            // For the very first visible row (visibleIndex === 0), currentBgShouldBeAlt remains its initial state (false).
            // So the first group gets 'row-bg-normal'.
            if (currentBgShouldBeAlt) {
                rowClass = 'row-bg-alt';
            }
        } else {
            // Standard odd/even logic for visible rows (0-indexed)
            if (visibleIndex % 2 !== 0) { // 0 is normal, 1 is alt, 2 is normal...
                rowClass = 'row-bg-alt';
            }
        }
        return { cells: row, class: rowClass, key: `filtered-row-${visibleIndex}` }; // Unique key for v-for
    });
});

const toggleFilterControls = () => {
    showFilterControls.value = !showFilterControls.value;
};

watch(showFilterControls, async (isShown) => {
    if (isShown) {
        await nextTick(); // Wait for the DOM to update
        if (filterControlsRef.value) {
            filterControlsHeight.value = filterControlsRef.value.offsetHeight;
        }
    } else {
        // reset filter when the filter input is hidden
        filterString.value = ''; // Directly reset filterString
    }
    // When hidden, the padding will be set to 0 based on showFilterControls directly in the template
});

watch(filterString, () => {
    if (tableScrollContainerRef.value) {
        // Use nextTick to ensure the DOM has updated if rows are being hidden/shown
        nextTick(() => {
            tableScrollContainerRef.value.scrollTop = 0;
        });
    }
});

onMounted(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const groupByColParam = urlParams.get('groupByColumn');
    if (groupByColParam) {
        const parsedIndex = parseInt(groupByColParam, 10);
        if (!isNaN(parsedIndex) && parsedIndex >= 0) {
            groupByColumnIndex.value = parsedIndex;
        } else {
            console.warn(`Invalid groupByColumn parameter: "${groupByColParam}". Must be a non-negative integer.`);
        }
    }
    // Dragscroll initialization
    document.getElementsByTagName('body')[0].classList.add('dragscroll');
    dragscroll.reset();
});

onUpdated(() => {
    dragscroll.reset();
});

</script>

<template>
    <div class="datatable-view-wrapper">
        <Header :title="props.endpoint" :loading="isLoading" :error="error" />

        <div class="table-scroll-container" ref="tableScrollContainerRef"
            :style="{ paddingBottom: showFilterControls ? filterControlsHeight + 'px' : '0px' }">
            <!-- Data Table -->
            <table v-if="displayedRows.length > 0">
                <tbody>
                    <template v-for="processedRow in displayedRows" :key="processedRow.key">
                        <tr :class="processedRow.class">
                            <td v-for="(col, colIndex) in processedRow.cells"
                                :key="`col-${processedRow.key}-${colIndex}`">{{ col }}</td>
                        </tr>
                    </template>
                </tbody>
            </table>

            <!-- Message when no data is available -->
            <div v-else class="no-data-message">
                No data available or matches your filter for "{{ props.endpoint }}".
            </div>
        </div>

        <button class="toggle-filter-btn" @click="toggleFilterControls"
            :title="showFilterControls ? 'Hide Filters' : 'Show Filters'"
            :style="{ bottom: showFilterControls ? (filterControlsHeight + 10) + 'px' : '10px' }">
            <font-awesome-icon :icon="['fas', showFilterControls ? 'times' : 'search']" />
        </button>

        <div class="filter_input" v-if="showFilterControls" ref="filterControlsRef">
            <input type="text" placeholder="Filter..." v-model="filterString"
                @input="filterString = $event.target.value.toUpperCase()">
            <OnScreenKeyboard v-model="filterString" :search-mode="searchMode" @toggle-search-mode="toggleSearchMode"
                @reset-filter="filterString = ''" />
        </div>
    </div>
</template>

<style lang="scss" scoped>
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

tr.row-bg-alt {
    background-color: color.scale($light-button-background, $lightness: +30%);
}

.datatable-view-wrapper {
    display: flex;
    flex-direction: column;
    height: 100vh;
    /* Assuming component takes full viewport height */
}

.table-scroll-container {
    flex-grow: 1;
    overflow-y: auto;
    position: relative;
    /* Context for absolute positioned elements if any in future */
    transition: padding-bottom 0.3s ease-in-out;
}

.no-data-message {
    padding: 20px;
    text-align: center;
    color: #666;
}

.toggle-filter-btn {
    position: fixed;
    bottom: 10px;
    right: 10px;
    z-index: 1001;
    /* Above filter panel */
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.filter_input {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    background-color: color.scale($light-background, $lightness: -3%); // Approx #f0f0f0, slightly darker than main bg
    padding: 10px;
    border-top: 1px solid $light-border; // Use global border color
    flex-direction: column;
    gap: 5px;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1); // Optional: add a subtle shadow to lift it visually
}
</style>
