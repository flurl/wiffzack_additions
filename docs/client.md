# Wiffzack Client Documentation

This is the frontend client for the Wiffzack Additions. It is a Vue 3 application built with Vite, providing a user interface for storage management, messaging, invoicing, and alarm features.

## Features

- **Vue 3** with Composition API
- **Vite** for fast development and builds
- **Vue Router** (memory history)
- **Vue I18n** for internationalization (German/English)
- **FontAwesome** icon support
- **SCSS** with custom variables and global styles
- Modular, reusable components
- Dynamic configuration via `/public/config.json` (overrides defaults)
- Responsive design for touch screens and desktop

## Project Structure

```
client/
├── index.html
├── jsconfig.json
├── package.json
├── vite.config.js
├── public/
│   ├── config.json   # Optional: override default config
│   └── favicon.ico
└── src/
    ├── App.vue
    ├── config.default.js
    ├── main.js
    ├── assets/
    │   ├── _variables.scss
    │   └── global.scss
    ├── components/
    │   ├── AlarmDialog.vue
    │   ├── ArticleList.vue
    │   ├── DataTable.vue
    │   ├── Header.vue
    │   ├── InvoicePrintDialog.vue
    │   ├── JOTD.vue
    │   ├── MessageList.vue
    │   ├── MessageView.vue
    │   ├── ModalDialog.vue
    │   ├── OnScreenKeyboard.vue
    │   ├── QuitButton.vue
    │   ├── Storage.vue
    │   ├── StorageSelection.vue
    │   └── ToggleSwitch.vue
    ├── composables/
    │   └── useApiData.js
    ├── router/
    │   └── index.js
    └── utils/
        └── useColor.js
```

## Setup

### Install dependencies

```sh
npm install
```

### Development server

```sh
npm run dev
```

### Build for production

```sh
npm run build
```

### Preview production build

```sh
npm run preview
```

## Configuration

- Default configuration: [`src/config.default.js`](src/config.default.js)
- To override, create `public/config.json`. It will be merged with the defaults at runtime.

Example `public/config.json`:
```json
{
  "backendHost": "http://your-backend-host:5000"
}
```

## Internationalization

- English and German translations included.
- Default language: German (`de`). Fallback: English (`en`).

## Usage Notes

- Uses memory history for routing (supports kiosk environments).
- SCSS variables and global styles: [`src/assets/_variables.scss`](src/assets/_variables.scss), [`src/assets/global.scss`](src/assets/global.scss)
- FontAwesome icons are globally available as `<font-awesome-icon>`.
- Modular components for dialogs, tables, storage, messaging, and more.
- API endpoints and backend host are configurable.

## Further Reading

- [Vite Documentation](https://vite.dev/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Vue Router](https://router.vuejs.org/)
- [Vue I18n](https://kazupon.github.io/vue-i18n/)

## Component and Composable Descriptions

### Components

- **AlarmDialog.vue**: Dialog for triggering an alarm for a specific client. Uses API to send alarm requests and displays modal dialogs for confirmation and errors.
- **ArticleList.vue**: Displays a list of articles with amounts and names. Allows removal of articles via an event.
- **DataTable.vue**: Generic table component that fetches and displays data from a specified API endpoint. Supports filtering and uses an on-screen keyboard for input.
- **Header.vue**: Page header with a title, loading spinner, error display, and a quit button.
- **InvoicePrintDialog.vue**: Dialog for listing, selecting, and printing invoices. Fetches invoice data from the backend and allows filtering by type.
- **JOTD.vue**: Displays the "Joke of the Day" or message of the day, fetched from the backend.
- **MessageList.vue**: Lists available messages from the backend. Each message links to a detailed view.
- **MessageView.vue**: Displays the content of a selected message, supporting both text and HTML message types.
- **ModalDialog.vue**: Generic modal dialog component for confirmations, alerts, and custom dialogs. Supports different types and button configurations.
- **OnScreenKeyboard.vue**: On-screen keyboard for text input, supporting different search modes and emitting events for input changes.
- **QuitButton.vue**: Button to close the application window (for kiosk environments).
- **Storage.vue**: Main component for storage management, handling different modes (request, distribute, transfer, stock). Integrates article lists, dialogs, and storage data composable.
- **StorageSelection.vue**: Allows selection of storage locations/terminals, highlights those with pending requests, and fetches configuration from the backend.
- **ToggleSwitch.vue**: Simple toggle switch component for boolean options, emits toggled events.

### Composables

- **useApiData.js**: Generic composable for fetching data from an API endpoint. Handles loading, error, and data state, supports transformation of responses, and can be used reactively with refs or computed paths.
- **useStorageData.js**: Composable for managing storage-related data and actions. Handles fetching storage names, article groups, articles in source/destination/transfer storage, and supports operations like inventory initialization and transfer. Provides reactive state for use in storage-related components.
- **useColor.js**: Utility composable for color calculations. Provides functions to generate a color from a string and to determine if a color is dark, used for UI theming and contrast.

---

For questions or contributions, see the main project README or contact the maintainers.
