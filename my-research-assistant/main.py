"""
Updated main.py with full functionality
"""
import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import components
try:
    from data.arxiv_fetcher import ArxivFetcher
    from data.semantic_scholar_fetcher import SemanticScholarFetcher
    from models.embedding_generator import EmbeddingGenerator
    from models.clustering import FaissClusterer
    from config.settings import DEFAULT_MAX_PAPERS, DEFAULT_ARXIV_CATEGORIES, PAPERS_DIR
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Some components not available: {str(e)}")
    COMPONENTS_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AcademicResearchPipeline:
    """
    Main pipeline class that orchestrates the complete research assistant workflow
    """
    
    def __init__(self):
        """Initialize the research pipeline"""
        if COMPONENTS_AVAILABLE:
            print("Academic Research Assistant - Full Version!")
            print("All components loaded successfully.")
        else:
            print("Academic Research Assistant - Demo Version")
            print("Some components missing. Copy component files for full functionality.")
        
        # Initialize components
        self.arxiv_fetcher = None
        self.semantic_fetcher = None
        self.embedding_generator = None
        self.clusterer = None
        
        # Data storage
        self.papers_data = []
        self.embeddings = None
        self.paper_ids = []
        self.clusters = {}
        
    def run_complete_pipeline(
        self,
        query: str,
        max_papers_per_source: int = 50,
        use_arxiv: bool = True,
        use_semantic_scholar: bool = True,
        arxiv_categories: List[str] = None,
        clustering_method: str = 'kmeans',
        analyze_gaps: bool = True,
        save_results: bool = True
    ) -> Dict:
        """Run the complete research assistant pipeline"""
        
        if not COMPONENTS_AVAILABLE:
            return self._run_demo_pipeline(query)
        
        logger.info("Starting Academic Research Assistant Pipeline")
        logger.info(f"Query: {query}")
        
        results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # Step 1: Fetch Papers
            logger.info("Step 1: Fetching papers...")
            papers = self.fetch_papers(
                query=query,
                max_papers_per_source=max_papers_per_source,
                use_arxiv=use_arxiv,
                use_semantic_scholar=use_semantic_scholar,
                arxiv_categories=arxiv_categories or DEFAULT_ARXIV_CATEGORIES
            )
            
            if not papers:
                raise Exception("No papers found for the given query")
            
            results['papers_found'] = len(papers)
            results['steps_completed'].append('fetch_papers')
            logger.info(f"✅ Fetched {len(papers)} papers")
            
            # Step 2: Generate Embeddings
            logger.info("Step 2: Generating embeddings...")
            embeddings, paper_ids = self.generate_embeddings(papers)
            
            if embeddings is None or len(embeddings) == 0:
                raise Exception("Failed to generate embeddings")
            
            results['embeddings_generated'] = len(embeddings)
            results['embedding_dimension'] = embeddings.shape[1]
            results['steps_completed'].append('generate_embeddings')
            logger.info(f"✅ Generated embeddings: {embeddings.shape}")
            
            # Step 3: Cluster Papers
            logger.info("Step 3: Clustering papers...")
            clusters = self.cluster_papers(
                embeddings=embeddings,
                paper_ids=paper_ids,
                method=clustering_method
            )
            
            if not clusters:
                logger.warning("No clusters generated")
            else:
                results['clusters_created'] = len(clusters)
                results['clustering_method'] = clustering_method
                results['steps_completed'].append('cluster_papers')
                logger.info(f"✅ Created {len(clusters)} clusters")
            
            # Step 4: Generate mock gap analysis (Llama2 optional)
            if analyze_gaps and clusters:
                logger.info("Step 4: Generating research gap analysis...")
                gap_analyses = self.generate_mock_gap_analysis(clusters)
                results['gap_analyses'] = len(gap_analyses)
                results['steps_completed'].append('analyze_gaps')
                logger.info(f"✅ Generated analysis for {len(gap_analyses)} clusters")
            
            # Step 5: Save Results
            if save_results:
                logger.info("Step 5: Saving results...")
                saved_files = self.save_results(query)
                results['saved_files'] = saved_files
                results['steps_completed'].append('save_results')
                logger.info("✅ Results saved")
            
            # Generate summary
            results['summary'] = self.generate_summary()
            
            logger.info("🎉 Pipeline completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            results['errors'].append(f"Pipeline error: {str(e)}")
            return results
    
    def _run_demo_pipeline(self, query: str) -> Dict:
        """Demo version when components are missing"""
        print(f"🚀 Running DEMO pipeline for query: {query}")
        print("📚 Step 1: Would fetch papers from arXiv and Semantic Scholar")
        print("🧠 Step 2: Would generate SBERT embeddings")
        print("🔍 Step 3: Would cluster papers using FAISS")
        print("🎯 Step 4: Would analyze research gaps")
        print("💾 Step 5: Would save results")
        
        return {
            "query": query,
            "status": "demo_completed",
            "message": "This is a demo run. Add component files for full functionality.",
            "steps_completed": ["demo_run"]
        }
    
    def fetch_papers(
        self,
        query: str,
        max_papers_per_source: int,
        use_arxiv: bool,
        use_semantic_scholar: bool,
        arxiv_categories: List[str]
    ) -> List[Dict]:
        """Fetch papers from selected sources"""
        all_papers = []
        
        try:
            if use_arxiv:
                logger.info("Fetching from arXiv...")
                if self.arxiv_fetcher is None:
                    self.arxiv_fetcher = ArxivFetcher()
                
                arxiv_papers = self.arxiv_fetcher.search_papers(
                    query=query,
                    categories=arxiv_categories,
                    max_results=max_papers_per_source
                )
                all_papers.extend(arxiv_papers)
                logger.info(f"Found {len(arxiv_papers)} papers from arXiv")
            
            if use_semantic_scholar:
                logger.info("Fetching from Semantic Scholar...")
                if self.semantic_fetcher is None:
                    self.semantic_fetcher = SemanticScholarFetcher()
                
                semantic_papers = self.semantic_fetcher.search_papers(
                    query=query,
                    max_results=max_papers_per_source
                )
                all_papers.extend(semantic_papers)
                logger.info(f"Found {len(semantic_papers)} papers from Semantic Scholar")
            
            # Remove duplicates
            unique_papers = self._deduplicate_papers(all_papers)
            self.papers_data = unique_papers
            
            logger.info(f"Total unique papers: {len(unique_papers)}")
            return unique_papers
            
        except Exception as e:
            logger.error(f"Error fetching papers: {str(e)}")
            raise
    
    def generate_embeddings(self, papers: List[Dict]) -> tuple:
        """Generate SBERT embeddings for papers"""
        try:
            if self.embedding_generator is None:
                logger.info("Loading SBERT model...")
                self.embedding_generator = EmbeddingGenerator()
            
            embeddings, paper_ids = self.embedding_generator.generate_paper_embeddings(
                papers, text_field='combined_text'
            )
            
            self.embeddings = embeddings
            self.paper_ids = paper_ids
            
            return embeddings, paper_ids
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def cluster_papers(self, embeddings, paper_ids: List[str], method: str = 'kmeans') -> Dict:
        """Cluster papers using FAISS"""
        try:
            if self.clusterer is None:
                embedding_dim = embeddings.shape[1]
                self.clusterer = FaissClusterer(embedding_dim)
            
            # Add embeddings to FAISS index
            self.clusterer.add_embeddings(embeddings, paper_ids)
            
            # Perform clustering
            clusters = self.clusterer.cluster_papers(
                embeddings=embeddings,
                paper_ids=paper_ids,
                method=method
            )
            
            self.clusters = clusters
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering papers: {str(e)}")
            raise
    
    def generate_mock_gap_analysis(self, clusters: Dict) -> Dict:
        """Generate mock gap analysis"""
        gap_analyses = {}
        
        for cluster_id, paper_ids in clusters.items():
            gap_analyses[cluster_id] = {
                'summary': f'This cluster contains {len(paper_ids)} related research papers.',
                'gaps': [
                    'Limited cross-domain validation of proposed methods',
                    'Insufficient comparison with recent state-of-the-art approaches',
                    'Lack of theoretical analysis for empirical results'
                ],
                'suggestions': [
                    'Explore applications in emerging domains (Novelty: 8/10)',
                    'Develop comprehensive benchmarking frameworks (Novelty: 7/10)',
                    'Investigate theoretical foundations (Novelty: 9/10)'
                ],
                'cluster_size': len(paper_ids)
            }
        
        return gap_analyses
    
    def save_results(self, query: str) -> Dict[str, str]:
        """Save results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = {}
        
        try:
            # Save papers
            if self.papers_data:
                papers_file = PAPERS_DIR / f"papers_{query.replace(' ', '_')}_{timestamp}.json"
                with open(papers_file, 'w', encoding='utf-8') as f:
                    json.dump(self.papers_data, f, indent=2, ensure_ascii=False)
                saved_files['papers'] = str(papers_file)
                logger.info(f"Saved papers to {papers_file}")
            
            # Save embeddings
            if self.embeddings is not None and self.embedding_generator:
                embeddings_file = self.embedding_generator.save_embeddings(
                    self.embeddings, self.paper_ids, 
                    f"embeddings_{query.replace(' ', '_')}_{timestamp}"
                )
                saved_files['embeddings'] = embeddings_file
            
            # Save clusters
            if self.clusters and self.clusterer:
                clusters_file = self.clusterer.save_clusters()
                saved_files['clusters'] = clusters_file
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return {}
    
    def generate_summary(self) -> Dict:
        """Generate summary of results"""
        summary = {
            'total_papers': len(self.papers_data),
            'total_clusters': len(self.clusters),
            'largest_cluster_size': max(len(papers) for papers in self.clusters.values()) if self.clusters else 0,
        }
        
        # Calculate year range
        years = [paper.get('year') for paper in self.papers_data if paper.get('year')]
        if years:
            summary['year_range'] = (min(years), max(years))
        
        return summary
    
    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """Remove duplicate papers based on title similarity"""
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            title = paper.get('title', '').lower().strip()
            if title and title not in seen_titles:
                unique_papers.append(paper)
                seen_titles.add(title)
        
        return unique_papers

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Academic Research Assistant CLI')
    
    # Required arguments
    parser.add_argument('query', help='Research query string')
    
    # Optional arguments
    parser.add_argument('--max-papers', type=int, default=50,
                       help='Maximum papers per source (default: 50)')
    parser.add_argument('--no-arxiv', action='store_true',
                       help='Skip arXiv search')
    parser.add_argument('--no-semantic-scholar', action='store_true', 
                       help='Skip Semantic Scholar search')
    parser.add_argument('--clustering-method', choices=['kmeans', 'community', 'hierarchical'],
                       default='kmeans', help='Clustering method (default: kmeans)')
    parser.add_argument('--no-gap-analysis', action='store_true',
                       help='Skip research gap analysis')
    parser.add_argument('--no-save', action='store_true',
                       help='Don\'t save results to files')
    parser.add_argument('--arxiv-categories', nargs='+',
                       default=DEFAULT_ARXIV_CATEGORIES,
                       help='arXiv categories to search')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize pipeline
    pipeline = AcademicResearchPipeline()
    
    try:
        results = pipeline.run_complete_pipeline(
            query=args.query,
            max_papers_per_source=args.max_papers,
            use_arxiv=not args.no_arxiv,
            use_semantic_scholar=not args.no_semantic_scholar,
            arxiv_categories=args.arxiv_categories,
            clustering_method=args.clustering_method,
            analyze_gaps=not args.no_gap_analysis,
            save_results=not args.no_save
        )
        
        # Print results summary
        print("\n" + "="*60)
        print("📊 RESULTS SUMMARY")
        print("="*60)
        print(f"Query: {results['query']}")
        print(f"Status: {results.get('status', 'completed')}")
        
        if 'summary' in results:
            summary = results['summary']
            print(f"\n📈 STATISTICS:")
            print(f"  • Total Papers: {summary['total_papers']}")
            if summary.get('year_range'):
                print(f"  • Year Range: {summary['year_range'][0]}-{summary['year_range'][1]}")
            print(f"  • Clusters Created: {summary['total_clusters']}")
            if summary['largest_cluster_size']:
                print(f"  • Largest Cluster: {summary['largest_cluster_size']} papers")
        
        if results.get('saved_files'):
            print(f"\n💾 SAVED FILES:")
            for file_type, filepath in results['saved_files'].items():
                print(f"  • {file_type}: {filepath}")
        
        if results.get('errors'):
            print(f"\n⚠️  ERRORS:")
            for error in results['errors']:
                print(f"  • {error}")
        
        print("\n🎉 Pipeline completed!")
        print("\nTo view results in dashboard, run:")
        print("streamlit run dashboard/app.py")
        
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        if not COMPONENTS_AVAILABLE:
            print("Hint: Make sure all component files are properly installed!")
        sys.exit(1)

if __name__ == "__main__":
    main()