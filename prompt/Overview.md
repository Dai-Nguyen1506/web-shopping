## 1. Tổng quan & Thiết kế Hệ thống

Dự án xây dựng một trang web bán hàng (E-commerce) hiệu năng cao, mã nguồn sạch, triển khai nhanh chóng bằng cách tích hợp **FastAPI** (xử lý bất đồng bộ), **Jinja2** (render giao diện phía server để tối ưu SEO và tốc độ tải trang), và **Redis** (lưu trữ phiên làm việc và bộ đệm dữ liệu). Toàn bộ hệ thống được đóng gói bằng **Docker Compose** để khởi chạy nhất quán trên mọi môi trường.

### Mục tiêu dự án

* **Tốc độ phản hồi cực hạn:** Thời gian phản hồi API và render trang < 50ms nhờ cơ chế async của FastAPI và bộ đệm Redis.
* **Cấu trúc sạch (Clean Architecture):** Tách biệt rõ ràng giữa Định tuyến (Routers), Logic nghiệp vụ (Services), và Thao tác dữ liệu (Repositories).
* **Sẵn sàng vận hành:** Đầy đủ các luồng nghiệp vụ thực tế từ quản lý giỏ hàng, đặt hàng cho đến thanh toán và tra cứu đơn hàng.

---

## 2. Công nghệ & Công cụ Sử dụng

| Thành phần | Công nghệ lựa chọn | Vai trò trong hệ thống |
| --- | --- | --- |
| **Backend Framework** | `FastAPI` (Python 3.11+) | Xử lý logic, định tuyến, render Jinja2 Templates, tự động sinh tài liệu OpenAPI. |
| **Database ORM** | `SQLAlchemy` (Async) + `Alembic` | Tương tác cơ sở dữ liệu bất đồng bộ, quản lý phiên bản migration schema. |
| **Database** | `PostgreSQL 15` | Lưu trữ dữ liệu quan hệ ổn định (Người dùng, Sản phẩm, Đơn hàng). |
| **Caching & Session** | `Redis` | Lưu trữ giỏ hàng tạm thời, session người dùng và cache danh mục sản phẩm. |
| **Frontend Integration** | `Jinja2` + `TailwindCSS` | Render giao diện phía server (SSR), tối ưu hóa SEO và tốc độ hiển thị giao diện. |
| **Containerization** | `Docker` & `Docker Compose` | Đóng gói toàn bộ ứng dụng và các dịch vụ phụ thuộc thành một thể thống nhất. |

---

## 3. Cấu trúc Thư mục Toàn diện (Clean Architecture)

Dự án tuân thủ cấu trúc phân tầng tách biệt để dễ dàng bảo trì, mở rộng và kiểm thử:

```text
ecommerce-fastapi/
├── .env.example              # File cấu hình mẫu cho các biến môi trường
├── Dockerfile                # Cấu hình build image cho ứng dụng FastAPI
├── docker-compose.yml        # Điều phối các container (App, DB, Redis)
├── requirements.txt          # Danh sách thư viện Python phụ thuộc
├── alembic.ini               # Cấu hình migration database
├── src/
│   ├── main.py               # Điểm khởi chạy ứng dụng (Khởi tạo FastAPI app)
│   ├── config.py             # Đọc và validate biến môi trường (Pydantic Settings)
│   ├── database.py           # Thiết lập kết nối Async PostgreSQL Session
│   ├── redis.py              # Thiết lập kết nối Redis client
│   │
│   ├── models/               # Định nghĩa các bảng Database (SQLAlchemy Models)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   │
│   ├── schemas/              # Pydantic Schemas (Validate dữ liệu đầu vào/đầu ra)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   │
│   ├── repositories/         # Tầng thao tác trực tiếp với Database (CRUD)
│   │   ├── base.py
│   │   ├── user_repo.py
│   │   ├── product_repo.py
│   │   └── order_repo.py
│   │
│   ├── services/             # Tầng xử lý Logic Nghiệp vụ (Business Logic)
│   │   ├── auth_service.py
│   │   ├── cart_service.py   # Xử lý giỏ hàng trên Redis
│   │   └── order_service.py  # Xử lý tính toán hóa đơn, trừ kho
│   │
│   ├── routers/              # Tầng định tuyến điều hướng (Giao diện & API)
│   │   ├── __init__.py
│   │   ├── web/              # Render Jinja2 Templates cho người dùng
│   │   │   ├── views_auth.py
│   │   │   ├── views_shop.py
│   │   │   └── views_cart.py
│   │   └── api/              # API endpoints phục vụ xử lý ngầm (AJAX/Fetch)
│   │       ├── api_cart.py
│   │       └── api_order.py
│   │
│   ├── static/               # File tĩnh (CSS, JS, Images)
│   │   ├── css/              # Tailwind sản phẩm
│   │   └── js/               # Xử lý AJAX thêm vào giỏ hàng, thanh toán
│   │
│   └── templates/            # Giao diện Jinja2 HTML
│       ├── base.html         # Giao diện khung (Header, Footer, Navbar)
│       ├── shop/
│       │   ├── index.html    # Trang chủ danh sách sản phẩm
│       │   └── detail.html   # Trang chi tiết sản phẩm
│       ├── cart/
│       │   └── index.html    # Trang chi tiết giỏ hàng
│       └── checkout/
│           ├── index.html    # Trang điền thông tin đặt hàng
│           └── success.html  # Trang thông báo đặt hàng thành công
└── alembic/                  # Thư mục chứa các file tự động sinh của Alembic

```

---

## 4. Chi tiết Các Chức năng Hệ thống

Để cấu thành một website bán hàng thực thụ, các chức năng được thiết kế khép kín và phân bổ logic rõ ràng:

### 4.1. Phân hệ Quản lý Sản phẩm & Cửa hàng (Shop Module)

* **Trang chủ cửa hàng:** Hiển thị danh sách sản phẩm phân trang. Truy vấn danh mục sản phẩm (Categories) được cache trực tiếp trên Redis để tránh bóp nghẹt Database khi có lượng truy cập lớn.
* **Trang chi tiết sản phẩm:** Hiển thị thông số, mô tả, hình ảnh và số lượng tồn kho theo thời gian thực.
* **Tìm kiếm & Lọc:** Tìm kiếm sản phẩm theo tên, lọc theo khoảng giá và danh mục (Sử dụng Async SQLAlchemy và Indexing trên Postgres).

### 4.2. Phân hệ Giỏ hàng Tốc độ cao (Cart Module - Sử dụng Redis)

Để tối ưu tốc độ và không làm tăng tải cho PostgreSQL, toàn bộ giỏ hàng của khách vãng lai và khách đăng nhập đều được lưu trên Redis.

* **Thêm/Sửa/Xóa sản phẩm trong giỏ:** Sử dụng Redis Hash với cấu trúc `cart:{session_id}` hoặc `cart:{user_id}`. Thay đổi số lượng sản phẩm cập nhật ngay lập tức thông qua Fetch API (AJAX) không cần tải lại trang.
* **Đồng bộ giỏ hàng:** Tự động gộp giỏ hàng vãng lai vào giỏ hàng thành viên ngay sau khi người dùng đăng nhập thành công.
* **Tính toán tổng tiền:** Thực hiện xử lý bất đồng bộ phía backend dựa trên giá gốc trong DB, ngăn chặn việc thao túng giá từ phía client.

### 4.3. Phân hệ Người dùng & Xác thực (Authentication Module)

* **Đăng ký / Đăng nhập:** Hệ thống biểu mẫu (Form) xử lý qua FastAPI mã hóa mật khẩu bằng `Passlib` (bcrypt).
* **Quản lý Session:** Phát hành JWT token hoặc Session ID lưu vào Cookie (HttpOnly, Secure) để duy trì trạng thái đăng nhập một cách an toàn.

### 4.4. Phân hệ Đặt hàng & Thanh toán (Checkout & Order Module)

Đây là phần cốt lõi đảm bảo tính toàn vẹn dữ liệu:

* **Trang thanh toán:** Thu thập thông tin giao hàng (Tên, Số điện thoại, Địa chỉ). hiển thị tóm tắt đơn hàng lấy từ Redis Cart.
* **Xử lý Đơn hàng (Database Transaction):**
1. Mở một transaction bất đồng bộ trong PostgreSQL.
2. Kiểm tra số lượng tồn kho (`product.stock`). Nếu đủ, tiến hành trừ kho trực tiếp (áp dụng cơ chế khóa hàng để tránh hiện tượng Race Condition - bán quá số lượng tồn).
3. Tạo bản ghi vào bảng `orders` và `order_items`.
4. Xóa dữ liệu giỏ hàng tương ứng trên Redis.
5. Commit Transaction. Nếu có bất kỳ lỗi nào xảy ra ở các bước, thực hiện Rollback lập tức.


* **Trang trạng thái đơn hàng:** Hiển thị hóa đơn chi tiết và trạng thái xử lý đơn hàng (Chờ xử lý, Đang giao, Đã giao) sau khi đặt hàng thành công.

---

## 5. Cấu hình Khởi chạy Hệ thống ứng dụng (Docker)

Hệ thống được thiết kế để vận hành đồng bộ chỉ thông qua một lệnh duy nhất. Bạn cần chuẩn bị file cấu hình nền tảng sau để khởi động dự án:

### File `docker-compose.yml`

```yaml
version: '3.8'

services:
  web:
    build: .
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ecommerce
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=ecommerce
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:

```

### File `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
```