import {
  createContext,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";

import { papers as initialPapers } from "../data/paper";

const PaperContext = createContext(null);

export function PaperProvider({ children }) {

  const [papers, setPapers] = useState(() => {
    const savedPapers = localStorage.getItem("scholarpulse_research_papers");

    if (savedPapers) {
      try {
        return JSON.parse(savedPapers);
      } catch {
        return initialPapers;
      }
    }

    return initialPapers;
  });

  const [selectedIds, setSelectedIds] = useState([]);
  const [researchResults, setResearchResults] = useState(null);
  const [bookmarksLoaded, setBookmarksLoaded] = useState(false);

  useEffect(() => {
    const savedBookmarks = JSON.parse(
      localStorage.getItem("scholarpulse_bookmarks") || "[]"
    );

    setPapers((current) =>
      current.map((paper) => ({
        ...paper,
        bookmarked: savedBookmarks.includes(paper.id),
      }))
    );

    setBookmarksLoaded(true);
  }, []);

  useEffect(() => {
    if (!bookmarksLoaded) return;

    const bookmarkedIds = papers
      .filter((paper) => paper.bookmarked)
      .map((paper) => paper.id);

    localStorage.setItem(
      "scholarpulse_bookmarks",
      JSON.stringify(bookmarkedIds)
    );
  }, [papers, bookmarksLoaded]);

  useEffect(() => {
    localStorage.setItem(
      "scholarpulse_research_papers",
      JSON.stringify(papers)
    );
  }, [papers]);

  const setResearchPapers = (newPapers) => {
    const bookmarkedIds = JSON.parse(
      localStorage.getItem("scholarpulse_bookmarks") || "[]"
    );

    setPapers(
      newPapers.map((paper) => ({
        ...paper,
        bookmarked: bookmarkedIds.includes(paper.id),
      }))
    );
  };

  const toggleBookmark = (paperId) => {
    setPapers((current) =>
      current.map((paper) =>
        paper.id === paperId
          ? {
              ...paper,
              bookmarked: !paper.bookmarked,
            }
          : paper
      )
    );
  };

  const toggleSelection = (paperId) => {
    setSelectedIds((current) =>
      current.includes(paperId)
        ? current.filter((id) => id !== paperId)
        : [...current, paperId]
    );
  };

  const clearSelection = () => {
    setSelectedIds([]);
  };

  const getPaper = (paperId) => {
    return papers.find(
      (paper) => String(paper.id) === String(paperId)
    );
  };

  const selectedPapers = useMemo(
    () => papers.filter((paper) => selectedIds.includes(paper.id)),
    [papers, selectedIds]
  );

  const bookmarkedPapers = useMemo(
    () => papers.filter((paper) => paper.bookmarked),
    [papers]
  );

  const value = {
    papers,
    selectedIds,
    selectedPapers,
    bookmarkedPapers,
    researchResults,
    toggleBookmark,
    toggleSelection,
    clearSelection,
    getPaper,
    setResearchPapers,
    setResearchResults,
  };

  return (
    <PaperContext.Provider value={value}>
      {children}
    </PaperContext.Provider>
  );
}

export function usePapers() {
  const context = useContext(PaperContext);

  if (!context) {
    throw new Error(
      "usePapers must be used inside a PaperProvider"
    );
  }

  return context;
}