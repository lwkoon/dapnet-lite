<template>
	<div v-if="dialog.open" class="modal-backdrop-lite" @click.self="close">
		<div class="modal-lite card shadow" role="dialog" aria-modal="true">
			<div class="card-body text-center">
				<i class="bi fs-1" :class="icon"></i>
				<h4 class="mt-2">{{ dialog.title }}</h4>
				<div class="mb-3" v-html="dialog.html"></div>
				<button v-if="dialog.confirm" class="btn btn-danger me-2" @click="run">{{ dialog.confirmText }}</button>
				<button class="btn" :class="dialog.confirm ? 'btn-outline-secondary' : 'btn-primary'" @click="close">
					{{ dialog.confirm ? $t('general.abort') : 'OK' }}
				</button>
			</div>
		</div>
	</div>
	<div class="toast-stack">
		<div v-for="toast in toasts" :key="toast.id" class="alert alert-success shadow-sm py-2 mb-2">
			<i class="bi bi-check-circle me-1"></i><b>{{ toast.title }}</b> — {{ toast.text }}
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue';
import { dialog, toasts, close } from '../dialogs';

const icon = computed(() => ({
	error: 'bi-x-circle text-danger',
	warning: 'bi-exclamation-triangle text-warning',
	info: 'bi-info-circle text-info'
}[dialog.kind]));

function run() {
	const fn = dialog.confirm;
	close();
	if (fn) fn();
}
</script>
