# -*- coding: utf-8 -*-
"""Kiểm thử nhập/xuất ngân hàng câu hỏi từ file TXT (storage.import_txt/export_txt)."""
import tempfile
from pathlib import Path

try:
    from src.models.entities import Subject, Topic
    from src.services.question_bank import QuestionBank
    from src.utils import storage
except ModuleNotFoundError:
    from models.entities import Subject, Topic
    from services.question_bank import QuestionBank
    from utils import storage


def _bank():
    b = QuestionBank()
    b.them_mon(Subject("S01", "Python"))
    b.them_chu_de(Topic("T01", "S01", "Cơ bản"))
    return b


MAU = """\
[Q01] T01 | De | 1
Kiểu dữ liệu nào lưu số nguyên?
* int
- str
- float

[Q02] T01 | TrungBinh | 1 | multiple
Các kiểu số trong Python?
* int
* float
- str

[Q03] T01 | De | 1 | fill
Từ khóa định nghĩa hàm là ____ ?
= def
"""


def test_import_hop_le():
    b = _bank()
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cauhoi.txt"
        p.write_text(MAU, encoding="utf-8")
        them, loi = storage.import_txt(p, b)
        assert them == 3, (them, loi)
        assert loi == []
        q1 = b.tim_cau_hoi("Q01"); assert q1.LOAI == "single"
        assert [o.noi_dung for o in q1.dap_an_dung()] == ["int"]
        assert b.tim_cau_hoi("Q02").LOAI == "multiple"
        assert b.tim_cau_hoi("Q03").LOAI == "fill"
    print("PASS test_import_hop_le")


def test_import_bao_loi_tung_dong():
    b = _bank()
    xau = "[Q01] T01 | De | 1\nNoi dung\n* a\n\n[Q02] T01 | De | x\nNoi dung\n* a\n- b\n"
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.txt"; p.write_text(xau, encoding="utf-8")
        them, loi = storage.import_txt(p, b)
        # Q01 thiếu phương án thứ 2 (loi validation); Q02 diem 'x' khong phai so
        assert them == 0, them
        assert any("Dòng 5" in e for e in loi), loi   # Q02 bat dau dong 5
    print("PASS test_import_bao_loi_tung_dong")


def test_roundtrip_export_import():
    b = _bank()
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cauhoi.txt"
        p.write_text(MAU, encoding="utf-8")
        storage.import_txt(p, b)
        # Xuat ra roi nhap lai vao bank moi -> giu nguyen so cau + loai
        out = Path(d) / "export.txt"
        storage.export_txt(b, out)
        b2 = _bank()
        them, loi = storage.import_txt(out, b2)
        assert them == 3 and loi == [], (them, loi)
        for qid in ("Q01", "Q02", "Q03"):
            assert b.tim_cau_hoi(qid).LOAI == b2.tim_cau_hoi(qid).LOAI
    print("PASS test_roundtrip_export_import")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n==> TẤT CẢ {len(tests)} CA KIỂM THỬ ĐỀU PASS")


if __name__ == "__main__":
    main()
