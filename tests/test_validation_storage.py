# -*- coding: utf-8 -*-
"""
Kiểm thử regex định dạng mã (validation) và độ bền của storage.load.

Chạy trực tiếp:  python -m tests.test_validation_storage
"""
import json
import tempfile
from pathlib import Path

try:
    from src.models.entities import Subject, Topic, Option, CauHoiMotDapAn
    from src.services.question_bank import QuestionBank
    from src.utils import storage
except ModuleNotFoundError:
    from models.entities import Subject, Topic, Option, CauHoiMotDapAn
    from services.question_bank import QuestionBank
    from utils import storage


def _bank_co_ban():
    bank = QuestionBank()
    bank.them_mon(Subject("S01", "Lập trình Python"))
    bank.them_chu_de(Topic("T01", "S01", "Biến"))
    return bank


def _cau(qid="Q01", opt_ids=("O1", "O2")):
    opts = [Option(opt_ids[0], "a", True), Option(opt_ids[1], "b", False)]
    return CauHoiMotDapAn(qid, "T01", "Noi dung?", "De", 1.0, opts)


# ---------------- REGEX ----------------
def test_ma_mon_sai_dinh_dang():
    bank = QuestionBank()
    for ma_sai in ("MON1", "s01", "01", "S", "S01 "):
        try:
            bank.them_mon(Subject(ma_sai, "X"))
            assert False, f"Phải báo lỗi với mã môn '{ma_sai}'"
        except ValueError as e:
            assert "dinh dang" in str(e).lower() or "dang" in str(e).lower()
    bank.them_mon(Subject("S01", "OK"))  # mã đúng -> không lỗi
    print("PASS test_ma_mon_sai_dinh_dang")


def test_ma_chu_de_sai_dinh_dang():
    bank = QuestionBank()
    bank.them_mon(Subject("S01", "X"))
    for ma_sai in ("CD1", "t01", "T", "S01"):
        try:
            bank.them_chu_de(Topic(ma_sai, "S01", "Y"))
            assert False, f"Phải báo lỗi với mã chủ đề '{ma_sai}'"
        except ValueError:
            pass
    bank.them_chu_de(Topic("T01", "S01", "OK"))
    print("PASS test_ma_chu_de_sai_dinh_dang")


def test_ma_cau_hoi_sai_dinh_dang():
    bank = _bank_co_ban()
    try:
        bank.them_cau_hoi(_cau(qid="CAU01"))
        assert False, "Phải báo lỗi mã câu hỏi sai định dạng"
    except ValueError as e:
        assert "dinh dang" in str(e).lower()
    bank.them_cau_hoi(_cau(qid="Q01"))  # đúng
    print("PASS test_ma_cau_hoi_sai_dinh_dang")


def test_ma_phuong_an_sai_dinh_dang():
    bank = _bank_co_ban()
    try:
        bank.them_cau_hoi(_cau(qid="Q01", opt_ids=("OP1", "O2")))
        assert False, "Phải báo lỗi mã phương án sai định dạng"
    except ValueError as e:
        assert "dinh dang" in str(e).lower()
    print("PASS test_ma_phuong_an_sai_dinh_dang")


# ---------------- STORAGE ----------------
def test_load_file_thieu_tao_mac_dinh():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sub" / "khong_co.json"   # file + thư mục chưa tồn tại
        bank = storage.load(p)
        assert isinstance(bank, QuestionBank) and bank.subjects == []
        assert p.exists(), "Phải tự tạo lại file cấu trúc mặc định"
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["subjects"] == [] and "questions" in data
    print("PASS test_load_file_thieu_tao_mac_dinh")


def test_load_file_rong():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "rong.json"
        p.write_text("   ", encoding="utf-8")
        bank = storage.load(p)
        assert isinstance(bank, QuestionBank) and bank.subjects == []
    print("PASS test_load_file_rong")


def test_load_file_hong_khong_ghi_de():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "hong.json"
        rac = "{ day khong phai JSON hop le "
        p.write_text(rac, encoding="utf-8")
        bank = storage.load(p)
        assert isinstance(bank, QuestionBank) and bank.subjects == []
        # Không ghi đè file hỏng (giữ để khôi phục)
        assert p.read_text(encoding="utf-8") == rac
    print("PASS test_load_file_hong_khong_ghi_de")


def test_roundtrip_hop_le():
    bank = _bank_co_ban()
    bank.them_cau_hoi(_cau("Q01"))
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "data.json"
        storage.save(bank, p)
        b2 = storage.load(p)
        assert len(b2.subjects) == 1
        assert b2.tim_cau_hoi("Q01") is not None
    print("PASS test_roundtrip_hop_le")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n==> TẤT CẢ {len(tests)} CA KIỂM THỬ ĐỀU PASS")


if __name__ == "__main__":
    main()
