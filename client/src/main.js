//import './assets/bulma.css'
import './assets/global.scss'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createI18n } from 'vue-i18n'

import axios from 'axios';

const i18n = createI18n({
  locale: 'de',
  fallbackLocale: 'en',
  messages: {
    en: {
      message: {
        cancel: 'Cancel',
        OK: 'OK',
        request: "Request",
        distribute: "Distribute",
        receive: "Receive",
        request_articles: "Request articles",
        distribute_articles: "Distribute articles",
        transfer_articles: "Transfer articles",
        all: "all",
        success: "Success",
        error: "Error",
        init_stock: "Set initial storage inventory",
        init_stock_success: "Setting the initial inventory succeeded",
        init_stock_error: "Setting the initial inventory failed",
        messages: "Messages",
        quit: "Quit"
      }
    },
    de: {
      message: {
        cancel: 'Abbrechen',
        OK: 'OK',
        request: "Anfordern",
        distribute: "Verteilen",
        receive: "Empfangen",
        request_articles: "Artikel anfordern",
        distribute_articles: "Artikel verteilen",
        transfer_articles: "Artikel verschieben",
        all: "alle",
        success: "Erfolg",
        error: "Fehler",
        init_stock: "Initialen Lagerstand setzen",
        init_stock_success: "Initialen Lagerstand erfolgreich gesetzt",
        init_stock_error: "Initialen Lagerstand konnte nicht gesetzt werden",
        messages: "Nachrichten",
        quit: "Beenden"
      }
    }
  }
})

/* import the fontawesome core */
import { library } from '@fortawesome/fontawesome-svg-core'
/* import font awesome icon component */
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
/* import specific icons */
import { fas } from '@fortawesome/free-solid-svg-icons'
/* add icons to the library */
library.add(fas)

const app = createApp(App)

const config = { backendHost: 'http://localhost:5000' };
app.provide('config', config);


app.use(router)
app.use(i18n)
app.component('font-awesome-icon', FontAwesomeIcon)

// get terminal id
const urlParams = new URLSearchParams(window.location.search);
const terminal = urlParams.get('terminal');
const destTerminal = urlParams.get('destTerminal');

const fetchConfig = async (terminalId) => {
  try {
    const response = await axios.get(`${config.backendHost}/api/get_config/${terminalId}`);
    return response.data.config;
  } catch (error) {
    console.error(`Error fetching config for terminal ${terminalId}:`, error);
    return {};
  }
};

const init = async () => {
  const terminalConfig = await fetchConfig(terminal);
  const destTerminalConfig = destTerminal ? await fetchConfig(destTerminal) : {};
  app.config.globalProperties.$terminalConfig = terminalConfig;
  app.config.globalProperties.$destTerminalConfig = destTerminalConfig;
  app.mount('#app');
};

init();







