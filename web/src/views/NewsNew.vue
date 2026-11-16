<template>
	<Page :title="$t('navigation.rubrics.content')" :info="$t('news.new.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ $t('news.new.newrubriccontent') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('news.new.message') }}</label>
				<textarea v-model="form.text" rows="2" maxlength="80" class="form-control"></textarea>
				<div class="form-text">{{ 80 - form.text.length }} / 80 {{ $t('news.new.charactersremaining') }}.</div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('news.new.rubrics') }}</label>
				<MultiSelect v-model="form.rubricName" :options="rubrics" :multiple="false" />
			</div>
			<div class="row g-3 mb-3 align-items-center">
				<label class="col-md-2 form-label mb-0">{{ $t('news.new.number') }}</label>
				<div class="col-md-5">
					<div class="form-check">
						<input id="auto" class="form-check-input" type="checkbox" v-model="form.auto">
						<label for="auto" class="form-check-label">{{ $t('news.new.chooseautomatically') }}</label>
					</div>
				</div>
				<div class="col-md-5">
					<input v-model.number="form.number" :disabled="form.auto" type="number" min="1" max="10" class="form-control" placeholder="1 - 10">
				</div>
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/rubrics/content" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
		</form>
	</Page>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import Page from '../components/Page.vue';
import MultiSelect from '../components/MultiSelect.vue';
import { api } from '../api';
import { dialogs } from '../dialogs';
import { hasInput } from '../helpers';

const router = useRouter();
const form = reactive({ text: '', rubricName: '', auto: true, number: 1 });
const rubrics = ref([]);
api.get('rubrics').then((r) => { rubrics.value = r.map((x) => x.name); }).catch(dialogs.ajaxError);

async function submit() {
	if (!hasInput(form, ['auto'])) return;
	try {
		await api.post('news', { text: form.text.trim(), rubricName: form.rubricName, number: form.auto ? 0 : form.number });
		dialogs.success();
		router.push('/rubrics/content');
	} catch (e) {
		dialogs.ajaxError(e);
	}
}
</script>
