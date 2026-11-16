// Thin fetch wrapper around the core REST API (replaces vue-resource).
import { state } from './store';

const ROOT = '/api/';

export class ApiError extends Error {
	constructor(status, body) {
		super('HTTP ' + status);
		this.status = status;
		this.body = body;
	}
}

async function request(method, path, body, { auth = true } = {}) {
	const headers = { Accept: 'application/json' };
	if (auth && state.user.auth) headers.Authorization = 'Basic ' + state.user.auth;
	if (body !== undefined) headers['Content-Type'] = 'application/json';
	let res;
	try {
		res = await fetch(ROOT + path.replace(/^\/+/, ''), {
			method,
			headers,
			body: body === undefined ? undefined : JSON.stringify(body),
			signal: AbortSignal.timeout(30000)
		});
	} catch (e) {
		throw new ApiError(0, null);
	}
	const text = await res.text();
	let data = null;
	if (text) {
		try {
			data = JSON.parse(text);
		} catch (e) {
			data = text;
		}
	}
	if (!res.ok) throw new ApiError(res.status, data);
	return data;
}

export const api = {
	get: (path, opts) => request('GET', path, undefined, opts),
	post: (path, body) => request('POST', path, body),
	put: (path, body) => request('PUT', path, body),
	delete: (path) => request('DELETE', path)
};

export function basicAuth(user, password) {
	const bytes = new TextEncoder().encode(user + ':' + password);
	let bin = '';
	bytes.forEach((b) => { bin += String.fromCharCode(b); });
	return btoa(bin);
}
