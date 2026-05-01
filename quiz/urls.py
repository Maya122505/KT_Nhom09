from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # 1. Xác thực (Authentication)
    path('login/', views.user_login, name='login'),
    path('dang-ky/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('khoi-phuc-mat-khau/', views.recover_password, name='recover_password'),

    # 2. Trang chủ
    path('', views.trang_chu, name='trang_chu'),
    path('trang-chu/', views.trang_chu, name='trang_chu'),

    # 3. Luồng của Người Học (Sinh viên)
    path('thuc-hien-de-thi/', views.thuc_hien_de_thi, name='danh_sach_de_thi'),
    path('xac-nhan-thi/<int:ma_de_thi>/', views.xac_nhan_thi, name='xac_nhan_thi'),
    path('bat-dau-thi/<int:ma_de_thi>/', views.bat_dau_thi, name='bat_dau_thi'),
    path('hien-thi-de/<int:ma_ket_qua>/', views.hien_thi_de_thi, name='hien_thi_de_thi'),
    path('nop-bai/<int:ma_ket_qua>/', views.nop_bai, name='nop_bai'),
    path('tra-cuu-ket-qua/', views.tra_cuu_ket_qua, name='tra_cuu_ket_qua'),
    path('xem-lai-bai-lam/<int:ma_ket_qua>/', views.xem_lai_bai_lam, name='xem_lai_bai_lam'),
    path('api/luu-nhap/<int:ma_ket_qua>/', views.api_luu_nhap, name='api_luu_nhap'),
    path('api/luu-nhap/<int:ma_ket_qua>/', views.api_luu_nhap, name='api_luu_nhap'),
]
