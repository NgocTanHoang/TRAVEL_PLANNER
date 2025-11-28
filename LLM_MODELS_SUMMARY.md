# Tóm tắt các Model LLM đang sử dụng trong Project

## 1. OpenAI Models

### 1.1. Chat Models (GPT)
- **Model mặc định**: `gpt-4o-mini`
- **Cấu hình**: Được set qua biến môi trường `MODEL` (mặc định: `gpt-4o-mini`)
- **Nơi sử dụng**:
  - **RAG Agent** (`agents/travel_agents/rag.py`):
    - Model: `gpt-4o-mini` (mặc định)
    - Temperature: `0.7`
    - Mục đích: Generate recommendations và enhance search results
  
  - **Travel Chatbot** (`ml/travel_chatbot.py`):
    - Model: `gpt-4o-mini` (mặc định, có thể override)
    - Temperature: `0.7` (có thể tùy chỉnh)
    - Provider: `openai`
    - Mục đích: Chatbot tư vấn du lịch với RAG
  
  - **Planning Tools** (`tools/planning_tools.py`):
    - Model: `gpt-4o-mini` (mặc định)
    - Temperature: `0.3` (thấp hơn để format text chính xác)
    - **Lưu ý**: Tắt mặc định (`PLANNING_USE_LLM=false`), chỉ dùng để format text cuối cùng
    - Mục đích: Format và combine thông tin thành văn bản mượt mà

### 1.2. Embedding Models
- **Model**: OpenAI Embeddings (theo comment trong code: `text-embedding-ada-002` hoặc tương đương)
- **Nơi sử dụng**: 
  - **Vector Database Agent** (`agents/travel_agents/vector_db.py`)
  - ChromaDB sử dụng OpenAI Embeddings để tạo vector embeddings cho semantic search
  - Mục đích: Tạo embeddings cho places data để semantic search

## 2. LLaMA Models (Local)

### 2.1. LlamaCpp
- **Provider**: `llama` (qua `langchain_community.llms.LlamaCpp`)
- **Cấu hình**: 
  - Model path: Được set qua biến môi trường `LLAMA_MODEL_PATH`
  - Temperature: `0.7` (có thể tùy chỉnh)
  - Context window: `2048` tokens
- **Nơi sử dụng**:
  - **Travel Chatbot** (`ml/travel_chatbot.py`)
  - **Lưu ý**: Chỉ sử dụng khi `llm_provider='llama'` và có `LLAMA_MODEL_PATH`
  - Mục đích: Alternative local LLM option (không cần API key)

## 3. Google Gemini (Optional)

### 3.1. Gemini Models
- **Package**: `google-generativeai>=0.3.0` (trong requirements.txt)
- **Trạng thái**: Đã có package nhưng chưa thấy được sử dụng trong code
- **Lưu ý**: Có comment trong requirements.txt về conflict với langchain-core 1.x

## 4. Cấu hình Environment Variables

### 4.1. OpenAI
```bash
OPENAI_API_KEY=<your-api-key>  # Bắt buộc để sử dụng OpenAI models
MODEL=gpt-4o-mini              # Model name (mặc định: gpt-4o-mini)
```

### 4.2. LLaMA (Local)
```bash
LLAMA_MODEL_PATH=<path-to-model-file>  # Đường dẫn đến model file
```

### 4.3. Planning Tools
```bash
PLANNING_USE_LLM=false  # Tắt mặc định, set 'true' để bật
```

## 5. LangSmith (Monitoring & Tracing)

- **Package**: `langsmith>=0.3.0,<1.0.0`
- **Cấu hình**: 
  - File: `config/langsmith_config.py`
  - Environment variables:
    - `LANGCHAIN_API_KEY`: API key cho LangSmith
    - `LANGCHAIN_TRACING_V2`: Enable/disable tracing (mặc định: `true`)
    - `LANGCHAIN_PROJECT`: Project name (mặc định: `vi-vu-travel-planner`)
    - `LANGCHAIN_ENDPOINT`: Endpoint URL (mặc định: `https://api.smith.langchain.com`)
- **Mục đích**: Monitor và trace LLM calls, debug agent workflows

## 6. Tổng kết

### Models đang được sử dụng tích cực:
1. **OpenAI GPT-4o-mini** (Chat model) - Chính
   - RAG Agent
   - Travel Chatbot
   - Planning Tools (optional)

2. **OpenAI Embeddings** (Embedding model) - Chính
   - Vector Database Agent (ChromaDB)

### Models có sẵn nhưng chưa sử dụng:
1. **LLaMA (LlamaCpp)** - Local alternative
2. **Google Gemini** - Package đã có nhưng chưa tích hợp

### Monitoring:
- **LangSmith** - Đang được cấu hình và sử dụng để trace LLM calls

## 7. Ghi chú

- Tất cả các model đều được wrap qua LangChain để dễ dàng switch giữa các providers
- Model mặc định là `gpt-4o-mini` (cost-effective option)
- Có thể thay đổi model bằng cách set biến môi trường `MODEL`
- Planning Tools tắt LLM mặc định để tiết kiệm chi phí API

