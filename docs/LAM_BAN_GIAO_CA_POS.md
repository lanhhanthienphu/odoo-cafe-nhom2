Tài liệu phần việc Nguyễn Trường Lâm — Bàn giao ca POS

Dự án quán cà phê Nhóm 2 trên Odoo. Tài liệu được lập ngày 27/11/2026 theo mã nguồn trên main, commit 99eb7e9496551f85ea8f784104f1b31900ea28b8.

Phụ trách XML views, menu, danh sách, biểu mẫu, bộ lọc, các nút gửi/xác nhận và đối chiếu báo cáo POS với dữ liệu mẫu. Mã giao diện đã được đẩy lên nhánh feature/handover-views và ghép vào main cùng backend bàn giao ca.

Nhóm dùng Odoo 18 Community. Bản mã tham chiếu lúc lập tài liệu ghi Odoo 19 Community và bản tích hợp hiện tại đã chuyển sang Odoo 18. Các kịch bản trong tài liệu là kế hoạch kiểm thử, đang chờ thực hiện trên môi trường nhóm.

Nhánh làm việc của Lâm là `feature/handover-views`. File giao diện nằm tại `addons/pos_session_handover/views/pos_handover_views.xml`. Model dùng chung là `pos.session.handover`.

| Thành phần | Tên kỹ thuật | Nội dung |
|---|---|---|
| Danh sách | `view_pos_session_handover_list` | Phiên POS, tiền dự kiến, tiền thực đếm, chênh lệch, trạng thái |
| Biểu mẫu | `view_pos_session_handover_form` | Chọn phiên, nhập tiền thực đếm và thực hiện quy trình bàn giao |
| Bộ lọc | `view_pos_session_handover_search` | Tìm theo phiên, lọc trạng thái, nhóm theo trạng thái hoặc phiên |
| Action | `action_pos_session_handover` | Mở giao diện danh sách và biểu mẫu |
| Menu | `menu_pos_session_handover` | Vào POS → Bàn giao ca |

| Trường dữ liệu | Ý nghĩa |
|---|---|
| `session_id` | Phiên POS được bàn giao |
| `currency_id` | Tiền tệ của phiên |
| `expected_amount` | Tiền dự kiến, lấy từ `cash_register_balance_end` của phiên khi tạo phiếu |
| `counted_amount` | Tiền thực đếm do người dùng nhập |
| `difference_amount` | Tiền thực đếm trừ tiền dự kiến, làm tròn theo tiền tệ |
| `state` | Trạng thái xử lý phiếu |

Quy trình trạng thái dùng `draft` (Nháp) → `submitted` (Đã gửi) → `confirmed` (Đã xác nhận). Nút Gửi gọi `action_submit`. Nút Xác nhận gọi `action_confirm` và hiển thị cho quản lý POS khi phiếu đã gửi.

Tiền dự kiến được chụp lại khi tạo phiếu. Chênh lệch bằng 0 thể hiện số tiền khớp, số âm thể hiện thiếu tiền và số dương thể hiện dư tiền. Người dùng POS nhập hoặc sửa tiền thực đếm khi phiếu còn Nháp. Backend kiểm tra trạng thái, quyền xác nhận và ràng buộc mỗi phiên có tối đa một phiếu.

Để kiểm tra giao diện, chuẩn bị tài khoản nhân viên POS và tài khoản quản lý POS trong cơ sở dữ liệu thử nghiệm. Chuẩn bị một phiên đã đóng có thanh toán tiền mặt. Với ví dụ VND trong bảng kiểm thử, dùng phiên có tiền dự kiến 30.000đ. Các trường hợp TC03–TC05 sửa trên cùng một phiếu Nháp. Chuẩn bị thêm các phiên khác để có phiếu ở đủ ba trạng thái khi thử bộ lọc.

1. Đăng nhập bằng tài khoản nhân viên POS và mở POS → Bàn giao ca.
2. Bấm Mới, chọn một phiên đã đóng có phương thức tiền mặt và nhập tiền thực đếm.
3. Lưu phiếu. Kiểm tra tiền dự kiến và chênh lệch được hiển thị sau khi lưu. Phiên POS được khóa chọn trên phiếu đã lưu.
4. Khi phiếu còn Nháp, sửa tiền thực đếm và lưu để đối chiếu cách tính chênh lệch.
5. Bấm Gửi. Kiểm tra trạng thái chuyển sang submitted và ô tiền thực đếm được khóa.
6. Đăng nhập bằng tài khoản quản lý POS, mở phiếu đã gửi và bấm Xác nhận. Kiểm tra trạng thái confirmed.
7. Thử tìm theo phiên, các bộ lọc trạng thái và các nhóm dữ liệu. Ghi kết quả thực tế vào bảng bên dưới và lưu ảnh tương ứng.

| Mã | Thao tác và dữ liệu | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|
| TC01 | Mở POS → Bàn giao ca bằng tài khoản nhân viên POS và quản lý POS | Mở được danh sách, mở được biểu mẫu tạo phiếu theo quyền đã cấp | Chờ ghi nhận | Chờ chạy |
| TC02 | Mở danh sách chọn phiên trên phiếu mới | Hiển thị các phiên đã đóng có sổ tiền mặt theo domain của giao diện | Chờ ghi nhận | Chờ chạy |
| TC03 | Tạo phiếu với tiền dự kiến 30.000đ, thực đếm 30.000đ, lưu phiếu | Tiền dự kiến 30.000đ, chênh lệch 0đ, trạng thái draft và phiên POS được khóa chọn sau lưu | Chờ ghi nhận | Chờ chạy |
| TC04 | Trên phiếu Nháp TC03, đổi thực đếm thành 28.000đ rồi lưu | Chênh lệch -2.000đ | Chờ ghi nhận | Chờ chạy |
| TC05 | Trên phiếu Nháp TC03, đổi thực đếm thành 32.000đ rồi lưu | Chênh lệch +2.000đ | Chờ ghi nhận | Chờ chạy |
| TC06 | Tạo thêm phiếu cho phiên đã có phiếu bàn giao | Thao tác lưu bị từ chối do ràng buộc duy nhất theo phiên | Chờ ghi nhận | Chờ chạy |
| TC07 | Trên phiếu Nháp, nhập tiền thực đếm -1đ rồi lưu | Có thông báo từ chối số tiền âm | Chờ ghi nhận | Chờ chạy |
| TC08 | Nhân viên POS bấm Gửi trên phiếu Nháp hợp lệ | Trạng thái submitted, ô tiền thực đếm được khóa và nút Gửi được ẩn | Chờ ghi nhận | Chờ chạy |
| TC09 | Xem phiếu đã gửi bằng nhân viên POS, sau đó mở bằng quản lý POS và xác nhận | Nút Xác nhận được ẩn với nhân viên POS và hiển thị cho quản lý POS. Quản lý bấm xác nhận để chuyển phiếu sang confirmed | Chờ ghi nhận | Chờ chạy |
| TC10 | Tìm một phiên, lần lượt lọc Nháp/Đã gửi/Đã xác nhận và nhóm theo phiên/trạng thái | Các phiếu và nhóm khớp dữ liệu đã tạo | Chờ ghi nhận | Chờ chạy |

Sau TC06 và TC07, nạp lại phiếu Nháp hợp lệ trước khi thực hiện TC08.

Khi thực hiện mỗi ca kiểm thử, thay cột Kết quả thực tế bằng điều đã quan sát, ghi tên ảnh minh chứng hoặc nội dung lỗi và cập nhật Trạng thái thành Đạt hoặc Lỗi. Ghi kèm ngày chạy, phiên bản Odoo, tên cơ sở dữ liệu và commit được thử. Các ca hiện đều đang chờ chạy.

Đối chiếu báo cáo POS mẫu đã thực hiện trên hệ thống học tập online ngày 19/11/2026 dựa trên ảnh và kết quả người thực hiện cung cấp.

| Nội dung | Kết quả đã đối chiếu |
|---|---|
| Quầy | Cafe Nhóm 2 – Quầy chính |
| Đơn hàng | Cafe Nhóm 2 – Quầy chính - 000005 |
| Số biên lai | 261-1-000005 |
| Mặt hàng | [CF-SUA] Cà phê sữa |
| Số lượng | 1 |
| Tổng giá đơn hàng | 30.000đ |
| Thanh toán | Tiền mặt, 30.000đ |
| Báo cáo POS | 1 đơn, số lượng sản phẩm 1, tổng giá 30.000đ |
| Đối chiếu phiên | Người thực hiện đã xác nhận phiên trên đơn và báo cáo khớp nhau |

Kết quả mẫu ghi nhận tổng giá đơn hàng và tổng giá trên báo cáo POS bằng nhau. Số tiền dự kiến của phiếu bàn giao ca lấy từ số dư tiền mặt của phiên theo backend. Khi báo cáo tiền mặt, cần đối chiếu cả số dư đầu ca và các khoản thu/chi của phiên.

Các ảnh minh chứng của bài báo cáo cần gồm chi tiết đơn 000005 và báo cáo POS có phiên đã đối chiếu. Sau khi chạy addon trên môi trường nhóm, bổ sung ảnh danh sách phiếu, biểu mẫu Nháp, phiếu đã gửi, phiếu đã xác nhận và bộ lọc đang dùng.
