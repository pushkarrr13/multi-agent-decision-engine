# Multi-Agent Decision Engine

AI-powered multi-agent business decision support platform that analyzes business questions, gathers evidence, routes work to specialist agents, applies configurable business rules, critiques intermediate findings, and produces explainable recommendations.

## Overview

The Multi-Agent Decision Engine is designed as a generic business recommendation system rather than a single-purpose credit or risk application.

A business user can ask questions such as:

- Why did delivery delays increase this month?
- Should we increase the price of a product by 8%?
- Which supplier should we choose?
- Should we enter a new market?

The platform converts the question into a structured workflow, executes the relevant agents, evaluates business rules, and synthesizes the results into a recommendation with supporting evidence, confidence, risks, assumptions, and an auditable execution trail.

## Product Goal

The goal is to provide an explainable AI decision-support layer for business teams.

The system does not replace the business user. It provides structured analysis and recommendations that can be reviewed and acted upon by people.

## Architecture

```text
Business User
      |
      v
React DecisionOS Frontend
      |
      v
FastAPI Backend
      |
      v
BusinessQuestionService
      |
      v
DecisionOrchestrator
      |
      +--------------------+
      |                    |
      v                    v
Question Router       Evidence Agent
      |                    |
      +---------+----------+
                |
                v
       Specialist Agents
                |
                v
             Critic
                |
                v
        Business Rule Engine
                |
                v
           Synthesizer
                |
                v
         Final Recommendation
                |
                v
           PostgreSQL
        +-------+--------+
        |                |
   Agent Runs       Audit Trail
```

## Core Workflow

```text
Question
   ↓
Question Router
   ↓
Evidence Collection
   ↓
Dynamic Specialist Agents
   ↓
Critic
   ↓
Business Rules
   ↓
Synthesis
   ↓
Recommendation
   ↓
Audit Trail
```

## Key Features

### Generic Business Question Routing

The platform identifies the business area and question type from the user's request and resolves the relevant specialist agents.

Examples of business areas include:

- Operations
- Finance
- Sales
- Marketing
- Procurement
- General business analysis

### Multi-Agent Analysis

The system uses a multi-agent workflow instead of relying on a single model response.

Typical roles include:

- Question Router
- Evidence Agent
- Domain Specialist Agents
- Critic
- Synthesis Agent

This allows different parts of the analysis to be handled independently before the final recommendation is produced.

### Configurable Business Rules

Business users can create and manage rules from the UI.

A rule can define:

- Business area
- Applicable question types
- Priority
- Severity
- Conditions
- Actions
- Enabled/disabled status

Example:

```text
Rule: High Delivery Delay
Business Area: OPERATIONS
Question Type: INVESTIGATE

Condition:
delay_rate > 15

Action:
FLAG → HIGH_DELAY_RISK
```

Rules are evaluated against the supplied business context and their outcomes are included in the final decision trace.

### Explainable Recommendations

The result page provides structured output including:

- Final answer
- Recommendation
- Confidence
- Key factors
- Risks
- Assumptions
- Supporting evidence
- Business rule checks
- Agent reasoning trace

### Audit Trail

The platform records the execution lifecycle of business questions, including:

- Request creation
- Routing
- Agent execution
- Evidence processing
- Business rule evaluation
- Rule triggers
- Final synthesis
- Completion

This provides traceability for how a recommendation was generated.

### Analytics

The application includes operational analytics such as:

- Total questions
- Completed questions
- Average confidence
- Business-area distribution
- Question-type distribution
- Agent performance
- Recent activity
- Execution health

## Example

### Input

```text
Why did delivery delays increase this month?
```

Context:

```json
{
  "delay_rate": 18
}
```

Objective:

```text
Identify the main causes and determine the appropriate action.
```

### Processing

```text
OPERATIONS
    ↓
INVESTIGATE
    ↓
Evidence Agent
    ↓
Operations Specialist
    ↓
Critic
    ↓
High Delivery Delay Rule
    ↓
Synthesis
```

### Example Output

```text
Recommendation:
Investigate the operational factors contributing to the increased
 delivery delay rate before taking corrective action.

Business Rule:
High Delivery Delay → TRIGGERED

Flag:
HIGH_DELAY_RISK
```

The exact recommendation depends on the data and context provided to the system.

## Tech Stack

### Frontend

- React
- Vite
- JavaScript
- Lucide React

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic

### AI

- Google Gemini API
- `google-genai`

### Database

- PostgreSQL 16

### Infrastructure

- Docker
- Docker Compose

## Project Structure

```text
multi-agent-decision-engine/
│
├── backend/
│   ├── app/
│   │   ├── services/
│   │   ├── schemas/
│   │   ├── models_business.py
│   │   ├── models_rules.py
│   │   ├── rule_engine.py
│   │   ├── llm_service.py
│   │   ├── database.py
│   │   └── ...
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## API Overview

### Business Questions

```text
POST /api/v1/business-questions
GET  /api/v1/business-questions
GET  /api/v1/business-questions/{request_id}
```

### Rules

```text
GET    /api/v1/rules
POST   /api/v1/rules
PUT    /api/v1/rules/{rule_id}
DELETE /api/v1/rules/{rule_id}
```

### Analytics

```text
GET /api/v1/analytics
```

### Audit Trail

```text
GET /api/v1/audit-trail
GET /api/v1/audit-trail/{request_id}
```

### Health

```text
GET /health
```

## Database

The platform persists business decision activity in PostgreSQL.

Core tables include:

```text
business_question_requests
business_agent_runs
business_decision_results
business_audit_logs
business_rules
```

These tables support request tracking, agent execution history, final results, audit events, and configurable business rules.

## Running the Project

### Prerequisites

- Docker Desktop
- Git
- A Gemini API key

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

Never commit the real `.env` file.

### Start the Application

From the project root:

```powershell
docker compose up -d --build
```

### Backend

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

### Frontend

```text
http://localhost:5173
```

### Stop the Application

```powershell
docker compose down
```

## Product Screens

The DecisionOS frontend includes:

- Dashboard
- New Business Question
- Decision Result
- Decision History
- Investigation
- Analytics
- Agent Network
- Business Rules
- Audit Trail
- System/Configuration views

Add project screenshots here as the repository is finalized.

## Product / BA Perspective

This project was designed as a product-oriented AI decision-support platform, with emphasis on:

- Converting ambiguous business questions into structured analysis workflows
- Separating routing, evidence gathering, specialist analysis, critique, and synthesis
- Making business logic configurable rather than hardcoded
- Providing explainable recommendations
- Maintaining traceability through audit events
- Designing APIs, data models, workflows, and user-facing product experiences together

## Design Principles

### Generic First

The architecture is not tied to a single business domain. Credit/risk-style scenarios can be implemented as one use case, while operations, pricing, procurement, sales, and other domains can reuse the same orchestration model.

### Explainability

Recommendations are accompanied by factors, risks, assumptions, evidence, and rule outcomes.

### Human Decision Support

The platform provides recommendations and analysis to support business users rather than acting as an autonomous decision maker.

### Configurability

Business rules are managed through the product interface instead of requiring code changes for every rule update.

### Traceability

Important execution events are persisted so a recommendation can be understood in the context of its processing history.

## Security Notes

Do not commit secrets or API credentials.

The repository ignores `.env` files. Use `.env.example` as a template for local setup.

## Future Enhancements

Possible future extensions include:

- More domain-specific specialist agents
- External business data connectors
- More advanced evidence retrieval
- Recommendation comparison
- Scenario and what-if analysis
- Rule simulation/testing
- Improved observability
- Automated evaluation datasets for agent quality

## Portfolio Context

This project demonstrates a combination of:

- Business analysis
- Product thinking
- AI/LLM orchestration
- Multi-agent system design
- REST API design
- Database modeling
- Business rule modeling
- Frontend product design
- Docker-based development
- Auditability and explainability

It is intended as a portfolio project showing how a business requirement can be translated into a working AI-enabled product architecture.
