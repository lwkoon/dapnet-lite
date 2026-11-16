import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// During `npm run dev` the API is proxied to a locally running core.
export default defineConfig({
	plugins: [vue()],
	server: {
		proxy: {
			'/api': process.env.DAPNET_API || 'http://127.0.0.1:8080'
		}
	},
	build: {
		chunkSizeWarningLimit: 600
	}
});
