FROM python:3.12-slim
RUN groupadd -r groupflask && useradd -r -g groupflask userflask

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

WORKDIR /app
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .

USER userflask

ENTRYPOINT ["sh","entrypoint.sh"]
