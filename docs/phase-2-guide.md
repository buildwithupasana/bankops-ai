# Phase 2: Banking REST APIs

## What and why

Expose our existing JSON banking service through six read-only HTTP endpoints. An API is a defined interface that another program can call. A future AI application can retrieve facts through it; no AI is implemented here. HTTP APIs are useful for separating systems, but are not a requirement for every AI program.

FastAPI is the Python web framework that maps URLs and HTTP methods to functions. Uvicorn is the server that listens for HTTP requests and runs the FastAPI application. Pydantic describes and validates the response data contracts.

## Concepts

| Concept | Explanation |
| --- | --- |
| Request | The caller's message: HTTP method, URL, headers, and optionally a body. Our GET calls need no body. |
| Response | The server's reply: status code, headers, and body, usually JSON here. |
| GET | Retrieve information without requesting a state change. |
| POST | Submit information for processing or creation; no POST endpoint is implemented here. |
| JSON | A text format of objects, arrays, strings, numbers, booleans, and null. Python dictionaries become JSON response objects. |
| REST | A resource-oriented API design style using standard HTTP methods and stateless requests. Each request supplies the information needed to handle it. |
| OpenAPI | A machine-readable description of paths, methods, fields, and responses, available at `/openapi.json`. |
| Swagger UI | The interactive documentation at `/docs`, generated from OpenAPI. |

| HTTP code | Meaning here |
| --- | --- |
| 200 | Successful retrieval, including an empty collection for an existing parent. |
| 404 | Unknown customer, account, transaction, or URL. |
| 405 | Unsupported method, such as POST to a GET-only route. |
| 422 | Request validation failure if an input violates declared constraints. IDs currently accept any string, so an unknown ID returns 404. |
| 500 | Server failure, such as missing/malformed JSON or invalid response data. |

HTTP codes are part of an HTTP response. They are different from PowerShell `$LASTEXITCODE`; curl can successfully receive a 404 response while exiting with code 0. Use `curl.exe -i` to inspect HTTP status.

## Request flow

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI route
    participant Service as Banking service
    participant Data as JSON data
    User->>API: GET /transactions/TXN001
    API->>Service: get_transaction("TXN001")
    Service->>Data: Read transactions.json
    Data-->>Service: Records
    Service-->>API: Matching dictionary
    Note over API: Validate with Transaction model; serialize to JSON
    API-->>User: HTTP 200 + JSON response
```

`backend/main.py` creates the application, includes the router, and translates banking-data and response-validation exceptions into a generic HTTP 500 response. Details are logged on the server rather than returned to the caller.

`backend/banking/routes.py` maps URLs to functions using decorators such as `@router.get(...)`. `{transaction_id}` is a path parameter: FastAPI extracts TXN001 and passes it to the function. Routes call service functions and translate None into HTTPException(404). Collection routes first check whether the parent exists.

`backend/banking/models.py` defines Pydantic BaseModel subclasses, which describe required response fields. `Literal` restricts values to listed currencies or statuses. `Field(gt=0, strict=True)` requires a positive integer amount. `AwareDatetime` requires a timestamp with a timezone. These are response contracts, not database tables. A response that violates the contract is a server error, not invalid client input.

The service remains responsible for JSON loading and lookups. The router does not open files. Synchronous `def` routes are appropriate for our synchronous file service; FastAPI runs these route functions in a thread pool. The small JSON datasets are still loaded for each lookup.

## Run from PowerShell

If your prompt is `>>>`, type `exit()` first. From the project root, create `.venv` only if it is absent with `python -m venv .venv`.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

`backend.main:app` means the `app` object in `backend/main.py`. `--reload` restarts the development server when code changes. Leave this terminal running. Open a second PowerShell terminal for the examples below. Stop the server with Ctrl+C.

## Test every endpoint

Use `curl.exe` on Windows to avoid PowerShell's possible `curl` alias. Each response should have HTTP status 200.

```powershell
curl.exe -i http://127.0.0.1:8000/health
curl.exe -i http://127.0.0.1:8000/customers/CUST001
curl.exe -i http://127.0.0.1:8000/customers/CUST001/accounts
curl.exe -i http://127.0.0.1:8000/accounts/ACC001
curl.exe -i http://127.0.0.1:8000/accounts/ACC001/transactions
curl.exe -i http://127.0.0.1:8000/transactions/TXN001
```

Expect, respectively: `{"status":"ok"}`; Synthetic Amal Noor; ACC001 and ACC011; ACC001 owned by CUST001; TXN001/TXN016/TXN031/TXN046; TXN001 with amount_minor 250000, currency AED, and status PROCESSING.

For Postman, select GET, paste any URL above, and click Send. No request body is needed.

## Five manual checks

1. Run all six requests above; confirm 200 and the expected records.
2. Request `/transactions/TXN999`; expect 404 and `{"detail":"Transaction not found: TXN999"}`.
3. Request `/customers/UNKNOWN/accounts` and `/accounts/UNKNOWN/transactions`; expect 404, not empty success responses.
4. Run `curl.exe -i -X POST http://127.0.0.1:8000/transactions/TXN001`; expect 405.
5. Open http://127.0.0.1:8000/docs, expand GET /transactions/{transaction_id}, click Try it out, enter TXN001, and Execute. Confirm 200. Repeat with TXN999 for 404. Inspect schemas at the bottom and open `/openapi.json` to see their source description.

Swagger's default JavaScript and CSS load from a CDN, so the interactive page requires browser access to those assets. API calls and OpenAPI JSON are served locally.

## Automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

FastAPI TestClient sends requests to the application inside the test process; no running server is required. HTTPX supports that client. Tests cover real JSON lookups, missing parents, existing parents with empty collections, unreadable/malformed data, invalid response fields, disallowed methods, Swagger HTML and OpenAPI contracts. Temporary test files do not change the project dataset. Earlier service and terminal tests still run.

## Common errors

- Connection refused: start Uvicorn and leave it running; check the port.
- No module named fastapi or uvicorn: install requirements with the same `.venv` Python used to launch the server.
- Could not import backend.main: run from the project root.
- Port already in use: stop the other server or use `--port 8001` and update URLs.
- 404: check the path and case-sensitive ID; `/` itself has no route.
- 500: inspect the server log and JSON data; it does not mean the transaction is absent.
- Blank Swagger UI: check whether the browser can load its CDN assets.

## Learning checklist

- [ ] Explain request versus response and GET versus POST.
- [ ] Follow TXN001 from its URL through route, service, JSON, validation, and response.
- [ ] Explain why an unknown parent returns 404 but an existing parent may return 200 with [].
- [ ] Explain response models, OpenAPI, and Swagger UI.
- [ ] Run every endpoint, read HTTP status codes, and run the tests.

## Five interview questions

1. What separate jobs do Uvicorn, FastAPI routes, and the banking service perform?
2. Why should a GET request avoid requesting a state change?
3. Why do an unknown transaction and a malformed data file produce different HTTP codes?
4. How do Pydantic response models help clients and API documentation?
5. Why must a collection endpoint check its parent before returning an empty list?

## Milestone checkpoint

Completed scope: Phase 2 only. Next: Phase 3 LLM integration, only after you confirm Phase 2 works and you understand this checklist.

Suggested commit: `feat: expose banking lookups through FastAPI with response models and tests`

Official references: [First steps](https://fastapi.tiangolo.com/tutorial/first-steps/), [Response models](https://fastapi.tiangolo.com/tutorial/response-model/), [HTTP errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), [Testing](https://fastapi.tiangolo.com/tutorial/testing/).
