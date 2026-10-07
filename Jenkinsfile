pipeline {
    agent any
    options { timestamps(); disableConcurrentBuilds() }
    stages {
        stage('Install') {
            steps { sh 'python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"' }
        }
        stage('Lint') {
            steps { sh '.venv/bin/ruff check .' }
        }
        stage('Tests') {
            steps { sh '.venv/bin/pytest -q' }
        }
        stage('Build image') {
            steps { sh 'docker build -t zielona-polska:${BUILD_NUMBER} .' }
        }
        stage('Container smoke test') {
            steps {
                sh '''
                  set -eu
                  docker run -d --name zielona-polska-ci -p 18501:8501 zielona-polska:${BUILD_NUMBER}
                  trap 'docker logs zielona-polska-ci || true; docker rm -f zielona-polska-ci || true' EXIT
                  for attempt in $(seq 1 30); do
                    if docker exec zielona-polska-ci python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"; then exit 0; fi
                    sleep 2
                  done
                  exit 1
                '''
            }
        }
    }
    post { always { sh 'docker image rm zielona-polska:${BUILD_NUMBER} || true' } }
}
