# AI Guardian - Secure AI Conversation Platform

![AI Guardian](https://img.shields.io/badge/AI%20Guardian-Secure%20Conversations-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15.4.6-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112.1-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

## 🛡️ Overview

AI Guardian is a privacy-first conversational AI platform that automatically detects and masks sensitive information (PII) while providing intelligent document-based question answering through Retrieval-Augmented Generation (RAG). The platform ensures secure conversations by protecting personal data while maintaining the quality of AI interactions.

## ✨ Key Features

### 🔒 Privacy & Security
- **Automatic PII Detection**: Real-time detection of sensitive information using Presidio
- **Data Masking**: Intelligent pseudonymization of personal data
- **Secure File Upload**: Protected file storage with MinIO
- **Session Management**: Secure user authentication and session handling

### 🤖 AI Capabilities
- **RAG-Powered Q&A**: Document-based question answering with Weaviate vector database
- **Multi-LLM Support**: Integration with Azure OpenAI and Google Gemini
- **File Processing**: Extract text from PDF, DOCX, images, and other formats
- **Smart Agent System**: Intelligent routing between conversation and RAG agents

### 📁 File Management
- **Multiple Format Support**: PDF, DOCX, TXT, CSV, Excel, images (PNG, JPG, JPEG)
- **Document Ingestion**: Automatic processing and vectorization of uploaded documents
- **Text Extraction**: Advanced OCR and document parsing using SmolDocling

### 💬 Chat Features
- **Real-time Streaming**: Live response streaming with WebSocket support
- **Chat History**: Persistent conversation storage
- **File Attachments**: Upload and reference files in conversations
- **Multi-session Support**: Manage multiple chat sessions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Vector DB     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Weaviate)    │
│                 │    │                 │    │                 │
│ • React UI      │    │ • RAG Engine    │    │ • Document      │
│ • Chat Interface│    │ • PII Detection │    │   Embeddings    │
│ • File Upload   │    │ • Auth System   │    │ • Similarity    │
│ • Theming       │    │ • File Storage  │    │   Search        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Azure OpenAI API access
- Weaviate instance

### 1. Clone Repository
```bash
git clone https://github.com/your-repo/ai-guardian.git
cd ai-guardian
```

### 2. Environment Setup

#### Backend Configuration
Create `backend/.env`:
```env
# Azure OpenAI Configuration
deployment_name=your-deployment-name
model_name=gpt-4
azure_endpoint=https://your-resource.openai.azure.com/
openai_api_key=your-api-key
openai_api_version=2024-02-15-preview

# Embedding Model
embedding_deployment_name=text-embedding-ada-002
embedding_model_name=text-embedding-ada-002
embedding_azure_endpoint=https://your-resource.openai.azure.com/
embedding_openai_api_key=your-embedding-api-key
embedding_openai_api_version=2024-02-15-preview

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_guardian

# MinIO (File Storage)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret
```

#### Frontend Configuration
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Docker Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Manual Setup (Development)

#### Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt
# or with Poetry
poetry install

# Run database migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install
# or with pnpm
pnpm install

# Start development server
npm run dev
# or
pnpm dev
```

## 📚 API Documentation

Once the backend is running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /user/register` - User registration
- `POST /user/login` - User authentication
- `GET /user/profile` - Get user profile

#### Chat & Conversations
- `GET /api/sessions/{session_id}` - Get chat history
- `POST /api/sessions/{session_id}` - Send message to chat session

#### File Management
- `POST /file/upload` - Upload file
- `POST /file/extract` - Extract text from uploaded file

#### PII Protection
- `POST /mask/` - Mask sensitive content
- `POST /mask/unmask` - Unmask content
- `POST /mask/validate-sensitive` - Check for sensitive information

#### RAG Operations
- `POST /ai/rag/query` - Query document knowledge base
- `POST /ai/rag/update` - Update RAG content

## 🔧 Configuration

### RAG Configuration
The system uses multiple specialized LLM configurations for different tasks:

- **Agent Decision**: Temperature 0.1 (deterministic)
- **Conversation**: Temperature 0.7 (creative but factual)
- **RAG Response**: Temperature 0.3 (balanced)
- **Summarization**: Temperature 0.5 (moderate creativity)

### Vector Database
- **Embedding Model**: Azure OpenAI text-embedding-ada-002
- **Vector Dimension**: 1536
- **Distance Metric**: Cosine similarity
- **Chunk Size**: 512 tokens with 50 token overlap

### PII Detection
Supported entity types:
- Names, emails, phone numbers
- Credit card numbers, SSNs
- Addresses, dates of birth
- Custom entity patterns

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📁 Project Structure

```
ai-guardian/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/routers/       # API route handlers
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   └── agents/        # AI agent implementations
│   │   ├── database/          # Database configuration
│   │   └── config.py          # Application configuration
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Test suites
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/              # App router pages
│   │   ├── components/       # Reusable components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utility libraries
│   │   └── services/         # API services
│   └── package.json          # Node.js dependencies
└── docker-compose.yml        # Container orchestration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Presidio](https://github.com/microsoft/presidio) for PII detection
- [LangChain](https://github.com/langchain-ai/langchain) for LLM orchestration
- [Weaviate](https://weaviate.io/) for vector database
- [FastAPI](https://fastapi.tiangolo.com/) for backend framework
- [Next.js](https://nextjs.org/) for frontend framework

## 📞 Support

For support, email support@aiguardian.com or join our [Discord community](https://discord.gg/aiguardian).

---

**Made with ❤️ by the AI Guardian Team**
