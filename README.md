<div align="center">

# 🏦 Audit Lens — Banking Financial Statement Review Automation
### *An AI-Assisted Audit Copilot for Automated Financial Statement Verification & WP-514 Working Paper Generation*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

</div>

---

## 📋 Executive Overview

**Audit Lens** is an enterprise-grade AI Audit Copilot designed to automate 80% of mechanical review tasks during bank financial statement audits. It ingests complex banking financial statements (PDF & XLSX), extracts and normalizes accounting structures into a unified **Canonical Financial Data Model (Schema v1.0)**, runs deterministic mathematical and cross-statement consistency checks, generates grounded AI narrative commentary, and auto-drafts a standardized **WP-514 Financial Statement Review Working Paper** for human auditor sign-off.

---

## 🎯 Problem Statement & Impact

| Manual Audit Pain Point | Audit Lens Automated Copilot Solution |
| :--- | :--- |
| **Manual Re-casting & Footing:** Recalculating totals across Balance Sheet, P&L, and Cash Flow by hand. | **Deterministic Math Engine:** Cross-foots statement equations instantly in Python with zero arithmetic error risk. |
| **Cross-Statement Tracing:** Manually verifying note disclosures against primary statements. | **Consistency Engine (C001–C007):** Cross-checks cash balances, equity linkages, depreciation, and tax across disclosures automatically. |
| **YoY Comparative Eyeballing:** Spotting material percentage shifts across years manually. | **Prior-Year Engine (PY001–PY008):** Flags material YoY absolute and percentage movements ($>20\%$ threshold). |
| **Commentary Drafting:** Writing anomaly explanations and review notes from scratch. | **Grounded Local LLM Layer:** Synthesizes evidence-grounded anomaly commentary strictly bound to validated figures. |
| **Working Paper Preparation:** Manual transcription into audit working papers. | **WP-514 Auto-Population:** Drafts all 8 WP-514 working paper sections ready for human auditor sign-off. |

---

## 🏗️ System Architecture

Audit Lens follows a **Stateless Single-Pass Modular Monolith Architecture** designed for high throughput, zero data leakage, and complete audit trail reproducibility.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUDITOR / USER INTERFACE                           │
│                React 18 + TypeScript + Vite + Tailwind CSS                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Upload PDF / XLSX (POST /api/review)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND ORCHESTRATOR                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DOCUMENT EXTRACTION LAYER                             │
│       pdfplumber + PyMuPDF (PDF) / openpyxl + Pandas (Excel)               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CANONICAL FINANCIAL DATA MODEL                          │
│               Normalized JSON: Accounts x Periods + Evidence Pointers       │
└───────┬──────────────────────────────┼──────────────────────────────┬───────┘
        │                              │                              │
        ▼                              ▼                              ▼
┌──────────────┐              ┌─────────────────┐           ┌──────────────────┐
│ MATH ENGINE  │              │ CONSISTENCY &   │           │ AI REVIEW LAYER  │
│ Deterministic│              │ PY ENGINE       │           │ Local LLM        │
│ Python Checks│              │ Deterministic   │           │ Grounded Only    │
└───────┬──────┘              └────────┬────────┘           └────────┬─────────┘
        │                              │                             │
        └──────────────────────────────┼─────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FINDINGS & RISK AGGREGATOR                            │
│           Normalized Findings (Pass / Exception / Warning / N.A.)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WP-514 WORKING PAPER ENGINE                          │
│               Auto-Drafts 8-Section Standard Audit Working Paper            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXECUTIVE AUDIT DASHBOARD & EXPORT                       │
│      Overview KPIs | Findings Table | Evidence Inspector | WP-514 Sign-off  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Core Features & Technical Highlights

- ⚡ **Zero-Hallucination Determinism:** Every arithmetic equation, cross-footing check, and YoY movement comparison is computed strictly in pure Python/Pandas code. The LLM is never trusted with math.
- 📍 **Cell-Level Source Evidence Tracing:** Every finding carries an explicit evidence pointer (`{doc_id, page, table, row, period}`) enabling auditors to click any finding and inspect the exact highlight line in the source document.
- 🤖 **Grounded AI Narrative Layer:** Local LLM integration (via Ollama / Llama 3.1) receives already-validated numbers and generates natural-language review comments and anomaly explanations with strict prompt constraints.
- 📄 **WP-514 Working Paper Engine:** Generates an auditable, 8-section WP-514 working paper containing engagement details, financial statement summaries, math check results, prior-year analysis, banking analytics, field mappings, and final sign-off controls.
- 🛡️ **Stateless & Privacy-First:** Operates on an in-memory single-pass pipeline — zero data stored in databases or persistent storage, protecting sensitive financial data.

---

## 🛠️ Tech Stack & Engineering Specifications

### **Frontend Stack**
- **Framework:** React 18 with TypeScript & Vite
- **Styling:** Tailwind CSS + Lucide Icons
- **Data Visualization:** Recharts (Grouped Bar, Movement Charts, Cash Recon, Donut Charts)
- **Testing:** Vitest + React Testing Library

### **Backend Stack**
- **Framework:** Python 3.11 + FastAPI (Async route handlers)
- **PDF & Excel Extraction:** PyMuPDF (`fitz`), `pdfplumber`, `openpyxl`, `pandas`
- **Rule Engines:** NumPy & Pandas pure functional engines
- **AI Integration:** Grounded structured JSON output via Ollama / local LLM
- **Testing:** Pytest (Unit tests for adapters & full pipeline integration test)

---

## 🚀 Quick Start & Installation

### **Prerequisites**
- Python 3.11+
- Node.js 18+ and npm
- Git

---

### **1. Local Development Setup**

#### **Backend Setup:**
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn main:app --reload --port 8000
```
> The API server will run at `http://localhost:8000`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

#### **Frontend Setup:**
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
> The React Dashboard application will run at `http://localhost:3000`.

---

### **2. Docker Containerized Setup**

Run the entire application (Frontend + Backend) using Docker Compose:

```bash
# Build and launch all services
docker compose up --build
```

- **Frontend Application:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`

---

## 🧪 Test Suite Execution

Run automated unit and integration tests across backend and frontend stacks:

### **Backend Unit & Integration Tests:**
```bash
cd backend

# Run adapter normalization unit tests (14/14 tests)
python tests/test_adapters.py

# Run full pipeline end-to-end integration test
python tests/test_full_pipeline.py
```

### **Frontend Test Suite:**
```bash
cd frontend

# Run Vitest test suite (13/13 tests)
npx vitest run
```

---

## 📊 Sample Test Dataset

The project repository includes sample synthetic banking datasets located in `backend/data/`:
- `sunrise_bank_dummy_dataset.pdf` (Clean & Seeded Bank Financial Statements)
- `horizon_financial_services_dummy_dataset.pdf` (NBFC Financial Statements)
- `meridian_capital_finance_dummy_dataset_values_only.xlsx` (Excel Dataset)

To test the application, launch the dashboard, click **"New Review"**, select `sunrise_bank_dummy_dataset.pdf`, and observe the live extraction, deterministic checks, findings, and auto-generated WP-514 working paper.

---

## 📜 License & Compliance

This project is developed for hackathon and technical demonstration purposes. All synthetic datasets used are fictional banking entities.
