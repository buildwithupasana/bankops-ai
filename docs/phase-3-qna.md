# Phase 3: prerequisites, professional answers, and lessons learned

These answers document the concepts requested in the phase brief and the lessons from implementing BankOps AI. They describe the current learning project, not a production banking system. Use the questions for self-assessment before reading the answers.

The prerequisite questions below cover every concept explicitly requested before Phase 3 implementation. Provider troubleshooting records observed results from this project; it is not a guarantee of current provider availability.

## Prerequisite questions and professional answers

### 1. What is an LLM?

A Large Language Model is a trained model that processes token sequences and generates likely continuations based on patterns learned during training and the supplied context. It can interpret language, classify complaints, and extract fields. It is not a transaction database and does not automatically access our JSON records. In this phase, its output reflects the user's statement rather than verified banking evidence.

### 2. What is a prompt?

A prompt is the instructions and context supplied for a model request. Our request contains an extraction task, the Operations complaint, and a response schema. Good prompting defines the scope, allowable classifications, treatment of missing information, and prohibited inferences. Prompt instructions alone are not a guarantee that the model will follow every rule.

### 3. What is a system prompt?

The system prompt contains application-controlled instructions setting the task and boundaries. Our instructions restrict the model to classification and extraction and tell it not to investigate, recommend actions, or invent facts. Keeping these instructions separate from user content makes their roles explicit. This separation does not by itself eliminate prompt-injection risks.

### 4. What is a user prompt?

The user prompt is the Operations message being processed. It may contain reported facts, ambiguities, or instructions that conflict with the application's task. We treat the complaint as input data. For example, the statement that TXN001 was debited is a claim to extract, not an independently established fact.

### 5. What are tokens?

Tokens are the units of text processed by the model: they may be words, fragments, punctuation, or other text segments. Token counts affect request size, latency, and usage charges where applicable. A 4,000-character input limit is not a 4,000-token limit; different text can tokenize differently.

### 6. What is a context window?

The context window limits how much token context a model can handle for a request, including input and generated output within the model's rules. Input can include instructions, messages, and schemas. BankOps sends one complaint per request without conversation history. A large context window does not guarantee accurate interpretation.

### 7. What is temperature?

Temperature adjusts the sampling distribution used during generation. Lower values generally reduce variation; higher values allow more varied choices. We use 0 for extraction. It does not guarantee correctness, eliminate hallucinations, or ensure identical results across all requests and provider implementations.

### 8. What is hallucination?

A hallucination is generated information that is unsupported or incorrect in the task's context. Examples include inventing an amount, guessing AED from a UAE location, or claiming a delay was caused by a compliance review. Our prompt instructs the model to use null for missing or ambiguous fields. Semantic checks and evaluation remain necessary even when the response has valid JSON structure.

### 9. What is structured output?

Structured output constrains a model response to a defined schema. BankOps supplies a Pydantic TriageResult through the SDK's parse method, which sends a JSON schema and parses the returned data. This is stronger than asking for JSON in prose and then searching the response for braces. Schema validation checks shape and allowed values; it cannot establish that the model extracted the correct facts. Refusals and incomplete responses also require explicit handling.

## Lessons learned: architecture Q&A

### Why use a dedicated AI service?

The AI service owns provider configuration, prompting, request parameters, parsing, and provider-error translation. The route validates HTTP input and returns HTTP results. This separation makes provider changes and mocked tests possible without embedding SDK logic in API routes.

### How do OpenRouter, the OpenAI SDK, and the model differ?

OpenRouter is the gateway receiving our request and routing it to a model provider. The OpenAI Python SDK is the client library used because OpenRouter exposes a compatible interface. The selected model performs the language task. Using this SDK does not mean the request is sent directly to OpenAI: our configured base URL points to OpenRouter.

### Why did the model change during Phase 3?

The project first integrated OpenAI, then switched to OpenRouter at the user's request. A live check of the selected Qwen free endpoint returned an explicit upstream provider rate-limit message. The user subsequently selected Nex-N2.5-Mini. Offline tests verified the request configuration for the replacement, but those tests did not establish its live availability or extraction quality.

### Why use null for missing details?

Null explicitly represents unknown information. Filling an absent amount with zero or guessing a currency would turn missing evidence into a false claim. All four result keys are present, but transaction_id, amount, and currency may be null. Our narrow issue categories are payment_not_received, other, and unclear.

### Why can the AI extract TXN999 when no such record exists?

Extraction identifies text in the complaint. Lookup checks a data source. Phase 3 implements extraction only, so it should preserve an explicitly reported ID even when it is absent from the synthetic dataset. This distinction prevents an extraction result from being mistaken for an investigation.

### Why does AI output use amount 2500 while banking data uses 250000?

The extraction contract uses whole currency units to match the user's statement. The banking dataset uses integer minor units for precise storage. No financial calculation occurs in the AI service. Any future connection between the two must validate currency, precision, and conversion explicitly rather than mixing the values directly.

## Lessons learned: troubleshooting Q&A

### Why did editing .env.example not configure the application?

.env.example is a shareable template. The service reads .env and process environment variables. A real key belongs only in the ignored local .env file or a suitable secret-management mechanism. Existing process variables take precedence because dotenv is loaded with override=False.

### Why can a restart or clearing a terminal variable matter?

A running process can retain an earlier environment value. Editing .env does not replace a nonempty process variable under the current loading policy. Stop the server, clear the specific terminal override when appropriate, and restart. Do not print the key to diagnose the problem.

### What did the initial generic 503 hide?

The initial handler grouped rejected credentials and rate limits together. Splitting upstream 401 from 429 made diagnosis more precise. The public API still returns 503 because the AI dependency is unavailable; the safe detail identifies the upstream status. A local HTTP status and a provider HTTP status describe different boundaries.

### What did we learn from the repeated 429 responses?

A 429 can originate from platform request limits or provider capacity. In the observed diagnostic check, the key-status endpoint accepted the key and reported 0 daily requests used with 50 remaining. A separate synthetic generation request then identified the Qwen provider's temporary upstream rate limit. That evidence identified the incident's cause; the same diagnosis should not be assumed for every future 429.

### Why did zero dashboard activity not resolve the diagnosis?

The screenshot showed a filtered view, not complete evidence of every attempted request. The filter might refer to a different key, and a rejected request might not appear as completed usage. We did not establish the dashboard's precise counting behavior. Direct response evidence was more useful than inferring success or failure from a blank usage summary.

### Why did a $100 key limit not prove that requests should work?

A key spending cap, account credit balance, daily request allowance, and provider capacity are different constraints. Raising a spending cap does not necessarily change a free endpoint's request limits or available capacity. Diagnosis should identify the failing constraint before changing account settings.

### How can errors be useful without exposing secrets?

Use controlled error messages, documented metadata, and narrowly validated headers such as numeric retry delays. Do not echo arbitrary raw provider bodies, request headers, or exception strings to callers. Our tests exercise error responses with secret-like placeholders to check that those values are not returned or logged by the tested paths.

### What should happen if a key is exposed?

Revoke the exposed key, issue a replacement, update local configuration, and restart the application. Removing a key from a later message or file does not undo exposure. Git ignore rules prevent ordinary tracking of .env, but do not protect keys copied into screenshots, chat, another tracked file, or existing history.

### What do mocked tests prove, and what requires a live call?

Mocks verify input validation, request parameters, SDK schema handling, error mapping, and API behavior without invoking the provider. A real-SDK test with a mocked HTTP transport also verifies serialization and parsing. Live tests are needed to check actual credentials, provider availability, schema acceptance, and model extraction behavior. One successful live example is still not a comprehensive accuracy evaluation.

### Why disable reasoning and avoid a second conversational call?

Our task is a small, independent extraction request. A two-turn conversation with preserved reasoning details adds state and complexity without being required by the phase objective. The implementation requests disabled reasoning and retains the four-field schema. This is an implementation choice for this milestone, not a claim that reasoning is never useful.

## Learning checkpoint

- [ ] Explain LLM, prompt roles, tokens, context window, temperature, and hallucination.
- [ ] Explain schema validity versus factual accuracy.
- [ ] Trace Operations user -> FastAPI -> AI service -> OpenRouter -> model -> structured response.
- [ ] Distinguish configuration, authentication, quota, and provider-capacity failures.
- [ ] Explain mocked tests versus live checks and handle secrets without displaying them.

[Return to the Phase 3 implementation guide](phase-3-guide.md)

References used in the implementation: [OpenRouter SDK integration](https://openrouter.ai/docs/guides/community/openai-sdk), [structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs), and [limits](https://openrouter.ai/docs/api/reference/limits). Model availability and limit policies should be rechecked when diagnosing a new incident.
