# Awesome Docify

Your AI assistant for painless documentation updates.

## Tech Stack

- [**Next.js 15**](https://nextjs.org/) - React framework with App Router
- [**FastAPI**](https://fastapi.tiangolo.com/) - Modern Python web framework
- [**TypeScript**](https://www.typescriptlang.org/) - Type-safe development
- [**Tailwind CSS**](https://tailwindcss.com/) - Utility-first CSS framework
- [**shadcn/ui**](https://ui.shadcn.com/) - Beautiful React components
- [**Docker**](https://www.docker.com/) - Containerized development environment

## Prerequisites

Before getting started, ensure you have the following tools installed:

- **UV** - Fast Python package manager
- **PNPM** - Fast Next.js & React package manager
- **Make** - Build automation tool
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration

**For detailed installation instructions, see [docs/prerequisites.md](docs/prerequisites.md)**

### Quick Verification

Run this command to verify all prerequisites are installed:

```bash
echo "UV: $(uv --version)" && echo "PNPM: $(pnpm --version)" && echo "Make: $(make --version)" && echo "Docker: $(docker --version)" && echo "Docker Compose: $(docker compose version)"
```

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/AnishNavalgund/awesome-docify.git
cd awesome-docify
```

### 2. Install dependencies

```bash
# Install all dependencies (backend + frontend)
make install

# Or install manually:
# Backend dependencies
cd fastapi_backend
uv sync

# Frontend dependencies
cd ../nextjs-frontend
pnpm install
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your API keys
nano .env
```

**Required Environment Variables:**
- `OPENAI_API_KEY` - Your OpenAI API key (required)

**Optional Environment Variables:**
- `LLM_MODEL` - OpenAI model (default: gpt-4o)
- `EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)

### 4. Start the application

**Option A: Using Docker (Recommended)**
```bash
docker compose up -d
```

**Option B: Local Development**
```bash
# Start backend
cd fastapi_backend
uv run uvicorn app.main:app --reload

# Start frontend (in another terminal)
cd nextjs-frontend
pnpm dev

# Postgres Database
docker compose up db -d
```

### 5. Access the application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Postgres Database**: http://localhost:5432
- **Qdrant Database**: http://localhost:6333 (if running locally)

## Code Quality with Pre-commit

This project uses pre-commit hooks to ensure code quality and consistency.

### Setup Pre-commit

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Run on all files (first time)
pre-commit run --all-files
```

### Usage

Pre-commit runs automatically on every commit. If any checks fail:
1. Fix the issues
2. Stage the fixed files
3. Commit again

**Manual run:**
```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
```

## Project Structure

```
awesome-docify/
├── fastapi_backend/          # FastAPI backend
│   ├── app/                 # Application code
│   ├── tests/               # Backend tests
│   └── pyproject.toml       # Python dependencies
├── nextjs-frontend/         # Next.js frontend
│   ├── app/                 # App Router pages
│   ├── components/          # React components
│   └── package.json         # Node.js dependencies
├── docs/                    # Documentation
├── docker-compose.yml       # Docker services
└── Makefile                 # Build automation
```

## Available Commands

### Make Commands (Local Development/Deployment)
- `make install` - Install all dependencies
- `make start-local-application` - Start local application
- `make build-frontend` - Build frontend for production
- `make lint-frontend` - Run ESLint
- `make test-frontend` - Run frontend tests
- `make start-frontend` - Start frontend
- `make test-backend` - Run backend tests
- `make coverage-backend` - Run backend tests with coverage
- `make start-backend` - Start backend
- `make migrate` - Run database migrations
- `make reset-db` - Reset database

### Docker Commands
- `docker compose up -d` - Start all services
- `docker compose down` - Stop all services
- `docker compose logs -f` - View logs
- `docker compose up backend -d` - Start backend only
- `docker compose up frontend -d` - Start frontend only
- `docker compose up db -d` - Start database only


## License

This project is open source and available under the [MIT License](LICENSE.txt).
