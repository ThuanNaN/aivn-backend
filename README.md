# AIVN Deep Learning Codeless Project

## Getting Started

### Python env

Conda venv

```bash
conda create -n codeless python=3.11 --y
conda activate codeless
pip3 install -r requirements.txt
```

Dev the FastAPI service

```bash
# for dev
fastapi dev --reload --host 0.0.0.0 --port 8000

# for test production
fastapi run --reload --host 0.0.0.0 --port 8000
```

Deploy the FastAPI service

```bash
# for deploy uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 
```

```bash
# for deploy gunicorn with uvicorn worker
gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
