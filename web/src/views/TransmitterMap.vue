<template>
	<div class="container py-3">
		<h1 class="page-title">{{ $t('transmitter.map.title') }}</h1>
		<div class="row g-4">
			<div class="col-lg-9">
				<LeafletMap :markers="markers" :lines="lines" :focus="$route.params.id" />
			</div>
			<div class="col-lg-3">
				<div class="panel">
					<h2 class="h6 text-uppercase text-body-secondary">{{ $t('transmitter.map.settings.title') }}</h2>
					<div class="form-check"><input id="o1" class="form-check-input" type="checkbox" v-model="opt.onlineOnly"><label for="o1" class="form-check-label">{{ $t('transmitter.map.checkbox.showonlineonly') }}</label></div>
					<div class="form-check"><input id="o2" class="form-check-input" type="checkbox" v-model="opt.widerangeOnly"><label for="o2" class="form-check-label">{{ $t('transmitter.map.checkbox.showwiderangeonly') }}</label></div>
					<div class="form-check"><input id="o3" class="form-check-input" type="checkbox" v-model="opt.nodes"><label for="o3" class="form-check-label">{{ $t('transmitter.map.checkbox.shownodes') }}</label></div>
					<div class="form-check"><input id="o4" class="form-check-input" type="checkbox" v-model="opt.nodeLines"><label for="o4" class="form-check-label">{{ $t('transmitter.map.checkbox.shownodeline') }}</label></div>
					<div class="form-check mb-2"><input id="o5" class="form-check-input" type="checkbox" v-model="opt.bySlot"><label for="o5" class="form-check-label">{{ $t('transmitter.map.checkbox.showbytimeslot') }}</label></div>
					<div v-if="opt.bySlot" class="timeslots mb-2">
						<label v-for="s in SLOTS" :key="s" class="d-flex flex-column align-items-center small">{{ s }}<input type="checkbox" class="form-check-input" :value="s" v-model="opt.slots"></label>
					</div>
					<hr>
					<div class="small d-flex flex-column gap-1">
						<span><span class="legend-dot" style="background:#2a9d8f"></span> Transmitter ONLINE</span>
						<span><span class="legend-dot" style="background:#adb5bd"></span> Transmitter OFFLINE</span>
						<span><span class="legend-dot" style="background:#e76f51"></span> Transmitter ERROR / DISABLED</span>
						<span><span class="legend-dot" style="background:#264653"></span> Node</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import LeafletMap from '../components/LeafletMap.vue';
import { api } from '../api';
import { dialogs, escapeHtml } from '../dialogs';

const SLOTS = '0123456789ABCDEF'.split('');
const COLORS = { ONLINE: '#2a9d8f', OFFLINE: '#adb5bd' };
const transmitters = ref([]);
const nodes = ref([]);
const opt = reactive({ onlineOnly: false, widerangeOnly: false, nodes: true, nodeLines: false, bySlot: false, slots: [] });

Promise.all([api.get('transmitters'), api.get('nodes')]).then(([t, n]) => {
	transmitters.value = t;
	nodes.value = n;
}).catch(dialogs.ajaxError);

const visible = computed(() => transmitters.value.filter((t) =>
	(!opt.onlineOnly || t.status === 'ONLINE') &&
	(!opt.widerangeOnly || t.usage === 'WIDERANGE') &&
	(!opt.bySlot || opt.slots.some((s) => (t.timeSlot || '').includes(s)))));

const markers = computed(() => {
	const list = visible.value.map((t) => ({
		id: t.name,
		lat: parseFloat(t.latitude),
		lng: parseFloat(t.longitude),
		color: COLORS[t.status] || '#e76f51',
		popup: '<b>' + escapeHtml(t.name) + '</b> (' + escapeHtml(t.status) + ')<br>' +
			escapeHtml((t.deviceType || '') + ' ' + (t.deviceVersion || '')) + '<br>' +
			'Power: ' + escapeHtml(t.power) + ' W · Slots: ' + escapeHtml(t.timeSlot) + '<br>' +
			'Owner: ' + escapeHtml((t.ownerNames || []).join(', '))
	}));
	if (opt.nodes) {
		nodes.value.forEach((n) => list.push({
			id: 'node:' + n.name, lat: parseFloat(n.latitude), lng: parseFloat(n.longitude), color: '#264653', radius: 10,
			popup: '<b>Node ' + escapeHtml(n.name) + '</b><br>' + escapeHtml(n.status) + (n.version ? ' · v' + escapeHtml(n.version) : '')
		}));
	}
	return list;
});

const lines = computed(() => {
	if (!opt.nodeLines) return [];
	const byName = Object.fromEntries(nodes.value.map((n) => [n.name.toLowerCase(), n]));
	return visible.value.filter((t) => t.status === 'ONLINE' && t.nodeName && byName[t.nodeName.toLowerCase()])
		.map((t) => {
			const n = byName[t.nodeName.toLowerCase()];
			return [[parseFloat(t.latitude), parseFloat(t.longitude)], [parseFloat(n.latitude), parseFloat(n.longitude)]];
		});
});
</script>

<style scoped>
.legend-dot {
	display: inline-block;
	width: .75rem;
	height: .75rem;
	border-radius: 50%;
	margin-right: .35rem;
	vertical-align: middle;
}
</style>
