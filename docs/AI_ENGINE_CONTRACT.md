# FinSight AI ↔ Financial Engine Interface Contract

**Document Version:** 1.0.0  
**Target Audience:** Backend Engineers, AI/ML Engineers, Frontend Developers, Product & QA Teams  
**Status:** Canonical Interface Specification  

---

## 1. Architectural Principles & Boundaries

> [!IMPORTANT]
> **Core Rule:** The AI layer **never** performs financial calculations. The financial engine is **authoritative**.

FinSight maintains a strict architectural boundary between natural language processing and financial computations:

```
[ User Query (Natural Language) ]
               │
               ▼
   [ 1. AI Intent Router ]
     - Natural Language Understanding (LLM)
     - Parameter Extraction (NO calculations)
     - Secure user_id Injection (Python)
               │
               ▼  (Function Name + Raw Arguments)
  [ 2. Financial Engine (Backend) ]
     - Single Source of Truth
     - Deterministic Math & Database Queries
     - 100% Precision & Integrity
               │
               ▼  (Authoritative JSON Result)
   [ 3. Grounded AI Explainer ]
     - Translates JSON to speech-friendly voice response
     - Strictly grounded: numbers must exist in engine output
     - Post-generation validation rejects hallucinated numbers
               │
               ▼
[ Final Response (Answer Text + Structured Data) ]
```

### Key Safety Invariants:
1. **Zero LLM Math:** The LLM is prohibited from calculating balances, interest, affordability, percentages, projections, or spending totals.
2. **No Direct Database Access from AI:** The LLM does not query SQL databases, write ORM queries, or inspect raw transactions.
3. **No Synthetic Identifiers:** The router never invents `user_id`, `goal_id`, or account IDs.
4. **Authoritative Grounding:** The explainer only narrates what the financial engine returns. If a data field is missing, it explicitly states that the information is unavailable rather than guessing.

---

## 2. Supported Financial Engine Functions

The financial engine exposes **five deterministic functions** to the AI layer:

1. [`get_balance`](#function-1-get_balance)
2. [`get_spending_summary`](#function-2-get_spending_summary)
3. [`check_affordability`](#function-3-check_affordability)
4. [`project_goal_completion`](#function-4-project_goal_completion)
5. [`get_insights`](#function-5-get_insights)

---

### Function 1: `get_balance`

Fetches current account balances and total net worth for the authenticated user.

#### **Input Arguments**
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `string` | **Yes** | — | Authenticated user identifier (injected by application context). |

#### **Expected Output JSON Shape**
```json
{
  "balance": 42000.00,
  "as_of": "2026-08-27"
}
```

*Optional extended fields supported by engine:*
```json
{
  "balance": 42000.00,
  "currency": "INR",
  "as_of": "2026-08-27",
  "account_breakdown": {
    "savings": 32000.00,
    "checking": 10000.00
  }
}
```

---

### Function 2: `get_spending_summary`

Retrieves spending breakdown and totals over a specified time period and optional category filter.

#### **Input Arguments**
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `string` | **Yes** | — | Authenticated user identifier. |
| `period` | `string` | **Yes** | `"this_month"` | Enum: `["this_month", "last_month", "this_week", "last_week", "custom"]`. |
| `category` | `string` | No | `null` | Optional category filter (e.g. `"food"`, `"transport"`, `"shopping"`). |

#### **Expected Output JSON Shape**

**Overall Spending Breakdown:**
```json
{
  "total": 25000.00,
  "period": "this_month",
  "by_category": {
    "Food": 8000.00,
    "Transport": 3000.00,
    "Shopping": 6500.00,
    "Utilities": 4500.00,
    "Entertainment": 3000.00
  },
  "vs_last_period_pct": 15
}
```

**Single Category Query (e.g., Food):**
```json
{
  "total": 8000.00,
  "period": "this_month",
  "by_category": {
    "Food": 8000.00
  },
  "vs_last_period_pct": 15
}
```

---

### Function 3: `check_affordability`

Evaluates whether the user can safely afford a proposed purchase amount given current balances, fixed upcoming obligations, and buffer requirements.

#### **Input Arguments**
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `string` | **Yes** | — | Authenticated user identifier. |
| `amount` | `number` | **Yes** | — | Explicit numerical price/cost of the item or service. |
| `item_description` | `string` | No | `null` | Optional description (e.g. `"phone"`, `"laptop"`, `"concert ticket"`). |

#### **Expected Output JSON Shape**

**Affordable Purchase:**
```json
{
  "can_afford": true,
  "balance_after": 32000.00,
  "upcoming_bills": 5000.00,
  "reasoning_facts": [
    "Purchase leaves sufficient balance",
    "Remaining cushion after purchase exceeds upcoming bills"
  ]
}
```

**Non-Affordable Purchase:**
```json
{
  "can_afford": false,
  "balance_after": 42000.00,
  "upcoming_bills": 5000.00,
  "reasoning_facts": [
    "Purchase exceeds safe discretionary balance",
    "Upcoming fixed bills would be compromised"
  ]
}
```

---

### Function 4: `project_goal_completion`

Projects timeline, milestone completion dates, and the impact of hypothetical extra contributions toward a savings goal.

#### **Input Arguments**
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `string` | **Yes** | — | Authenticated user identifier. |
| `goal_id` | `string` | **Yes** | — | Valid goal ID resolved from application context. |
| `hypothetical_contribution` | `number` | No | `null` | Proposed additional recurring contribution amount. |

#### **Expected Output JSON Shape**
```json
{
  "goal_name": "Emergency Fund",
  "current_months_remaining": 6,
  "hypothetical_months_remaining": 4
}
```

*Optional extended fields supported by engine:*
```json
{
  "goal_id": "goal_efund_001",
  "goal_name": "Emergency Fund",
  "target_amount": 100000.00,
  "current_amount": 60000.00,
  "current_months_remaining": 6,
  "hypothetical_months_remaining": 4,
  "estimated_completion_date": "2027-02-28"
}
```

---

### Function 5: `get_insights`

Returns algorithmic financial insights, spending spikes, detected recurring subscriptions, and budget anomalies.

#### **Input Arguments**
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `string` | **Yes** | — | Authenticated user identifier. |

#### **Expected Output JSON Shape**
```json
[
  {
    "type": "spending_increase",
    "category": "Food",
    "percentage": 22,
    "period": "3 months"
  }
]
```

*Multiple insights list structure:*
```json
[
  {
    "type": "spending_increase",
    "category": "Food",
    "percentage": 22,
    "period": "3 months"
  },
  {
    "type": "recurring_subscription",
    "merchant": "Streaming Service",
    "amount": 649.00,
    "period": "monthly"
  }
]
```

---

## 3. End-to-End Pipeline Examples

Below are end-to-end trace walkthroughs demonstrating data flow across all 5 stages of the pipeline:

---

### Example A: Affordability Check

```
User Query: "Can I afford a phone for ₹10,000?"
```

#### **1. Router Output**
```json
{
  "status": "success",
  "function_name": "check_affordability",
  "arguments": {
    "amount": 10000,
    "item_description": "phone",
    "user_id": "usr_99812"
  }
}
```

#### **2. Engine Input**
```python
check_affordability(
    user_id="usr_99812",
    amount=10000,
    item_description="phone"
)
```

#### **3. Engine Output**
```json
{
  "can_afford": true,
  "balance_after": 32000,
  "upcoming_bills": 5000,
  "reasoning_facts": [
    "Purchase leaves sufficient balance"
  ]
}
```

#### **4. Explainer Input**
* **User Question:** `"Can I afford a phone for ₹10,000?"`
* **Engine Data:**
  ```json
  {
    "can_afford": true,
    "balance_after": 32000,
    "upcoming_bills": 5000,
    "reasoning_facts": [
      "Purchase leaves sufficient balance"
    ]
  }
  ```

#### **5. Final Pipeline Response**
```json
{
  "answer_text": "Yes, you can afford the phone for ₹10,000. Your remaining balance will be ₹32,000 with ₹5,000 reserved for upcoming bills.",
  "structured_data": {
    "can_afford": true,
    "balance_after": 32000,
    "upcoming_bills": 5000,
    "reasoning_facts": [
      "Purchase leaves sufficient balance"
    ]
  }
}
```

---

### Example B: Balance Query

```
User Query: "What's my current balance?"
```

#### **1. Router Output**
```json
{
  "status": "success",
  "function_name": "get_balance",
  "arguments": {
    "user_id": "usr_99812"
  }
}
```

#### **2. Engine Input**
```python
get_balance(user_id="usr_99812")
```

#### **3. Engine Output**
```json
{
  "balance": 42000,
  "as_of": "2026-08-27"
}
```

#### **4. Explainer Input**
* **User Question:** `"What's my current balance?"`
* **Engine Data:** `{"balance": 42000, "as_of": "2026-08-27"}`

#### **5. Final Pipeline Response**
```json
{
  "answer_text": "Your current account balance is ₹42,000 as of today.",
  "structured_data": {
    "balance": 42000,
    "as_of": "2026-08-27"
  }
}
```

---

### Example C: Spending Summary by Category

```
User Query: "How much did I spend on food this month?"
```

#### **1. Router Output**
```json
{
  "status": "success",
  "function_name": "get_spending_summary",
  "arguments": {
    "period": "this_month",
    "category": "food",
    "user_id": "usr_99812"
  }
}
```

#### **2. Engine Input**
```python
get_spending_summary(
    user_id="usr_99812",
    period="this_month",
    category="food"
)
```

#### **3. Engine Output**
```json
{
  "total": 8000,
  "period": "this_month",
  "by_category": {
    "Food": 8000
  },
  "vs_last_period_pct": 15
}
```

#### **4. Explainer Input**
* **User Question:** `"How much did I spend on food this month?"`
* **Engine Data:** `{"total": 8000, "period": "this_month", "by_category": {"Food": 8000}, "vs_last_period_pct": 15}`

#### **5. Final Pipeline Response**
```json
{
  "answer_text": "You have spent a total of ₹8,000 on Food this month, which is 15% higher compared to your last period.",
  "structured_data": {
    "total": 8000,
    "period": "this_month",
    "by_category": {
      "Food": 8000
    },
    "vs_last_period_pct": 15
  }
}
```

---

### Example D: Ambiguous Query (Clarification Flow)

```
User Query: "Can I buy this?"
```

#### **1. Router Output**
*(Router detects missing price without invoking engine)*
```json
{
  "status": "clarification_needed",
  "question": "How much does the item cost?"
}
```

#### **2. Engine Input**
*None (engine is skipped).*

#### **3. Final Pipeline Response**
```json
{
  "answer_text": "How much does the item cost?",
  "structured_data": {
    "status": "clarification_needed",
    "question": "How much does the item cost?"
  }
}
```

---

## 4. Pipeline Response Structure for Frontend & API

All consumer clients (FastAPI, React, Mobile Apps) receive a consistent response format from [`run_finSight_pipeline`](file:///c:/Users/vatsh/OneDrive/Desktop/antigrav/ai/pipeline.py):

```typescript
interface FinSightPipelineResponse {
  // Conversational natural-language answer (ready for speech TTS / screen reader)
  answer_text: string;

  // Authoritative structured JSON returned by the engine (or error/clarification metadata)
  structured_data: Record<string, any> | Array<Record<string, any>>;
}
```

### UI Integration Guidance:
* **TTS / Voice:** Speak `answer_text` directly.
* **Charts & Visuals:** Render cards, progress bars, and breakdown charts using `structured_data`.
* **State Management:** When `structured_data.status === "clarification_needed"`, keep context open for user follow-up.
