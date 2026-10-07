FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY app.py ./app.py
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 appuser \
    && mkdir -p /data && chown appuser:appuser /data
ENV DATA_PATH=/data/poland_energy.csv
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2)" || exit 1
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.headless=true"]
