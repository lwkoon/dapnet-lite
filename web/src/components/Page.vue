<template>
	<div class="container py-3">
		<h1 class="page-title">{{ title }}</h1>
		<div class="row g-4">
			<div class="col-lg-9">
				<slot />
			</div>
			<div class="col-lg-3">
				<slot name="side" />
				<template v-if="info">
					<h2 class="h5 mt-3">{{ $t('general.information') }}</h2>
					<p class="text-body-secondary small" v-html="info"></p>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({ title: String, info: String });
</script>
