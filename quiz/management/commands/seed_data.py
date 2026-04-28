import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from quiz.models import (
    Khoa, MonHoc, NguoiDung, LopHoc, NganHangCauHoi,
    CauHoi, LuaChon, DeThi, KetQuaThi, ChiTietBaiLam
)


class Command(BaseCommand):
    help = 'Tạo bộ dữ liệu test hoàn hảo cho kịch bản sinh viên Nguyễn Thị Lê Uyên'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Đang dọn dẹp dữ liệu cũ (Giữ lại Admin)..."))
        ChiTietBaiLam.objects.all().delete()
        KetQuaThi.objects.all().delete()
        DeThi.objects.all().delete()
        LuaChon.objects.all().delete()
        CauHoi.objects.all().delete()
        NganHangCauHoi.objects.all().delete()
        LopHoc.objects.all().delete()
        MonHoc.objects.all().delete()
        NguoiDung.objects.filter(is_superuser=False).delete()
        Khoa.objects.all().delete()

        now = timezone.now()

        # ==========================================
        # 1. TẠO KHOA & MÔN HỌC
        # ==========================================
        khoa_tkth = Khoa.objects.create(tenKhoa="Thống Kê Tin Học")
        danh_sach_ten_mon = ["Cơ sở dữ liệu", "Kiểm thử phần mềm", "Cơ sở lập trình bằng Python"]
        mon_hocs = [MonHoc.objects.create(tenMonHoc=ten, khoa=khoa_tkth) for ten in danh_sach_ten_mon]

        # ==========================================
        # 2. TẠO GIẢNG VIÊN & SINH VIÊN (Uyên)
        # ==========================================
        giang_vien = NguoiDung.objects.create_user(
            username="giangvien@gmail.com", email="giangvien@gmail.com", password="123",
            ho_ten="TS. Trần Văn Bình", is_teacher=True, is_student=False, khoa=khoa_tkth
        )

        sinh_vien_uyen = NguoiDung.objects.create_user(
            username="uyenntl@gmail.com", email="uyenntl@gmail.com", password="123",
            ho_ten="Nguyễn Thị Lê Uyên", is_teacher=False, is_student=True, khoa=khoa_tkth
        )

        # ==========================================
        # 3. TẠO NGÂN HÀNG CÂU HỎI (Dữ liệu thực tế)
        # ==========================================
        data_cau_hoi = {
            "Cơ sở dữ liệu": [
                ("Lệnh nào dùng để thêm dữ liệu vào bảng?", "INSERT INTO", "ADD DATA", "UPDATE", "CREATE ROW"),
                ("Khóa chính (Primary Key) có đặc điểm gì?", "Duy nhất và không được NULL", "Chỉ được chứa số",
                 "Có thể trùng lặp", "Chỉ dùng cho bảng phụ"),
                ("Phép JOIN nào giữ lại tất cả các bản ghi của bảng bên trái?", "LEFT JOIN", "INNER JOIN", "RIGHT JOIN",
                 "CROSS JOIN"),
            ],
            "Kiểm thử phần mềm": [
                ("Mục đích chính của Kiểm thử là gì?", "Tìm ra lỗi (bug) trong phần mềm", "Sửa lỗi code",
                 "Viết tài liệu hệ thống", "Tối ưu hóa database"),
                ("Đâu là kỹ thuật kiểm thử hộp đen?", "Phân tích giá trị biên", "Kiểm thử đường dẫn",
                 "Kiểm thử điều kiện", "Phân tích mã nguồn"),
                ("Unit Test thường do ai thực hiện?", "Lập trình viên (Developer)", "Khách hàng", "Quản lý dự án",
                 "Chuyên viên BA"),
            ],
            "Cơ sở lập trình bằng Python": [
                ("Cách khai báo một hàm trong Python?", "def ten_ham():", "function ten_ham():", "void ten_ham():",
                 "create ten_ham():"),
                ("Kiểu dữ liệu nào lưu trữ theo cặp Key-Value?", "Dictionary", "List", "Tuple", "Set"),
                ("Đâu là cú pháp đúng để in ra màn hình?", "print('Hello')", "echo('Hello')", "console.log('Hello')",
                 "write('Hello')"),
            ]
        }

        ngan_hang_dict = {}
        for mon in mon_hocs:
            nh = NganHangCauHoi.objects.create(tenNganHang=f"Ngân hàng {mon.tenMonHoc}", monHoc=mon,
                                               nguoiQuanLy=giang_vien)
            ngan_hang_dict[mon.tenMonHoc] = nh

            cau_hoi_mau = data_cau_hoi[mon.tenMonHoc]
            for i in range(15):
                cau_mau = cau_hoi_mau[i % 3]
                ch = CauHoi.objects.create(nganHang=nh, noiDungCauHoi=f"{cau_mau[0]} (Biến thể {i + 1})",
                                           nguoiTao=giang_vien)

                dap_ans = [(cau_mau[1], True), (cau_mau[2], False), (cau_mau[3], False), (cau_mau[4], False)]
                random.shuffle(dap_ans)
                for noidung_da, is_dung in dap_ans:
                    LuaChon.objects.create(cauHoi=ch, noiDungLuaChon=noidung_da, dapAnDung=is_dung)

        # ==========================================
        # 4. TẠO LỚP HỌC (Uyên tham gia tất cả các môn)
        # ==========================================
        lop_hocs = []
        for mon in mon_hocs:
            lop = LopHoc.objects.create(maLop=f"{mon.tenMonHoc}_01", monHoc=mon, giangVien=giang_vien)
            lop.danhSachSinhVien.add(sinh_vien_uyen)
            lop_hocs.append(lop)

        # ==========================================
        # 5. TẠO ĐỀ THI (CÓ THÊM MẬT KHẨU)
        # ==========================================

        # Cập nhật hàm tạo đề để nhận thêm tham số mat_khau
        def tao_de_thi(lop, ten_de, trang_thai, thoi_gian_lam, so_lan_lam, thoi_gian_bat_dau, thoi_gian_ket_thuc,
                       mat_khau=""):
            de = DeThi.objects.create(
                tenDeThi=ten_de,
                lopHoc=lop,
                thoiGianBatDau=thoi_gian_bat_dau,
                thoiGianKetThuc=thoi_gian_ket_thuc,
                thoiGianLamBai=thoi_gian_lam,
                soLanLamToiDa=so_lan_lam,
                matKhauDeThi=mat_khau,  # Nhận mật khẩu tại đây
                choPhepXemKetQua=True,
                trangThai=trang_thai,
                nguoiTao=giang_vien
            )
            nh = ngan_hang_dict[lop.monHoc.tenMonHoc]
            tat_ca_cau_hoi = list(nh.cac_cau_hoi.all())
            de.danhSachCauHoi.add(*random.sample(tat_ca_cau_hoi, random.randint(5, 10)))
            return de

        lop_csdl = lop_hocs[0]
        lop_ktpm = lop_hocs[1]
        lop_python = lop_hocs[2]

        # --- A. 3 ĐỀ ĐANG MỞ (DANG_THI) ---
        tao_de_thi(lop_csdl, "Bài tập chương 1 - Cơ sở dữ liệu", 'DANG_THI', 15, 3, now - timedelta(days=1),
                   now + timedelta(days=5))
        tao_de_thi(lop_ktpm, "Bài tập thực hành - Kiểm thử phần mềm", 'DANG_THI', 30, 5, now - timedelta(hours=2),
                   now + timedelta(days=7))

        # THÊM MỚI: 1 đề Python đang mở và CÓ PASS "123456"
        tao_de_thi(lop_python, "Kiểm tra định kỳ - Lập trình Python", 'DANG_THI', 20, 2, now - timedelta(minutes=30),
                   now + timedelta(days=2), mat_khau="123456")

        # --- B. 2 ĐỀ ĐÃ QUÁ HẠN (KET_THUC) ---
        tao_de_thi(lop_python, "Kỳ thi giữa kỳ - Lập trình Python", 'KET_THUC', 45, 1, now - timedelta(days=10),
                   now - timedelta(days=2))
        tao_de_thi(lop_csdl, "Kỳ thi thực hành - Cơ sở dữ liệu", 'KET_THUC', 60, 1, now - timedelta(days=15),
                   now - timedelta(days=5))

        # --- C. 2 ĐỀ ĐÃ ĐÓNG (BAN_NHAP / HUY) ---
        tao_de_thi(lop_ktpm, "Kỳ thi cuối kỳ - Kiểm thử phần mềm", 'BAN_NHAP', 90, 1, now + timedelta(days=10),
                   now + timedelta(days=11))
        tao_de_thi(lop_python, "Bài tập nâng cao - Lập trình Python", 'HUY', 20, 2, now - timedelta(days=1),
                   now + timedelta(days=5))

        self.stdout.write(self.style.SUCCESS("\n🎉 TẠO KỊCH BẢN TEST CHO SINH VIÊN THÀNH CÔNG! 🎉"))
        self.stdout.write(self.style.WARNING("=== TÀI KHOẢN ĐĂNG NHẬP ==="))
        self.stdout.write("👨‍🎓 Sinh viên: uyenntl@gmail.com | Pass: 123")
        self.stdout.write("👨‍🏫 Giảng viên: giangvien@gmail.com | Pass: 123")
        self.stdout.write(self.style.ERROR("🔑 Mật khẩu bài thi Python: 123456"))
        self.stdout.write(self.style.WARNING("==========================="))