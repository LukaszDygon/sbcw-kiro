# SoftBankCashWire

Internal banking application for employee money exchanges and event funding.

## Features

- **Microsoft SSO Authentication**: Secure login using company Microsoft accounts
- **Peer-to-Peer Transfers**: Send money between employees instantly
- **Money Requests**: Request payments from colleagues
- **Event Funding**: Collaborative funding for team events and celebrations
- **Transaction History**: Complete audit trail with search and filtering
- **Role-Based Access**: Different permissions for employees, admins, and finance team
- **Real-time Notifications**: Instant updates for transactions and events
- **Comprehensive Reporting**: Financial reports and analytics

## Technology Stack

### Backend
- Python 3.11+ with Flask
- SQLAlchemy ORM with SQLite database
- JWT authentication with Microsoft Graph API
- Comprehensive test suite with pytest

### Frontend
- TypeScript with React 18
- Vite for fast development and building
- TailwindCSS for styling
- React Query for state management
- Jest and React Testing Library for testing

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Microsoft Azure App Registration for SSO

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp ../.env.example .env
   # Edit .env with your configuration
   ```

5. Initialize database:
   ```bash
   flask db upgrade
   ```

6. Run development server:
   ```bash
   python app.py
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=. --cov-report=html  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage  # With coverage
```

## Project Structure

```
softbank-cashwire/
├── backend/
│   ├── api/                 # REST API endpoints
│   ├── models/              # Database models
│   ├── services/            # Business logic
│   ├── tests/               # Backend tests
│   ├── app.py              # Flask application
│   ├── config.py           # Configuration
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Vite configuration
└── .kiro/specs/            # Feature specifications
```

## Security

- All financial data encrypted at rest (AES-256)
- TLS 1.3 for data in transit
- JWT tokens with refresh rotation
- Role-based access control
- Comprehensive audit logging
- Rate limiting and fraud detection

## License

Internal use only - SoftBank Group