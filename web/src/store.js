// Small persisted store (replaces vuex + vuex-persistedstate).
import { reactive, computed, watch } from 'vue';
import { detectLanguage } from './languages';

const KEY = 'dapnet-lite-web';

function load() {
	try {
		return JSON.parse(localStorage.getItem(KEY)) || {};
	} catch (e) {
		return {};
	}
}

const saved = load();

export const state = reactive({
	user: saved.user || { name: 'Guest', auth: '', admin: false },
	language: saved.language || detectLanguage(navigator.language),
	map: { center: [3.14, 101.69], zoom: 6 },
	mapTiles: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
});

watch(() => ({ user: state.user, language: state.language }), (v) => {
	try {
		localStorage.setItem(KEY, JSON.stringify(v));
	} catch (e) {
		// private mode etc. — session still works in memory
	}
}, { deep: true });

export const isLoggedIn = computed(() => state.user.name !== 'Guest' && state.user.auth !== '');

export function login(name, auth, admin) {
	state.user = { name, auth, admin };
}

export function logout() {
	state.user = { name: 'Guest', auth: '', admin: false };
}
