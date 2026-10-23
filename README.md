# Đề tài 7 – Hệ thống quản lý ngân hàng câu hỏi

Ứng dụng desktop (Python + Tkinter) giúp quản lý câu hỏi theo môn, chủ đề, mức độ và
tạo đề kiểm tra ngẫu nhiên, chấm điểm, thống kê kết quả.

## 1. Yêu cầu môi trường

- Python 3.9 trở lên
- Tkinter (đi kèm Python trên Windows)

## 2. Cài đặt

```bash
# Tạo & kích hoạt môi trường ảo (đã tạo sẵn thư mục venv)
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell/CMD)
# source venv/bin/activate     # macOS/Linux

# Cài thư viện (tùy chọn)
pip install -r requirements.txt
```

## 3. Chạy ứng dụng

```bash
python -m src.main
```

## 4. Cấu trúc thư mục

```
De Tai So 7/
├── src/                  # Mã nguồn
│   ├── main.py           # Điểm khởi động ứng dụng
│   ├── models/           # Lớp dữ liệu (Subject, Topic, Question, Exam, Result...)
│   ├── views/            # Giao diện Tkinter (Treeview, Editor, form tạo đề, Canvas)
│   ├── controllers/      # Điều phối giữa view và service
│   ├── services/         # Nghiệp vụ (CRUD, tạo đề, chấm điểm, xuất file)
│   └── utils/            # Tiện ích chung (đọc/ghi JSON-CSV, validate, seed)
├── data/                 # Dữ liệu lưu trữ
│   └── samples/          # Dữ liệu JSON/CSV mẫu
├── exports/              # Đề & đáp án được xuất ra
├── docs/                 # Báo cáo, thiết kế lớp, hướng dẫn sử dụng
├── tests/                # Kiểm thử
├── assets/               # Ảnh, icon...
├── requirements.txt
└── README.md
```

## 5. Chức năng chính

- CRUD ngân hàng câu hỏi (môn / chủ đề / câu hỏi / phương án)
- Kiểm tra nội dung và đáp án
- Tạo đề theo ma trận mức độ bằng `random.sample()`
- Trộn thứ tự câu và phương án với `seed` (tái lập được)
- Chấm điểm và thống kê theo chủ đề
- **Nâng cao:** Custom QuestionEditor, tái lập đề theo seed, xuất đề & đáp án ra file

## 6. Nhóm thực hiện

| Thành viên        | Nhiệm vụ                                                     |
| ----------------- | ------------------------------------------------------------ |
| Lê Đạt Tuấn Kiệt  | Mô hình dữ liệu hướng đối tượng (entities)                   |
| Nguyễn Lê Chi Bảo | CRUD, kiểm tra dữ liệu (validation), đọc/ghi JSON            |
| Trương Hoài Bảo   | Sinh đề (sample + seed), trộn câu/phương án, xuất đề & đáp án |

> Phần soạn báo cáo và kiểm thử do cả ba thành viên cùng thực hiện.
