<template>
	<h2 class="h4 d-flex align-items-center gap-2">
		{{ title }}
		<button class="btn btn-sm btn-link p-0" :title="'Reload'" @click="$emit('reload')">
			<i class="bi bi-arrow-clockwise" :class="{ spin: running }"></i>
		</button>
	</h2>
	<div v-if="error" class="alert alert-danger">
		<b>{{ $t('rest.errors.title') }}</b><br>{{ error }}
	</div>
</template>

<script setup>
defineProps({ title: String, running: Boolean, error: [String, Boolean] });
defineEmits(['reload']);
</script>
