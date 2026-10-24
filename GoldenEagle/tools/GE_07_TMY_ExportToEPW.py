# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE TMY Export to EPW | تصدير سنة نموذجية إلى EPW  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, y_from, y_to, city, out_dir, site_elev, run
OUTPUTS: epw_path, lat_o, lon_o, tz_o, elev_o, city_o, T_m, GHI_m, years, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE TMY Export to EPW', u'تصدير سنة نموذجية إلى EPW', u"Creates an EPW file for a typical meteorological year (NREL TMY3 method on NASA POWER data) for any GE Location, to wire into Ladybug's Import EPW.", u'ينشئ ملف EPW لسنة نموذجية (طريقة NREL TMY3 على بيانات NASA POWER) لأي موقع من GE Location، لتوصيله بـ Import EPW في Ladybug.',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('y_from', u'First year of the pool (optional; default 2002, the earliest allowed).', u'أول سنة بالحوض (اختياري؛ الافتراضي 2002، أبكر سنة مسموحة).'),
    ('y_to', u'Last year of the pool (optional; default the last complete year).', u'آخر سنة بالحوض (اختياري؛ الافتراضي آخر سنة مكتملة).'),
    ('city', u'City name written in the EPW header (optional, English letters only).', u'اسم المدينة المكتوب بترويسة EPW (اختياري، بحروف إنجليزية فقط).'),
    ('out_dir', u'Output folder (optional; default %APPDATA%/GoldenEagle/epw).', u'مجلد الحفظ (اختياري؛ الافتراضي %APPDATA%/GoldenEagle/epw).'),
    ('site_elev', u'Optional site elevation in metres (simple, unvalidated correction of temperature, pressure and dew point). Leave empty to keep grid-cell values.', u'ارتفاع الموقع بالمتر (اختياري؛ تصحيح بسيط غير مُتحقَّق منه للحرارة والضغط ونقطة الندى). اتركه فارغًا لإبقاء قيم الخلية.'),
    ('run', u'True to execute. The first run for a new location can download many large requests from NASA (the tool may freeze for several minutes).', u'True للتنفيذ. أول تشغيل لموقع جديد قد يحمّل طلبات كبيرة كثيرة من NASA (قد تتجمد الأداة عدة دقائق).'),
],
[
    ('epw_path', u"Path of the TMY EPW file: wire it to _epw_file of Ladybug's Import EPW.", u'مسار ملف EPW النموذجي: وصّله بـ _epw_file في Import EPW من Ladybug.'),
    ('lat_o', u'Latitude.', u'خط العرض.'),
    ('lon_o', u'Longitude.', u'خط الطول.'),
    ('tz_o', u'Time zone as a UTC offset.', u'المنطقة الزمنية كفرق عن UTC.'),
    ('elev_o', u'Elevation written in the header (m).', u'الارتفاع المكتوب بالترويسة (م).'),
    ('city_o', u'City name written in the EPW header.', u'اسم المدينة المكتوب بترويسة EPW.'),
    ('T_m', u'12 monthly mean dry-bulb temperatures of the TMY (degC).', u'12 متوسطًا شهريًا لحرارة الهواء في السنة النموذجية (°م).'),
    ('GHI_m', u'12 monthly mean daily GHI totals of the TMY (kWh/m2/day).', u'12 متوسطًا شهريًا لمجموع الإشعاع الكلي اليومي في السنة النموذجية (kWh/m2/يوم).'),
    ('years', u'The 12 source years chosen for January..December.', u'السنوات المصدر الـ12 المختارة لأشهر كانون الثاني..كانون الأول.'),
    ('report_en', u'English report: selected years, candidates, checks, method and limits.', u'التقرير الإنجليزي: السنوات المختارة والمرشحون والفحوصات والطريقة والحدود.'),
    ('report_ar', u'Arabic report (right-to-left).', u'التقرير العربي (من اليمين لليسار).'),
],
u'TMY to EPW')

epw_path = lat_o = lon_o = tz_o = elev_o = city_o = T_m = GHI_m = years = None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.export_tmy(d, y_from, y_to, out_dir, city, site_elev)
        epw_path, lat_o, lon_o, tz_o, elev_o, city_o = r["epw_path"], r["lat"], r["lon"], r["tz"], r["elev"], r["city"]
        T_m, GHI_m, years = r["T_m"], r["GHI_m"], r["years"]
        report_en, report_ar = r["report_en"], r["report_ar"]
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
