// Port of the original $helpers.
import { api } from './api';
import { dialogs } from './dialogs';

// Every field must be non-empty (arrays included), like checkForInput in DAPNET Web.
export function hasInput(form, skip = []) {
	for (const [k, v] of Object.entries(form)) {
		if (skip.includes(k)) continue;
		if (v === '' || v === null || v === undefined || (Array.isArray(v) && v.length === 0)) {
			dialogs.missingInput();
			return false;
		}
	}
	return true;
}

// When creating (no id in route) refuse to overwrite an existing object.
export async function saveChecked(router, routeId, url, body, gotoUrl) {
	if (!routeId) {
		try {
			await api.get(url);
			dialogs.overwrite();
			return;
		} catch (e) {
			if (e.status !== 404) {
				dialogs.ajaxError(e);
				return;
			}
		}
	}
	try {
		await api.put(url, body);
		router.push(gotoUrl);
	} catch (e) {
		dialogs.ajaxError(e);
	}
}

export function generatePassword(length = 16) {
	const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789';
	const buf = new Uint32Array(length);
	crypto.getRandomValues(buf);
	return Array.from(buf, (n) => chars[n % chars.length]).join('');
}

export function formatTime(v) {
	if (!v) return '---';
	return new Date(v).toLocaleString(undefined, {
		day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit'
	});
}

export function zeroPad(n, width) {
	return String(n).padStart(width, '0');
}

export function names(list) {
	return (list || []).map((x) => (typeof x === 'string' ? x : x.name));
}

export async function mailTo(ownerFilter, subject) {
	try {
		const users = await api.get('users');
		const mails = [...new Set(users.filter(ownerFilter).map((u) => u.mail).filter(Boolean))];
		window.location.href = 'mailto:' + mails.join(',') + '?subject=' + encodeURIComponent(subject);
	} catch (e) {
		dialogs.ajaxError(e);
	}
}
