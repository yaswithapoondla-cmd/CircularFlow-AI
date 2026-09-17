# CircularFlow AI — Institutional Governance OS

CircularFlow AI is an institutional governance operating system that manages university circulars, policy lifecycles, compliance tracking, and automated institutional action items.

---

## Phase 16: Full AI Agent Workflow Architecture

Phase 16 upgrades **Cira** from a basic RAG chat interface into an autonomous institutional AI agent that executes dynamic intent routing, safe read-only database tool selection, semantic vector retrieval, and grounded answer synthesis.

### Core Capabilities
1. **Autonomous Tool Routing**: Routes natural language queries into specific governance tools:
   - `get_latest_circular`: Fetches the latest published circulars filtered by topic or department.
   - `get_circular_lineage`: Traces policy supersession trees (which policy replaced an old one, or what replaced the current one).
   - `get_acknowledgement_status`: Queries recipient acknowledgement compliance and pending student/faculty lists.
   - `get_pending_actions`: Inspects actionable directives, responsible roles, and deadlines.
   - `search_circulars`: Conjunction-based keyword and metadata search over PostgreSQL records.
   - `search_knowledge_base`: Semantic cosine retrieval over ChromaDB vector store.
2. **Deterministic Fallback**: Runs completely offline and deterministically without requiring an `LLM_API_KEY`. When an LLM key is supplied, grounded context is augmented for generative summarization.
3. **Guardrails & Grounded Verification**: Enforces zero hallucination. If institutional records do not contain verified data for an out-of-domain or missing query, the agent responds with clear absence notices and marks `grounded: false`.
4. **Interactive UI Activity Workflow**: Emits step-by-step activity logs and displays tool badges (`🔧 get_latest_circular`, `📜 Circular`, `⚡ Action Record`, `📄 Policy Doc`) on the frontend.

---

## Backend Agent API

### Endpoint: `POST /api/v1/agent/chat`
- **Request Body**:
  ```json
  {
    "message": "Which circular replaced the previous attendance policy?",
    "session_id": "session_default"
  }
  ```
- **Response Structure**:
  ```json
  {
    "answer": "### Lineage & Supersession Status: CIR-2026-052\n...",
    "intent": "LINEAGE_QUERY",
    "tools_used": ["get_circular_lineage"],
    "sources": [
      {
        "source_type": "circular",
        "title": "Biometric Attendance & Leave Regularization Framework 2026",
        "reference": "CIR-2026-052",
        "score": 1.0
      }
    ],
    "grounded": true,
    "activity_steps": [
      "Understanding request...",
      "Tracing circular lineage tree & supersession records...",
      "Preparing answer..."
    ]
  }
  ```

---

## Testing & Verification

### Running the Phase 16 Automated Test Suite (10/10 Scenarios)
To run the full test suite verifying Scenarios A through J against PostgreSQL and ChromaDB:
```bash
python backend/test_phase16_agent.py
```

### Running the 5 Core Demo Scenarios
```bash
python backend/verify_demo_queries.py
```

Demo Scenarios verified:
1. `"Show me the latest circular about attendance."` -> Returns `CIR-2026-052` (`get_latest_circular`).
2. `"Which circular replaced the previous attendance policy?"` -> Identifies `CIR-2026-052` superseding `CIR-2026-041` (`get_circular_lineage`).
3. `"Which students have not acknowledged the latest attendance circular?"` -> Identifies pending student Vikramaditya Rao (`get_acknowledgement_status`).
4. `"What actions are still pending?"` -> Lists 5 institutional pending actions with priorities and deadlines (`get_pending_actions`).
5. `"What does the university policy say about attendance?"` -> Retrieves Regulation 1.1 (75% mandatory minimum) from `Attendance_Policy_2026.txt` (`search_knowledge_base`).
