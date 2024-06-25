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
fastapi dev --reload --host 0.0.0.0 --port 8000
```

Deploy the FastAPI service

```bash
fastapi run --reload --host 0.0.0.0 --port 8000
```
