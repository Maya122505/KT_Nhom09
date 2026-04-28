from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# 1. KHOA & MÔN HỌC
class Khoa(models.Model):
    tenKhoa = models.CharField(max_length=255, unique=True, verbose_name="Tên Khoa")

    def __str__(self):
        return self.tenKhoa


class MonHoc(models.Model):
    tenMonHoc = models.CharField(max_length=255, verbose_name="Tên Môn Học")
    khoa = models.ForeignKey(Khoa, on_delete=models.CASCADE, related_name='cac_mon_hoc', verbose_name="Khoa")

    def __str__(self):
        return self.tenMonHoc


# 2. NGƯỜI DÙNG (Tích hợp chuẩn hệ thống Auth, đăng nhập bằng Email)
class NguoiDung(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Địa chỉ Email")
    ho_ten = models.CharField(max_length=255, verbose_name="Họ và tên")

    is_student = models.BooleanField(default=True, verbose_name="Là Người học")
    is_teacher = models.BooleanField(default=False, verbose_name="Là Người dạy")

    khoa = models.ForeignKey(Khoa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khoa")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'ho_ten']

    def __str__(self):
        vai_tro = "Người dạy" if self.is_teacher else "Người học"
        return f"{self.ho_ten or self.email} ({vai_tro})"


# 3. LỚP HỌC (Giải quyết luồng Sinh viên - Môn học - Giảng viên)
class LopHoc(models.Model):
    maLop = models.CharField(max_length=50, unique=True, help_text="VD: INT1306_01", verbose_name="Mã Lớp")
    monHoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE, related_name='cac_lop_hoc', verbose_name="Môn Học")

    giangVien = models.ForeignKey(
        NguoiDung,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cac_lop_giang_day',
        limit_choices_to={'is_teacher': True},
        verbose_name="Giảng Viên"
    )

    danhSachSinhVien = models.ManyToManyField(
        NguoiDung,
        related_name='cac_lop_dang_hoc',
        limit_choices_to={'is_student': True},
        blank=True,
        verbose_name="Danh Sách Sinh Viên"
    )

    def __str__(self):
        return f"{self.maLop} - {self.monHoc.tenMonHoc}"


# 4. NGÂN HÀNG CÂU HỎI & CÂU HỎI & LỰA CHỌN
class NganHangCauHoi(models.Model):
    tenNganHang = models.CharField(max_length=255, verbose_name="Tên Ngân Hàng")
    monHoc = models.OneToOneField(MonHoc, on_delete=models.CASCADE, verbose_name="Môn Học")

    nguoiQuanLy = models.ForeignKey(
        NguoiDung,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_teacher': True},
        related_name='cac_ngan_hang_quan_ly',
        verbose_name="Người Quản Lý"
    )

    def __str__(self):
        return self.tenNganHang


class CauHoi(models.Model):
    nganHang = models.ForeignKey(NganHangCauHoi, on_delete=models.CASCADE, related_name='cac_cau_hoi',
                                 verbose_name="Ngân Hàng Câu Hỏi")
    noiDungCauHoi = models.TextField(verbose_name="Nội Dung Câu Hỏi")

    nguoiTao = models.ForeignKey(
        NguoiDung,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_teacher': True},
        verbose_name="Người Tạo"
    )

    def __str__(self):
        return self.noiDungCauHoi[:50]


class LuaChon(models.Model):
    cauHoi = models.ForeignKey(CauHoi, on_delete=models.CASCADE, related_name='cac_lua_chon', verbose_name="Câu Hỏi")
    noiDungLuaChon = models.TextField(verbose_name="Nội Dung Lựa Chọn")
    dapAnDung = models.BooleanField(default=False, verbose_name="Đáp Án Đúng")

    def __str__(self):
        return self.noiDungLuaChon


# 5. ĐỀ THI
class DeThi(models.Model):
    TRANG_THAI_CHOICES = [
        ('BAN_NHAP', 'Bản nháp'),
        ('DA_CONG_BO', 'Đã công bố'),
        ('DANG_THI', 'Đang diễn ra'),
        ('KET_THUC', 'Đã kết thúc'),
        ('HUY', 'Đã hủy'),
    ]

    tenDeThi = models.CharField(max_length=255, verbose_name="Tên Đề Thi")
    lopHoc = models.ForeignKey(LopHoc, on_delete=models.CASCADE, related_name='cac_de_thi', verbose_name="Lớp Học")

    # Khung thời gian và giới hạn
    thoiGianBatDau = models.DateTimeField(verbose_name="Thời Gian Bắt Đầu")
    thoiGianKetThuc = models.DateTimeField(verbose_name="Thời Gian Kết Thúc")
    thoiGianLamBai = models.IntegerField(help_text="Số phút làm bài", verbose_name="Thời Gian Làm Bài (Phút)")
    soLanLamToiDa = models.IntegerField(default=1, verbose_name="Số Lần Làm Tối Đa")

    # Cấu hình tính năng
    matKhauDeThi = models.CharField(max_length=50, null=True, blank=True, help_text="Bỏ trống nếu không cần mật khẩu",
                                    verbose_name="Mật Khẩu Đề Thi")
    choPhepXemKetQua = models.BooleanField(default=True,
                                           help_text="Cho phép sinh viên xem chi tiết đúng/sai sau khi thi",
                                           verbose_name="Cho Phép Xem Kết Quả")
    trangThai = models.CharField(max_length=20, choices=TRANG_THAI_CHOICES, default='BAN_NHAP',
                                 verbose_name="Trạng Thái")

    # Liên kết dữ liệu
    danhSachCauHoi = models.ManyToManyField(CauHoi, related_name='cac_de_thi', verbose_name="Danh Sách Câu Hỏi")
    nguoiTao = models.ForeignKey(
        NguoiDung,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_teacher': True},
        related_name='cac_de_thi_da_tao',
        verbose_name="Người Tạo"
    )

    def __str__(self):
        return f"{self.tenDeThi} ({self.get_trangThai_display()})"


# 6. KẾT QUẢ THI
class KetQuaThi(models.Model):
    sinhVien = models.ForeignKey(NguoiDung, on_delete=models.CASCADE, limit_choices_to={'is_student': True},
                                 verbose_name="Sinh Viên")
    deThi = models.ForeignKey(DeThi, on_delete=models.CASCADE, verbose_name="Đề Thi")

    diemSo = models.FloatField(null=True, blank=True, verbose_name="Điểm Số")
    thoiGianBatDau = models.DateTimeField(default=timezone.now, verbose_name="Thời Gian Bắt Đầu Làm")
    thoiGianNopBai = models.DateTimeField(null=True, blank=True, verbose_name="Thời Gian Nộp Bài")

    def __str__(self):
        return f"{self.sinhVien.ho_ten} - {self.deThi.tenDeThi}"


class ChiTietBaiLam(models.Model):
    ketQua = models.ForeignKey(KetQuaThi, on_delete=models.CASCADE, related_name='chi_tiet', verbose_name="Kết Quả Thi")
    cauHoi = models.ForeignKey(CauHoi, on_delete=models.CASCADE, verbose_name="Câu Hỏi")
    luaChonDaChon = models.ForeignKey(LuaChon, on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name="Lựa Chọn Đã Chọn")