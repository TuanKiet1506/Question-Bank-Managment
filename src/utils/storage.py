# -*- coding: utf-8 -*-
"""
Tiện ích đọc/ghi dữ liệu.

Chức năng:
    - load(duong_dan): đọc file JSON -> dựng lại cây đối tượng QuestionBank
    - save(bank, duong_dan): ghi cây đối tượng QuestionBank ra file JSON
"""
import json
from pathlib import Path

# Import các lớp nền tảng từ entities và question_bank
try:
    from src.models.entities import Subject, Topic, tao_cau_hoi_tu_dict
    from src.services.question_bank import QuestionBank
except ModuleNotFoundError:
    from models.entities import Subject, Topic, tao_cau_hoi_tu_dict
    from services.question_bank import QuestionBank


def load(duong_dan):
    """
    Đọc dữ liệu từ file JSON và tái tạo lại toàn bộ cấu trúc cây đối tượng QuestionBank.

    An toàn với các tình huống hỏng dữ liệu (không làm dừng ứng dụng):
        - File bị xóa hoặc rỗng  -> tự tạo lại file cấu trúc mặc định, trả về ngân hàng rỗng.
        - File sai cú pháp JSON  -> GIỮ NGUYÊN file (để khôi phục), trả về ngân hàng rỗng.

    Tham số:
        duong_dan (str hoặc Path): Đường dẫn tới file JSON nguồn.

    Trả về:
        QuestionBank: Đối tượng quản lý toàn bộ ngân hàng câu hỏi sau khi dựng cây.
    """
    path = Path(duong_dan)

    noi_dung = None
    if path.exists():
        try:
            noi_dung = path.read_text(encoding='utf-8').strip()
        except OSError:
            noi_dung = None

    # File bị xóa hoặc rỗng -> tạo lại cấu trúc mặc định rồi trả về ngân hàng rỗng.
    if not noi_dung:
        save(QuestionBank(), path)
        return QuestionBank()

    # File có nội dung nhưng sai cú pháp JSON -> không ghi đè, trả về ngân hàng rỗng.
    try:
        data = json.loads(noi_dung)
    except json.JSONDecodeError:
        return QuestionBank()

    bank = QuestionBank()
    
    # 1. Khởi tạo và thêm các Môn học (Subjects) vào ngân hàng
    for s_dict in data.get('subjects', []):
        subject_obj = Subject.from_dict(s_dict)
        bank.subjects.append(subject_obj)
        
    # 2. Khởi tạo Chủ đề (Topics) và gắn vào đúng Môn học tương ứng
    for t_dict in data.get('topics', []):
        topic_obj = Topic.from_dict(t_dict)
        mon = bank.tim_mon(topic_obj.subject_id)
        if mon is not None:
            mon.them_chu_de(topic_obj)
            
    # 3. Khởi tạo Câu hỏi (Questions) thông qua hàm factory và gắn vào đúng Chủ đề tương ứng
    for q_dict in data.get('questions', []):
        cau_hoi_obj = tao_cau_hoi_tu_dict(q_dict)
        chu_de = bank.tim_chu_de(cau_hoi_obj.topic_id)
        if chu_de is not None:
            chu_de.them_cau_hoi(cau_hoi_obj)
            
    return bank


def save(bank, duong_dan):
    """
    Chuyển đổi toàn bộ cây đối tượng trong QuestionBank thành danh sách phẳng và ghi ra file JSON.
    
    Tham số:
        bank (QuestionBank): Đối tượng quản lý ngân hàng câu hỏi hiện tại.
        duong_dan (str hoặc Path): Đường dẫn file JSON cần lưu.
    """
    subjects_list = []
    topics_list = []
    questions_list = []
    
    # Duyệt qua các cấp để trích xuất dữ liệu dạng dictionary (.to_dict())
    for mon in bank.subjects:
        subjects_list.append(mon.to_dict())
        for cd in mon.chu_de:
            topics_list.append(cd.to_dict())
            for cau in cd.cau_hoi:
                questions_list.append(cau.to_dict())
                
    data = {
        'subjects': subjects_list,
        'topics': topics_list,
        'questions': questions_list,
        'exams': [],
        'results': []
    }
    
    path = Path(duong_dan)
    # Tự động tạo thư mục chứa nếu chưa tồn tại
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =============================================================
# NHẬP / XUẤT NGÂN HÀNG CÂU HỎI TỪ FILE TXT (theo format quy ước)
# -------------------------------------------------------------
# Mỗi câu cách nhau bằng 1 dòng trống. Cấu trúc một câu:
#   [Q01] T01 | De | 1 [| loai]      <- tiêu đề: mã | chủ đề | mức độ | điểm | loại
#   Nội dung câu hỏi                 <- dòng ngay sau tiêu đề
#   * phương án đúng                 <- '*' đúng, '-' sai (single/multiple)
#   - phương án sai
#   = đáp án                         <- '=' cho câu điền khuyết (fill)
# Loại mặc định là 'single' nếu bỏ trống. Mã phương án (O1, O2...) tự sinh.
# =============================================================

def _parse_block_txt(lines):
    """Phân tích một khối câu hỏi TXT -> dict; ném ValueError nếu sai format."""
    dong = [l for l in lines if l.strip() != ""]
    if not dong:
        raise ValueError("khối câu hỏi rỗng")

    header = dong[0].strip()
    if not (header.startswith("[") and "]" in header):
        raise ValueError("thiếu dòng tiêu đề dạng [mã] chủ_đề | mức_độ | điểm")
    ma = header[1:header.index("]")].strip()
    phan = [p.strip() for p in header[header.index("]") + 1:].split("|")]
    if len(phan) < 3 or not phan[0]:
        raise ValueError("tiêu đề thiếu thông tin (cần: chủ_đề | mức_độ | điểm)")
    topic_id, muc_do, diem_str = phan[0], phan[1], phan[2]
    loai = phan[3] if len(phan) >= 4 and phan[3] else "single"
    try:
        diem = float(diem_str)
    except ValueError:
        raise ValueError(f"điểm '{diem_str}' không phải số")

    if len(dong) < 2:
        raise ValueError("thiếu nội dung câu hỏi")
    noi_dung = dong[1].strip()

    options = []
    for stt, l in enumerate(dong[2:], start=1):
        s = l.strip()
        dau, text = s[0], s[1:].strip()
        if loai == "fill":
            if dau != "=":
                raise ValueError("câu fill chỉ dùng dấu '=' cho đáp án")
            options.append({"id": f"O{stt}", "noi_dung": text, "is_dung": True})
        else:
            if dau == "*":
                options.append({"id": f"O{stt}", "noi_dung": text, "is_dung": True})
            elif dau == "-":
                options.append({"id": f"O{stt}", "noi_dung": text, "is_dung": False})
            else:
                raise ValueError(f"phương án phải bắt đầu bằng '*' hoặc '-': {s[:20]}")

    return {
        "id": ma, "topic_id": topic_id, "noi_dung": noi_dung,
        "muc_do": muc_do, "loai_cau": loai, "diem": diem, "options": options,
    }


def import_txt(duong_dan, bank):
    """Đọc file TXT theo format quy ước và thêm câu hỏi vào ``bank``.

    Trả về: (so_cau_them, danh_sach_loi). Câu nào lỗi sẽ bị bỏ qua và ghi vào
    danh_sach_loi kèm số dòng, các câu hợp lệ vẫn được thêm bình thường.
    """
    dong = Path(duong_dan).read_text(encoding="utf-8").splitlines()

    # Tách thành các khối, ghi nhớ số dòng bắt đầu để báo lỗi.
    khoi, hien_tai, so_dong_bd = [], [], 1
    for i, l in enumerate(dong, start=1):
        if l.strip() == "":
            if hien_tai:
                khoi.append((so_dong_bd, hien_tai)); hien_tai = []
        else:
            if not hien_tai:
                so_dong_bd = i
            hien_tai.append(l)
    if hien_tai:
        khoi.append((so_dong_bd, hien_tai))

    them, loi = 0, []
    for so_dong, lines in khoi:
        try:
            cau = tao_cau_hoi_tu_dict(_parse_block_txt(lines))
            bank.them_cau_hoi(cau)
            them += 1
        except (ValueError, KeyError) as e:
            loi.append(f"Dòng {so_dong}: {e}")
    return them, loi


def export_txt(bank, duong_dan):
    """Xuất toàn bộ ngân hàng ra file TXT theo đúng format có thể tái nhập."""
    out = []
    for mon in bank.subjects:
        for cd in mon.chu_de:
            for cau in cd.cau_hoi:
                loai = getattr(cau, "LOAI", "single")
                header = f"[{cau.id}] {cau.topic_id} | {cau.muc_do} | {cau.diem:g}"
                if loai != "single":
                    header += f" | {loai}"
                out.append(header)
                out.append(cau.noi_dung)
                if loai == "fill":
                    out.extend(f"= {o.noi_dung}" for o in cau.options if o.is_dung)
                else:
                    out.extend(f"{'*' if o.is_dung else '-'} {o.noi_dung}" for o in cau.options)
                out.append("")   # dòng trống ngăn cách câu
    path = Path(duong_dan)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    return path


if __name__ == "__main__":
    # Chạy thử nhanh: đọc dữ liệu mẫu rồi báo số liệu đã nạp.
    duong_dan = Path("data/samples/question_bank_sample.json")
    bank = load(duong_dan)
    so_cau = sum(len(cd.cau_hoi) for mon in bank.subjects for cd in mon.chu_de)
    print(f"Tải dữ liệu thành công: {len(bank.subjects)} môn, {so_cau} câu hỏi.")