# -*- coding: utf-8 -*-
"""
Nghiep vu tao de thi - phan Truong Hoai Bao.

Chuc nang:
    - Sinh de theo ma tran muc do (chon ngau nhien bang random.sample)
    - Tron thu tu cau va phuong an theo seed (cung seed -> cung mot de)
    - Tai lap lai mot de cu tu seed + ma tran da luu
    - Xuat de (cho thi sinh) va dap an (cho giao vien) ra file TXT/JSON
"""
import json
import random
from pathlib import Path

try:
    from src.models.entities import Exam, CauHoiDienKhuyet
except ModuleNotFoundError:
    from models.entities import Exam, CauHoiDienKhuyet

# Nhan hien thi cho cac phuong an: A, B, C, D, ...
NHAN = ["A", "B", "C", "D", "E", "F", "G", "H"]


class ExamGenerator:
    """Sinh de thi tu mot ngan hang cau hoi (QuestionBank)."""

    def __init__(self, bank):
        self.bank = bank

    # ---------- Sinh de ----------
    def sinh_de(self, matrix, seed=None, ten_de="De kiem tra", ma_de="E01"):
        """Sinh mot de thi theo ma tran muc do.

        matrix: danh sach cac dong, moi dong la dict:
            {"muc_do": "De"/"TrungBinh"/"Kho", "so_cau": so_cau,
             "topic_id": ma_chu_de (tuy chon)}
        seed: so nguyen de tai lap lai de (hoac None).
        """
        self._kiem_tra_matrix(matrix)
        rng = random.Random(seed)   # bo sinh ngau nhien co dinh theo seed

        # Buoc 1: chon cau theo tung dong ma tran
        da_chon = []
        da_chon_id = []
        for dong in matrix:
            muc_do = dong["muc_do"]
            so_cau = dong["so_cau"]

            # Lay cac cau phu hop, bo nhung cau da chon o dong truoc (tranh trung)
            nguon = []
            for cau in self.bank.loc_cau_hoi(topic_id=dong.get("topic_id"), muc_do=muc_do):
                if cau.id not in da_chon_id:
                    nguon.append(cau)

            if len(nguon) < so_cau:
                raise ValueError(
                    f"Không đủ câu hỏi mức '{muc_do}': cần {so_cau}, hiện có {len(nguon)}.")

            chon = rng.sample(nguon, so_cau)   # chon ngau nhien, khong lap
            for cau in chon:
                da_chon.append(cau)
                da_chon_id.append(cau.id)

        # Buoc 2: tron thu tu cac cau hoi
        rng.shuffle(da_chon)

        # Buoc 3: tron thu tu phuong an trong tung cau
        thu_tu_phuong_an = {}
        for cau in da_chon:
            cac_pa = list(cau.options)
            rng.shuffle(cac_pa)
            danh_sach_ma = []
            for pa in cac_pa:
                danh_sach_ma.append(pa.id)
            thu_tu_phuong_an[cau.id] = danh_sach_ma

        # Tao doi tuong de thi
        danh_sach_cau_id = []
        for cau in da_chon:
            danh_sach_cau_id.append(cau.id)

        exam = Exam(ma_de, ten_de, seed, matrix, danh_sach_cau_id)
        exam.cac_cau = da_chon                       # luu them de xuat file
        exam.thu_tu_phuong_an = thu_tu_phuong_an
        return exam

    def tai_lap_de(self, exam):
        """Tai lap lai dung mot de cu tu seed + ma tran da luu."""
        return self.sinh_de(exam.matrix, seed=exam.seed,
                            ten_de=exam.ten_de, ma_de=exam.id)

    # ---------- Tinh toan ----------
    def tong_diem(self, exam):
        """Tinh tong diem cua de."""
        tong = 0
        for cau in exam.cac_cau:
            tong = tong + cau.diem
        return tong

    # ---------- Xuat file ----------
    def xuat_de(self, exam, duong_dan):
        """Xuat de cho thi sinh (khong co dap an)."""
        return self._xuat_file(exam, duong_dan, co_dap_an=False)

    def xuat_dap_an(self, exam, duong_dan):
        """Xuat ban dap an cho giao vien (danh dau dap an dung)."""
        return self._xuat_file(exam, duong_dan, co_dap_an=True)

    def xuat_json(self, exam, duong_dan):
        """Luu de ra file JSON de tai lap sau nay."""
        path = Path(duong_dan)
        path.parent.mkdir(parents=True, exist_ok=True)
        f = open(path, "w", encoding="utf-8")
        json.dump(exam.to_dict(), f, ensure_ascii=False, indent=2)
        f.close()
        return exam.to_dict()

    # ---------- Ham phu tro ----------
    def _kiem_tra_matrix(self, matrix):
        """Kiem tra ma tran hop le, nem ValueError neu sai."""
        if not isinstance(matrix, list) or len(matrix) == 0:
            raise ValueError("Ma tran de phai la danh sach khac rong.")
        for dong in matrix:
            if not isinstance(dong, dict) or "so_cau" not in dong:
                raise ValueError("Moi dong ma tran can co 'muc_do' va 'so_cau'.")
            so_cau = dong["so_cau"]
            if isinstance(so_cau, bool) or not isinstance(so_cau, int) or so_cau <= 0:
                raise ValueError("'so_cau' phai la so nguyen lon hon 0.")

    def _phuong_an_theo_thu_tu(self, exam, cau):
        """Tra ve danh sach phuong an cua cau theo dung thu tu da tron."""
        ket_qua = []
        for ma in exam.thu_tu_phuong_an[cau.id]:
            for pa in cau.options:
                if pa.id == ma:
                    ket_qua.append(pa)
        return ket_qua

    def _xuat_file(self, exam, duong_dan, co_dap_an):
        """Tao noi dung va ghi file de / dap an."""
        dong = []
        dong.append(exam.ten_de.upper())
        dong.append(f"Mã đề: {exam.id}    Seed: {exam.seed}    "
                    f"Số câu: {len(exam.cac_cau)}    Tổng điểm: {self.tong_diem(exam)}")
        if co_dap_an:
            dong.append("(BẢN ĐÁP ÁN - DÀNH CHO GIÁO VIÊN)")
        dong.append("=" * 60)

        stt = 1
        for cau in exam.cac_cau:
            dong.append(f"Câu {stt} ({cau.muc_do}, {cau.diem}đ): {cau.noi_dung}")

            if isinstance(cau, CauHoiDienKhuyet):
                # Cau dien khuyet: khong co A/B/C/D
                if co_dap_an:
                    cac_dap_an = []
                    for pa in cau.dap_an_dung():
                        cac_dap_an.append(pa.noi_dung)
                    dong.append("    => Đáp án: " + " / ".join(cac_dap_an))
                else:
                    dong.append("    Trả lời: ...................................")
            else:
                # Cau trac nghiem: in cac phuong an theo thu tu da tron
                cac_pa = self._phuong_an_theo_thu_tu(exam, cau)
                dap_an_dung = []
                i = 0
                for pa in cac_pa:
                    nhan = NHAN[i]
                    if co_dap_an and pa.is_dung:
                        dong.append(f"    {nhan}. {pa.noi_dung} (*)")
                        dap_an_dung.append(nhan)
                    else:
                        dong.append(f"    {nhan}. {pa.noi_dung}")
                    i = i + 1
                if co_dap_an:
                    dong.append("    => Đáp án đúng: " + ", ".join(dap_an_dung))

            dong.append("")   # dong trong ngan cach giua cac cau
            stt = stt + 1

        noi_dung = "\n".join(dong)
        path = Path(duong_dan)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(noi_dung, encoding="utf-8")
        return noi_dung
