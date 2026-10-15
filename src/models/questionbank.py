# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 20:35:01 2026

@author: nguyenlechibao
"""

from math import isfinite
from numbers import Real
try:
    from src.entities import Subject, Topic, Question, Option
except ModuleNotFoundError:
    from entities import Subject, Topic, Question, Option
    
class QuestionBank:
    """Lop tong quan, quan ly danh sach Subject va cac thao tac nghiep vu."""

    CAC_MUC_DO = {"De", "TrungBinh", "Kho"}
    CAC_LOAI_CAU_HOI = {"single", "multiple", "fill"}
    def __init__(self):
        self.subjects = []
    
    @staticmethod
    def _kiem_tra_chuoi_bat_buoc(gia_tri, ten_truong):
        if not isinstance(gia_tri, str) or not gia_tri.strip():
            raise ValueError(f"{ten_truong} khong duoc de trong.")

    def _loi_cau_hoi(self, cau_hoi, bo_qua_id=None):
        """Kiem tra mot cau hoi va tra ve danh sach loi, khong lam thay doi du lieu."""
        loi = []

        if not isinstance(cau_hoi, Question):
            return ["Du lieu phai la mot doi tuong Question hoac lop con cua Question."]

        if not isinstance(cau_hoi.id, str) or not cau_hoi.id.strip():
            loi.append("Ma cau hoi khong duoc de trong.")
        else:
            for cau_khac in self._tat_ca_cau_hoi():
                if cau_khac.id == cau_hoi.id and cau_khac.id != bo_qua_id:
                    loi.append(f"Ma cau hoi '{cau_hoi.id}' da ton tai.")
                    break

        if not isinstance(cau_hoi.topic_id, str) or self.tim_chu_de(cau_hoi.topic_id) is None:
            loi.append(f"Chu de '{cau_hoi.topic_id}' khong ton tai.")

        if not isinstance(cau_hoi.noi_dung, str) or not cau_hoi.noi_dung.strip():
            loi.append(f"Cau hoi {cau_hoi.id}: noi dung khong duoc de trong.")

        if not isinstance(cau_hoi.muc_do, str) or cau_hoi.muc_do not in self.CAC_MUC_DO:
            loi.append(f"Cau hoi {cau_hoi.id}: muc do phai la De, TrungBinh hoac Kho.")

        diem_hop_le = (
            isinstance(cau_hoi.diem, Real)
            and not isinstance(cau_hoi.diem, bool)
            and isfinite(float(cau_hoi.diem))
            and cau_hoi.diem > 0)
        if not diem_hop_le:
            loi.append(f"Cau hoi {cau_hoi.id}: diem phai la so huu han lon hon 0.")

        loai_cau = getattr(cau_hoi, "LOAI", "base")
        if not isinstance(loai_cau, str) or loai_cau not in self.CAC_LOAI_CAU_HOI:
            loi.append(f"Cau hoi {cau_hoi.id}: loai cau hoi khong duoc ho tro.")

        options = getattr(cau_hoi, "options", None)
        options_hop_le = isinstance(options, list)
        if not options_hop_le:
            loi.append(f"Cau hoi {cau_hoi.id}: options phai la mot danh sach.")
        else:
            cac_ma_phuong_an = []
            for vi_tri, phuong_an in enumerate(options, start=1):
                if not isinstance(phuong_an, Option):
                    loi.append(f"Cau hoi {cau_hoi.id}: phuong an thu {vi_tri} khong phai Option.")
                    options_hop_le = False
                    continue
                if not isinstance(phuong_an.id, str) or not phuong_an.id.strip():
                    loi.append(f"Cau hoi {cau_hoi.id}: ma phuong an thu {vi_tri} khong duoc de trong.")
                    options_hop_le = False
                else:
                    cac_ma_phuong_an.append(phuong_an.id)
                if not isinstance(phuong_an.noi_dung, str) or not phuong_an.noi_dung.strip():
                    loi.append(f"Cau hoi {cau_hoi.id}: noi dung phuong an thu {vi_tri} khong duoc de trong.")
                    options_hop_le = False
                if not isinstance(phuong_an.is_dung, bool):
                    loi.append(f"Cau hoi {cau_hoi.id}: is_dung cua phuong an thu {vi_tri} phai la True/False.")
                    options_hop_le = False

            if len(cac_ma_phuong_an) != len(set(cac_ma_phuong_an)):
                loi.append(f"Cau hoi {cau_hoi.id}: ma phuong an khong duoc trung nhau.")

        # Tai su dung quy tac kiem tra da cai dat trong entities.py.
        # Chi goi khi cac thuoc tinh quan trong co kieu du lieu an toan.
        if (
            isinstance(cau_hoi.noi_dung, str)
            and diem_hop_le
            and options_hop_le
        ):
            try:
                loi.extend(cau_hoi.kiem_tra_hop_le())
            except (TypeError, AttributeError, ValueError) as exc: loi.append(f"Cau hoi {cau_hoi.id}: khong the kiem tra hop le ({exc}).")
        return loi
    def them_mon(self, mon):
        """Them mot Subject moi vao ngan hang."""
        if not isinstance(mon, Subject):
            raise TypeError("Du lieu phai la doi tuong Subject.")
        self._kiem_tra_chuoi_bat_buoc(mon.id, "Ma mon hoc")
        self._kiem_tra_chuoi_bat_buoc(mon.ten_mon, "Ten mon hoc")
        if self.tim_mon(mon.id) is not None:
            raise ValueError(f"Ma mon '{mon.id}' da ton tai.")
        self.subjects.append(mon)
        return mon
    def sua_mon(self, ma_mon, ten_mon=None, mo_ta=None):
        """Sua ten/mo ta mon hoc; khong thay the danh sach chu de hien co."""
        mon = self.tim_mon(ma_mon)
        if mon is None:
            raise KeyError(f"Khong tim thay mon '{ma_mon}'.")
        if ten_mon is not None:
            self._kiem_tra_chuoi_bat_buoc(ten_mon, "Ten mon hoc")
            mon.ten_mon = ten_mon.strip()
        if mo_ta is not None:
            if not isinstance(mo_ta, str):
                raise ValueError("Mo ta mon hoc phai la chuoi.")
            mon.mo_ta = mo_ta
        return mon
    def xoa_mon(self, ma_mon):
        """Xoa mon neu mon chua co chu de de tranh mat du lieu lien quan."""
        mon = self.tim_mon(ma_mon)
        if mon is None:
            raise KeyError(f"Khong tim thay mon '{ma_mon}'.")
        if mon.chu_de:
            raise ValueError("Khong the xoa mon hoc dang co chu de.")
        self.subjects.remove(mon)
        return mon
    def them_chu_de(self, chu_de):
        """Them Topic vao dung Subject duoc tham chieu boi subject_id."""
        if not isinstance(chu_de, Topic):
            raise TypeError("Du lieu phai la doi tuong Topic.")
        self._kiem_tra_chuoi_bat_buoc(chu_de.id, "Ma chu de")
        self._kiem_tra_chuoi_bat_buoc(chu_de.ten_chu_de, "Ten chu de")
        if self.tim_chu_de(chu_de.id) is not None:
            raise ValueError(f"Ma chu de '{chu_de.id}' da ton tai.")
        mon = self.tim_mon(chu_de.subject_id)
        if mon is None:
            raise ValueError(f"Mon '{chu_de.subject_id}' khong ton tai.")
        mon.them_chu_de(chu_de)
        return chu_de
    def sua_chu_de(self, ma_chu_de, ten_chu_de=None, ma_mon_moi=None):
        """Sua ten chu de va/hoac chuyen chu de sang mon khac."""
        mon_cu, chu_de = self._tim_mon_chua_chu_de(ma_chu_de)
        if chu_de is None:
            raise KeyError(f"Khong tim thay chu de '{ma_chu_de}'.")

        if ten_chu_de is not None:
            self._kiem_tra_chuoi_bat_buoc(ten_chu_de, "Ten chu de")
            chu_de.ten_chu_de = ten_chu_de.strip()

        if ma_mon_moi is not None and ma_mon_moi != chu_de.subject_id:
            mon_moi = self.tim_mon(ma_mon_moi)
            if mon_moi is None:
                raise ValueError(f"Mon '{ma_mon_moi}' khong ton tai.")
            mon_cu.chu_de.remove(chu_de)
            chu_de.subject_id = ma_mon_moi
            mon_moi.them_chu_de(chu_de)
        return chu_de
    def xoa_chu_de(self, ma_chu_de):
        """Xoa Topic neu chua co cau hoi."""
        mon, chu_de = self._tim_mon_chua_chu_de(ma_chu_de)
        if chu_de is None:
            raise KeyError(f"Khong tim thay chu de '{ma_chu_de}'.")
        if chu_de.cau_hoi:
            raise ValueError("Khong the xoa chu de dang co cau hoi.")
        mon.chu_de.remove(chu_de)
        return chu_de
    def them_cau_hoi(self, cau_hoi):
        """Kiem tra du lieu roi them Question vao dung Topic."""
        if not isinstance(cau_hoi, Question):
            raise TypeError("Du lieu phai la Question hoac lop con cua Question.")
        loi = self._loi_cau_hoi(cau_hoi)
        if loi:
            raise ValueError("Khong the them cau hoi:\n- " + "\n- ".join(loi))
        chu_de = self.tim_chu_de(cau_hoi.topic_id)
        chu_de.them_cau_hoi(cau_hoi)
        return cau_hoi
    def sua_cau_hoi(self, ma_cau_hoi, cau_moi):
        """Thay cau hoi cu bang cau_moi; ma cau hoi phai duoc giu nguyen."""
        mon_cu, chu_de_cu, cau_cu = self._tim_chu_de_chua_cau_hoi(ma_cau_hoi)
        if cau_cu is None:
            raise KeyError(f"Khong tim thay cau hoi '{ma_cau_hoi}'.")
        if not isinstance(cau_moi, Question):
            raise TypeError("Du lieu moi phai la Question hoac lop con cua Question.")
        if cau_moi.id != ma_cau_hoi:
            raise ValueError("Ma cau hoi phai giu nguyen khi cap nhat.")

        loi = self._loi_cau_hoi(cau_moi, bo_qua_id=ma_cau_hoi)
        if loi:
            raise ValueError("Khong the sua cau hoi:\n- " + "\n- ".join(loi))

        chu_de_moi = self.tim_chu_de(cau_moi.topic_id)
        if chu_de_moi is None:
            raise ValueError(f"Chu de '{cau_moi.topic_id}' khong ton tai.")

        vi_tri = chu_de_cu.cau_hoi.index(cau_cu)
        if chu_de_moi is chu_de_cu:
            chu_de_cu.cau_hoi[vi_tri] = cau_moi
        else:
            chu_de_cu.cau_hoi.remove(cau_cu)
            chu_de_moi.cau_hoi.append(cau_moi)
        return cau_moi
    def xoa_cau_hoi(self, ma_cau_hoi):
        """Xoa cau hoi theo ma."""
        _, chu_de, cau_hoi = self._tim_chu_de_chua_cau_hoi(ma_cau_hoi)
        if cau_hoi is None:
            raise KeyError(f"Khong tim thay cau hoi '{ma_cau_hoi}'.")
        chu_de.cau_hoi.remove(cau_hoi)
        return cau_hoi
    def tim_mon(self, id):
        """Tim va tra ve mot Subject theo id; None neu khong co."""
        for mon in self.subjects:
            if mon.id == id:
                return mon
        return None
    def tim_chu_de(self, id):
        """Tim va tra ve mot Topic theo id; None neu khong co."""
        _, chu_de = self._tim_mon_chua_chu_de(id)
        return chu_de