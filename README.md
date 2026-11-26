# odoo-cafe-nhom2
Dự án Odoo quản lý quán cà phê nhóm 2

## Bàn giao ca POS

Addon `pos_session_handover` ghép giao diện bàn giao ca của Nguyễn Trường Lâm với phần xử lý kiểm tiền của Lưu Gia Bảo. Bản này dùng Odoo 19 Community.

1. Đóng một ca POS có phương thức thanh toán tiền mặt.
2. Vào **Điểm bán hàng → Bàn giao ca**, tạo phiếu cho phiên đó và nhập tiền thực đếm. Sau khi lưu, Odoo hiển thị tiền dự kiến và chênh lệch. Số âm là thiếu, số dương là dư. Mỗi ca có tối đa một phiếu.
3. Nhân viên POS bấm **Gửi** để khóa phiếu. Quản lý POS bấm **Xác nhận** để hoàn tất.

### Chạy kiểm thử

Từ thư mục mã nguồn Odoo 19 Community, chạy lệnh sau với PostgreSQL đã cấu hình. Thay `REPO/addons` bằng đường dẫn tuyệt đối tới thư mục `addons` của dự án.

```sh
python odoo-bin -d cafe_pos_test "--addons-path=addons,REPO/addons" -i pos_session_handover --test-tags=/pos_session_handover --stop-after-init
```

Sử dụng một cơ sở dữ liệu thử nghiệm. Nếu addon đã được cài, dùng `-u` thay cho `-i`.

### Tên dùng chung

- Model `pos.session.handover`.
- Phiên POS và tiền tệ dùng `session_id` và `currency_id`. Ba trường tiền là `expected_amount`, `counted_amount` và `difference_amount`.
- `state` đi theo thứ tự `draft`, `submitted`, `confirmed`. Hai nút gọi `action_submit` và `action_confirm`.
