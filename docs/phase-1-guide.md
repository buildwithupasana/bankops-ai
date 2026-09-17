# Phase 1 beginner guide

## What we built and why

A small, read-only banking system that answers factual questions such as "What happened to transaction TXN001?" It returns the stored facts, including PROCESSING, without inventing a cause. Later components can call these same service functions.

The terminal demonstration calls the service; the service reads JSON. Separating these responsibilities means changing how users interact with the application need not change how records are retrieved.

## Five concepts to understand

1. **JSON, lists, and dictionaries.** Each JSON file contains an array (`[...]`). `json.load(file)` converts it to a Python list. Each object (`{...}`) becomes a dictionary, so `transaction["status"]` retrieves a field. JSON is persistent text; Python objects live in memory.
2. **IDs and relationships.** CUST001 identifies a customer. ACC001 refers to CUST001. TXN001 refers to ACC001 and CUST001. A reference connects records without copying an entire customer into every account. Tests ensure those links agree.
3. **Functions and return contracts.** A function takes an input and returns a result. `dict | None` documents a single record or its absence. `list[dict]` documents multiple records; an empty list means no matches, including an unknown parent ID. Type hints document intent rather than enforcing runtime types.
4. **Modules, packages, and paths.** A `.py` file is a module; `__init__.py` marks a package. Importing `backend.banking.service` exposes its functions. `Path(__file__).resolve().parents[2]` finds the project root from the service file, so data loading does not depend on the working directory.
5. **Error handling and tests.** No matching ID is a normal result. Broken storage raises `BankingDataError`. Tests use `assert` for expected facts and `pytest.raises` for expected errors. Integer amounts avoid floating-point rounding; `divmod(amount_minor, 100)` splits whole and fractional units for display.

## Walk through the service

Start with `get_transaction("TXN001")`. It calls `_find_record` with the filename, the field to search, and the requested ID. `_find_record` asks `_load_records` to read JSON, loops over the records, and returns the matching dictionary. If the loop ends without a match, it returns `None`.

An underscore in `_load_records` is a convention meaning "internal helper." Sharing helpers keeps the three single-record functions consistent. The loader opens a file using `with`, which closes it automatically, even if an error occurs. The `try`/`except` block translates file and JSON failures into a clear banking-data error.

`get_customer_accounts` uses a list comprehension: read it as "collect each account whose customer_id matches." It returns every match instead of stopping after the first. `get_account_transactions` follows the same pattern.

The demonstration reads a command-line ID with `argparse`, calls the service, handles absent records or storage errors, and prints the returned dictionary with `json.dumps`. `json.load` reads JSON; `json.dumps` produces JSON text. The main guard prevents the terminal interface from running when another Python file imports the module.

## Five manual tests

Run these from the project root in PowerShell. The application requires no installed packages.

1. Retrieve the investigation example:

   ```powershell
   python bankops.py TXN001
   ```

   Expect CUST001, ACC001, 250000 minor units, AED 2,500.00, TRANSFER, and PROCESSING.

2. Retrieve the customer and its accounts:

   ```powershell
   python -c "from backend.banking.service import get_customer, get_customer_accounts; print(get_customer('CUST001')); print(get_customer_accounts('CUST001'))"
   ```

   Expect Synthetic Amal Noor in Dubai and accounts ACC001 and ACC011.

3. Retrieve an account and its transactions:

   ```powershell
   python -c "from backend.banking.service import get_account, get_account_transactions; print(get_account('ACC001')); print([t['transaction_id'] for t in get_account_transactions('ACC001')])"
   ```

   Expect an AED account owned by CUST001 and TXN001, TXN016, TXN031, TXN046.

4. Check all five functions with unknown IDs:

   ```powershell
   python -c "from backend.banking.service import get_customer, get_account, get_transaction, get_customer_accounts, get_account_transactions; print(get_customer('UNKNOWN'), get_account('UNKNOWN'), get_transaction('UNKNOWN')); print(get_customer_accounts('UNKNOWN'), get_account_transactions('UNKNOWN'))"
   ```

   Expect `None None None`, followed by `[] []`.

5. Check the terminal's not-found behavior:

   ```powershell
   python bankops.py TXN999
   $LASTEXITCODE
   ```

   Expect `Transaction not found: TXN999` and exit code `1`.

## Five interview questions

1. How does JSON become a Python list of dictionaries, and why keep data separate from code?
2. How do customer_id and account_id connect the three datasets, and how would you detect an invalid reference?
3. Why return None for one missing record but an empty list for a collection lookup?
4. How does a missing transaction differ from a malformed JSON file, and how does the caller handle each?
5. Why store money in integer minor units, and why does PROCESSING alone not prove a delay cause?

## Stop and explain it yourself

Follow TXN001 from the command line to its JSON record and back. Run the five manual tests, then explain the five concepts in your own words. Confirm this milestone works before we choose the next one.
