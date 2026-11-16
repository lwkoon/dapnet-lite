<template>
	<Page :title="$t('navigation.rubrics.title')" :info="$t('rubric.new.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ id ? $t('rubric.new.editrubric') : $t('rubric.new.newrubric') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('rubric.new.name') }}</label>
				<input v-model="form.name" class="form-control" :readonly="!!id">
			</div>
			<div class="row g-3 mb-3">
				<div class="col-md-8">
					<label class="form-label">{{ $t('rubric.new.label') }}</label>
					<input v-model="form.label" class="form-control" maxlength="11">
				</div>
				<div class="col-md-4">
					<label class="form-label">{{ $t('rubric.new.number') }}</label>
					<input v-model.number="form.number" type="number" min="1" max="95" class="form-control" placeholder="1 - 95">
				</div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('rubric.new.transmittergroup') }}</label>
				<MultiSelect v-model="form.transmitterGroupNames" :options="groups" />
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.owner') }}</label>
				<MultiSelect v-model="form.ownerNames" :options="users" />
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/rubrics" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
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
const form = reactive({ name: '', label: '', number: 1, transmitterGroupNames: [], ownerNames: [state.user.name] });
const groups = ref([]);
const users = ref([]);

api.get('transmitterGroups').then((r) => { groups.value = r.map((g) => g.name); }).catch(() => {});
api.get('users').then((r) => { users.value = r.map((u) => u.name); }).catch(() => {});
if (id) {
	api.get('rubrics/' + encodeURIComponent(id)).then((r) => Object.assign(form, r)).catch(() => router.push('/rubrics'));
}

function submit() {
	if (!hasInput(form)) return;
	const { label, number, transmitterGroupNames, ownerNames } = form;
	saveChecked(router, id, 'rubrics/' + encodeURIComponent(form.name.trim().toLowerCase()),
		{ label, number, transmitterGroupNames, ownerNames }, '/rubrics');
}
</script>
