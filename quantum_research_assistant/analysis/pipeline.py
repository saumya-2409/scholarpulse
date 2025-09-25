"""
Complete Analysis Pipeline
Orchestrates the entire research analysis process
"""

import streamlit as st
import time
from concurrent.futures import ThreadPoolExecutor
from data.fetchers.multi_source_fetcher import MultiSourceFetcher
from data.processors.deduplication import deduplicate_papers
from data.processors.enhancement import enhance_papers
from analysis.embeddings import EmbeddingGenerator
from analysis.clustering import ClusteringManager
from analysis.gap_analysis import GapAnalyzer
from analysis.reading_optimizer import ReadingOrderOptimizer
from data.storage.session_manager import (
    update_papers_data, update_embeddings, update_clusters,
    update_gap_analyses, update_reading_order, set_analysis_progress
)

class AnalysisPipeline:
    """Complete analysis pipeline orchestrator"""
    
    def __init__(self):
        self.steps = [
            ("Initializing sources", self._initialize_sources),
            ("Fetching papers", self._fetch_papers),
            ("Processing & deduplication", self._process_papers),
            ("Generating embeddings", self._generate_embeddings),
            ("Clustering papers", self._cluster_papers),
            ("Analyzing gaps", self._analyze_gaps),
            ("Optimizing reading order", self._optimize_reading_order),
            ("Finalizing results", self._finalize_results)
        ]
        
        self.fetcher = MultiSourceFetcher()
        self.embedding_generator = EmbeddingGenerator()
        self.clustering_manager = ClusteringManager()
        self.gap_analyzer = GapAnalyzer()
        self.reading_optimizer = ReadingOrderOptimizer()
        
        self.progress_callback = None
        
    def run_complete_analysis(self, query, sources, max_papers, **kwargs):
        """
        Run the complete analysis pipeline
        
        Args:
            query: Research query string
            sources: List of sources to fetch from
            max_papers: Maximum papers per source
            **kwargs: Additional configuration
        
        Returns:
            bool: Success status
        """
        
        try:
            total_steps = len(self.steps)
            
            for i, (step_name, step_function) in enumerate(self.steps):
                
                # Update progress
                progress = (i / total_steps) * 100
                self._update_progress(progress, step_name)
                
                # Execute step
                try:
                    result = step_function(query, sources, max_papers, **kwargs)
                    
                    if not result:
                        st.error(f"❌ Failed at step: {step_name}")
                        return False
                        
                except Exception as e:
                    st.error(f"❌ Error in {step_name}: {str(e)}")
                    return False
                
                # Small delay for UI updates
                time.sleep(0.1)
            
            # Final progress update
            self._update_progress(100, "Analysis complete!")
            return True
            
        except Exception as e:
            st.error(f"❌ Pipeline error: {str(e)}")
            return False
    
    def _initialize_sources(self, query, sources, max_papers, **kwargs):
        """Initialize data sources"""
        try:
            self.fetcher.initialize_sources(sources)
            return True
        except Exception as e:
            st.warning(f"Source initialization warning: {str(e)}")
            return True  # Continue even if some sources fail
    
    def _fetch_papers(self, query, sources, max_papers, **kwargs):
        """Fetch papers from all sources"""
        try:
            papers = self.fetcher.fetch_from_all_sources(
                query=query,
                sources=sources,
                max_papers_per_source=max_papers
            )
            
            if not papers:
                st.warning("No papers fetched from any source")
                return False
            
            # Store raw papers temporarily
            self._raw_papers = papers
            st.info(f"✅ Fetched {len(papers)} papers from {len(sources)} sources")
            return True
            
        except Exception as e:
            st.error(f"Paper fetching failed: {str(e)}")
            return False
    
    def _process_papers(self, query, sources, max_papers, **kwargs):
        """Process and deduplicate papers"""
        try:
            if not hasattr(self, '_raw_papers'):
                return False
            
            # Deduplicate papers
            unique_papers = deduplicate_papers(self._raw_papers)
            
            # Enhance papers with AI summaries and links
            enhanced_papers = enhance_papers(unique_papers)
            
            # Update session data
            update_papers_data(enhanced_papers)
            
            self._processed_papers = enhanced_papers
            
            st.info(f"✅ Processed {len(enhanced_papers)} unique papers")
            return True
            
        except Exception as e:
            st.error(f"Paper processing failed: {str(e)}")
            return False
    
    def _generate_embeddings(self, query, sources, max_papers, **kwargs):
        """Generate semantic embeddings"""
        try:
            if not hasattr(self, '_processed_papers'):\n                return False\n            \n            embeddings = self.embedding_generator.generate_embeddings(\n                self._processed_papers\n            )\n            \n            if embeddings is None:\n                st.warning(\"Embedding generation failed, skipping clustering\")\n                return True  # Continue without embeddings\n            \n            # Update session data\n            update_embeddings(embeddings)\n            \n            self._embeddings = embeddings\n            \n            st.info(f\"✅ Generated embeddings for {len(self._processed_papers)} papers\")\n            return True\n            \n        except Exception as e:\n            st.warning(f\"Embedding generation failed: {str(e)}\")\n            return True  # Continue without embeddings\n    \n    def _cluster_papers(self, query, sources, max_papers, **kwargs):\n        \"\"\"Cluster papers using embeddings\"\"\"\n        try:\n            if not hasattr(self, '_embeddings') or self._embeddings is None:\n                st.info(\"⏭️ Skipping clustering (no embeddings)\")\n                return True\n            \n            cluster_method = kwargs.get('cluster_method', 'kmeans')\n            \n            clusters = self.clustering_manager.cluster_papers(\n                papers=self._processed_papers,\n                embeddings=self._embeddings,\n                method=cluster_method\n            )\n            \n            if not clusters:\n                st.warning(\"Clustering produced no results\")\n                return True\n            \n            # Update session data\n            update_clusters(clusters)\n            \n            self._clusters = clusters\n            \n            st.info(f\"✅ Created {len(clusters)} research clusters\")\n            return True\n            \n        except Exception as e:\n            st.warning(f\"Clustering failed: {str(e)}\")\n            return True  # Continue without clustering\n    \n    def _analyze_gaps(self, query, sources, max_papers, **kwargs):\n        \"\"\"Analyze research gaps\"\"\"\n        try:\n            if not kwargs.get('enable_gap_analysis', True):\n                st.info(\"⏭️ Gap analysis disabled\")\n                return True\n            \n            if not hasattr(self, '_clusters'):\n                st.info(\"⏭️ Skipping gap analysis (no clusters)\")\n                return True\n            \n            gap_analyses = self.gap_analyzer.analyze_research_gaps(\n                papers=self._processed_papers,\n                clusters=self._clusters,\n                query=query\n            )\n            \n            if not gap_analyses:\n                st.warning(\"Gap analysis produced no results\")\n                return True\n            \n            # Update session data\n            update_gap_analyses(gap_analyses)\n            \n            st.info(f\"✅ Completed gap analysis for {len(gap_analyses)} clusters\")\n            return True\n            \n        except Exception as e:\n            st.warning(f\"Gap analysis failed: {str(e)}\")\n            return True  # Continue without gap analysis\n    \n    def _optimize_reading_order(self, query, sources, max_papers, **kwargs):\n        \"\"\"Generate optimized reading order\"\"\"\n        try:\n            if not kwargs.get('enable_reading_order', True):\n                st.info(\"⏭️ Reading order optimization disabled\")\n                return True\n            \n            reading_order = self.reading_optimizer.optimize_reading_order(\n                papers=self._processed_papers,\n                clusters=getattr(self, '_clusters', {}),\n                query=query\n            )\n            \n            if not reading_order:\n                st.warning(\"Reading order optimization produced no results\")\n                return True\n            \n            # Update session data\n            update_reading_order(reading_order)\n            \n            st.info(f\"✅ Generated optimized reading order for {len(reading_order)} papers\")\n            return True\n            \n        except Exception as e:\n            st.warning(f\"Reading order optimization failed: {str(e)}\")\n            return True  # Continue without reading order\n    \n    def _finalize_results(self, query, sources, max_papers, **kwargs):\n        \"\"\"Finalize analysis results\"\"\"\n        try:\n            # Clean up temporary data\n            if hasattr(self, '_raw_papers'):\n                delattr(self, '_raw_papers')\n            \n            # Generate summary statistics\n            summary = {\n                'query': query,\n                'sources': sources,\n                'total_papers': len(self._processed_papers),\n                'clusters': len(getattr(self, '_clusters', {})),\n                'gap_analyses': len(st.session_state.get('gap_analyses', {})),\n                'reading_order': len(st.session_state.get('reading_order', [])),\n                'timestamp': time.time()\n            }\n            \n            # Store analysis summary\n            st.session_state.analysis_summary = summary\n            \n            st.success(\"🎉 Analysis completed successfully!\")\n            return True\n            \n        except Exception as e:\n            st.warning(f\"Finalization warning: {str(e)}\")\n            return True  # Still consider success\n    \n    def _update_progress(self, progress, message):\n        \"\"\"Update progress callback\"\"\"\n        set_analysis_progress(progress, message)\n        \n        if self.progress_callback:\n            self.progress_callback(progress, message)\n        \n        # Force UI update\n        if hasattr(st, 'rerun'):\n            st.rerun()\n\ndef start_complete_analysis(query, sources, max_papers, **kwargs):\n    \"\"\"\n    Convenience function to start complete analysis\n    \n    Args:\n        query: Research query\n        sources: List of source names\n        max_papers: Max papers per source\n        **kwargs: Additional options\n    \n    Returns:\n        bool: Success status\n    \"\"\"\n    \n    pipeline = AnalysisPipeline()\n    \n    # Set progress callback if provided\n    if 'progress_callback' in kwargs:\n        pipeline.progress_callback = kwargs['progress_callback']\n    \n    return pipeline.run_complete_analysis(\n        query=query,\n        sources=sources,\n        max_papers=max_papers,\n        **kwargs\n    )\n\ndef run_analysis_async(query, sources, max_papers, **kwargs):\n    \"\"\"\n    Run analysis asynchronously (future enhancement)\n    \n    This is a placeholder for future async implementation\n    \"\"\"\n    \n    # For now, run synchronously\n    return start_complete_analysis(query, sources, max_papers, **kwargs)