import { useSearchParams, useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";
import { usePapers } from "../context/PaperContext";

function Compare() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const { papers } = usePapers();

  const papersParam = searchParams.get("papers");

  const selectedIds = papersParam
    ? decodeURIComponent(papersParam).split(",")
    : [];

  const selectedPapers = papers.filter((paper) =>
    selectedIds.includes(String(paper.id))
  );

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body-md">
      <NavBar />

      <main className="w-full">
        <div className="mx-auto w-full max-w-7xl px-6 py-10">

          {/* Header */}
          <div className="mb-8">
            <button
              type="button"
              onClick={() => navigate("/papers")}
              className="mb-5 inline-flex items-center gap-1.5 text-label-md font-medium text-on-surface-variant transition hover:text-secondary"
            >
              <span className="material-symbols-outlined text-[18px]">
                arrow_back
              </span>
              Back to Papers
            </button>

            <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="mb-3 flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                    <span className="material-symbols-outlined text-[16px]">
                      compare_arrows
                    </span>
                  </div>

                  <span className="font-citation-tag text-citation-tag uppercase tracking-wider text-secondary font-semibold">
                    LITERATURE ANALYSIS
                  </span>
                </div>

                <h1 className="font-headline-xl text-3xl font-semibold tracking-tight text-on-surface">
                  Literature Comparison
                </h1>

                <p className="mt-2 max-w-2xl text-body-md leading-6 text-on-surface-variant">
                  Compare selected papers across their research questions,
                  methods, findings, and limitations.
                </p>
              </div>

              {selectedPapers.length >= 2 && (
                <div className="inline-flex w-fit items-center gap-2 rounded-full border border-outline-variant/40 bg-surface-container-low px-3.5 py-2 text-label-sm font-medium text-on-surface-variant">
                  <span className="material-symbols-outlined text-[17px]">
                    description
                  </span>

                  {selectedPapers.length} papers
                </div>
              )}
            </div>
          </div>

          {/* No papers selected */}
          {selectedPapers.length === 0 && (
            <EmptyState
              icon="compare_arrows"
              title="No papers selected"
              description="Select two or more papers from the Papers page to start a literature comparison."
              buttonLabel="Browse papers"
              onClick={() => navigate("/papers")}
            />
          )}

          {/* Too few papers */}
          {selectedPapers.length === 1 && (
            <EmptyState
              icon="compare_arrows"
              title="Select another paper"
              description="Literature comparison requires at least two papers."
              buttonLabel="Add papers"
              onClick={() => navigate("/papers")}
            />
          )}

          {/* Comparison workspace */}
          {selectedPapers.length >= 2 && (
            <>
              {/* Selected papers */}
              <section className="mb-8">
                <div className="mb-4 flex items-end justify-between gap-4">
                  <div>
                    <h2 className="text-headline-sm font-semibold text-on-surface">
                      Selected papers
                    </h2>

                    <p className="mt-1 text-body-sm text-on-surface-variant">
                      The studies included in this comparison.
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  {selectedPapers.map((paper) => (
                    <article
                      key={paper.id}
                      className="group rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-5 shadow-sm transition-all hover:border-secondary/30 hover:shadow-md"
                    >
                      <div className="mb-4 flex items-start justify-between gap-3">
                        <div className="flex flex-wrap gap-2">
                          {paper.year && (
                            <span className="rounded-md bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                              {paper.year}
                            </span>
                          )}

                          {paper.venue && (
                            <span className="max-w-[150px] truncate rounded-md bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                              {paper.venue}
                            </span>
                          )}
                        </div>

                        <button
                          type="button"
                          onClick={() =>
                            navigate(
                              `/paper/${encodeURIComponent(String(paper.id))}`
                            )
                          }
                          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-on-surface-variant transition hover:bg-surface-container hover:text-secondary"
                          aria-label={`Open ${paper.title}`}
                        >
                          <span className="material-symbols-outlined text-[18px]">
                            open_in_new
                          </span>
                        </button>
                      </div>

                      <h3 className="font-headline-sm text-[17px] font-semibold leading-6 text-on-surface">
                        {paper.title}
                      </h3>

                      <p className="mt-2 line-clamp-3 text-body-sm leading-5 text-on-surface-variant">
                        {Array.isArray(paper.authors)
                          ? paper.authors.join(", ")
                          : paper.authors || "Unknown authors"}
                      </p>
                    </article>
                  ))}
                </div>
              </section>

              {/* Comparison table */}
              <section className="overflow-hidden rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm">
                <div className="border-b border-outline-variant/30 bg-surface-container-low px-5 py-5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                      <span className="material-symbols-outlined text-[19px]">
                        table_chart
                      </span>
                    </div>

                    <div>
                      <h2 className="text-headline-sm font-semibold text-on-surface">
                        Comparison
                      </h2>

                      <p className="mt-1 text-body-sm text-on-surface-variant">
                        Review the available information side by side.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full min-w-[850px] border-collapse">
                    <thead>
                      <tr className="border-b border-outline-variant/30">
                        <th className="w-44 bg-surface-container-low px-5 py-4 text-left text-label-sm uppercase tracking-wide text-on-surface-variant">
                          Attribute
                        </th>

                        {selectedPapers.map((paper) => (
                          <th
                            key={paper.id}
                            className="min-w-[250px] border-l border-outline-variant/30 px-5 py-4 text-left"
                          >
                            <p className="text-label-md font-semibold leading-5 text-on-surface">
                              {paper.title}
                            </p>

                            <p className="mt-1 text-body-sm font-normal text-on-surface-variant">
                              {Array.isArray(paper.authors)
                                ? paper.authors.join(", ")
                                : paper.authors || "Unknown authors"}
                            </p>
                          </th>
                        ))}
                      </tr>
                    </thead>

                    <tbody>
                      <ComparisonRow
                        label="Year"
                        papers={selectedPapers}
                        render={(paper) => paper.year || "—"}
                      />

                      <ComparisonRow
                        label="Venue"
                        papers={selectedPapers}
                        render={(paper) => paper.venue || "—"}
                      />

                      <ComparisonRow
                        label="Citations"
                        papers={selectedPapers}
                        render={(paper) =>
                          paper.citations != null
                            ? Number(paper.citations).toLocaleString()
                            : "—"
                        }
                      />

                      <ComparisonRow
                        label="Research summary"
                        papers={selectedPapers}
                        render={(paper) => (
                          <div className="space-y-4">
                            {paper.summary?.length ? (
                              paper.summary.map((item) => (
                                <div key={item.title}>
                                  <p className="text-label-md font-semibold text-on-surface">
                                    {item.title}
                                  </p>

                                  <p className="mt-1 text-body-sm leading-5 text-on-surface-variant">
                                    {item.text}
                                  </p>
                                </div>
                              ))
                            ) : (
                              <span>—</span>
                            )}
                          </div>
                        )}
                      />

                      <ComparisonRow
                        label="Identifier"
                        papers={selectedPapers}
                        render={(paper) => (
                          <span className="font-code-sm text-[11px] text-on-surface-variant">
                            {paper.arxiv || paper.doi || "—"}
                          </span>
                        )}
                      />
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Future synthesis area */}
              <section className="mt-6 rounded-xl border border-outline-variant/30 bg-surface-container-low p-5">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                    <span className="material-symbols-outlined text-[19px]">
                      auto_awesome
                    </span>
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-label-md font-semibold text-on-surface">
                        AI synthesis
                      </h2>

                      <span className="rounded-full bg-surface-container px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-on-surface-variant">
                        Coming later
                      </span>
                    </div>

                    <p className="mt-1 max-w-3xl text-body-sm leading-5 text-on-surface-variant">
                      Cross-paper synthesis will appear here once the AI
                      research pipeline is connected. It will remain grounded
                      in the selected papers and link claims back to their
                      sources.
                    </p>
                  </div>
                </div>
              </section>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function EmptyState({ icon, title, description, buttonLabel, onClick }) {
  return (
    <div className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest px-6 py-16 text-center shadow-sm">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
        <span className="material-symbols-outlined text-2xl">
          {icon}
        </span>
      </div>

      <h2 className="mt-4 text-headline-sm font-semibold text-on-surface">
        {title}
      </h2>

      <p className="mx-auto mt-2 max-w-md text-body-sm leading-5 text-on-surface-variant">
        {description}
      </p>

      <button
        type="button"
        onClick={onClick}
        className="mt-5 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-label-md font-medium text-white transition hover:opacity-90"
      >
        {buttonLabel}

        <span className="material-symbols-outlined text-[17px]">
          arrow_forward
        </span>
      </button>
    </div>
  );
}

function ComparisonRow({ label, papers, render }) {
  return (
    <tr className="border-b border-outline-variant/30 last:border-b-0">
      <td className="bg-surface-container-low px-5 py-5 align-top text-label-md font-semibold text-on-surface">
        {label}
      </td>

      {papers.map((paper) => (
        <td
          key={paper.id}
          className="border-l border-outline-variant/30 px-5 py-5 align-top text-body-sm text-on-surface-variant"
        >
          {render(paper)}
        </td>
      ))}
    </tr>
  );
}

export default Compare;