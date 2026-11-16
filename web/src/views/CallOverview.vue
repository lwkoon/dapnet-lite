<template>
	<Page :title="$t('navigation.calls')" :info="$t('calls.overview.information.help')">
		<div class="panel">
			<ListHeader :title="$t('calls.overview.allcalls')" :running="running" :error="error" @reload="load" />
			<TableGrid v-if="rows" :columns="columns" :data="rows" />
		</div>
		<template #side>
			<div class="panel">
				<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.actions') }}</h2>
				<router-link to="/calls/new" class="btn btn-primary w-100 mb-3"><i class="bi bi-send me-1"></i>{{ $t('calls.overview.newcall') }}</router-link>
				<template v-if="rows">
					<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.statistics') }}</h2>
					<ul class="list-group stat-list">
						<li class="list-group-item"><b>{{ $t('calls.overview.emergencies') }}</b><span class="badge text-bg-danger">{{ rows.filter((r) => r.emergency).length }}</span></li>
						<li class="list-group-item"><b>{{ $t('calls.overview.totalcalls') }}</b><span class="badge text-bg-primary">{{ rows.length }}</span></li>
					</ul>
				</template>
			</div>
		</template>
	</Page>
</template>

<script setup>
import { ref } from 'vue';
import Page from '../components/Page.vue';
import ListHeader from '../components/ListHeader.vue';
import TableGrid from '../components/TableGrid.vue';
import { api } from '../api';
import { errorMessage } from '../dialogs';
import { state } from '../store';

const columns = [
	{ id: 'timestamp', title: 'calls.overview.table.timestamp', time: true },
	{ id: 'callSignNames', title: 'navigation.subscribers' },
	{ id: 'transmitterGroupNames', title: 'calls.overview.table.txgroups' },
	{ id: 'text', title: 'calls.overview.table.message' },
	{ id: 'emergency', title: 'calls.overview.table.emergency' },
	{ id: 'ownerName', title: 'general.owner' }
];
const rows = ref(null);
const running = ref(false);
const error = ref(false);

async function load() {
	running.value = true;
	try {
		const url = state.user.admin ? 'calls' : 'calls?ownerName=' + encodeURIComponent(state.user.name);
		rows.value = (await api.get(url)).reverse();
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

load();
</script>
