<template>
	<Page :title="$t('navigation.rubrics.title')" :info="$t('rubric.overview.information.help')">
		<div class="panel">
			<ListHeader :title="$t('navigation.rubrics.all')" :running="running" :error="error" @reload="load" />
			<TableGrid v-if="rows" :columns="columns" :data="rows">
				<template #actions="{ row }">
					<ActionButtons v-if="canEdit(row)" :on-edit="() => $router.push('/rubrics/edit/' + row.name)" :on-delete="() => remove(row)" />
					<span v-else>---</span>
				</template>
			</TableGrid>
		</div>
		<template #side>
			<div class="panel">
				<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.actions') }}</h2>
				<router-link v-if="state.user.admin" to="/rubrics/new" class="btn btn-primary w-100 mb-2"><i class="bi bi-plus-lg me-1"></i>{{ $t('rubric.new.newrubric') }}</router-link>
				<router-link to="/rubrics/activate" class="btn btn-outline-primary w-100 mb-3">{{ $t('navigation.rubrics.activate') }}</router-link>
				<ul v-if="rows" class="list-group stat-list">
					<li class="list-group-item"><b>{{ $t('rubric.overview.totalrubrics') }}</b><span class="badge text-bg-primary">{{ rows.length }}</span></li>
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
	{ id: 'number', title: 'rubric.overview.table.number' },
	{ id: 'name', title: 'rubric.overview.table.name' },
	{ id: 'label', title: 'rubric.overview.table.label' },
	{ id: 'transmitterGroupNames', title: 'rubric.overview.table.transmittergroup' },
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
		rows.value = (await api.get('rubrics')).sort((a, b) => a.number - b.number);
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

function remove(row) {
	dialogs.confirmDelete(async () => {
		try {
			await api.delete('rubrics/' + encodeURIComponent(row.name));
			load();
		} catch (e) {
			dialogs.ajaxError(e);
		}
	});
}

load();
</script>
