# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE Custom Average | المتوسط بفترة مخصصة  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, y1, m1, y2, m2, date, run, update
OUTPUTS: name, elev, T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P, daily, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE Custom Average', u'المتوسط بفترة مخصصة', u'Monthly climate averages over a period you choose (whole months, from 1981 to the last complete month).', u'المتوسطات المناخية الشهرية لفترة تحددها (أشهر كاملة، من 1981 حتى آخر شهر مكتمل).',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('y1', u'Start year of the period.', u'سنة بداية الفترة.'),
    ('m1', u'Start month (1-12).', u'شهر البداية (1-12).'),
    ('y2', u'End year of the period.', u'سنة نهاية الفترة.'),
    ('m2', u'End month (1-12).', u'شهر النهاية (1-12).'),
    ('date', u'Optional date YYYY-MM-DD for single-day values (any day since 1981, including the current month).', u'تاريخ اختياري بصيغة YYYY-MM-DD لعرض قيم يوم محدد (أي يوم منذ 1981، ويشمل الشهر الحالي).'),
    ('run', u'True to execute. The network is used only if no cache exists for the cell, or update is on.', u'True للتنفيذ. لا تُستخدم الشبكة إلا إذا لم يوجد كاش للخلية أو كان update مفعّلًا.'),
    ('update', u'True (with run) to fetch missing days and re-download the last ~150 days, which NASA may revise.', u'True (مع run) لجلب الأيام الناقصة وإعادة تحميل آخر ~150 يومًا لأن NASA قد تعدّلها.'),
],
[
    ('name', u'Location name.', u'اسم الموقع.'),
    ('elev', u'Elevation of the weather-grid cell in metres (not the actual site elevation).', u'ارتفاع خلية الأرصاد بالمتر (وليس ارتفاع الموقع الفعلي).'),
    ('T', u'12 monthly mean air temperatures (degC), January to December.', u'12 متوسطًا شهريًا لحرارة الهواء (°م)، من كانون الثاني إلى كانون الأول.'),
    ('Tmax', u'12 monthly means of the daily maximum temperature (degC).', u'12 متوسطًا شهريًا لأعلى حرارة يومية (°م).'),
    ('Tmin', u'12 monthly means of the daily minimum temperature (degC).', u'12 متوسطًا شهريًا لأقل حرارة يومية (°م).'),
    ('RH', u'12 monthly mean relative humidity values (%).', u'12 متوسطًا شهريًا للرطوبة النسبية (%).'),
    ('WS', u'12 monthly mean wind speeds at 10 m (km/h); daily means, not gusts.', u'12 متوسطًا شهريًا لسرعة الرياح على 10 م (كم/سا)؛ متوسطات يومية وليست هبّات.'),
    ('GHI', u'12 monthly mean global horizontal irradiance values (kWh/m2/day).', u'12 متوسطًا شهريًا للإشعاع الكلي الأفقي (kWh/m2/يوم).'),
    ('DNI', u'12 monthly mean direct normal irradiance values (kWh/m2/day).', u'12 متوسطًا شهريًا للإشعاع المباشر العمودي (kWh/m2/يوم).'),
    ('DHI', u'12 monthly mean diffuse horizontal irradiance values (kWh/m2/day).', u'12 متوسطًا شهريًا للإشعاع المنتشر الأفقي (kWh/m2/يوم).'),
    ('P', u'12 monthly precipitation totals (mm), averaged over the years (months missing more than 10% of days are skipped).', u'12 مجموعًا شهريًا للهطول (ملم) بمتوسط السنوات (تُهمل الأشهر الناقصة أكثر من 10% من أيامها).'),
    ('daily', u'Single-day values for the given date: English block, then Arabic block.', u'قيم اليوم المحدد: كتلة إنجليزية ثم كتلة عربية.'),
    ('report_en', u'English report with the monthly table. Tip: set the Panel to a monospaced font for aligned columns.', u'التقرير الإنجليزي مع الجدول الشهري. نصيحة: اجعل خط الـ Panel أحادي العرض لتصطف الأعمدة.'),
    ('report_ar', u'Arabic report (right-to-left) with the monthly table.', u'التقرير العربي (من اليمين لليسار) مع الجدول الشهري.'),
],
u'Cust Average')

name = elev = T = Tmax = Tmin = RH = WS = GHI = DNI = DHI = P = daily = None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.climate(d, 2, y1, m1, y2, m2, date, update)
        name, elev = r["name"], r["elev"]
        T, Tmax, Tmin, RH, WS = r["T"], r["Tmax"], r["Tmin"], r["RH"], r["WS"]
        GHI, DNI, DHI, P = r["GHI"], r["DNI"], r["DHI"], r["P"]
        daily, report_en, report_ar = r["daily"], r["report_en"], r["report_ar"]
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
