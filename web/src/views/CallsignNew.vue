<template>
	<Page :title="$t('navigation.subscribers')" :info="$t('subscribers.new.information.help')">
		<form class="panel" @submit.prevent="submit">
			<h2 class="h5 mb-3">{{ id ? $t('subscribers.new.editsubscriber') : $t('subscribers.new.newsubscriber') }}</h2>
			<div class="mb-3">
				<label class="form-label">{{ $t('navigation.subscribers') }}</label>
				<input v-model="form.name" class="form-control" :readonly="!!id">
				<div class="form-text">{{ $t('subscribers.new.subscriber.help') }}</div>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('general.description') }}</label>
				<input v-model="form.description" class="form-control" maxlength="60">
				<div class="form-text">{{ $t('subscribers.new.description.help') }}</div>
			</div>
			<div class="row g-3 mb-3">
				<div class="col-md-6">
					<label class="form-label">{{ $t('subscribers.new.pager.title') }} — RIC</label>
					<textarea v-model="form.numbers" class="form-control font-monospace" rows="5" placeholder="0123456"></textarea>
					<div class="form-text">{{ $t('subscribers.new.pager.helprics') }}</div>
				</div>
				<div class="col-md-6">
					<label class="form-label">{{ $t('subscribers.new.pager.title') }} — {{ $t('general.name') }}</label>
					<textarea v-model="form.names" class="form-control" rows="5" placeholder="Skyper"></textarea>
					<div class="form-text">{{ $t('subscribers.new.pager.helpnames') }}</div>
				</div>
			</div>
			<div class="form-check mb-3">
				<input id="numeric" class="form-check-input" type="checkbox" v-model="form.numeric">
				<label for="numeric" class="form-check-label">Numeric-only pager</label>
			</div>
			<div class="mb-3">
				<label class="form-label">{{ $t('subscribers.new.owner.title') }}</label>
				<MultiSelect v-model="form.ownerNames" :options="users" />
				<div class="form-text">{{ $t('subscribers.new.owner.help') }}</div>
			</div>
			<button type="submit" class="btn btn-primary me-2">{{ $t('general.submit') }}</button>
			<router-link to="/subscribers" class="btn btn-outline-secondary">{{ $t('general.abort') }}</router-link>
		</form>
	</Page>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Page from '../components/Page.vue';
import MultiSelect from '../components/MultiSelect.vue';
import { api } from '../api';
import { dialogs, escapeHtml } from '../dialogs';
import { hasInput, saveChecked, zeroPad } from '../helpers';
import { state } from '../store';

const route = useRoute();
const router = useRouter();
const id = route.params.id;
const form = reactive({ name: '', description: '', numbers: '', names: '', numeric: false, ownerNames: [state.user.name] });
const users = ref([]);
const knownRics = ref(new Map());

api.get('users').then((r) => { users.value = r.map((u) => u.name); }).catch(() => { users.value = [state.user.name]; });
api.get('callsigns').then((r) => {
	r.forEach((c) => (c.pagers || []).forEach((p) => knownRics.value.set(p.number, c.name)));
}).catch(() => {});

if (id) {
	api.get('callsigns/' + encodeURIComponent(id)).then((c) => {
		Object.assign(form, {
			name: c.name,
			description: c.description,
			numeric: !!c.numeric,
			numbers: (c.pagers || []).map((p) => zeroPad(p.number, 7)).join('\n'),
			names: (c.pagers || []).map((p) => p.name).join('\n'),
			ownerNames: c.ownerNames
		});
	}).catch(() => router.push('/subscribers'));
}

async function submit() {
	if (!hasInput(form, ['description', 'numeric'])) return;
	const numbers = form.numbers.split('\n').map((s) => s.trim()).filter(Boolean);
	const pagerNames = form.names.split('\n').map((s) => s.trim());
	const pagers = numbers.map((n, i) => ({ number: parseInt(n, 10), name: pagerNames[i] || form.name }));
	const body = { description: form.description, numeric: form.numeric, pagers, ownerNames: form.ownerNames };
	const url = 'callsigns/' + encodeURIComponent(form.name.trim().toLowerCase());
	const dup = pagers.find((p) => knownRics.value.has(p.number) && knownRics.value.get(p.number) !== (id || '').toLowerCase());
	if (dup) {
		dialogs.confirm('Duplicate pager RIC',
			'The given pager RIC (' + escapeHtml(dup.number) + ') is already used by ' + escapeHtml(knownRics.value.get(dup.number)) + '.',
			() => saveChecked(router, id, url, body, '/subscribers'), "I know what I'm doing");
		return;
	}
	saveChecked(router, id, url, body, '/subscribers');
}
</script>
