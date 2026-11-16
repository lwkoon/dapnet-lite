<template>
	<Page :title="$t('navigation.transmitters.groups')" :info="$t('group.new.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ id ? $t('group.new.edittxgroup') : $t('group.new.newtxgroup') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.name') }}</label>
				<input v-model="form.name" class="form-control" :readonly="!!id">
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.description') }}</label>
				<input v-model="form.description" class="form-control" maxlength="60">
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('navigation.transmitters.title') }}</label>
				<MultiSelect v-model="form.transmitterNames" :options="transmitters" />
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.owner') }}</label>
				<MultiSelect v-model="form.ownerNames" :options="users" />
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/transmitters/groups" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
		</form>
	</Page>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Page from '../components/Page.vue';
import MultiSelect from '../components/MultiSelect.vue';
import { api } from '../api';
import { hasInput, saveChecked } from '../helpers';
import { state } from '../store';

const route = useRoute();
const router = useRouter();
const id = route.params.id;
const form = reactive({ name: '', description: '', transmitterNames: [], ownerNames: [state.user.name] });
const transmitters = ref([]);
const users = ref([]);

api.get('transmitters').then((r) => { transmitters.value = r.map((t) => t.name); }).catch(() => {});
api.get('users').then((r) => { users.value = r.map((u) => u.name); }).catch(() => {});
if (id) {
	api.get('transmitterGroups/' + encodeURIComponent(id)).then((g) => Object.assign(form, g)).catch(() => router.push('/transmitters/groups'));
}

function submit() {
	if (!hasInput(form, ['description'])) return;
	const { description, transmitterNames, ownerNames } = form;
	saveChecked(router, id, 'transmitterGroups/' + encodeURIComponent(form.name.trim().toLowerCase()),
		{ description, transmitterNames, ownerNames }, '/transmitters/groups');
}
</script>
