FROM python:3.9.17-slim-bullseye

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Poetry
RUN apt-get update && apt-get install gcc g++ curl build-essential postgresql-server-dev-all -y
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="${PATH}:/root/.local/bin"

# Copy the pyproject.toml and poetry.lock files
COPY poetry.lock pyproject.toml ./

# Copy the rest of the application codes
COPY ./ ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Create settings.toml
RUN ailingbot init --silence --overwrite