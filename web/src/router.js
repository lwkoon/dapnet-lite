import { createRouter, createWebHistory } from 'vue-router';
import { isLoggedIn } from './store';
import { t } from './i18n';

const v = (name) => () => import(`./views/${name}.vue`);

const routes = [
	{ path: '/', component: v('Home'), meta: { title: 'pagetitle.home' } },
	{ path: '/login', component: v('Login'), meta: { title: 'navigation.login' } },
	{ path: '/logout', component: v('Logout'), meta: { auth: true, title: 'navigation.logout' } },
	{ path: '/calls', component: v('CallOverview'), meta: { auth: true, title: 'navigation.calls' } },
	{ path: '/calls/new', component: v('CallNew'), meta: { auth: true, title: 'navigation.calls' } },
	{ path: '/subscribers', component: v('CallsignOverview'), meta: { auth: true, title: 'navigation.subscribers' } },
	{ path: '/subscribers/new', component: v('CallsignNew'), meta: { auth: true, title: 'navigation.subscribers' } },
	{ path: '/subscribers/edit/:id', component: v('CallsignNew'), meta: { auth: true, title: 'navigation.subscribers' } },
	{ path: '/rubrics', component: v('RubricOverview'), meta: { auth: true, title: 'navigation.rubrics.title' } },
	{ path: '/rubrics/new', component: v('RubricNew'), meta: { auth: true, title: 'navigation.rubrics.title' } },
	{ path: '/rubrics/edit/:id', component: v('RubricNew'), meta: { auth: true, title: 'navigation.rubrics.title' } },
	{ path: '/rubrics/activate', component: v('RubricActivation'), meta: { auth: true, title: 'navigation.rubrics.activate' } },
	{ path: '/rubrics/content', component: v('NewsOverview'), meta: { auth: true, title: 'navigation.rubrics.content' } },
	{ path: '/rubrics/content/new', component: v('NewsNew'), meta: { auth: true, title: 'navigation.rubrics.content' } },
	{ path: '/transmitters', component: v('TransmitterOverview'), meta: { auth: true, title: 'navigation.transmitters.title' } },
	{ path: '/transmitters/new', component: v('TransmitterNew'), meta: { auth: true, title: 'navigation.transmitters.title' } },
	{ path: '/transmitters/edit/:id', component: v('TransmitterNew'), meta: { auth: true, title: 'navigation.transmitters.title' } },
	{ path: '/transmitters/map/:id?', component: v('TransmitterMap'), meta: { auth: true, title: 'navigation.transmitters.map' } },
	{ path: '/transmitters/groups', component: v('GroupOverview'), meta: { auth: true, title: 'navigation.transmitters.groups' } },
	{ path: '/transmitters/groups/new', component: v('GroupNew'), meta: { auth: true, title: 'navigation.transmitters.groups' } },
	{ path: '/transmitters/groups/edit/:id', component: v('GroupNew'), meta: { auth: true, title: 'navigation.transmitters.groups' } },
	{ path: '/nodes', component: v('NodeOverview'), meta: { auth: true, title: 'navigation.nodes' } },
	{ path: '/nodes/new', component: v('NodeNew'), meta: { auth: true, title: 'navigation.nodes' } },
	{ path: '/nodes/edit/:id', component: v('NodeNew'), meta: { auth: true, title: 'navigation.nodes' } },
	{ path: '/users', component: v('UserOverview'), meta: { auth: true, title: 'navigation.users' } },
	{ path: '/users/new', component: v('UserNew'), meta: { auth: true, title: 'navigation.users' } },
	{ path: '/users/edit/:id', component: v('UserNew'), meta: { auth: true, title: 'navigation.users' } },
	{ path: '/:pathMatch(.*)*', component: v('NotFound'), meta: { title: 'pagetitle.notfound' } }
];

const router = createRouter({ history: createWebHistory(), routes, linkActiveClass: 'active' });

router.beforeEach((to) => {
	if (to.meta.auth && !isLoggedIn.value) return { path: '/login', query: { next: to.fullPath } };
	return true;
});

router.afterEach((to) => {
	const title = to.meta.title ? t(to.meta.title) : '';
	document.title = (title && !title.startsWith('pagetitle.') ? title + ' | ' : '') + 'DAPNET Lite';
});

export default router;
