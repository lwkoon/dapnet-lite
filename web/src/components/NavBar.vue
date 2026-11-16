<template>
	<nav class="navbar navbar-expand-lg navbar-dark app-navbar sticky-top">
		<div class="container">
			<router-link to="/" class="navbar-brand d-flex align-items-center gap-2">
				<img src="/favicon.svg" alt="" width="26" height="26"> DAPNET <span class="brand-lite">Lite</span>
			</router-link>
			<button class="navbar-toggler" type="button" @click="open = !open" aria-label="Toggle navigation">
				<span class="navbar-toggler-icon"></span>
			</button>
			<div class="collapse navbar-collapse" :class="{ show: open }" @click="closeOnLink">
				<ul v-if="isLoggedIn" class="navbar-nav me-auto">
					<li class="nav-item"><router-link class="nav-link" to="/calls">{{ $t('navigation.calls') }}</router-link></li>
					<li class="nav-item"><router-link class="nav-link" to="/subscribers">{{ $t('navigation.subscribers') }}</router-link></li>
					<Dropdown :label="$t('navigation.rubrics.title')">
						<router-link class="dropdown-item" to="/rubrics">{{ $t('navigation.rubrics.all') }}</router-link>
						<router-link class="dropdown-item" to="/rubrics/activate">{{ $t('navigation.rubrics.activate') }}</router-link>
						<hr class="dropdown-divider">
						<router-link class="dropdown-item" to="/rubrics/content">{{ $t('navigation.rubrics.content') }}</router-link>
					</Dropdown>
					<Dropdown :label="$t('navigation.transmitters.title')">
						<router-link class="dropdown-item" to="/transmitters">{{ $t('navigation.transmitters.all') }}</router-link>
						<router-link class="dropdown-item" to="/transmitters/map">{{ $t('navigation.transmitters.map') }}</router-link>
						<hr class="dropdown-divider">
						<router-link class="dropdown-item" to="/transmitters/groups">{{ $t('navigation.transmitters.groups') }}</router-link>
					</Dropdown>
					<li class="nav-item"><router-link class="nav-link" to="/nodes">{{ $t('navigation.nodes') }}</router-link></li>
					<li class="nav-item"><router-link class="nav-link" to="/users">{{ $t('navigation.users') }}</router-link></li>
				</ul>
				<ul v-else class="navbar-nav me-auto"></ul>
				<ul class="navbar-nav">
					<Dropdown :label="$t('footer.language.' + (state.language || 'en'))" icon="bi-translate" end>
						<button v-for="[code] in LANGUAGES" :key="code" class="dropdown-item" @click="state.language = code">
							{{ $t('footer.language.' + code) }}
						</button>
					</Dropdown>
					<Dropdown :label="state.user.name" icon="bi-person-circle" end>
						<template v-if="isLoggedIn">
							<router-link class="dropdown-item" :to="'/users/edit/' + state.user.name">{{ $t('navigation.settings') }}</router-link>
							<hr class="dropdown-divider">
							<router-link class="dropdown-item" to="/logout">{{ $t('navigation.logout') }}</router-link>
						</template>
						<router-link v-else class="dropdown-item" to="/login">{{ $t('navigation.login') }}</router-link>
					</Dropdown>
				</ul>
			</div>
		</div>
	</nav>
</template>

<script setup>
import { ref } from 'vue';
import Dropdown from './Dropdown.vue';
import { state, isLoggedIn } from '../store';
import { LANGUAGES } from '../i18n';

const open = ref(false);

function closeOnLink(e) {
	if (e.target.closest('a.nav-link:not(.dropdown-toggle), .dropdown-item')) open.value = false;
}
</script>
