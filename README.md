# AnonTex

**AnonTex** is a privacy-first experimental LLM proxy that anonymizes Personally Identifiable Information (PII) before forwarding requests to the OpenAI Completion API. It is designed to be compatible with the `/v1/chat/completions` endpoint, making it a drop-in proxy with minimal integration effort.

> ⚠️ **Note:** This is an **experimental** project. Use with caution in production environments.

---

## ✨ Features

- Acts as a transparent proxy for OpenAI's chat completion endpoint.
- Automatically anonymizes user input using PII detection.
- Compatible with OpenAI clients, such as the OpenAI Python SDK and LangChain.
- Redis-backed for entity management and fast caching.

---

## 📦 Installation

Install via pip:

```bash
pip install anontex
```

> ✅ **Note:** Redis is a required external dependency for caching and PII management.
Make sure you have Redis running locally or remotely.

---

## 🚀 Usage

Once installed and configured, AnonTex runs a proxy server compatible with OpenAI’s Chat Completion API.

### 🔁 Example with `curl`

```bash
curl --request POST \
  --url http://localhost:8000/v1/chat/completions \
  --header 'Authorization: Bearer YOUR-OPENAI-API-KEY' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello! My name is John Smith"
      }
    ]
  }'
```

### 🐍 Example with OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="YOUR-OPENAI-API-KEY"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "My email is john@example.com."}
    ]
)

print(response.choices[0].message.content)
```

### 🔗 Example with LangChain

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

chat = ChatOpenAI(
    openai_api_key="YOUR-OPENAI-API-KEY",
    openai_api_base="http://localhost:8000/v1"
)

messages = [HumanMessage(content="My phone number is 123-456-7890.")]
response = chat(messages)
print(response.content)
```

---

## ⚙️ Configuration

### Running Locally

Start the proxy via CLI:

```bash
anontex run
```

#### CLI Options

- `--host`: Server host (default: `0.0.0.0`)
- `--port`: Server port (default: `8000`)
- `--config`: Path to configuration file
- `--log-level`: Logging level (default: `info`)

#### Config File

You can pass settings via a YAML config file:

```yaml
# default
nlp_engine_name: spacy
models:
  -
    lang_code: en
    model_name: en_core_web_lg

ner_model_configuration:
  model_to_presidio_entity_mapping:
    PER: PERSON
    PERSON: PERSON
    NORP: NRP
    FAC: LOCATION
    LOC: LOCATION
    GPE: LOCATION
    LOCATION: LOCATION
    ORG: ORGANIZATION
    ORGANIZATION: ORGANIZATION
    DATE: DATE_TIME
    TIME: DATE_TIME

  low_confidence_score_multiplier: 0.4
  low_score_entity_names:
  -
  labels_to_ignore:
  - ORGANIZATION # Has many false positives
  - CARDINAL
  - EVENT
  - LANGUAGE
  - LAW
  - MONEY
  - ORDINAL
  - PERCENT
  - PRODUCT
  - QUANTITY
  - WORK_OF_ART
```

#### .env File

Additional configurations can be done environment variables via `.env`:

```
# Target server (OpenAI chat completion compatible API endpoint ex: https://api.openai.com)
TARGET=
# Redis connection URL for caching
REDIS_URL=
# Time-to-live duration for cached entities
ENTITY_TTL=
# Default path to analyzer configuration file
DEFAULT_CONFIG_PATH=
# Language to detect by analyzer
LANGUAGE=
```
If `.env` not set default values will be used.

---

## 🐳 Docker Deployment

You can deploy AnonTex with Docker using Docker Compose:

### Run:

```bash
docker compose up -d
```

---

## 🚧 Limitations & Future Improvements

- ❌ No support for **multi-turn PII tracking** (PII memory is per-message only).
- 🔗 Only supports **OpenAI** API compatible endpoints.
- 🌐 Limited **language support** (primarily English).
- 📈 Planned support for:
  - Multi-turn entity memory
  - Custom anonymization rules
  - Model switching and vendor abstraction
  - Analytics & tracing integration

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## 📄 License

This project is licensed under the Apache 2.0 License.

---
