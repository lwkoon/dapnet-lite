<template>
	<Page :title="$t('navigation.users')" :info="$t('users.new.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ id ? $t('users.new.edituser') : $t('users.general.newuser') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.name') }}</label>
				<input v-model="form.name" class="form-control" :readonly="!!id" autocomplete="off">
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.password') }}</label>
				<div class="input-group">
					<input v-model="form.password" :type="show ? 'text' : 'password'" class="form-control" autocomplete="new-password"
						:placeholder="id ? '(unchanged)' : ''">
					<button type="button" class="btn btn-outline-secondary" @click="show = !show"><i class="bi" :class="show ? 'bi-eye' : 'bi-eye-slash'"></i></button>
					<button type="button" class="btn btn-outline-secondary" title="Generate" @click="form.password = generatePassword(); show = true"><i class="bi bi-arrow-repeat"></i></button>
				</div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('users.general.email') }}</label>
				<input v-model="form.mail" type="email" class="form-control">
			</div>
			<div v-if="state.user.admin" class="form-check mb-3">
				<input id="admin" class="form-check-input" type="checkbox" v-model="form.admin">
				<label for="admin" class="form-check-label">{{ $t('users.general.admin') }}</label>
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/users" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
		</form>
	</Page>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Page from '../components/Page.vue';
import { api, basicAuth } from '../api';
import { dialogs } from '../dialogs';
import { generatePassword, hasInput } from '../helpers';
import { login, state } from '../store';

const route = useRoute();
const router = useRouter();
const id = route.params.id;
const form = reactive({ name: '', password: '', mail: '', admin: false });
const show = ref(false);

if (id) {
	api.get('users/' + encodeURIComponent(id)).then((u) => {
		Object.assign(form, { name: u.name, mail: u.mail || '', admin: !!u.admin });
	}).catch(() => router.push('/users'));
}

async function submit() {
	if (!hasInput(form, id ? ['password', 'admin'] : ['admin'])) return;
	const name = form.name.trim().toLowerCase();
	const body = { mail: form.mail, admin: form.admin };
	if (form.password) body.hash = form.password;
	try {
		if (!id) {
			try {
				await api.get('users/' + encodeURIComponent(name));
				dialogs.overwrite();
				return;
			} catch (e) {
				if (e.status !== 404) throw e;
			}
		}
		await api.put('users/' + encodeURIComponent(name), body);
		// keep the session valid after changing one's own password
		if (name === state.user.name && form.password) login(name, basicAuth(name, form.password), state.user.admin);
		dialogs.success();
		router.push('/users');
	} catch (e) {
		dialogs.ajaxError(e);
	}
}
</script>
