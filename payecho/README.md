# PayEcho — AI Revenue Recovery Platform

PayEcho is a prototype for finance/accounts-receivable teams. It combines SQLite account history, Hindsight Cloud persistent memory, and a Groq-powered recovery assistant to produce customer-specific recovery guidance.

## What is implemented

- Streamlit three-column dashboard: customer list, account/memory detail, AI Recovery Assistant.
- SQLite schema with `customers`, `invoices`, `interactions`, `promises`, and `recovery_actions`.
- Synthetic seed data for five customers, including multi-step histories.
- Backend service functions: `get_customer`, `get_invoice_summary`, `get_interactions`, `retain_interaction`, `recall_customer_memory`, and `record_outcome`.
- Real Hindsight Cloud integration through the official `hindsight-client` package. Each customer gets a separate memory bank so recalled memories cannot cross customer boundaries.
- Groq recovery agent with the required structured output and a safe local fallback when no API key is configured.
- Outcome recording writes to SQLite and retains the new outcome in Hindsight.
- Analytics chart and risk/overdue heuristics.
- Unit tests for the database/service layer, memory adapter fallback, and agent contract.

## Setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python database/setup_db.py
```

Create a local `.env` from `.env.example` and add your real keys:

```env
HINDSIGHT_API_KEY=your_hindsight_key
GROQ_API_KEY=your_groq_key
```

Do **not** commit `.env` or real API keys.

## Run

```bash
streamlit run app.py
```

Then:

1. Select a customer.
2. Review invoices, interactions, promises, and AI Customer Memory.
3. Ask the Recovery Assistant a question.
4. Generate the recommendation.
5. Edit the draft message if needed.
6. Record the real/simulated outcome.
7. The outcome is stored in SQLite and retained in that customer's Hindsight memory.
8. On a later interaction, recall can use that new memory.

## Tests

```bash
pytest -q
```

## Memory integration

The Hindsight adapter uses the current official Python client and the managed API base URL. The app creates a customer-scoped bank such as `payecho_c01`, retains meaningful payment/recovery history into that bank, and recalls from the same bank. This keeps the memory boundary explicit.

## Prototype honesty

- Customer, invoice, interaction, promise, and outcome data are synthetic seed/demo data.
- The customer does not log into the application.
- PayEcho drafts messages; it does not send them automatically.
- Hindsight memory is customer-scoped.
- Risk/priority is a simple rule-based heuristic, not a trained ML model.
