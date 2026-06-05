FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY deai/ deai/
COPY web/ web/

RUN pip install --no-cache-dir -e ".[web]"

EXPOSE 5000

CMD ["python", "web/app.py"]
