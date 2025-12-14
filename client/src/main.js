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
        new: "New",
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
        transfer_storage_not_empty: "The transfer storage is not empty. Remove articles?",
        articles_in_transfer_storage_list_header: "Articles in transfer storage",
        transfer_storage_empty_success: "The transfer storage was successfully emptied",
        destination_storage: "Destination storage",
        source_storage: "Source storage",
        show_dest_inventory_abbreviation: "Show dest.",
        messages: "Messages",
        quit: "Quit",
        invoices: "Invoices",
        show_all_invoices: "Show all invoices",
        print: "Print",
        alarm: "Alarm",
        trigger_alarm: "Trigger alarm",
        trigger_alarm_success: "Alarm triggered",
        alarm_url_construction_error: "Alarm trigger URL could not be constructed. Configuration or Terminal ID missing.",
        sending_alarm_signal: "Sending alarm signal...",
        terminal_id_not_found_error: "Terminal ID not found in URL. Cannot trigger alarm.",
        checklists: "Checklists",
        new_checklist_name: "New checklist name",
        enter_checklist_category: "Enter checklist category",
        enter_new_checklist_name: "Enter new checklist name",
        error_updating_checklist: "Error updating checklist",
        error_fetching_checklists: "Error fetching checklists",
        error_fetching_checklist_questions: "Error fetching checklist questions",
        error_creating_checklist: "Error creating checklist",
        error_closing_checklist: "Error closing checklist",
        error_fetching_checklist_answers: "Error fetching checklist answers",
        error_deleting_checklist: "Error deleting checklist",
        confirm_delete_checklist: "Are you sure you want to delete '{name}'?",
        done: "Done",
        skip: "Skip",
        close_checklist: "Close checklist",
        save: "Save",
        storage_swap_not_possible: "Storage swap not possible",
        remove_article_title: "Remove Article",
        remove_article_body: "Do you want to remove '{articleName}' completely from the storage?",
        yes: "Yes",
        no: "No",
        updating: "Updating..."
      }
    },
    de: {
      message: {
        cancel: 'Abbrechen',
        OK: 'OK',
        new: "Neu",
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
        transfer_storage_not_empty: "Das Transferlager ist nicht leer. Artikel löschen?",
        articles_in_transfer_storage_list_header: "Artikel im Transferlager",
        transfer_storage_empty_success: "Das Transferlager wurde erfolgreich geleert",
        destination_storage: "Ziellager",
        source_storage: "Quelllager",
        show_dest_inventory_abbreviation: "Ziel anz.",
        messages: "Nachrichten",
        quit: "Beenden",
        invoices: "Rechnungen",
        show_all_invoices: "Alle Rechnungen anzeigen",
        print: "Drucken",
        alarm: "Alarm",
        trigger_alarm: "Alarm auslösen",
        trigger_alarm_success: "Alarm erfolgreich ausgelöst",
        alarm_url_construction_error: "Alarm-URL konnte nicht erstellt werden. Konfiguration oder Terminal-ID fehlt.",
        sending_alarm_signal: "Alarmsignal wird gesendet...",
        terminal_id_not_found_error: "Terminal-ID nicht in URL gefunden. Alarm kann nicht ausgelöst werden.",
        checklists: "Checklisten",
        new_checklist_name: "Neue Checklist Name",
        enter_checklist_category: "Checklist-Kategorie eingeben",
        enter_new_checklist_name: "Neuen Checklistennamen eingeben",
        error_updating_checklist: "Fehler beim Aktualisieren der Checkliste",
        error_fetching_checklists: "Fehler beim Abrufen der Checklisten",
        error_fetching_checklist_questions: "Fehler beim Abrufen der Checklist Fragen",
        error_creating_checklist: "Fehler beim Erstellen der Checkliste",
        error_closing_checklist: "Fehler beim Schließen der Checkliste",
        error_fetching_checklist_answers: "Fehler beim Abrufen der Checklist-Antworten",
        error_deleting_checklist: "Fehler beim Löschen der Checkliste",
        confirm_delete_checklist: "Sind Sie sicher, dass Sie '{name}' löschen möchten?",
        done: "Erledigt",
        skip: "Überspringen",
        close_checklist: "Checkliste schließen",
        save: "Speichern",
        storage_swap_not_possible: "Umschalten der Lager nicht möglich",
        remove_article_title: "Artikel löschen",
        remove_article_body: "Den Artikel '{articleName}' komplett aus dem Lager löschen?",
        yes: "Ja",
        no: "Nein",
        updating: "Aktualisierung..."
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

// Import baseline default configuration.
import { config as defConf } from './config.default.js';
let config = defConf;
try {
  // Attempt to fetch optional client config from server root.
  const response = await fetch("/config.json");
  const conf = await response.json();
  // Merge client config over defaults (shallow merge).
  config = { ...config, ...conf };
  console.log('Config file found.');
} catch (error) {
  // On error (404, network, bad JSON), use defaults.
  console.log('No config file found, using defaults.');
}

const app = createApp(App)

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
