<template>
	<div class="container py-5 text-center text-body-secondary">{{ $t('logout.seepagewrong') }}</div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { logout } from '../store';

logout();
useRouter().replace('/');
</script>
