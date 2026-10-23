# -*- coding: utf-8 -*-
"""
Nghiệp vụ tạo đề thi - phần Trương Hoài Bảo.

Chức năng:
    - Sinh đề theo ma trận mức độ bằng random.sample() (chọn ngẫu nhiên, không lặp)
    - Trộn thứ tự câu hỏi và thứ tự phương án theo seed (cùng seed + ma trận -> cùng một đề)
    - Tái lập lại đúng một đề cũ từ seed + ma trận đã lưu
    - Xuất đề (cho thí sinh) và bản đáp án (cho giáo viên) ra file TXT/JSON

Thiết kế tách biệt: chỉ phụ thuộc QuestionBank (qua loc_cau_hoi/tim_cau_hoi) và
các lớp entities, không đụng tới giao diện hay tầng lưu trữ CRUD.
"""
import json
import random
from pathlib import Path

try:
    from src.models.entities import Exam, CauHoiDienKhuyet
except ModuleNotFoundError:
    from models.entities import Exam, CauHoiDienKhuyet

# Nhãn hiển thị phương án: A, B, C, D...
_NHAN_PHUONG_AN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class ExamGenerator:
    """Sinh đề thi từ một đối tượng QuestionBank."""

    def __init__(self, bank):
        self.bank = bank

    # =========================================================
    # 1) SINH ĐỀ
    # =========================================================
    def sinh_de(self, matrix, seed=None, ten_de="Đề kiểm tra", ma_de="E01"):
        """Sinh một đề thi theo ma trận mức độ.

        Tham số:
            matrix : danh sách spec, mỗi spec là dict gồm
                     - "muc_do"     : "De" | "TrungBinh" | "Kho" (bắt buộc)
                     - "so_cau"     : số câu cần lấy (int > 0, bắt buộc)
                     - "subject_id" : giới hạn theo môn (tùy chọn)
                     - "topic_id"   : giới hạn theo chủ đề (tùy chọn)
            seed   : số nguyên cố định trạng thái ngẫu nhiên để tái lập (hoặc None).
            ten_de : tên đề thi.
            ma_de  : mã đề.

        Trả về: đối tượng Exam, kèm 2 thuộc tính phụ (không lưu JSON) phục vụ xuất file:
            exam.cac_cau            : danh sách Question theo đúng thứ tự trong đề
            exam.thu_tu_phuong_an   : {id_câu: [id phương án theo thứ tự đã trộn]}

        Ném ValueError nếu ma trận sai định dạng hoặc ngân hàng không đủ câu.
        """
        self._kiem_tra_matrix(matrix)
        rng = random.Random(seed)

        # --- Bước 1: chọn câu theo từng dòng ma trận (random.sample -> không lặp) ---
        da_chon = []
        da_chon_id = set()
        for spec in matrix:
            muc_do = spec.get("muc_do")
            so_cau = spec["so_cau"]
            # Lọc nguồn theo phạm vi và loại bỏ câu đã chọn ở dòng trước (tránh trùng).
            nguon = [c for c in self.bank.loc_cau_hoi(
                        subject_id=spec.get("subject_id"),
                        topic_id=spec.get("topic_id"),
                        muc_do=muc_do)
                     if c.id not in da_chon_id]
            if len(nguon) < so_cau:
                raise ValueError(
                    f"Không đủ câu hỏi: cần {so_cau} câu mức '{muc_do}'"
                    f"{self._mo_ta_pham_vi(spec)} nhưng chỉ có {len(nguon)}.")
            chon = rng.sample(nguon, so_cau)
            da_chon.extend(chon)
            da_chon_id.update(c.id for c in chon)

        # --- Bước 2: trộn thứ tự các câu hỏi trong đề ---
        rng.shuffle(da_chon)

        # --- Bước 3: trộn thứ tự phương án trong từng câu (đáp án đúng vẫn giữ nguyên) ---
        thu_tu_phuong_an = {}
        for cau in da_chon:
            phuong_an = list(cau.options)
            rng.shuffle(phuong_an)
            thu_tu_phuong_an[cau.id] = [o.id for o in phuong_an]

        exam = Exam(ma_de, ten_de, seed, list(matrix), [c.id for c in da_chon])
        exam.cac_cau = da_chon
        exam.thu_tu_phuong_an = thu_tu_phuong_an
        return exam

    def tai_lap_de(self, exam):
        """Tái lập lại đúng một đề cũ từ seed + ma trận đã lưu trong Exam.

        Cùng ngân hàng + cùng seed + cùng ma trận sẽ cho ra đề giống hệt
        (cùng thứ tự câu và thứ tự phương án).
        """
        return self.sinh_de(exam.matrix, seed=exam.seed,
                             ten_de=exam.ten_de, ma_de=exam.id)

    # =========================================================
    # 2) TÍNH TOÁN HỖ TRỢ
    # =========================================================
    def tong_diem(self, exam):
        """Tổng điểm của đề."""
        return sum(c.diem for c in self._lay_cac_cau(exam))

    # =========================================================
    # 3) XUẤT FILE
    # =========================================================
    def xuat_de(self, exam, duong_dan):
        """Xuất đề cho thí sinh (không có đáp án) ra file TXT."""
        return self._xuat_txt(exam, duong_dan, kem_dap_an=False)

    def xuat_dap_an(self, exam, duong_dan):
        """Xuất bản đáp án cho giáo viên (đánh dấu đáp án đúng) ra file TXT."""
        return self._xuat_txt(exam, duong_dan, kem_dap_an=True)

    def xuat_json(self, exam, duong_dan):
        """Lưu đề ra JSON (id, tên, seed, ma trận, danh sách câu) để tái lập sau này."""
        p = Path(duong_dan)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(exam.to_dict(), f, ensure_ascii=False, indent=2)
        return exam.to_dict()

    # =========================================================
    # 4) HÀM PHỤ TRỢ (nội bộ)
    # =========================================================
    @staticmethod
    def _kiem_tra_matrix(matrix):
        if not isinstance(matrix, (list, tuple)) or not matrix:
            raise ValueError("Ma trận đề phải là danh sách khác rỗng.")
        for vi_tri, spec in enumerate(matrix, start=1):
            if not isinstance(spec, dict):
                raise ValueError(f"Dòng ma trận thứ {vi_tri} phải là dict.")
            so_cau = spec.get("so_cau")
            if not isinstance(so_cau, int) or isinstance(so_cau, bool) or so_cau <= 0:
                raise ValueError(f"Dòng ma trận thứ {vi_tri}: 'so_cau' phải là số nguyên > 0.")

    @staticmethod
    def _mo_ta_pham_vi(spec):
        phan = []
        if spec.get("subject_id"):
            phan.append(f"môn {spec['subject_id']}")
        if spec.get("topic_id"):
            phan.append(f"chủ đề {spec['topic_id']}")
        return (", " + ", ".join(phan)) if phan else ""

    def _lay_cac_cau(self, exam):
        """Trả về danh sách Question theo thứ tự đề; tự tái lập nếu exam chưa resolve."""
        if getattr(exam, "cac_cau", None) is not None:
            return exam.cac_cau
        # Exam nạp từ JSON: tái lập để có thứ tự câu + thứ tự phương án.
        if exam.matrix:
            return self.tai_lap_de(exam).cac_cau
        # Không có ma trận: dựng lại theo danh_sach_cau đã lưu.
        cac_cau = [self.bank.tim_cau_hoi(cid) for cid in exam.danh_sach_cau]
        return [c for c in cac_cau if c is not None]

    def _thu_tu_phuong_an(self, exam, cau):
        order = getattr(exam, "thu_tu_phuong_an", None)
        if order and cau.id in order:
            bang = {o.id: o for o in cau.options}
            return [bang[oid] for oid in order[cau.id] if oid in bang]
        return list(cau.options)

    def _xuat_txt(self, exam, duong_dan, kem_dap_an):
        # Đảm bảo có thứ tự câu + phương án (tái lập nếu cần).
        if getattr(exam, "cac_cau", None) is None and exam.matrix:
            exam = self.tai_lap_de(exam)
        cac_cau = self._lay_cac_cau(exam)

        dong = []
        dong.append(exam.ten_de.upper())
        dong.append(
            f"Mã đề: {exam.id}    Seed: {exam.seed}    "
            f"Số câu: {len(cac_cau)}    Tổng điểm: {self.tong_diem(exam):g}")
        if kem_dap_an:
            dong.append("(BẢN ĐÁP ÁN - DÀNH CHO GIÁO VIÊN)")
        dong.append("=" * 64)

        for i, cau in enumerate(cac_cau, start=1):
            dong.append(f"Câu {i} ({cau.muc_do}, {cau.diem:g}đ): {cau.noi_dung}")

            if isinstance(cau, CauHoiDienKhuyet):
                if kem_dap_an:
                    da = " / ".join(o.noi_dung for o in cau.dap_an_dung())
                    dong.append(f"    => Đáp án: {da}")
                else:
                    dong.append("    Trả lời: ...........................................")
            else:
                phuong_an = self._thu_tu_phuong_an(exam, cau)
                for nhan, o in zip(_NHAN_PHUONG_AN, phuong_an):
                    danh_dau = " (*)" if (kem_dap_an and o.is_dung) else ""
                    dong.append(f"    {nhan}. {o.noi_dung}{danh_dau}")
                if kem_dap_an:
                    dung = [_NHAN_PHUONG_AN[k] for k, o in enumerate(phuong_an) if o.is_dung]
                    dong.append(f"    => Đáp án đúng: {', '.join(dung)}")
            dong.append("")

        noi_dung = "\n".join(dong)
        p = Path(duong_dan)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(noi_dung, encoding="utf-8")
        return noi_dung


# -------------------------------------------------------------
# Hàm tiện lợi dạng thủ tục (tương đương minh họa trong báo cáo)
# -------------------------------------------------------------
def sinh_de(bank, matrix, seed=None, ten_de="Đề kiểm tra", ma_de="E01"):
    """Sinh nhanh một đề mà không cần tạo đối tượng ExamGenerator."""
    return ExamGenerator(bank).sinh_de(matrix, seed=seed, ten_de=ten_de, ma_de=ma_de)
