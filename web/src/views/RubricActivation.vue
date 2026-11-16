<template>
	<Page :title="$t('navigation.rubrics.title')" :info="$t('rubric.activation.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ $t('navigation.rubrics.activate') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('rubric.activation.pagernumber') }}</label>
				<input v-model.number="form.number" type="number" min="0" max="2097151" class="form-control" placeholder="0 - 2097151">
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('rubric.activation.transmittergroup') }}</label>
				<MultiSelect v-model="form.transmitterGroupNames" :options="groups" />
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/rubrics" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
		</form>
	</Page>
</template>

<script setup>
import { reactive, ref } from 'vue';
import Page from '../components/Page.vue';
import MultiSelect from '../components/MultiSelect.vue';
import { api } from '../api';
import { dialogs } from '../dialogs';
import { hasInput } from '../helpers';

const form = reactive({ number: 1, transmitterGroupNames: [] });
const groups = ref([]);
api.get('transmitterGroups').then((r) => { groups.value = r.map((g) => g.name); }).catch(dialogs.ajaxError);

async function submit() {
	if (!hasInput(form)) return;
	try {
		await api.post('activation', form);
		dialogs.success();
	} catch (e) {
		dialogs.ajaxError(e);
	}
}
</script>
