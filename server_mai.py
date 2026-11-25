from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.exceptions import StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

app = FastAPI()

class LoginRequest(BaseModel):
    login: str
    pin: str

# Раздача статики (CSS, JS, картинки)
app.mount("/css", StaticFiles(directory="front/css"), name="css")
app.mount("/js", StaticFiles(directory="front/js"), name="js")
app.mount("/img", StaticFiles(directory="front/img"), name="img")

@app.exception_handler(500)
async def internal_exception_handler(request: Request, exc: Exception):
    return FileResponse("front/500.html", status_code=500)

# Отдача HTML-страниц
@app.get("/")
def index_page():
    return FileResponse("front/index.html")

@app.get("/app")
async def app_page(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/app/login", status_code=302)
    else:
        return FileResponse("front/app.html")

@app.get("/terms")
def index_page():
    return FileResponse("front/terms.html")

@app.get("/app/login")
def login_page():
    return FileResponse("front/login.html")

# api

@app.post("/api/login")
def login(data: LoginRequest):
    return JSONResponse({'status': 'ok', 'code': 'transfer.self'})

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return FileResponse("front/404.html", status_code=404)
    return FileResponse("front/500.html", status_code=exc.status_code)

# Перехватываем любые падения Python-кода (500 Internal Server Error)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return FileResponse("front/500.html", status_code=500)

# 3. В САМОМ КОНЦЕ монтируем папку со статикой
app.mount("/", StaticFiles(directory="front", html=True), name="front")