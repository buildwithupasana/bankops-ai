# Phase 1: prerequisites, professional answers, and lessons learned

These answers document the concepts requested in the phase brief and the lessons from implementing BankOps AI. They describe the current learning project, not a production banking system. Use the questions for self-assessment before reading the answers.

Phase 1 did not contain a separate prerequisite-topic list. The questions below are derived from its Python/JSON requirements and the follow-up questions asked during implementation.

## Prerequisite questions and professional answers

### 1. What are we building with Python and JSON?

We are building a small read-only banking service. JSON files store fictional customers, accounts, and transactions; Python functions retrieve records and related collections. This establishes deterministic data access before introducing an HTTP interface or an LLM.

### 2. What is JSON, and how does Python use it?

JSON is a language-independent text format for structured data. A JSON array becomes a Python list, and each JSON object becomes a dictionary. `json.load(file)` reads JSON from a file; `json.dumps(value)` converts a Python value into JSON text. A dictionary supports field access such as `transaction["status"]`.

### 3. Why separate JSON data from lookup code?

Data and behavior change for different reasons. Separating them allows records to change without editing lookup functions, makes testing easier, and gives future storage changes a clear boundary. Replacing JSON with a database would still require implementation work, but callers could retain familiar service interfaces.

### 4. How do we verify that a transaction belongs to the correct customer?

Find the account referenced by the transaction's account_id, confirm that the account exists, and compare its customer_id with the transaction's customer_id. Then confirm that the customer exists. For example, TXN001 refers to ACC001, which belongs to CUST001. Tests also check unique identifiers and currency consistency. These checks establish data integrity, not permission for a logged-in user to access a record.

### 5. Why return None for a missing record but [] for a collection?

A single-record lookup promises one record or its absence, represented by None. A collection lookup promises a list; zero matches are represented by an empty list. Consistent return contracts simplify calling code. At the service layer, an unknown parent also produces an empty collection; the HTTP layer later adds explicit parent-existence checks.

### 6. How does a missing transaction differ from a damaged JSON file?

A missing transaction means a valid dataset was searched successfully and contained no matching ID. Damaged or unreadable JSON means the search could not be completed. Returning None for both would hide operational failures. The service returns None for absence and raises BankingDataError for a loading failure.

### 7. Why store money as integer minor units?

Binary floating-point values cannot represent every decimal fraction exactly. Integer minor units avoid that problem for stored amounts. In the supported two-decimal currencies, 250000 minor units represents 2500 whole units. Currency-specific rules must be considered before expanding this convention to other currencies.

### 8. Why cannot PROCESSING alone explain a payment delay?

A status describes a state, not the full history or cause. PROCESSING does not establish which step is waiting, whether a deadline has passed, or whether the beneficiary received funds. A defensible explanation would require additional evidence such as events and timestamps. This phase retrieves facts without making that inference.

### 9. What are modules, packages, and imports?

A Python file is a module. An __init__.py file marks a regular package containing related modules. An import makes a module's functions available in another execution context. Importing get_customer does not execute a lookup; calling get_customer("CUST001") does.

## Lessons learned: practical Q&A

### Why did PowerShell reject the word from?

Python import syntax was entered into PowerShell. A prompt beginning with PS accepts shell commands. Start Python with `python`, wait for `>>>`, then enter the import and function call. Activating `.venv` selects a Python environment but does not start the interpreter.

```powershell
python
```

Then, inside Python:

```python
from backend.banking.service import get_customer
get_customer("CUST001")
exit()
```

### How do I run a Python lookup directly from PowerShell?

Use Python's `-c` option and print the result. This executes Python code without opening an interactive interpreter.

```powershell
python -c "from backend.banking.service import get_customer_accounts; print(get_customer_accounts('CUST001'))"
```

### What does $LASTEXITCODE mean?

It is PowerShell's stored exit code from the last native program. In our terminal demonstration, 0 means a successful lookup, 1 means a missing transaction, and 2 means an argument or banking-data error. These values describe process completion; they are not HTTP status codes.

### Why resolve data paths relative to the service file?

The terminal's current folder can vary. Resolving the data directory from __file__ makes data loading depend on the project's layout rather than where a caller happens to run Python. The module still needs to be importable by the caller.

### What did our integrity tests establish, and what did they not establish?

They checked the supplied synthetic fixtures: record counts, unique IDs, valid links, supported values, and expected lookup behavior. They did not implement full validation for arbitrary imported data, account balances, settlement, or double-entry accounting. Test scope should be stated explicitly.

## Learning checkpoint

- [ ] Explain a lookup from JSON file to returned dictionary.
- [ ] Run both a shell command and an interactive Python call correctly.
- [ ] Distinguish missing data from failed data access.
- [ ] Explain relationship integrity and integer amounts.
- [ ] Explain why a status is not evidence of a delay cause.

[Return to the Phase 1 implementation guide](phase-1-guide.md)
