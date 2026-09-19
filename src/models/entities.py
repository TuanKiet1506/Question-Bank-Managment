# -*- coding: utf-8 -*-
"""
Định nghĩa các lớp dữ liệu (entities) của hệ thống.

Dự kiến các lớp:
    - Subject  (Môn học): id, ten_mon, mo_ta
    - Topic    (Chủ đề):  id, subject_id, ten_chu_de
    - Question (Câu hỏi): id, topic_id, noi_dung, muc_do, loai_cau, diem
    - Option   (Phương án): id, question_id, noi_dung, is_dung
    - Exam     (Đề thi):  id, ten_de, seed, matrix, danh_sach_cau
    - Result   (Kết quả): id, exam_id, thi_sinh, diem, chi_tiet, thoi_gian

TODO: cài đặt các lớp (gợi ý dùng dataclass).
"""
