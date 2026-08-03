# Tennis Rankings API

A full-stack application that displays live ATP tennis rankings. Built as a portfolio project to learn the complete software development lifecycle — from local development through CI/CD to cloud deployment.

## Live Demo

- **API:** https://55c7s6pssb.execute-api.eu-west-2.amazonaws.com/prod/rankings
- **Frontend:** http://tennis-rankings-frontend.s3-website.eu-west-2.amazonaws.com

## What it does

Fetches live ATP rankings data from an external API, processes it, and displays the top 50 players in a clean table. The backend handles data fetching and caching, while the frontend provides a simple interface to view the rankings.

## Tech Stack

**Backend**
- Python 3.11
- FastAPI
- Pydantic for data validation
- httpx for async HTTP requests
- pytest for testing

**Frontend**
- React 18
- Vite
- Vanilla CSS

**Infrastructure**
- AWS Lambda (containerised)
- AWS ECR (container registry)
- AWS API Gateway
- AWS S3 (static site hosting)
- GitHub Actions (CI/CD)
- Docker

## How it works

```
User visits S3 website
        ↓
React app loads in browser
        ↓
App calls Lambda API
        ↓
Lambda checks cache (1 hour TTL)
        ↓
If cache empty, fetches from RapidAPI
        ↓
Returns rankings data
        ↓
React displays table
```

## Running Locally

### Backend

```bash
cd tennis-project
uv sync
uv run uvicorn app.main:app --reload --port 8003
```

Needs a `.env` file with:
```
RAPIDAPI_KEY=your_key
RAPIDAPI_HOST=tennisapi1.p.rapidapi.com
```

#### Optional: alternative rankings provider

`/rankings` can be served from [Live Tennis API](https://livetennisapi.com)
instead. This is off by default — with nothing below set, the provider above is
used exactly as before.

```
RANKINGS_PROVIDER=livetennisapi
LIVETENNISAPI_KEY=your_key
```

Optional, with the defaults shown:

```
LIVETENNISAPI_BASE_URL=https://api.livetennisapi.com/api/public/v1
LIVETENNISAPI_SYSTEM=atp      # atp, wta, itf_jt, itf_mt, itf_wt
LIVETENNISAPI_LIMIT=50
```

The response shape is unchanged, so the frontend needs no edit. Two notes:

- The ranking table is a PRO-tier endpoint there; player lookups used to fill in
  names are free.
- A ranking record carries no player name, so one `/players/{id}` call is made
  per player on a cache miss (the cache TTL is 1 hour). If a future response
  embeds the player, that lookup is skipped automatically.

### Frontend

```bash
cd tennis-rankings-frontend
npm install
npm run dev
```

Opens at http://localhost:5173

## Project Structure

```
tennis-project/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings and env vars
│   ├── cache.py             # In-memory caching
│   ├── exceptions.py        # Custom exceptions
│   ├── models/
│   │   └── player.py        # Pydantic models
│   ├── routers/
│   │   ├── rankings.py      # Rankings endpoints
│   │   └── health.py        # Health check endpoint
│   └── services/
│       ├── rankings.py      # Business logic
│       └── livetennisapi.py # Optional alternative provider
├── tests/
├── Dockerfile               # Local development
├── Dockerfile.lambda        # AWS Lambda deployment
└── .github/workflows/
    └── ci.yml               # Test and deploy pipeline
```

## CI/CD Pipeline

On every push to main:
1. Runs pytest
2. Builds Docker image
3. Pushes to ECR
4. Updates Lambda function

Pull requests only run tests (no deployment).

## Future Improvements

- **Redis caching** — Replace in-memory cache with Upstash Redis for persistence across Lambda instances
- **Claude AI integration** — Add natural language queries like "show me Italian players in the top 20"
- **Player filtering** — Filter by country, ranking range
- **Historical data** — Show ranking changes over time using Sackmann's historical dataset
- **WTA rankings** — Add women's rankings alongside ATP

## What I learned

This project taught me how to take an application from zero to production:

- Designing REST APIs with FastAPI
- Data validation with Pydantic models
- Async programming in Python
- React fundamentals (components, state, effects)
- Docker containerisation
- AWS services (Lambda, ECR, API Gateway, S3)
- CI/CD with GitHub Actions
- The importance of proper error handling and logging
