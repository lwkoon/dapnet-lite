<template>
	<Page :title="$t('navigation.users')" :info="$t('users.overview.information.help')">
		<div class="panel">
			<ListHeader :title="$t('users.overview.allusers')" :running="running" :error="error" @reload="load" />
			<TableGrid v-if="rows" :columns="columns" :data="rows">
				<template #actions="{ row }">
					<ActionButtons v-if="state.user.admin || row.name === state.user.name"
						:on-edit="() => $router.push('/users/edit/' + row.name)"
						:on-delete="state.user.admin ? () => remove(row) : null"
						:on-mail="row.mail ? () => mail(row) : null" />
					<span v-else>---</span>
				</template>
			</TableGrid>
		</div>
		<template #side>
			<div class="panel">
				<template v-if="state.user.admin">
					<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.actions') }}</h2>
					<router-link to="/users/new" class="btn btn-primary w-100 mb-2"><i class="bi bi-plus-lg me-1"></i>{{ $t('users.general.newuser') }}</router-link>
					<button class="btn btn-outline-secondary w-100 mb-3" @click="mailAll">{{ $t('users.overview.sendemailallusers') }}</button>
				</template>
				<ul v-if="rows" class="list-group stat-list">
					<li class="list-group-item"><b>{{ $t('users.overview.totaladmins') }}</b><span class="badge text-bg-warning">{{ rows.filter((u) => u.admin).length }}</span></li>
					<li class="list-group-item"><b>{{ $t('users.overview.totalusers') }}</b><span class="badge text-bg-primary">{{ rows.length }}</span></li>
				</ul>
			</div>
		</template>
	</Page>
</template>

<script setup>
import { ref } from 'vue';
import Page from '../components/Page.vue';
import ListHeader from '../components/ListHeader.vue';
import TableGrid from '../components/TableGrid.vue';
import ActionButtons from '../components/ActionButtons.vue';
import { api } from '../api';
import { dialogs, errorMessage } from '../dialogs';
import { state } from '../store';

const columns = [
	{ id: 'name', title: 'general.name' },
	{ id: 'mail', title: 'users.general.email' },
	{ id: 'admin', title: 'users.general.admin' },
	{ id: 'callsigns', title: 'navigation.subscribers' },
	{ id: 'actions', title: 'general.actions' }
];
const rows = ref(null);
const running = ref(false);
const error = ref(false);

async function load() {
	running.value = true;
	try {
		const [users, callsigns] = await Promise.all([api.get('users'), api.get('callsigns')]);
		users.forEach((u) => {
			u.callsigns = callsigns.filter((c) => (c.ownerNames || []).includes(u.name)).map((c) => c.name);
		});
		rows.value = users;
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

function remove(row) {
	dialogs.confirmDelete(async () => {
		try {
			await api.delete('users/' + encodeURIComponent(row.name));
			load();
		} catch (e) {
			dialogs.ajaxError(e);
		}
	});
}

function mail(row) {
	window.location.href = 'mailto:' + row.mail + '?subject=DAPNET';
}

function mailAll() {
	window.location.href = 'mailto:' + rows.value.map((u) => u.mail).filter(Boolean).join(',') + '?subject=DAPNET';
}

load();
</script>
