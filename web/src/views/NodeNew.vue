<template>
	<Page :title="$t('navigation.nodes')" :info="$t('nodes.new.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ id ? $t('nodes.new.editnode') : $t('nodes.new.newnode') }}</h2>
			<div class="row g-3 mb-3">
				<div class="col-md-6">
					<label class="form-label">{{ $t('nodes.new.name.title') }}</label>
					<input v-model="form.name" class="form-control" :readonly="!!id">
				</div>
				<div class="col-md-6">
					<label class="form-label">{{ $t('nodes.new.status.title') }}</label>
					<select v-model="form.status" class="form-select">
						<option value="ONLINE">{{ $t('nodes.new.status.online') }}</option>
						<option value="SUSPENDED">{{ $t('nodes.new.status.suspended') }}</option>
						<option value="UNKNOWN">UNKNOWN</option>
					</select>
				</div>
			</div>
			<div class="mb-2">
				<label class="form-label">{{ $t('general.latlong.title') }}</label>
				<div class="input-group">
					<input v-model.number="pos.lat" type="number" step="any" class="form-control" placeholder="lat">
					<input v-model.number="pos.lng" type="number" step="any" class="form-control" placeholder="lng">
				</div>
			</div>
			<div class="mb-3">
				<LeafletMap small :pick="pos" @pick="(p) => Object.assign(pos, p)" />
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.owner') }}</label>
				<MultiSelect v-model="form.ownerNames" :options="users" />
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/nodes" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
		</form>
	</Page>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Page from '../components/Page.vue';
import MultiSelect from '../components/MultiSelect.vue';
import LeafletMap from '../components/LeafletMap.vue';
import { api } from '../api';
import { hasInput, saveChecked } from '../helpers';
import { state } from '../store';

const route = useRoute();
const router = useRouter();
const id = route.params.id;
const form = reactive({ name: '', status: 'ONLINE', ownerNames: [state.user.name] });
const pos = reactive({ lat: 0, lng: 0 });
const users = ref([]);

api.get('users').then((r) => { users.value = r.map((u) => u.name); }).catch(() => {});
if (id) {
	api.get('nodes/' + encodeURIComponent(id)).then((n) => {
		Object.assign(form, { name: n.name, status: n.status, ownerNames: n.ownerNames || [] });
		pos.lat = parseFloat(n.latitude) || 0;
		pos.lng = parseFloat(n.longitude) || 0;
	}).catch(() => router.push('/nodes'));
}

function submit() {
	if (!hasInput(form)) return;
	saveChecked(router, id, 'nodes/' + encodeURIComponent(form.name.trim().toLowerCase()), {
		status: form.status, ownerNames: form.ownerNames,
		latitude: String(+pos.lat.toFixed(6)), longitude: String(+pos.lng.toFixed(6))
	}, '/nodes');
}
</script>
