# TestForge — AI-Powered Test Case Generation System

An intelligent test case generation engine that produces structured testing scenarios from UI descriptions and product requirements using Ollama phi3 as the local LLM backend, built with FastAPI.

---

## Features

- Generates Positive, Negative, and Edge Case test scenarios using LLM prompt pipelines
- Structured output with steps, preconditions, priorities, and tags
- Export test suites as JSON or CSV
- Clean frontend UI with tabbed results and one-click export
- Fully local — no API keys, no cloud, runs entirely on your machine

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| LLM Backend | Ollama (phi3 model) |
| Data Validation | Pydantic v2 |
| HTTP Client | HTTPX (async) |
| Frontend | Vanilla HTML/CSS/JS |
| Export Formats | JSON, CSV |

---

## Project Structure

```
test case generator/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Settings via pydantic-settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py        # Ollama phi3 async caller
│   │   ├── prompt_service.py     # Prompt engineering pipelines
│   │   ├── parser_service.py     # LLM output to structured TestCase
│   │   └── export_service.py     # JSON and CSV report generation
│   └── routers/
│       ├── __init__.py
│       └── test_generation.py    # API route handlers
├── index.html                    # Frontend UI
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Ollama installed on your machine — https://ollama.com

---

## Setup and Installation

### 1. Navigate to the project folder

```bash
cd "/Users/your-username/Desktop/test case generator"
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Pull the phi3 model via Ollama

```bash
ollama pull phi3
```

---

## Running the Project

You need two terminals running simultaneously.

### Terminal 1 — Start Ollama

```bash
ollama serve
```

### Terminal 2 — Start the API

```bash
cd "/Users/your-username/Desktop/test case generator"
python3 -m uvicorn app.main:app --port 8000 --no-access-log
```

You should see:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Open the Frontend

```bash
open "/Users/your-username/Desktop/test case generator/index.html"
```

Or double-click index.html directly from Finder.

---

## Using the API

### Interactive Docs

```
http://127.0.0.1:8000/docs
```

### Health Check

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Response:

```json
{
  "api": "ok",
  "ollama": "ok",
  "model": "phi3"
}
```

### Generate Test Cases

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate-tests \
  -H "Content-Type: application/json" \
  -d '{
    "ui_description": "A login page with an email input field, password input field with show/hide toggle button, a Submit button, a Forgot Password link, and a Remember Me checkbox.",
    "product_requirements": "Email must be in valid format. Password must be minimum 8 characters long. Show inline error message if credentials are wrong. Redirect user to dashboard on successful login. Lock account after 5 consecutive failed login attempts.",
    "test_types": ["positive", "negative", "edge_case"],
    "max_per_type": 3
  }'
```

### Download as JSON

```bash
curl "http://127.0.0.1:8000/api/v1/download/YOUR_SESSION_ID?format=json" -o test_cases.json
```

### Download as CSV

```bash
curl "http://127.0.0.1:8000/api/v1/download/YOUR_SESSION_ID?format=csv" -o test_cases.csv
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root — service info |
| GET | `/api/v1/health` | Health check for API and Ollama |
| POST | `/api/v1/generate-tests` | Generate test cases from description |
| GET | `/api/v1/export/{session_id}` | Get export as JSON response |
| GET | `/api/v1/download/{session_id}` | Download file as JSON or CSV |

### Request Body — /generate-tests

| Field | Type | Required | Description |
|---|---|---|---|
| `ui_description` | string | Yes | UI component description, min 20 characters |
| `product_requirements` | string | Yes | Functional requirements, min 20 characters |
| `test_types` | array | No | One or more of: positive, negative, edge_case |
| `max_per_type` | integer | No | Max cases per type, 1 to 10, default 5 |

---

## Configuration

Create a .env file in the project root to override defaults:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3
OLLAMA_TIMEOUT=120
MAX_TEST_CASES_PER_TYPE=5
DEBUG=false
```

To switch to a different Ollama model:

```env
OLLAMA_MODEL=mistral
```

---

## How It Works

```
Client Request
     |
     v
FastAPI Router
     |
     |-- Prompt Service    builds positive / negative / edge prompts
     |
     |-- LLM Service       calls Ollama phi3 sequentially
     |
     |-- Parser Service    cleans LLM output into Pydantic TestCase objects
     |
     |-- Export Service    renders JSON and CSV reports
```

Each test type is generated one after another rather than in parallel. Ollama on a local machine queues concurrent requests, so sequential calls produce faster and more reliable results.

---

## Troubleshooting

**ModuleNotFoundError: No module named app**

Run uvicorn from the project root using python3 -m uvicorn, not the plain uvicorn command:

```bash
python3 -m uvicorn app.main:app --port 8000
```

**ModuleNotFoundError: No module named pydantic_settings**

```bash
pip install pydantic-settings
```

**503 Ollama not running**

Start Ollama in a separate terminal:

```bash
ollama serve
```

**Generation takes too long**

Lower max_per_type to 2 or 3. phi3 is a small model and runs on CPU — each generation round takes 30 to 90 seconds depending on your machine.

**No test cases generated**

phi3 occasionally returns malformed JSON. Run the request again. The parser will log a warning and skip invalid output.

**CORS error in browser**

Make sure the API is running on port 8000 and open index.html as a local file, not through a separate dev server on a different port.

---

## Example Inputs

| UI Description | Product Requirements |
|---|---|
| Login form with email, password, and submit button | Valid email format, password min 8 chars, redirect on success |
| Registration form with name, email, password, confirm password | Unique email, passwords must match, name min 2 chars |
| Search bar with filter dropdown | Query min 3 chars, show empty state, filter by category |
| File upload with drag and drop area | PDF and JPG only, max 5MB, show progress bar |
| Checkout form with card and address fields | Card number validation, required address fields, order confirmation |

---

## License

MIT — free to use, modify, and distribute.
