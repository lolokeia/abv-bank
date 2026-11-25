#!/opt/sys-agent/.venv/bin/python3
import os
import time
import sqlite3
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager, closing
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
import psutil
import docker
from dotenv import load_dotenv
import subprocess
import json

load_dotenv("/opt/sys-agent/.env")
API_TOKEN = os.getenv("API_TOKEN", "abv_secret_token")
DB_PATH = Path("/opt/sys-agent/monitor.db")
INTERVAL_SEC = 60



api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# В начале файла (после импортов) создаем один клиент Docker и кэш
try:
    DOCKER_CLIENT = docker.from_env()
except Exception:
    DOCKER_CLIENT = None

CACHE = {
    "system": None,
    "docker": {"available": False, "containers": []},
}

def collect_system_snapshot():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=None),  # неблокирующий замер с прошлого вызова!
            "cores": psutil.cpu_count(),
            "load_avg": os.getloadavg(),
        },
        "ram": {
            "total_gb": round(vm.total / (1024**3), 2),
            "used_gb": round(vm.used / (1024**3), 2),
            "percent": vm.percent,
        },
        "disk_root": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent,
        },
        "network": {
            "sent_mb": round(net.bytes_sent / (1024**2), 2),
            "recv_mb": round(net.bytes_recv / (1024**2), 2),
        },
        "temp_max_c": get_max_temp(),
    }


def verify_token(api_key: str = Security(api_key_header)):
    if api_key != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            minute_ts INTEGER PRIMARY KEY,
            cpu_percent REAL,
            ram_percent REAL,
            temp_max REAL
        )
    """)
    return conn

def get_max_temp():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        all_vals = [entry.current for entries in temps.values() for entry in entries if entry.current]
        return round(max(all_vals), 1) if all_vals else None
    except Exception:
        return None

async def collector_loop():
    last_db_min = 0
    psutil.cpu_percent(interval=None)  # первый прогревочный замер

    while True:
        try:
            # 1. Раз в 5 секунд обновляем лёгкий кэш в памяти для /api/system
            snap = await asyncio.to_thread(collect_system_snapshot)
            CACHE["system"] = snap

            # 2. Раз в 60 секунд пишем heartbeat в SQLite (для графиков и Uptime Ratio)
            now_min = (int(time.time()) // INTERVAL_SEC) * INTERVAL_SEC
            if now_min != last_db_min:
                last_db_min = now_min
                with closing(get_db()) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO metrics "
                        "(minute_ts, cpu_percent, ram_percent, temp_max) "
                        "VALUES (?, ?, ?, ?)",
                        (now_min, snap["cpu"]["percent"], snap["ram"]["percent"], snap["temp_max_c"]),
                    )
                    conn.commit()
        except Exception as e:
            print(f"[Collector Error]: {e}", flush=True)

        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(collector_loop())
    yield
    task.cancel()

app = FastAPI(title="Linux System Monitor API", lifespan=lifespan)

@app.get("/api/health")
def api_health():
    return {"status": "ok"}

@app.get("/api/uptime", dependencies=[Depends(verify_token)])
def api_uptime(days: int = 30):
    now_min = (int(time.time()) // INTERVAL_SEC) * INTERVAL_SEC
    with open("/proc/uptime") as f:
        os_uptime_sec = float(f.readline().split().pop(0))

    window_start = now_min - days * 86400

    with closing(get_db()) as conn:
        (first_ts,) = conn.execute("SELECT MIN(minute_ts) FROM metrics").fetchone()
        if not first_ts:
            return {
                "uptime_hours": round(os_uptime_sec / 3600, 2),
                "uptime_days": round(os_uptime_sec / 86400, 2),
                "ratios": {},
                "daily": [],
            }

        def calc_ratio(window_days):
            start = first_ts if window_days is None else max(first_ts, now_min - window_days * 86400)
            (alive,) = conn.execute("SELECT COUNT(*) FROM metrics WHERE minute_ts >= ?", (start,)).fetchone()
            total = max(1, ((now_min - start) // INTERVAL_SEC) + 1)
            return min(100.0, round((alive / total) * 100, 2))

        daily_rows = conn.execute("""
            SELECT date(minute_ts, 'unixepoch', 'localtime') AS day_str,
                   MIN(minute_ts) AS min_ts,
                   COUNT(*) AS mins
            FROM metrics
            WHERE minute_ts >= ?
            GROUP BY day_str ORDER BY day_str ASC
        """, (window_start,)).fetchall()

        ratios = {
            "24h": calc_ratio(1),
            "7d": calc_ratio(7),
            "30d": calc_ratio(30),
            "all_time": calc_ratio(None),
        }

    daily_stats = []
    for day_str, min_ts, mins in daily_rows:
        # Вычисляем начало и конец этого локального дня в timestamp
        t_struct = time.strptime(day_str, "%Y-%m-%d")
        day_start_ts = int(time.mktime(t_struct))
        day_end_ts = day_start_ts + 86340

        day_start = max(first_ts, day_start_ts, window_start)
        day_end = min(now_min, day_end_ts)
        if day_start > day_end:
            continue
        expected_mins = max(1, ((day_end - day_start) // INTERVAL_SEC) + 1)
        pct = min(100.0, round((mins / expected_mins) * 100, 1))
        daily_stats.append({
            "day_ts": day_start_ts,
            "date": day_str,
            "uptime_pct": pct,
        })


    return {
        "uptime_hours": round(os_uptime_sec / 3600, 2),
        "uptime_days": round(os_uptime_sec / 86400, 2),
        "ratios": ratios,
        "daily": daily_stats,
    }

@app.get("/api/system", dependencies=[Depends(verify_token)])
def api_system():
    return CACHE["system"] or collect_system_snapshot()


@app.get("/api/docker", dependencies=[Depends(verify_token)])
def api_docker():
    try:
        client = docker.from_env()
        containers = [
            {
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown",
            }
            for c in client.containers.list(all=True)
        ]
        return {"available": True, "count": len(containers), "containers": containers}
    except Exception as e:
        return {"available": False, "error": str(e), "containers": []}

SSH_EVENTS = []

@app.post("/api/ssh/push", dependencies=[Depends(verify_token)])
def push_ssh_event(payload: dict):
    SSH_EVENTS.append({"id": str(time.time()), "message": payload.get("msg", "")})
    del SSH_EVENTS[:-20]  # храним только последние 20
    return {"ok": True}

@app.get("/api/ssh", dependencies=[Depends(verify_token)])
def get_ssh_logins():
    return {"logins": SSH_EVENTS}


@app.get("/api/history", dependencies=[Depends(verify_token)])
def api_history(hours: int = 24):
    since = int(time.time()) - hours * 3600
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT minute_ts, cpu_percent, ram_percent, temp_max "
            "FROM metrics WHERE minute_ts >= ? ORDER BY minute_ts ASC",
            (since,),
        ).fetchall()
    return [{"ts": ts, "cpu": cpu, "ram": ram, "temp": temp} for ts, cpu, ram, temp in rows]