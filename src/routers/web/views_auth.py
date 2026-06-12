import os
from fastapi import APIRouter, Request, Depends, Form, responses, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services import auth_service
from src.repositories.user_repo import UserRepository
from src.models.user import User

router = APIRouter()
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates_dir = os.path.join(current_dir, "templates")
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory=templates_dir)

@router.get("/login", response_class=responses.HTMLResponse)
async def get_login_page(request: Request):
    """Hiển thị trang đăng nhập cho người dùng."""
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"request": request})

@router.post("/login")
async def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Xử lý thông tin đăng nhập và lưu token vào cookie."""
    user = await auth_service.authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"request": request, "error": "Email hoặc mật khẩu không đúng"})
    token = auth_service.create_access_token({"sub": user.email})
    response = responses.RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@router.get("/register", response_class=responses.HTMLResponse)
async def get_register_page(request: Request):
    """Hiển thị trang đăng ký tài khoản mới."""
    return templates.TemplateResponse(request=request, name="auth/register.html", context={"request": request})

@router.post("/register")
async def post_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Đăng ký tài khoản người dùng mới và mã hóa mật khẩu bảo mật."""
    repo = UserRepository(db)
    existing_user = await repo.get_by_email(email)
    if existing_user:
        return templates.TemplateResponse(request=request, name="auth/register.html", context={"request": request, "error": "Email này đã được sử dụng"})
    hashed = auth_service.get_password_hash(password)
    user = User(email=email, hashed_password=hashed, full_name=full_name, is_admin=False)
    await repo.create(user)
    return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
async def logout():
    """Đăng xuất người dùng bằng cách xóa cookie chứa token xác thực."""
    response = responses.RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
