# Test Execution Guide

This guide provides instructions for running and troubleshooting the comprehensive test suites for SoftBankCashWire.

## Frontend Tests

### Prerequisites
- Node.js 18+ installed
- Dependencies installed: `cd frontend && npm install`

### Running Frontend Tests

#### All Tests
```bash
cd frontend
npm test
```

#### Specific Test Suites
```bash
# Component tests only
npm run test:component

# Coverage report
npm run test:coverage

# Watch mode
npm run test:watch

# E2E tests
npm run test:e2e
```

#### Individual Test Files
```bash
# Dashboard tests
npm test -- --testPathPattern="Dashboard.test.tsx"

# AuthGuard tests
npm test -- --testPathPattern="AuthGuard.test.tsx"

# SendMoney tests
npm test -- --testPathPattern="SendMoney.test.tsx"
```

### Common Frontend Test Issues and Fixes

#### Issue 1: AccessibilityProvider Missing
**Error**: `useAccessibility must be used within an AccessibilityProvider`

**Fix**: Ensure test components are wrapped with AccessibilityProvider:
```tsx
const TestWrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <AccessibilityProvider>
        {children}
      </AccessibilityProvider>
    </BrowserRouter>
  </QueryClientProvider>
);
```

#### Issue 2: Mock Service Methods Missing
**Error**: `Cannot read properties of undefined (reading 'mockResolvedValue')`

**Fix**: Add missing methods to service mocks in `src/services/__mocks__/`

#### Issue 3: Jest Configuration Issues
**Error**: `import.meta` not defined

**Fix**: Update `jest.config.js` with proper ESM support and globals configuration.

## Backend Tests

### Prerequisites
- Python 3.11+ installed
- Virtual environment activated: `cd backend && source venv/bin/activate`
- Dependencies installed: `pip install -r requirements.txt`

### Running Backend Tests

#### All Tests
```bash
cd backend
python -m pytest
```

#### Specific Test Categories
```bash
# Unit tests only
python -m pytest -m unit

# Integration tests only
python -m pytest -m integration

# Security tests only
python -m pytest -m security

# Performance tests only
python -m pytest -m performance
```

#### Individual Test Files
```bash
# Transaction service tests
python -m pytest tests/test_transaction_service.py -v

# Auth service tests
python -m pytest tests/test_auth_service.py -v

# API integration tests
python -m pytest tests/test_api_integration.py -v
```

#### With Coverage
```bash
python -m pytest --cov=services --cov=models --cov=api --cov-report=html
```

### Common Backend Test Issues and Fixes

#### Issue 1: AuditService Method Signature Errors
**Error**: `AuditService.log_user_action() got an unexpected keyword argument 'action'`

**Fix**: Use correct parameter names:
```python
# Wrong
AuditService.log_user_action(user_id=user_id, action='LOGIN_SUCCESS')

# Correct
AuditService.log_user_action(user_id=user_id, action_type='LOGIN_SUCCESS', entity_type='User')
```

#### Issue 2: Database Constraint Violations
**Error**: `CHECK constraint failed: ck_accounts_ck_account_max_balance`

**Fix**: Ensure test data respects account balance limits (-£250 to £250):
```python
# Create test account with valid balance
account = Account(user_id=user.id, balance=Decimal('100.00'))
```

#### Issue 3: Missing JWT Attribute
**Error**: `module 'services.auth_service' has no attribute 'jwt'`

**Fix**: Mock JWT properly in integration tests:
```python
@patch('services.auth_service.jwt')
def test_protected_endpoint(self, mock_jwt):
    mock_jwt.decode.return_value = {'user_id': 'test-user-id'}
```

#### Issue 4: Connection Refused Errors
**Error**: `HTTPConnectionPool(host='localhost', port=5000): Max retries exceeded`

**Fix**: These are integration tests that require the Flask app to be running. Either:
1. Start the Flask app: `python app.py`
2. Skip integration tests: `python -m pytest -m "not integration"`

## E2E Tests

### Prerequisites
- Both frontend and backend running
- Playwright installed: `cd frontend && npx playwright install`

### Running E2E Tests
```bash
cd frontend
npm run test:e2e
```

### E2E Test Configuration
E2E tests are configured in `frontend/playwright.config.ts` and located in `frontend/tests/e2e/`.

## Test Database Setup

### Backend Test Database
Backend tests use an in-memory SQLite database that's created and destroyed for each test. No manual setup required.

### Frontend Test Mocking
Frontend tests use Jest mocks for API calls. Service mocks are located in `frontend/src/services/__mocks__/`.

## Coverage Reports

### Frontend Coverage
```bash
cd frontend
npm run test:coverage
```
Coverage reports are generated in `frontend/coverage/`.

### Backend Coverage
```bash
cd backend
python -m pytest --cov=services --cov=models --cov=api --cov-report=html
```
Coverage reports are generated in `backend/htmlcov/`.

## Troubleshooting Common Issues

### 1. Tests Timing Out
- Increase Jest timeout in `jest.config.js`
- Check for infinite loops in components
- Ensure mocks are properly configured

### 2. Mock Issues
- Verify mock files exist in `__mocks__` directories
- Check mock function signatures match real implementations
- Clear Jest cache: `npm test -- --clearCache`

### 3. Database Issues
- Ensure test database is properly isolated
- Check for transaction rollbacks in test teardown
- Verify model constraints are respected

### 4. Import/Module Issues
- Check file paths and imports
- Verify TypeScript configuration
- Ensure proper ESM/CommonJS configuration

## Continuous Integration

### GitHub Actions
Tests should run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled runs (daily)

### Local Pre-commit
Run all tests before committing:
```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && python -m pytest

# E2E tests (optional)
cd frontend && npm run test:e2e
```

## Performance Considerations

### Test Execution Speed
- Use `--maxWorkers=4` for Jest to limit parallel execution
- Skip slow integration tests during development
- Use test.only() for focused testing

### Memory Usage
- Monitor memory usage during test execution
- Clear large test data between tests
- Use smaller datasets for performance tests

## Debugging Tests

### Frontend Debugging
```bash
# Debug mode
npm test -- --detectOpenHandles --forceExit

# Verbose output
npm test -- --verbose

# Run single test
npm test -- --testNamePattern="specific test name"
```

### Backend Debugging
```bash
# Verbose output
python -m pytest -v -s

# Debug specific test
python -m pytest tests/test_file.py::TestClass::test_method -v -s

# Print statements
python -m pytest -s --capture=no
```

## Test Data Management

### Fixtures
- Backend: Use pytest fixtures for consistent test data
- Frontend: Use factory functions for mock data

### Cleanup
- Ensure proper cleanup in test teardown
- Use database transactions that rollback
- Clear mocks between tests

## Security Test Considerations

### Authentication Tests
- Test with various user roles
- Verify token expiration handling
- Check unauthorized access prevention

### Input Validation Tests
- Test SQL injection prevention
- Verify XSS protection
- Check input sanitization

### Rate Limiting Tests
- Test API rate limits
- Verify login attempt limiting
- Check transaction frequency limits

This guide should help you run and troubleshoot the comprehensive test suites effectively.