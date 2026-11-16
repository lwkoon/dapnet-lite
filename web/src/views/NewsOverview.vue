<template>
	<Page :title="$t('navigation.rubrics.content')" :info="$t('news.overview.information.help')">
		<div class="panel">
			<ListHeader :title="$t('news.overview.allrubriccontent')" :running="running" :error="error" @reload="load" />
			<TableGrid v-if="rows" :columns="columns" :data="rows" />
		</div>
		<template #side>
			<div class="panel">
				<h2 class="h6 text-uppercase text-body-secondary">{{ $t('general.actions') }}</h2>
				<router-link to="/rubrics/content/new" class="btn btn-primary w-100 mb-3"><i class="bi bi-plus-lg me-1"></i>{{ $t('news.overview.newrubriccontent') }}</router-link>
				<ul v-if="rows" class="list-group stat-list">
					<li class="list-group-item"><b>{{ $t('news.overview.totalrubriccontent') }}</b><span class="badge text-bg-primary">{{ rows.length }}</span></li>
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
import { api } from '../api';
import { errorMessage } from '../dialogs';

const columns = [
	{ id: 'timestamp', title: 'news.overview.table.timestamp', time: true },
	{ id: 'rubricName', title: 'news.overview.table.rubric' },
	{ id: 'number', title: 'news.overview.table.number' },
	{ id: 'text', title: 'news.overview.table.message' },
	{ id: 'ownerName', title: 'general.owner' }
];
const rows = ref(null);
const running = ref(false);
const error = ref(false);

async function load() {
	running.value = true;
	try {
		const data = await api.get('news');
		rows.value = Object.values(data).flat().filter(Boolean);
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

load();
</script>
