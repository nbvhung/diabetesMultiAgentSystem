import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./e2e', timeout:90000, workers:1, retries:0,
  reporter:[['list'],['json',{outputFile:process.env.UI_QA_REPORT_FILE || '../docs/validation/diabetes_expansion/browser-results.json'}]],
  use:{baseURL:process.env.UI_QA_BASE_URL || 'http://127.0.0.1:5173',viewport:{width:1440,height:1100},screenshot:'only-on-failure',trace:'retain-on-failure',
    launchOptions:process.env.PHASE07_CHROMIUM_PATH ? {executablePath:process.env.PHASE07_CHROMIUM_PATH}:{}},
  webServer:process.env.PHASE07_EXTERNAL_SERVERS ? undefined : [
    {command:'python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000',cwd:'..',url:'http://127.0.0.1:8000/health',timeout:120000,reuseExistingServer:false,env:{DIABETES_LLM_ENABLED:'false'}},
    {command:'python -m uvicorn scripts.phase07_fault_app:knowledge_down --factory --host 127.0.0.1 --port 8001',cwd:'..',url:'http://127.0.0.1:8001/health',timeout:120000,reuseExistingServer:false,env:{DIABETES_LLM_ENABLED:'false'}},
    {command:'npm run dev -- --strictPort',url:'http://127.0.0.1:5173',timeout:120000,reuseExistingServer:!process.env.CI},
  ],
});
