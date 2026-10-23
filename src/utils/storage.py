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


if __name__ == "__main__":
    # Chạy thử nhanh: đọc dữ liệu mẫu rồi báo số liệu đã nạp.
    duong_dan = Path("data/samples/question_bank_sample.json")
    bank = load(duong_dan)
    so_cau = sum(len(cd.cau_hoi) for mon in bank.subjects for cd in mon.chu_de)
    print(f"Tải dữ liệu thành công: {len(bank.subjects)} môn, {so_cau} câu hỏi.")