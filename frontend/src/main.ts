// Vue 3 完整版入口 (Vite)
// 当前 Phase 1 MVP 用 CDN 单文件版 (index.html) 演示, 此文件作为 Vite 迁移目标
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
