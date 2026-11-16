<template>
	<Page :title="$t('navigation.transmitters.title')" :info="$t('transmitter.new.table.description')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ id ? $t('transmitter.new.edittransmitter') : $t('transmitter.new.newtransmitter') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('transmitter.new.callsign.title') }}</label>
				<input v-model="form.name" class="form-control" :readonly="!!id">
				<div class="form-text">{{ $t('transmitter.new.callsign.help') }}</div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('transmitter.new.password.title') }}</label>
				<div class="input-group">
					<input :type="showKey ? 'text' : 'password'" v-model="form.authKey" class="form-control font-monospace" autocomplete="new-password">
					<button type="button" class="btn btn-outline-secondary" title="Toggle visibility" @click="showKey = !showKey"><i class="bi" :class="showKey ? 'bi-eye' : 'bi-eye-slash'"></i></button>
					<button type="button" class="btn btn-outline-secondary" title="Copy" @click="copy"><i class="bi bi-clipboard"></i></button>
					<button type="button" class="btn btn-outline-secondary" title="Generate" @click="form.authKey = generatePassword(); showKey = true"><i class="bi bi-arrow-repeat"></i></button>
				</div>
				<div class="form-text">{{ $t('transmitter.new.password.help') }} (A-Z, a-z, 0-9)</div>
			</div>
			<div class="row g-3 mb-2">
				<div class="col-md-6">
					<label class="form-label">{{ $t('general.latlong.title') }}</label>
					<div class="input-group">
						<input v-model.number="pos.lat" type="number" step="any" min="-90" max="90" class="form-control" placeholder="lat">
						<input v-model.number="pos.lng" type="number" step="any" min="-180" max="180" class="form-control" placeholder="lng">
					</div>
				</div>
				<div class="col-md-6">
					<label class="form-label">{{ $t('transmitter.new.usage.title') }}</label>
					<select class="form-select" v-model="form.usage">
						<option value="PERSONAL">{{ $t('transmitter.new.usage.personal') }}</option>
						<option value="WIDERANGE">{{ $t('transmitter.new.usage.widerange') }}</option>
					</select>
				</div>
			</div>
			<div class="mb-3">
				<label class="form-label small text-body-secondary">{{ $t('general.latlong.picker') }}</label>
				<LeafletMap small :pick="pos" @pick="(p) => Object.assign(pos, p)" />
			</div>
			<div class="row g-3 mb-3">
				<div class="col-md-4">
					<label class="form-label">{{ $t('transmitter.new.antennatype.title') }}</label>
					<select class="form-select" v-model="form.antennaType">
						<option value="OMNI">{{ $t('transmitter.new.antennatype.omni') }}</option>
						<option value="DIRECTIONAL">{{ $t('transmitter.new.antennatype.directional') }}</option>
					</select>
				</div>
				<div class="col-md-4">
					<label class="form-label">Direction (°)</label>
					<input v-model.number="form.antennaDirection" :disabled="form.antennaType === 'OMNI'" type="number" min="0" max="359" class="form-control">
				</div>
				<div class="col-md-4">
					<label class="form-label">Power (W)</label>
					<input v-model.number="form.power" type="number" step="any" min="0" max="200" class="form-control">
				</div>
				<div class="col-md-4">
					<label class="form-label">Antenna height AGL (m)</label>
					<input v-model.number="form.antennaAboveGroundLevel" type="number" min="0" max="1000" class="form-control">
				</div>
				<div class="col-md-4">
					<label class="form-label">Antenna gain (dBi)</label>
					<input v-model.number="form.antennaGainDbi" type="number" step="any" min="-50" max="80" class="form-control">
				</div>
				<div class="col-md-4">
					<label class="form-label">ID RIC</label>
					<input v-model.number="form.identificationAddress" type="number" min="0" max="2097151" class="form-control">
				</div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('transmitter.new.timeslots.title') }}</label>
				<div class="timeslots">
					<label v-for="s in SLOTS" :key="s" class="d-flex flex-column align-items-center small">
						{{ s }}<input type="checkbox" class="form-check-input mt-1" :value="s" v-model="slots">
					</label>
				</div>
				<div class="form-text">{{ $t('transmitter.new.timeslots.help') }}</div>
			</div>
			<div class="row g-3 mb-3">
				<div class="col-md-8">
					<label class="form-label">{{ $t('general.owner') }}</label>
					<MultiSelect v-model="form.ownerNames" :options="users" />
					<div class="form-text">{{ $t('transmitter.new.owner.help') }}</div>
				</div>
				<div class="col-md-4">
					<label class="form-label">Status</label>
					<div class="form-check form-switch mt-2">
						<input id="disabled" class="form-check-input" type="checkbox" v-model="disabled">
						<label for="disabled" class="form-check-label">DISABLED</label>
					</div>
				</div>
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/transmitters" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
		</form>
		<template #side>
			<ul v-if="info" class="list-group stat-list">
				<li class="list-group-item"><b>Status</b><StatusBadge :status="info.status" /></li>
				<li v-if="info.deviceType" class="list-group-item"><b>Device</b><span>{{ info.deviceType }} {{ info.deviceVersion }}</span></li>
				<li v-if="info.nodeName" class="list-group-item"><b>Node</b><span>{{ info.nodeName }}</span></li>
				<li v-if="info.address" class="list-group-item"><b>IP</b><span class="font-monospace small">{{ info.address.ip_addr }}:{{ info.address.port }}</span></li>
				<li v-if="info.lastConnected" class="list-group-item"><b>Last</b><span class="small">{{ formatTime(info.lastConnected) }}</span></li>
				<li v-if="info.connectedSince" class="list-group-item"><b>Since</b><span class="small">{{ formatTime(info.connectedSince) }}</span></li>
				<li class="list-group-item"><b>Calls</b><span>{{ info.callCount || 0 }}</span></li>
			</ul>
		</template>
	</Page>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Page from '../components/Page.vue';
import MultiSelect from '../components/MultiSelect.vue';
import LeafletMap from '../components/LeafletMap.vue';
import StatusBadge from '../components/StatusBadge.vue';
import { api } from '../api';
import { dialogs } from '../dialogs';
import { formatTime, generatePassword, hasInput, saveChecked } from '../helpers';
import { state } from '../store';

const SLOTS = '0123456789ABCDEF'.split('');
const route = useRoute();
const router = useRouter();
const id = route.params.id;

const form = reactive({
	name: '', authKey: '', power: 1, usage: 'PERSONAL', antennaType: 'OMNI', antennaDirection: 0,
	antennaAboveGroundLevel: 0, antennaGainDbi: 0, identificationAddress: 8, ownerNames: [state.user.name]
});
const pos = reactive({ lat: 0, lng: 0 });
const slots = ref(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']);
const disabled = ref(false);
const showKey = ref(false);
const users = ref([]);
const info = ref(null);

api.get('users').then((r) => { users.value = r.map((u) => u.name); }).catch(() => {});

if (id) {
	api.get('transmitters/' + encodeURIComponent(id)).then((t) => {
		Object.keys(form).forEach((k) => { if (t[k] !== undefined && t[k] !== null) form[k] = t[k]; });
		form.power = parseFloat(t.power);
		pos.lat = parseFloat(t.latitude);
		pos.lng = parseFloat(t.longitude);
		slots.value = (t.timeSlot || '').split('');
		disabled.value = t.status === 'DISABLED';
		info.value = t;
	}).catch(() => router.push('/transmitters'));
}

async function copy() {
	try {
		await navigator.clipboard.writeText(form.authKey);
		dialogs.success();
	} catch (e) {
		// clipboard blocked (http or permissions)
	}
}

function submit() {
	if (!hasInput({ name: form.name, authKey: form.authKey, ownerNames: form.ownerNames, slots: slots.value })) return;
	if (!/^[A-Za-z0-9]+$/.test(form.authKey)) {
		dialogs.error('Forbidden character', 'The auth key may only contain <code>A-Z</code>, <code>a-z</code> and <code>0-9</code>.');
		return;
	}
	if (!Number.isFinite(pos.lat) || !Number.isFinite(pos.lng)) {
		dialogs.error('Invalid location', 'Please check latitude and longitude.');
		return;
	}
	const body = {
		...form,
		latitude: String(+pos.lat.toFixed(6)),
		longitude: String(+pos.lng.toFixed(6)),
		power: String(form.power),
		timeSlot: SLOTS.filter((s) => slots.value.includes(s)).join(''),
		status: disabled.value ? 'DISABLED' : 'OFFLINE'
	};
	delete body.name;
	saveChecked(router, id, 'transmitters/' + encodeURIComponent(form.name.trim().toLowerCase()), body, '/transmitters');
}
</script>
