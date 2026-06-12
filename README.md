# E-Shop Premium (FastAPI + Jinja2 + Redis)

Dự án xây dựng một trang web bán hàng (E-commerce) hiệu năng cao, sử dụng kiến trúc phân tầng sạch sẽ (Clean Architecture), tích hợp cơ chế kết xuất phía server (SSR) tối ưu SEO và tốc độ tải trang dưới 50ms.

---

## 1. Yêu cầu Hệ thống
- Python 3.11+
- Redis Server (Tùy chọn, dự án có cơ chế tự động chuyển vùng sang Mock Redis in-memory nếu không kết nối được Redis thật)
- Docker & Docker Compose (Tùy chọn, nếu muốn khởi chạy toàn bộ môi trường qua container)

---

## 2. Hướng dẫn Cài đặt & Khởi chạy (Chạy trực tiếp trên máy)

Nếu bạn đang đứng ở thư mục gốc của dự án (`ecommerce-fastapi`), hãy thực hiện các bước sau trong terminal của bạn:

### Bước 2.1: Tạo môi trường ảo Python
Tạo môi trường ảo `.venv` để cài đặt các thư viện độc lập:
```bash
python -m venv .venv
```

### Bước 2.2: Kích hoạt môi trường ảo
- **Trên Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Trên Windows (Command Prompt - cmd):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Trên macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### Bước 2.3: Cài đặt các thư viện phụ thuộc
Cài đặt toàn bộ các thư viện được khai báo trong `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Bước 2.4: Khởi tạo cơ sở dữ liệu và gieo dữ liệu mẫu (Seed)
Chạy script sinh dữ liệu mẫu để tạo sẵn bảng SQLite, 2 tài khoản thử nghiệm, sản phẩm và mã giảm giá:
```bash
python -m src.seed
```

### Bước 2.5: Khởi động Web Server
Chạy ứng dụng bằng Uvicorn:
```bash
uvicorn src.main:app --reload
```
Sau đó, hãy mở trình duyệt và truy cập: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 3. Khởi chạy bằng Docker Compose

Nếu bạn muốn chạy ứng dụng đồng bộ đầy đủ các dịch vụ FastAPI, PostgreSQL 15 và Redis 7 thông qua Docker:
```bash
docker-compose up --build
```
Hệ thống sẽ tự động khởi chạy và cấu hình kết nối. Ứng dụng sẽ hoạt động tại địa chỉ: [Link](http://127.0.0.1:8000/)

---

## 4. Chạy kiểm thử tự động (Automated Tests)

Để xác thực tất cả các tính năng đăng ký, đăng nhập, giỏ hàng, áp dụng mã giảm giá và đặt hàng hoạt động chính xác:
```bash
pytest --asyncio-mode=auto tests/
```

---

## 5. Danh sách tài khoản thử nghiệm có sẵn (Đã được sinh qua script seed)

| Email | Mật khẩu | Quyền truy cập | Mục đích |
| --- | --- | --- | --- |
| **admin@eshop.com** | `admin123` | Quản trị viên (Admin) | Truy cập bảng quản trị tại [http://127.0.0.1:8000/admin/dashboard](http://127.0.0.1:8000/admin/dashboard) để quản lý sản phẩm và mã giảm giá. |
| **user@eshop.com** | `user123` | Khách hàng (User) | Đăng nhập để thực hiện mua sắm và thanh toán đơn hàng. |

---

## 6. Danh sách các mã giảm giá thử nghiệm có sẵn
- `GIAM20`: Giảm 20% tổng giá trị đơn hàng (Giảm tối đa 500,000đ, yêu cầu đơn hàng từ 1,000,000đ).
- `ESHOP100`: Giảm trực tiếp 100,000đ (yêu cầu đơn hàng tối thiểu từ 500,000đ).
- `VIP500`: Giảm trực tiếp 500,000đ (yêu cầu đơn hàng tối thiểu từ 5,000,000đ).
