FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY infra/docker/runtime-requirements.txt /tmp/runtime-requirements.txt
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0 \
    && pip install -r /tmp/runtime-requirements.txt
RUN groupadd -g 10001 app && useradd -m -u 10001 -g app app
COPY --chown=app:app backend /app/backend
COPY --chown=app:app scripts /app/scripts
COPY --chown=app:app alembic.ini pyproject.toml /app/
RUN mkdir -p /app/docs/validation /app/artifacts /app/data/knowledge /app/experiments/results /app/experiments/figures \
    && chown -R app:app /app
USER app
EXPOSE 8000
ENTRYPOINT ["python", "scripts/container_entrypoint.py"]
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
