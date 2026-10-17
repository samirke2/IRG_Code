[app]
title = IRG Keygen
package.name = irgkeygen
package.domain = org.irgkeygen

source.dir = .
# ttf مهمة: بدونها لن يدخل الخط العربي Sahel.ttf في الـ APK
source.include_exts = py,png,ttf
source.exclude_dirs = bin, .buildozer, venv, __pycache__, .git, .github
source.exclude_patterns = *.pem, *.csv, *.log

version = 1.0

# python-bidi يجب أن تبقى 0.4.2 (نقية بايثون): الإصدارات الأحدث مكتوبة بـ Rust ولا تعمل على أندرويد
requirements = python3,kivy==2.3.0,arabic-reshaper==3.0.1,python-bidi==0.4.2,six,future

orientation = portrait
fullscreen = 0

# فعّلهما فقط بعد إضافة icon.png و presplash.png إلى المستودع
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png
presplash.color = #0E2623

android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = False

p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
