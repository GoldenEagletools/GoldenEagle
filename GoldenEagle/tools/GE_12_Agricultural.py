# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE Agricultural | الزراعي  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, y_from, y_to, kc, base_gdd, run, update
OUTPUTS: et0_m, et0_year, rain_year, deficit_m, aridity, frost_last, frost_first, frost_days, gdd_year, hot_days, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE Agricultural', u'الزراعي', u'Agriculture/landscape data: reference evapotranspiration (Hargreaves), rough water deficit, frost dates, growing degree-days, with a bilingual report.', u'بيانات الزراعة والحدائق: التبخر-نتح المرجعي (Hargreaves)، والعجز المائي التقريبي، وتواريخ الصقيع، ودرجات النمو، مع تقرير بلغتين.',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('y_from', u'First year of the statistics period (optional; default 1991).', u'أول سنة بفترة الإحصاءات (اختياري؛ الافتراضي 1991).'),
    ('y_to', u'Last year of the statistics period (optional; default 2020, the WMO standard period; must be a complete year).', u'آخر سنة بفترة الإحصاءات (اختياري؛ الافتراضي 2020، الفترة المعيارية WMO؛ يجب أن تكون سنة مكتملة).'),
    ('kc', u'Crop coefficient Kc (optional, default 1.0): ETc = Kc x ET0.', u'معامل المحصول Kc (اختياري، الافتراضي 1.0): ETc = Kc × ET0.'),
    ('base_gdd', u'Base temperature for growing degree-days in degC (optional, default 10).', u'درجة الأساس لدرجات النمو بالمئوية (اختياري، الافتراضي 10).'),
    ('run', u'True to execute. The network is used only if the cell has no cache (or hourly data are requested), or update is on.', u'True للتنفيذ. لا تُستخدم الشبكة إلا إذا لم يوجد كاش للخلية (أو طُلبت بيانات ساعية) أو كان update مفعّلًا.'),
    ('update', u'True (with run) to fetch missing days and re-download the last ~150 days, which NASA may revise.', u'True (مع run) لجلب الأيام الناقصة وإعادة تحميل آخر ~150 يومًا لأن NASA قد تعدّلها.'),
],
[
    ('et0_m', u'12 monthly mean reference evapotranspiration values (mm/day).', u'12 متوسطًا شهريًا للتبخر-نتح المرجعي (ملم/يوم).'),
    ('et0_year', u'Annual reference evapotranspiration (mm).', u'التبخر-نتح المرجعي السنوي (ملم).'),
    ('rain_year', u'Mean annual rainfall (mm).', u'متوسط الهطول السنوي (ملم).'),
    ('deficit_m', u'12 monthly rough water deficits max(Kc x ET0 - rain, 0) (mm).', u'12 عجزًا مائيًا شهريًا تقريبيًا max(Kc × ET0 - الهطول، 0) (ملم).'),
    ('aridity', u'Aridity index P / ET0.', u'مؤشر الجفاف P / ET0.'),
    ('frost_last', u'Mean day of year of the last spring frost, or empty.', u'متوسط رقم اليوم من السنة لآخر صقيع ربيعي، أو فارغ.'),
    ('frost_first', u'Mean day of year of the first autumn frost, or empty.', u'متوسط رقم اليوم من السنة لأول صقيع خريفي، أو فارغ.'),
    ('frost_days', u'Frost days per year.', u'أيام الصقيع سنويًا.'),
    ('gdd_year', u'Annual growing degree-days.', u'درجات النمو السنوية.'),
    ('hot_days', u'Days above 35 degC per year.', u'أيام فوق 35 °م سنويًا.'),
    ('report_en', u'English report (tables, method and limits).', u'التقرير الإنجليزي (جداول والطريقة والحدود).'),
    ('report_ar', u'Arabic report (right-to-left).', u'التقرير العربي (من اليمين لليسار).'),
],
u'Agricultural')

et0_m, et0_year, rain_year, deficit_m, aridity, frost_last, frost_first, frost_days, gdd_year, hot_days = None, None, None, None, None, None, None, None, None, None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.agri_report(d, y_from, y_to, kc, base_gdd, update)
        et0_m = r.get("et0_m")
        et0_year = r.get("et0_year")
        rain_year = r.get("rain_year")
        deficit_m = r.get("deficit_m")
        aridity = r.get("aridity")
        frost_last = r.get("frost_last")
        frost_first = r.get("frost_first")
        frost_days = r.get("frost_days")
        gdd_year = r.get("gdd_year")
        hot_days = r.get("hot_days")
        report_en = r.get("report_en")
        report_ar = r.get("report_ar")
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
