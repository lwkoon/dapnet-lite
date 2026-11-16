// Minimal i18n using the original DAPNET Web translation files (replaces vue-i18n).
import { state } from './store';
import en from './i18n/en.json';

const loaders = import.meta.glob('./i18n/*.json');
const messages = { en };
const loading = {};

export const LANGUAGES = [
	['en', 'gb'], ['de', 'de'], ['nl', 'nl'], ['fr', 'fr'], ['it', 'it'],
	['pl', 'pl'], ['pt', 'pt'], ['es', 'es'], ['se', 'se']
];

export function ensureLanguage(lang) {
	if (messages[lang] || loading[lang]) return;
	const loader = loaders['./i18n/' + lang + '.json'];
	if (!loader) return;
	loading[lang] = true;
	loader().then((m) => {
		messages[lang] = m.default;
		// force re-render by touching the reactive language
		const cur = state.language;
		state.language = '';
		state.language = cur;
	});
}

function lookup(dict, key) {
	return key.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : undefined), dict);
}

export function t(key, params) {
	const lang = state.language || 'en';
	ensureLanguage(lang);
	let s = lookup(messages[lang], key);
	if (typeof s !== 'string') s = lookup(en, key);
	if (typeof s !== 'string') return key;
	if (params) s = s.replace(/\{(\w+)\}/g, (m, p) => (params[p] !== undefined ? params[p] : m));
	return s;
}

export default {
	install(app) {
		app.config.globalProperties.$t = t;
	}
};
