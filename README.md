# MP Cargo Tracker

A cargo tracking application with support for air and sea freight tracking.

## Features

- Air freight tracking (Air India, AF/KLM)
- Sea freight tracking (CMA CGM, Hapag-Lloyd)
- AI-powered tracking assistance
- Modern web interface

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: React/TypeScript
- Database: TBD
- AI: OpenAI integration

## Setup

1. Backend setup:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Frontend setup:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Usage

Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

