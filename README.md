# AnonTex

**AnonTex** is a privacy-first experimental LLM proxy that anonymizes Personally Identifiable Information (PII) before forwarding requests to the OpenAI Completion API. It is designed to be compatible with the `/v1/chat/completions` endpoint, making it a drop-in proxy with minimal integration effort.

> ⚠️ **Note:** This is an **experimental** project. Use with caution in production environments.

---

## ✨ Features

- Acts as a transparent proxy for OpenAI's chat completion endpoint.
- Automatically anonymizes user input using PII detection.
- Redis-backed for entity management and fast caching.

---

## 📦 Installation

Install via pip:

```bash
pip install anontex
```

> ✅ **Note:** Redis is a required external dependency for caching and PII management.
Make sure you have Redis running locally or remotely.

##### for additional dependencies with transformers:
```bash
pip install anontex[transformers]
```
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
- `--config`: Path to configuration file (default: `spacy` engine configs)
- `--log-level`: Logging level (default: `info`)

#### Config File (Optional)
You can pass settings via a YAML config file. Read the following documentation to customize the [config file](https://github.com/ChamathKB/AnonTex/wiki/Config-File).
> This project uses the `presidio-analyzer` Python package as an entity detector. You can use the default config file without specifying a custom file or point to a `presidio-analyzer` supported [config file](https://microsoft.github.io/presidio/analyzer/customizing_nlp_models/#Configure-Presidio-to-use-the-new-model).

#### .env File (Optional)

Additional configurations can be done via environment variables in a `.env` file.
If `.env` is not set, default values will be used. Read the following documentation to customize the [.env file](https://github.com/ChamathKB/AnonTex/wiki/Configuring-.env-File).

---

## 🐳 Docker Deployment

You can deploy AnonTex with Docker using Docker Compose.
### Clone repo:
```bash
git clone https://github.com/ChamathKB/AnonTex
```

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
