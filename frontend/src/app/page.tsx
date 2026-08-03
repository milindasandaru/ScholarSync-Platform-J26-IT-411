export default function Home() {
  const modules = [
    {
      name: "Adaptive Academic Planner",
      status: "Module 1",
      summary: "Plan study goals, sessions, and academic milestones.",
    },
    {
      name: "Concept-Centric Learning",
      status: "Module 2",
      summary: "Track concept understanding before assessment.",
    },
    {
      name: "Competency Assessment Engine",
      status: "Module 3",
      summary: "Measure mastery and identify learning gaps.",
    },
    {
      name: "Learning Analytics & Intervention",
      status: "Module 4",
      summary: "Turn planner, concept, and assessment data into actions.",
    },
  ];

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-10 sm:py-14">
        <div className="flex flex-col gap-4">
          <p className="text-sm font-semibold uppercase tracking-wider text-emerald-700">
            ScholarSync Platform
          </p>
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <h1 className="text-4xl font-bold tracking-normal sm:text-5xl">
                Academic planning, assessment, and analytics in one workflow.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
                Frontend and backend modules are isolated so each feature team
                can build independently while keeping one API-first integration
                path.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 rounded-lg border border-slate-200 bg-white p-4 text-sm shadow-sm">
              <span className="text-slate-500">Frontend</span>
              <strong>Next.js</strong>
              <span className="text-slate-500">Backend</span>
              <strong>NestJS</strong>
              <span className="text-slate-500">Database</span>
              <strong>Supabase PostgreSQL</strong>
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {modules.map((module) => (
            <article
              key={module.name}
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
            >
              <p className="text-sm font-medium text-emerald-700">
                {module.status}
              </p>
              <h2 className="mt-2 text-xl font-semibold">{module.name}</h2>
              <p className="mt-3 leading-7 text-slate-600">{module.summary}</p>
            </article>
          ))}
        </div>

        <div className="grid gap-4 border-y border-slate-200 py-6 text-sm text-slate-600 sm:grid-cols-4">
          <span>API-first integration</span>
          <span>Module ownership</span>
          <span>Docker Compose ready</span>
          <span>CI/CD baseline</span>
        </div>
      </section>
    </main>
  );
}
