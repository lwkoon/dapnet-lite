<template>
	<Page :title="$t('navigation.nodes')" :info="$t('nodes.overview.information.help')">
		<div class="panel">
			<ListHeader :title="$t('nodes.overview.allnodes')" :running="running" :error="error" @reload="load" />
			<TableGrid v-if="rows" :columns="columns" :data="rows">
				<template #address="{ value }">{{ value ? value.ip_addr : '---' }}</template>
				<template #status="{ value }"><StatusBadge :status="value" /></template>
				<template #actions="{ row }">
					<ActionButtons v-if="state.user.admin" :on-edit="() => $router.push('/nodes/edit/' + row.name)" :on-delete="() => remove(row)" />
					<span v-else>---</span>
				</template>
			</TableGrid>
		</div>
		<template #side>
			<div class="panel">
				<template v-if="state.user.admin">
					<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.actions') }}</h2>
					<router-link to="/nodes/new" class="btn btn-primary w-100 mb-3"><i class="bi bi-plus-lg me-1"></i>{{ $t('nodes.overview.newnode') }}</router-link>
				</template>
				<ul v-if="rows" class="list-group stat-list">
					<li class="list-group-item"><b>{{ $t('nodes.overview.statistics.totalnodes') }}</b><span class="badge text-bg-primary">{{ rows.length }}</span></li>
				</ul>
				<p class="small text-body-secondary mt-3 mb-0">This core runs standalone; the node list only describes this server.</p>
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
import StatusBadge from '../components/StatusBadge.vue';
import { api } from '../api';
import { dialogs, errorMessage } from '../dialogs';
import { state } from '../store';

const columns = [
	{ id: 'name', title: 'nodes.overview.table.name' },
	{ id: 'version', title: 'nodes.overview.table.version' },
	{ id: 'address', title: 'nodes.overview.table.ipaddress' },
	{ id: 'ownerNames', title: 'general.owner' },
	{ id: 'status', title: 'nodes.overview.table.status' },
	{ id: 'actions', title: 'general.actions' }
];
const rows = ref(null);
const running = ref(false);
const error = ref(false);

async function load() {
	running.value = true;
	try {
		rows.value = await api.get('nodes');
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

function remove(row) {
	dialogs.confirmDelete(async () => {
		try {
			await api.delete('nodes/' + encodeURIComponent(row.name));
			load();
		} catch (e) {
			dialogs.ajaxError(e);
		}
	});
}

load();
</script>
