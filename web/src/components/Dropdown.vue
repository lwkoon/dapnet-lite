<template>
	<li class="nav-item dropdown" ref="root">
		<a href="#" class="nav-link dropdown-toggle" role="button" :aria-expanded="open" @click.prevent="open = !open">
			<i v-if="icon" class="bi me-1" :class="icon"></i>{{ label }}
		</a>
		<div class="dropdown-menu" :class="{ show: open, 'dropdown-menu-end': end }" @click="open = false">
			<slot />
		</div>
	</li>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';

defineProps({ label: String, icon: String, end: Boolean });
const open = ref(false);
const root = ref(null);

function outside(e) {
	if (root.value && !root.value.contains(e.target)) open.value = false;
}

onMounted(() => document.addEventListener('click', outside));
onBeforeUnmount(() => document.removeEventListener('click', outside));
</script>
