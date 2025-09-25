"""
Quick setup script to add component files for full functionality
Run this after you've copied the component file contents
"""
import os
import sys
from pathlib import Path

def setup_components():
    """Setup component files"""
    
    print("Setting up Academic Research Assistant components...")
    
    # Check if files exist
    required_files = {
        'data/arxiv_fetcher.py': 'arXiv API integration',
        'data/semantic_scholar_fetcher.py': 'Semantic Scholar API integration', 
        'models/embedding_generator.py': 'SBERT embeddings generator',
        'models/clustering.py': 'FAISS clustering system'
    }
    
    missing_files = []
    existing_files = []
    
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            existing_files.append(f"✅ {file_path} - {description}")
        else:
            missing_files.append(f"❌ {file_path} - {description}")
    
    print("\nComponent Status:")
    print("=" * 50)
    
    for file_status in existing_files:
        print(file_status)
    
    for file_status in missing_files:
        print(file_status)
    
    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} component files!")
        print("\nTo get full functionality:")
        print("1. Copy the component file contents from the previous messages")
        print("2. Save them to the correct locations shown above")
        print("3. Run this script again to verify")
        return False
    else:
        print(f"\n🎉 All {len(existing_files)} component files found!")
        print("\nTesting imports...")
        
        # Test imports
        try:
            sys.path.append(str(Path(__file__).parent))
            
            from data.arxiv_fetcher import ArxivFetcher
            print("✅ arXiv fetcher imported successfully")
            
            from data.semantic_scholar_fetcher import SemanticScholarFetcher  
            print("✅ Semantic Scholar fetcher imported successfully")
            
            from models.embedding_generator import EmbeddingGenerator
            print("✅ Embedding generator imported successfully")
            
            from models.clustering import FaissClusterer
            print("✅ Clustering system imported successfully")
            
            print("\n🚀 SETUP COMPLETE!")
            print("=" * 50)
            print("Your Academic Research Assistant is ready!")
            print("\nNext steps:")
            print("1. Test: python main.py 'machine learning' --max-papers 10")
            print("2. Dashboard: streamlit run dashboard/app.py")
            print("3. Full run: python main.py 'your research topic' --max-papers 50")
            
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {str(e)}")
            print("\nPlease check that all files are copied correctly.")
            return False

if __name__ == "__main__":
    setup_components()