# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE Civil | المدني  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, y_from, y_to, soil, run, update
OUTPUTS: elev, wind_mean, wind_max, tmax_rec, tmin_rec, range_mean, rain_year, rain_max_day, frost_days, freeze_thaw, rh_mean, soil_info, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE Civil', u'المدني', u'Civil engineering indicators: wind, temperature range, frost, rainfall, humidity and (optional) soil texture, with a bilingual report. Indicators only, not design loads.', u'مؤشرات الهندسة المدنية: الرياح والمدى الحراري والصقيع والهطول والرطوبة وقوام التربة (اختياري)، مع تقرير بلغتين. مؤشرات فقط وليست أحمال تصميم.',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('y_from', u'First year of the statistics period (optional; default 1991).', u'أول سنة بفترة الإحصاءات (اختياري؛ الافتراضي 1991).'),
    ('y_to', u'Last year of the statistics period (optional; default 2020, the WMO standard period; must be a complete year).', u'آخر سنة بفترة الإحصاءات (اختياري؛ الافتراضي 2020، الفترة المعيارية WMO؛ يجب أن تكون سنة مكتملة).'),
    ('soil', u'True to query the SoilGrids online model for soil texture (indicative only; needs internet).', u'True لاستعلام نموذج SoilGrids عن قوام التربة (تقدير فقط؛ يحتاج إنترنت).'),
    ('run', u'True to execute. The network is used only if the cell has no cache (or hourly data are requested), or update is on.', u'True للتنفيذ. لا تُستخدم الشبكة إلا إذا لم يوجد كاش للخلية (أو طُلبت بيانات ساعية) أو كان update مفعّلًا.'),
    ('update', u'True (with run) to fetch missing days and re-download the last ~150 days, which NASA may revise.', u'True (مع run) لجلب الأيام الناقصة وإعادة تحميل آخر ~150 يومًا لأن NASA قد تعدّلها.'),
],
[
    ('elev', u'Elevation of the weather-grid cell (m).', u'ارتفاع خلية الأرصاد (م).'),
    ('wind_mean', u'Mean wind speed at 10 m (km/h).', u'متوسط سرعة الرياح على 10 م (كم/سا).'),
    ('wind_max', u'Highest hourly-mean wind speed on record at 10 m (km/h), not a gust.', u'أعلى متوسط ساعي لسرعة الرياح على 10 م (كم/سا)، وليس هبّة.'),
    ('tmax_rec', u'Record daily maximum temperature (degC).', u'أعلى حرارة عظمى يومية مسجّلة (°م).'),
    ('tmin_rec', u'Record daily minimum temperature (degC).', u'أدنى حرارة صغرى يومية مسجّلة (°م).'),
    ('range_mean', u'Mean daily temperature range (degC).', u'المدى الحراري اليومي المتوسط (°م).'),
    ('rain_year', u'Mean annual rainfall (mm).', u'متوسط الهطول السنوي (ملم).'),
    ('rain_max_day', u'Highest daily rainfall on record (mm).', u'أعلى هطول يومي مسجّل (ملم).'),
    ('frost_days', u'Frost days per year (daily minimum < 0 degC).', u'أيام الصقيع سنويًا (الصغرى < 0 °م).'),
    ('freeze_thaw', u'Freeze-thaw days per year.', u'أيام التجمد والذوبان سنويًا.'),
    ('rh_mean', u'Mean annual relative humidity (%).', u'متوسط الرطوبة النسبية السنوي (%).'),
    ('soil_info', u'Soil texture lines per depth (empty unless soil = True).', u'أسطر قوام التربة لكل عمق (فارغ ما لم يكن soil = True).'),
    ('report_en', u'English report (tables, method and limits).', u'التقرير الإنجليزي (جداول والطريقة والحدود).'),
    ('report_ar', u'Arabic report (right-to-left).', u'التقرير العربي (من اليمين لليسار).'),
],
u'Civil')

elev, wind_mean, wind_max, tmax_rec, tmin_rec, range_mean, rain_year, rain_max_day, frost_days, freeze_thaw, rh_mean, soil_info = None, None, None, None, None, None, None, None, None, None, None, None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.civil_report(d, y_from, y_to, soil, update)
        elev = r.get("elev")
        wind_mean = r.get("wind_mean")
        wind_max = r.get("wind_max")
        tmax_rec = r.get("tmax_rec")
        tmin_rec = r.get("tmin_rec")
        range_mean = r.get("range_mean")
        rain_year = r.get("rain_year")
        rain_max_day = r.get("rain_max_day")
        frost_days = r.get("frost_days")
        freeze_thaw = r.get("freeze_thaw")
        rh_mean = r.get("rh_mean")
        soil_info = r.get("soil_info")
        report_en = r.get("report_en")
        report_ar = r.get("report_ar")
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
