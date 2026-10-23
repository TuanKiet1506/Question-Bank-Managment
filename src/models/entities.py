# -*- coding: utf-8 -*-
"""
Các lớp dữ liệu (entities) của hệ thống - Tuấn Kiệt

Mô hình "chứa nhau" (composition):
    Subject (Môn) -> Topic (Chủ đề) -> Question (Câu hỏi) -> Option (Phương án)

Các loại câu hỏi dùng KẾ THỪA + ĐA HÌNH:
    Question (lớp cha, trừu tượng)
        ├── CauHoiMotDapAn    (single)   - chọn đúng 1 phương án
        ├── CauHoiNhieuDapAn  (multiple) - chọn đúng cả tập phương án đúng
        └── CauHoiDienKhuyet  (fill)     - gõ đúng chuỗi đáp án

Nhờ đa hình, nơi chấm điểm chỉ cần gọi:
        cau.kiem_tra_dap_an(bai_lam)
mà KHÔNG cần biết đó là loại câu nào.

Lưu ý: Exam (Đề thi) và Result (Kết quả) do cài đặt ở phần tạo đề/chấm điểm.
"""


# =============================================================
# 1) OPTION - Phương án trả lời
# =============================================================
class Option:
    """Một phương án của câu hỏi.

    Thuộc tính:
        id       : mã phương án (vd "O1")
        noi_dung : nội dung hiển thị (vd "int")
        is_dung  : True nếu đây là phương án đúng
    """

    def __init__(self, id, noi_dung, is_dung=False):
        self.id = id
        self.noi_dung = noi_dung
        self.is_dung = is_dung

    def to_dict(self):
        """Chuyển object -> dict để lưu ra JSON."""
        return {"id": self.id, "noi_dung": self.noi_dung, "is_dung": self.is_dung}

    @staticmethod
    def from_dict(data):
        """Tạo object Option từ dict đọc được trong JSON."""
        return Option(
            id=data["id"],
            noi_dung=data["noi_dung"],
            is_dung=data.get("is_dung", False),
        )

    def __repr__(self):
        dau = "[x]" if self.is_dung else "[ ]"
        return f"{dau} {self.id}: {self.noi_dung}"


# =============================================================
# 2) QUESTION - Lớp cha cho mọi loại câu hỏi
# =============================================================
class Question:
    """Lớp cha (trừu tượng) của câu hỏi.

    Mỗi lớp con tự định nghĩa hằng LOAI và cách kiem_tra_dap_an().

    Thuộc tính:
        id       : mã câu hỏi (vd "Q01")
        topic_id : thuộc chủ đề nào (vd "T01")
        noi_dung : đề bài
        muc_do   : "De" | "TrungBinh" | "Kho"
        diem     : điểm của câu
        options  : danh sách Option (composition)
    """

    LOAI = "base"  # lớp con sẽ ghi đè: "single" / "multiple" / "fill"

    def __init__(self, id, topic_id, noi_dung, muc_do="De", diem=1.0, options=None):
        self.id = id
        self.topic_id = topic_id
        self.noi_dung = noi_dung
        self.muc_do = muc_do
        self.diem = diem
        # options or [] : nếu không truyền thì tạo danh sách rỗng mới
        self.options = options if options is not None else []

    # ---- Thao tác với phương án ----
    def them_phuong_an(self, option):
        """Thêm một Option vào câu hỏi."""
        self.options.append(option)
        return option

    def dap_an_dung(self):
        """Trả về danh sách các Option được đánh dấu đúng."""
        return [o for o in self.options if o.is_dung]

    # ---- Phần ĐA HÌNH: lớp con bắt buộc cài đặt ----
    def kiem_tra_dap_an(self, bai_lam):
        """So khớp bài làm với đáp án -> True/False.

        Lớp con PHẢI ghi đè. Gọi trực tiếp ở lớp cha sẽ báo lỗi.
        """
        raise NotImplementedError("Lớp con phải cài đặt kiem_tra_dap_an()")

    def cham(self, bai_lam):
        """Chấm câu hỏi: đúng -> trả về self.diem, sai -> 0.0.

        Dùng lại kiem_tra_dap_an() của lớp con (đa hình).
        """
        return self.diem if self.kiem_tra_dap_an(bai_lam) else 0.0

    def kiem_tra_hop_le(self):
        """Kiểm tra câu hỏi có hợp lệ không -> trả về danh sách lỗi (rỗng = hợp lệ).

        Lớp con có thể bổ sung luật riêng.
        """
        loi = []
        if not self.noi_dung or not self.noi_dung.strip():
            loi.append(f"Câu {self.id}: thiếu nội dung.")
        if self.diem <= 0:
            loi.append(f"Câu {self.id}: điểm phải lớn hơn 0.")
        return loi

    # ---- Chuyển đổi dữ liệu ----
    def to_dict(self):
        """Chuyển object -> dict khớp định dạng JSON mẫu."""
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "noi_dung": self.noi_dung,
            "muc_do": self.muc_do,
            "loai_cau": self.LOAI,
            "diem": self.diem,
            "options": [o.to_dict() for o in self.options],
        }

    def __repr__(self):
        return f"<{self.LOAI}> {self.id}: {self.noi_dung} ({self.diem}đ)"


# =============================================================
# 3) CÁC LỚP CON - KẾ THỪA Question
# =============================================================
class CauHoiMotDapAn(Question):
    """Câu hỏi 1 đáp án đúng.

    bai_lam: id của phương án được chọn (một chuỗi), vd "O1".
    """

    LOAI = "single"

    def kiem_tra_dap_an(self, bai_lam):
        dung = self.dap_an_dung()
        return len(dung) == 1 and bai_lam == dung[0].id

    def kiem_tra_hop_le(self):
        loi = super().kiem_tra_hop_le()  # giữ lại luật của lớp cha
        if len(self.dap_an_dung()) != 1:
            loi.append(f"Câu {self.id}: câu 1 đáp án phải có đúng 1 phương án đúng.")
        if len(self.options) < 2:
            loi.append(f"Câu {self.id}: cần ít nhất 2 phương án.")
        return loi


class CauHoiNhieuDapAn(Question):
    """Câu hỏi nhiều đáp án đúng.

    bai_lam: tập/ds id các phương án được chọn, vd ["O1", "O3"].
    Đúng khi chọn CHÍNH XÁC tập phương án đúng (không thừa, không thiếu).
    """

    LOAI = "multiple"

    def kiem_tra_dap_an(self, bai_lam):
        chon = set(bai_lam or [])
        dung = {o.id for o in self.dap_an_dung()}
        return len(dung) > 0 and chon == dung

    def kiem_tra_hop_le(self):
        loi = super().kiem_tra_hop_le()
        if len(self.dap_an_dung()) < 1:
            loi.append(f"Câu {self.id}: cần ít nhất 1 phương án đúng.")
        if len(self.options) < 2:
            loi.append(f"Câu {self.id}: cần ít nhất 2 phương án.")
        return loi


class CauHoiDienKhuyet(Question):
    """Câu hỏi điền khuyết.

    bai_lam: chuỗi người dùng gõ vào, vd "int".
    Các đáp án chấp nhận được lưu trong options có is_dung=True
    (so khớp không phân biệt hoa/thường và khoảng trắng thừa).
    """

    LOAI = "fill"

    def kiem_tra_dap_an(self, bai_lam):
        bl = (bai_lam or "").strip().lower() # Chuẩn hóa chuỗi
        if not bl:
            return False
        return any(bl == o.noi_dung.strip().lower() for o in self.dap_an_dung())

    def kiem_tra_hop_le(self):
        loi = super().kiem_tra_hop_le()
        if len(self.dap_an_dung()) < 1:
            loi.append(f"Câu {self.id}: cần ít nhất 1 đáp án đúng để so khớp.")
        return loi


# ---- "Nhà máy" tạo câu hỏi đúng loại từ dict (dùng khi đọc JSON) ----
_MAP_LOAI = {
    "single": CauHoiMotDapAn,
    "multiple": CauHoiNhieuDapAn,
    "fill": CauHoiDienKhuyet,
}


def tao_cau_hoi_tu_dict(data):
    """Đọc dict -> tạo đúng lớp con câu hỏi dựa vào trường 'loai_cau'.

    Ví dụ khi load JSON chỉ cần gọi hàm này, không cần if/else loại câu.
    """
    loai = data.get("loai_cau", "single")
    lop = _MAP_LOAI.get(loai)
    if lop is None:
        raise ValueError(f"Loại câu hỏi không hợp lệ: {loai}")

    options = [Option.from_dict(o) for o in data.get("options", [])]
    return lop(
        id=data["id"],
        topic_id=data["topic_id"],
        noi_dung=data["noi_dung"],
        muc_do=data.get("muc_do", "De"),
        diem=data.get("diem", 1.0),
        options=options,
    )


# =============================================================
# 4) TOPIC - Chủ đề (chứa nhiều câu hỏi)
# =============================================================
class Topic:
    """Chủ đề thuộc một môn học.

    Thuộc tính:
        id         : mã chủ đề (vd "T01")
        subject_id : thuộc môn nào (vd "S01")
        ten_chu_de : tên chủ đề
        cau_hoi    : danh sách Question (composition)
    """

    def __init__(self, id, subject_id, ten_chu_de, cau_hoi=None):
        self.id = id
        self.subject_id = subject_id
        self.ten_chu_de = ten_chu_de
        self.cau_hoi = cau_hoi if cau_hoi is not None else []

    def them_cau_hoi(self, question):
        self.cau_hoi.append(question)
        return question

    def to_dict(self):
        """Chỉ gồm thông tin của chính chủ đề (danh sách câu hỏi lưu riêng ở JSON).

        """
        return {"id": self.id, "subject_id": self.subject_id, "ten_chu_de": self.ten_chu_de}

    @staticmethod
    def from_dict(data):
        return Topic(
            id=data["id"],
            subject_id=data["subject_id"],
            ten_chu_de=data["ten_chu_de"],
        )

    def __repr__(self):
        return f"Topic {self.id}: {self.ten_chu_de} ({len(self.cau_hoi)} câu)"


# =============================================================
# 5) SUBJECT - Môn học (chứa nhiều chủ đề)
# =============================================================
class Subject:
    """Môn học - gốc của cây dữ liệu.

    Thuộc tính:
        id      : mã môn (vd "S01")
        ten_mon : tên môn học
        mo_ta   : mô tả ngắn
        chu_de  : danh sách Topic (composition)
    """

    def __init__(self, id, ten_mon, mo_ta="", chu_de=None):
        self.id = id
        self.ten_mon = ten_mon
        self.mo_ta = mo_ta
        self.chu_de = chu_de if chu_de is not None else []

    def them_chu_de(self, topic):
        self.chu_de.append(topic)
        return topic

    def to_dict(self):
        return {"id": self.id, "ten_mon": self.ten_mon, "mo_ta": self.mo_ta}

    @staticmethod
    def from_dict(data):
        return Subject(
            id=data["id"],
            ten_mon=data["ten_mon"],
            mo_ta=data.get("mo_ta", ""),
        )

    def __repr__(self):
        return f"Subject {self.id}: {self.ten_mon} ({len(self.chu_de)} chủ đề)"


# =============================================================
# 6) EXAM - Đề thi được sinh ra từ ngân hàng câu hỏi
# =============================================================
class Exam:
    """Một đề thi sinh ra từ QuestionBank theo một ma trận mức độ.

    Phục vụ phần nghiệp vụ tạo đề (services/exam_generator.py).

    Thuộc tính:
        id            : mã đề (vd "E01")
        ten_de        : tên đề thi
        seed          : seed trộn câu/phương án (int hoặc None) -> tái lập được
        matrix        : ma trận yêu cầu, danh sách spec dạng
                        {"muc_do":.., "so_cau":.., "subject_id":.., "topic_id":..}
        danh_sach_cau : danh sách id câu hỏi theo đúng thứ tự trong đề
    """

    def __init__(self, id, ten_de="Đề kiểm tra", seed=None, matrix=None, danh_sach_cau=None):
        self.id = id
        self.ten_de = ten_de
        self.seed = seed
        self.matrix = matrix if matrix is not None else []
        self.danh_sach_cau = danh_sach_cau if danh_sach_cau is not None else []

    def to_dict(self):
        """Chuyển object -> dict để lưu JSON (đủ để tái lập đề)."""
        return {
            "id": self.id,
            "ten_de": self.ten_de,
            "seed": self.seed,
            "matrix": self.matrix,
            "danh_sach_cau": list(self.danh_sach_cau),
        }

    @staticmethod
    def from_dict(data):
        return Exam(
            id=data["id"],
            ten_de=data.get("ten_de", "Đề kiểm tra"),
            seed=data.get("seed"),
            matrix=data.get("matrix", []),
            danh_sach_cau=data.get("danh_sach_cau", []),
        )

    def __repr__(self):
        return f"Exam {self.id}: {self.ten_de} ({len(self.danh_sach_cau)} câu, seed={self.seed})"
