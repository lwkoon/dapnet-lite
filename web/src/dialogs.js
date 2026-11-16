// Modal + toast state (replaces sweetalert2). Rendered by components/Dialogs.vue.
import { reactive } from 'vue';
import { t } from './i18n';

export const dialog = reactive({ open: false, kind: 'info', title: '', html: '', confirm: null, confirmText: '' });
export const toasts = reactive([]);

function show(kind, title, html, confirm = null, confirmText = '') {
	Object.assign(dialog, { open: true, kind, title, html, confirm, confirmText });
}

export function close() {
	dialog.open = false;
	dialog.confirm = null;
}

export const dialogs = {
	success() {
		const id = Date.now() + Math.random();
		toasts.push({ id, title: t('alerts.success.title'), text: t('alerts.success.text') });
		setTimeout(() => {
			const i = toasts.findIndex((x) => x.id === id);
			if (i >= 0) toasts.splice(i, 1);
		}, 3000);
	},
	error(title, html) {
		show('error', title, html);
	},
	confirmDelete(work) {
		show('warning', t('alerts.delete.title'), t('alerts.delete.text'), work, t('general.yes'));
	},
	confirm(title, html, work, confirmText) {
		show('warning', title, html, work, confirmText || t('general.continue'));
	},
	missingInput() {
		show('error', t('alerts.input.title'), t('alerts.input.text'));
	},
	overwrite() {
		show('error', t('alerts.overwrite.title'), t('alerts.overwrite.text'));
	},
	ajaxError(err) {
		const status = err && err.status !== undefined ? err.status : -1;
		const body = (err && err.body) || {};
		if (status === 0) {
			show('error', t('rest.errors.no-connection'), t('rest.errors.api-unreachable'));
		} else if (status === 400) {
			let html = escapeHtml(body.message || '') + ':';
			if (body.code === 4001 && Array.isArray(body.violations)) {
				html += '<ul class="text-start mt-2">' + body.violations.map((v) =>
					'<li>' + escapeHtml(v.field + ' ' + v.message + ' (' + v.code + ' - ' + v.constraint + ')') + '</li>').join('') + '</ul>';
			}
			show('error', (body.name || 'Bad Request') + ' (' + (body.code || 400) + ')', html);
		} else if (status === 401) {
			show('error', t('rest.errors.title'), t('rest.errors.permissions'));
		} else if (status === 403) {
			show('error', t('rest.errors.403.title'), t('rest.errors.403.text'));
		} else if (status === 404) {
			show('error', t('rest.errors.404.title'), t('rest.errors.404.text'));
		} else if (status === 406 && body.message) {
			show('error', body.name || t('rest.errors.title'), escapeHtml(body.message));
		} else {
			show('error', t('rest.errors.title'), t('rest.errors.http-error', { status }));
		}
	}
};

export function errorMessage(err) {
	if (!err || err.status === 0) return t('rest.errors.api-unreachable');
	if (err.status === 401 || err.status === 403) return t('rest.errors.permissions');
	return t('rest.errors.http-error', { status: err.status });
}

export function escapeHtml(s) {
	return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
