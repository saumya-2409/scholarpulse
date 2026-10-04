import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { usePapers } from "../context/PaperContext";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";

function Papers() {
  const navigate = useNavigate();
  const { token } = useAuth();

  const {
    papers,
    selectedIds,
    selectedPapers,
    toggleBookmark,
    toggleSelection,
    clearSelection,
  } = usePapers();

  const [search, setSearch] = useState("");
  const [yearFilter, setYearFilter] = useState("all");
  const [venueFilter, setVenueFilter] = useState("all");
  const [bookmarkedOnly, setBookmarkedOnly] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [savingPaperId, setSavingPaperId] = useState(null);
  const [saveMessage, setSaveMessage] = useState("");
  const [savedPaperMap, setSavedPaperMap] = useState({});

  useEffect(() => {
    const loadSavedPapers = async () => {
      if (!token) return;

      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/paper/saved",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || "Failed to load saved papers."
          );
        }

        const map = {};

        (data.papers || []).forEach((paper) => {
          if (paper.id && paper.saved_id) {
            map[paper.id] = paper.saved_id;
          }
        });

        setSavedPaperMap(map);
      } catch (error) {
        console.error("Failed to load saved papers:", error);
      }
    };

    loadSavedPapers();
  }, [token]);

  const years = useMemo(
    () => [...new Set(papers.map((paper) => paper.year))].sort((a, b) => b - a),
    [papers]
  );

  const venues = useMemo(
    () => [...new Set(papers.map((paper) => paper.venue))].sort(),
    [papers]
  );

  const filteredPapers = useMemo(() => {
    const query = search.trim().toLowerCase();

    return papers.filter((paper) => {
      const matchesSearch =
        !query ||
        [
          paper.title,
          paper.authors,
          paper.venue,
          paper.arxiv,
          paper.doi,
        ]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(query));

      const matchesYear =
        yearFilter === "all" || String(paper.year) === yearFilter;

      const matchesVenue =
        venueFilter === "all" || paper.venue === venueFilter;

      const matchesBookmark =
        !bookmarkedOnly || Boolean(savedPaperMap[paper.id]);

      return (
        matchesSearch &&
        matchesYear &&
        matchesVenue &&
        matchesBookmark
      );
    });
  }, [papers, search, yearFilter, venueFilter, bookmarkedOnly, savedPaperMap]);

  const clearFilters = () => {
    setSearch("");
    setYearFilter("all");
    setVenueFilter("all");
    setBookmarkedOnly(false);
  };

  const handleSavePaper = async (paper) => {
    if (!token) return;

    const savedId = savedPaperMap[paper.id];

    setSavingPaperId(paper.id);
    setSaveMessage("");

    try {
      // Already saved → remove it
      if (savedId) {
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

        setSavedPaperMap((current) => {
          const updated = { ...current };
          delete updated[paper.id];
          return updated;
        });

        toggleBookmark(paper.id);
        setSaveMessage("Paper removed from your library.");
        return;
      }

      // Not saved → save it
      const response = await fetch(
        "http://127.0.0.1:8000/api/paper/save",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            paper,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to save paper."
        );
      }

      // Reload saved papers so we get the new saved_id.
      const savedResponse = await fetch(
        "http://127.0.0.1:8000/api/paper/saved",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const savedData = await savedResponse.json();

      if (!savedResponse.ok) {
        throw new Error(
          savedData.detail || "Paper was saved, but saved state could not be refreshed."
        );
      }

      const savedPaper = (savedData.papers || []).find(
        (item) => item.id === paper.id
      );

      if (savedPaper?.saved_id) {
        setSavedPaperMap((current) => ({
          ...current,
          [paper.id]: savedPaper.saved_id,
        }));
      }

      toggleBookmark(paper.id);
      setSaveMessage("Paper saved to your library.");
    } catch (error) {
      console.error("Failed to update saved paper:", error);
      setSaveMessage(error.message);
    } finally {
      setSavingPaperId(null);
    }
  };

  const handleCompare = () => {
    if (selectedIds.length < 2 || selectedIds.length > 4) return;

    navigate(`/compare?papers=${selectedIds.join(",")}`);
  };

  const handleCite = (paper) => {
    const title = paper.title || "Untitled paper";
    const authors = Array.isArray(paper.authors)
      ? paper.authors.join(", ")
      : paper.authors || "Unknown authors";

    const year = paper.year || paper.published || "";
    const venue = paper.venue || paper.journal || "";

    const citation = `${authors}. (${year}). ${title}.${venue ? ` ${venue}.` : ""}`;

    navigator.clipboard.writeText(citation);

    setSaveMessage("Citation copied to clipboard.");
    setTimeout(() => setSaveMessage(""), 2500);
  };

  const allVisibleSelected =
    filteredPapers.length > 0 &&
    filteredPapers.every((paper) => selectedIds.includes(paper.id));

  const hasActiveFilters =
    search ||
    yearFilter !== "all" ||
    venueFilter !== "all" ||
    bookmarkedOnly;

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body-md">
      <NavBar />

      <main className="w-full">
        <div className="mx-auto w-full max-w-7xl px-6 py-10">

          {/* Page header */}
          <div className="mb-8">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="mb-3 flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                    <span className="material-symbols-outlined text-[16px]">
                      library_books
                    </span>
                  </div>

                  <span className="font-citation-tag text-citation-tag uppercase tracking-wider text-secondary font-semibold">
                    RESEARCH LIBRARY
                  </span>
                </div>

                <h1 className="font-headline-xl text-3xl font-semibold tracking-tight text-on-surface">
                  Papers
                </h1>

                <p className="mt-2 max-w-2xl text-body-md leading-6 text-on-surface-variant">
                  Review papers, save useful sources, and select studies for comparison.
                </p>
              </div>

              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-outline-variant/40 bg-surface-container-low px-3.5 py-2 text-label-sm font-medium text-on-surface-variant">
                <span className="material-symbols-outlined text-[17px]">
                  description
                </span>

                {filteredPapers.length}{" "}
                {filteredPapers.length === 1 ? "paper" : "papers"}
              </div>
            </div>
          </div>

          {/* Search + filters */}
          <div className="mb-6 rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-4 shadow-sm">
            <div className="flex flex-col gap-4">

              {/* Search */}
              <div className="flex items-center gap-3 rounded-lg border border-outline-variant/30 bg-surface-container-low px-3.5 py-3">
                <span className="material-symbols-outlined text-[20px] text-on-surface-variant">
                  search
                </span>

                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search papers, authors, topics, DOI..."
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

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-2.5">

                <select
                  value={yearFilter}
                  onChange={(event) => setYearFilter(event.target.value)}
                  className="rounded-lg border border-outline-variant/40 bg-surface-container-low px-3 py-2.5 text-body-sm text-on-surface outline-none transition focus:border-secondary focus:ring-2 focus:ring-secondary/10"
                >
                  <option value="all">All years</option>

                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>

                <select
                  value={venueFilter}
                  onChange={(event) => setVenueFilter(event.target.value)}
                  className="max-w-[220px] rounded-lg border border-outline-variant/40 bg-surface-container-low px-3 py-2.5 text-body-sm text-on-surface outline-none transition focus:border-secondary focus:ring-2 focus:ring-secondary/10"
                >
                  <option value="all">All venues</option>

                  {venues.map((venue) => (
                    <option key={venue} value={venue}>
                      {venue}
                    </option>
                  ))}
                </select>

                <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-outline-variant/40 bg-surface-container-low px-3 py-2.5 text-body-sm text-on-surface transition hover:bg-surface-container">
                  <input
                    type="checkbox"
                    checked={bookmarkedOnly}
                    onChange={(event) =>
                      setBookmarkedOnly(event.target.checked)
                    }
                    className="h-4 w-4 accent-secondary"
                  />

                  <span>Bookmarked only</span>
                </label>

                {hasActiveFilters && (
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2.5 text-label-md font-medium text-secondary transition hover:bg-secondary/5"
                  >
                    <span className="material-symbols-outlined text-[17px]">
                      filter_alt_off
                    </span>

                    Clear filters
                  </button>
                )}
              </div>
            </div>
          </div>

          {saveMessage && (
            <div className="mb-4 rounded-lg border border-outline-variant bg-surface-container-low px-4 py-3 text-body-sm text-on-surface-variant">
              {saveMessage}
            </div>
          )}

          {/* Selection toolbar */}
          {selectedIds.length > 0 && (
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-secondary/30 bg-secondary/5 px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="text-label-md font-medium text-on-surface">
                  {selectedIds.length}{" "}
                  {selectedIds.length === 1 ? "paper" : "papers"} selected
                </span>

                {selectedIds.length < 2 && (
                  <span className="text-body-sm text-on-surface-variant">
                    Select at least 2 papers to compare.
                  </span>
                )}

                {selectedIds.length > 4 && (
                  <span className="text-body-sm text-error">
                    Select up to 4 papers for comparison.
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={clearSelection}
                  className="rounded-lg px-3 py-2 text-label-md font-medium text-on-surface-variant transition hover:bg-surface-container"
                >
                  Clear selection
                </button>

                <button
                  type="button"
                  disabled={selectedIds.length < 2 || selectedIds.length > 4}
                  onClick={() =>
                    navigate(
                      `/compare?papers=${encodeURIComponent(
                        selectedIds.join(",")
                      )}`
                    )
                  }
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-label-md font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <span className="material-symbols-outlined text-[17px]">
                    compare_arrows
                  </span>

                  Compare selected
                </button>
              </div>
            </div>
          )}

          {/* Papers table */}
          <div className="overflow-hidden rounded-lg border border-outline-variant bg-surface-container-lowest">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] border-collapse">

                <thead>
                  <tr className="border-b border-outline-variant bg-surface-container-low">
                    <th className="w-12 px-4 py-3 text-left">
                     <input
  type="checkbox"
  checked={
    filteredPapers.length > 0 &&
    filteredPapers.every((paper) =>
      selectedIds.includes(paper.id)
    )
  }
  onChange={() => {
    const allSelected = filteredPapers.every((paper) =>
      selectedIds.includes(paper.id)
    );

    filteredPapers.forEach((paper) => {
      const isSelected = selectedIds.includes(paper.id);

      if (allSelected && isSelected) {
        toggleSelection(paper.id);
      } else if (!allSelected && !isSelected) {
        toggleSelection(paper.id);
      }
    });
  }}
/>
                    </th>

                    <th className="px-4 py-3 text-left text-label-sm uppercase tracking-wide text-on-surface-variant">
                      Paper
                    </th>

                    <th className="w-24 px-4 py-3 text-left text-label-sm uppercase tracking-wide text-on-surface-variant">
                      Year
                    </th>

                    <th className="w-32 px-4 py-3 text-left text-label-sm uppercase tracking-wide text-on-surface-variant">
                      Citations
                    </th>

                    <th className="w-48 px-4 py-3 text-right text-label-sm uppercase tracking-wide text-on-surface-variant">
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {filteredPapers.length === 0 ? (
                    <tr>
                      <td
                        colSpan="5"
                        className="px-6 py-16 text-center"
                      >
                        <div className="flex flex-col items-center">
                          <span className="material-symbols-outlined mb-3 text-3xl text-on-surface-variant">
                            search_off
                          </span>

                          <p className="text-label-md font-medium text-on-surface">
                            No papers found
                          </p>

                          <p className="mt-1 text-body-sm text-on-surface-variant">
                            Try changing your search or filters.
                          </p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filteredPapers.map((paper) => {
                      const isSelected = selectedIds.includes(paper.id);
                      const isExpanded = expandedId === paper.id;
                      const isSaved = Boolean(savedPaperMap[paper.id]);

                      return (
                        <>
                          <tr
                            className={`border-b border-outline-variant transition ${
                              isSelected
                                ? "bg-secondary/5"
                                : "hover:bg-surface-container-low"
                            }`}
                          >
                            {/* Select */}
                            <td className="px-4 py-4 align-top">
                              <input
                                type="checkbox"
                                checked={selectedIds.includes(paper.id)}
                                onChange={() => toggleSelection(paper.id)}
                                className="mt-1 h-4 w-4 accent-secondary"
                                aria-label={`Select ${paper.title}`}
                              />
                            </td>

                            {/* Paper information */}
                            <td className="px-4 py-4">
                              <div className="max-w-3xl">
                                <button
                                  type="button"
                                  onClick={() =>
                                    navigate(`/paper/${encodeURIComponent(String(paper.id))}`)
                                  }
                                  className="text-left font-headline-sm text-[18px] font-semibold leading-6 text-on-surface hover:text-secondary"
                                >
                                  {paper.title}
                                </button>

                                <p className="mt-1 text-body-sm text-on-surface-variant">
                                  {paper.authors}
                                </p>

                                <div className="mt-2 flex flex-wrap items-center gap-2">
                                  <span className="rounded bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                                    {paper.venue}
                                  </span>

                                  <span className="rounded bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                                    {paper.arxiv}
                                  </span>
                                </div>

                                {/* Expandable summary */}
                                <button
                                  type="button"
                                  onClick={() =>
                                    setExpandedId(
                                      isExpanded ? null : paper.id
                                    )
                                  }
                                  className="mt-3 inline-flex items-center gap-1 text-label-md font-medium text-secondary hover:underline"
                                >
                                  <span className="material-symbols-outlined text-[17px]">
                                    {isExpanded
                                      ? "expand_less"
                                      : "expand_more"}
                                  </span>

                                  {isExpanded
                                    ? "Hide summary"
                                    : "Show summary"}
                                </button>
                              </div>
                            </td>

                            {/* Year */}
                            <td className="px-4 py-4 align-top text-body-md text-on-surface">
                              {paper.year}
                            </td>

                            {/* Citations */}
                            <td className="px-4 py-4 align-top">
                              <div className="flex items-center gap-1.5 text-body-md text-on-surface">
                                <span className="material-symbols-outlined text-[18px] text-on-surface-variant">
                                  format_quote
                                </span>

                                {(paper.citations ?? 0).toLocaleString()}
                              </div>
                            </td>

                            {/* Actions */}
                            <td className="px-4 py-4 align-top">
                              <div className="flex justify-end gap-1">
                                <button
                                  type="button"
                                  onClick={() => handleSavePaper(paper)}
                                  disabled={savingPaperId === paper.id}
                                  className={`flex h-9 w-9 items-center justify-center rounded-md transition ${
                                    isSaved
                                      ? "bg-secondary/10 text-secondary"
                                      : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                                  }`}
                                  aria-label={
                                    isSaved
                                      ? "Remove bookmark"
                                      : "Bookmark paper"
                                  }
                                >
                                  <span className="material-symbols-outlined text-[20px]">
                                    {isSaved
                                      ? "bookmark"
                                      : "bookmark_border"}
                                  </span>
                                </button>

                                <button
                                  type="button"
                                  onClick={() => handleCite(paper)}
                                  className="flex h-9 items-center gap-1 rounded-md px-2 text-label-md font-medium text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                                >
                                  <span className="material-symbols-outlined text-[18px]">
                                    format_quote
                                  </span>

                                  Cite
                                </button>

                                <button
                                  type="button"
                                  onClick={() =>
                                    navigate(`/paper/${encodeURIComponent(String(paper.id))}`)
                                  }
                                  className="flex h-9 items-center gap-1 rounded-md bg-primary px-3 text-label-md font-medium text-white hover:opacity-90"
                                >
                                  <span className="material-symbols-outlined text-[18px]">
                                    chat
                                  </span>

                                  Chat
                                </button>
                              </div>
                            </td>
                          </tr>

                          {/* Expanded summary row */}
                          {isExpanded && (
                            <tr className="border-b border-outline-variant bg-surface-container-low">
                              <td></td>

                              <td colSpan="4" className="px-4 pb-5">
                                <div className="rounded-md border border-outline-variant bg-surface-container-lowest p-4">
                                  <p className="mb-3 text-label-sm font-semibold uppercase tracking-wide text-on-surface-variant">
                                    Summary
                                  </p>

                                  <div className="grid gap-4 md:grid-cols-2">
                                    {paper.summary?.map((item) => (
                                      <div key={item.title}>
                                        <h3 className="text-label-md font-semibold text-on-surface">
                                          {item.title}
                                        </h3>

                                        <p className="mt-1 text-body-sm leading-5 text-on-surface-variant">
                                          {item.text}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                          </>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Current demo-data note */}
          {papers.length === 1 && (
            <p className="mt-4 text-body-sm text-on-surface-variant">
              This workspace currently contains one demo paper. Additional
              papers can be added once the research/search pipeline is connected.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}

export default Papers;