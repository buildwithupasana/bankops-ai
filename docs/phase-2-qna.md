# Phase 2: prerequisites, professional answers, and lessons learned

These answers document the concepts requested in the phase brief and the lessons from implementing BankOps AI. They describe the current learning project, not a production banking system. Use the questions for self-assessment before reading the answers.

The prerequisite questions below cover every concept explicitly requested before Phase 2 implementation.

## Prerequisite questions and professional answers

### 1. What is FastAPI?

FastAPI is a Python framework for building HTTP APIs. It maps methods and URL paths to Python functions and integrates validation and API documentation. In BankOps, the route accepts an identifier, calls the banking service, and returns an HTTP response. Uvicorn is the server that listens for incoming connections and runs the application.

### 2. Why does an AI application need APIs?

An AI application often needs a defined interface for obtaining facts from other systems. An API lets a caller request a transaction without knowing how it is stored. It also creates a place to introduce authentication, validation, and access policies later. Not every AI application requires HTTP APIs: a local Python program can call functions directly. We introduced HTTP to establish a reusable system boundary.

### 3. What is a request, and what is a response?

An HTTP request contains a method, URL, headers, and optionally a body. The response contains a status code, headers, and optionally a body. For example, GET /transactions/TXN001 asks for a transaction; a successful response contains HTTP 200 and a JSON representation of that record.

### 4. What is the difference between GET and POST?

GET retrieves a resource and should not request a change to application state. POST submits data for processing or creation. Phase 2 uses GET for banking lookups. Phase 3 uses POST to submit a complaint for classification. A POST operation does not necessarily create a database record. Sensitive data should not be assumed safe merely because it is in a POST body; transport security and handling policies are separate concerns.

### 5. What do HTTP status codes tell a client?

Status codes communicate the outcome at the HTTP boundary. BankOps uses 200 for successful retrieval, 404 for an unknown resource, 405 for an unsupported method, 422 for invalid request input, and 500 for server-side data failures. A caller should inspect both the code and the documented response body. HTTP status does not establish whether a payment itself succeeded.

### 6. What is JSON in an API?

JSON is the serialized representation exchanged between client and server. Python dictionaries and lists become JSON objects and arrays in the response body. A Pydantic model describes the expected fields and types; it is separate from the serialized JSON and from a database table. The response typically identifies its format with Content-Type: application/json.

### 7. What is REST?

REST is an architectural style organized around resources, representations, and a uniform interface. Our API applies resource-oriented URLs and standard HTTP methods: /customers/CUST001 identifies a customer, and /customers/CUST001/accounts identifies its account collection. Requests are independent rather than relying on a conversational session. Using JSON alone does not make an API RESTful.

### 8. What are OpenAPI and Swagger?

OpenAPI is a machine-readable API description specifying paths, operations, parameters, schemas, and responses. Swagger UI renders that description as an interactive browser interface. In this project, /openapi.json serves the specification and /docs serves Swagger UI. The documentation is generated from the route and model declarations, but actual behavior still needs testing.

## Lessons learned: practical Q&A

### Why keep the route separate from the banking service?

The route translates HTTP concerns: path parameters, status codes, and serialization. The service handles banking lookups and file access. This keeps the service usable from both the terminal and API and avoids coupling data logic to a web framework.

### Why check the parent before returning an account or transaction collection?

An unknown customer is different from a known customer with no accounts. The route checks existence so the first case returns 404 and the second returns 200 with []. The same rule applies to account transactions. This adds HTTP meaning without changing the original service return contract.

### Why is invalid stored output a 500 rather than a 422?

A response-model failure means the server could not fulfill its promised output contract. That is a server-side error. A request-validation failure means the client submitted input that does not satisfy the input contract and receives 422. Identifying which side violated the contract improves diagnosis.

### Why can curl finish successfully while displaying HTTP 404?

The command may have successfully exchanged an HTTP request and response even though the requested resource was absent. Its process exit code and the HTTP response status measure different things. Use `curl.exe -i` to inspect response headers and status rather than relying only on $LASTEXITCODE.

### Why do API tests not require a running Uvicorn server?

TestClient exercises the application in the test process. This makes route and response-contract testing repeatable without managing a listening server. A separate live-server smoke check verifies startup and actual HTTP access; neither kind of test replaces the other entirely.

### Does /health prove the data and AI provider are available?

No. It is a liveness endpoint confirming that the application can respond. It does not validate every JSON file or call an external provider. A readiness check would have a different purpose and must be designed explicitly.

## Interview answers to rehearse

The prerequisite and lesson answers above cover the original five interview questions: component responsibilities, GET semantics, absent versus malformed data, Pydantic documentation, and collection parent checks. Practice answering each with the TXN001 example rather than memorizing definitions.

## Learning checkpoint

- [ ] Trace request -> route -> service -> JSON -> response.
- [ ] Distinguish request validation, absence, and server failure.
- [ ] Explain REST resources and GET/POST semantics.
- [ ] Explain OpenAPI versus Swagger UI.
- [ ] Explain why HTTP status and process exit status differ.

[Return to the Phase 2 implementation guide](phase-2-guide.md)
