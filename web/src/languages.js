// Supported UI languages: [code, flag]. Shared by the store and i18n.
export const LANGUAGES = [
	['en', 'gb'], ['de', 'de'], ['nl', 'nl'], ['fr', 'fr'], ['it', 'it'],
	['pl', 'pl'], ['pt', 'pt'], ['es', 'es'], ['se', 'se'],
	['zh-CN', 'cn'], ['zh-TW', 'tw']
];

// Map a browser locale (e.g. "zh-HK", "zh-Hant-TW", "de-AT") to one of LANGUAGES.
export function detectLanguage(locale) {
	const l = (locale || 'en').toLowerCase();
	if (l.startsWith('zh')) return /hant|-tw|-hk|-mo/.test(l) ? 'zh-TW' : 'zh-CN';
	if (l.startsWith('sv')) return 'se';
	const code = l.slice(0, 2);
	return LANGUAGES.some(([c]) => c === code) ? code : 'en';
}
