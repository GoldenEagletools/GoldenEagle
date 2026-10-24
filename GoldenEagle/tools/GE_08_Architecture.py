# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE Architecture | المعماري  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: loc, y_from, y_to, wind_years, overhang_depth, window_height, run, update
OUTPUTS: qibla_deg, qibla_km, qibla_vec, noon_alt, wind_dir, wind_dir_name, wind_rose, facades, facade_kwh, best_facade, sunny_pct, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE Architecture', u'المعماري', u'Architecture data: qibla direction, sun and horizontal overhang depth, facade guide, sky conditions and wind rose, with a bilingual report.', u'بيانات المعماري: اتجاه القبلة، والشمس وعمق كاسر الشمس الأفقي، ودليل الواجهات، وحالة السماء ووردة الرياح، مع تقرير بلغتين.',
[
    ('loc', u'Location from the GE Location tool.', u'الموقع القادم من أداة GE Location.'),
    ('y_from', u'First year of the statistics period (optional; default 1991).', u'أول سنة بفترة الإحصاءات (اختياري؛ الافتراضي 1991).'),
    ('y_to', u'Last year of the statistics period (optional; default 2020, the WMO standard period; must be a complete year).', u'آخر سنة بفترة الإحصاءات (اختياري؛ الافتراضي 2020، الفترة المعيارية WMO؛ يجب أن تكون سنة مكتملة).'),
    ('wind_years', u'Number of recent complete years of HOURLY wind data for the wind rose (default 3; 0 = skip). Each year is a large download on first use.', u'عدد السنوات المكتملة الأحدث من بيانات الرياح الساعية لوردة الرياح (الافتراضي 3؛ 0 = تخطّي). كل سنة تحميل كبير عند أول استخدام.'),
    ('overhang_depth', u'Optional overhang depth in metres to compute the shaded share of the window at noon.', u'عمق الكاسر بالمتر (اختياري) لحساب نسبة الظل على النافذة عند الظهر.'),
    ('window_height', u'Window height in metres (optional, default 1.0 = results per metre of height).', u'ارتفاع النافذة بالمتر (اختياري، الافتراضي 1.0 = نتائج لكل متر ارتفاع).'),
    ('run', u'True to execute. The network is used only if the cell has no cache (or hourly data are requested), or update is on.', u'True للتنفيذ. لا تُستخدم الشبكة إلا إذا لم يوجد كاش للخلية (أو طُلبت بيانات ساعية) أو كان update مفعّلًا.'),
    ('update', u'True (with run) to fetch missing days and re-download the last ~150 days, which NASA may revise.', u'True (مع run) لجلب الأيام الناقصة وإعادة تحميل آخر ~150 يومًا لأن NASA قد تعدّلها.'),
],
[
    ('qibla_deg', u'Qibla bearing in degrees from TRUE north (clockwise).', u'زاوية القبلة بالدرجات من الشمال الحقيقي (مع عقارب الساعة).'),
    ('qibla_km', u'Distance to the Kaaba in km.', u'المسافة إلى الكعبة بالكم.'),
    ('qibla_vec', u'Unit vector toward the qibla in the XY plane (true north = +Y).', u'متجه وحدة نحو القبلة بمستوى XY (الشمال الحقيقي = +Y).'),
    ('noon_alt', u'Solar noon altitude (deg) on Mar 21, Jun 21, Sep 23, Dec 21.', u'ارتفاع الشمس عند الظهر (درجة) أيام 21 آذار و21 حزيران و23 أيلول و21 كانون الأول.'),
    ('wind_dir', u'Prevailing wind direction (deg, wind blowing FROM), or empty.', u'اتجاه الرياح السائد (درجة، التي تهب منها)، أو فارغ.'),
    ('wind_dir_name', u'Prevailing wind compass name (16 points).', u'اسم اتجاه الرياح السائد (16 جهة).'),
    ('wind_rose', u'Wind frequency (%) for the 16 compass sectors starting at N.', u'تكرار الرياح (%) لـ16 جهة تبدأ من الشمال.'),
    ('facades', u'Facade names in the order of facade_kwh: N, E, S, W.', u'أسماء الواجهات بترتيب facade_kwh: N وE وS وW.'),
    ('facade_kwh', u'Annual irradiation on each vertical facade (kWh/m2/yr).', u'الإشعاع السنوي على كل واجهة رأسية (kWh/m2/سنة).'),
    ('best_facade', u'Best facade for large windows by the rule-of-thumb score.', u'أفضل واجهة للنوافذ الكبيرة حسب نقاط القاعدة الإرشادية.'),
    ('sunny_pct', u'Share of sunny days (Kt >= 0.7), %.', u'نسبة الأيام المشمسة (Kt >= 0.7) %.'),
    ('report_en', u'English report (tables, method and limits).', u'التقرير الإنجليزي (جداول والطريقة والحدود).'),
    ('report_ar', u'Arabic report (right-to-left).', u'التقرير العربي (من اليمين لليسار).'),
],
u'Architecture')

qibla_deg, qibla_km, qibla_vec, noon_alt, wind_dir, wind_dir_name, wind_rose, facades, facade_kwh, best_facade, sunny_pct = None, None, None, None, None, None, None, None, None, None, None
report_en = u"Set run=True to execute."
report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
if run:
    try:
        d = ge.loc_from_json(loc)
        r = ge.arch_report(d, y_from, y_to, wind_years, overhang_depth, window_height, update)
        qibla_deg = r.get("qibla_deg")
        qibla_km = r.get("qibla_km")
        qibla_vec = r.get("qibla_vec")
        noon_alt = r.get("noon_alt")
        wind_dir = r.get("wind_dir")
        wind_dir_name = r.get("wind_dir_name")
        wind_rose = r.get("wind_rose")
        facades = r.get("facades")
        facade_kwh = r.get("facade_kwh")
        best_facade = r.get("best_facade")
        sunny_pct = r.get("sunny_pct")
        report_en = r.get("report_en")
        report_ar = r.get("report_ar")
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
