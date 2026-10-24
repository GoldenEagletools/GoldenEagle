# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE Electrical | الكهربائي  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, y_from, y_to, noct, tcoef, run, update
OUTPUTS: psh, psh_m, best_tilt, tilt_winter, tilt_summer, yield_opt, gain_vs_horizontal, derate_hot, temp_factor_m, voc_tmin, autonomy_days, wind50, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE Electrical', u'الكهربائي', u'Electrical/PV data: peak sun hours, best fixed tilt, temperature effects, battery-autonomy days and small-wind estimate, with a bilingual report.', u'بيانات الكهربائي/الطاقة الشمسية: ساعات الذروة الشمسية، وأفضل ميلان ثابت، وأثر الحرارة، وأيام استقلالية البطاريات، وتقدير الرياح الصغيرة، مع تقرير بلغتين.',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('y_from', u'First year of the statistics period (optional; default 1991).', u'أول سنة بفترة الإحصاءات (اختياري؛ الافتراضي 1991).'),
    ('y_to', u'Last year of the statistics period (optional; default 2020, the WMO standard period; must be a complete year).', u'آخر سنة بفترة الإحصاءات (اختياري؛ الافتراضي 2020، الفترة المعيارية WMO؛ يجب أن تكون سنة مكتملة).'),
    ('noct', u'PV nominal operating cell temperature in degC (optional, default 45, typical value).', u'درجة حرارة الخلية التشغيلية الاسمية للألواح بالمئوية (اختياري، الافتراضي 45، قيمة نموذجية).'),
    ('tcoef', u'PV power temperature coefficient in %/K (optional, default 0.35, typical crystalline silicon).', u'معامل حرارة قدرة الألواح بـ%/كلفن (اختياري، الافتراضي 0.35، سيليكون بلوري نموذجي).'),
    ('run', u'True to execute. The network is used only if the cell has no cache (or hourly data are requested), or update is on.', u'True للتنفيذ. لا تُستخدم الشبكة إلا إذا لم يوجد كاش للخلية (أو طُلبت بيانات ساعية) أو كان update مفعّلًا.'),
    ('update', u'True (with run) to fetch missing days and re-download the last ~150 days, which NASA may revise.', u'True (مع run) لجلب الأيام الناقصة وإعادة تحميل آخر ~150 يومًا لأن NASA قد تعدّلها.'),
],
[
    ('psh', u'Average daily peak sun hours (h/day).', u'متوسط ساعات الذروة الشمسية اليومية (ساعة/يوم).'),
    ('psh_m', u'12 monthly mean peak sun hours.', u'12 متوسطًا شهريًا لساعات الذروة الشمسية.'),
    ('best_tilt', u'Best fixed tilt (deg) for maximum annual yield, facing the equator.', u'أفضل ميلان ثابت (درجة) لأعلى إنتاج سنوي، متجه نحو خط الاستواء.'),
    ('tilt_winter', u'Best tilt (deg) for the winter half of the year.', u'أفضل ميلان (درجة) لنصف السنة الشتوي.'),
    ('tilt_summer', u'Best tilt (deg) for the summer half of the year.', u'أفضل ميلان (درجة) لنصف السنة الصيفي.'),
    ('yield_opt', u'Annual irradiation on the best tilt (kWh/m2/yr).', u'الإشعاع السنوي على أفضل ميلان (kWh/m2/سنة).'),
    ('gain_vs_horizontal', u'Gain of the best tilt over a horizontal plane (%).', u'زيادة أفضل ميلان عن السطح الأفقي (%).'),
    ('derate_hot', u'PV power loss on a hot day (%), from the 99th percentile of daily maxima.', u'فقد قدرة الألواح بيوم حار (%)، من المئين 99 للعظمى اليومية.'),
    ('temp_factor_m', u'12 monthly midday temperature efficiency factors.', u'12 معامل كفاءة شهري بسبب الحرارة وقت الظهيرة.'),
    ('voc_tmin', u'Coldest daily minimum on record (degC) for the maximum open-circuit voltage.', u'أبرد صغرى يومية مسجّلة (°م) لأقصى جهد دائرة مفتوحة.'),
    ('autonomy_days', u'95th percentile of consecutive cloudy-day runs (days).', u'المئين 95 لسلاسل الأيام الغائمة المتتالية (أيام).'),
    ('wind50', u'Estimated mean wind speed at 50 m (m/s), power-law extrapolation.', u'تقدير متوسط سرعة الرياح على 50 م (م/ث)، بقانون القدرة.'),
    ('report_en', u'English report (tables, method and limits).', u'التقرير الإنجليزي (جداول والطريقة والحدود).'),
    ('report_ar', u'Arabic report (right-to-left).', u'التقرير العربي (من اليمين لليسار).'),
],
u'Electrical')

psh, psh_m, best_tilt, tilt_winter, tilt_summer, yield_opt, gain_vs_horizontal, derate_hot, temp_factor_m, voc_tmin, autonomy_days, wind50 = None, None, None, None, None, None, None, None, None, None, None, None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.elec_report(d, y_from, y_to, noct, tcoef, update)
        psh = r.get("psh")
        psh_m = r.get("psh_m")
        best_tilt = r.get("best_tilt")
        tilt_winter = r.get("tilt_winter")
        tilt_summer = r.get("tilt_summer")
        yield_opt = r.get("yield_opt")
        gain_vs_horizontal = r.get("gain_vs_horizontal")
        derate_hot = r.get("derate_hot")
        temp_factor_m = r.get("temp_factor_m")
        voc_tmin = r.get("voc_tmin")
        autonomy_days = r.get("autonomy_days")
        wind50 = r.get("wind50")
        report_en = r.get("report_en")
        report_ar = r.get("report_ar")
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
