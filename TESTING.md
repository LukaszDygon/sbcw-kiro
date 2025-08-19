# SoftBankCashWire Testing Guide

This document provides comprehensive information about the testing setup and practices for the SoftBankCashWire application.

## Overview

The SoftBankCashWire application has a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components and functions in isolation
- **Integration Tests**: Test API endpoints and service interactions
- **Component Tests**: Test React components with user interactions
- **End-to-End Tests**: Test complete user workflows
- **Security Tests**: Test authentication, authorization, and security measures
- **Performance Tests**: Test system performance under load

## Backend Testing

### Test Structure

```
backend/tests/
├── conftest.py                    # Pytest configuration and fixtures
├── test_models.py                 # Database model tests
├── test_*_service.py             # Service layer unit tests
├── test_*_api.py                 # API endpoint tests
├── test_api_integration.py       # Comprehensive API integration tests
├── test_security.py              # Security and authentication tests
└── test_performance.py           # Performance and load tests
```

### Running Backend Tests

#### Using the Test Runner Script

```bash
# Run all tests
python backend/run_tests.py

# Run specific test suites
python backend/run_tests.py --suite unit
python backend/run_tests.py --suite integration
python backend/run_tests.py --suite security
python backend/run_tests.py --suite performance
python backend/run_tests.py --suite coverage

# Run quick smoke tests
python backend/run_tests.py --suite quick

# Run specific test file
python backend/run_tests.py --test tests/test_transaction_service.py
```

#### Using Pytest Directly

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=models --cov=api --cov-report=html

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m security              # Security tests only
pytest -m performance           # Performance tests only

# Run specific test files
pytest tests/test_transaction_service.py
pytest tests/test_security.py -v

# Run tests matching pattern
pytest -k "test_send_money"
```

### Test Categories and Markers

- `@pytest.mark.unit`: Unit tests for individual functions/methods
- `@pytest.mark.integration`: Integration tests for API endpoints
- `@pytest.mark.security`: Security-focused tests
- `@pytest.mark.performance`: Performance and load tests
- `@pytest.mark.slow`: Tests that take longer to run

### Backend Test Coverage

The backend tests achieve comprehensive coverage of:

#### Unit Tests
- **Models**: User, Account, Transaction, EventAccount, MoneyRequest, AuditLog, Notification
- **Services**: AuthService, AccountService, TransactionService, EventService, NotificationService, AuditService
- **Business Logic**: Balance validation, transaction limits, role-based permissions

#### Integration Tests
- **Authentication Flow**: Microsoft SSO login, token validation, session management
- **Account Management**: Balance retrieval, transaction history, account operations
- **Money Transfers**: Single transfers, bulk transfers, validation, error handling
- **Money Requests**: Creation, approval, decline, expiration
- **Event Management**: Creation, contributions, closure, progress tracking
- **Reporting**: Transaction reports, user activity, audit trails

#### Security Tests
- **Authentication**: JWT validation, token expiration, tampering detection
- **Authorization**: Role-based access control, resource ownership validation
- **Input Validation**: SQL injection prevention, XSS prevention, amount validation
- **Rate Limiting**: Login attempts, API calls, transaction frequency
- **Data Protection**: Sensitive data masking, audit trail integrity

#### Performance Tests
- **Transaction Processing**: Single transaction performance, concurrent transactions
- **Database Operations**: Query performance, connection pooling
- **Memory Usage**: Memory consumption under load
- **Scalability**: Performance with large datasets

## Frontend Testing

### Test Structure

```
frontend/
├── src/components/__tests__/      # Component tests
│   ├── Dashboard.test.tsx
│   ├── SendMoney.test.tsx
│   ├── TransactionList.test.tsx
│   └── AuthGuard.test.tsx
├── e2e/                          # End-to-end tests
│   ├── auth.spec.ts
│   ├── money-transfer.spec.ts
│   ├── event-management.spec.ts
│   ├── global-setup.ts
│   └── global-teardown.ts
├── jest.config.js                # Jest configuration
├── playwright.config.ts          # Playwright configuration
└── run_tests.js                  # Test runner script
```

### Running Frontend Tests

#### Using the Test Runner Script

```bash
# Run all tests
node frontend/run_tests.js

# Run specific test suites
node frontend/run_tests.js --suite=unit
node frontend/run_tests.js --suite=component
node frontend/run_tests.js --suite=e2e
node frontend/run_tests.js --suite=coverage

# Run quick smoke tests
node frontend/run_tests.js --suite=quick

# Run specific test
node frontend/run_tests.js --test=Dashboard
```

#### Using NPM Scripts

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run component tests
npm run test:component

# Run end-to-end tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run all tests
npm run test:all
```

### Frontend Test Coverage

#### Component Tests (React Testing Library + Jest)
- **Dashboard**: Balance display, quick actions, transaction history
- **SendMoney**: Form validation, recipient selection, transaction submission
- **TransactionList**: Filtering, sorting, pagination, transaction details
- **AuthGuard**: Authentication checks, role-based access, redirects
- **Event Components**: Event creation, contributions, progress tracking

#### End-to-End Tests (Playwright)
- **Authentication Flow**: Microsoft SSO login, logout, session management
- **Money Transfer Flow**: Complete transfer process, validation, error handling
- **Event Management Flow**: Event creation, contributions, closure
- **Cross-browser Testing**: Chrome, Firefox, Safari, Edge
- **Mobile Testing**: Responsive design on mobile devices

## Test Data and Fixtures

### Backend Fixtures (conftest.py)
- **app**: Flask application instance with test configuration
- **client**: Test client for API requests
- **runner**: CLI test runner

### Test Database
- Uses SQLite in-memory database for fast, isolated tests
- Automatic setup and teardown for each test
- Consistent test data across test runs

### Mock Data
- Realistic user accounts with various roles
- Sample transactions and event data
- Mock Microsoft SSO responses

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: python backend/run_tests.py --suite=all
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: cd frontend && node run_tests.js --suite=all
```

## Test Coverage Requirements

### Backend Coverage Targets
- **Overall Coverage**: 90% minimum
- **Services**: 95% minimum
- **Models**: 90% minimum
- **API Endpoints**: 85% minimum

### Frontend Coverage Targets
- **Components**: 80% minimum
- **Services**: 85% minimum
- **Utilities**: 90% minimum

## Best Practices

### Writing Tests

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
3. **Test Isolation**: Each test should be independent and not rely on other tests
4. **Mock External Dependencies**: Mock external APIs, databases, and services
5. **Test Edge Cases**: Include tests for error conditions and boundary cases

### Test Organization

1. **Group Related Tests**: Use test classes or describe blocks to group related tests
2. **Use Fixtures**: Create reusable test data and setup code
3. **Separate Concerns**: Keep unit tests separate from integration tests
4. **Document Complex Tests**: Add comments for complex test logic

### Performance Considerations

1. **Fast Unit Tests**: Unit tests should run quickly (< 100ms each)
2. **Parallel Execution**: Run tests in parallel when possible
3. **Selective Testing**: Use test markers to run specific test categories
4. **Resource Cleanup**: Properly clean up resources after tests

## Debugging Tests

### Backend Debugging

```bash
# Run tests with verbose output
pytest -v

# Run specific test with debugging
pytest tests/test_transaction_service.py::TestTransactionService::test_send_money -v -s

# Run with pdb debugger
pytest --pdb tests/test_transaction_service.py

# Generate coverage report
pytest --cov=services --cov-report=html
open htmlcov/index.html
```

### Frontend Debugging

```bash
# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- Dashboard.test.tsx

# Run with coverage
npm run test:coverage

# Debug E2E tests
npm run test:e2e:ui
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**: Ensure test database is properly configured
2. **Mock Service Failures**: Check that external services are properly mocked
3. **Timing Issues**: Use proper async/await patterns and timeouts
4. **Test Data Conflicts**: Ensure proper test isolation and cleanup

### Performance Issues

1. **Slow Tests**: Profile tests to identify bottlenecks
2. **Memory Leaks**: Monitor memory usage during test runs
3. **Database Locks**: Use proper transaction handling in concurrent tests

## Contributing

When adding new features:

1. **Write Tests First**: Follow TDD practices when possible
2. **Maintain Coverage**: Ensure new code meets coverage requirements
3. **Update Documentation**: Update this guide when adding new test types
4. **Run Full Test Suite**: Verify all tests pass before submitting PRs

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)