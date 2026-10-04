import { defineConfig } from 'vite';

// Relative asset paths work on both repository Pages and a custom domain.
export default defineConfig({ base: './', build: { target: 'es2022' } });
