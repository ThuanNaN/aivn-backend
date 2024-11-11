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

### Local MongoDB Replica Set

#### 1. Tools (Depends on respective roles)

- OrbStack: run Docker locally. [Download](https://orbstack.dev/download)
- MongoDB Compass: GUI for MongoDB. [Download](https://www.mongodb.com/try/download/compass)
- MongoDB CLI Database Tools: dump and restore data. [Download](https://www.mongodb.com/try/download/database-tools)

#### 2. Setup key

```bash
openssl rand -base64 756 > mongodb-keyfile
chmod 600 ./mongodb-keyfile
```

#### 3. Start Docker & MongoDB Replica Set setup

```bash
docker compose up -d

# Add key to the container
docker exec -it aivietnam-mongodb /bin/bash
chown mongodb:mongodb /data/configdb/mongodb-keyfile
```

```bash
docker exec -it aivietnam-mongodb mongosh --authenticationDatabase admin -u duongthuan1445 -p <passwd>
```

```js
rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "localhost:27017" }]});
```

- Connect to local MongoDB at: mongodb://localhost:27017 via MongoDB Compass to make sure it works as expected

#### 4. Dump data from the respective environment and restore it to local MongoDB

- Dump data

```bash
export DB_URL="..."
mongodump --uri=$DB_URL --out="aivietnam-$(date +%Y-%m-%d)"
```

- Restore

```bash
mongorestore --uri=mongodb://duongthuan1445:<passwd>@localhost:27017/ --authenticationDatabase admin --drop --nsInclude="aivietnam.*" <database>
```

- If backend is running in Docker, you can use the following command to restore data

```js
rs.reconfig({ _id: "rs0", members: [{ _id: 0, host: "aivietnam-mongodb:27017" }] });
```

```bash
docker compose restart
```
