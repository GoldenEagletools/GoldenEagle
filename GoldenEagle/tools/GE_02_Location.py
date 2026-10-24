# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
GE Location | الموقع  (GoldenEagle v0.1.1 - untested in Rhino / لم يُختبر بعد داخل Rhino)

INPUTS: idx, lat, lon, tz, name, run
OUTPUTS: loc, names, report_en, report_ar
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

ge.set_tooltips(ghenv, u'GE Location', u'الموقع', u'Pick a location from the list of 68 Syrian locations (idx) or enter free coordinates (lat/lon, anywhere in the world). Outputs a location to wire into the other GoldenEagle tools.', u'اختر موقعًا من قائمة 68 موقعًا سوريًا (idx) أو أدخل إحداثيات حرة (lat/lon لأي مكان بالعالم). يخرج موقعًا يُوصَّل بباقي أدوات GoldenEagle.',
[
    ('idx', u"Index 0..67 of a Syrian location (see 'names'). Ignored if lat and lon are given.", u'فهرس 0..67 لموقع سوري (انظر names). يُتجاهل إذا أُعطي lat و lon.'),
    ('lat', u'Latitude in degrees (optional, free coordinates).', u'خط العرض بالدرجات (اختياري، إحداثيات حرة).'),
    ('lon', u'Longitude in degrees (optional, free coordinates).', u'خط الطول بالدرجات (اختياري، إحداثيات حرة).'),
    ('tz', u'Standard-time offset from GMT in hours (optional). Default +3 for the Syrian list; required for free coordinates only when exporting EPW.', u'فرق التوقيت القياسي عن GMT بالساعات (اختياري). الافتراضي +3 لقائمة سوريا؛ يلزم للإحداثيات الحرة عند تصدير EPW فقط.'),
    ('name', u'Display name for free coordinates (optional).', u'اسم يُعرض للإحداثيات الحرة (اختياري).'),
    ('run', u'True to execute (no network is used by this tool).', u'True للتنفيذ (هذه الأداة لا تستخدم الشبكة).'),
],
[
    ('loc', u'Location as text (JSON). Wire it into the loc input of other GoldenEagle tools.', u'الموقع كنص (JSON). وصّله بمدخل loc في باقي أدوات GoldenEagle.'),
    ('names', u'List of the 68 locations: index | Arabic name | English name.', u'قائمة المواقع الـ68: الفهرس | الاسم العربي | الاسم الإنجليزي.'),
    ('report_en', u'English location report.', u'تقرير الموقع بالإنجليزية.'),
    ('report_ar', u'Arabic location report (right-to-left).', u'تقرير الموقع بالعربية (من اليمين لليسار).'),
],
u'GE Location')

names = ge.location_names()
loc = report_en = report_ar = None
if run:
    try:
        d = ge.make_location(idx, lat, lon, tz, name)
        loc = ge.loc_to_json(d)
        report_en, report_ar = ge.location_report(d)
    except Exception as ex:
        report_en = u"Failed: %s" % ge.msg(ex)
        report_ar = ge.rtl(u"فشل: %s" % ge.msg(ex))
else:
    report_en = u"Set run=True to execute."
    report_ar = ge.rtl(u"فعّل run=True للتنفيذ.")
