from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db import transaction
from django.db.models import Avg, Max
from .models import NguoiDung, DeThi, KetQuaThi, DeThi_CauHoi, LuaChon, ChiTietBaiLam,Khoa

# 1. TRANG CHỦ (DASHBOARD)
def trang_chu(request):
    ma_nd = request.session.get('maNguoiDung')
    if not ma_nd:
        return redirect('quiz:login')

    try:
        user = NguoiDung.objects.get(maNguoiDung=ma_nd)
    except NguoiDung.DoesNotExist:
        return redirect('quiz:login')

    ds_de_thi = DeThi.objects.all()
    context = {
        'user': user,
        'ds_de_thi': ds_de_thi,
    }

    if user.vaiTro == 'Giáo viên':
        context['tong_de_thi'] = DeThi.objects.count()
        context['de_dang_mo'] = DeThi.objects.filter(trangThai='Mở').count()
        context['tong_sinh_vien'] = NguoiDung.objects.filter(vaiTro='Học sinh').count()
        context['tong_luot_lam'] = KetQuaThi.objects.count()
    else:
        # SỬA TẠI ĐÂY: Lọc theo user để hết bị số ÂM
        context['tong_bai_thi'] = DeThi.objects.count()
        da_lam_count = KetQuaThi.objects.filter(maNguoiHoc=user).count()
        context['da_lam'] = da_lam_count

        # Tính điểm trung bình chuẩn của cá nhân
        diem_avg = KetQuaThi.objects.filter(maNguoiHoc=user).aggregate(Avg('diemSo'))['diemSo__avg']
        context['diem_tb'] = round(diem_avg, 1) if diem_avg else 0

        # Con số này bây giờ sẽ luôn dương và chuẩn
        context['chua_lam'] = max(0, context['tong_bai_thi'] - da_lam_count)

    return render(request, 'thi_trac_nghiem/trang_chu.html', context)


# 2. XÁC NHẬN TRƯỚC KHI THI
def xac_nhan_thi(request, ma_de_thi):
    # 1. Kiểm tra đăng nhập
    ma_nd = request.session.get('maNguoiDung')
    if not ma_nd:
        return redirect('quiz:login')

    # 2. Lấy người dùng
    nguoi_dung = get_object_or_404(NguoiDung, maNguoiDung=ma_nd)

    # 3. Lấy đề thi
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)

    # 4. Đếm số câu hỏi
    so_cau = DeThi_CauHoi.objects.filter(maDeThi=de_thi).count()

    # 5. Đếm số lần đã làm
    da_lam = KetQuaThi.objects.filter(
        maNguoiHoc=nguoi_dung,
        maDeThi=de_thi
    ).count()

    # 6. Tính số lần còn lại (KHÔNG BAO GIỜ ÂM)
    so_lan_con_lai = max(0, de_thi.soLanLam - da_lam)

    # 7. Trả dữ liệu về giao diện
    context = {
        'de_thi': de_thi,
        'so_cau': so_cau,
        'so_lan_con_lai': so_lan_con_lai,
    }

    return render(request, 'thi_trac_nghiem/xac_nhan_thi.html', context)
# 3. BẮT ĐẦU THI
def bat_dau_thi(request, ma_de_thi):
    ma_nd = request.session.get('maNguoiDung')
    if not ma_nd: return redirect('quiz:login')

    nguoi_dung = get_object_or_404(NguoiDung, maNguoiDung=ma_nd)
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)

    so_lan_da_lam = KetQuaThi.objects.filter(maNguoiHoc=nguoi_dung, maDeThi=de_thi).count()
    if so_lan_da_lam >= de_thi.soLanLam:
        return HttpResponseForbidden("Bạn đã hết lượt làm bài.")

    max_id = KetQuaThi.objects.aggregate(Max('maKetQua'))['maKetQua__max']
    next_id = (max_id + 1) if max_id is not None else 1

    ket_qua = KetQuaThi.objects.create(
        maKetQua=next_id,
        maNguoiHoc=nguoi_dung,
        maDeThi=de_thi,
        diemSo=0.0,
        thoiGianBatDau=timezone.now(),
        soLanLam=so_lan_da_lam + 1
    )
    return redirect('quiz:hien_thi_de_thi', ma_ket_qua=ket_qua.maKetQua)


# 4. GIAO DIỆN LÀM BÀI
def hien_thi_de_thi(request, ma_ket_qua):
    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    de_thi = ket_qua.maDeThi
    # Phải có select_related('maCauHoi') thì mới lấy được nội dung câu hỏi
    danh_sach_cau_hoi = DeThi_CauHoi.objects.filter(maDeThi=de_thi).select_related('maCauHoi')

    return render(request, 'thi_trac_nghiem/lam_bai.html', {
        'ket_qua': ket_qua,
        'de_thi': de_thi,
        'danh_sach_cau_hoi': danh_sach_cau_hoi,  # Tên biến này phải khớp với HTML
    })


# 5. NỘP BÀI
def nop_bai(request, ma_ket_qua):
    if request.method != 'POST': return redirect('quiz:trang_chu')

    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    de_thi = ket_qua.maDeThi
    tong_so_cau = DeThi_CauHoi.objects.filter(maDeThi=de_thi).count()
    diem_moi_cau = 10.0 / tong_so_cau if tong_so_cau > 0 else 0
    so_cau_dung = 0

    with transaction.atomic():
        max_ct = ChiTietBaiLam.objects.aggregate(Max('maChiTiet'))['maChiTiet__max']
        current_id = (max_ct + 1) if max_ct is not None else 1

        for key, value in request.POST.items():
            if key.startswith('cauhoi_'):
                cau_hoi_id = int(key.split('_')[1])
                lua_chon_id = int(value)
                lua_chon = get_object_or_404(LuaChon, pk=lua_chon_id)

                ChiTietBaiLam.objects.create(
                    maChiTiet=current_id,
                    maKetQua=ket_qua,
                    maCauHoi_id=cau_hoi_id,
                    maLuaChonDaChon=lua_chon
                )
                current_id += 1
                if lua_chon.dapAnDung: so_cau_dung += 1

        ket_qua.diemSo = round(so_cau_dung * diem_moi_cau, 2)
        ket_qua.thoiGianNopBai = timezone.now()
        ket_qua.save()

    return render(request, 'thi_trac_nghiem/ket_qua.html', {'ket_qua': ket_qua})


# 6. TRA CỨU & XEM LẠI
def tra_cuu_ket_qua(request):
    ma_nd = request.session.get('maNguoiDung')
    if not ma_nd: return redirect('quiz:login')

    user = get_object_or_404(NguoiDung, maNguoiDung=ma_nd)
    ds_ket_qua = KetQuaThi.objects.filter(maNguoiHoc=user).order_by('-thoiGianNopBai')
    return render(request, 'thi_trac_nghiem/tra_cuu_ket_qua.html', {'user': user, 'ds_ket_qua': ds_ket_qua})


def xem_lai_bai_lam(request, ma_ket_qua):
    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    # Đã bỏ _id để hết lỗi FieldError
    chi_tiet = ChiTietBaiLam.objects.filter(maKetQua=ket_qua).select_related('maCauHoi', 'maLuaChonDaChon')
    return render(request, 'thi_trac_nghiem/xem_lai_bai.html', {'ket_qua': ket_qua, 'chi_tiet': chi_tiet})


# 7. AUTHENTICATION
def user_login(request):
    if request.method == 'POST':
        email_input = request.POST.get('email')
        matkhau_input = request.POST.get('password')
        try:
            user = NguoiDung.objects.get(email=email_input, matKhau=matkhau_input)
            request.session['maNguoiDung'] = user.maNguoiDung
            return redirect('quiz:trang_chu')
        except NguoiDung.DoesNotExist:
            return render(request, 'thi_trac_nghiem/login.html', {'error': 'Sai tài khoản!'})
    return render(request, 'thi_trac_nghiem/login.html')


def user_logout(request):
    request.session.flush()
    return redirect('quiz:login')


def quan_ly_de_thi(request):
    # 1. Lấy tham số id_de từ URL (ví dụ: ?id_de=2)
    id_de = request.GET.get('id_de')

    context = {
        'ds_de_thi': DeThi.objects.all(),
        'ds_mon': MonHoc.objects.all(),
        'ds_khoa': Khoa.objects.all(),
        'ds_ngan_hang': NganHangCauHoi.objects.all(),
    }

    # 2. Nếu có id_de, bốc đúng 5 câu hỏi từ SQL ra
    if id_de:
        de_thi = get_object_or_404(DeThi, pk=id_de)
        # Lấy danh sách câu hỏi thông qua bảng trung gian
        ds_cau_hoi = de_thi.objects.filter(maDeThi=de_thi)

        # Nạp dữ liệu vào context để HTML hiển thị
        context['de_thi'] = de_thi
        context['ds_cau_hoi'] = ds_cau_hoi

    return render(request, 'quan_ly_de_thi.html', context)
def danh_sach_de_thi(request):
    ma_nd = request.session.get('maNguoiDung')
    if not ma_nd: return redirect('quiz:login')

    user = get_object_or_404(NguoiDung, maNguoiDung=ma_nd)
    # Lấy các đề thi đang trạng thái "Mở"
    ds_de_thi = DeThi.objects.filter(trangThai='Mở')

    return render(request, 'thi_trac_nghiem/thuc_hien_de_thi.html', {
        'user': user,
        'ds_de_thi': ds_de_thi
    })
def quan_ly_de_thi(request):
    id_de = request.GET.get('id_de')

    # 1. Tạo context với các dữ liệu nền TRƯỚC
    context = {
        'ds_de_thi': DeThi.objects.all(),
        'ds_mon': MonHoc.objects.all(),
        'ds_khoa': Khoa.objects.all(),
        'ds_ngan_hang': NganHangCauHoi.objects.all(),
        'ds_cau_hoi': [],  # Mặc định để trống, sẽ nạp ở dưới nếu có id_de
        'id_de': id_de,  # Gửi cái này sang để HTML nhận diện đề đang chọn
    }

    if id_de:
        try:
            # 2. Tìm đúng cái đề thi (ID số 1 hoặc 2)
            de_thi = DeThi.objects.get(pk=id_de)
            context['de_thi'] = de_thi

            # 3. LẤY CÂU HỎI VÀ LỰA CHỌN (Phải dùng prefetch_related để lấy câu A, B, C, D)
            # Dùng select_related để lấy nội dung câu hỏi
            # Dùng prefetch_related để lấy các đáp án từ bảng LuaChon
            context['ds_cau_hoi'] = DeThi_CauHoi.objects.filter(maDeThi=de_thi) \
                .select_related('maCauHoi') \
                .prefetch_related('maCauHoi__luachon_set')

        except DeThi.DoesNotExist:
            pass

    return render(request, 'thi_trac_nghiem/quan_ly_de_thi.html', context)
from django.contrib import messages

def xoa_de_thi(request, ma_de_thi):
    # Tìm đề thi theo ID
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)

    # Thực hiện xóa
    de_thi.delete()

    # Hiển thị thông báo thành công
    messages.success(request, f"Đã xóa thành công đề thi: {de_thi.tenDeThi}")

    # Quay lại trang quản lý
    return redirect('quiz:quan_ly_de_thi')


from django.shortcuts import render, get_object_or_404, redirect
from .models import DeThi


# 1. Hàm Tạo & Sửa đề thi (Dùng chung 1 view cho gọn)
def form_de_thi(request, ma_de_thi=None):
    de_thi = None
    if ma_de_thi:
        de_thi = get_object_or_404(DeThi, pk=ma_de_thi)

    if request.method == 'POST':
        ten = request.POST.get('tenDeThi')
        tg = request.POST.get('thoiGian')
        trang_thai = request.POST.get('trangThai')

        if de_thi:  # Nếu có ID thì là Sửa
            de_thi.tenDeThi = ten
            de_thi.thoiGian = tg
            de_thi.trangThai = trang_thai
            de_thi.save()
        else:  # Không có ID thì là Tạo mới
            DeThi.objects.create(tenDeThi=ten, thoiGian=tg, trangThai=trang_thai)

        return redirect('quiz:quan_ly_de_thi')

    return render(request, 'thi_trac_nghiem/form_de_thi.html', {'de_thi': de_thi})


# 2. Hàm Xóa (Cập nhật lại cho chắc chắn)
def xoa_de_thi(request, ma_de_thi):
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)
    de_thi.delete()
    return redirect('quiz:quan_ly_de_thi')


def ngan_hang_cau_hoi(request):
    # Phải có dòng import này bên trong hoặc đầu file
    from .models import NganHangCauHoi, MonHoc, Khoa

    # 1. Định nghĩa các biến lấy từ URL (Phải có dòng này mới hết lỗi Unresolved reference)
    query = request.GET.get('q', '')
    khoa_id = request.GET.get('khoa', '')
    mon_id = request.GET.get('mon', '')

    # 2. Lấy dữ liệu ban đầu
    ds_khoa = Khoa.objects.all()
    ds_mon = MonHoc.objects.all()
    ds_nh = NganHangCauHoi.objects.all()

    # 3. Logic lọc (Sử dụng các biến đã định nghĩa ở trên)
    if query:
        ds_nh = ds_nh.filter(tenNganHang__icontains=query)

    if khoa_id and khoa_id != "Tất cả":
        # Sửa thành khoa_id để khớp với kiểu dữ liệu số từ SQL
        ds_nh = ds_nh.filter(maMonHoc__maKhoa_id=khoa_id)
        ds_mon = ds_mon.filter(maKhoa_id=khoa_id)

    if mon_id and mon_id != "Tất cả":
        ds_nh = ds_nh.filter(maMonHoc_id=mon_id)

    # 4. Gửi dữ liệu sang HTML
    return render(request, 'thi_trac_nghiem/ngan_hang_cau_hoi.html', {
        'ds_cau_hoi': ds_nh,
        'ds_khoa': ds_khoa,
        'ds_mon': ds_mon,
        'query': query,  # Phải gửi lại biến này để ô tìm kiếm không bị trống
        'khoa_sel': khoa_id,
        'mon_sel': mon_id
    })


from django.shortcuts import redirect
from .models import NganHangCauHoi, MonHoc

def luu_ngan_hang_moi(request):
    if request.method == 'POST':
        ten_nh = request.POST.get('ten_nh')
        mon_id = request.POST.get('mon_id')

        if ten_nh and mon_id:
            # Lấy đúng môn học từ SQL
            mon_obj = MonHoc.objects.get(maMonHoc=mon_id)

            # Tạo mới Ngân hàng câu hỏi vào SQL Server
            NganHangCauHoi.objects.create(
                tenNganHang=ten_nh,
                maMonHoc=mon_obj
            )

    # Lưu xong thì quay về trang danh sách
    return redirect('quiz:ngan_hang_cau_hoi')
# Mở file views.py của Uyên ra và thêm hàm này vào:

from django.shortcuts import render, redirect
from .models import DeThi, MonHoc, NganHangCauHoi

def tao_de_thi_moi(request):
    if request.method == "POST":
        # 1. Lấy dữ liệu từ các ô nhập liệu (dựa vào thuộc tính 'name')
        ten_de = request.POST.get('ten_de')
        ten_mon = request.POST.get('ten_mon')
        thoi_gian = request.POST.get('thoi_gian')
        so_cau = request.POST.get('so_cau')
        mat_khau = request.POST.get('mat_khau')
        so_lan = request.POST.get('so_lan')

        # 2. Tìm môn học tương ứng trong SQL
        mon_hoc_obj = MonHoc.objects.get(tenMonHoc=ten_mon)

        # 3. Tạo đề thi mới và lưu vào SQL
        moi_de = DeThi.objects.create(
            tenDeThi=ten_de,
            maMonHoc=mon_hoc_obj,
            thoiGian=thoi_gian,
            matKhau=mat_khau,
            soLanLam=so_lan
            # Trạng thái mặc định sẽ là 'Đang soạn thảo'
        )

        # 4. Sau khi lưu xong, quay lại trang danh sách
        return redirect('quiz:quan_ly_de_thi')


def xem_chi_tiet_de(request, ma_de_thi):
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)
    # Phải dùng DeThi_CauHoi (có gạch dưới) để lấy 5 câu hỏi
    ds_cau_hoi = DeThi_CauHoi.objects.filter(maDeThi=de_thi).select_related('maCauHoi')

    return render(request, 'quan_ly_de_thi.html', {
        'de_thi': de_thi,
        'ds_cau_hoi': ds_cau_hoi,
        'view_mode': 'detail'  # Biến này để ép HTML hiện cái giao diện đẹp kia
    })


# ẢNH 1: Danh sách các bài thi đã tạo
def ds_bai_thi_da_tao(request):
    # Lấy dữ liệu từ SQL
    ds_bai_thi = DeThi.objects.all()
    # TRỎ ĐÚNG VÀO THƯ MỤC TRONG ẢNH CỦA UYÊN
    return render(request, 'thi_trac_nghiem/ds_bai_thi.html', {'ds_bai_thi': ds_bai_thi})


# ẢNH 2 & 3: Danh sách người thi & Phổ điểm
def xem_ket_qua_chi_tiet(request, ma_de_thi):
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)
    ds_ket_qua = KetQuaThi.objects.filter(maDeThi=de_thi).select_related('maNguoiHoc')

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
    # Đã đổi thành thi_trac_nghiem/ luôn nè
    # Sửa lại cho khớp với cái tên file trong danh sách bên trái của Uyên
    return render(request, 'thi_trac_nghiem/quan_ly_ket_qua.html', context)


# ẢNH 4: Chi tiết bài làm của từng cá nhân
def chi_tiet_bai_lam(request, ma_ket_qua):
    ket_qua = get_object_or_404(KetQuaThi, pk=ma_ket_qua)
    chi_tiet = ChiTietBaiLam.objects.filter(maKetQua=ket_qua).select_related('maCauHoi', 'maLuaChonDaChon')

    context = {
        'ket_qua': ket_qua,
        'chi_tiet': chi_tiet
    }
    # Đổi nốt cái này sang thi_trac_nghiem/ cho Uyên luôn
    return render(request, 'thi_trac_nghiem/chi_tiet_bai_lam.html', context)


def xac_nhan_thi(request, ma_de_thi):
    ma_nd = request.session.get('maNguoiDung')
    if not ma_nd:
        return redirect('quiz:login')

    nguoi_dung = get_object_or_404(NguoiDung, maNguoiDung=ma_nd)
    # 1. Tìm đúng cái đề thi mà học sinh vừa bấm vào
    de_thi = get_object_or_404(DeThi, pk=ma_de_thi)

    # 2. Đếm xem đề này có bao nhiêu câu hỏi
    so_cau = DeThi_CauHoi.objects.filter(maDeThi=de_thi).count()
    da_lam = KetQuaThi.objects.filter(maNguoiHoc=nguoi_dung, maDeThi=de_thi).count()
    so_lan_con_lai = max(0, de_thi.soLanLam - da_lam)


    context = {
        'de_thi': de_thi,
        'so_cau': so_cau,
        'so_lan_con_lai': so_lan_con_lai,
    }

    # 4. Trả về giao diện xác nhận thi
    return render(request, 'thi_trac_nghiem/xac_nhan_thi.html', context)
