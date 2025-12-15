# Huawei Cloud AI Health Assistant

A cloud-native medical diagnostic assistant built on Huawei Cloud infrastructure, featuring Milvus GraphRAG and Agentic RAG architectures.

## 🏗️ Architecture Overview

This application follows a cloud-based microservices architecture deployed on Huawei Cloud:

```
┌─────────────────────────────────────────────────────────────┐
│                    User (Doctors/Students)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ELB (Elastic Load Balancer)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Application Server (ECS) Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Input Processing (Speech-to-Text / Pre-processing) │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agentic Orchestrator (Task Planner)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Context Integration                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Intelligence Layer (ModelArts)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DeepSeek v3.1 Model                                 │  │
│  │  (Huawei ModelArts)                                 │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Ascend Chips (AI Acceleration)              │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│      Data & Memory Layer (Access Layer)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Milvus (Vector & Graph DB)                         │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  OBS Object Storage Service                  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OBS Object Storage Service (External APIs)         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### Core Capabilities
- **Medical Diagnostic Assistance**: AI-powered medical diagnosis support for doctors
- **Multi-layered RAG Architecture**: Combines vector search and graph-based retrieval
- **Agentic Reasoning**: Intelligent task planning and multi-step reasoning
- **GraphRAG**: Knowledge graph traversal for enhanced context understanding
- **Cloud-Native**: Built for Huawei Cloud infrastructure

### Technical Features
- **Input Processing**: Speech-to-text conversion and text preprocessing
- **Agentic Orchestrator**: Task planning and execution coordination
- **Context Integration**: Unified context from vector and graph databases
- **Milvus Integration**: Vector and graph database for medical knowledge
- **OBS Storage**: Object storage for large medical documents

## 📁 Project Structure

```
huaweict/
├── app.py                      # Streamlit UI application
├── rag_service.py              # Main RAG service orchestrator
├── config.py                   # Configuration management
├── input_processing.py         # Input preprocessing module
├── agentic_orchestrator.py     # Agentic RAG task planner
├── context_integration.py      # Milvus & GraphRAG integration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in repo)
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Huawei Cloud account with access to:
  - ECS (Elastic Cloud Server)
  - ModelArts
  - Milvus
  - OBS (Object Storage Service)
  - ELB (Elastic Load Balancer)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd huaweict
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your credentials:
   ```env
   # API Keys
   GOOGLE_API_KEY=your_google_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   
   # Milvus Configuration
   MILVUS_HOST=your_milvus_host
   MILVUS_PORT=19530
   MILVUS_USER=your_milvus_user
   MILVUS_PASSWORD=your_milvus_password
   MILVUS_COLLECTION_NAME=medical_knowledge_base
   
   # OBS Configuration
   OBS_ACCESS_KEY=your_obs_access_key
   OBS_SECRET_KEY=your_obs_secret_key
   OBS_ENDPOINT=your_obs_endpoint
   OBS_BUCKET_NAME=your_bucket_name
   
   # ModelArts Configuration
   MODELARTS_ENDPOINT=your_modelarts_endpoint
   MODELARTS_PROJECT_ID=your_project_id
   MODELARTS_MODEL_NAME=deepseek-v3.1
   
   # RAG Configuration
   RETRIEVAL_TOP_K=5
   GRAPH_RAG_ENABLED=true
   AGENTIC_RAG_ENABLED=true
   ```

5. **Initialize Milvus Collection**
   ```python
   # Run initialization script (to be created)
   python scripts/init_milvus.py
   ```

## 🚀 Running the Application

### Local Development
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Cloud Deployment

#### Deploy to Huawei Cloud ECS

1. **Prepare deployment package**
   ```bash
   # Create deployment package
   tar -czf deployment.tar.gz \
       app.py rag_service.py config.py \
       input_processing.py agentic_orchestrator.py \
       context_integration.py requirements.txt
   ```

2. **Upload to ECS**
   ```bash
   scp deployment.tar.gz user@your-ecs-ip:/opt/app/
   ```

3. **SSH into ECS and setup**
   ```bash
   ssh user@your-ecs-ip
   cd /opt/app
   tar -xzf deployment.tar.gz
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure ELB**
   - Create ELB instance in Huawei Cloud Console
   - Add ECS instance as backend server
   - Configure health checks
   - Set up SSL certificate (optional)

5. **Run with Streamlit**
   ```bash
   streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   ```

## 🔧 Configuration

### Milvus Setup

1. **Create Collection**
   ```python
   from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
   
   connections.connect(host="your_milvus_host", port="19530")
   
   fields = [
       FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
       FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
       FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
       FieldSchema(name="metadata", dtype=DataType.JSON),
       FieldSchema(name="entity_id", dtype=DataType.VARCHAR, max_length=255)
   ]
   
   schema = CollectionSchema(fields, "Medical knowledge base")
   collection = Collection("medical_knowledge_base", schema)
   ```

2. **Create Index**
   ```python
   index_params = {
       "metric_type": "L2",
       "index_type": "IVF_FLAT",
       "params": {"nlist": 1024}
   }
   collection.create_index("embedding", index_params)
   ```

### ModelArts Integration

To use DeepSeek v3.1 model from Huawei ModelArts:

1. Deploy model in ModelArts
2. Get endpoint URL
3. Update `MODELARTS_ENDPOINT` in `.env`
4. Modify `rag_service.py` to use ModelArts API instead of Google Gemini

## 📊 Architecture Components

### 1. Input Processing Layer
- **Purpose**: Preprocess user input, extract medical context
- **Features**:
  - Text cleaning and normalization
  - Medical keyword extraction
  - Entity recognition
  - Input type classification

### 2. Agentic Orchestrator
- **Purpose**: Plan and coordinate RAG tasks
- **Features**:
  - Task type determination
  - Execution plan creation
  - Multi-step reasoning
  - Iterative refinement

### 3. Context Integration
- **Purpose**: Retrieve and integrate context from multiple sources
- **Features**:
  - Vector similarity search (Milvus)
  - Graph traversal (GraphRAG)
  - Context merging and ranking

### 4. Intelligence Layer
- **Purpose**: Generate responses using LLM
- **Models**:
  - Google Gemini (default)
  - DeepSeek v3.1 via ModelArts (configurable)
  - Accelerated with Ascend chips

### 5. Data & Memory Layer
- **Milvus**: Vector and graph database
- **OBS**: Object storage for large documents

## 🔍 Usage Examples

### Basic Query
```
User: "Patient has severe headache and fever for 3 days"
```

### Complex Query with GraphRAG
```
User: "What is the relationship between hypertension and diabetes?"
```

### Agentic Multi-step Reasoning
```
User: "Why might a patient with chest pain also experience shortness of breath?"
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Test Milvus connection
python scripts/test_milvus.py
```

## 📝 API Documentation

### RAG Service API

```python
from rag_service import RAGService

service = RAGService()
result = service.process_query("Patient symptoms: headache, fever")

print(result["response"])
print(result["sources"])
print(result["execution_trace"])
```

## 🔒 Security Considerations

- API keys stored in `.env` (not committed to repo)
- HTTPS for ELB communication
- VPC isolation for cloud resources
- Access control for Milvus and OBS
- Input sanitization in preprocessing

## 📈 Performance Optimization

- **Caching**: RAG service cached with `@st.cache_resource`
- **Batch Processing**: Multiple queries processed in parallel
- **Indexing**: Milvus indexes optimized for medical queries
- **Ascend Acceleration**: ModelArts uses Ascend chips for faster inference

## 🐛 Troubleshooting

### Milvus Connection Issues
- Check `MILVUS_HOST` and `MILVUS_PORT` in `.env`
- Verify network connectivity from ECS to Milvus
- Check Milvus service status

### ModelArts Integration Issues
- Verify `MODELARTS_ENDPOINT` is correct
- Check API credentials
- Ensure model is deployed and running

### OBS Access Issues
- Verify `OBS_ACCESS_KEY` and `OBS_SECRET_KEY`
- Check bucket permissions
- Verify endpoint URL

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

[Specify your license here]

## 👥 Authors

- Huawei ICT Spark Infinity Team

## 🙏 Acknowledgments

- Huawei Cloud Platform
- Milvus Community
- LangChain Framework
- Streamlit Team

## 📞 Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Email: [your-email]

---

**Note**: This application is designed for medical professionals as a diagnostic support tool. It should not replace professional medical judgment.
