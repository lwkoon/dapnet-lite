<template>
	<Page :title="$t('navigation.login')" :info="$t('login.information.help')">
		<form class="panel" @submit.prevent="submit">
			<div class="mb-3">
				<label class="form-label">{{ $t('login.username') }}</label>
				<input v-model="username" class="form-control" autocomplete="username" autofocus>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('login.password') }}</label>
				<input v-model="password" type="password" class="form-control" autocomplete="current-password">
			</div>
			<div v-if="error" class="alert alert-danger">{{ error }}</div>
			<button type="submit" class="btn btn-primary" :disabled="busy">
				<span v-if="busy" class="spinner-border spinner-border-sm me-1"></span>{{ $t('general.submit') }}
			</button>
		</form>
	</Page>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Page from '../components/Page.vue';
import { api, basicAuth } from '../api';
import { errorMessage } from '../dialogs';
import { login, state } from '../store';

const router = useRouter();
const route = useRoute();
const username = ref('');
const password = ref('');
const error = ref('');
const busy = ref(false);

async function submit() {
	if (!username.value || !password.value) return;
	busy.value = true;
	error.value = '';
	const auth = basicAuth(username.value.trim(), password.value);
	const previous = { ...state.user };
	login(username.value.trim().toLowerCase(), auth, false);
	try {
		const user = await api.get('users/' + encodeURIComponent(username.value.trim()));
		login(user.name, auth, !!user.admin);
		router.push(typeof route.query.next === 'string' && route.query.next.startsWith('/') ? route.query.next : '/');
	} catch (e) {
		state.user = previous.auth ? previous : { name: 'Guest', auth: '', admin: false };
		error.value = errorMessage(e);
	}
	busy.value = false;
}
</script>
