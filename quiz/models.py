from django.db import models
from django.utils import timezone

# 1. MODEL KHOA & MÔN HỌC
class Khoa(models.Model):
    maKhoa = models.AutoField(primary_key=True, db_column='maKhoa')
    tenKhoa = models.CharField(max_length=255, db_column='tenKhoa')
    class Meta:
        db_table = 'Khoa'
        managed = False

class MonHoc(models.Model):
    maMonHoc = models.AutoField(primary_key=True, db_column='maMonHoc')
    tenMonHoc = models.CharField(max_length=255, db_column='tenMonHoc')
    class Meta:
        db_table = 'MonHoc'
        managed = False
    def __str__(self): return self.tenMonHoc

# 2. MODEL NGƯỜI DÙNG
class NguoiDung(models.Model):
    maNguoiDung = models.AutoField(primary_key=True, db_column='maNguoiDung')
    hoTen = models.CharField(max_length=255, db_column='hoTen')
    email = models.EmailField(max_length=100, unique=True, db_column='email')
    matKhau = models.CharField(max_length=255, db_column='matKhau')
    vaiTro = models.CharField(max_length=50, db_column='vaiTro')
    class Meta:
        db_table = 'NguoiDung'
        managed = False
    def __str__(self): return self.hoTen

# 3. MODEL NGÂN HÀNG CÂU HỎI
class NganHangCauHoi(models.Model):
    maNganHang = models.AutoField(primary_key=True, db_column='maNganHang')
    tenNganHang = models.CharField(max_length=255, db_column='tenNganHang')
    maKhoa = models.ForeignKey(Khoa, on_delete=models.CASCADE, db_column='maKhoa')
    maMonHoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE, db_column='maMonHoc')
    class Meta:
        db_table = 'NganHangCauHoi'
        managed = False

# 4. MODEL CÂU HỎI & LỰA CHỌN
class CauHoi(models.Model):
    maCauHoi = models.AutoField(primary_key=True, db_column='maCauHoi')
    maNganHang = models.ForeignKey(NganHangCauHoi, on_delete=models.CASCADE, db_column='maNganHang')
    noiDungCauHoi = models.TextField(db_column='noiDungCauHoi')
    class Meta:
        db_table = 'CauHoi'
        managed = False

class LuaChon(models.Model):
    maLuaChon = models.IntegerField(primary_key=True, db_column='maLuaChon')
    maCauHoi = models.ForeignKey(CauHoi, on_delete=models.CASCADE, db_column='maCauHoi')
    noiDungLuaChon = models.TextField(db_column='noiDungLuaChon')
    dapAnDung = models.BooleanField(db_column='dapAnDung')
    class Meta:
        db_table = 'LuaChon'
        managed = False

# 5. MODEL ĐỀ THI
class DeThi(models.Model):
    maDeThi = models.AutoField(primary_key=True, db_column='maDeThi')
    tenDeThi = models.CharField(max_length=255, db_column='tenDeThi')
    maMonHoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE, db_column='maMonHoc')
    thoiGian = models.IntegerField(db_column='thoiGian')
    soLanLam = models.IntegerField(db_column='soLanLam')
    trangThai = models.CharField(max_length=20, db_column='trangThai')
    class Meta:
        db_table = 'DeThi'
        managed = False

class DeThi_CauHoi(models.Model):
    # Dùng maCauHoi làm PK tạm thời để tránh lỗi 'id'
    maDeThi = models.ForeignKey(DeThi, on_delete=models.CASCADE, db_column='maDeThi')
    maCauHoi = models.ForeignKey(CauHoi, on_delete=models.CASCADE, db_column='maCauHoi', primary_key=True)
    class Meta:
        db_table = 'DeThi_CauHoi'
        managed = False

# 6. MODEL KẾT QUẢ
class KetQuaThi(models.Model):
    maKetQua = models.IntegerField(primary_key=True, db_column='maKetQua')
    maNguoiHoc = models.ForeignKey(NguoiDung, on_delete=models.CASCADE, db_column='maNguoiHoc')
    maDeThi = models.ForeignKey(DeThi, on_delete=models.CASCADE, db_column='maDeThi')
    diemSo = models.FloatField(null=True, blank=True, db_column='diemSo')
    thoiGianBatDau = models.DateTimeField(default=timezone.now, db_column='thoiGianBatDau')
    thoiGianNopBai = models.DateTimeField(null=True, blank=True, db_column='thoiGianNopBai')
    soLanLam = models.IntegerField(db_column='soLanLam')
    class Meta:
        db_table = 'KetQuaThi'
        managed = False

class ChiTietBaiLam(models.Model):
    # Đổi AutoField thành IntegerField
    maChiTiet = models.IntegerField(primary_key=True, db_column='maChiTiet')
    maKetQua = models.ForeignKey(KetQuaThi, on_delete=models.CASCADE, db_column='maKetQua')
    maCauHoi = models.ForeignKey(CauHoi, on_delete=models.CASCADE, db_column='maCauHoi')
    maLuaChonDaChon = models.ForeignKey(LuaChon, on_delete=models.SET_NULL, null=True, db_column='maLuaChonDaChon')

    class Meta:
        db_table = 'ChiTietBaiLam'
        managed = False

