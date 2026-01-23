# Prophily

A multi-agent AI system that analyzes Kalshi prediction markets and generates intelligent trading signals by combining real-time market data, news aggregation, and AI-powered analysis.

## Project Summary and Motivation

**Prophily** is an automated analysis platform for prediction markets that leverages specialized AI agents to process market data, aggregate relevant news, and generate actionable trading signals with confidence levels and risk-adjusted sizing recommendations.

### Why This Project?

Prediction markets contain a lot of information, but turning a single market URL into a *clear, actionable, and explainable* view is still very manual:

- You have to understand the contract details and resolution criteria.
- You have to read news, macro context, and platform-specific details.
- You have to translate all of that into a probability, an edge vs current prices, and a position size.

This system automates the analysis process by:

- **Aggregating Context**: Automatically fetches relevant news articles from Tavily API based on market context
- **AI-Powered Analysis**: Uses OpenAI's language models to synthesize market data, news, and probabilities into coherent signals
- **Risk Management**: Incorporates Kelly Criterion sizing and confidence-based filtering
- **Historical Tracking**: Stores all analysis runs in MongoDB for future backtesting and performance evaluation

### Key Capabilities

- **Multi-Agent Orchestration**: Specialized AI agents handle market data, news aggregation, signal generation, and reporting
- **Real-Time Phased Analysis**: Asynchronous processing that updates results incrementally as analysis progresses
- **Market Intelligence**: Combines Kalshi market data with Tavily news aggregation and sentiment analysis
- **Trading Signals**: Generates directional signals (up/down/flat) with confidence levels, edge calculations, and Kelly sizing recommendations
- **Interactive Dashboard**: Modern Next.js frontend with real-time polling and market selection for events with multiple markets

## Architecture

- **Backend**: FastAPI (Python 3.11) with async/await patterns, deployed on AWS Elastic Beanstalk
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS, deployed on Vercel
- **Database**: MongoDB Atlas for persistent storage of analysis runs and market history
- **Cache**: Redis (optional) or in-memory caching for API responses
- **External APIs**:
  - Kalshi API (market data)
  - Tavily Search API (news aggregation)
  - OpenAI API (AI analysis and signal generation)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher (or compatible package manager)
- **MongoDB**: MongoDB Atlas account (free tier works) or local MongoDB instance

### Required API Keys

You'll need API keys for the following services:

1. **OpenAI API Key** (required) - For AI-powered analysis and signal generation

2. **Tavily API Key** (required) - For news aggregation

3. **Kalshi API Key** (required) - For market data
   - Get your API key from: https://kalshi.com/account/api
   - You'll need both a Key ID and a Private Key (PEM format)

4. **MongoDB Connection String** (required) - For data persistence

5. **Redis** (optional) - For production caching

**Note**: These are provided in the deployed version for the purposes of the assignment as env vars in AWS Beanstalk

## Setup and Installation Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd prophecy-pred-markets
```

### 2. Backend Setup

Navigate to the backend directory and install Python dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

**Note**: The backend dependencies are managed in `backend/requirements.txt` for service-specific documentation.

### 3. Frontend Setup

Navigate to the frontend directory and install Node.js dependencies:

```bash
cd frontend
npm install
```

### 4. Environment Configuration

Create a `.env` file in the project root directory with the following variables:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
MONGODB_URI=your_mongodb_connection_string_here

# Kalshi API Configuration
KALSHI_API_KEY_ID=your_kalshi_api_key_id_here
KALSHI_PRIVATE_KEY_PATH=/path/to/your/kalshi_private_key.pem
# Or use base64-encoded key instead:
# KALSHI_PRIVATE_KEY_BASE64=your_base64_encoded_private_key_here
KALSHI_ENV=demo  # or "production" for live markets

# Optional Configuration
LOG_LEVEL=INFO
USE_REDIS_CACHE=false
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

See `.env.example` for a complete template with all available options.

### 5. Verify Installation

**Backend**:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` to see the API documentation.

**Frontend**:
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to see the dashboard.

## Usage Examples

### Basic Analysis

1. **Start both backend and frontend** (see Development section below)

2. **Open the dashboard** at `http://localhost:3000`

3. **Paste a Kalshi URL** into the input field:
   ```
   https://kalshi.com/markets/kxbtc/bitcoin-above-100000-on-december-31
   ```
   - Supports both event URLs and direct market URLs
   - If an event has multiple markets, you'll be prompted to select one

4. **View results** as the analysis progresses through phases:
   - **Phase 1**: Market snapshot (current prices, volume, liquidity)
   - **Phase 2**: News context (aggregated relevant articles with sentiment)
   - **Phase 3**: Trading signal (direction, confidence, rationale, Kelly sizing)
   - **Phase 4**: Final report (comprehensive analysis with bull/bear cases)

### API Usage

#### Start Analysis (Asynchronous)

```bash
curl -X POST http://localhost:8000/api/analyze/start \
  -H "Content-Type: application/json" \
  -d '{
    "market_url": "https://kalshi.com/markets/kxbtc/bitcoin-above-100000-on-december-31",
    "horizon": "24h",
    "strategy_preset": "Balanced"
  }'
```

Response:
```json
{
  "run_id": "run-abc123..."
}
```

#### Poll for Results

```bash
curl http://localhost:8000/api/run/run-abc123...
```

The response includes phased status and partial results:
```json
{
  "run": {
    "run_id": "run-abc123...",
    "status": {
      "market": "done",
      "news": "done",
      "signal": "pending",
      "report": "pending"
    },
    "market_snapshot": { ... },
    "news_context": { ... },
    "signal": { ... },
    "report": { ... }
  }
}
```

#### Synchronous Analysis (Legacy)

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "market_url": "https://kalshi.com/markets/kxbtc/bitcoin-above-100000-on-december-31",
    "horizon": "24h",
    "strategy_preset": "Balanced"
  }'
```

Returns complete analysis in a single response (may take 30-60 seconds).

### Configuration Options

You can customize the analysis behavior:

```json
{
  "market_url": "https://kalshi.com/markets/...",
  "horizon": "24h",
  "strategy_preset": "Balanced",
  "configuration": {
    "use_tavily_prompt_agent": true,
    "use_news_summary_agent": true,
    "max_articles": 15,
    "max_articles_per_query": 8,
    "min_confidence": "medium",
    "enable_sentiment_analysis": true
  }
}
```

### Strategy Presets

- **Cautious**: Lower risk, higher confidence requirements
- **Balanced**: Moderate risk and confidence (default)
- **Aggressive**: Higher risk tolerance, accepts lower confidence signals

### Time Horizons

- **intraday**: Analysis for same-day trading
- **24h**: Analysis for next 24 hours (default)
- **resolution**: Analysis until market resolution

## Development

### Starting the Backend

From the `backend/` directory:

```bash
# Using uvicorn directly
python -m uvicorn app.main:app --reload --port 8000

# Or using the dev server script
python dev_server.py
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Starting the Frontend

From the `frontend/` directory:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Quick Start Scripts

The repository includes helper scripts in the `scripts/` directory:

**Windows:**
```powershell
.\scripts\backend\start.ps1   # Start backend
.\scripts\frontend\start.ps1  # Start frontend
```

**Linux/Mac:**
```bash
./scripts/backend/start.sh    # Start backend
./scripts/frontend/start.sh   # Start frontend
```

### Testing

**Backend Tests:**
```bash
cd backend
pytest                    # Run all tests
pytest --cov=app          # Run with coverage
pytest tests/test_config.py -v  # Run specific test
```

**Frontend Tests:**
```bash
cd frontend
npm test                  # Run all tests
npm run test:coverage    # Run with coverage
npm test -- --watch      # Run in watch mode
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

- `POST /api/analyze/start` - Start asynchronous analysis for a market URL
- `GET /api/run/{run_id}` - Get analysis results for a run (supports polling)
- `POST /api/analyze` - Legacy synchronous analysis endpoint
- `GET /api/runs/recent` - List recent analysis runs
- `GET /health` - Health check endpoint
- `GET /health/ready` - Readiness probe with dependency checks

## Deployment

### Backend Deployment (AWS Elastic Beanstalk)

The backend is configured for deployment on AWS Elastic Beanstalk:

- `Procfile` - Defines the web server process (gunicorn with uvicorn workers)
- `runtime.txt` - Specifies Python 3.11
- `requirements.txt` - Python dependencies

**Deployment Steps:**

1. Create an Elastic Beanstalk application and environment (Python 3.11)
2. Set environment variables in the Elastic Beanstalk console:
   - `OPENAI_API_KEY`
   - `TAVILY_API_KEY`
   - `KALSHI_API_KEY_ID`
   - `KALSHI_PRIVATE_KEY_BASE64` (base64-encoded private key)
   - `KALSHI_ENV` (demo or production)
   - `MONGODB_URI`
   - `USE_REDIS_CACHE` (optional)
   - `REDIS_URL` (if using Redis)
   - `CORS_ORIGINS` (your frontend domain)
   - `ENVIRONMENT=production`
3. Deploy using EB CLI or zip upload:
   ```bash
   cd backend
   python create_zip.py  # Creates deployment package
   # Upload to Elastic Beanstalk
   ```

### Frontend Deployment (Vercel)

The frontend is optimized for Vercel deployment:

1. Connect your repository to Vercel
2. Set environment variables:
   - `BACKEND_URL` - Your Elastic Beanstalk backend URL
   - `NODE_ENV=production`
3. Deploy automatically on push or manually via Vercel CLI

**Vercel CLI:**
```bash
cd frontend
vercel --prod
```

### Environment Variables for Production

```bash
# Required
OPENAI_API_KEY=your_production_openai_key
TAVILY_API_KEY=your_production_tavily_key
KALSHI_API_KEY_ID=your_kalshi_api_key_id
KALSHI_PRIVATE_KEY_BASE64=your_base64_encoded_private_key
KALSHI_ENV=production
MONGODB_URI=your_production_mongodb_uri

# Recommended for production
USE_REDIS_CACHE=true
REDIS_URL=your_redis_connection_string
CORS_ORIGINS=https://your-frontend-domain.com
LOG_LEVEL=WARNING
ENVIRONMENT=production
```

## Project Structure

```
prophecy-pred-markets/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── agents/            # Multi-agent orchestration
│   │   │   ├── graph.py       # Main analysis graph
│   │   │   ├── market_agent.py
│   │   │   ├── event_agent.py
│   │   │   ├── news_agent.py
│   │   │   ├── prob_agent.py
│   │   │   ├── strategy_agent.py
│   │   │   └── report_agent.py
│   │   ├── config/            # Configuration
│   │   │   ├── settings.py
│   │   │   └── constants.py
│   │   ├── infrastructure/    # External service clients
│   │   │   └── http/
│   │   │       ├── kalshi.py      # Kalshi API client
│   │   │       ├── kalshi_auth.py # Kalshi authentication
│   │   │       └── cache.py
│   │   ├── db/                # Database layer
│   │   │   ├── async_client.py
│   │   │   ├── async_repositories.py
│   │   │   └── models.py
│   │   ├── routes/            # FastAPI route handlers
│   │   │   ├── analyze.py
│   │   │   └── runs.py
│   │   ├── schemas/           # Pydantic models
│   │   │   └── api.py
│   │   ├── services/          # Business logic
│   │   │   ├── kalshi/        # Kalshi service layer
│   │   │   ├── phased_analysis.py
│   │   │   └── run_snapshot.py
│   │   └── main.py            # FastAPI app entry point
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Python dependencies
│   ├── Procfile              # Elastic Beanstalk process definition
│   └── runtime.txt           # Python version
├── frontend/                   # Next.js frontend application
│   ├── app/                   # Next.js App Router pages
│   │   ├── api/              # API route handlers (proxies to backend)
│   │   └── page.tsx          # Main dashboard page
│   ├── components/           # React components
│   │   ├── analysis/         # Analysis result components
│   │   │   ├── AnalysisResults.tsx
│   │   │   ├── MarketCard.tsx
│   │   │   ├── NewsCard.tsx
│   │   │   ├── SignalCard.tsx
│   │   │   └── ReportCard.tsx
│   │   ├── layout/           # Layout components
│   │   │   ├── AppShell.tsx
│   │   │   ├── TopNav.tsx
│   │   │   └── HistorySidebar.tsx
│   │   ├── input/            # Input components
│   │   │   ├── UrlInput.tsx
│   │   │   └── EmptyState.tsx
│   │   ├── ui/               # Shared UI components
│   │   │   ├── Toast.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   └── skeletons/        # Loading skeletons
│   ├── hooks/                # Custom React hooks
│   │   ├── useAnalysisPolling.ts
│   │   ├── useAnalysisSubmit.ts
│   │   └── useRecentRuns.ts
│   ├── types/                # TypeScript type definitions
│   │   ├── analysis.ts
│   │   └── market.ts
│   ├── lib/                  # Utilities
│   │   ├── api.ts            # API client helpers
│   │   └── logger.ts         # Logging utilities
│   ├── tests/                # Frontend tests
│   └── package.json          # Node.js dependencies
├── docs/                     # Additional documentation
│   ├── architecture.md
│   ├── data_model.md
│   └── deployment.md
├── scripts/                  # Helper scripts
│   ├── backend/
│   └── frontend/
├── .env.example             # Environment variable template
└── README.md               # This file
```

## Dependency Management

### Backend Dependencies

Backend dependencies are managed in `backend/requirements.txt`:

- **Web Framework**: FastAPI, Uvicorn, Gunicorn
- **Database**: Motor (async MongoDB driver), PyMongo
- **HTTP Clients**: httpx (async), aiohttp
- **AI/ML**: OpenAI Python SDK
- **Cryptography**: cryptography (for Kalshi RSA-PSS signing)
- **Utilities**: Pydantic, structlog, tenacity (retries), python-dotenv
- **Cache**: Redis (optional)
- **Testing**: pytest, pytest-asyncio, pytest-cov

### Frontend Dependencies

Frontend dependencies are managed in `frontend/package.json`:

- **Framework**: Next.js 15, React 19
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Testing**: Jest, React Testing Library
- **Type Safety**: TypeScript

## Troubleshooting

### Backend Issues

**MongoDB Connection Failed**
- Verify `MONGODB_URI` is correct in `.env`
- Check network connectivity to MongoDB Atlas
- Verify MongoDB credentials are valid
- Ensure IP whitelist includes your server IP

**Kalshi API Errors**
- Verify `KALSHI_API_KEY_ID` and private key are set correctly
- Ensure private key is in PEM format (RSA)
- Check `KALSHI_ENV` is set to "demo" for testing or "production" for live
- Verify API key has appropriate permissions

**OpenAI API Errors**
- Check `OPENAI_API_KEY` is set correctly
- Verify API key has sufficient credits/quota
- Check circuit breaker status (may need reset if open)
- Reset circuit breaker: `POST /api/reset-circuit-breaker`

**Import Errors**
- Ensure you're in the `backend/` directory when running commands
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` should be 3.11+

### Frontend Issues

**Build Errors**
- Run `npm install` to ensure dependencies are installed
- Clear `.next` directory: `rm -rf .next` (Linux/Mac) or `Remove-Item -Recurse -Force .next` (Windows)
- Verify TypeScript strict mode compatibility (enabled in `tsconfig.json`)

**API Connection Errors**
- Verify backend is running on `http://localhost:8000`
- Check `BACKEND_URL` environment variable if using custom backend URL
- Verify CORS is configured correctly in backend
- Check browser console for detailed error messages

### Common Issues

**Port Already in Use**
- Backend: Change port with `--port 8001` or kill existing process
- Frontend: Change port with `npm run dev -- -p 3001` or kill existing process

**Module Not Found**
- Backend: Reinstall dependencies with `pip install -r requirements.txt`
- Frontend: Reinstall dependencies with `npm install`

**Redis Connection Issues**
- If `USE_REDIS_CACHE=true`, ensure Redis is running
- System will fall back to in-memory cache if Redis unavailable
- Check Redis connection string format: `redis://host:port/db`

## Contribution Guidelines

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow code style**:
   - Backend: Follow PEP 8, use type hints, async/await patterns
   - Frontend: Follow ESLint rules, use TypeScript strictly
3. **Write tests** for new features and ensure all tests pass
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description of changes

### Development Workflow

1. Create an issue or discuss the feature first
2. Create a branch from `main`: `git checkout -b feature/your-feature`
3. Make your changes and write tests
4. Ensure all tests pass: `pytest` (backend) and `npm test` (frontend)
5. Update documentation if needed
6. Submit a pull request

### Code Review Process

- All pull requests require review before merging
- Ensure CI/CD checks pass
- Address any feedback from reviewers
- Maintain backward compatibility when possible

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Additional Resources

- [Architecture Documentation](docs/architecture.md) - System architecture and design
- [Data Model](docs/data_model.md) - Database schema and data structures
- [Deployment Guide](docs/deployment.md) - Detailed deployment instructions
- [Use Case Documentation](docs/use_case.md) - Use case and workflow description

## Support

For issues, questions, or contributions, please open an issue on the repository.
