  - type: worker
    name: seamlessdocs-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python worker.py
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: seamlessdocs-redis
    disk:
      name: shared
      mountPath: /data
