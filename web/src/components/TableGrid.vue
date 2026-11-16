<template>
	<div>
		<div class="d-flex flex-wrap gap-2 justify-content-between mb-2">
			<div class="input-group input-group-sm table-search">
				<input class="form-control" v-model="query" :placeholder="$t('general.search')">
				<button class="btn btn-outline-secondary" @click="query = ''" title="Clear"><i class="bi bi-x-lg"></i></button>
			</div>
			<div class="d-flex align-items-center gap-1 small">
				<button class="btn btn-outline-secondary btn-sm" @click="move(-1)"><i class="bi bi-arrow-left"></i></button>
				{{ $t('table.pagination.page') }}
				<input class="form-control form-control-sm page-input" v-model.number="gotoPage" type="number" min="1" :max="totalPages">
				{{ $t('table.pagination.of') }} {{ totalPages }}
				<button class="btn btn-outline-secondary btn-sm" @click="move(1)"><i class="bi bi-arrow-right"></i></button>
			</div>
		</div>
		<div class="table-responsive">
			<table class="table table-striped table-hover align-middle mb-0">
				<thead>
					<tr>
						<th v-for="col in columns" :key="col.id" @click="sortBy(col.id)" class="sortable" :class="{ active: sortKey === col.id }">
							{{ $t(col.title) }}
							<i v-if="sortKey === col.id" class="bi" :class="order[col.id] > 0 ? 'bi-caret-up-fill' : 'bi-caret-down-fill'"></i>
						</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, i) in pageRows" :key="row.name || row.timestamp || i">
						<td v-for="col in columns" :key="col.id">
							<slot :name="col.id" :row="row" :value="row[col.id]">
								<template v-if="col.time">{{ formatTime(row[col.id]) }}</template>
								<template v-else>{{ display(row[col.id]) }}</template>
							</slot>
						</td>
					</tr>
					<tr v-if="pageRows.length === 0">
						<td :colspan="columns.length" class="text-center text-body-secondary">—</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { t } from '../i18n';
import { formatTime } from '../helpers';

const props = defineProps({ data: Array, columns: Array, rowsPerPage: { type: Number, default: 10 } });

const query = ref('');
const sortKey = ref('');
const order = reactive(Object.fromEntries(props.columns.map((c) => [c.id, 1])));
const startRow = ref(0);
const gotoPage = ref(1);

function display(v) {
	if (Array.isArray(v)) return v.join(', ');
	if (v === true) return t('general.yes');
	if (v === false) return t('general.no');
	if (v === null || v === undefined || v === '') return '---';
	return v;
}

function searchable(v) {
	if (v && typeof v === 'object' && !Array.isArray(v)) return Object.values(v).join(' ');
	return String(display(v));
}

const filtered = computed(() => {
	let rows = props.data || [];
	const q = query.value.toLowerCase();
	if (q) rows = rows.filter((r) => Object.values(r).some((v) => searchable(v).toLowerCase().includes(q)));
	const key = sortKey.value;
	if (key) {
		const col = props.columns.find((c) => c.id === key) || {};
		const o = order[key];
		rows = rows.slice().sort((a, b) => {
			let x = a[key];
			let y = b[key];
			if (col.time) {
				if (!x) return 1;
				if (!y) return -1;
				x = new Date(x);
				y = new Date(y);
				return (x > y ? -1 : x < y ? 1 : 0) * o;
			}
			if (Array.isArray(x)) x = x.join(',');
			if (Array.isArray(y)) y = y.join(',');
			return (x > y ? 1 : x < y ? -1 : 0) * o;
		});
	}
	return rows;
});

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / props.rowsPerPage)));
const pageRows = computed(() => filtered.value.slice(startRow.value, startRow.value + props.rowsPerPage));

function sortBy(key) {
	if (key === 'actions') return;
	sortKey.value = key;
	order[key] *= -1;
	startRow.value = 0;
}

function move(dir) {
	const next = startRow.value + dir * props.rowsPerPage;
	if (next >= 0 && next < filtered.value.length) startRow.value = next;
}

watch(startRow, (v) => { gotoPage.value = v / props.rowsPerPage + 1; });
watch(query, () => { startRow.value = 0; });
watch(gotoPage, (p) => {
	if (p >= 1 && p <= totalPages.value) startRow.value = (p - 1) * props.rowsPerPage;
});
</script>
