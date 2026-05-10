import AppNavbar from '../components/AppNavbar'
import { syllabusModules, totalMarks } from '../data/syllabus'

function SyllabusPage() {
  return (
    <main className="min-h-screen bg-brand-bg">
      <AppNavbar />
      <section className="mx-auto max-w-7xl px-4 py-6 md:px-6">
        <div className="rounded-2xl border border-brand-line bg-brand-surface p-6">
          <h1 className="text-3xl font-bold">C Programming Syllabus</h1>
          <p className="mt-2 text-brand-muted">
            Phase-wise breakdown aligned with your <strong className="text-brand-text font-medium">C Foundation — Updated</strong>{' '}
            handbook — same structure as the lecture plan (Foundation → flow control → functions → arrays and
            strings → problem practice).
          </p>
          <div className="mt-4 inline-flex rounded-lg border border-brand-neonBlue/40 bg-brand-neonBlue/10 px-4 py-2 text-sm text-brand-neonBlue">
            Total Weightage: {totalMarks} marks
          </div>
        </div>

        <div className="mt-6 grid gap-4">
          {syllabusModules.map((module) => (
            <article
              key={module.id}
              className="rounded-2xl border border-brand-line bg-brand-surface p-5 transition hover:border-brand-neonBlue/60"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-semibold">
                  {module.id}. {module.title}
                </h2>
                <span className="rounded-full bg-brand-neonGreen/15 px-3 py-1 text-sm text-brand-neonGreen">
                  {module.marks} marks
                </span>
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-brand-line bg-brand-card p-4">
                  <p className="text-sm font-semibold text-brand-neonBlue">Topics Covered</p>
                  <ul className="mt-2 space-y-1 text-sm text-brand-muted">
                    {module.topics.map((topic) => (
                      <li key={topic}>- {topic}</li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-lg border border-brand-line bg-brand-card p-4">
                  <p className="text-sm font-semibold text-brand-neonGreen">Example Questions</p>
                  <ul className="mt-2 space-y-1 text-sm text-brand-muted">
                    {module.examples.map((example) => (
                      <li key={example}>- {example}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}

export default SyllabusPage
