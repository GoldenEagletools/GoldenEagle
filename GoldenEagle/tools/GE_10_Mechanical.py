# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE Mechanical | الميكانيكي  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, y_from, y_to, base_heat, base_cool, hourly_years, run, update
OUTPUTS: hdd, cdd, hdd_m, cdd_m, heat_design_daily, cool_design_daily, heat_design_hourly, cool_design_hourly, mcwb, wbt_m, wbd_m, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE Mechanical', u'الميكانيكي', u'Mechanical (HVAC) data: heating/cooling degree-days, design temperatures and wet-bulb, with a bilingual report. Preliminary sizing only.', u'بيانات الميكانيكي (التكييف): درجات يوم التدفئة والتبريد، وحرارة التصميم، والترمومتر المبتل، مع تقرير بلغتين. للتحجيم المبدئي فقط.',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('y_from', u'First year of the statistics period (optional; default 1991).', u'أول سنة بفترة الإحصاءات (اختياري؛ الافتراضي 1991).'),
    ('y_to', u'Last year of the statistics period (optional; default 2020, the WMO standard period; must be a complete year).', u'آخر سنة بفترة الإحصاءات (اختياري؛ الافتراضي 2020، الفترة المعيارية WMO؛ يجب أن تكون سنة مكتملة).'),
    ('base_heat', u'Heating degree-day base temperature in degC (optional, default 18).', u'درجة أساس درجات يوم التدفئة بالمئوية (اختياري، الافتراضي 18).'),
    ('base_cool', u'Cooling degree-day base temperature in degC (optional, default 24).', u'درجة أساس درجات يوم التبريد بالمئوية (اختياري، الافتراضي 24).'),
    ('hourly_years', u'Number of recent complete years of HOURLY data for ASHRAE-style design percentiles (e.g. 10; 0 = skip). Large downloads on first use.', u'عدد السنوات المكتملة الأحدث من البيانات الساعية لمئينات التصميم بأسلوب ASHRAE (مثلًا 10؛ 0 = تخطّي). تحميل كبير عند أول استخدام.'),
    ('run', u'True to execute. The network is used only if the cell has no cache (or hourly data are requested), or update is on.', u'True للتنفيذ. لا تُستخدم الشبكة إلا إذا لم يوجد كاش للخلية (أو طُلبت بيانات ساعية) أو كان update مفعّلًا.'),
    ('update', u'True (with run) to fetch missing days and re-download the last ~150 days, which NASA may revise.', u'True (مع run) لجلب الأيام الناقصة وإعادة تحميل آخر ~150 يومًا لأن NASA قد تعدّلها.'),
],
[
    ('hdd', u'Annual heating degree-days (mean per year).', u'درجات يوم التدفئة السنوية (متوسط سنوي).'),
    ('cdd', u'Annual cooling degree-days (mean per year).', u'درجات يوم التبريد السنوية (متوسط سنوي).'),
    ('hdd_m', u'12 monthly heating degree-days.', u'12 قيمة شهرية لدرجات يوم التدفئة.'),
    ('cdd_m', u'12 monthly cooling degree-days.', u'12 قيمة شهرية لدرجات يوم التبريد.'),
    ('heat_design_daily', u'Heating design from daily minima: [1%, 0.4%] coldest days (degC).', u'تصميم التدفئة من الصغرى اليومية: [أبرد 1%، 0.4%] من الأيام (°م).'),
    ('cool_design_daily', u'Cooling design from daily maxima: [1%, 0.4%] hottest days (degC).', u'تصميم التبريد من العظمى اليومية: [أحرّ 1%، 0.4%] من الأيام (°م).'),
    ('heat_design_hourly', u'Hourly heating design [99%, 99.6%] (degC), or empty.', u'تصميم التدفئة الساعي [99%، 99.6%] (°م)، أو فارغ.'),
    ('cool_design_hourly', u'Hourly cooling design dry-bulb [2%, 1%, 0.4%] (degC), or empty.', u'تصميم التبريد الساعي بالترمومتر الجاف [2%، 1%، 0.4%] (°م)، أو فارغ.'),
    ('mcwb', u'Mean coincident wet-bulb for the three cooling values (degC), or empty.', u'متوسط الترمومتر المبتل المتزامن للقيم الثلاث (°م)، أو فارغ.'),
    ('wbt_m', u'12 monthly mean wet-bulb temperatures (degC).', u'12 متوسطًا شهريًا لحرارة الترمومتر المبتل (°م).'),
    ('wbd_m', u'12 monthly wet-bulb depressions (degC): evaporative-cooling potential.', u'12 فرقًا شهريًا للترمومتر المبتل (°م): إمكانية التبريد التبخيري.'),
    ('report_en', u'English report (tables, method and limits).', u'التقرير الإنجليزي (جداول والطريقة والحدود).'),
    ('report_ar', u'Arabic report (right-to-left).', u'التقرير العربي (من اليمين لليسار).'),
],
u'Mechanical')

hdd, cdd, hdd_m, cdd_m, heat_design_daily, cool_design_daily, heat_design_hourly, cool_design_hourly, mcwb, wbt_m, wbd_m = None, None, None, None, None, None, None, None, None, None, None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.mech_report(d, y_from, y_to, base_heat, base_cool, hourly_years, update)
        hdd = r.get("hdd")
        cdd = r.get("cdd")
        hdd_m = r.get("hdd_m")
        cdd_m = r.get("cdd_m")
        heat_design_daily = r.get("heat_design_daily")
        cool_design_daily = r.get("cool_design_daily")
        heat_design_hourly = r.get("heat_design_hourly")
        cool_design_hourly = r.get("cool_design_hourly")
        mcwb = r.get("mcwb")
        wbt_m = r.get("wbt_m")
        wbd_m = r.get("wbd_m")
        report_en = r.get("report_en")
        report_ar = r.get("report_ar")
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
