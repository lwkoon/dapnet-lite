<template>
	<div class="container py-3">
		<div class="hero mb-4">
			<h1 class="h2">{{ $t('home.carousel.1.title').replace('DAPNET Web', 'DAPNET Lite') }}</h1>
			<p class="mb-3 opacity-75">
				A standalone paging core for amateur radio: send calls and rubric news to POCSAG pagers through your own
				transmitters (UniPager, RasPager, MMDVM&nbsp;DAPNET gateways).
			</p>
			<router-link v-if="!isLoggedIn" to="/login" class="btn btn-light">{{ $t('navigation.login') }}</router-link>
			<router-link v-else to="/calls/new" class="btn btn-light"><i class="bi bi-send me-1"></i>{{ $t('calls.overview.newcall') }}</router-link>
		</div>

		<div class="row g-4">
			<div class="col-lg-8">
				<div class="panel">
					<h2 class="h5">{{ $t('navigation.transmitters.title') }} — ONLINE</h2>
					<LeafletMap :markers="markers" />
					<router-link v-if="isLoggedIn" to="/transmitters/map" class="d-inline-block mt-2">{{ $t('home.information.map') }}</router-link>
				</div>
			</div>
			<div class="col-lg-4">
				<div class="panel">
					<ListHeader :title="$t('general.statistics')" :running="running" :error="error" @reload="load" />
					<ul v-if="stats" class="list-group stat-list">
						<li class="list-group-item"><span><i class="bi bi-chat-text me-2"></i>{{ $t('home.information.statistics.calls') }}</span><span class="badge text-bg-primary">{{ stats.callsTotal }}</span></li>
						<li class="list-group-item"><span><i class="bi bi-people me-2"></i>{{ $t('navigation.subscribers') }}</span><span class="badge text-bg-primary">{{ stats.callSigns }}</span></li>
						<li class="list-group-item"><span><i class="bi bi-newspaper me-2"></i>{{ $t('home.information.statistics.rubric-content') }}</span><span class="badge text-bg-primary">{{ stats.news }}</span></li>
						<li class="list-group-item"><span><i class="bi bi-journal-text me-2"></i>{{ $t('home.information.statistics.rubrics') }}</span><span class="badge text-bg-primary">{{ stats.rubrics }}</span></li>
						<li class="list-group-item"><span><i class="bi bi-broadcast-pin me-2"></i>{{ $t('home.information.statistics.transmitters') }}</span><span class="badge text-bg-success">{{ stats.transmittersOnline }} / {{ stats.transmittersTotal }}</span></li>
						<li class="list-group-item"><span><i class="bi bi-hdd-network me-2"></i>{{ $t('home.information.statistics.nodes') }}</span><span class="badge text-bg-success">{{ stats.nodesOnline }} / {{ stats.nodesTotal }}</span></li>
						<li class="list-group-item"><span><i class="bi bi-person me-2"></i>{{ $t('home.information.statistics.users') }}</span><span class="badge text-bg-primary">{{ stats.users }}</span></li>
					</ul>
					<div v-if="stats" class="mt-3">
						<Doughnut :labels="['ONLINE', 'OFFLINE']" :values="[stats.transmittersOnline, stats.transmittersTotal - stats.transmittersOnline]"
							:colors="['#2a9d8f', '#adb5bd']" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from 'vue';
import LeafletMap from '../components/LeafletMap.vue';
import ListHeader from '../components/ListHeader.vue';
import Doughnut from '../components/Doughnut.vue';
import { api } from '../api';
import { errorMessage, escapeHtml } from '../dialogs';
import { isLoggedIn } from '../store';

const stats = ref(null);
const markers = ref([]);
const running = ref(false);
const error = ref(false);

async function load() {
	running.value = true;
	try {
		stats.value = await api.get('stats');
		const txs = await api.get('transmitters');
		markers.value = txs.filter((t) => t.status === 'ONLINE').map((t) => ({
			lat: parseFloat(t.latitude), lng: parseFloat(t.longitude), color: '#2a9d8f',
			popup: '<b>' + escapeHtml(t.name) + '</b><br>' + escapeHtml(t.deviceType || '') + ' ' + escapeHtml(t.deviceVersion || '')
		}));
		error.value = false;
	} catch (e) {
		error.value = errorMessage(e);
	}
	running.value = false;
}

load();
</script>
