<template>
	<NavBar />
	<main class="flex-grow-1">
		<router-view />
	</main>
	<footer class="app-footer py-3 mt-4">
		<div class="container d-flex flex-wrap justify-content-between gap-2 small">
			<span>DAPNET Lite {{ version }} — standalone paging core</span>
			<span>Based on <a href="https://github.com/DecentralizedAmateurPagingNetwork" target="_blank" rel="noopener">DAPNET</a> by RWTH Aachen (non-commercial, amateur radio use only)</span>
		</div>
	</footer>
	<Dialogs />
</template>

<script setup>
import { ref } from 'vue';
import NavBar from './components/NavBar.vue';
import Dialogs from './components/Dialogs.vue';
import { api } from './api';

const version = ref('');
api.get('core/version', { auth: false }).then((v) => { version.value = 'v' + v.core; }).catch(() => {});
</script>
