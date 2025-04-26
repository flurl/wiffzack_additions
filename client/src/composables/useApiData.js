// src/composables/useApiData.js
import { ref, inject, watch, computed, unref } from 'vue';
import axios from 'axios';

/**
 * A composable function for fetching data from the API.
 *
 * @param {Ref<string> | string} urlPath - The API path (e.g., '/api/message/list' or a ref/computed property).
 * @param {object} [options={}] - Configuration options.
 * @param {Function} [options.transformResponse=(data) => data] - Function to transform the raw response data.
 * @param {*} [options.initialData=null] - Initial value for the data ref.
 * @param {boolean} [options.immediate=true] - Whether to fetch data immediately when the composable is used or the urlPath changes.
 * @returns {object} - An object containing reactive refs for data, isLoading, error, and the fetchData function.
 */
export function useApiData(urlPath, options = {}) {
    const {
        transformResponse = (data) => data, // Default: return raw data
        initialData = null,
        immediate = true,
    } = options;

    const config = inject('config');
    const data = ref(initialData);
    const isLoading = ref(false);
    const error = ref(null);

    // Ensure urlPath is reactive if it's a ref or computed
    const reactiveUrlPath = computed(() => unref(urlPath));

    const fetchData = async () => {
        // Don't fetch if the path is empty or config is missing
        if (!reactiveUrlPath.value || !config?.backendHost) {
            console.warn('useApiData: Skipping fetch - URL path or backendHost is missing.');
            error.value = "Configuration or URL path missing.";
            return;
        }

        isLoading.value = true;
        error.value = null;
        // Reset data to initial state only if needed, often you want to keep old data while loading new
        // data.value = initialData;

        const fullUrl = `${config.backendHost}${reactiveUrlPath.value}`;

        try {
            const response = await axios.get(fullUrl);

            // Basic success check (can be customized)
            if (response.status === 200) {
                // Apply the transformation function provided in options
                data.value = transformResponse(response.data);
                // Handle potential nested success flags if needed within transformResponse
                if (response.data?.success === false) {
                    console.warn(`API indicated failure for ${fullUrl}:`, response.data);
                    error.value = `API request ${fullUrl} failed.`;
                }
            } else {
                console.warn(`Unexpected status code from ${fullUrl}:`, response.status);
                error.value = `Server returned status ${response.status} for ${fullUrl}.`;
            }
        } catch (err) {
            console.error(`Error fetching data from ${fullUrl}:`, err);
            error.value = err.message || 'Failed to fetch data.';
            if (err.response) {
                error.value = `Server error: ${err.response.status} - ${err.response.statusText}`;
            }
            data.value = initialData; // Reset data on error
        } finally {
            isLoading.value = false;
        }
    };

    // Watch the reactive URL path and refetch if it changes
    watch(reactiveUrlPath, (newPath, oldPath) => {
        // Only fetch if the path actually changed and immediate is true
        if (newPath && newPath !== oldPath && immediate) {
            fetchData();
        }
    }, { immediate: immediate }); // Use immediate option from parameters

    // Return reactive state and the fetch function
    return { data, isLoading, error, fetchData };
}
