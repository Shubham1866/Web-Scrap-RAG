# Web-Scrap-RAG

A powerful web scraping and Retrieval-Augmented Generation (RAG) application built with FastAPI, LLMs, and vector databases.

## 🎯 Overview

Web-Scrap-RAG is a full-stack application that combines:
- **Web Scraping**: Extract content from websites using BeautifulSoup and modern async HTTP clients
- **Document Processing**: Handle multiple file formats (PDF, DOCX, TXT)
- **RAG Pipeline**: Retrieve relevant information and augment LLM responses with embeddings and vector search
- **FastAPI Backend**: High-performance REST API with authentication and database support
- **Vector Database**: FAISS for efficient similarity search using sentence transformers

## ✨ Features

- 🕷️ **Web Scraping** - Scrape and process web content using multiple HTTP clients
- 📄 **Multi-format Document Support** - Process PDF, DOCX, and TXT files
- 🔐 **Authentication** - Secure user authentication with JWT and bcrypt
- 🧠 **LLM Integration** - Ollama support for local LLM inference
- 📊 **Vector Embeddings** - Sentence transformers for semantic understanding
- 🔍 **RAG Implementation** - Combine web scraping with LLM for intelligent retrieval
- 💾 **Database Support** - MySQL integration with SQLAlchemy ORM
- ⚡ **Async Processing** - Built with async/await for high performance
- 🗂️ **File Upload Handling** - Support for multipart file uploads

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI applications

### Database
- **SQLAlchemy** - ORM for database operations
- **PyMySQL** - MySQL database driver
- **Alembic** - Database migration tool

### Authentication & Security
- **python-jose** - JSON Web Token (JWT) support
- **passlib** - Password hashing utilities
- **bcrypt** - Secure password encryption

### Web Scraping
- **requests** - HTTP client for web requests
- **httpx** - Async HTTP client
- **aiohttp** - Async HTTP client and web server
- **BeautifulSoup4** - HTML/XML parsing
- **lxml** - XML and HTML processing

### Document Processing
- **pypdf** - PDF file handling
- **python-docx** - Microsoft Word document support

### Machine Learning & NLP
- **FAISS** - Facebook AI Similarity Search for vector search
- **NumPy** - Numerical computing
- **sentence-transformers** - Generate embeddings for semantic search
- **ollama** - Local LLM inference

### Utilities
- **python-dotenv** - Environment variable management
- **pydantic** - Data validation and settings
- **tqdm** - Progress bar utilities
- **python-multipart** - Multipart form data parsing

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- MySQL database (optional, for persistence)
- Ollama (for local LLM inference)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shubham1866/Web-Scrap-RAG.git
   cd Web-Scrap-RAG
Create a virtual environment

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

bash
pip install -r requirements.txt
Set up environment variables

bash
# Update DATABASE_URL in .env
alembic upgrade head

🚀 Usage
Start the API Server
bash
python -m uvicorn app.main:app --reload
The API will be available at http://localhost:8000

API Documentation
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
📁 Project Structure
Code
Web-Scrap-RAG/
├── app/                    # Main application directory
├── debug_output/           # Debug output files
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
🔧 Configuration
Environment Variables
Create a .env file in the root directory:

env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost/web_scrap_rag

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Vector DB
FAISS_INDEX_PATH=./data/faiss_index

# Application
DEBUG=True

## 🔌 API Endpoints
The API provides endpoints for:

User authentication (login, register)
Web scraping operations
Document upload and processing
RAG queries with LLM augmentation
Vector similarity search
For detailed API documentation, visit /docs after starting the server.

## 🤖 RAG Pipeline
The application implements a RAG pipeline that:

Scrapes web content or accepts uploaded documents
Processes content into chunks for embedding
Generates embeddings using sentence transformers
Stores embeddings in FAISS vector database
Retrieves relevant documents based on query similarity
Augments LLM prompts with retrieved context
Generates intelligent responses using Ollama

## 📚 Dependencies Overview
Category	Tools
Web Framework	FastAPI, Uvicorn
Databases	SQLAlchemy, PyMySQL, Alembic
Security	python-jose, passlib, bcrypt
Web Scraping	requests, httpx, aiohttp, BeautifulSoup4, lxml
Documents	pypdf, python-docx
ML/NLP	FAISS, NumPy, sentence-transformers, ollama
Utilities	python-dotenv, pydantic, tqdm, python-multipart

## 🛡️ Security
Passwords are hashed using bcrypt
JWT tokens for API authentication
Environment variables for sensitive data
SQL injection protection via SQLAlchemy ORM
CORS support for cross-origin requests

## 📝 License
This project is open source and available under the MIT License.

## 🤝 Contributing
Contributions are welcome! Please follow these steps:

## Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add some amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

## 🐛 Bug Reports
Found a bug? Please create an issue with:

## Description of the bug
Steps to reproduce
Expected behavior
Actual behavior
Python version and OS

## 📧 Contact
For questions or support, please contact the repository owner or open an issue.
