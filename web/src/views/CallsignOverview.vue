<template>
	<Page :title="$t('navigation.subscribers')" :info="$t('subscribers.overview.information.help')">
		<div class="panel">
			<ListHeader :title="$t('subscribers.overview.allsubscribers')" :running="running" :error="error" @reload="load" />
			<TableGrid v-if="rows" :columns="columns" :data="rows">
				<template #pagers="{ value }">{{ value ? value.map((p) => p.number + ' (' + p.name + ')').join(', ') : '---' }}</template>
				<template #actions="{ row }">
					<ActionButtons v-if="canEdit(row)" :on-edit="() => $router.push('/subscribers/edit/' + row.name)" :on-delete="() => remove(row)" />
					<span v-else>---</span>
				</template>
			</TableGrid>
		</div>
		<template #side>
			<div class="panel">
				<template v-if="state.user.admin">
					<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.actions') }}</h2>
					<router-link to="/subscribers/new" class="btn btn-primary w-100 mb-3"><i class="bi bi-plus-lg me-1"></i>{{ $t('subscribers.overview.newsubscriber') }}</router-link>
				</template>
				<ul v-if="rows" class="list-group stat-list">
					<li class="list-group-item"><b>{{ $t('subscribers.overview.totalsubscribers') }}</b><span class="badge text-bg-primary">{{ rows.length }}</span></li>
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
	{ id: 'name', title: 'subscribers.overview.table.subscriber' },
	{ id: 'description', title: 'general.description' },
	{ id: 'pagers', title: 'subscribers.overview.table.pager' },
	{ id: 'ownerNames', title: 'general.owner' },
	{ id: 'actions', title: 'general.actions' }
];
const rows = ref(null);
const running = ref(false);
const error = ref(false);

const canEdit = (row) => state.user.admin || (row.ownerNames || []).includes(state.user.name);

async function load() {
	running.value = true;
	try {
		rows.value = await api.get('callsigns');
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

function remove(row) {
	dialogs.confirmDelete(async () => {
		try {
			await api.delete('callsigns/' + encodeURIComponent(row.name));
			load();
		} catch (e) {
			dialogs.ajaxError(e);
		}
	});
}

load();
</script>
