# Wiffzack Additions - Client Documentation

This document describes the structure and functionality of the Vue.js client application for the Wiffzack additions project. The client interacts with the Python Flask backend (`server.py`) to display data and provide user interfaces for various features.

## Core Concepts

### 1. Routing (`src/router/index.js`)

Navigation within the application is handled by `vue-router`. Key routes include:

*   `/data_table/:endpoint`: Displays generic tabular data fetched from the specified backend API endpoint. Uses the `DataTable` component. The `:endpoint` part of the URL determines which API endpoint is called (e.g., `/data_table/artikel` calls `/api/artikel`).
*   `/storage/:mode`: Provides an interface for storage management (e.g., viewing, updating). Uses the `Storage` component. The `:mode` parameter likely controls the specific storage operation or view. (*Note: `Storage.vue` file not provided in context*).
*   `/message/list`: Shows a list of available messages fetched from the backend. Uses the `MessageList` component.
*   `/message/view/:msgPath`: Displays the content of a specific message identified by `:msgPath`. Uses the `MessageView` component.

### 2. API Interaction (`src/composables/useApiData.js`)

A reusable composable function, `useApiData`, centralizes the logic for fetching data from the backend API.

*   **Purpose:** Handles making `axios` GET requests, managing reactive `isLoading` and `error` states, and returning the fetched `data`.
*   **Usage:** Components import and call `useApiData`, providing the API path (e.g., `/api/message/list`) and optional configuration.
*   **Features:**
    *   Accepts static or reactive API paths.
    *   Injects backend configuration (`config.backendHost`).
    *   Provides `isLoading` and `error` refs for UI feedback.
    *   Allows response transformation via a `transformResponse` function to adapt to different API response structures.
    *   Handles automatic fetching on component mount or when the API path changes (controlled by the `immediate` option).

### 3. Configuration (`inject('config')`)

Components requiring backend information (like the base URL) use Vue's `inject('config')` mechanism. This configuration is expected to be provided by a parent component or the main application setup (`main.js`, not shown) and typically includes `backendHost`.

## Components

### 1. `DataTable.vue`

*   **Purpose:** A generic component to display data fetched from an API endpoint in an HTML table.
*   **Props:**
    *   `endpoint` (String, required): The specific API path segment (e.g., `artikel`, `wardrobe_sales`) to fetch data from. The component prepends `/api/` and the `backendHost`.
*   **Functionality:** Uses the `useApiData` composable to fetch and display data based on the `endpoint` prop. Shows loading and error states via the `Header` component.

### 2. `MessageList.vue`

*   **Purpose:** Displays a list of messages available on the server.
*   **Functionality:** Uses `useApiData` to fetch data from the `/api/message/list` endpoint. Renders each message name as a `RouterLink` pointing to the `MessageView` component for that specific message. Uses the `Header` component for title, loading, and error states.

### 3. `MessageView.vue`

*   **Purpose:** Displays the content of a single message. Supports both plain text (`txt`) and HTML (`html`) message types.
*   **Routing:** Activated via the `/message/view/:msgPath` route. The `msgPath` parameter from the URL determines which message to fetch.
*   **Functionality:**
    *   Uses the `useApiData` composable with a dynamic API path based on `route.params.msgPath` (e.g., `/api/message/some-message-path`).
    *   Conditionally renders the content based on `message.type`:
        *   `txt`: Displays content within a `<pre>` tag.
        *   `html`: Renders the message content within an `<iframe>`. The `iframe`'s `src` attribute points to the backend's HTML serving endpoint (`/message/html/<message_path>/`).
    *   Uses the `Header` component to display the message name.

### 4. `Header.vue` (*Inferred*)

*   **Purpose:** Likely a common header component used across different views.
*   **Props (Inferred):**
    *   `title` (String): The title to display.
    *   `loading` (Boolean): Indicates if data is currently loading.
    *   `error` (String/Object): Displays an error message if present.
*   **Functionality:** Provides a consistent look and feel for page titles and displays loading/error feedback passed down from parent components using the `useApiData` composable.

### 5. `Storage.vue` (*Inferred from Router*)

*   **Purpose:** Likely handles interactions related to storage management (viewing stock, moving items, etc.).
*   **Routing:** Activated via `/storage/:mode`.
*   **Functionality:** Interacts with various `/api/storage_...` and `/api/update_storage/...` backend endpoints, potentially using the `useApiData` composable or direct `axios` calls for POST requests.

## Running the Client

(Assuming standard Vue project setup)

1.  Install dependencies: `npm install`
2.  Run the development server: `npm run dev`
3.  Access the application in your browser, usually at `http://localhost:5173` (or the port specified by Vite).

Ensure the backend server (`server.py`) is running and accessible at the `backendHost` URL configured for the client.
