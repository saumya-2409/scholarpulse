import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import NavBar from "../components/NavBar";
import { usePapers } from "../context/PaperContext";
import { useAuth } from "../context/AuthContext";

function PaperReader() {
  const navigate = useNavigate();
  const { id } = useParams();
  const paperId = decodeURIComponent(id);

  const { token } = useAuth();
  const { getPaper } = usePapers();

  const paper = getPaper(paperId); 

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [isAsking, setIsAsking] = useState(false);

  if (!paper) {
    return (
      <div className="min-h-screen bg-surface text-on-surface font-body-md">
        <NavBar />

        <main className="mx-auto max-w-4xl px-6 py-16">
          <div className="rounded-lg border border-outline-variant bg-surface-container-lowest p-10 text-center">
            <span className="material-symbols-outlined mb-3 text-4xl text-on-surface-variant">
              find_in_page
            </span>

            <h1 className="text-headline-sm font-semibold">
              Paper not found
            </h1>

            <p className="mt-2 text-body-sm text-on-surface-variant">
              This paper is not available in the current research workspace.
            </p>

            <button
              type="button"
              onClick={() => navigate("/papers")}
              className="mt-5 rounded-md bg-primary px-4 py-2 text-label-md font-medium text-white hover:opacity-90"
            >
              Back to Papers
            </button>
          </div>
        </main>
      </div>
    );
  }

  const handleAsk = async (event) => {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isAsking) return;

    setIsAsking(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/paper/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            paper_id: paper.id,
            question: trimmedQuestion,
            paper: paper,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to get an answer."
        );
      }

      setMessages((current) => [
        ...current,
        {
          id: Date.now(),
          question: trimmedQuestion,
          answer: data.answer,
          evidence: data.evidence,
        },
      ]);

      setQuestion("");
    } catch (error) {
      console.error("Paper chat error:", error);

      setMessages((current) => [
        ...current,
        {
          id: Date.now(),
          question: trimmedQuestion,
          answer: `Sorry, I couldn't answer that question. ${error.message}`,
          evidence: "",
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  const suggestedQuestions = [
    "What is the main contribution of this paper?",
    "What methodology does the paper use?",
    "What are the key findings?",
    "What are the limitations?",
  ];

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body-md">
      <NavBar />

      <main className="w-full">
        <div className="mx-auto max-w-7xl px-6 py-8">

          {/* Back */}
          <button
            type="button"
            onClick={() => navigate("/papers")}
            className="mb-6 inline-flex items-center gap-1.5 text-label-md font-medium text-on-surface-variant transition hover:text-secondary"
          >
            <span className="material-symbols-outlined text-[18px]">
              arrow_back
            </span>
            Back to Papers
          </button>

          {/* Paper header */}
          <section className="mb-8">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                <span className="material-symbols-outlined text-[16px]">
                  article
                </span>
              </div>

              <span className="font-citation-tag text-citation-tag uppercase tracking-wider text-secondary font-semibold">
                PAPER READER
              </span>

              {paper.source && (
                <span className="rounded-md bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                  {paper.source}
                </span>
              )}

              {paper.year && (
                <span className="rounded-md bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                  {paper.year}
                </span>
              )}

              {paper.accessibility && (
                <span className="rounded-md bg-surface-container px-2 py-1 font-code-sm text-[11px] text-on-surface-variant">
                  {paper.accessibility}
                </span>
              )}
            </div>

            <h1 className="max-w-5xl font-headline-xl text-3xl font-semibold leading-tight tracking-tight text-on-surface">
              {paper.title}
            </h1>

            <p className="mt-3 max-w-4xl text-body-md leading-6 text-on-surface-variant">
              {Array.isArray(paper.authors)
                ? paper.authors.join(", ")
                : paper.authors || "Authors unavailable"}
            </p>

            <div className="mt-4 flex flex-wrap items-center gap-4 text-body-sm text-on-surface-variant">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px]">
                  format_quote
                </span>

                {(paper.citations ?? 0).toLocaleString()} citations
              </span>

              {paper.doi && (
                <span className="font-code-sm text-[11px]">
                  DOI: {paper.doi}
                </span>
              )}
            </div>
          </section>

          {/* Reader + Copilot */}
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">

            {/* Paper reader */}
            <section className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm">

              <div className="flex items-center justify-between border-b border-outline-variant px-5 py-4">
                <div>
                  <h2 className="text-headline-sm font-semibold">
                    Paper overview
                  </h2>

                  <p className="mt-1 text-body-sm text-on-surface-variant">
                    Key information available for this paper.
                  </p>
                </div>

                <button
                  type="button"
                  className="flex items-center gap-1.5 rounded-md border border-outline-variant px-3 py-2 text-label-md font-medium text-on-surface-variant hover:bg-surface-container"
                  onClick={() => {
  const pdfUrl = paper.pdf_url || paper.url;

  if (pdfUrl) {
    window.open(pdfUrl, "_blank", "noopener,noreferrer");
  }
}}
                >
                  <span className="material-symbols-outlined text-[18px]">
                    picture_as_pdf
                  </span>
                  PDF
                </button>
              </div>

              <div className="space-y-8 p-6">

                {/* Summary */}

                <div>
  <h3 className="mb-3 text-label-md font-semibold text-on-surface">
    Abstract
  </h3>

  <div className="rounded-md bg-surface-container-low p-5">
    <p className="text-body-md leading-7 text-on-surface-variant">
      {paper.abstract || "No abstract is available for this paper."}
    </p>
  </div>
</div>

{paper.ai_summary && (
  <div>
    <h3 className="mb-3 text-label-md font-semibold text-on-surface">
      AI Summary
    </h3>

    <div className="rounded-md border border-outline-variant bg-surface-container-low p-5">
      <pre className="whitespace-pre-wrap font-body-md text-body-md leading-7 text-on-surface-variant">
        {typeof paper.ai_summary === "string"
          ? paper.ai_summary
          : JSON.stringify(paper.ai_summary, null, 2)}
      </pre>
    </div>
  </div>
)}
                {/* Metadata */}
                <div>
                  <h3 className="mb-3 text-label-md font-semibold text-on-surface">
                    Paper information
                  </h3>

                  <dl className="divide-y divide-outline-variant rounded-md border border-outline-variant">                   
                    <MetadataRow
                      label="Authors"
                      value={
                        Array.isArray(paper.authors)
                          ? paper.authors.join(", ")
                          : paper.authors || "—"
                      }
                    />
                    <MetadataRow label="Year" value={paper.year || "—"} />
                    <MetadataRow label="Source" value={paper.source || "—"} />
                    <MetadataRow label="DOI" value={paper.doi || "—"} />
                    <MetadataRow label="URL" value={paper.url || "—"} />

                  </dl>
                </div>

                {/* Grounding notice */}
                <div className="rounded-md border border-outline-variant bg-surface-container-low p-4">
                  <div className="flex gap-3">
                    <span className="material-symbols-outlined text-secondary">
                      verified
                    </span>

                    <div>
                      <p className="text-label-md font-semibold text-on-surface">
                        Grounded answers
                      </p>

                      <p className="mt-1 text-body-sm leading-5 text-on-surface-variant">
                        Answers are grounded in the paper's available content
                        and include supporting evidence when available.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Copilot */}
            <aside className="flex min-h-[650px] flex-col rounded-xl border border-outline-variant/30 bg-surface-container-lowest shadow-sm">

              <div className="border-b border-outline-variant px-5 py-4">
                <div className="flex items-center gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
                    <span className="material-symbols-outlined text-[18px]">
                      auto_awesome
                    </span>
                  </div>

                  <div>
                    <h2 className="text-headline-sm font-semibold">
                      Research Copilot
                    </h2>

                    <p className="text-body-sm text-on-surface-variant">
                      Ask about this paper
                    </p>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-5">

                {messages.length === 0 ? (
                  <div>
                    <div className="mb-5 rounded-md bg-surface-container-low p-4">
                      <p className="text-body-sm leading-5 text-on-surface-variant">
                        Ask a question about this paper. Responses are generated
                        from the paper's available content and include supporting
                        evidence when available.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <p className="mb-3 text-label-sm uppercase tracking-wide text-on-surface-variant">
                        Suggested questions
                      </p>

                      {suggestedQuestions.map((item) => (
                        <button
                          key={item}
                          type="button"
                          onClick={() => setQuestion(item)}
                          className="block w-full rounded-lg border border-outline-variant/40 bg-surface-container-lowest px-3.5 py-3 text-left text-body-sm leading-5 text-on-surface transition hover:border-secondary/40 hover:bg-surface-container-low"
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-5">
                   {messages.map((message) => (
  <div key={message.id} className="space-y-4">
    <div className="rounded-lg bg-surface-container-low p-4">
      <p className="text-sm font-medium text-on-surface">
        {message.question}
      </p>
    </div>

    <div className="rounded-lg border border-outline-variant/30 bg-surface-container-lowest p-5 shadow-sm">
      <p className="text-sm leading-6 text-on-surface">
        {message.answer}
      </p>

      {message.evidence && (
        <div className="mt-4 border-t border-outline-variant pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-on-surface-variant">
            Evidence
          </p>

          <p className="mt-2 text-sm leading-6 text-on-surface-variant">
            {message.evidence}
          </p>
        </div>
      )}
    </div>
  </div>
))}
                  </div>
                )}
              </div>

              {/* Input */}
              <form
                onSubmit={handleAsk}
                className="border-t border-outline-variant p-4"
              >
                <div className="rounded-md border border-outline-variant bg-surface-container-low">
                  <textarea
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask about this paper..."
                    rows={3}
                    className="w-full resize-none bg-transparent px-3 py-3 text-body-sm text-on-surface outline-none placeholder:text-on-surface-variant"
                  />

                  <div className="flex justify-end border-t border-outline-variant px-2 py-2">
                    <button
                      type="submit"
                      disabled={isAsking || !question.trim()}
                      className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-label-md font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {isAsking ? "Thinking..." : "Ask"}
                    </button>
                  </div>
                </div>
              </form>
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}

function MetadataRow({ label, value }) {
  return (
    <div className="grid grid-cols-[110px_1fr] gap-4 px-4 py-3">
      <dt className="text-label-sm uppercase tracking-wide text-on-surface-variant">
        {label}
      </dt>

      <dd className="text-body-sm text-on-surface">
        {value}
      </dd>
    </div>
  );
}

export default PaperReader;