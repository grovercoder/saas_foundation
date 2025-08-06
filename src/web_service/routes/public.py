from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from src.web_service.app import get_web_service

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    web_service = get_web_service()
    return web_service.templates.TemplateResponse("public/home.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    web_service = get_web_service()
    return web_service.templates.TemplateResponse("public/login.html", {"request": request})

@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    web_service = get_web_service()
    return web_service.templates.TemplateResponse("public/logout.html", {"request": request})

@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    web_service = get_web_service()
    return web_service.templates.TemplateResponse("public/pricing.html", {"request": request})

@router.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    web_service = get_web_service()
    return web_service.templates.TemplateResponse("public/signup.html", {"request": request})

@router.get("/stop", response_class=PlainTextResponse)
async def stop_server():
    web_service = get_web_service()
    if web_service.mode == "dev" and web_service.server:
        web_service.server.should_exit = True
        return "Server shutdown initiated."
    return "Server not running or not controllable in this mode."
