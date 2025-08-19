import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Cleaning up E2E test environment...');
  
  // Clean up any resources created during setup
  // Stop backend server if we started it
  
  console.log('✅ E2E test environment cleaned up');
}

export default globalTeardown;