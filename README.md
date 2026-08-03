# ScholarSync Platform

ScholarSync is organized as an API-first academic learning platform.

## Architecture

- `frontend/`: Next.js App Router, TypeScript, Tailwind CSS, Axios, React Query-ready.
- `backend/`: NestJS REST API, module-isolated feature structure, Morgan request logging, Winston application logging.
- `backend/prisma/`: Prisma schema for Supabase PostgreSQL.
- `docker/`: Docker Compose for local frontend/backend orchestration.
- `.github/workflows/`: CI checks for frontend and backend.

## Main Modules

- Adaptive Academic Planner
- Concept-Centric Learning
- Competency Assessment Engine
- Learning Analytics & Intervention

## Local Development

```bash
cd frontend
npm run dev
```

```bash
cd backend
npm run start:dev
```

Set `DATABASE_URL` for the Supabase PostgreSQL connection before running Prisma commands or database-backed API features.
