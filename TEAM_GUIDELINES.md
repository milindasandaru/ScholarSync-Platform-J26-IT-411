# ScholarSync Engineering Guidelines & Architecture Specification
**Research Group**: J26-IT-411  
**Project Title**: ScholarSync: An Integrated Adaptive Learning Framework for Competency Calibration and Academic Performance Enhancement  

---

## 1. System Overview & Component Ownership

ScholarSync operates as a modern distributed micro-service platform. Each member owns an independent, evaluated research component that communicates through standardized REST contracts.

| Member Name | Student ID | Component Branch | Sub-Objective & Domain Ownership | Key Deliverables for 50% Review |
|:---|:---|:---|:---|:---|
| **Senarath S.A.M.S** *(Leader)* | **IT23284784** | `feature/assessment` & `sams-dev` | **Competency Assessment & Calibration Engine**: Bayesian Knowledge Tracing (pyBKT), behaviour-informed supervised modeling, probability calibration (ECE), and metacognitive gap analysis. | Core ML Engine, Synthetic Benchmark Pipeline, Profile API (`/api/v1/profile/{id}`). |
| **Gimali H.K.C** | **IT22344038** | `feature/planner` | **Adaptive Academic Planner**: Dynamic task scheduling, priority scoring, deadline management, and adaptive study session recommendation based on learner profile gaps. | Task CRUD API, Priority Scoring Algorithm, Study Session Scheduler. |
| **Abeyrathna A.H.M.P.S.B** | **IT22911780** | `feature/analytics` | **Learning Analytics & Intelligent Q&A Forum**: Student/Lecturer analytics dashboards, learning trend visualization, and NLP-based duplicate question detection. | Forum Post Schema, Semantic Similarity / Duplicate Detector, Analytics Aggregator. |
| **Jayasooriya I.P** | **IT23403956** | `feature/concept` | **Concept-Centric Learning Workspace**: Prerequisite dependency graphs (DAG), NLP concept extraction, and adaptive learning path generation. | Concept Node Graph API, Prerequisite Traversal Logic, Resource Linker. |

---

## 2. Technology Stack Standards

To avoid integration friction, all members must adhere strictly to these approved technologies:

### Frontend
- **Framework**: [Next.js 14+](https://nextjs.org/) (React, App Router, TypeScript)
- **Styling**: Tailwind CSS + [Shadcn UI](https://ui.shadcn.com/) / Radix Primitives
- **Icons**: Lucide-React
- **State & Data Fetching**: TanStack Query (React Query) / Axios

### Backend Services
- **Language**: Python 3.10+ / Node.js
- **API Framework**: **FastAPI** (Python) for ML/Analytics engines; Next.js API Routes for web integration.
- **Data Validation**: Pydantic v2 (enforces strict JSON contracts across all components).
- **ORM / Database**: PostgreSQL with Prisma ORM.

---

## 3. The Core Integration Data Contract

All components interact with the **Competency Engine** using the standardized Learner Profile Contract:

### 3.1 Ingesting Student Assessment Interactions
- **Endpoint**: `POST /api/v1/assessment/event`
- **Payload Schema**:
```json
{
  "learner_id": "STU_0042",
  "subject_id": "JAVA_FUNDAMENTALS",
  "concept_id": "LOOPS_ITERATION",
  "bloom_level": "APPLY",
  "item_id": "Q_LOOP_003",
  "question_type": "CODING",
  "is_correct": true,
  "score": 1.0,
  "duration_seconds": 45.2,
  "attempt_count": 1,
  "hints_requested": 0,
  "confidence_rating": 4
}
```

### 3.2 Fetching Calibrated Learner State (Consumed by Planner, Analytics & Concept Workspace)
- **Endpoint**: `GET /api/v1/profile/{learner_id}`
- **Response Highlights**:
  - `overall_mastery_index`: Normalized index `[0.0 - 1.0]`
  - `identified_knowledge_gaps`: Concepts flagged as `FOUNDATIONAL_GAP` or `APPLICATION_GAP` (used by Planner and Concept paths to recommend remedial topics).
  - `metacognitive_alerts`: Alerts for `ILLUSION_OF_COMPETENCE` (overconfidence) or `IMPOSTER_PHENOMENON` (underconfidence) for lecturer dashboards.

---

## 4. Git Branching & Daily Workflow

1. Always branch off `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/<your-component-name>
   ```
2. Commit with standard Conventional Commits:
   - `feat(...)`: New feature or algorithm
   - `fix(...)`: Bug fix or parameter tuning
   - `docs(...)`: Documentation or report updates
   - `test(...)`: Unit test or benchmark scripts
3. Never push directly to `main` without review.
