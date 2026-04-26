from django.contrib import admin
from .models import DeThi, CauHoi, LuaChon, Khoa, MonHoc

# Đăng ký các bảng hiển thị trên web
admin.site.register(DeThi)
admin.site.register(CauHoi)
admin.site.register(LuaChon)
admin.site.register(Khoa)
admin.site.register(MonHoc)