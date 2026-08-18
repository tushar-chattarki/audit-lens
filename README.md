# BANKING FINANCIAL STATEMENT REVIEW AUTOMATION — Member 7 Dashboard & Integration Foundation

An AI-Assisted Audit Copilot that ingests a bank's financial statements, executes deterministic mathematical and consistency rule checks, links every finding to source evidence, generates grounded AI narrative explanations, and auto-populates a digital **WP-514 working paper** for human sign-off.

---

## Technical Stack & Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS + Recharts
- **Backend**: Python 3.11 + FastAPI (Modular Monolith)
- **Containerization**: Docker Compose (`frontend`, `backend`)
- **Working Paper Standard**: WP-514 Financial Statement Review Template

---

## Development Quick Start

### 1. Local Development (Frontend + Backend)

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000)

#### Backend:
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Open API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Run with Docker Compose
```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

## Team Integration Boundaries (M1–M6)

Inter-module Python stubs are located in [`backend/modules_stub.py`](file:///c:/Users/Hp/Desktop/Audit%20lens%20_dashboard/backend/modules_stub.py).
Teammates can plug in their module logic as follows:

- **M1**: `m1_domain_wp514_mapper()`
- **M2**: `m2_synthetic_dataset_loader()`
- **M3**: `m3_extraction_engine()`
- **M4**: `m4_math_engine()`
- **M5**: `m5_consistency_prior_year_engine()`
- **M6**: `m6_ai_grounded_layer()`
