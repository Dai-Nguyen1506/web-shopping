Để biến trang web của bạn thành một sản phẩm thực thụ, phân hệ **Quản lý và Áp dụng Mã giảm giá (Coupon/Discount System)** cần được thiết kế chặt chẽ nhằm tránh các lỗ hổng bảo mật (như áp dụng mã hết hạn, mã vượt quá số lượng, hoặc bug đảo ngược số tiền đơn hàng).

Dưới đây là mô tả chi tiết, cấu trúc dữ liệu, logic nghiệp vụ và cách phân bổ chức năng này vào cấu trúc dự án hiện tại của bạn.

---

## 1. Thiết kế Cơ sở dữ liệu (SQLAlchemy Model)

Chúng ta cần một bảng `coupons` lưu trữ thông tin mã giảm giá và chỉnh sửa bảng `orders` để ghi nhận số tiền đã giảm.

### Bảng `coupons` (Lưu tại `src/models/product.py` hoặc file mới `coupon.py`)

* `id` (UUID/Int): Khóa chính.
* `code` (String, Unique, Index): Mã giảm giá người dùng nhập (ví dụ: `GIAYMOI2026`).
* `discount_type` (Enum): `percentage` (giảm theo % ) hoặc `fixed_amount` (giảm số tiền cố định).
* `discount_value` (Numeric): Giá trị giảm (ví dụ: `20` cho 20%, hoặc `50000` cho 50,000đ).
* `min_order_value` (Numeric): Số tiền đơn hàng tối thiểu để được áp dụng mã.
* `max_discount_amount` (Numeric): Số tiền giảm tối đa (đặc biệt quan trọng khi dùng loại `percentage`).
* `usage_limit` (Int): Tổng số lần mã này được phép sử dụng trong hệ thống.
* `used_count` (Int): Số lần đã sử dụng thực tế.
* `start_date` & `end_date` (DateTime): Thời hạn hiệu lực của mã.
* `is_active` (Boolean): Trạng thái kích hoạt (Bật/Tắt thủ công).

### Cập nhật Bảng `orders`

* `coupon_id` (FK): Khóa ngoại liên kết tới bảng `coupons` (để biết đơn hàng dùng mã nào).
* `discount_amount` (Numeric): Số tiền được giảm thực tế của đơn hàng đó.
* `final_amount` (Numeric): Số tiền cuối cùng khách phải trả (`total_amount - discount_amount`).

---

## 2. Luồng Hoạt động Nghiệp vụ (Business Logic)

### 2.1. Phân hệ Admin: Thêm, Sửa, Xóa Mã giảm giá (CRUD)

Giao diện Admin (Render qua Jinja2 + xử lý API qua HTTP POST/PUT/DELETE) cho phép quản lý vòng đời của mã:

* **Thêm mã (Create):** Định nghĩa các điều kiện ràng buộc (Thời gian, Số lượng, Loại giảm giá). Khi lưu, mã `code` tự động viết hoa và xóa khoảng trắng.
* **Sửa mã (Update):** Cho phép gia hạn `end_date` hoặc tăng `usage_limit` khi chương trình hot. Không cho phép sửa `discount_type` nếu mã đã có người sử dụng để tránh làm sai lệch báo cáo tài chính cũ.
* **Xóa mã (Delete):** Thực hiện **Soft Delete** (Chuyển `is_active = False`) thay vì xóa cứng khỏi Database. Điều này đảm bảo các đơn hàng cũ đã áp dụng mã này không bị lỗi toàn vẹn dữ liệu (Foreign Key Constraint).

### 2.2. Phân hệ Khách hàng: Áp dụng Mã giảm giá (Apply Coupon)

Quá trình này diễn ra tại **Trang Giỏ hàng** hoặc **Trang Thanh toán** và được xử lý hoàn toàn bằng **Async API + Redis Session**.

1. **Người dùng nhập mã:** Tại ô "Mã giảm giá", khách nhập mã và bấm "Áp dụng".
2. **Gọi API kiểm tra:** JavaScript gửi Fetch API `POST /api/cart/apply-coupon` kèm theo chuỗi `code`.
3. **Xác thực nghiêm ngặt (Validation Pipeline) tại Backend:**
* *Kiểm tra tồn tại:* Tìm mã trong DB. Nếu không thấy hoặc `is_active == False` $\rightarrow$ Báo lỗi.
* *Kiểm tra thời gian:* Thực hiện so sánh `start_date <= current_time <= end_date`. Nếu sai $\rightarrow$ Báo lỗi.
* *Kiểm tra lượt dùng:* So sánh `used_count < usage_limit`. Nếu bằng hoặc lớn hơn $\rightarrow$ Báo lỗi.
* *Kiểm tra giá trị đơn tối thiểu:* Lấy tổng tiền giỏ hàng hiện tại từ Redis. Nếu `total_cart_amount < min_order_value` $\rightarrow$ Báo lỗi.


4. **Tính toán số tiền giảm (Safe Calculation):**
* Nếu là `fixed_amount`: `discount = discount_value`.
* Nếu là `percentage`: `discount = total_cart_amount * (discount_value / 100)`. Sau đó so sánh, nếu `discount > max_discount_amount` thì gán `discount = max_discount_amount`.


5. **Lưu tạm vào Redis:** Nếu mã hợp lệ, lưu thông tin mã và số tiền giảm tạm thời vào cấu trúc giỏ hàng trên Redis của user đó (`cart:{user_id}` tăng thêm trường `applied_coupon: code`).
6. **Trả kết quả AJAX:** Trả về JSON chứa số tiền giảm và tổng tiền mới để JavaScript cập nhật giao diện ngay lập tức mà không reload trang.

### 2.3. Luồng Tạo Đơn hàng (Checkout Transaction)

Khi khách bấm "Xác nhận đặt hàng", tầng `order_service.py` sẽ thực hiện kiểm tra lại mã một lần cuối ngay trong DB Transaction để tránh trường hợp mã bị hủy hoặc hết lượt ngay trong lúc khách đang điền thông tin:

* Khóa dòng dữ liệu của mã giảm giá bằng `with_for_update()` trên Postgres: `SELECT * FROM coupons WHERE code = ... FOR UPDATE`.
* Tăng `used_count += 1`.
* Ghi nhận số tiền giảm vào đơn hàng và tiến hành commit.

---

## 3. Cập nhật cấu trúc mã nguồn dự án

Chức năng này được tích hợp gọn gàng vào cấu trúc thư mục sẵn có của bạn như sau:

```text
ecommerce-fastapi/
├── src/
│   ├── models/
│   │   └── coupon.py          # SQLAlchemy Model: Coupon
│   ├── schemas/
│   │   └── coupon.py          # Pydantic: CouponCreate, CouponResponse, ApplyCouponSchema
│   ├── repositories/
│   │   └── coupon_repo.py     # Thao tác DB: find_by_code, increment_usage, get_active_coupons
│   ├── services/
│   │   └── coupon_service.py  # Logic cốt lõi: validate_coupon, calculate_discount
│   ├── routers/
│   │   ├── web/
│   │   │   └── views_admin.py # Render giao diện quản lý Coupon cho Admin
│   │   └── api/
│   │       └── api_cart.py    # Thêm Endpoint: POST /api/cart/apply-coupon, DELETE /api/cart/remove-coupon
│   └── templates/
│       ├── admin/
│       │   └── coupons.html   # Giao diện Admin thêm/sửa/xóa mã
│       └── checkout/
│           └── index.html     # Cập nhật thêm Form nhập mã giảm giá (AJAX)

```

## 4. Tối ưu hóa tốc độ với Redis (Caching chiến lược)

Vì mã giảm giá có thể được áp dụng liên tục bởi hàng ngàn người cùng lúc (đặc biệt là các mã hot chạy chiến dịch), ta sẽ áp dụng cơ chế Cache:

* Khi Admin tạo hoặc kích hoạt một mã giảm giá, thông tin cấu hình của mã đó (loại giảm giá, giá trị, điều kiện tối thiểu) sẽ được đồng bộ lên **Redis String** hoặc **Hash** với key dạng `coupon:info:{code}`.
* Khi khách hàng áp dụng mã, hệ thống sẽ thực hiện khâu **Validation nhanh** (kiểm tra hạn dùng, kiểm tra điều kiện đơn hàng) trực tiếp từ dữ liệu trên Redis, giảm thiểu số lượng truy cập vào PostgreSQL xuống mức thấp nhất. Chỉ khi khách bấm "Đặt hàng thực sự", hệ thống mới truy vấn PostgreSQL để trừ số lượt dùng (`used_count`) trong Transaction.