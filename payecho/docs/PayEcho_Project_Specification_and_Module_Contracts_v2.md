# PayEcho — Project Specification & Module Contracts (v2)
### AI Revenue Recovery Platform — Shared Source of Truth

**This is the single source of truth for the team.** Every module must follow these exact table/column names, function signatures, and I/O formats so the pieces plug into each other without last-minute rewiring. If you need to change something here, agree as a team first and update this doc — don't silently change your own module's format.

---

## Table of Contents

1. Core Concept — What Are We Building?
2. The Interface (Finalized)
3. Tech Stack & Setup
4. Database Schema (SQLite)
5. Hindsight Memory Design
6. Module Ownership & I/O Contracts
7. Environment / API Keys
8. Repository Structure
9. Data Flow (End to End)
10. AI Agent — Input / Output Contract
11. Working in Parallel Without Blocking Each Other
12. Honesty Checklist for Documentation
13. Quick Reference — Who Owns What

---

## 1. Core Concept — What Are We Building?

PayEcho is an **AI Revenue Recovery Platform** for a company's finance / accounts-receivable / collections employees.

Customers sometimes miss invoice payments, ask for extensions, give reasons for delay, or make promises they don't keep. Instead of every follow-up being a generic reminder, PayEcho **remembers the entire payment relationship** with each customer (using Hindsight persistent memory) and uses that memory to generate a personalized recovery recommendation and follow-up message.

**Core product story:** the agent should become more useful after repeated interactions because it can recall what happened before. Hindsight memory must be visible on screen and central to the demo — this is not an optional add-on, it is the point of the project.

### Who uses it
- **Primary user:** the company employee (AR / finance / collections / revenue ops).
- **The customer does not log in.** Customer conversations are simulated/entered by the employee for the prototype.

---

## 2. The Interface (Finalized)

This is the agreed, final interface. Do not redesign it independently — if a change is needed, raise it with the team first.

**Screen 1 — Customer List**
```
 AI REVENUE RECOVERY
 Search customer: [ ABC Ltd            🔍 ]
 ---------------------------------------------
 ABC Ltd          ₹80,000 overdue   🔴 High
 XYZ Pvt Ltd      ₹35,000 overdue   🟡 Medium
 PQR Solutions    ₹12,000 overdue   🟢 Low
```

**Screen 2 — Customer Detail (three-column layout)**

- **Left:** navigation + customer list (search/filter, risk color).
- **Center:** selected customer's account info (outstanding amount, invoice, due date, days overdue), interaction timeline, and the **AI Customer Memory** card (what Hindsight recalls — the previous reasons, extensions, promises, and outcomes, shown as a timeline).
- **Right:** **AI Recovery Assistant** — employee types a question (e.g. "What should I do about this customer?"), and the panel shows: Customer History summary → Recommended Action → Draft Message (editable) → buttons to record the outcome.

The employee can edit the drafted message and send it through their normal channel (email/phone/chat) — PayEcho does not send messages itself in v1.

---

## 3. Tech Stack & Setup — FINAL

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Python + Streamlit | Web dashboard, forms, cards, tables, charts, navigation |
| Backend / Application | Python | Business logic, orchestration, data access, agent workflow |
| Database | SQLite | Prototype customer, invoice, interaction, promise, recovery-action data |
| Persistent memory | Hindsight Cloud | Retain, Recall, and optional Reflect operations for customer memory |
| LLM | Groq (or another supported LLM API) | Reasoning, recommendation, and personalized message generation |
| Charts | Plotly / Streamlit charts | Recovery and account analytics |
| Secrets | python-dotenv + `.env` | Local API-key management |
| Testing | pytest | Unit and integration tests |
| Version control | Git + GitHub | Shared codebase across all laptops |

**Frontend framework decision:** Streamlit, intentionally — not React. Streamlit lets the frontend person build the whole interface in Python with no separate JavaScript app.

**Backend decision:** plain Python modules called directly by Streamlit. A separate FastAPI service is **not required** for v1 — it can be added later if needed, but it is not part of the required architecture for this build.

### Common `requirements.txt`
```
streamlit
pandas
numpy
plotly
python-dotenv
hindsight-client
requests
pytest
groq
```

---

## 4. Database Schema (SQLite)

All data lives in **one shared SQLite file: `payecho.db`**. Whoever builds the backend module creates this file first; everyone else reads/writes to it using these exact table names and columns.

### `customers`
| column | type | notes |
|---|---|---|
| customer_id | TEXT, primary key | e.g. "C01" |
| company_name | TEXT | |
| contact_name | TEXT | |
| email | TEXT | |
| segment | TEXT | e.g. SMB / Enterprise |
| status | TEXT | Active / Inactive |

### `invoices`
| column | type | notes |
|---|---|---|
| invoice_id | TEXT, primary key | e.g. "INV-1024" |
| customer_id | TEXT | FK to customers |
| amount | FLOAT | total invoice amount |
| due_date | TEXT (YYYY-MM-DD) | |
| outstanding_amount | FLOAT | amount still unpaid |
| status | TEXT | Paid / Overdue / Partially Paid |

### `interactions`
| column | type | notes |
|---|---|---|
| interaction_id | INTEGER, autoincrement | |
| customer_id | TEXT | FK to customers |
| timestamp | TEXT (ISO format) | |
| channel | TEXT | email / phone / chat / simulated |
| summary | TEXT | free-text summary of what was said |
| outcome | TEXT (nullable) | e.g. "promise made", "no response" |

### `promises`
| column | type | notes |
|---|---|---|
| promise_id | INTEGER, autoincrement | |
| customer_id | TEXT | FK to customers |
| promised_date | TEXT (YYYY-MM-DD) | date customer committed to pay |
| amount | FLOAT | amount promised |
| status | TEXT | Pending / Kept / Missed |

### `recovery_actions`
| column | type | notes |
|---|---|---|
| action_id | INTEGER, autoincrement | |
| customer_id | TEXT | FK to customers |
| action_type | TEXT | e.g. "follow_up_sent", "escalation" |
| timestamp | TEXT (ISO format) | |
| outcome | TEXT (nullable) | recorded after the fact |

> **Note:** `interactions`, `promises`, and `recovery_actions` are the SQLite record of what happened — they are the source data that gets **retained into Hindsight** so the AI can recall it later. SQLite is the ledger; Hindsight is the memory the AI actually queries.

---

## 5. Hindsight Memory Design

- **Retain:** save meaningful customer interactions, promises, reasons for delay, outcomes, and relevant context — tagged to the customer.
- **Recall:** retrieve memories relevant to the selected customer and the current recovery question.
- **Reflect (optional):** a Hindsight-generated synthesis across many memories, used if the team wants a higher-level summary rather than raw recalled snippets.
- **Memory must be customer-scoped** — every retain/recall call is tagged or filtered by `customer_id`, never mixed across customers.
- **The UI must show the recalled memory** (the "AI Customer Memory" card) so it's visible *why* the AI's response changed — this is the whole point of the demo.

**The learning-curve demonstration this project must produce:**
first interaction → later interaction → increasingly personalized recovery guidance, visibly driven by what Hindsight recalls.

---

## 6. Module Ownership & I/O Contracts

Each module is a black box to the others: it reads specific tables/functions and writes specific tables/functions. As long as everyone follows the contract below, each person can build without waiting on the others — use mock/dummy data in the meantime (see Section 11).

### Module 1 — Frontend / Streamlit UI — Owner: Person A

**Input (reads, via agreed service functions only — never touches the DB or Hindsight directly):**
- `get_customer(customer_id)`, `get_invoice_summary(customer_id)`, `get_interactions(customer_id)` — from Person B
- `recover(customer_data, current_interaction, recalled_memory, employee_question)` — from Person C

**Output (writes, via agreed service functions):**
- Customer ID + form data → `record_outcome(customer_id, outcome)` (Person B)
- Customer context + employee question → `recover(...)` (Person C)

**Builds:**
- Customer list / search / filter (risk color-coded)
- Customer Detail page: account summary, invoice info, interaction timeline
- Hindsight Memory card
- AI Recovery Assistant panel (question box → summary → recommendation → draft message editor)
- Outcome-recording form
- Analytics charts (recovery progress, aging, promises kept/missed)

**Does not need to build:** Hindsight API calls, database schema/queries, or LLM prompt engineering.

---

### Module 2 — Backend + Database + Hindsight — Owner: Person B

**Input:** raw customer/invoice/interaction data (synthetic seed data for the prototype), plus outcome data submitted from the frontend.

**Output:** a populated `payecho.db` (all five tables above), plus a working Hindsight connection with Retain and Recall implemented.

**Builds / suggested service functions:**
```python
get_customer(customer_id)
get_invoice_summary(customer_id)
get_interactions(customer_id)
retain_interaction(customer_id, text, metadata)      # writes to Hindsight
recall_customer_memory(customer_id, query)            # reads from Hindsight
record_outcome(customer_id, outcome)                   # writes to SQLite + retains to Hindsight
```

**Must also handle:**
- SQLite schema creation + synthetic seed data generation
- Environment-variable / API-key handling for Hindsight
- Formatting recalled memory into a clean structure the frontend and AI agent can both consume (e.g. a list of `{date, summary, type}` dicts)

---

### Module 3 — AI Agent + LLM + Recovery Logic — Owner: Person C

**Input:** current account data + recalled Hindsight memory (both supplied by Person B, in predictable Python dicts) + the employee's question (supplied by Person A).

**Output:** a structured agent result returned to the frontend:
```python
recover(customer_data, current_interaction, recalled_memory, employee_question)
→ {
    "summary": str,            # situation summary
    "action": str,             # recommended next action
    "reason": str,             # why this action is recommended
    "tone": str,                # suggested tone (e.g. firm, empathetic)
    "message": str,             # personalized draft follow-up
    "memory_evidence": list     # which recalled memories the recommendation used
  }
```

**Builds:**
- LLM API connection (Groq or equivalent)
- Recovery-agent system prompt combining current facts + recalled memory + employee question
- Structured output schema (the dict above)
- Simple priority/risk heuristics (e.g. flag customers whose promise date has passed)
- Before-memory vs. after-memory test cases for the demo
- LLM/API error handling (timeouts, malformed responses)

---

## 7. Environment / API Keys

- **Hindsight Cloud:** one person registers the account/API key and shares it privately (WhatsApp/Drive DM — **never in the repo or in a public chat**).
- **LLM API (Groq or equivalent):** same rule — registered once, shared privately.
- Every team member creates their **own local `.env` file**:
```
HINDSIGHT_API_KEY=paste_the_real_key_here
GROQ_API_KEY=paste_the_real_key_here
```
- **Add `.env` to `.gitignore` immediately — before your first commit.** This is the single most common way student/hackathon teams accidentally leak API keys on GitHub.

---

## 8. Repository Structure

```
payecho/
├── app.py
├── requirements.txt
├── .env                      (not committed)
├── .gitignore
├── data/
├── database/                 (Person B)
├── memory/                   (Person B — Hindsight retain/recall)
├── agent/                    (Person C — LLM + recovery logic)
├── ui/                       (Person A — Streamlit screens)
├── tests/
└── docs/
    └── this spec doc + step-by-step guide + report/PPT drafts
```

---

## 9. Data Flow (End to End)

```
Employee opens PayEcho
        ↓
Employee selects a customer
        ↓
Backend retrieves current customer/invoice info from SQLite
        ↓
Backend builds a focused memory query
        ↓
Hindsight recalls relevant previous interactions
        ↓
Agent receives: current facts + recalled memory + employee question
        ↓
LLM returns: situation summary + recommended action + reason + tone + message
        ↓
Streamlit displays the result (with memory evidence visible)
        ↓
Employee records the outcome
        ↓
The new outcome is retained in Hindsight for future interactions
```

---

## 10. AI Agent — Input / Output Contract (Reference)

**Input:** customer profile + current invoice state + days overdue + recent interaction + recalled Hindsight memories + employee question.

**Output:** situation summary + recommended next action + reason + suggested tone + personalized follow-up message + memory evidence used.

This is the same contract defined in Section 6, restated here for quick reference since it's the most-checked contract during integration.

---

## 11. Working in Parallel Without Blocking Each Other

Since the Agent (Module 3) needs the Backend's (Module 2) output, and the Frontend (Module 1) needs both, don't wait in sequence:

1. **Day 1 (first hour):** Agree on this spec as a team. Person B starts the SQLite schema and synthetic data.
2. **In parallel:**
   - Person A builds the full Streamlit UI against **dummy/hardcoded data** (fake customer list, fake memory card, fake recommendation).
   - Person C builds the agent against a **mocked `recalled_memory` list** (just hardcode 3–4 fake memory snippets) so they don't wait on Hindsight being wired up.
3. **Mid-point:** Person B finishes real SQLite + Hindsight Retain/Recall and pushes.
4. **Swap-in:** Person A and Person C replace their mock data calls with Person B's real service functions. If everyone followed the contracts in Section 6, this should be a near-zero-friction swap.
5. **Final:** full integration test, then the memory-learning demo (Section 12 in the step-by-step guide).

---

## 12. Honesty Checklist for Documentation

Say these explicitly in your report/demo — don't let a judge "discover" them:

- Customer data, interactions, and promises are **synthetic/seed data** for this prototype, not real company data.
- The customer never logs into the application — all customer-side conversation is entered/simulated by the employee.
- PayEcho **drafts** the follow-up message; it does not send it automatically. Sending remains a manual step by the employee.
- Hindsight memory is **customer-scoped** — memories are never shared or mixed across customers.
- Any risk/priority heuristic (e.g. flagging missed promises) is a **simple rule-based heuristic**, not a trained ML model, unless the team explicitly adds one.

---

## 13. Quick Reference — Who Owns What

| Person | Module(s) | Key Deliverable |
|---|---|---|
| Person A | Frontend / Streamlit UI | Full working dashboard reading from real service functions |
| Person B | Backend + Database + Hindsight | Populated `payecho.db` + working Retain/Recall |
| Person C | AI Agent + LLM + Recovery Logic | `recover()` function returning the structured result, integrated into the UI |

**Shared-reference rule:** This document is the master specification. If a team member starts work on a different laptop or in a different chat, upload this file first. The same technology stack, architecture, schema, and contracts must be followed. If a change is agreed later, update this master file and redistribute it so there is only one current source of truth.
