FROM python as poetry
ENV PYTHONUNBUFFERED=true
WORKDIR /app
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -
COPY . ./app
COPY pyproject.toml ./pyproject.toml
RUN poetry install --no-interaction --no-ansi -v
FROM python as runtime
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=poetry /app /app
CMD ["python3", "-u", "/app/app/owalert/main.py"]