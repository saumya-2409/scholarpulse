# Academic Research Paper Assistant

**Semi-autonomous literature survey tool with clustering and research gap analysis**

A comprehensive AI-powered research assistant that fetches academic papers, clusters them semantically, and identifies research gaps using modern NLP techniques.

## Features

- **Multi-source Paper Fetching**: Integrates arXiv and Semantic Scholar APIs
- **Semantic Embeddings**: Uses SBERT for high-quality paper representations
- **Intelligent Clustering**: FAISS-powered similarity search and clustering
- **Research Gap Analysis**: Llama2-based analysis for identifying unexplored areas
- **Interactive Dashboard**: Streamlit-powered web interface
- **CLI Interface**: Command-line tool for automated processing

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Dashboard
```bash
streamlit run dashboard/app.py
```

### 3. Or Use CLI
```bash
python main.py "machine learning transformers" --max-papers 50
```

## Technology Stack

- **Paper Sources**: arXiv API, Semantic Scholar API
- **Embeddings**: SBERT (all-MiniLM-L6-v2)
- **Clustering**: FAISS + scikit-learn
- **Gap Analysis**: Llama2-7B (quantized)
- **Dashboard**: Streamlit
- **Data Processing**: pandas, numpy

## Project Structure

```
Academic-Research-Assistant/
├── README.md
├── requirements.txt
├── main.py                    # CLI interface
├── config/
│   └── settings.py           # Configuration
├── data/                     # Data fetching modules
├── models/                   # AI/ML components  
├── dashboard/
│   └── app.py               # Streamlit dashboard
└── storage/                 # Data storage
```

## Usage Examples

### Web Dashboard
1. Launch: `streamlit run dashboard/app.py`
2. Enter query: "transformer attention mechanisms"
3. Configure parameters
4. Click "Process All"
5. Explore results

### Command Line
```bash
# Basic usage
python main.py "computer vision deep learning"

# Advanced options
python main.py "NLP transformers" \
  --max-papers 100 \
  --clustering-method kmeans \
  --no-gap-analysis
```

## Expected Results

The system generates:
- **Paper Collections**: Deduplicated papers from multiple sources
- **Semantic Clusters**: Groups of related research papers
- **Research Gap Analysis**: Identified unexplored research directions
- **Novelty Ratings**: Potential impact scores for suggested research

## Configuration

Customize settings in `config/settings.py`:
- API endpoints and rate limits
- Model configurations (SBERT, Llama2)
- Clustering parameters
- Output formats

## Prerequisites

- Python 3.8+
- 4GB+ RAM (8GB+ recommended)
- Internet connection for APIs and model downloads
- Optional: CUDA GPU for faster processing

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## License

MIT License - see LICENSE file for details.

## Educational Value

This project demonstrates:
- Modern NLP pipeline development
- API integration and data processing
- Machine learning model deployment
- Full-stack application development
- Academic research automation

---

**Star this repository if you find it useful!**

**Happy researching!**