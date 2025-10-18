FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY main.py .
COPY data/law_aliases.json ./data/law_aliases.json
COPY data/law_alias_to_id.json ./data/law_alias_to_id.json

EXPOSE 8978
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8978"]
