import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";
import { useAuth } from "../context/AuthContext";

function Library() {
  const navigate = useNavigate();

  const { token } = useAuth();

  const [search, setSearch] = useState("");
  const [savedPapers, setSavedPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadSavedPapers = async () => {
      if (!token) return;

      setLoading(true);
      setError("");

      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/paper/saved",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "Failed to load saved papers."
          );
        }

        const data = await response.json();

        setSavedPapers(data.papers || []);
      } catch (error) {
        console.error("Failed to load saved papers:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    loadSavedPapers();
  }, [token]);

  const filteredPapers = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return savedPapers;

    return savedPapers.filter((paper) => {
      return [
        paper.title,
        paper.authors,
        paper.venue,
        paper.arxiv,
        paper.doi,
      ]
        .filter(Boolean)
        .some((value) =>
          String(value).toLowerCase().includes(query)
        );
    });
  }, [savedPapers, search]);

  const handleRemovePaper = async (savedId) => {
    if (!token || !savedId) return;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/paper/saved/${savedId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to remove paper."
        );
      }

      setSavedPapers((current) =>
        current.filter(
          (paper) => paper.saved_id !== savedId
        )
      );
    } catch (error) {
      console.error("Failed to remove paper:", error);
      setError(error.message);
    }
  };

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body-md">
      <NavBar />

      <main className="w-full">
        <div className="mx-auto w-full max-w-7xl px-6 py-10">

          {/* Header */}
          <div className="mb-8">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="mb-3 flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                    <span className="material-symbols-outlined text-[16px]">
                      bookmark
                    </span>
                  </div>

                  <span className="font-citation-tag text-citation-tag uppercase tracking-wider text-secondary font-semibold">
                    SAVED RESEARCH
                  </span>
                </div>

                <h1 className="font-headline-xl text-3xl font-semibold tracking-tight text-on-surface">
                  Library
                </h1>

                <p className="mt-2 max-w-2xl text-body-md leading-6 text-on-surface-variant">
                  Papers you've saved for later research and reference.
                </p>
              </div>

              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-outline-variant/40 bg-surface-container-low px-3.5 py-2 text-label-sm font-medium text-on-surface-variant">
                <span className="material-symbols-outlined text-[17px]">
                  bookmarks
                </span>

                {filteredPapers.length}{" "}
                {filteredPapers.length === 1 ? "paper" : "papers"}
              </div>
            </div>
          </div>

          {/* Search */}
          <div className="mb-6 rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-4 shadow-sm">
            <div className="flex items-center gap-3 rounded-lg border border-outline-variant/30 bg-surface-container-low px-3.5 py-3">
              <span className="material-symbols-outlined text-[20px] text-on-surface-variant">
                search
              </span>

              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search your saved papers..."
                className="w-full bg-transparent text-body-md text-on-surface outline-none placeholder:text-on-surface-variant"
              />

              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition hover:bg-surface-container-high hover:text-on-surface"
                  aria-label="Clear search"
                >
                  <span className="material-symbols-outlined text-[18px]">
                    close
                  </span>
                </button>
              )}
            </div>
          </div>

          {loading && (
  <div className="rounded-lg border border-outline-variant bg-surface-container-lowest px-6 py-16 text-center">
    <span className="material-symbols-outlined mb-3 animate-spin text-4xl text-secondary">
      progress_activity
    </span>

    <h2 className="text-headline-sm font-semibold text-on-surface">
      Loading your library...
    </h2>
  </div>
)}

          {error && !loading && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center">
              <span className="material-symbols-outlined mb-3 text-3xl text-red-500">
                error
              </span>

              <h2 className="text-headline-sm font-semibold text-red-700">
                Could not load your library
              </h2>

              <p className="mt-2 text-body-sm text-red-600">
                {error}
              </p>
            </div>
          )}

          {/* Empty state */}
          {!loading && !error && filteredPapers.length === 0 && (
            <div className="rounded-lg border border-outline-variant bg-surface-container-lowest px-6 py-16 text-center">
              <span className="material-symbols-outlined mb-3 text-4xl text-on-surface-variant">
                {search ? "search_off" : "bookmark_border"}
              </span>

              <h2 className="text-headline-sm font-semibold text-on-surface">
                {search
                  ? "No saved papers found"
                  : "Your library is empty"}
              </h2>

              <p className="mx-auto mt-2 max-w-md text-body-sm leading-5 text-on-surface-variant">
                {search
                  ? "Try a different search term."
                  : "Save papers from the Papers page and they will appear here."}
              </p>

              {!search && (
                <button
                  type="button"
                  onClick={() => navigate("/papers")}
                  className="mt-5 rounded-md bg-primary px-4 py-2 text-label-md font-medium text-white hover:opacity-90"
                >
                  Browse papers
                </button>
              )}
            </div>
          )}

          {/* Saved papers */}
          {!loading && !error && filteredPapers.length > 0 && (
            <section className="overflow-hidden rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm">
              <div className="border-b border-outline-variant/30 bg-surface-container-low px-5 py-4">
                <h2 className="text-headline-sm font-semibold text-on-surface">
                  Saved papers
                </h2>
              </div>

              <div className="divide-y divide-outline-variant">
                {filteredPapers.map((paper) => (
                  <article
                    key={paper.id}
                    className="flex flex-col gap-5 px-5 py-6 transition hover:bg-surface-container-low md:flex-row md:items-start md:justify-between"
                  >
                    {/* Paper info */}
                    <div className="min-w-0 flex-1">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <span className="rounded bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                          {paper.venue}
                        </span>

                        <span className="rounded bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                          {paper.year}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/paper/${encodeURIComponent(String(paper.id))}`
                          )
                        }
                        className="text-left font-headline-sm text-[19px] font-semibold leading-6 text-on-surface hover:text-secondary"
                      >
                        {paper.title}
                      </button>

                      <p className="mt-2 text-body-sm text-on-surface-variant">
                        {paper.authors}
                      </p>

                      <div className="mt-3 flex flex-wrap items-center gap-4 text-body-sm text-on-surface-variant">
                        <span className="flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[17px]">
                            format_quote
                          </span>

                          {paper.citations?.toLocaleString()} citations
                        </span>

                        {paper.arxiv && (
                          <span className="font-code-sm text-[11px]">
                            {paper.arxiv}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex shrink-0 items-center gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/paper/${encodeURIComponent(String(paper.id))}`
                          )
                        }
                        className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-label-md font-medium text-white hover:opacity-90"
                      >
                        <span className="material-symbols-outlined text-[18px]">
                          chat
                        </span>

                        Open
                      </button>

                      <button
                        type="button"
                        onClick={() => handleRemovePaper(paper.saved_id)}
                        className="flex items-center gap-1.5 rounded-md border border-outline-variant px-3 py-2 text-label-md font-medium text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                      >
                        <span className="material-symbols-outlined text-[18px]">
                          bookmark_remove
                        </span>

                        Remove
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          {/* Browse link */}
          {!loading && !error && filteredPapers.length > 0 && (
            <div className="mt-6">
              <button
                type="button"
                onClick={() => navigate("/papers")}
                className="inline-flex items-center gap-1.5 text-label-md font-medium text-secondary hover:underline"
              >
                Browse more papers
                <span className="material-symbols-outlined text-[17px]">
                  arrow_forward
                </span>
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Library;