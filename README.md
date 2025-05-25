

```markdown
# LLM Tracing with Arize Phoenix & OpenTelemetry

This repository demonstrates how to trace OpenAI API calls using [OpenTelemetry](https://opentelemetry.io/) and visualize them in [Arize Phoenix](https://docs.arize.com/phoenix/), an observability tool for LLM applications.

## 🔍 What You'll Learn

- How to instrument an LLM app using OpenTelemetry
- How to send spans to Phoenix for trace collection and visualization
- How to use auto-instrumentation for OpenAI API calls
- End-to-end flow: from running the app to visualizing traces

---

## 📁 Project Structure

 main.py                 # Main application to generate a haiku using OpenAI
docker-compose.yml      # Phoenix + PostgreSQL setup
.env                    # Contains OpenAI API key and Phoenix endpoint
requirements.txt / pyproject.toml
README.md               # This file

###
````

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/llm-tracing-phoenix.git
cd llm-tracing-phoenix
````

### 2. Install Dependencies

```bash
poetry install  # or pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file with:

```
OPENAI_API_KEY=your-openai-key
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
```

### 4. Start Phoenix & DB (PostgreSQL)

```bash
docker-compose up -d
```

* Phoenix UI: [http://localhost:6006](http://localhost:6006)

---

### 5. Run the App

```bash
python main.py
```

This generates a haiku using OpenAI and sends traces to Phoenix.

---

## 🔄 Tracing Flow (How It Works)

### 1. Instrumentation & Tracer Setup

`main.py` initializes tracing:

```python
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=phoenix_endpoint))
tracer_provider = register(
    project_name="sample-llm-app",
    endpoint=phoenix_endpoint,
    auto_instrument=True,
    span_processor=span_processor
)
```

* **Tracer Provider**: Registers OpenTelemetry with Phoenix.
* **BatchSpanProcessor**: Buffers and exports spans in batches.
* **OTLPSpanExporter**: Sends spans over HTTP to Phoenix.

---

### 2. ⚙️ Auto-Instrumentation of OpenAI

The call:

```python
client.chat.completions.create(...)
```

is automatically traced by `openinference-instrumentation-openai`, capturing:

* Span Name: `chat.completions.create`
* Attributes: `model`, `prompt`, `response`
* Trace Context: `trace_id`, `span_id`

---

### 3. 📤 Span Exporting

Spans are:

* Collected by `BatchSpanProcessor`
* Exported as OTLP protobuf via HTTP to:

  ```
  http://localhost:6006/v1/traces
  ```

---

### 4. 🐘 Trace Collection & Storage

Phoenix server (in Docker):

* Accepts incoming traces via HTTP OTLP
* Stores spans in PostgreSQL (`db` container)

---

### 5. 🖥️ Visualization in Phoenix

Visit: [http://localhost:6006](http://localhost:6006)

* Navigate to **Traces** tab
* Select `sample-llm-app` project
* View spans like `chat.completions.create` with full metadata

---

## 🐳 Docker Compose Breakdown

```yaml
services:
  phoenix:
    image: arizephoenix/phoenix:latest
    ports:
      - "6006:6006"
      - "4317:4317"
    environment:
      - PHOENIX_SQL_DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
    depends_on:
      - db

  db:
    image: postgres:latest
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=postgres
    ports:
      - "5432:5432"
    volumes:
      - database_data:/var/lib/postgresql/data

volumes:
  database_data:
```

---

## 📌 Key Libraries Used

* [`openinference-instrumentation-openai`](https://pypi.org/project/openinference-instrumentation-openai/)
* `opentelemetry-sdk`
* `opentelemetry-exporter-otlp`
* `phoenix-tracing`
* `python-dotenv`
* `openai`

---

## 🧪 Example Logs

```bash
INFO:__main__:Phoenix endpoint: http://localhost:6006/v1/traces
INFO:__main__:Configuring Phoenix tracer...
INFO:__main__:Phoenix tracer configured successfully with BatchSpanProcessor
INFO:__main__:Generating haiku...
INFO:__main__:Haiku generated successfully
```

---

## 📈 Troubleshooting

* **Trace Not Visible**: Wait 3–5 seconds due to batch delay.
* **Invalid Endpoint**: Ensure `http://localhost:6006/v1/traces` is correct.
* **No Spans?**: Check that `openinference-instrumentation-openai` is installed and auto-instrumentation is enabled.

---

## 💡 Learn More

* [Phoenix Docs](https://docs.arize.com/phoenix/)
* [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
* [OpenInference GitHub](https://github.com/Arize-ai/openinference)

---

## 🧑‍💻 Contributing

PRs are welcome! If you find issues or want to enhance this tracing example, feel free to fork and improve it.

---

## 📜 License

MIT

```

---

Let me know if you'd like this README tailored for `poetry`, `pip`, or another runtime setup like FastAPI or Streamlit integration.
```
