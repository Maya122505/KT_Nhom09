from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Trang chủ & Login
    path('', views.trang_chu, name='trang_chu'),
    path('trang-chu/', views.trang_chu, name='trang_chu'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Quản lý đề thi & Ngân hàng
    path('quan-ly-de-thi/', views.quan_ly_de_thi, name='quan_ly_de_thi'),
    path('xoa-de/<int:ma_de_thi>/', views.xoa_de_thi, name='xoa_de_thi'),
    path('ngan-hang-cau-hoi/', views.ngan_hang_cau_hoi, name='ngan_hang_cau_hoi'),
    path('luu-ngan-hang-moi/', views.luu_ngan_hang_moi, name='luu_ngan_hang_moi'),

    # THỰC HIỆN LUỒNG QUẢN LÝ KẾT QUẢ (ẢNH 1 ĐẾN 4)
    path('quan-ly-ket-qua/', views.ds_bai_thi_da_tao, name='ds_bai_thi_da_tao'),
    path('ket-qua/<int:ma_de_thi>/', views.xem_ket_qua_chi_tiet, name='xem_ket_qua_chi_tiet'),
    path('chi-tiet-bai-lam/<int:ma_ket_qua>/', views.chi_tiet_bai_lam, name='chi_tiet_bai_lam'),

    # Giao diện làm bài cho sinh viên
    path('thuc-hien-de-thi/', views.danh_sach_de_thi, name='danh_sach_de_thi'),
    path('hien-thi-de/<int:ma_ket_qua>/', views.hien_thi_de_thi, name='hien_thi_de_thi'),
    path('nop-bai/<int:ma_ket_qua>/', views.nop_bai, name='nop_bai'),
    path('tra-cuu-ket-qua/', views.tra_cuu_ket_qua, name='tra_cuu_ket_qua'),
# Trong quiz/urls.py
    path('quan-ly-ket-qua/', views.ds_bai_thi_da_tao, name='quan_ly_ket_qua'),
# Thêm dòng này vào urlpatterns trong quiz/urls.py
path('xac-nhan-thi/<int:ma_de_thi>/', views.xac_nhan_thi, name='xac_nhan_thi'),
# Trong quiz/urls.py
path('xem-lai-bai-lam/<int:ma_ket_qua>/', views.xem_lai_bai_lam, name='xem_lai_bai_lam'),
path('bat-dau-thi/<int:ma_de_thi>/', views.bat_dau_thi, name='bat_dau_thi'),
]