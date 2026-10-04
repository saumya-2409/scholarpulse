import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";
import { usePapers } from "../context/PaperContext";

function Research() {
  const navigate = useNavigate();
  const { token } = useAuth();

  const {
    researchResults,
    setResearchResults,
    setResearchPapers,
  } = usePapers();

  const [query, setQuery] = useState("");
  const [isResearching, setIsResearching] = useState(false);
  const [error, setError] = useState("");
  const [recentResearch, setRecentResearch] = useState([]);
  

  const suggestions = [
    "How does retrieval-augmented generation improve factuality in LLMs?",
    "What are recent methods for mechanistic interpretability?",
    "How are multimodal language models evaluated?",
    "What are the main limitations of current RAG systems?",
  ];

  useEffect(() => {
    const restoreResearch = async () => {
      if (!token) return;
      const lastQuery = localStorage.getItem(
        "scholarpulse_last_research_query"
      );

      if (!lastQuery) return;

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/research/cache?query=${encodeURIComponent(
            lastQuery
          )}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          return;
        }
        const data = await response.json();
        setResearchResults(data);
        setResearchPapers(data.papers || []);
        setQuery(lastQuery);
      } catch (error) {
        console.error("Failed to restore cached research:", error);
      }
    };

    restoreResearch();
  }, [token]);

  const loadRecentResearch = async () => {
    if (!token) return;

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/research/recent",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load recent research.");
      }

      const data = await response.json();

      setRecentResearch(data.searches || []);
    } catch (error) {
      console.error("Failed to load recent research:", error);
    }
  };

  useEffect(() => {
    loadRecentResearch();
  }, [token]);

  const handleSuggestion = (text) => {
    setQuery(text);
  };

  const clearQuery = () => {
    setQuery("");
  };

  const handleViewCachedResearch = async (researchQuery) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/research/cache?query=${encodeURIComponent(
          researchQuery
        )}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Cached research results are no longer available.");
      }

      const data = await response.json();

      setResearchResults(data);
      setResearchPapers(data.papers || []);
      setQuery(researchQuery);
    } catch (error) {
      console.error("Failed to load cached research:", error);
      setError(error.message);
    }
  };

  const handleResearch = async (researchQuery = query) => {
    if (!researchQuery.trim() || isResearching) return;

    setIsResearching(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/research", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
        query: researchQuery.trim(),
        papers_per_source: 3,
      }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Research request failed.");
      }

      const data = await response.json();
      localStorage.setItem(
        "scholarpulse_last_research_query",
        researchQuery.trim()
      );

      setResearchResults(data);
      setResearchPapers(data.papers);
      await loadRecentResearch();

    } catch (error) {
      console.error("Research error:", error);
      setError(error.message);
    } finally {
      setIsResearching(false);
    }
  };

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface antialiased min-h-screen flex flex-col">
      <NavBar />
    
      <main className="w-full pt-16 bg-surface flex-1">
        <div className="flex flex-col w-full">
          {/* Interactive Canvas Wrapper */}
          <div className="w-full max-w-7xl mx-auto flex flex-col px-6 sm:px-8 py-5 gap-6">
            {/* Top Heroic Synthesis Workspace */}
            <div className="relative w-full rounded-2xl bg-surface-container-lowest shadow-sm overflow-hidden p-5">
              {/* Ambient subtle background element */}
              <div className="absolute -top-32 -right-32 w-96 h-96 bg-gradient-to-br from-secondary/5 via-tertiary-fixed/10 to-transparent rounded-full blur-3xl pointer-events-none" />
              <div className="relative z-10 flex flex-col gap-4">
                {/* Academic Command Interface Title */}
                <div className="max-w-4xl flex flex-col gap-2.5">
                  <div className="flex items-center gap-2">
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-secondary-fixed/40 border border-secondary/20">
                      <span className="relative flex h-1.5 w-1.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75" />
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-secondary" />
                      </span>
                      <span className="font-citation-tag text-citation-tag text-secondary uppercase tracking-wider font-semibold">
                        RESEARCH WORKSPACE
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <h2 className="font-headline-lg text-headline-lg sm:text-[24px] text-on-surface tracking-tight font-semibold">
                      Turn a research question into
                      <span className="italic font-normal text-secondary">
                        {" "}evidence you can explore
                      </span>
                    </h2>
                    
                  </div>
                </div>
                {/* Search & Synthesis Input Container */}
                <div className="relative flex flex-col gap-3 bg-surface-container-lowest p-4 sm:p-5 rounded-2xl border border-secondary/25 shadow-[0_8px_30px_rgb(0,81,213,0.08)] transition-all">
                  <div className="absolute -top-24 right-1/4 w-72 h-32 bg-secondary/5 rounded-full blur-2xl pointer-events-none" />
                  <div className="relative w-full rounded-xl bg-surface-container-lowest border border-outline-variant/30 focus-within:border-secondary/60 focus-within:shadow-md transition-all p-3 shadow-sm">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <div className="w-9 h-9 rounded-xl bg-secondary/10 border border-secondary/20 flex items-center justify-center text-secondary shrink-0 shadow-sm">
                        <span className="material-symbols-outlined text-[22px]">
                          manage_search
                        </span>
                      </div>
                      <div className="flex-1 flex flex-col">
                        <textarea
                          className="w-full bg-transparent text-on-surface placeholder:text-on-surface-variant/60 font-body-md text-body-md sm:text-[15px] outline-none resize-none pt-0.5 pb-1 leading-relaxed min-h-[56px] sm:min-h-[64px]"
                          id="search-query-input"
                          placeholder='Ask a research question or search papers, e.g. "What are the latest mechanistic interpretability techniques for attention heads?"'
                          rows={2}
                          value={query}
                          onChange={(event) => setQuery(event.target.value)}
                          onKeyDown={(event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleResearch();
  }
}}
                        />
                        <div className="flex items-center justify-between pt-1.5 border-t border-outline-variant/20 mt-0.5 flex-wrap gap-2">
                          <span className="font-citation-tag text-citation-tag text-on-surface-variant/70">
                            Supports cross-engine arXiv, PubMed, DOI &amp; natural
                            language prompts
                          </span>
                          <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1 bg-surface-container px-2 py-0.5 rounded-md text-on-surface-variant border border-outline-variant/20">
                              <span className="material-symbols-outlined text-[13px]">
                                keyboard_command_key
                              </span>
                             <span className="font-citation-tag text-citation-tag font-semibold tracking-wider">
                              Enter
                            </span>
                            </div>
                        
                            <button
                              className="flex items-center gap-2 px-4 py-1.5 bg-secondary hover:bg-secondary/90 text-on-secondary rounded-lg font-label-md text-label-md font-semibold transition-all shadow-[0_4px_16px_rgb(0,81,213,0.35)] hover:shadow-[0_6px_22px_rgb(0,81,213,0.45)] active:scale-95 group disabled:cursor-not-allowed disabled:opacity-60"
                              type="button"
                              disabled={isResearching || !query.trim()}
                              onClick={handleResearch}
                            >
                              <span
                                className={`material-symbols-outlined text-[18px] text-tertiary-fixed transition-transform ${
                                  isResearching ? "animate-spin" : "group-hover:rotate-12"
                                }`}
                              >
                                {isResearching ? "progress_activity" : "auto_awesome"}
                              </span>

                              <span className="tracking-wide">
                                {isResearching ? "Researching..." : "Start research"}
                              </span>
                            </button>
                            {error && (
  <div className="mt-4 flex items-start gap-3 rounded-xl border border-error/20 bg-error/5 px-4 py-4 text-error">
    <span className="material-symbols-outlined mt-0.5 text-[20px]">
      error
    </span>

    <div className="min-w-0 flex-1">
      <p className="text-sm font-semibold">
        Research request failed
      </p>

      <p className="mt-1 text-sm leading-5 text-error/80">
        {error}
      </p>

      <button
        type="button"
        onClick={() => setError("")}
        className="mt-2 text-xs font-semibold underline underline-offset-2 hover:no-underline"
      >
        Dismiss
      </button>
    </div>
  </div>
)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                    <div className="flex items-center gap-1.5 text-on-surface-variant shrink-0">
                      <span className="material-symbols-outlined text-secondary text-[16px]">
                        explore
                      </span>
                      <span className="font-label-sm text-label-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                        Suggestions:
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {suggestions.map((suggestion, index) => (
                        <button
                          key={suggestion}
                          className="inline-flex items-center gap-1.5 text-left font-code-sm text-code-sm text-on-surface bg-surface-container-low hover:bg-surface-container-high hover:border-secondary/30 border border-outline-variant/30 px-2.5 py-1 rounded-lg transition-all shadow-sm group"
                          onClick={() => handleSuggestion(suggestion)}
                          type="button"
                        >
                          <span className="material-symbols-outlined text-secondary/70 group-hover:text-secondary text-[14px]">
                            {["auto_awesome", "psychology", "hub", "science"][index]}
                          </span>

                          <span className="font-medium">
                            {suggestion}
                          </span>
                        </button>
                      ))}
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end lg:self-auto">
                      <button
                        className="flex items-center gap-1.5 px-3 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface rounded-xl font-label-md text-label-md font-medium transition-all shadow-sm border border-outline-variant/30"
                        onClick={clearQuery}
                        type="button"
                      >
                        <span className="material-symbols-outlined text-[16px]">
                          clear_all
                        </span>
                        <span>Clear</span>
                      </button>
                    </div>
                  </div>           
                </div>                
              </div>
            </div>
            {/* How ScholarPulse Works (Scientific Workflow Pipeline) */}
            <div className="flex flex-col gap-3.5">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-1">
                <div>
                  <div className="font-citation-tag text-citation-tag uppercase tracking-wider text-secondary font-semibold">
                    HOW IT WORKS
                  </div>
                  <h3 className="font-headline-lg text-headline-lg font-semibold text-on-surface">
                     From research question to evidence
                  </h3>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Step 1 */}
                <div className="relative bg-surface-container-lowest p-5 rounded-2xl shadow-sm flex flex-col justify-between gap-4 group hover:shadow-md transition-all border border-outline-variant/20">
                  <div className="flex items-center justify-between">
                    <span className="font-code-sm text-code-sm font-semibold bg-surface-container-high text-on-surface px-space-xs py-space-2xs rounded">
                      01
                    </span>
                    <span className="material-symbols-outlined text-secondary text-[22px]">
                      search
                    </span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                      Discover
                    </h4>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Search for papers and evidence related to your research question.
                    </p>
                  </div>
                  
                </div>

                {/* Step 2 */}
                <div className="relative bg-surface-container-lowest p-5 rounded-2xl shadow-sm flex flex-col justify-between gap-4 group hover:shadow-md transition-all border border-outline-variant/20">
                  <div className="flex items-center justify-between">
                    <span className="font-code-sm text-code-sm font-semibold bg-surface-container-high text-on-surface px-space-xs py-space-2xs rounded">
                      02
                    </span>
                    <span className="material-symbols-outlined text-secondary text-[22px]">
                       compare_arrows
                    </span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                    Analyze
                    </h4>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Inspect papers, compare findings, and examine the evidence behind them.
                    </p>
                  </div>
                  
                </div>

                {/* Step 3 */}
                <div className="relative bg-surface-container-lowest p-5 rounded-2xl shadow-sm flex flex-col justify-between gap-4 group hover:shadow-md transition-all border border-outline-variant/20">
                  <div className="flex items-center justify-between">
                    <span className="font-code-sm text-code-sm font-semibold bg-surface-container-high text-on-surface px-space-xs py-space-2xs rounded">
                      03
                    </span>
                    <span className="material-symbols-outlined text-secondary text-[22px]">
                      auto_awesome
                    </span>
                  </div>
                  <div className="flex flex-col gap-1">
                    <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                      Synthesize
                    </h4>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                     Build a grounded synthesis from the papers you select.
                    </p>
                  </div>
                  
                </div>

              </div>
            </div>

            {/* Core Platform Capabilities Grid */}
            <div className="flex flex-col gap-3.5">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-1">
                <div>
                  <div className="font-citation-tag text-citation-tag uppercase tracking-wider text-secondary font-semibold">
                    CAPABILITIES
                  </div>
                  <h3 className="font-headline-lg text-headline-lg font-semibold text-on-surface">
                    Core Analytical Suite
                  </h3>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Feature 1 */}
                <div className="bg-surface-container-lowest p-5 rounded-2xl shadow-sm flex flex-col justify-between gap-4 hover:shadow-md transition-all border border-outline-variant/20 min-h-[200px]">
                  <div className="flex flex-col gap-2">
                    <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-on-surface">
                      <span className="material-symbols-outlined text-[20px]">
                        auto_stories
                      </span>
                    </div>
                    <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                      Paper Discovery
                    </h4>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Find and explore research papers relevant to your question.
                    </p>
                  </div>
                </div>
                {/* Feature 2 */}
                <div className="bg-surface-container-lowest p-5 rounded-2xl shadow-sm flex flex-col justify-between gap-4 hover:shadow-md transition-all border border-outline-variant/20 min-h-[200px]">
                  <div className="flex flex-col gap-2">
                    <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-on-surface">
                      <span className="material-symbols-outlined text-[20px]">
                        bubble_chart
                      </span>
                    </div>
                    <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                      Paper Comparison
                    </h4>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Compare selected papers across methods, findings, and limitations.
                    </p>
                  </div>
                </div>
                {/* Feature 3 */}
                <div className="bg-surface-container-lowest p-5 rounded-2xl shadow-sm flex flex-col justify-between gap-4 hover:shadow-md transition-all border border-outline-variant/20 min-h-[200px]">
                  <div className="flex flex-col gap-2">
                    <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-on-surface">
                      <span className="material-symbols-outlined text-[20px]">
                        format_quote
                      </span>
                    </div>
                    <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                      Grounded Copilot
                    </h4>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Ask questions about papers and trace answers back to their sources.
                    </p>
                  </div>
                </div>
                {/* Feature 4 */}
                <div className="bg-surface-container-lowest p-5 rounded-2xl shadow-sm flex flex-col justify-between gap-4 hover:shadow-md transition-all border border-outline-variant/20 min-h-[200px]">
                  <div className="flex flex-col gap-2">
                    <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-on-surface">
                      <span className="material-symbols-outlined text-[20px]">
                        psychology
                      </span>
                    </div>
                    <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                      Citation Tools
                    </h4>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Save papers and generate common citation formats.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Queries & Research Sessions */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary">
                    <span className="material-symbols-outlined text-[16px]">
                      history
                    </span>
                  </div>

                  <h3 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                    Recent Research
                  </h3>

                  <span className="inline-flex items-center px-2 py-0.5 rounded-full font-citation-tag text-citation-tag bg-surface-container-high text-on-surface-variant font-medium border border-outline-variant/30">
                    {recentResearch.length} sessions
                  </span>
                </div>
              </div>

              {recentResearch.length === 0 ? (
                <div className="bg-surface-container-lowest border border-outline-variant/30 rounded-xl p-8 shadow-sm text-center">
                  <span className="material-symbols-outlined text-3xl text-on-surface-variant/50">
                    manage_search
                  </span>

                  <h4 className="mt-3 font-headline-sm text-headline-sm font-semibold text-on-surface">
                    No research sessions yet
                  </h4>

                  <p className="mt-1 font-body-md text-body-md text-on-surface-variant">
                    Start with a research question above to begin building your research history.
                  </p>
                </div>
              ) : (
                <div className="bg-surface-container-lowest border border-outline-variant/30 rounded-xl overflow-hidden shadow-sm divide-y divide-outline-variant/20">
                  {recentResearch.map((session) => (
                    <div
                      key={`${session.query}-${session.created_at}`}
                      className="hover:bg-surface-container-low/50 transition-colors p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="flex items-start gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-lg bg-secondary-fixed/40 text-secondary flex items-center justify-center shrink-0 mt-0.5">
                          <span className="material-symbols-outlined text-[16px]">
                            history
                          </span>
                        </div>

                        <div className="flex flex-col min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-headline-sm text-[14px] font-semibold text-on-surface truncate">
                              {session.query}
                            </span>

                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full font-citation-tag text-citation-tag font-medium bg-emerald-500/10 text-on-tertiary-container border border-on-tertiary-container/20">
                              <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container" />
                              Research
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-2 mt-0.5 font-code-sm text-code-sm text-on-surface-variant">
                            <span>
                              {new Date(session.created_at).toLocaleString()}
                            </span>

                            <span>•</span>

                            <span>
                              {session.paper_count} papers
                            </span>

                            <span>•</span>

                            <span>
                              {session.cluster_count} clusters
                            </span>

                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                        
                        <button
                          className="px-2.5 py-1 bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/30 rounded-lg font-label-md text-xs font-medium flex items-center gap-1.5 transition-colors"
                          onClick={() => {
                            handleViewCachedResearch(session.query);
                          }}
                          type="button"
                        >
                          <span className="material-symbols-outlined text-[14px]">
                            visibility
                          </span>
                          <span>View</span>
                        </button>

                        <button
                          className="px-2.5 py-1 bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/30 rounded-lg font-label-md text-xs font-medium flex items-center gap-1.5 transition-colors"
                          onClick={() => {
                            setQuery(session.query);
                            handleResearch(session.query);
                          }}
                          type="button"
                        >
                          <span className="material-symbols-outlined text-[14px]">
                            replay
                          </span>
                          <span>Re-run</span>
                        </button>

                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {researchResults && (
        <section className="w-full max-w-7xl mx-auto px-6 sm:px-8 pb-10">
          <div className="flex flex-col gap-4">

            {/* Results header */}
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary">
                    <span className="material-symbols-outlined text-[16px]">
                      library_books
                    </span>
                  </div>

                  <span className="font-citation-tag text-citation-tag uppercase tracking-wider text-secondary font-semibold">
                    RESEARCH RESULTS
                  </span>
                </div>

                <h2 className="mt-2 text-xl sm:text-2xl font-semibold tracking-tight text-on-surface">
                  {researchResults.query}
                </h2>

                <p className="mt-1 text-sm text-on-surface-variant">
                  {researchResults.papers?.length || 0} papers discovered for this research question
                </p>
              </div>

              <button
                type="button"
                onClick={() => navigate("/papers")}
                className="self-start sm:self-auto inline-flex items-center gap-2 rounded-lg border border-outline-variant/30 bg-surface-container-low px-3.5 py-2 text-sm font-medium text-on-surface transition hover:bg-surface-container-high"
              >
                <span className="material-symbols-outlined text-[17px]">
                  library_books
                </span>
                View all papers
                <span className="material-symbols-outlined text-[16px]">
                  arrow_forward
                </span>
              </button>
            </div>

            {/* Result cards */}
            <div className="grid gap-3">
              {researchResults.papers?.map((paper) => (
                <article
                  key={paper.id}
                  className="group rounded-xl border border-outline-variant/25 bg-surface-container-lowest p-5 shadow-sm transition-all hover:border-secondary/30 hover:shadow-md"
                >
                  <div className="flex flex-col gap-4">

                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <h3 className="text-[16px] sm:text-[17px] font-semibold leading-6 text-on-surface">
                          {paper.title}
                        </h3>

                        <p className="mt-2 text-sm text-on-surface-variant">
                          {Array.isArray(paper.authors)
                            ? paper.authors.join(", ")
                            : paper.authors || "Unknown authors"}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          navigate(
                            `/paper/${encodeURIComponent(String(paper.id))}`
                          )
                        }
                        className="shrink-0 inline-flex items-center gap-1.5 rounded-lg border border-outline-variant/30 bg-surface-container px-3 py-2 text-xs font-semibold text-on-surface transition hover:bg-surface-container-high"
                      >
                        <span className="material-symbols-outlined text-[16px]">
                          open_in_new
                        </span>
                        Open
                      </button>
                    </div>

                    {/* Metadata */}
                    <div className="flex flex-wrap items-center gap-2 text-xs text-on-surface-variant">
                      {paper.year && (
                        <span className="rounded-md bg-surface-container px-2 py-1">
                          {paper.year}
                        </span>
                      )}

                      {paper.source && (
                        <span className="rounded-md bg-surface-container px-2 py-1">
                          {paper.source}
                        </span>
                      )}

                      {paper.citations != null && (
                        <span className="rounded-md bg-surface-container px-2 py-1">
                          {Number(paper.citations).toLocaleString()} citations
                        </span>
                      )}
                    </div>

                    {/* Abstract */}
                    {paper.abstract && (
                      <p className="line-clamp-3 text-sm leading-6 text-on-surface-variant">
                        {paper.abstract}
                      </p>
                    )}

                  </div>
                </article>
              ))}
            </div>

          </div>
        </section>
      )}

      <footer className="w-full bg-surface-container-low shadow-[0_-1px_4px_rgba(0,0,0,0.02)] py-space-md">
        <div className="w-full max-w-7xl mx-auto px-6 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-space-sm text-on-surface-variant font-label-sm text-label-sm">
          <span className="">
            ScholarPulse Academic Intelligence • Research, Comparison & Citation Tools
          </span>
          <div className="flex items-center gap-space-md font-code-sm text-code-sm" />
        </div>
      </footer>
    </div>
  );
}

export default Research;