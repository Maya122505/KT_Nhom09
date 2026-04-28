from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db import transaction
from django.db.models import Avg, Count
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import NguoiDung, DeThi, KetQuaThi, LuaChon, ChiTietBaiLam, Khoa, MonHoc, LopHoc, NganHangCauHoi, CauHoi


# ==========================================
# 1. AUTHENTICATION (Chuẩn Django)
# ==========================================
def user_login(request):
    if request.method == 'POST':
        email_input = request.POST.get('email')
        matkhau_input = request.POST.get('password')

        # Xác thực tài khoản
        user = authenticate(request, email=email_input, password=matkhau_input)

        if user is not None:

            # Nếu là Sinh viên / Giảng viên -> Cho phép vào Web
            login(request, user)
            return redirect('quiz:trang_chu')
        else:
            return render(request, 'thi_trac_nghiem/login.html', {'error': 'Sai email hoặc mật khẩu!'})

    return render(request, 'thi_trac_nghiem/login.html')


def user_logout(request):
    logout(request)
    return redirect('quiz:login')


def user_register(request):
    if request.method == 'POST':
        ho_ten = (request.POST.get('ho_ten') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        mat_khau = request.POST.get('password') or ''
        nhap_lai = request.POST.get('password2') or ''
        role_choice = request.POST.get('role') or 'hoc'

        if not ho_ten or not email or not mat_khau:
            return render(request, 'thi_trac_nghiem/dang_ky.html', {'error': 'Vui lòng nhập đầy đủ thông tin.'})

        if mat_khau != nhap_lai:
            return render(request, 'thi_trac_nghiem/dang_ky.html', {'error': 'Mật khẩu nhập lại không khớp.'})

        if NguoiDung.objects.filter(email=email).exists():
            return render(request, 'thi_trac_nghiem/dang_ky.html', {'error': 'Email đã tồn tại.'})

        is_teacher = True if role_choice == 'day' else False
        is_student = True if role_choice == 'hoc' else False

        try:
            # Dùng create_user để mật khẩu được mã hóa an toàn
            user = NguoiDung.objects.create_user(
                username=email, email=email, password=mat_khau,
                ho_ten=ho_ten, is_teacher=is_teacher, is_student=is_student
            )
            login(request, user)
            return redirect('quiz:trang_chu')
        except Exception as e:
            return render(request, 'thi_trac_nghiem/dang_ky.html', {'error': f'Lỗi hệ thống: {e}'})

    return render(request, 'thi_trac_nghiem/dang_ky.html')


def recover_password(request):
    return render(request, 'thi_trac_nghiem/khoi_phuc_mat_khau.html')


# ==========================================
# 2. TRANG CHỦ
# ==========================================
@login_required(login_url='quiz:login')
def trang_chu(request):
    user = request.user
    context = {'user': user}

    if user.is_teacher:
        context['tong_de_thi'] = DeThi.objects.filter(nguoiTao=user).count()
        context['de_dang_mo'] = DeThi.objects.filter(nguoiTao=user, trangThai='DANG_THI').count()
        context['tong_sinh_vien'] = NguoiDung.objects.filter(is_student=True).count()
        context['tong_luot_lam'] = KetQuaThi.objects.filter(deThi__nguoiTao=user).count()
    else:
        # Tìm các đề thi thuộc các lớp sinh viên đang học
        cac_de_thi = DeThi.objects.filter(lopHoc__danhSachSinhVien=user)
        context['tong_bai_thi'] = cac_de_thi.count()

        da_lam_count = KetQuaThi.objects.filter(sinhVien=user).values('deThi').distinct().count()
        context['da_lam'] = da_lam_count

        diem_avg = KetQuaThi.objects.filter(sinhVien=user).aggregate(Avg('diemSo'))['diemSo__avg']
        context['diem_tb'] = round(diem_avg, 1) if diem_avg else 0
        context['chua_lam'] = max(0, context['tong_bai_thi'] - da_lam_count)

        context['ds_de_thi'] = cac_de_thi[:5]  # Hiển thị 5 đề mới nhất

    return render(request, 'thi_trac_nghiem/trang_chu.html', context)


# ==========================================
# 3. LUỒNG THI TRẮC NGHIỆM (SINH VIÊN)
# ==========================================
@login_required(login_url='quiz:login')
def thuc_hien_de_thi(request):
    user = request.user
    # Lấy các đề thi thuộc lớp mà sinh viên tham gia
    ds_de_thi = DeThi.objects.filter(lopHoc__danhSachSinhVien=user)

    for de in ds_de_thi:
        # Lấy số lượt đã thi của user này
        so_luot_da_thi = KetQuaThi.objects.filter(sinhVien=user, deThi=de).count()
        de.so_luot_con_lai = max(0, de.soLanLamToiDa - so_luot_da_thi)

    return render(request, 'thi_trac_nghiem/danh_sach_bai_thi.html', {
        'user': user,
        'ds_de_thi': ds_de_thi,
    })


@login_required(login_url='quiz:login')
def xac_nhan_thi(request, ma_de_thi):
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)
    da_lam = KetQuaThi.objects.filter(sinhVien=request.user, deThi=de_thi).count()
    so_lan_con_lai = max(0, de_thi.soLanLamToiDa - da_lam)

    context = {
        'user': request.user,
        'de_thi': de_thi,
        'so_cau': de_thi.danhSachCauHoi.count(),
        'so_lan_con_lai': so_lan_con_lai,
    }
    return render(request, 'thi_trac_nghiem/xac_nhan_thi.html', context)


@login_required(login_url='quiz:login')
def bat_dau_thi(request, ma_de_thi):
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)
    so_lan_da_lam = KetQuaThi.objects.filter(sinhVien=request.user, deThi=de_thi).count()

    if so_lan_da_lam >= de_thi.soLanLamToiDa:
        return HttpResponseForbidden("Bạn đã hết lượt làm bài.")

    # Không cần tính ID thủ công, Django tự động làm
    ket_qua = KetQuaThi.objects.create(
        sinhVien=request.user,
        deThi=de_thi,
        diemSo=0.0,
        thoiGianBatDau=timezone.now()
    )
    return redirect('quiz:hien_thi_de_thi', ma_ket_qua=ket_qua.id)


@login_required(login_url='quiz:login')
def hien_thi_de_thi(request, ma_ket_qua):
    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    de_thi = ket_qua.deThi

    # Lấy danh sách câu hỏi qua trường ManyToMany (danhSachCauHoi)
    danh_sach_cau_hoi = de_thi.danhSachCauHoi.all().prefetch_related('cac_lua_chon')

    return render(request, 'thi_trac_nghiem/lam_bai.html', {
        'ket_qua': ket_qua,
        'de_thi': de_thi,
        'danh_sach_cau_hoi': danh_sach_cau_hoi,
    })


@login_required(login_url='quiz:login')
def nop_bai(request, ma_ket_qua):
    if request.method != 'POST': return redirect('quiz:trang_chu')

    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    de_thi = ket_qua.deThi
    tong_so_cau = de_thi.danhSachCauHoi.count()
    diem_moi_cau = 10.0 / tong_so_cau if tong_so_cau > 0 else 0
    so_cau_dung = 0

    with transaction.atomic():
        for key, value in request.POST.items():
            if key.startswith('cauhoi_'):
                cau_hoi_id = int(key.split('_')[1])
                lua_chon_id = int(value)

                cau_hoi = get_object_or_404(CauHoi, pk=cau_hoi_id)
                lua_chon = get_object_or_404(LuaChon, pk=lua_chon_id)

                ChiTietBaiLam.objects.create(
                    ketQua=ket_qua,
                    cauHoi=cau_hoi,
                    luaChonDaChon=lua_chon
                )
                if lua_chon.dapAnDung:
                    so_cau_dung += 1

        ket_qua.diemSo = round(so_cau_dung * diem_moi_cau, 2)
        ket_qua.thoiGianNopBai = timezone.now()
        ket_qua.save()

    return render(request, 'thi_trac_nghiem/ket_qua.html', {'ket_qua': ket_qua})


@login_required(login_url='quiz:login')
def tra_cuu_ket_qua(request):
    ds_ket_qua = KetQuaThi.objects.filter(sinhVien=request.user).order_by('-thoiGianNopBai')
    return render(request, 'thi_trac_nghiem/tra_cuu_ket_qua.html', {'user': request.user, 'ds_ket_qua': ds_ket_qua})


@login_required(login_url='quiz:login')
def xem_lai_bai_lam(request, ma_ket_qua):
    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    chi_tiet = ChiTietBaiLam.objects.filter(ketQua=ket_qua).select_related('cauHoi', 'luaChonDaChon')
    return render(request, 'thi_trac_nghiem/xem_lai_bai.html', {'ket_qua': ket_qua, 'chi_tiet': chi_tiet})


# ==========================================
# 4. LUỒNG QUẢN LÝ (GIẢNG VIÊN)
# ==========================================
@login_required(login_url='quiz:login')
def quan_ly_de_thi(request):
    id_de = request.GET.get('id_de')
    context = {
        'ds_de_thi': DeThi.objects.filter(nguoiTao=request.user),
        'ds_mon': MonHoc.objects.all(),
        'ds_ngan_hang': NganHangCauHoi.objects.filter(nguoiQuanLy=request.user),
        'ds_cau_hoi': [],
        'id_de': id_de,
    }

    if id_de:
        try:
            de_thi = DeThi.objects.get(pk=id_de)
            context['de_thi'] = de_thi
            context['ds_cau_hoi'] = de_thi.danhSachCauHoi.all().prefetch_related('cac_lua_chon')
        except DeThi.DoesNotExist:
            pass

    return render(request, 'thi_trac_nghiem/quan_ly_de_thi.html', context)


@login_required(login_url='quiz:login')
def xoa_de_thi(request, ma_de_thi):
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)
    de_thi.delete()
    messages.success(request, f"Đã xóa thành công đề thi: {de_thi.tenDeThi}")
    return redirect('quiz:quan_ly_de_thi')


@login_required(login_url='quiz:login')
def tao_de_thi_moi(request):
    if request.method == "POST":
        ten_de = request.POST.get('ten_de')
        lop_id = request.POST.get('lop_id')  # Nên gắn vào lớp thay vì môn học
        thoi_gian = request.POST.get('thoi_gian')
        mat_khau = request.POST.get('mat_khau')
        so_lan = request.POST.get('so_lan')

        lop_hoc = get_object_or_404(LopHoc, pk=lop_id)

        DeThi.objects.create(
            tenDeThi=ten_de,
            lopHoc=lop_hoc,
            thoiGianBatDau=timezone.now(),
            thoiGianKetThuc=timezone.now() + timezone.timedelta(days=7),
            thoiGianLamBai=thoi_gian,
            matKhauDeThi=mat_khau,
            soLanLamToiDa=so_lan,
            nguoiTao=request.user
        )
        return redirect('quiz:quan_ly_de_thi')
    return redirect('quiz:quan_ly_de_thi')


@login_required(login_url='quiz:login')
def ngan_hang_cau_hoi(request):
    query = request.GET.get('q', '')
    mon_id = request.GET.get('mon', '')

    ds_mon = MonHoc.objects.all()
    ds_nh = NganHangCauHoi.objects.all()

    if query:
        ds_nh = ds_nh.filter(tenNganHang__icontains=query)
    if mon_id and mon_id != "Tất cả":
        ds_nh = ds_nh.filter(monHoc_id=mon_id)

    return render(request, 'thi_trac_nghiem/ngan_hang_cau_hoi.html', {
        'ds_cau_hoi': ds_nh,
        'ds_mon': ds_mon,
        'query': query,
        'mon_sel': mon_id
    })


@login_required(login_url='quiz:login')
def luu_ngan_hang_moi(request):
    if request.method == 'POST':
        ten_nh = request.POST.get('ten_nh')
        mon_id = request.POST.get('mon_id')

        if ten_nh and mon_id:
            mon_obj = get_object_or_404(MonHoc, pk=mon_id)
            NganHangCauHoi.objects.create(
                tenNganHang=ten_nh,
                monHoc=mon_obj,
                nguoiQuanLy=request.user
            )
    return redirect('quiz:ngan_hang_cau_hoi')


@login_required(login_url='quiz:login')
def ds_bai_thi_da_tao(request):
    ds_bai_thi = DeThi.objects.filter(nguoiTao=request.user)
    return render(request, 'thi_trac_nghiem/ds_bai_thi.html', {'ds_bai_thi': ds_bai_thi})


@login_required(login_url='quiz:login')
def xem_ket_qua_chi_tiet(request, ma_de_thi):
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)
    ds_ket_qua = KetQuaThi.objects.filter(deThi=de_thi).select_related('sinhVien')

    pho_diem = [0] * 11
    for kq in ds_ket_qua:
        diem = int(kq.diemSo) if kq.diemSo is not None else 0
        if 0 <= diem <= 10: pho_diem[diem] += 1

    context = {
        'de_thi': de_thi,
        'ds_ket_qua': ds_ket_qua,
        'pho_diem': pho_diem,
        'tab': request.GET.get('tab', 'list')
    }
    return render(request, 'thi_trac_nghiem/quan_ly_ket_qua.html', context)


@login_required(login_url='quiz:login')
def chi_tiet_bai_lam(request, ma_ket_qua):
    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    chi_tiet = ChiTietBaiLam.objects.filter(ketQua=ket_qua).select_related('cauHoi', 'luaChonDaChon')

    return render(request, 'thi_trac_nghiem/chi_tiet_bai_lam.html', {
        'ket_qua': ket_qua,
        'chi_tiet': chi_tiet
    })