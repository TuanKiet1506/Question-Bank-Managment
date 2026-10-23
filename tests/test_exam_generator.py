# -*- coding: utf-8 -*-
"""
Kiểm thử module tạo đề (services/exam_generator.py).

Chạy trực tiếp:  python -m tests.test_exam_generator
(Cũng tương thích pytest: các hàm test_* dùng assert.)
"""
import sys
import tempfile
from pathlib import Path

try:
    from src.models.entities import (
        Subject, Topic, Option, Exam,
        CauHoiMotDapAn, CauHoiNhieuDapAn, CauHoiDienKhuyet,
    )
    from src.services.question_bank import QuestionBank
    from src.services.exam_generator import ExamGenerator
except ModuleNotFoundError:
    from models.entities import (
        Subject, Topic, Option, Exam,
        CauHoiMotDapAn, CauHoiNhieuDapAn, CauHoiDienKhuyet,
    )
    from services.question_bank import QuestionBank
    from services.exam_generator import ExamGenerator


def _opt(i, dung=False):
    return Option(f"O{i}", f"phuong an {i}", dung)


def build_bank():
    """Dựng một ngân hàng mẫu đủ câu để sinh đề (1 môn, 2 chủ đề, 9 câu)."""
    bank = QuestionBank()
    bank.them_mon(Subject("S01", "Lập trình Python"))
    bank.them_chu_de(Topic("T01", "S01", "Biến và kiểu dữ liệu"))
    bank.them_chu_de(Topic("T02", "S01", "Vòng lặp"))

    stt = 0

    def them(topic, muc_do, loai="single"):
        nonlocal stt
        stt += 1
        qid = f"Q{stt:02d}"
        if loai == "single":
            c = CauHoiMotDapAn(qid, topic, f"Câu hỏi {qid}?", muc_do, 1.0,
                               [_opt(1, True), _opt(2), _opt(3), _opt(4)])
        elif loai == "multiple":
            c = CauHoiNhieuDapAn(qid, topic, f"Câu hỏi {qid}?", muc_do, 1.0,
                                 [_opt(1, True), _opt(2, True), _opt(3), _opt(4)])
        else:
            c = CauHoiDienKhuyet(qid, topic, f"Câu hỏi {qid}?", muc_do, 1.0,
                                 [_opt(1, True)])
        bank.them_cau_hoi(c)

    # T01: 3 De, 2 TrungBinh, 1 Kho ; T02: 2 De, 1 Kho
    them("T01", "De"); them("T01", "De"); them("T01", "De", "multiple")
    them("T01", "TrungBinh"); them("T01", "TrungBinh", "fill")
    them("T01", "Kho")
    them("T02", "De"); them("T02", "De")
    them("T02", "Kho")
    return bank


def test_sinh_de_dung_so_luong():
    bank = build_bank()
    gen = ExamGenerator(bank)
    matrix = [
        {"muc_do": "De", "so_cau": 3},
        {"muc_do": "TrungBinh", "so_cau": 2},
        {"muc_do": "Kho", "so_cau": 1},
    ]
    exam = gen.sinh_de(matrix, seed=123, ten_de="Kiểm tra giữa kỳ", ma_de="E01")
    assert len(exam.danh_sach_cau) == 6
    # Không trùng câu
    assert len(set(exam.danh_sach_cau)) == 6
    # Đúng số câu theo từng mức độ
    cac_cau = {c.id: c for c in exam.cac_cau}
    dem = {"De": 0, "TrungBinh": 0, "Kho": 0}
    for cid in exam.danh_sach_cau:
        dem[cac_cau[cid].muc_do] += 1
    assert dem == {"De": 3, "TrungBinh": 2, "Kho": 1}
    print("PASS test_sinh_de_dung_so_luong")


def test_loc_theo_chu_de():
    bank = build_bank()
    gen = ExamGenerator(bank)
    exam = gen.sinh_de([{"muc_do": "De", "so_cau": 2, "topic_id": "T02"}], seed=1)
    for cid in exam.danh_sach_cau:
        assert bank.tim_cau_hoi(cid).topic_id == "T02"
    print("PASS test_loc_theo_chu_de")


def test_thieu_cau_bao_loi():
    bank = build_bank()
    gen = ExamGenerator(bank)
    try:
        gen.sinh_de([{"muc_do": "Kho", "so_cau": 10}], seed=1)  # chỉ có 2 câu Kho
        assert False, "Phải ném ValueError khi thiếu câu"
    except ValueError as e:
        assert "Không đủ câu" in str(e)
    print("PASS test_thieu_cau_bao_loi")


def test_matrix_sai_dinh_dang():
    gen = ExamGenerator(build_bank())
    for xau in ([], [{"muc_do": "De"}], [{"muc_do": "De", "so_cau": 0}],
                [{"muc_do": "De", "so_cau": -1}], [{"muc_do": "De", "so_cau": True}]):
        try:
            gen.sinh_de(xau, seed=1)
            assert False, f"Phải ném ValueError với {xau}"
        except ValueError:
            pass
    print("PASS test_matrix_sai_dinh_dang")


def test_tai_lap_cung_seed():
    bank = build_bank()
    gen = ExamGenerator(bank)
    matrix = [{"muc_do": "De", "so_cau": 3}, {"muc_do": "TrungBinh", "so_cau": 2}]

    e1 = gen.sinh_de(matrix, seed=2026)
    e2 = gen.sinh_de(matrix, seed=2026)
    # Cùng seed -> cùng thứ tự câu và cùng thứ tự phương án
    assert e1.danh_sach_cau == e2.danh_sach_cau
    assert e1.thu_tu_phuong_an == e2.thu_tu_phuong_an

    # Tái lập từ Exam nạp lại (mô phỏng đọc từ JSON)
    e3 = gen.tai_lap_de(Exam.from_dict(e1.to_dict()))
    assert e3.danh_sach_cau == e1.danh_sach_cau
    assert e3.thu_tu_phuong_an == e1.thu_tu_phuong_an

    # Seed khác -> rất có thể khác thứ tự (không bắt buộc, chỉ cảnh báo nếu trùng)
    e4 = gen.sinh_de(matrix, seed=999)
    if e4.danh_sach_cau == e1.danh_sach_cau:
        print("  (chú ý) seed khác cho ra cùng thứ tự - hiếm nhưng có thể xảy ra")
    print("PASS test_tai_lap_cung_seed")


def test_tron_phuong_an_giu_dap_an():
    bank = build_bank()
    gen = ExamGenerator(bank)
    exam = gen.sinh_de([{"muc_do": "De", "so_cau": 3}], seed=7)
    for cau in exam.cac_cau:
        order = exam.thu_tu_phuong_an[cau.id]
        # Cùng tập phương án, chỉ khác thứ tự
        assert set(order) == {o.id for o in cau.options}
        # Đáp án đúng vẫn còn trong danh sách
        assert any(o.is_dung for o in cau.options)
    print("PASS test_tron_phuong_an_giu_dap_an")


def test_tong_diem():
    bank = build_bank()
    gen = ExamGenerator(bank)
    exam = gen.sinh_de([{"muc_do": "De", "so_cau": 3}], seed=1)
    assert gen.tong_diem(exam) == 3.0
    print("PASS test_tong_diem")


def test_xuat_file():
    bank = build_bank()
    gen = ExamGenerator(bank)
    exam = gen.sinh_de([{"muc_do": "De", "so_cau": 3},
                        {"muc_do": "TrungBinh", "so_cau": 2}], seed=5, ma_de="E09")
    with tempfile.TemporaryDirectory() as d:
        f_de = Path(d) / "de.txt"
        f_da = Path(d) / "dapan.txt"
        f_js = Path(d) / "de.json"
        de = gen.xuat_de(exam, f_de)
        da = gen.xuat_dap_an(exam, f_da)
        gen.xuat_json(exam, f_js)
        assert f_de.exists() and f_da.exists() and f_js.exists()
        # Bản đề KHÔNG lộ đáp án; bản đáp án CÓ đánh dấu
        assert "(*)" not in de
        assert "(*)" in da and "Đáp án đúng" in da
        assert "Câu 5" in de  # đủ 5 câu
    print("PASS test_xuat_file")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n==> TẤT CẢ {len(tests)} CA KIỂM THỬ ĐỀU PASS")


if __name__ == "__main__":
    main()
