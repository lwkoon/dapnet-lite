<template>
	<div class="btn-group btn-group-sm">
		<button v-if="onEdit" @click="onEdit" class="btn btn-outline-primary" :title="$t('table.actionbuttons.edit')"><i class="bi bi-pencil"></i></button>
		<button v-if="onDelete" @click="onDelete" class="btn btn-outline-danger" :title="$t('table.actionbuttons.delete')"><i class="bi bi-trash"></i></button>
		<button v-if="onMail" @click="onMail" class="btn btn-outline-secondary" :title="$t('table.actionbuttons.email')"><i class="bi bi-envelope"></i></button>
		<button v-if="onRubrics" @click="onRubrics" class="btn btn-outline-secondary" :title="$t('table.actionbuttons.rubrics')"><i class="bi bi-journal-text"></i></button>
	</div>
</template>

<script setup>
defineProps({ onEdit: Function, onDelete: Function, onMail: Function, onRubrics: Function });
</script>
