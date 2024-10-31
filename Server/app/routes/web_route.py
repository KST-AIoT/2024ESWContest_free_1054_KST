from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/example")
async def example_page(request: Request):
    return templates.TemplateResponse("example.html", {"request": request})
