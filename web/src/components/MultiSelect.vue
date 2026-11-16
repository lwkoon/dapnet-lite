<template>
	<div class="multiselect" ref="root">
		<div class="form-control d-flex flex-wrap gap-1 align-items-center" @click="focusInput">
			<span v-for="item in selected" :key="item" class="badge text-bg-primary d-inline-flex align-items-center">
				{{ item }}
				<button type="button" class="btn-close btn-close-white ms-1" aria-label="Remove" @click.stop="remove(item)"></button>
			</span>
			<input ref="input" v-model="query" class="ms-input" :placeholder="selected.length ? '' : 'Type to search'"
				@focus="open = true" @keydown.enter.prevent="pickFirst" @keydown.backspace="backspace" @keydown.esc="open = false">
		</div>
		<ul v-if="open && options.length" class="dropdown-menu show w-100 ms-menu">
			<li v-for="opt in options" :key="opt"><button type="button" class="dropdown-item" @mousedown.prevent="add(opt)">{{ opt }}</button></li>
		</ul>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

// v-model is an array of names; `multiple=false` turns it into a single string.
const props = defineProps({ modelValue: [Array, String], options: Array, multiple: { type: Boolean, default: true } });
const emit = defineEmits(['update:modelValue']);

const query = ref('');
const open = ref(false);
const root = ref(null);
const input = ref(null);

const selected = computed(() => {
	if (props.multiple) return props.modelValue || [];
	return props.modelValue ? [props.modelValue] : [];
});

const options = computed(() => {
	const q = query.value.toLowerCase();
	return (props.options || []).filter((o) => !selected.value.includes(o) && o.toLowerCase().includes(q)).slice(0, 50);
});

function set(list) {
	emit('update:modelValue', props.multiple ? list : (list[list.length - 1] || ''));
}

function add(opt) {
	set(props.multiple ? [...selected.value, opt] : [opt]);
	query.value = '';
	if (!props.multiple) open.value = false;
}

function remove(item) {
	set(selected.value.filter((x) => x !== item));
}

function pickFirst() {
	if (options.value.length) add(options.value[0]);
}

function backspace() {
	if (!query.value && selected.value.length) remove(selected.value[selected.value.length - 1]);
}

function focusInput() {
	input.value && input.value.focus();
}

function outside(e) {
	if (root.value && !root.value.contains(e.target)) open.value = false;
}

onMounted(() => document.addEventListener('click', outside));
onBeforeUnmount(() => document.removeEventListener('click', outside));
</script>
