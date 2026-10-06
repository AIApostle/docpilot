# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Individual doctors who need a lightweight way to capture and retrieve patient information across visits through natural conversation.

## Product Purpose

DocPilot lets doctors store, retrieve, and update patient information conversationally. Success means doctors can find documented patient context without leaving their workflow, while the system stays grounded in stored memories.

## Positioning

DocPilot is a doctor-facing conversational medical memory, with Walrus Memory as the persistent source of truth. It is not an EHR, hospital-management product, patient-facing application, or autonomous clinical decision-maker.

## Operating Context

Doctors use the web chat to ask about documented patient history, add visit information, and update existing memories. Telegram is another interface to the same backend and memory system. Conversation history is retrieved from backend endpoints; the frontend must not persist medical conversation content in browser storage.

## Capabilities and Constraints

- The web app provides doctor registration, login, conversational chat, patient-memory retrieval, and conversational updates.
- After authentication, the primary destination is `/new`. Sending the first message creates a conversation and navigates to `/chat/{id}`.
- Doctors can list and reopen all conversations through backend `GET /chats` and `GET /chats/{id}` endpoints.
- The PRD specifies `POST /auth/register`, `POST /auth/login`, and `POST /chat`; exact request and response fields remain dependent on the backend contract.
- Patient information must be grounded in retrieved memories. Missing information must be identified as undocumented; ambiguous patient references require clarification.
- DocPilot must not diagnose, recommend treatment, automate prescriptions, or fabricate patient facts.
- Memory namespaces are server-resolved from the authenticated doctor. The client must not choose a namespace.
- Sensitive credentials remain server-side. Use synthetic patient examples in demonstrations.

## Brand Commitments

The product is named DocPilot. The primary brand color should be green, associated with health.

## Evidence on Hand

- Product requirements: `DocPilot_Product_Requirements_Document.docx`
- No real patient data, customer proof, or approved logo asset is provided. Do not invent or imply any.

## Product Principles

- Keep the doctor in a natural conversational workflow.
- Ground patient information in persistent, retrieved memories.
- Preserve doctor-specific data isolation and keep privileged secrets off the client.
- Make uncertainty explicit and ask for clarification rather than guessing.
- Keep the product an assistant for memory and workflow, never an autonomous clinical decision-maker.
