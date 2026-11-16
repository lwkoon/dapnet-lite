<template>
	<Page :title="$t('navigation.transmitters.title')" :info="$t('transmitter.overview.information.text')">
		<div class="panel">
			<ListHeader :title="$t('navigation.transmitters.all')" :running="running" :error="error" @reload="load" />
			<TableGrid v-if="rows" :columns="columns" :data="rows">
				<template #address="{ value }">{{ value ? value.ip_addr : '---' }}</template>
				<template #deviceType="{ row }">
					<i class="bi me-1" :class="row.usage === 'WIDERANGE' ? 'bi-broadcast' : 'bi-house'" :title="row.usage"></i>
					{{ row.deviceType || '---' }}<span v-if="row.deviceVersion" class="text-body-secondary"> v{{ row.deviceVersion }}</span>
				</template>
				<template #status="{ value }"><StatusBadge :status="value" /></template>
				<template #actions="{ row }">
					<ActionButtons v-if="canEdit(row)" :on-edit="() => $router.push('/transmitters/edit/' + row.name)"
						:on-delete="() => remove(row)" :on-mail="() => mailOwners(row)" :on-rubrics="() => sendRubrics(row)" />
					<router-link v-else :to="'/transmitters/map/' + row.name" class="btn btn-sm btn-outline-secondary"><i class="bi bi-geo-alt"></i></router-link>
				</template>
			</TableGrid>
		</div>
		<template #side>
			<div class="panel">
				<template v-if="state.user.admin">
					<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.actions') }}</h2>
					<router-link to="/transmitters/new" class="btn btn-primary w-100 mb-2"><i class="bi bi-plus-lg me-1"></i>{{ $t('transmitter.overview.actions.newtransmitter') }}</router-link>
					<button class="btn btn-outline-secondary w-100 mb-3" @click="mailAll">{{ $t('transmitter.overview.actions.sendmailtoallowners') }}</button>
				</template>
				<template v-if="rows">
					<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.statistics') }}</h2>
					<ul class="list-group stat-list mb-3">
						<li class="list-group-item"><b>{{ $t('transmitter.overview.statistics.widerange') }}</b><span class="badge text-bg-primary">{{ count('WIDERANGE', true) }} / {{ count('WIDERANGE') }}</span></li>
						<li class="list-group-item"><b>{{ $t('transmitter.overview.statistics.personal') }}</b><span class="badge text-bg-primary">{{ count('PERSONAL', true) }} / {{ count('PERSONAL') }}</span></li>
						<li class="list-group-item"><b>{{ $t('transmitter.overview.statistics.total') }}</b><span class="badge text-bg-success">{{ count(null, true) }} / {{ rows.length }}</span></li>
					</ul>
					<Doughnut :labels="chart.labels" :values="chart.values" :colors="chart.colors" />
					<div class="form-check mt-2">
						<input id="wro" class="form-check-input" type="checkbox" v-model="widerangeOnly">
						<label for="wro" class="form-check-label small">{{ $t('transmitter.overview.statistics.widerangeonly') }}</label>
					</div>
				</template>
			</div>
		</template>
	</Page>
</template>

<script setup>
import { computed, ref } from 'vue';
import Page from '../components/Page.vue';
import ListHeader from '../components/ListHeader.vue';
import TableGrid from '../components/TableGrid.vue';
import ActionButtons from '../components/ActionButtons.vue';
import StatusBadge from '../components/StatusBadge.vue';
import Doughnut from '../components/Doughnut.vue';
import { api } from '../api';
import { dialogs, errorMessage } from '../dialogs';
import { mailTo } from '../helpers';
import { state } from '../store';

const columns = [
	{ id: 'name', title: 'transmitter.overview.table.callsign' },
	{ id: 'nodeName', title: 'transmitter.overview.table.node' },
	{ id: 'address', title: 'transmitter.overview.table.ipaddress' },
	{ id: 'ownerNames', title: 'general.owner' },
	{ id: 'deviceType', title: 'transmitter.overview.table.device' },
	{ id: 'status', title: 'transmitter.overview.table.status' },
	{ id: 'connectedSince', title: 'transmitter.overview.table.connectedsince', time: true },
	{ id: 'actions', title: 'general.actions' }
];
const PALETTE = ['#1f6f78', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51', '#6d597a', '#457b9d', '#8ab17d'];
const rows = ref(null);
const running = ref(false);
const error = ref(false);
const widerangeOnly = ref(false);

const canEdit = (row) => state.user.admin || (row.ownerNames || []).includes(state.user.name);
const count = (usage, online) => rows.value.filter((r) => (!usage || r.usage === usage) && (!online || r.status === 'ONLINE')).length;

const chart = computed(() => {
	const counts = {};
	(rows.value || []).forEach((r) => {
		if (r.status !== 'ONLINE' || (widerangeOnly.value && r.usage !== 'WIDERANGE')) return;
		const k = r.deviceType || 'Unknown';
		counts[k] = (counts[k] || 0) + 1;
	});
	const labels = Object.keys(counts).sort();
	return { labels, values: labels.map((l) => counts[l]), colors: labels.map((_, i) => PALETTE[i % PALETTE.length]) };
});

async function load() {
	running.value = true;
	try {
		rows.value = await api.get('transmitters');
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

function remove(row) {
	dialogs.confirmDelete(async () => {
		try {
			await api.delete('transmitters/' + encodeURIComponent(row.name));
			load();
		} catch (e) {
			dialogs.ajaxError(e);
		}
	});
}

async function sendRubrics(row) {
	try {
		await api.get('transmitterControl/sendRubricNames/' + encodeURIComponent(row.name));
		dialogs.success();
	} catch (e) {
		dialogs.ajaxError(e);
	}
}

const mailOwners = (row) => mailTo((u) => row.ownerNames.includes(u.name), 'DAPNET Transmitter: ' + row.name);
const mailAll = () => mailTo((u) => rows.value.some((r) => r.ownerNames.includes(u.name)), 'DAPNET Transmitter');

load();
</script>
