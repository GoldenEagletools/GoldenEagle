# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE AMY Export to EPW | تصدير سنة فعلية إلى EPW  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, year, city, out_dir, site_elev, run
OUTPUTS: epw_path, lat_o, lon_o, tz_o, elev_o, city_o, T_m, GHI_m, report_en, report_ar
"""
import sys
import os

_lib = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "GoldenEagle", "lib")
if _lib not in sys.path:
    sys.path.append(_lib)
import goldeneagle_core as ge
try:
    reload(ge)  # أثناء التطوير فقط: لالتقاط تعديلات النواة دون إعادة تشغيل Rhino
except NameError:
    pass

ge.set_tooltips(ghenv, u'GE AMY Export to EPW', u'تصدير سنة فعلية إلى EPW', u"Creates an EPW weather file for an ACTUAL year you choose (AMY, from hourly NASA POWER data) for any GE Location, to wire into Ladybug's Import EPW.", u'ينشئ ملف طقس EPW لسنة فعلية تختارها (AMY، من بيانات NASA POWER الساعية) لأي موقع من GE Location، لتوصيله بـ Import EPW في Ladybug.',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('year', u'The actual year (2002 up to the last complete year).', u'السنة الفعلية (من 2002 حتى آخر سنة مكتملة).'),
    ('city', u'City name written in the EPW header (optional, English letters only).', u'اسم المدينة المكتوب بترويسة EPW (اختياري، بحروف إنجليزية فقط).'),
    ('out_dir', u'Output folder (optional; default %APPDATA%/GoldenEagle/epw).', u'مجلد الحفظ (اختياري؛ الافتراضي %APPDATA%/GoldenEagle/epw).'),
    ('site_elev', u'Optional site elevation in metres. If given, temperature, pressure and dew point are adjusted from the grid-cell elevation with a simple, unvalidated method (6.5 K/km, standard atmosphere, constant mixing ratio); wind and solar are not adjusted. Leave empty to keep the grid-cell values.', u'ارتفاع الموقع بالمتر (اختياري). إذا أُعطي تُصحَّح الحرارة والضغط ونقطة الندى من ارتفاع الخلية بطريقة بسيطة غير مُتحقَّق منها (6.5 كلفن/كم، الغلاف المعياري، ثبات نسبة الخلط)؛ الرياح والإشعاع لا تُصحَّح. اتركه فارغًا لإبقاء قيم الخلية.'),
    ('run', u'True to execute. The first run for a new year and location downloads two large requests from NASA (the tool may freeze for a while).', u'True للتنفيذ. أول تشغيل لسنة وموقع جديدين يحمّل طلبين كبيرين من NASA (قد تتجمد الأداة فترة).'),
],
[
    ('epw_path', u"Path of the EPW file: wire it to _epw_file of Ladybug's Import EPW.", u'مسار ملف EPW: وصّله بـ _epw_file في Import EPW من Ladybug.'),
    ('lat_o', u"Latitude (for Ladybug's Construct Location).", u'خط العرض (لـ Construct Location في Ladybug).'),
    ('lon_o', u"Longitude (for Ladybug's Construct Location).", u'خط الطول (لـ Construct Location في Ladybug).'),
    ('tz_o', u"Time zone as a UTC offset (for Ladybug's Construct Location).", u'المنطقة الزمنية كفرق عن UTC (لـ Construct Location في Ladybug).'),
    ('elev_o', u'Elevation of the weather-grid cell in metres.', u'ارتفاع خلية الأرصاد بالمتر.'),
    ('city_o', u'City name written in the EPW header.', u'اسم المدينة المكتوب بترويسة EPW.'),
    ('T_m', u'12 monthly mean dry-bulb temperatures of the EPW year (degC), for comparison.', u'12 متوسطًا شهريًا لحرارة الهواء بسنة الـEPW (°م) للمقارنة.'),
    ('GHI_m', u'12 monthly mean daily GHI totals of the EPW year (kWh/m2/day), for comparison.', u'12 متوسطًا شهريًا لمجموع الإشعاع الكلي اليومي بسنة الـEPW (kWh/m2/يوم) للمقارنة.'),
    ('report_en', u'English report with the checks.', u'التقرير الإنجليزي مع الفحوصات.'),
    ('report_ar', u'Arabic report (right-to-left).', u'التقرير العربي (من اليمين لليسار).'),
],
u'AMY to EPW')

epw_path = lat_o = lon_o = tz_o = elev_o = city_o = T_m = GHI_m = None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.export_epw(d, year, out_dir, city, site_elev)
        epw_path, lat_o, lon_o, tz_o, elev_o, city_o = r["epw_path"], r["lat"], r["lon"], r["tz"], r["elev"], r["city"]
        T_m, GHI_m = r["T_m"], r["GHI_m"]
        report_en, report_ar = r["report_en"], r["report_ar"]
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
