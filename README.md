# AUDIT LENS — BANKING FINANCIAL STATEMENT REVIEW AUTOMATION

An AI-Assisted Audit Copilot that ingests a bank's financial statements (PDF/Excel), executes deterministic mathematical and consistency rule checks, links every finding to source evidence, generates grounded AI narrative explanations, and auto-populates a digital **WP-514 working paper** for human sign-off.

---

## Key Features

- **Document Extraction**: Automatic ingestion of PDF and Excel financial statements into Canonical Financial JSON (schema v1.0).
- **Deterministic Math Engine**: Cross-foots Balance Sheet equation ($\text{Assets} = \text{Liabilities} + \text{Equity}$), P&L, and Cash Flow statements with zero arithmetic AI risk.
- **Consistency & Prior-Year Engine**: Executes cross-statement consistency checks (C001–C007) and YoY movement analysis against materiality thresholds (PY001–PY008).
- **Grounded AI Narrative Layer**: Synthesizes evidence-grounded anomaly explanations and candidate review commentary.
- **Source Evidence Tracing**: Every finding carries cell-level page and row evidence pointers for auditor verification.
- **WP-514 Working Paper Auto-Population**: Populates the standard 8-section audit working paper ready for human reviewer sign-off.

---

## Technical Architecture & Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Recharts
- **Backend**: Python 3.11 + FastAPI (Modular Monolith, Stateless In-Memory Pipeline)
- **Containerization**: Docker Compose (`frontend`, `backend`)
- **Audit Standard**: WP-514 Financial Statement Review Working Paper

---

## Quick Start Guide

### 1. Backend Server Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
API Documentation available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Application Setup
```bash
cd frontend
npm install
npm run dev
```
Dashboard Application available at: [http://localhost:3000](http://localhost:3000)

---

### 3. Docker Compose Setup
```bash
docker compose up --build
```
- Frontend SPA: `http://localhost:3000`
- Backend API: `http://localhost:8000`
