<template>
	<span class="badge" :class="cls">{{ status || '---' }}</span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({ status: String });
const cls = computed(() => ({
	ONLINE: 'text-bg-success',
	OFFLINE: 'text-bg-secondary',
	DISABLED: 'text-bg-dark',
	SUSPENDED: 'text-bg-warning',
	ERROR: 'text-bg-danger'
}[props.status] || 'text-bg-warning'));
</script>
