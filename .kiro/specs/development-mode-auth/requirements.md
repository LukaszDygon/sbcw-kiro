# Requirements Document

## Introduction

Development Mode Authentication is a developer experience enhancement for the SoftBankCashWire application that allows automatic authentication of the admin user (admin@softbank.com) when running in development mode. This feature eliminates the need for Microsoft SSO integration during local development, testing, and debugging, while maintaining security by only being available in non-production environments.

## Requirements

### Requirement 1: Development Mode Configuration

**User Story:** As a developer, I want to enable development mode through environment configuration, so that I can bypass Microsoft SSO authentication during local development.

#### Acceptance Criteria

1. WHEN the environment variable `DEVELOPMENT_MODE` is set to `true` THEN the system SHALL enable development mode authentication
2. WHEN the environment variable `DEVELOPMENT_MODE` is not set or set to `false` THEN the system SHALL use standard Microsoft SSO authentication
3. WHEN running in production environment THEN the system SHALL ignore development mode settings and always use Microsoft SSO
4. WHEN development mode is enabled THEN the system SHALL log a warning message indicating development mode is active
5. WHEN starting the application THEN the system SHALL clearly indicate in startup logs whether development mode is enabled or disabled

### Requirement 2: Automatic Admin Authentication

**User Story:** As a developer, I want to be automatically authenticated as the admin user, so that I can test admin functionality without going through Microsoft SSO flow.

#### Acceptance Criteria

1. WHEN development mode is enabled AND a user accesses any protected route THEN the system SHALL automatically authenticate them as admin@softbank.com
2. WHEN development mode authentication occurs THEN the system SHALL create or retrieve the admin user account with admin role
3. WHEN the admin user doesn't exist in the database THEN the system SHALL create it with default admin permissions
4. WHEN development mode authentication occurs THEN the system SHALL generate a valid JWT token for the admin user
5. WHEN accessing the application in development mode THEN the system SHALL skip Microsoft SSO redirect and proceed directly to the dashboard
6. WHEN development mode is active THEN the system SHALL display a visual indicator in the UI showing "Development Mode" status

### Requirement 3: Admin User Account Management

**User Story:** As a developer, I want the admin user account to be properly configured, so that I can test all administrative features during development.

#### Acceptance Criteria

1. WHEN creating the admin user in development mode THEN the system SHALL set the email to admin@softbank.com
2. WHEN creating the admin user in development mode THEN the system SHALL set the name to "Development Admin"
3. WHEN creating the admin user in development mode THEN the system SHALL assign the ADMIN role
4. WHEN creating the admin user in development mode THEN the system SHALL set account status to ACTIVE
5. WHEN creating the admin user in development mode THEN the system SHALL create an associated account with £0.00 balance
6. WHEN the admin user already exists THEN the system SHALL use the existing user without modification

### Requirement 4: Security and Safety Measures

**User Story:** As a developer, I want development mode to be secure and safe, so that it cannot be accidentally enabled in production environments.

#### Acceptance Criteria

1. WHEN the application detects a production environment THEN the system SHALL disable development mode regardless of configuration
2. WHEN development mode is enabled THEN the system SHALL add security headers indicating development environment
3. WHEN development mode is active THEN the system SHALL log all authentication bypasses for audit purposes
4. WHEN development mode is enabled THEN the system SHALL display prominent warnings in the UI about development mode being active
5. WHEN building for production THEN the system SHALL exclude development mode code from production builds
6. IF development mode is accidentally enabled in production THEN the system SHALL fail to start with a clear error message

### Requirement 5: Developer Experience Features

**User Story:** As a developer, I want convenient development features, so that I can efficiently develop and test the application.

#### Acceptance Criteria

1. WHEN development mode is active THEN the system SHALL provide a way to switch between different user roles for testing
2. WHEN development mode is active THEN the system SHALL allow quick user switching without re-authentication
3. WHEN development mode is active THEN the system SHALL provide debug information about the current authenticated user
4. WHEN development mode is active THEN the system SHALL allow bypassing certain validation rules for testing purposes
5. WHEN development mode is active THEN the system SHALL provide enhanced logging for authentication and authorization flows