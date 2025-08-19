#!/usr/bin/env node
/**
 * Comprehensive test runner for SoftBankCashWire frontend
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class TestRunner {
  constructor() {
    this.results = [];
  }

  async runCommand(command, args, description) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Running: ${description}`);
    console.log(`Command: ${command} ${args.join(' ')}`);
    console.log(`${'='.repeat(60)}`);

    const startTime = Date.now();

    return new Promise((resolve) => {
      const process = spawn(command, args, {
        stdio: 'inherit',
        shell: true
      });

      process.on('close', (code) => {
        const duration = (Date.now() - startTime) / 1000;
        console.log(`\n${description} completed in ${duration.toFixed(2)} seconds`);

        if (code === 0) {
          console.log(`✅ ${description} PASSED`);
          this.results.push({ name: description, success: true });
        } else {
          console.log(`❌ ${description} FAILED`);
          this.results.push({ name: description, success: false });
        }

        resolve(code === 0);
      });
    });
  }

  async runUnitTests() {
    return this.runCommand('npm', ['run', 'test', '--', '--watchAll=false', '--coverage=false'], 'Unit Tests');
  }

  async runComponentTests() {
    return this.runCommand('npm', ['run', 'test', '--', '--watchAll=false', '--testPathPattern=components/__tests__'], 'Component Tests');
  }

  async runCoverageTests() {
    return this.runCommand('npm', ['run', 'test:coverage', '--', '--watchAll=false'], 'Coverage Tests');
  }

  async runE2ETests() {
    // Check if Playwright is available
    if (fs.existsSync('playwright.config.js') || fs.existsSync('playwright.config.ts')) {
      return this.runCommand('npx', ['playwright', 'test'], 'End-to-End Tests');
    } else {
      console.log('⚠️  Playwright not configured, skipping E2E tests');
      return true;
    }
  }

  async runLinting() {
    return this.runCommand('npm', ['run', 'lint'], 'ESLint');
  }

  async runTypeChecking() {
    return this.runCommand('npx', ['tsc', '--noEmit'], 'TypeScript Type Checking');
  }

  async runAccessibilityTests() {
    // Run accessibility tests if axe-core is available
    const axeTestPath = path.join(__dirname, 'src', '__tests__', 'accessibility.test.tsx');
    if (fs.existsSync(axeTestPath)) {
      return this.runCommand('npm', ['run', 'test', '--', '--testPathPattern=accessibility'], 'Accessibility Tests');
    } else {
      console.log('⚠️  Accessibility tests not found, skipping');
      return true;
    }
  }

  async runQuickTests() {
    console.log('🚀 Running quick smoke tests...');
    return this.runCommand('npm', ['run', 'test', '--', '--watchAll=false', '--testPathPattern=Dashboard|SendMoney|AuthGuard'], 'Quick Smoke Tests');
  }

  async runAllTests() {
    console.log('🚀 Starting comprehensive test suite for SoftBankCashWire frontend');

    const testSuites = [
      ['Type Checking', () => this.runTypeChecking()],
      ['Linting', () => this.runLinting()],
      ['Unit Tests', () => this.runUnitTests()],
      ['Component Tests', () => this.runComponentTests()],
      ['Accessibility Tests', () => this.runAccessibilityTests()],
      ['End-to-End Tests', () => this.runE2ETests()],
    ];

    for (const [suiteName, testFunction] of testSuites) {
      console.log(`\n🔄 Starting ${suiteName}...`);
      const success = await testFunction();
      
      if (!success) {
        console.log(`⚠️  ${suiteName} failed, but continuing with other tests...`);
      }
    }

    this.generateReport();
    return this.results.every(result => result.success);
  }

  generateReport() {
    console.log(`\n${'='.repeat(80)}`);
    console.log('📊 FINAL TEST REPORT');
    console.log(`${'='.repeat(80)}`);

    let passed = 0;
    let failed = 0;

    this.results.forEach(result => {
      const status = result.success ? '✅ PASSED' : '❌ FAILED';
      console.log(`${result.name.padEnd(25)} ${status}`);
      if (result.success) {
        passed++;
      } else {
        failed++;
      }
    });

    console.log(`\n📈 Summary: ${passed} passed, ${failed} failed out of ${this.results.length} test suites`);

    if (failed === 0) {
      console.log('🎉 All test suites passed!');
    } else {
      console.log(`⚠️  ${failed} test suite(s) failed`);
    }
  }

  async setupTestEnvironment() {
    console.log('🔧 Setting up test environment...');

    // Check if node_modules exists
    if (!fs.existsSync('node_modules')) {
      console.log('📦 Installing dependencies...');
      await this.runCommand('npm', ['install'], 'Installing Dependencies');
    }

    // Set test environment variables
    process.env.NODE_ENV = 'test';
    process.env.CI = 'true';

    console.log('✅ Test environment ready');
  }
}

async function main() {
  const args = process.argv.slice(2);
  const runner = new TestRunner();

  // Parse command line arguments
  const suite = args.find(arg => arg.startsWith('--suite='))?.split('=')[1] || 'all';
  const skipSetup = args.includes('--no-setup');
  const specificTest = args.find(arg => arg.startsWith('--test='))?.split('=')[1];

  // Setup test environment unless explicitly skipped
  if (!skipSetup) {
    await runner.setupTestEnvironment();
  }

  let success = false;

  // Run specific test if provided
  if (specificTest) {
    success = await runner.runCommand('npm', ['run', 'test', '--', '--testPathPattern=' + specificTest], `Specific Test: ${specificTest}`);
    process.exit(success ? 0 : 1);
  }

  // Run selected test suite
  switch (suite) {
    case 'unit':
      success = await runner.runUnitTests();
      break;
    case 'component':
      success = await runner.runComponentTests();
      break;
    case 'coverage':
      success = await runner.runCoverageTests();
      break;
    case 'e2e':
      success = await runner.runE2ETests();
      break;
    case 'lint':
      success = await runner.runLinting();
      break;
    case 'type':
      success = await runner.runTypeChecking();
      break;
    case 'a11y':
      success = await runner.runAccessibilityTests();
      break;
    case 'quick':
      success = await runner.runQuickTests();
      break;
    case 'all':
      success = await runner.runAllTests();
      break;
    default:
      console.log(`Unknown test suite: ${suite}`);
      console.log('Available suites: unit, component, coverage, e2e, lint, type, a11y, quick, all');
      process.exit(1);
  }

  process.exit(success ? 0 : 1);
}

// Show help if requested
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
SoftBankCashWire Frontend Test Runner

Usage: node run_tests.js [options]

Options:
  --suite=<suite>    Test suite to run (default: all)
                     Available: unit, component, coverage, e2e, lint, type, a11y, quick, all
  --test=<pattern>   Run specific test matching pattern
  --no-setup         Skip test environment setup
  --help, -h         Show this help message

Examples:
  node run_tests.js --suite=unit
  node run_tests.js --test=Dashboard
  node run_tests.js --suite=quick --no-setup
`);
  process.exit(0);
}

main().catch(error => {
  console.error('Test runner failed:', error);
  process.exit(1);
});