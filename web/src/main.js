import { createApp } from 'vue';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.min.css';
import 'leaflet/dist/leaflet.css';
import './style.css';

import App from './App.vue';
import router from './router';
import i18n, { ensureLanguage } from './i18n';
import { state } from './store';

ensureLanguage(state.language);

// follow the OS colour scheme
const dark = window.matchMedia('(prefers-color-scheme: dark)');
const applyTheme = () => document.documentElement.setAttribute('data-bs-theme', dark.matches ? 'dark' : 'light');
applyTheme();
dark.addEventListener('change', applyTheme);

createApp(App).use(router).use(i18n).mount('#app');
