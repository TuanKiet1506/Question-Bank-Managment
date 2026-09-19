# -*- coding: utf-8 -*-
"""
Đề tài 7 - Hệ thống quản lý ngân hàng câu hỏi
Điểm khởi động ứng dụng (entry point).

TODO: Khởi tạo cửa sổ Tkinter chính và nạp giao diện.
Hiện tại chỉ là khung placeholder - chưa cài đặt logic.
"""

import sys

# Đảm bảo in được tiếng Việt trên console Windows (tránh lỗi cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def main() -> None:
    """Hàm chạy chính của ứng dụng."""
    # TODO: import và khởi chạy MainWindow từ src.views
    print("Hệ thống quản lý ngân hàng câu hỏi - môi trường đã sẵn sàng.")


if __name__ == "__main__":
    main()
