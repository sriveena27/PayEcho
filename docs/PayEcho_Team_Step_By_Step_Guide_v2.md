# PayEcho — Team Step-by-Step Guide (v2)

One page per teammate. Do the steps in order. Don't skip ahead. Use this together with **PayEcho_Project_Specification_and_Module_Contracts_v2.md** — that file is the source of truth for architecture, schema, and contracts; this file tells you what to personally do, in what order.

---

## Before Anyone Starts — Everyone Does This Once

Do this once, together if possible, so everyone has the exact same setup.

### Step 1: Install the basics (if you don't already have them)
- Python 3.11 or newer — python.org
- Git — git-scm.com
- A GitHub account (free) — this is where the shared code lives
- Your AI coding assistant of choice (e.g. Claude Code / Antigravity / whatever your team uses)

### Step 2: Create the shared GitHub repository
- One person creates a new repository, e.g. `payecho`
- That person adds the other teammates as collaborators (GitHub → Settings → Collaborators)
- Everyone else clones it:
```
git clone <the repo link your teammate sends you>
```

### Step 3: Create the folder structure
Inside the project folder, create these empty folders:
```
ui/
database/
memory/
agent/
data/
tests/
docs/
```

### Step 4: Create the `.gitignore` file FIRST — before anything else
Create a file named exactly `.gitignore` in the main project folder and paste:
```
.env
__pycache__/
*.pyc
.venv/
*.db-journal
```
Do this **before** you create your `.env` file in the next step. Order matters.

### Step 5: Get the API keys sorted
- **Hindsight Cloud:** one person registers, verifies, gets the API key.
- **LLM (Groq or equivalent):** one person registers, gets the API key.
- Share both keys with the team **privately** (WhatsApp / private note) — never paste them into GitHub, a shared chat, or any file that gets committed.

### Step 6: Each person creates their own `.env` file
In the main project folder, create a file named exactly `.env`:
```
HINDSIGHT_API_KEY=paste_the_real_key_here
GROQ_API_KEY=paste_the_real_key_here
```
Everyone has their own copy on their own laptop. It is never uploaded to GitHub — the `.gitignore` from Step 4 makes sure of that automatically.

### Step 7: Get the shared documents
Make sure everyone has the **Project Specification & Module Contracts v2** doc and this guide. Keep both in the `docs/` folder.

**Checklist:**
- [ ] Python, Git, GitHub account, coding assistant installed
- [ ] Shared GitHub repo created and everyone added as collaborator
- [ ] Folder structure created
- [ ] `.gitignore` created FIRST
- [ ] Hindsight + LLM API keys obtained and shared privately
- [ ] Personal `.env` file created (not uploaded to GitHub)
- [ ] Spec doc + this guide saved in `docs/` folder

Once all 7 steps are done by everyone, move to your own personal page below.

---

## PERSON A — Frontend / Streamlit UI

**What you're actually building, in plain words:**
You're building the screen the employee actually looks at — the customer list, the customer detail page, the Hindsight memory card, and the AI Recovery Assistant panel where the recommendation and draft message appear. You do **not** need to implement Hindsight, database internals, or LLM logic yourself.

**Use:** Python + Streamlit + Plotly/Streamlit charts.

### Step 1: Open your coding assistant in the `ui/` folder
### Step 2: Attach the Spec doc and ask it to build the screens listed in Section 6, Module 1 of the spec
It should generate: the customer list/search page, the customer detail page (three-column layout), the memory card, the AI Assistant panel, the outcome form, and the analytics charts.

### Step 3: Build the UI first with dummy/hardcoded data
- Hardcode 3–5 fake customers with different risk levels
- Hardcode a fake memory timeline and a fake AI recommendation
- Get the full navigation and layout working before wiring anything real

### Step 4: Make customer selection and forms work
- Clicking a customer in the list shows their detail page
- The outcome form actually captures input (even if it just prints to console for now)

### Step 5: Once Person B pushes real data, swap in the real service functions
```
git pull
```
Replace your dummy data calls with `get_customer()`, `get_invoice_summary()`, `get_interactions()` from Person B's module.

### Step 6: Once Person C pushes the agent, wire up the AI Assistant panel
Replace your hardcoded recommendation with a real call to `recover(...)`.

### Step 7: Polish
Spacing, labels, card layout, chart formatting. Test every user flow: search → select customer → read memory → ask question → get recommendation → edit message → record outcome.

### Step 8: Push your code
```
git add ui/
git commit -m "Frontend: Streamlit UI working"
git push
```

**Checklist:**
- [ ] Coding assistant session started with the spec doc attached
- [ ] All screens built with dummy data first
- [ ] Customer selection and outcome form working
- [ ] Swapped in real data from Person B
- [ ] Swapped in real recommendations from Person C
- [ ] All user flows tested end to end
- [ ] Code pushed to GitHub, team notified

---

## PERSON B — Backend + Database + Hindsight

**What you're actually building, in plain words:**
You're the one who sets up the shared "notebook" (SQLite database) that holds customer, invoice, interaction, promise, and outcome data — and you connect it to Hindsight so the AI can actually remember things across interactions.

### Step 1: Open your coding assistant in the `database/` and `memory/` folders
### Step 2: Attach the Spec doc and ask it to build:
- A script that creates `payecho.db` with the five tables from Section 4 of the spec (`customers`, `invoices`, `interactions`, `promises`, `recovery_actions`)
- A script that generates realistic synthetic seed data (at least 5–10 customers with varied risk levels, invoices, and a multi-step interaction history for at least 2–3 customers so the memory demo has something to recall)
- The service functions listed in Section 6, Module 2 of the spec:
```python
get_customer(customer_id)
get_invoice_summary(customer_id)
get_interactions(customer_id)
retain_interaction(customer_id, text, metadata)
recall_customer_memory(customer_id, query)
record_outcome(customer_id, outcome)
```

### Step 3: Run the schema + seed script
```
pip install -r requirements.txt
python database/setup_db.py
```

### Step 4: Check it worked
Open `payecho.db` with a free tool like "DB Browser for SQLite" and confirm all five tables have real rows, not empty.

### Step 5: Connect Hindsight
- Implement `retain_interaction()` — write meaningful interaction summaries, promises, and outcomes into Hindsight, tagged by `customer_id`.
- Implement `recall_customer_memory()` — retrieve memories relevant to a customer and a query, and format them into a clean list (e.g. `[{date, summary, type}, ...]`) that both the frontend and the agent can use directly.

### Step 6: Test the memory loop yourself, standalone
Retain 2–3 fake interactions for one test customer, then recall them, and confirm the recalled memory actually reflects what you retained. This is the core mechanic of the whole project — get it right before anyone else depends on it.

### Step 7: Push your code
```
git add database/ memory/ data/
git commit -m "Backend: database + Hindsight retain/recall working"
git push
```
Tell Person A and Person C in the group chat the moment this is pushed — they're waiting to swap out their mock data.

**Checklist:**
- [ ] Coding assistant session started with the spec doc attached
- [ ] `payecho.db` created with all five tables
- [ ] Synthetic seed data checked and looks realistic
- [ ] All six service functions implemented and tested standalone
- [ ] Retain → Recall loop verified with a test customer
- [ ] Code pushed to GitHub, team notified

---

## PERSON C — AI Agent + LLM + Recovery Logic

**What you're actually building, in plain words:**
You're teaching the system to take a customer's current situation plus what Hindsight remembers about them, and turn that into a specific, personalized recommendation and draft message — not a generic reminder.

### Step 1: Open your coding assistant in the `agent/` folder
### Step 2: Attach the Spec doc and ask it to build the `recover()` function from Section 6, Module 3
### Step 3: Build against mocked memory first
Hardcode a fake `recalled_memory` list (e.g. "customer cited cash-flow issue on Sep 10", "customer promised payment by Sep 27, missed") so you're not blocked waiting on Person B.

### Step 4: Write the recovery-agent system prompt
It should combine: current account facts + recalled memory + the employee's question, and return the structured dict:
```python
{
  "summary": str,
  "action": str,
  "reason": str,
  "tone": str,
  "message": str,
  "memory_evidence": list
}
```

### Step 5: Run it and check the output makes sense
```
pip install -r requirements.txt
python agent/test_recover.py
```
Confirm the output is valid structured data (not free-form text you have to parse by hand) and that `memory_evidence` actually references the mock memories you gave it.

### Step 6: Build the before/after demo case
Run the same customer question **with an empty memory list** vs. **with the mock memory list**, and confirm the recommendation is visibly more generic without memory and visibly more personalized with it. This is your key deliverable for the demo story.

### Step 7: Add basic error handling
What happens if the LLM call times out or returns something malformed? Don't let it crash the whole app — return a safe fallback message.

### Step 8: Once Person B pushes real data, swap in the real `recall_customer_memory()`
```
git pull
```
Point your agent at real recalled memory instead of your mock list, and re-test.

### Step 9: Push your code
```
git add agent/
git commit -m "Agent: recover() function working with real memory"
git push
```

**Checklist:**
- [ ] Coding assistant session started with the spec doc attached
- [ ] `recover()` built and tested against mock memory
- [ ] Structured output format matches the contract exactly
- [ ] Before/after (no-memory vs. with-memory) demo case working
- [ ] Basic LLM error handling added
- [ ] Swapped in real memory from Person B
- [ ] Code pushed to GitHub, team notified

---

## INTEGRATION — Do This After All Three Modules Are Individually Working

*(Whoever is coordinating integration — could be any one person, or shared)*

### Step 1: Pull everyone's latest code
```
git pull
```

### Step 2: Wire Person B's functions into Person A's UI
Replace dummy data calls in `ui/` with real calls to `get_customer()`, `get_invoice_summary()`, `get_interactions()`, `record_outcome()`.

### Step 3: Wire Person C's `recover()` into Person A's AI Assistant panel
The employee's typed question + selected customer's data + recalled memory should flow into `recover()` and the result should render in the panel.

### Step 4: Run the full app end to end
```
streamlit run app.py
```

### Step 5: Test the full flow like an examiner would
- Select a customer with a real interaction history → confirm the memory card shows it
- Ask the AI Assistant a question → confirm a sensible, memory-grounded recommendation appears
- Edit and "send" the draft message → record an outcome
- Select a **new** customer with no history → confirm it doesn't crash, just shows a sensible "no prior interactions" state

### Step 6: Run the memory-learning demo end to end
This is the centerpiece of the demo — walk through it exactly like a judge would see it:

1. **Interaction 1:** enter that the customer explained why payment is delayed.
2. **Interaction 2:** enter that the customer gave a payment promise.
3. **Interaction 3:** the promised date has passed with no payment.
4. Employee asks: "What should I do?"
5. Confirm Hindsight recalls the previous reason and promise (visible in the memory card).
6. Confirm the AI recommends a specific action and drafts a message referencing the prior commitment — not a generic reminder.
7. Employee records the outcome.
8. Confirm the new outcome becomes part of that customer's memory for future interactions.

### Step 7: Do a full team walkthrough call
Everyone explains their own module out loud, in plain words, no code — this is a practice viva/Q&A for each other. Write down any question someone couldn't answer smoothly, and go fix that understanding before the real presentation.

### Step 8: Assign the documentation/demo-script rotation
Confirm who's writing which part of the report/PPT and keep a shared checklist of what's done.

**Checklist:**
- [ ] All three modules pulled and wired together
- [ ] Full app runs end to end without errors
- [ ] "New customer, no history" edge case handled gracefully
- [ ] Full memory-learning demo (interactions 1→3→recommendation) tested and works
- [ ] Team walkthrough call done, weak spots identified and fixed
- [ ] Documentation/demo rotation confirmed

---

## If Something Goes Wrong

This is completely normal — nobody's code works perfectly the first time.

### Step 1: Read the actual error message
It usually tells you exactly what's wrong — read the last line first, not the whole wall of text.

### Step 2: Paste the exact error back into your coding assistant
Just copy-paste it and say "this error happened, please fix it."

### Step 3: Check the Spec doc
Most cross-module bugs happen because someone's table/column name or function signature doesn't match what's written there — compare carefully against Section 4 and Section 6.

### Step 4: Ask in the team group chat before spending more than 20–30 minutes stuck alone
Someone else may have hit the exact same issue already.
