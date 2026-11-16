<template>
	<Page :title="$t('navigation.calls')" :info="$t('calls.new.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ $t('calls.new.newcall') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('calls.new.message.title') }}</label>
				<textarea class="form-control" rows="2" maxlength="80" v-model="form.text"></textarea>
				<div class="form-text" v-html="$t('calls.new.message.charactersremaining', { remaining: 80 - form.text.length })"></div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('navigation.subscribers') }}</label>
				<MultiSelect v-model="form.callSignNames" :options="callsigns" />
				<div class="form-text">{{ $t('calls.new.subscribers.help') }}</div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('navigation.transmitters.groups') }}</label>
				<MultiSelect v-model="form.transmitterGroupNames" :options="groups" />
				<div class="form-text">{{ $t('calls.new.transmittergroups.help') }}</div>
			</div>
			<div class="form-check mb-3">
				<input id="emergency" class="form-check-input" type="checkbox" v-model="form.emergency">
				<label for="emergency" class="form-check-label">{{ $t('calls.new.emergency.title') }}</label>
				<div class="form-text">{{ $t('calls.new.emergency.help') }}</div>
			</div>
			<button type="submit" class="btn btn-primary me-2"><i class="bi bi-send me-1"></i>{{ $t('general.submit') }}</button>
			<router-link to="/calls" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
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
import { state } from '../store';

const router = useRouter();
const form = reactive({
	text: state.user.name.toUpperCase() + ': ',
	callSignNames: [],
	transmitterGroupNames: [],
	emergency: false
});
const callsigns = ref([]);
const groups = ref([]);

api.get('callsigns').then((r) => { callsigns.value = r.map((c) => c.name); }).catch(dialogs.ajaxError);
api.get('transmitterGroups').then((r) => {
	groups.value = r.map((g) => g.name);
	if (groups.value.includes('all')) form.transmitterGroupNames = ['all'];
}).catch(dialogs.ajaxError);

async function submit() {
	if (!hasInput(form, ['emergency'])) return;
	try {
		await api.post('calls', { ...form, text: form.text.trim() });
		dialogs.success();
		router.push('/calls');
	} catch (e) {
		dialogs.ajaxError(e);
	}
}
</script>
