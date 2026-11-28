from fastapi import FastAPI, Depends, Header, HTTPException
from contextlib import asynccontextmanager
from fastapi.exceptions import StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from typing import Optional

from server import auth, db, tokens, transactions, cmd_handle, luhn
from shared import comms, protocol, log, collibry, codes
from config import HOST, DB_PATH, PORT, API_VERSION

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect(DB_PATH)
    db.init()
    tokens_cleaned = tokens.cleanup()
    print(f'cleaned up {tokens_cleaned} tokens')

    yield
    
    db.close()

app = FastAPI(lifespan=lifespan)

class AuthRequest(BaseModel):
    login: str
    name: Optional[str] = None
    pin: str

# Раздача статики (CSS, JS, картинки)
app.mount("/css", StaticFiles(directory="front/css"), name="css")
app.mount("/js", StaticFiles(directory="front/js"), name="js")
app.mount("/img", StaticFiles(directory="front/img"), name="img")
app.mount("/icons", StaticFiles(directory="front/icons"), name="icons")

def authorize(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return None
    return tokens.resolve(token)


# Отдача HTML-страниц
@app.get("/")
def index_page():
    return FileResponse("front/index.html")

@app.get("/app")
async def app_page(user_uuid: Optional[str] = Depends(authorize)):
    if not user_uuid:
        return RedirectResponse(url="/app/login", status_code=302)
    return FileResponse("front/app.html")

@app.get("/terms")
def index_page():
    return FileResponse("front/terms.html")

@app.get("/app/login")
async def login_page(user_uuid: Optional[str] = Depends(authorize)):
    if user_uuid:
        return RedirectResponse(url="/app", status_code=302)
    return FileResponse("front/login.html")









# api

@app.post("/api/login")
def login(data: AuthRequest):
    result = auth.login(data.login, data.pin)
    result_data = result.get('data')
    token = None
    if result_data:
        token = result_data.pop("token", None) if isinstance(result, dict) else None
    
    resp = JSONResponse(result)
    if token:
        resp.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=False,       # Поставьте True, когда сайт будет работать по HTTPS
            samesite="lax",
            max_age=86400 * 7   # Кука будет жить 7 дней
        )
    return resp

@app.post("/api/register")
def register(data: AuthRequest):
    result = auth.register(data.login, data.name, data.pin)
    result_data = result.get('data')
    token = None
    if result_data:
        token = result_data.pop("token", None) if isinstance(result, dict) else None

    resp = JSONResponse(result)
    if token:
        resp.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=False,       # Поставьте True, когда сайт будет работать по HTTPS
            samesite="lax",
            max_age=86400 * 7   # Кука будет жить 7 дней
        )
    return resp

@app.post("/api/logout")
def logout():
    resp = JSONResponse({"status": "ok"})
    resp.delete_cookie(key="session_token")
    return resp




@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return FileResponse("front/404.html", status_code=404)
    return FileResponse("front/500.html", status_code=exc.status_code)

# Перехватываем любые падения Python-кода (500 Internal Server Error)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return FileResponse("front/500.html", status_code=500)