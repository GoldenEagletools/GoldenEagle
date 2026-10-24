# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Mohammad Ghazi Al-Hussami
"""
goldeneagle_core  -  النواة المشتركة لاكستنشن GoldenEagle (Rhino 6+ / IronPython 2.7)
مكان الملف: %APPDATA%\\GoldenEagle\\lib\\goldeneagle_core.py  (كل كومبوننت يضيف هذا المجلد لمسار بايثون).
الإصدار 0.1.1: تقارير ثنائية اللغة (إنجليزي/عربي) مع رموز اتجاه النص، تحقق أمتن من التاريخ، تلميحات (tooltips) تُضبط من الكود،
ونافذة تحديث 150 يومًا. لم يُختبر بعد داخل Rhino.
"""
VERSION = "0.3.0"

import clr
clr.AddReference("System.Net")
from System.Net import ServicePointManager, SecurityProtocolType, WebClient
from System.Threading import Thread
import json
import os
import math
import bisect
import datetime

try:
    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12
except Exception:
    ServicePointManager.SecurityProtocol = 3072

def pause(ms):
    # بديل Thread.Sleep على خيط STA (يتفادى تحذير Rhino)
    Thread.CurrentThread.Join(ms)


# ---------------- ثوابت ----------------
START = datetime.date(1981, 1, 1)
BASE_ORD = START.toordinal()
END_LAG_DAYS = 3
OVERLAP_DAYS = 150   # NASA تستبدل بيانات آخر 2-3 أشهر بنسخ أدق لاحقًا، فنعيد تحميل نافذة أوسع
CHUNK_YEARS = 10
MISSING = -998.0
MET_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "T2MDEW", "RH2M", "WS10M", "WS10M_MAX", "PRECTOTCORR"]
SOL_PARAMS = ["ALLSKY_SFC_SW_DWN", "ALLSKY_SFC_SW_DNI", "ALLSKY_SFC_SW_DIFF", "CLRSKY_SFC_SW_DWN"]
MONTHS_AR = [u"كانون الثاني", u"شباط", u"آذار", u"نيسان", u"أيار", u"حزيران",
             u"تموز", u"آب", u"أيلول", u"تشرين الأول", u"تشرين الثاني", u"كانون الأول"]

_base = os.environ.get("APPDATA") or os.path.expanduser("~")
CACHE_DIR = os.path.join(_base, "GoldenEagle", "cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# ---------------- المواقع (68): (محافظة, منطقة, governorate EN, district EN, lat, lon) ----------------
LOCS = [
 (u"دمشق", u"مركز دمشق", "Damascus", "Damascus Center", 33.5138, 36.2765),
 (u"حلب", u"مركز حلب", "Aleppo", "Aleppo Center", 36.2021, 37.1343),
 (u"حلب", u"منطقة جبل سمعان", "Aleppo", "Jabal Saman", 36.15, 37.05),
 (u"حلب", u"منطقة أعزاز", "Aleppo", "Azaz", 36.5867, 37.0464),
 (u"حلب", u"منطقة الأتارب", "Aleppo", "Atarib", 36.1667, 36.8333),
 (u"حلب", u"منطقة الباب", "Aleppo", "Al-Bab", 36.3711, 37.5178),
 (u"حلب", u"منطقة جرابلس", "Aleppo", "Jarablus", 36.8167, 38.0167),
 (u"حلب", u"منطقة دير حافر", "Aleppo", "Deir Hafer", 36.05, 37.75),
 (u"حلب", u"منطقة السفيرة", "Aleppo", "As-Safira", 36.0761, 37.3706),
 (u"حلب", u"منطقة عفرين", "Aleppo", "Afrin", 36.5117, 36.8683),
 (u"حلب", u"منطقة عين العرب", "Aleppo", "Ain al-Arab (Kobani)", 36.8906, 38.3536),
 (u"حلب", u"منطقة منبج", "Aleppo", "Manbij", 36.5281, 37.9547),
 (u"ريف دمشق", u"مركز ريف دمشق", "Rif Dimashq", "Rif Dimashq Center", 33.4833, 36.3167),
 (u"ريف دمشق", u"منطقة التل", "Rif Dimashq", "At-Tal", 33.6167, 36.3),
 (u"ريف دمشق", u"منطقة داريا", "Rif Dimashq", "Darayya", 33.4589, 36.2358),
 (u"ريف دمشق", u"منطقة دوما", "Rif Dimashq", "Douma", 33.5719, 36.4025),
 (u"ريف دمشق", u"منطقة الزبداني", "Rif Dimashq", "Zabadani", 33.7256, 36.1006),
 (u"ريف دمشق", u"منطقة قدسيا", "Rif Dimashq", "Qudsaya", 33.5286, 36.2367),
 (u"ريف دمشق", u"منطقة قطنا", "Rif Dimashq", "Qatana", 33.4394, 36.0669),
 (u"ريف دمشق", u"منطقة القطيفة", "Rif Dimashq", "Qatifah", 33.7469, 36.6017),
 (u"ريف دمشق", u"منطقة النبك", "Rif Dimashq", "An-Nabk", 34.0289, 36.7289),
 (u"ريف دمشق", u"منطقة يبرود", "Rif Dimashq", "Yabroud", 33.9689, 36.6578),
 (u"حمص", u"مركز حمص", "Homs", "Homs Center", 34.7325, 36.7167),
 (u"حمص", u"منطقة الرستن", "Homs", "Rastan", 34.9236, 36.7314),
 (u"حمص", u"منطقة تدمر", "Homs", "Palmyra (Tadmur)", 34.5561, 38.2811),
 (u"حمص", u"منطقة المخرّم", "Homs", "Al-Makhram", 34.6667, 36.9333),
 (u"حمص", u"منطقة القصير", "Homs", "Al-Qusayr", 34.5069, 36.575),
 (u"حمص", u"منطقة تلكلخ", "Homs", "Tall Kalakh", 34.6706, 36.2822),
 (u"حماة", u"مركز حماه", "Hama", "Hama Center", 35.1318, 36.7578),
 (u"حماة", u"منطقة السقيلبية", "Hama", "Suqaylabiyah", 35.3608, 36.3894),
 (u"حماة", u"منطقة السلمية", "Hama", "Salamiyah", 35.0111, 37.0531),
 (u"حماة", u"منطقة محردة", "Hama", "Muhradah", 35.2181, 36.5544),
 (u"حماة", u"منطقة مصياف", "Hama", "Masyaf", 35.0644, 36.3425),
 (u"حماة", u"منطقة سلحب", "Hama", "Salhab", 35.05, 36.9),
 (u"اللاذقية", u"مركز اللاذقية", "Latakia", "Latakia Center", 35.5317, 35.7915),
 (u"اللاذقية", u"منطقة القرداحة", "Latakia", "Qardaha", 35.4181, 36.0672),
 (u"اللاذقية", u"منطقة الحفّة", "Latakia", "Al-Haffah", 35.5744, 36.1867),
 (u"اللاذقية", u"منطقة جبلة", "Latakia", "Jableh", 35.3608, 35.925),
 (u"إدلب", u"مركز إدلب", "Idlib", "Idlib Center", 35.9306, 36.6339),
 (u"إدلب", u"منطقة معرة النعمان", "Idlib", "Maarat al-Numan", 35.6444, 36.6786),
 (u"إدلب", u"منطقة أريحا", "Idlib", "Ariha", 35.8128, 36.6117),
 (u"إدلب", u"منطقة حارم", "Idlib", "Harim", 36.2072, 36.5169),
 (u"إدلب", u"منطقة جسر الشغور", "Idlib", "Jisr al-Shughur", 35.8144, 36.3183),
 (u"إدلب", u"منطقة خان شيخون", "Idlib", "Khan Shaykhun", 35.4433, 36.6519),
 (u"الحسكة", u"مركز الحسكة", "Al-Hasakah", "Al-Hasakah Center", 36.5024, 40.7477),
 (u"الحسكة", u"منطقة رأس العين", "Al-Hasakah", "Ras al-Ayn", 36.8511, 40.0736),
 (u"الحسكة", u"منطقة المالكية", "Al-Hasakah", "Al-Malikiyah", 37.1808, 42.1436),
 (u"الحسكة", u"منطقة القامشلي", "Al-Hasakah", "Qamishli", 37.0522, 41.2364),
 (u"دير الزور", u"مركز دير الزور", "Deir ez-Zor", "Deir ez-Zor Center", 35.3359, 40.1408),
 (u"دير الزور", u"منطقة البوكمال", "Deir ez-Zor", "Abu Kamal", 34.4506, 40.9169),
 (u"دير الزور", u"منطقة الميادين", "Deir ez-Zor", "Al-Mayadin", 35.0147, 40.4536),
 (u"طرطوس", u"مركز طرطوس", "Tartus", "Tartus Center", 34.8886, 35.8867),
 (u"طرطوس", u"منطقة صافيتا", "Tartus", "Safita", 34.8203, 36.1178),
 (u"طرطوس", u"منطقة دريكيش", "Tartus", "Dreikish", 34.9022, 36.1372),
 (u"طرطوس", u"منطقة الشيخ بدر", "Tartus", "Sheikh Badr", 34.9578, 36.1108),
 (u"طرطوس", u"منطقة بانياس", "Tartus", "Baniyas", 35.1806, 35.945),
 (u"طرطوس", u"منطقة القدموس", "Tartus", "Qadmus", 34.7644, 36.2019),
 (u"الرقة", u"مركز الرقة", "Raqqa", "Raqqa Center", 35.95, 39.0089),
 (u"الرقة", u"منطقة الثورة", "Raqqa", "Al-Thawrah (Tabqa)", 35.8181, 38.5461),
 (u"الرقة", u"منطقة تل أبيض", "Raqqa", "Tal Abyad", 36.6989, 38.9553),
 (u"درعا", u"مركز درعا", "Daraa", "Daraa Center", 32.6189, 36.1021),
 (u"درعا", u"منطقة ازرع", "Daraa", "Izra", 32.8631, 36.2461),
 (u"درعا", u"منطقة الصنمين", "Daraa", "As-Sanamayn", 33.0678, 36.1097),
 (u"السويداء", u"مركز السويداء", "As-Suwayda", "As-Suwayda Center", 32.7047, 36.5697),
 (u"السويداء", u"منطقة شهبا", "As-Suwayda", "Shahba", 32.8547, 36.6289),
 (u"السويداء", u"منطقة صلخد", "As-Suwayda", "Salkhad", 32.4931, 36.7089),
 (u"القنيطرة", u"مركز القنيطرة", "Quneitra", "Quneitra Center", 33.1264, 35.8244),
 (u"القنيطرة", u"منطقة فيق", "Quneitra", "Fiq", 32.7789, 35.6608),
]


# ---------------- تواريخ ----------------
def ord_to_date(i):
    return datetime.date.fromordinal(BASE_ORD + i)


def date_to_idx(d):
    return d.toordinal() - BASE_ORD


def yyyymmdd(d):
    return "%04d%02d%02d" % (d.year, d.month, d.day)


def parse_yyyymmdd(s):
    return datetime.date(int(s[0:4]), int(s[4:6]), int(s[6:8]))


def days_in_month(y, m):
    if m == 12:
        return 31
    return (datetime.date(y, m + 1, 1) - datetime.date(y, m, 1)).days


def last_complete_month(d):
    if d.day == days_in_month(d.year, d.month):
        return (d.year, d.month)
    if d.month == 1:
        return (d.year - 1, 12)
    return (d.year, d.month - 1)


def msg(e):
    try:
        return unicode(e)
    except Exception:
        try:
            return str(e)
        except Exception:
            return repr(e)


# ---------------- مفاتيح الخلايا (مثبتة باختبار حمص فقط) ----------------
def met_key(lat, lon):
    return (int(math.floor((lat + 0.25) / 0.5)), int(math.floor((lon + 180.0 + 0.3125) / 0.625)))


def sol_key(lat, lon):
    return (int(math.floor(lat)), int(math.floor(lon)))


def near_edge(v, offset, step, tol=0.01):
    r = (v - offset) / step
    return abs(r - round(r)) * step < tol


def near_met_edge(lat, lon):
    return near_edge(lat, 0.25, 0.5) or near_edge(lon, -179.6875, 0.625)


def near_sol_edge(lat, lon):
    return near_edge(lat, 0.0, 1.0) or near_edge(lon, 0.0, 1.0)


def cache_name(group, lat, lon):
    near = near_met_edge(lat, lon) if group == "met" else near_sol_edge(lat, lon)
    if near:
        return ("%s_pt_%.4f_%.4f" % (group, lat, lon)).replace(".", "p").replace("-", "n")
    k = met_key(lat, lon) if group == "met" else sol_key(lat, lon)
    return "%s_%d_%d" % (group, k[0], k[1])


# ---------------- الكاش ----------------
def cache_path(name):
    return os.path.join(CACHE_DIR, name + ".json")


def load_cache(name):
    p = cache_path(name)
    if not os.path.exists(p):
        return None
    try:
        f = open(p, "r")
        try:
            return json.load(f)
        finally:
            f.close()
    except Exception:
        return None


def save_cache(name, data):
    p = cache_path(name)
    tmp = p + ".tmp"
    f = open(tmp, "w")
    try:
        json.dump(data, f)
    finally:
        f.close()
    if os.path.exists(p):
        os.remove(p)
    os.rename(tmp, p)


# ---------------- الشبكة ----------------
def _new_client():
    c = WebClient()
    try:
        c.Headers.Add("User-Agent", "GoldenEagle-Grasshopper/" + VERSION)
    except Exception:
        pass
    return c


def http_get(url):
    last = None
    for wait in (0, 2, 5):
        if wait:
            pause(wait * 1000)
        try:
            return _new_client().DownloadString(url)
        except Exception as e:
            last = e
            s = str(e)
            if "400" in s or "422" in s:
                break
    raise last


def fetch_chunk(lat, lon, params, d1, d2):
    use = list(params)
    dropped = []
    while True:
        url = ("https://power.larc.nasa.gov/api/temporal/daily/point?"
               "parameters=" + ",".join(use) + "&community=RE"
               "&longitude=" + str(lon) + "&latitude=" + str(lat) +
               "&start=" + yyyymmdd(d1) + "&end=" + yyyymmdd(d2) + "&format=JSON")
        try:
            txt = http_get(url)
            break
        except Exception as e:
            s = str(e)
            if "ALLSKY_SFC_SW_DNI" in use and ("400" in s or "422" in s):
                use.remove("ALLSKY_SFC_SW_DNI")
                dropped.append("ALLSKY_SFC_SW_DNI")
                continue
            raise
    d = json.loads(txt)
    p = d["properties"]["parameter"]
    series = {}
    for k in use:
        if k in p:
            series[k] = p[k]
    return series, d["geometry"]["coordinates"][2], dropped


def download_into(data, name, group, lat, lon, d_start, d_end, params=None):
    if params is None:
        params = MET_PARAMS if group == "met" else SOL_PARAMS
    cur = d_start
    while cur <= d_end:
        chunk_end = min(d_end, datetime.date(cur.year + CHUNK_YEARS - 1, 12, 31))
        series, elev, dropped = fetch_chunk(lat, lon, params, cur, chunk_end)
        data["elev"] = elev
        for dd in dropped:
            if dd not in data["dropped"]:
                data["dropped"].append(dd)
        need = date_to_idx(chunk_end) + 1
        for k, ser in series.items():
            arr = data["params"].setdefault(k, [])
            while len(arr) < need:
                arr.append(None)
            for ds, v in ser.items():
                i = date_to_idx(parse_yyyymmdd(ds))
                if 0 <= i < len(arr):
                    arr[i] = None if v <= MISSING else v
        data["last"] = yyyymmdd(chunk_end)
        save_cache(name, data)
        cur = chunk_end + datetime.timedelta(days=1)
        pause(300)


def _missing_params(data, group):
    required = MET_PARAMS if group == "met" else SOL_PARAMS
    return [k for k in required if k not in data["params"] and k not in data.get("dropped", [])]


def ensure_group(group, lat, lon, force_update, notes):
    name = cache_name(group, lat, lon)
    data = load_cache(name)
    end_target = datetime.date.today() - datetime.timedelta(days=END_LAG_DAYS)
    fresh = False
    if data is None:
        data = {"version": 2, "group": group, "start": yyyymmdd(START), "last": yyyymmdd(START),
                "elev": None, "dropped": [], "params": {}}
        download_into(data, name, group, lat, lon, START, end_target)
        notes.append((u"Downloaded group %s from NASA and cached it (file %s)" % (group, name),
                      u"تم تحميل مجموعة %s من NASA وحفظها (ملف %s)" % (group, name)))
        fresh = True
    if not fresh:
        mp = _missing_params(data, group)
        if mp:
            download_into(data, name, group, lat, lon, START, parse_yyyymmdd(data["last"]), mp)
            notes.append((u"Added new variables to cached group %s: %s" % (group, u", ".join(mp)),
                          u"أُضيفت متغيرات جديدة للمجموعة المخزّنة %s: %s" % (group, ltr(u", ".join(mp)))))
        if force_update:
            last = parse_yyyymmdd(data["last"])
            d_start = max(START, last - datetime.timedelta(days=OVERLAP_DAYS))
            if d_start <= end_target:
                download_into(data, name, group, lat, lon, d_start, end_target)
                notes.append((u"Updated group %s up to %s" % (group, iso_ymd(data["last"])),
                              u"تم تحديث مجموعة %s حتى %s" % (group, ltr(iso_ymd(data["last"])))))
    return data, name


# ---------------- الحساب ----------------
def resolve_period(mode, y1, m1, y2, m2, lc):
    if mode == 0:
        s, e = (1991, 1), (2020, 12)
    elif mode == 1:
        s, e = (1981, 1), lc
    elif mode == 2:
        if None in (y1, m1, y2, m2):
            raise ValueError(bi(u"Custom period needs y1, m1, y2, m2", u"الفترة المخصصة تتطلب y1 و m1 و y2 و m2"))
        s, e = (int(y1), int(m1)), (int(y2), int(m2))
    else:
        raise ValueError(bi(u"mode must be 0, 1 or 2", u"mode يجب أن يكون 0 أو 1 أو 2"))
    for t in (s, e):
        if t[1] < 1 or t[1] > 12:
            raise ValueError(bi(u"Month number outside 1..12", u"رقم الشهر خارج 1..12"))
    if s < (1981, 1):
        raise ValueError(bi(u"Period starts before 1981-01 (start of data)", u"بداية الفترة قبل 1981-01 (بداية البيانات)"))
    if e > lc:
        raise ValueError(bi(u"Period ends after the last complete month in the cache: %04d-%02d" % lc, u"نهاية الفترة بعد آخر شهر مكتمل في الكاش: %04d-%02d" % lc))
    if s > e:
        raise ValueError(bi(u"Period start is after its end", u"بداية الفترة بعد نهايتها"))
    return s, e


def compute_monthly(met, sol, s, e):
    i0 = date_to_idx(datetime.date(s[0], s[1], 1))
    i1 = date_to_idx(datetime.date(e[0], e[1], days_in_month(e[0], e[1])))
    series = {}
    for k in ("T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS10M"):
        series[k] = met["params"].get(k)
    for k in ("ALLSKY_SFC_SW_DWN", "ALLSKY_SFC_SW_DNI", "ALLSKY_SFC_SW_DIFF"):
        series[k] = sol["params"].get(k)
    prec = met["params"].get("PRECTOTCORR")
    sums = dict((k, [0.0] * 12) for k in series)
    cnts = dict((k, [0] * 12) for k in series)
    psum = {}
    for i in range(i0, i1 + 1):
        d = ord_to_date(i)
        m = d.month - 1
        for k, arr in series.items():
            if arr is not None and i < len(arr) and arr[i] is not None:
                sums[k][m] += arr[i]
                cnts[k][m] += 1
        if prec is not None and i < len(prec) and prec[i] is not None:
            key = (d.year, d.month)
            rec = psum.get(key)
            if rec is None:
                rec = [0.0, 0]
                psum[key] = rec
            rec[0] += prec[i]
            rec[1] += 1
    mean = {}
    for k in series:
        mean[k] = [(sums[k][m] / cnts[k][m]) if cnts[k][m] else None for m in range(12)]
    ptot = [0.0] * 12
    pn = [0] * 12
    for (y, mo), rec in psum.items():
        dim = days_in_month(y, mo)
        if rec[1] >= 0.9 * dim:
            ptot[mo - 1] += rec[0] / rec[1] * dim
            pn[mo - 1] += 1
    P = [(ptot[m] / pn[m]) if pn[m] else None for m in range(12)]
    WS = [None if v is None else v * 3.6 for v in mean["WS10M"]]
    return mean, WS, P


def fmt(v, nd=1):
    return "-" if v is None else ("%." + str(nd) + "f") % v



# ---------------- دعم الثنائية اللغة واتجاه النص (RTL/LTR) ----------------
import re

BIDI_MARKS = True   # False لتعطيل رموز اتجاه النص إن لم تُعرض جيدًا في Panel
_RLE = u"\u202b"
_LRE = u"\u202a"
_PDF = u"\u202c"
MONTHS_EN = [u"January", u"February", u"March", u"April", u"May", u"June",
             u"July", u"August", u"September", u"October", u"November", u"December"]


def ltr(s):
    return (_LRE + s + _PDF) if BIDI_MARKS else s


def rtl(s):
    return (_RLE + s + _PDF) if BIDI_MARKS else s


def bi(en, ar):
    return u"%s | %s" % (en, ar)


def iso_ymd(s):
    return u"%s-%s-%s" % (s[0:4], s[4:6], s[6:8])


def parse_date_input(d):
    """يقبل: نص YYYY-MM-DD أو YYYY/MM/DD أو YYYYMMDD، أو كائن DateTime، أو قائمة بعنصر. يرجع 'YYYY-MM-DD' أو None."""
    if d is None:
        return None
    try:
        if hasattr(d, "Year") and hasattr(d, "Month") and hasattr(d, "Day"):
            return "%04d-%02d-%02d" % (d.Year, d.Month, d.Day)
    except Exception:
        pass
    if isinstance(d, (list, tuple)):
        if len(d) == 0:
            return None
        d = d[0]
    try:
        s = (u"%s" % d).strip()
    except Exception:
        raise ValueError(bi(u"Unreadable date input", u"تعذّرت قراءة التاريخ"))
    if not s:
        return None
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s) or re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if not m:
        raise ValueError(bi(u"Date format not supported (use YYYY-MM-DD): %s" % s,
                            u"صيغة التاريخ غير مدعومة (استخدم YYYY-MM-DD): %s" % s))
    y, mo, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
    datetime.date(y, mo, dd)
    return "%04d-%02d-%02d" % (y, mo, dd)


def set_tooltips(ghenv, title_en, title_ar, desc_en, desc_ar, inputs, outputs, nick=None):
    """يضبط اسم الأداة ووصفها ووصف كل مدخل ومخرج (إنجليزي أولًا ثم عربي) ليظهر عند تمرير الماوس.
    inputs/outputs: قوائم (name, en, ar). يعتمد على ghenv.Component؛ أي فشل يُتجاهل بصمت."""
    try:
        comp = ghenv.Component
        comp.NickName = nick if nick else title_en
        comp.Description = u"%s\n%s" % (desc_en, desc_ar)
        comp.Message = u"GoldenEagle v%s" % VERSION
        for plist, items in ((comp.Params.Input, inputs), (comp.Params.Output, outputs)):
            by_name = dict((it[0], it) for it in items)
            for p in plist:
                it = by_name.get(p.NickName) or by_name.get(p.Name)
                if it:
                    p.Description = u"%s\n%s" % (it[1], it[2])
    except Exception:
        pass


# ---------------- الموقع ----------------
def make_location(idx=None, lat=None, lon=None, tz=None, name=None):
    """يبني الموقع (dict). إحداثيات حرة إذا أُعطي lat و lon، وإلا فهرس من القائمة (الافتراضي 0).
    tz: فرق التوقيت القياسي عن GMT. افتراضي +3 لمواقع القائمة، وبلا قيمة للإحداثيات الحرة."""
    if lat is not None and lon is not None:
        q_lat, q_lon = float(lat), float(lon)
        if not (-90.0 <= q_lat <= 90.0) or not (-180.0 <= q_lon <= 180.0):
            raise ValueError(bi(u"Coordinates out of range (check lat/lon order)", u"إحداثيات خارج النطاق (تأكد من ترتيب lat/lon)"))
        label = u"(%.4f, %.4f)" % (q_lat, q_lon)
        d = {"idx": None, "lat": q_lat, "lon": q_lon, "gov_ar": u"", "gov_en": "NA",
             "name_ar": name if name else label, "name_en": "Lat%.3f_Lon%.3f" % (q_lat, q_lon),
             "label_en": (u"%s %s" % (name, label)) if name else label,
             "country": "NA", "tz": None, "tz_default": False}
    else:
        i = int(idx) if idx is not None else 0
        if i < 0 or i >= len(LOCS):
            raise ValueError(bi(u"idx out of range 0..%d" % (len(LOCS) - 1), u"idx خارج النطاق 0..%d" % (len(LOCS) - 1)))
        L = LOCS[i]
        d = {"idx": i, "lat": L[4], "lon": L[5], "gov_ar": L[0], "gov_en": L[2],
             "name_ar": u"%s - %s" % (L[0], L[1]), "name_en": L[3],
             "label_en": u"%s - %s" % (L[2], L[3]), "country": "SYR",
             "tz": 3.0, "tz_default": True}
    if tz is not None:
        t = float(tz)
        if t < -12.0 or t > 14.0:
            raise ValueError(bi(u"tz out of range -12..14", u"tz خارج النطاق -12..14"))
        d["tz"] = t
        d["tz_default"] = False
    return d


def loc_to_json(d):
    return json.dumps(d)


def loc_from_json(s):
    if s is None or (not isinstance(s, dict) and len(s) == 0):
        raise ValueError(bi(u"Connect loc from the GE Location tool", u"وصّل loc من أداة GE Location"))
    d = s if isinstance(s, dict) else json.loads(s)
    if "lat" not in d or "lon" not in d:
        raise ValueError(bi(u"The text wired to loc is not a valid GE Location", u"النص الموصول بـ loc ليس موقعًا صالحًا من GE Location"))
    d["lat"] = float(d["lat"])
    d["lon"] = float(d["lon"])
    if "label_en" not in d:
        d["label_en"] = d.get("name_ar", u"")
    return d


def location_names():
    return [u"%d | %s - %s | %s - %s" % (i, l[0], l[1], l[2], l[3]) for i, l in enumerate(LOCS)]


def location_report(d):
    if d["tz"] is None:
        tz_en = u"not set (required only for EPW export)"
        tz_ar = u"غير محددة (لازمة لتصدير EPW فقط)"
    elif d["tz_default"]:
        tz_en = u"UTC%+d (default: Syria's official time since Oct 2022)" % int(d["tz"])
        tz_ar = u"%s (افتراضي: التوقيت الرسمي بسوريا منذ تشرين الأول 2022)" % ltr(u"UTC%+d" % int(d["tz"]))
    else:
        tz_en = u"UTC%+.1f (user-defined)" % d["tz"]
        tz_ar = u"%s (من المستخدم)" % ltr(u"UTC%+.1f" % d["tz"])
    en = [u"Location / Coordinates: %s" % d["label_en"],
          u"Latitude: %.4f" % d["lat"],
          u"Longitude: %.4f" % d["lon"],
          u"Time zone: %s" % tz_en]
    ar = [rtl(u"المنطقة / الإحداثيات: %s" % d["name_ar"]),
          rtl(u"خط العرض: %s" % ltr(u"%.4f" % d["lat"])),
          rtl(u"خط الطول: %s" % ltr(u"%.4f" % d["lon"])),
          rtl(u"المنطقة الزمنية: %s" % tz_ar)]
    return u"\n".join(en), u"\n".join(ar)


# ---------------- اليومي ----------------
DAILY_VARS = [
    ("T2M", u"Mean temperature", u"متوسط الحرارة", u"°C", u"°م", 2),
    ("T2M_MAX", u"Maximum temperature", u"أعلى حرارة", u"°C", u"°م", 2),
    ("T2M_MIN", u"Minimum temperature", u"أقل حرارة", u"°C", u"°م", 2),
    ("RH2M", u"Relative humidity", u"الرطوبة النسبية", u"%", u"%", 1),
    ("WS10M", u"Wind speed at 10 m", u"سرعة الرياح على 10 م", u"m/s", u"م/ث", 2),
    ("T2MDEW", u"Mean dew point", u"متوسط نقطة الندى", u"°C", u"°م", 2),
    ("WS10M_MAX", u"Maximum wind speed at 10 m", u"أعلى سرعة رياح على 10 م", u"m/s", u"م/ث", 2),
    ("PRECTOTCORR", u"Precipitation (corrected)", u"الهطول (مصحّح)", u"mm/day", u"ملم/يوم", 2),
    ("ALLSKY_SFC_SW_DWN", u"GHI (all-sky)", u"الإشعاع الكلي الأفقي GHI", u"kWh/m2/day", u"kWh/m2/يوم", 2),
    ("ALLSKY_SFC_SW_DNI", u"DNI (all-sky)", u"الإشعاع المباشر DNI", u"kWh/m2/day", u"kWh/m2/يوم", 2),
    ("ALLSKY_SFC_SW_DIFF", u"DHI (all-sky)", u"الإشعاع المنتشر DHI", u"kWh/m2/day", u"kWh/m2/يوم", 2),
    ("CLRSKY_SFC_SW_DWN", u"GHI (clear-sky)", u"الإشعاع الكلي بسماء صافية", u"kWh/m2/day", u"kWh/m2/يوم", 2),
]


def daily_text(met, sol, ds):
    """ds بصيغة YYYY-MM-DD. يرجع (أسطر إنجليزية، أسطر عربية). الشهر الحالي الناقص متاح هنا."""
    d = datetime.date(int(ds[0:4]), int(ds[5:7]), int(ds[8:10]))
    i = date_to_idx(d)
    if i < 0:
        raise ValueError(bi(u"Date is before the start of data (1981-01-01)", u"التاريخ قبل بداية البيانات (1981-01-01)"))
    last = min(parse_yyyymmdd(met["last"]), parse_yyyymmdd(sol["last"]))
    if d > last:
        raise ValueError(bi(u"Date is after the last loaded day (%s); use update=True" % last.isoformat(),
                            u"التاريخ بعد آخر يوم محمّل (%s)؛ استخدم update=True" % last.isoformat()))
    en = [u"Daily values for %s" % d.isoformat()]
    ar = [rtl(u"قيم يوم %s" % ltr(d.isoformat()))]
    for k, n_en, n_ar, u_en, u_ar, nd in DAILY_VARS:
        src = met if k in MET_PARAMS else sol
        arr = src["params"].get(k)
        v = arr[i] if (arr is not None and i < len(arr)) else None
        extra_en = extra_ar = u""
        if k == "WS10M" and v is not None:
            extra_en = u" (%s km/h)" % fmt(v * 3.6, 1)
            extra_ar = u" (%s كم/سا)" % ltr(fmt(v * 3.6, 1))
        en.append(u"%s (%s): %s %s%s" % (n_en, k, fmt(v, nd), u_en, extra_en))
        ar.append(rtl(u"%s (%s): %s %s%s" % (n_ar, ltr(k), ltr(fmt(v, nd)), u_ar, extra_ar)))
    return en, ar


# ---------------- الجداول والتقارير ----------------
_W = [10, 6, 6, 6, 5, 6, 8, 8, 8, 6]


def _table_en(T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P):
    names = [u"Month", u"T", u"Tmax", u"Tmin", u"RH", u"WS", u"GHI", u"DNI", u"DHI", u"P"]
    units = [u"", u"degC", u"degC", u"degC", u"%", u"km/h", u"kWh/m2/d", u"kWh/m2/d", u"kWh/m2/d", u"mm"]

    def row(cells):
        return u" | ".join([(c.ljust(_W[0]) if j == 0 else c.rjust(_W[j])) for j, c in enumerate(cells)])
    lines = [row(names), row(units)]
    for k in range(12):
        vals = [MONTHS_EN[k], fmt(T[k]), fmt(Tmax[k]), fmt(Tmin[k]), fmt(RH[k], 0), fmt(WS[k]),
                fmt(GHI[k], 2), fmt(DNI[k], 2), fmt(DHI[k], 2), fmt(P[k], 0)]
        lines.append(row(vals))
    return lines


def _table_ar(T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P):
    names = [u"الشهر", u"T", u"Tmax", u"Tmin", u"RH", u"WS", u"GHI", u"DNI", u"DHI", u"P"]
    units = [u"", u"°م", u"°م", u"°م", u"%", u"كم/سا", u"kWh/m2/يوم", u"kWh/m2/يوم", u"kWh/m2/يوم", u"ملم"]

    def row(cells):
        out = []
        for j, c in enumerate(cells):
            if j == 0:
                out.append(c.ljust(12))
            else:
                out.append(ltr(c.rjust(_W[j])))
        return rtl(u" | ".join(out))
    lines = [row(names), row(units)]
    for k in range(12):
        vals = [MONTHS_AR[k], fmt(T[k]), fmt(Tmax[k]), fmt(Tmin[k]), fmt(RH[k], 0), fmt(WS[k]),
                fmt(GHI[k], 2), fmt(DNI[k], 2), fmt(DHI[k], 2), fmt(P[k], 0)]
        lines.append(row(vals))
    return lines


def build_reports(loc, md, s, e, n_months, last_all, elev, T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P,
                  notes, dropped, mk, sk, same_names):
    modes_en = {0: u"Standard period (WMO 1991-2020)", 1: u"General average (1981 to last complete month)", 2: u"Custom period"}
    modes_ar = {0: u"الفترة المعيارية (WMO 1991-2020)", 1: u"المتوسط العام (من 1981 لآخر شهر مكتمل)", 2: u"فترة مخصصة"}
    pv = [v for v in P if v is not None]
    annual = fmt(sum(pv), 0)
    ps = u"%04d-%02d" % s
    pe = u"%04d-%02d" % e
    last_s = last_all.isoformat()
    mc = (mk[0] * 0.5, -180.0 + 0.625 * mk[1])
    edge = near_met_edge(loc["lat"], loc["lon"]) or near_sol_edge(loc["lat"], loc["lon"])
    en = [u"Location / Coordinates: %s" % loc["label_en"],
          u"Latitude: %.4f" % loc["lat"], u"Longitude: %.4f" % loc["lon"],
          u"Elevation (weather-grid cell, not the actual site): %s m" % fmt(elev, 0),
          u"Mode: %s" % modes_en[md],
          u"Period: %s to %s (%d months)" % (ps, pe, n_months),
          u"Last day loaded: %s" % last_s, u""]
    en += _table_en(T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P)
    en += [u"", u"Annual precipitation (estimated): %s mm" % annual, u"",
           u"Weather cell (~0.5 x 0.625 deg): center (%.2f, %.3f)" % mc,
           u"Solar cell (~1 x 1 deg; width assumed): from (%d, %d) to (%d, %d)" % (sk[0], sk[1], sk[0] + 1, sk[1] + 1)]
    ar = [rtl(u"المنطقة / الإحداثيات: %s" % loc["name_ar"]),
          rtl(u"خط العرض: %s" % ltr(u"%.4f" % loc["lat"])),
          rtl(u"خط الطول: %s" % ltr(u"%.4f" % loc["lon"])),
          rtl(u"الارتفاع (خلية الأرصاد، ليس الموقع الفعلي): %s م" % ltr(fmt(elev, 0))),
          rtl(u"النمط: %s" % modes_ar[md]),
          rtl(u"الفترة: من %s إلى %s (%s شهرًا)" % (ltr(ps), ltr(pe), ltr(u"%d" % n_months))),
          rtl(u"آخر يوم محمّل: %s" % ltr(last_s)), u""]
    ar += _table_ar(T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P)
    ar += [u"", rtl(u"الهطول السنوي التقديري: %s ملم" % ltr(annual)), u"",
           rtl(u"خلية الأرصاد (~0.5 x 0.625 درجة): مركزها %s" % ltr(u"(%.2f, %.3f)" % mc)),
           rtl(u"خلية الإشعاع (~1 x 1 درجة، العرض افتراض): من %s إلى %s" % (
               ltr(u"(%d, %d)" % (sk[0], sk[1])), ltr(u"(%d, %d)" % (sk[0] + 1, sk[1] + 1))))]
    if edge:
        en.append(u"Note: the point is near a cell edge, so a point-specific cache was used.")
        ar.append(rtl(u"تنبيه: النقطة قريبة من حد خلية، فاستُخدم كاش النقطة بدل كاش الخلية."))
    if same_names:
        en.append(u"Locations sharing the same weather cell (identical values, a source-resolution limit): %s" % u", ".join(same_names[0]))
        ar.append(rtl(u"مواقع تشارك نفس خلية الأرصاد (أرقامها متطابقة، وهذا حد دقة المصدر): %s" % u"، ".join(same_names[1])))
    if dropped:
        en.append(u"Note: the server rejected: %s" % u", ".join(dropped))
        ar.append(rtl(u"ملاحظة: رفض الخادم المتغيرات: %s" % ltr(u", ".join(dropped))))
    en.append(u"")
    ar.append(u"")
    if md == 0:
        en.append(u"Standard period: 30 years (1991-2020) adopted by the World Meteorological Organization (WMO) as a common reference, long enough to smooth year-to-year variability and uniform so locations and studies can be compared fairly.")
        ar.append(rtl(u"الفترة المعيارية: 30 سنة (1991-2020) تعتمدها المنظمة العالمية للأرصاد (WMO) مرجعًا موحدًا، لأنها طويلة كفاية لتخفيف تذبذب السنوات وموحدة لتصح المقارنة بين المواقع والدراسات."))
    elif md == 1:
        en.append(u"The general average mixes years from different eras and includes a warming trend, so it may be cooler than present-day conditions.")
        ar.append(rtl(u"المتوسط العام يخلط سنوات من حقب مختلفة، وفيه اتجاه احترار، فقد يكون أبرد من الواقع الحالي."))
    else:
        if n_months < 120:
            en.append(u"Warning: the period is under 10 years, so the average reflects the weather of those years more than the climate.")
            ar.append(rtl(u"تنبيه: الفترة أقل من 10 سنوات، فالمتوسط يعكس طقس تلك السنوات أكثر من المناخ."))
        elif n_months < 360:
            en.append(u"Note: the period is under 30 years, so it is not a WMO standard period.")
            ar.append(rtl(u"ملاحظة: الفترة أقل من 30 سنة، فهي ليست فترة معيارية بمعيار WMO."))
    if s < (2001, 1):
        en.append(u"Note: per NASA POWER documentation, its CERES-based solar data start on 2001-01-01; earlier solar values come from a different NASA product line, so solar averages over this period mix two sources.")
        ar.append(rtl(u"ملاحظة: حسب توثيق NASA POWER تبدأ بيانات الإشعاع المبنية على CERES من 2001-01-01، وما قبلها من خط منتجات مختلف، فمتوسطات الإشعاع لهذه الفترة تمزج مصدرين."))
    en.append(u"Source: NASA POWER (MERRA-2 meteorology ~0.5 x 0.625 deg; CERES-based solar ~1 x 1 deg). Reanalysis/model data, not station measurements. Precipitation is for preliminary estimates. WS is a daily mean, not gusts.")
    ar.append(rtl(u"المصدر: NASA POWER (أرصاد MERRA-2 بشبكة ~0.5 x 0.625 درجة؛ إشعاع مبني على CERES بشبكة ~1 x 1 درجة). بيانات إعادة تحليل ونماذج، وليست قياس محطات. الهطول للتقدير الأولي. WS متوسط يومي وليست هبّات."))
    for n_en, n_ar in notes:
        en.append(n_en)
        ar.append(rtl(n_ar))
    return u"\n".join(en), u"\n".join(ar)


def climate(loc, mode=0, y1=None, m1=None, y2=None, m2=None, date=None, update=False):
    q_lat, q_lon = loc["lat"], loc["lon"]
    date_iso = parse_date_input(date)
    notes = []
    met, met_name = ensure_group("met", q_lat, q_lon, bool(update), notes)
    sol, sol_name = ensure_group("sol", q_lat, q_lon, bool(update), notes)
    elev = met.get("elev")
    last_all = min(parse_yyyymmdd(met["last"]), parse_yyyymmdd(sol["last"]))
    lc = last_complete_month(last_all)
    md = int(mode) if mode is not None else 0
    s, e = resolve_period(md, y1, m1, y2, m2, lc)
    n_months = (e[0] - s[0]) * 12 + (e[1] - s[1]) + 1
    mean, WS, P = compute_monthly(met, sol, s, e)
    T, Tmax, Tmin, RH = mean["T2M"], mean["T2M_MAX"], mean["T2M_MIN"], mean["RH2M"]
    GHI, DNI, DHI = mean["ALLSKY_SFC_SW_DWN"], mean["ALLSKY_SFC_SW_DNI"], mean["ALLSKY_SFC_SW_DIFF"]
    daily = None
    d_en = d_ar = None
    if date_iso:
        d_en, d_ar = daily_text(met, sol, date_iso)
        daily = u"\n".join(d_en) + u"\n\n" + u"\n".join(d_ar)
    mk, sk = met_key(q_lat, q_lon), sol_key(q_lat, q_lon)
    same = None
    if loc.get("idx") is not None:
        idxs = [j for j in range(len(LOCS)) if j != loc["idx"] and met_key(LOCS[j][4], LOCS[j][5]) == mk]
        if idxs:
            same = ([LOCS[j][3] for j in idxs], [LOCS[j][1] for j in idxs])
    rep_en, rep_ar = build_reports(loc, md, s, e, n_months, last_all, elev, T, Tmax, Tmin, RH, WS, GHI, DNI, DHI, P,
                                   notes, sol["dropped"], mk, sk, same)
    if date_iso is None:
        rep_en += u"\nSingle-day lookup: not requested (give a date to the 'date' input)."
        rep_ar += u"\n" + rtl(u"البحث بيوم محدد: غير مطلوب (أعطِ تاريخًا للمدخل date).")
    return {"name": loc["name_ar"], "lat": q_lat, "lon": q_lon, "elev": elev,
            "T": T, "Tmax": Tmax, "Tmin": Tmin, "RH": RH, "WS": WS,
            "GHI": GHI, "DNI": DNI, "DHI": DHI, "P": P, "daily": daily,
            "report_en": rep_en, "report_ar": rep_ar}


# ---------------- تصدير EPW (من GH_09 المجرَّب بـ Rhino/Ladybug، مع تقارير ثنائية اللغة) ----------------
EPW_DIR = os.path.join(_base, "GoldenEagle", "epw")
if not os.path.exists(EPW_DIR):
    os.makedirs(EPW_DIR)
GSC = 1367.0
HMET = ["T2M", "T2MDEW", "RH2M", "PS", "WS10M", "WD10M", "PRECTOTCORR"]
HSOL = ["ALLSKY_SFC_SW_DWN", "ALLSKY_SFC_SW_DNI", "ALLSKY_SFC_SW_DIFF", "ALLSKY_SFC_LW_DWN",
        "CLOUD_AMT", "PW", "ALLSKY_SRF_ALB"]
FLAGS = "?9" * 28
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def hourly_cache_name(group, lat, lon):
    if group == "met":
        near = near_edge(lat, 0.25, 0.5) or near_edge(lon, -179.6875, 0.625)
        k = met_key(lat, lon)
    else:
        near = near_edge(lat, 0.0, 1.0) or near_edge(lon, 0.0, 1.0)
        k = sol_key(lat, lon)
    if near:
        return ("h%s_pt_%.4f_%.4f" % (group, lat, lon)).replace(".", "p").replace("-", "n")
    return "h%s_%d_%d" % (group, k[0], k[1])


def ascii_only(s):
    try:
        out = s.encode("ascii", "replace")
        if not isinstance(out, str):
            out = out.decode("ascii")
        return out.replace(",", " ")
    except Exception:
        return "unknown"

def get_hourly(group, lat, lon, year, notes):
    name = hourly_cache_name(group, lat, lon) + "_%d" % year
    wstart = datetime.date(year - 1, 12, 31)
    wend = datetime.date(year + 1, 1, 1)
    n_exp = ((wend - wstart).days + 1) * 24
    data = load_cache(name)
    if data is not None and data.get("n") == n_exp:
        return data
    params = HMET if group == "met" else HSOL
    url = ("https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=" + ",".join(params) +
           "&community=RE&longitude=" + str(lon) + "&latitude=" + str(lat) +
           "&start=" + yyyymmdd(wstart) + "&end=" + yyyymmdd(wend) + "&format=JSON&time-standard=UTC")
    d = json.loads(http_get(url))
    p = d["properties"]["parameter"]
    arrays = {}
    first = None
    for k in params:
        ser = p.get(k)
        if ser is None:
            raise ValueError(u"لم يرجع المتغير %s" % k)
        keys = sorted(ser.keys())
        if len(keys) != n_exp:
            raise ValueError(u"عدد القيم الساعية للمتغير %s هو %d بدل %d" % (k, len(keys), n_exp))
        if first is None:
            first = keys[0]
        arrays[k] = [None if ser[x] <= MISSING else ser[x] for x in keys]
    if first != yyyymmdd(wstart) + "00":
        raise ValueError(u"أول مفتاح زمني غير متوقع: %s" % first)
    data = {"version": 1, "first": first, "n": n_exp, "elev": d["geometry"]["coordinates"][2], "params": arrays}
    save_cache(name, data)
    notes.append((u"Downloaded hourly group %s for year %d and cached it (%s)" % (group, year, name), u"تم تحميل مجموعة %s الساعية لسنة %d وحفظها (%s)" % (group, year, name)))
    return data

# ---------------- فلك ----------------
def sun_terms(n):
    B = 2 * math.pi * (n - 1) / 365.0
    eot = 229.18 * (0.000075 + 0.001868 * math.cos(B) - 0.032077 * math.sin(B)
                    - 0.014615 * math.cos(2 * B) - 0.04089 * math.sin(2 * B))
    decl = (0.006918 - 0.399912 * math.cos(B) + 0.070257 * math.sin(B) - 0.006758 * math.cos(2 * B)
            + 0.000907 * math.sin(2 * B) - 0.002697 * math.cos(3 * B) + 0.00148 * math.sin(3 * B))
    e0 = (1.000110 + 0.034221 * math.cos(B) + 0.001280 * math.sin(B)
          + 0.000719 * math.cos(2 * B) + 0.000077 * math.sin(2 * B))
    return eot, decl, e0


def cosz_mean(lat, lon, n, h):
    phi = math.radians(lat)
    eot, decl, e0 = sun_terms(n)
    tot = 0.0
    for i in range(12):
        t = h + (i + 0.5) / 12.0
        st = t + lon / 15.0 + eot / 60.0
        H = math.radians(15.0 * (st - 12.0))
        c = math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(H)
        tot += max(c, 0.0)
    return tot / 12.0


def f1(v, nd=1):
    return ("%." + str(nd) + "f") % v




# ---------------- مكوّنات مشتركة لـ EPW (سجلات ساعية، تنعيم، تنسيق) ----------------
def _hourly_records(q_lat, q_lon, tzi, src_years, hourly, se, elev, p_ratio):
    """سجلات ساعية رقمية (8760) من سنة مصدر لكل شهر. التوقيت المحلي القياسي = UTC + tzi، وفبراير 28 يومًا دائمًا."""
    dpm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    recs = []
    for m in range(1, 13):
        ys = src_years[m - 1]
        met, sol = hourly[ys]
        pm = met["params"]
        ps_ = sol["params"]
        wstart = datetime.datetime(ys - 1, 12, 31, 0)
        for d in range(1, dpm[m - 1] + 1):
            for hh in range(24):
                cur = datetime.datetime(ys, m, d, hh)
                utc = cur - datetime.timedelta(hours=tzi)
                i = int((utc - wstart).total_seconds() // 3600)
                n_utc = utc.timetuple().tm_yday
                eot, decl, e0 = sun_terms(n_utc)
                cz = cosz_mean(q_lat, q_lon, n_utc, utc.hour)
                et_h = GSC * e0 * cz
                et_n = (GSC * e0) if cz > 0.0 else 0.0
                t = pm["T2M"][i]
                td = pm["T2MDEW"][i]
                rh = pm["RH2M"][i]
                ps = pm["PS"][i]
                ws = pm["WS10M"][i]
                wd = pm["WD10M"][i]
                pr = pm["PRECTOTCORR"][i]
                if se is not None:
                    t_site = (t + 6.5 * (elev - se) / 1000.0) if t is not None else None
                    td_site = rh_site = None
                    if td is not None and t_site is not None:
                        e_v = 6.1094 * math.exp(17.625 * td / (243.04 + td)) * p_ratio
                        xx = math.log(e_v / 6.1094)
                        td_site = 243.04 * xx / (17.625 - xx)
                        rh_site = 100.0 * e_v / (6.1094 * math.exp(17.625 * t_site / (243.04 + t_site)))
                        if rh_site >= 100.0 or td_site > t_site:
                            td_site, rh_site = t_site, 100.0
                    if ps is not None:
                        ps = ps * p_ratio
                    t, td, rh = t_site, td_site, rh_site
                recs.append({"y": ys, "mo": m, "d": d, "h": hh, "cz": cz, "eth": et_h, "etn": et_n,
                             "t": t, "td": td, "rh": rh, "ps": ps, "ws": ws, "wd": wd, "pr": pr,
                             "ghi": ps_["ALLSKY_SFC_SW_DWN"][i], "dni": ps_["ALLSKY_SFC_SW_DNI"][i],
                             "dif": ps_["ALLSKY_SFC_SW_DIFF"][i], "lw": ps_["ALLSKY_SFC_LW_DWN"][i],
                             "cl": ps_["CLOUD_AMT"][i], "pw": ps_["PW"][i], "alb": ps_["ALLSKY_SRF_ALB"][i]})
    return recs


def _rh_from(t, td):
    if t is None or td is None:
        return None
    r = 100.0 * math.exp(17.625 * td / (243.04 + td)) / math.exp(17.625 * t / (243.04 + t))
    return max(0.0, min(100.0, r))


def _smooth_interfaces(recs, src_years, half=6):
    """تنعيم الانقطاع عند حدود الأشهر المأخوذة من سنوات مختلفة (تنفيذ GoldenEagle لوصف NREL: تنعيم خطي 6 ساعات على كل جانب).
    الطريقة: يُوزَّع فرق القيمة بين آخر ساعة من الشهر السابق وأول ساعة من اللاحق نصفين على منحدر خطي يتلاشى خلال 6 ساعات
    من كل جانب، فيُحفظ شكل الدورة اليومية. الحقول: الحرارة، نقطة الندى، سرعة الرياح، الضغط، المياه المتكثفة، واتجاه الرياح (دائري).
    الرطوبة تُعاد من الحرارة ونقطة الندى بعد التنعيم. لا تنعيم بين شهرين من نفس السنة، ولا بين كانون الأول وكانون الثاني."""
    dpm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    pos = 0
    n_smoothed = 0
    for m in range(1, 12):
        pos += dpm[m - 1] * 24
        if src_years[m - 1] == src_years[m]:
            continue
        a_last, b_first = recs[pos - 1], recs[pos]
        for f in ("t", "td", "ws", "ps", "pw", "wd"):
            if a_last[f] is None or b_first[f] is None:
                continue
            delta = b_first[f] - a_last[f]
            if f == "wd":
                delta = ((delta + 180.0) % 360.0) - 180.0
            for j in range(1, half + 1):
                w = 0.5 * (half - j + 1) / float(half)
                ra, rb = recs[pos - j], recs[pos + j - 1]
                if ra[f] is not None:
                    ra[f] = ra[f] + delta * w
                if rb[f] is not None:
                    rb[f] = rb[f] - delta * w
        for j in range(1, half + 1):
            for rr in (recs[pos - j], recs[pos + j - 1]):
                if rr["ws"] is not None:
                    rr["ws"] = max(0.0, rr["ws"])
                if rr["wd"] is not None:
                    rr["wd"] = rr["wd"] % 360.0
                if rr["t"] is not None and rr["td"] is not None and rr["td"] > rr["t"]:
                    rr["td"] = rr["t"]
                rr["rh"] = _rh_from(rr["t"], rr["td"])
        n_smoothed += 1
    return n_smoothed


def _format_records(recs, miss):
    def val(name, v, fn, code):
        if v is None:
            miss[name] = miss.get(name, 0) + 1
            return code
        return fn(v)
    rows = []
    for r in recs:
        fields = [
            "%d" % r["y"], "%d" % r["mo"], "%d" % r["d"], "%d" % (r["h"] + 1), "60", FLAGS,
            val("T2M", r["t"], lambda v: f1(v, 2), "99.9"),
            val("T2MDEW", r["td"], lambda v: f1(v, 2), "99.9"),
            val("RH2M", r["rh"], lambda v: f1(max(0.0, min(110.0, v)), 1), "999"),
            val("PS", r["ps"], lambda v: "%.0f" % (v * 1000.0), "999999"),
            "%.0f" % r["eth"], "%.0f" % r["etn"],
            val("ALLSKY_SFC_LW_DWN", r["lw"], lambda v: f1(v, 1), "9999"),
            val("ALLSKY_SFC_SW_DWN", r["ghi"], lambda v: f1(max(0.0, v), 1), "9999"),
            val("ALLSKY_SFC_SW_DNI", r["dni"], lambda v: f1(max(0.0, v), 1), "9999"),
            val("ALLSKY_SFC_SW_DIFF", r["dif"], lambda v: f1(max(0.0, v), 1), "9999"),
            "999999", "999999", "999999", "9999",
            val("WD10M", r["wd"], lambda v: "%.0f" % v, "999"),
            val("WS10M", r["ws"], lambda v: f1(v, 2), "999"),
            val("CLOUD_AMT", r["cl"], lambda v: "%d" % int(round(max(0.0, min(100.0, v)) / 10.0)), "99"),
            "99", "9999", "99999", "9", "999999999",
            val("PW", r["pw"], lambda v: f1(v * 10.0, 1), "999"),
            ".999", "999", "99",
            val("ALLSKY_SRF_ALB", r["alb"], lambda v: f1(v, 3), "999"),
            val("PRECTOTCORR", r["pr"], lambda v: f1(max(0.0, v), 2), "999"),
            "1",
        ]
        rows.append(",".join(fields))
    return rows


def _record_stats(recs):
    dpm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    mT = [0.0] * 12
    mTn = [0] * 12
    mG = [0.0] * 12
    ghi_ratio = []
    rh_diff = []
    for r in recs:
        m = r["mo"] - 1
        if r["t"] is not None:
            mT[m] += r["t"]
            mTn[m] += 1
        if r["ghi"] is not None:
            mG[m] += r["ghi"]
        if None not in (r["ghi"], r["dni"], r["dif"]) and r["cz"] > 0.15:
            den = r["dni"] * r["cz"] + r["dif"]
            if den > 50.0:
                ghi_ratio.append(r["ghi"] / den)
        if None not in (r["t"], r["td"], r["rh"]):
            rc = _rh_from(r["t"], r["td"])
            rh_diff.append(abs(rc - r["rh"]))
    T_m = [(mT[k] / mTn[k]) if mTn[k] else None for k in range(12)]
    GHI_m = [mG[k] / 1000.0 / dpm[k] for k in range(12)]
    return T_m, GHI_m, ghi_ratio, rh_diff


def _ladybug_lines():
    en = [u"", u"Ladybug: wire epw_path to the _epw_file input of Import EPW. Ladybug reads the format's missing codes (e.g. 999999) as ordinary numbers, so avoid the illuminance, visibility, ceiling, weather, snow, aerosol, opaque-sky-cover and night-albedo fields.",
          u"Not yet validated with EnergyPlus/Honeybee. Reanalysis data, not station measurements."]
    ar = [u"", rtl(u"Ladybug: وصّل epw_path بمدخل _epw_file في Import EPW. تقرأ Ladybug رموز المفقود بالصيغة (مثل 999999) كأرقام عادية، فتجنب حقول الإضاءة والرؤية وارتفاع الغيوم والطقس والثلج والهباء والغطاء المعتم وانعكاسية الليل."),
          rtl(u"لم يُتحقق منه بعد مع EnergyPlus/Honeybee. بيانات إعادة تحليل، وليست قياس محطات.")]
    return en, ar


def _site_elev_setup(site_elev, elev, notes):
    se = None
    p_ratio = 1.0
    if site_elev is not None and len(u"%s" % site_elev) > 0:
        se = float(site_elev)
        if se < -400.0 or se > 6000.0:
            raise ValueError(bi(u"site_elev must be between -400 and 6000 m", u"site_elev يجب أن يكون بين -400 و6000 م"))
        if abs(elev - se) > 1500.0:
            raise ValueError(bi(u"site_elev differs from the grid-cell elevation (%.0f m) by more than 1500 m; the simple correction is not appropriate" % elev,
                                u"site_elev يختلف عن ارتفاع الخلية (%.0f م) بأكثر من 1500 م؛ التصحيح البسيط غير مناسب" % elev))
        if abs(elev - se) > 500.0:
            notes.append((u"Warning: the site differs from the grid-cell elevation by more than 500 m; the simple elevation correction is less reliable.",
                          u"تنبيه: ارتفاع الموقع يختلف عن ارتفاع الخلية بأكثر من 500 م؛ التصحيح البسيط أقل موثوقية."))
        p_ratio = ((1.0 - 2.25577e-5 * se) / (1.0 - 2.25577e-5 * elev)) ** 5.25588
    return se, p_ratio


# ---------------- اختيار الأشهر النموذجية (TMY) - طريقة Sandia/NREL TMY3 ----------------
# المرجع المتحقَّق منه: Wilcox & Marion (2008), Users Manual for TMY3 Data Sets, NREL/TP-581-43156.
# أوزان TMY3 /20: حرارة (عظمى 1، صغرى 1، متوسطة 2)، ندى (عظمى 1، صغرى 1، متوسطة 2)، رياح (عظمى 1، متوسطة 1)، إشعاع كلي 5، مباشر 5.
# الانحراف عن TMY3 (لأن NASA لا توفر ندى عظمى/صغرى يوميًا، فتحققنا بـ GH_12): وزن الندى كله (4/20) على المتوسط اليومي.
# خيارات GoldenEagle حيث المرجع غير محدد: معيار ترتيب الخطوة 2 (انظر _step2_score)، وتعريف "السلسلة" (يومان متتاليان فأكثر)،
# وطريقة تنعيم الحدود (_smooth_interfaces). الحوض يبدأ 2002 (البيانات الساعية من 2001 وتحتاج 31 كانون الأول السابق).
TMY_WEIGHTS = [("DB_MAX", 1), ("DB_MIN", 1), ("DB_MEAN", 2), ("DP_MEAN", 4),
               ("WS_MAX", 1), ("WS_MEAN", 1), ("GHI", 5), ("DNI", 5)]
TMY_SOURCES = {"DB_MAX": ("met", "T2M_MAX"), "DB_MIN": ("met", "T2M_MIN"), "DB_MEAN": ("met", "T2M"),
               "DP_MEAN": ("met", "T2MDEW"), "WS_MAX": ("met", "WS10M_MAX"), "WS_MEAN": ("met", "WS10M"),
               "GHI": ("sol", "ALLSKY_SFC_SW_DWN"), "DNI": ("sol", "ALLSKY_SFC_SW_DNI")}
TMY_POOL_START = 2002
TMY_MIN_YEARS = 10
TMY_MAX_MISSING = 0.10


def _quantile(sorted_vals, p):
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    k = (n - 1) * p
    f = int(math.floor(k))
    c = min(f + 1, n - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _mean(v):
    return sum(v) / float(len(v))


def _sd(v):
    m = _mean(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / float(len(v)))


def _ecdf(sorted_vals, x):
    return float(bisect.bisect_right(sorted_vals, x)) / len(sorted_vals)


def fs_statistic(cand, long_sorted):
    """إحصائية Finkelstein-Schafer: متوسط |CDF_طويل - CDF_مرشح| عند كل قيمة يومية للمرشح."""
    vals = sorted([v for v in cand if v is not None])
    if not vals or not long_sorted:
        return None
    tot = 0.0
    for x in vals:
        tot += abs(_ecdf(long_sorted, x) - _ecdf(vals, x))
    return tot / len(vals)


def _runs(flags):
    """سلسلة = يومان متتاليان فأكثر في نفس الفئة. يرجع (عدد السلاسل، أطولها)."""
    count = longest = cur = 0
    for f in list(flags) + [False]:
        if f:
            cur += 1
        else:
            if cur >= 2:
                count += 1
                longest = max(longest, cur)
            cur = 0
    return count, longest


def _pool_daily(met, sol, years):
    pool = {}
    for y in years:
        for m in range(1, 13):
            n = days_in_month(y, m)
            rec = {}
            for key, (grp, par) in TMY_SOURCES.items():
                arr = (met if grp == "met" else sol)["params"].get(par)
                vals = []
                for d in range(1, n + 1):
                    i = date_to_idx(datetime.date(y, m, d))
                    vals.append(arr[i] if (arr is not None and 0 <= i < len(arr)) else None)
                rec[key] = vals
            pool[(m, y)] = rec
    return pool


def _step2_score(cand_vals, long_valid):
    """ترتيب الخطوة 2: قرب متوسط ووسيط الشهر من متوسط ووسيط المدى الطويل. المرجع لا يحدد المقياس، فنحسب مجموعًا موزونًا لـ
    (|فرق المتوسط| + |فرق الوسيط|) / الانحراف المعياري الطويل لكل مؤشر، بنفس أوزان TMY3."""
    tot = 0.0
    wsum = 0.0
    for key, w in TMY_WEIGHTS:
        v = [x for x in cand_vals[key] if x is not None]
        lv = long_valid[key]
        sd = _sd(lv) or 1.0
        mlong = _mean(lv)
        medlong = _quantile(sorted(lv), 0.5)
        tot += w * (abs(_mean(v) - mlong) + abs(_quantile(sorted(v), 0.5) - medlong)) / sd
        wsum += w
    return tot / wsum


def select_tmy_months(met, sol, years):
    """يرجع قائمة من 12 قاموسًا (شهر، سنة مختارة، المرشحون بترتيب الخطوة 2، المستبعدون بالاستمرارية...)."""
    if len(years) < TMY_MIN_YEARS:
        raise ValueError(bi(u"The year pool must have at least %d years" % TMY_MIN_YEARS, u"يجب أن يضم حوض السنوات %d سنوات على الأقل" % TMY_MIN_YEARS))
    pool = _pool_daily(met, sol, years)
    out = []
    for m in range(1, 13):
        long_valid = {}
        for key in TMY_SOURCES:
            long_valid[key] = [v for y in years for v in pool[(m, y)][key] if v is not None]
            if not long_valid[key]:
                raise ValueError(bi(u"No daily data for month %d (%s)" % (m, key), u"لا بيانات يومية للشهر %d (%s)" % (m, key)))
        long_sorted = dict((k, sorted(v)) for k, v in long_valid.items())
        cands = []
        for y in years:
            rec = pool[(m, y)]
            vals_c = dict((k, (rec[k][:28] if m == 2 else rec[k])) for k in TMY_SOURCES)
            bad = False
            for k in TMY_SOURCES:
                miss_n = len([v for v in vals_c[k] if v is None])
                if miss_n > TMY_MAX_MISSING * len(vals_c[k]):
                    bad = True
            if bad:
                continue
            ws = 0.0
            for key, w in TMY_WEIGHTS:
                ws += w * fs_statistic(vals_c[key], long_sorted[key])
            cands.append({"year": y, "ws": ws, "vals": vals_c})
        if not cands:
            raise ValueError(bi(u"No valid candidate year for month %d" % m, u"لا سنة مرشحة صالحة للشهر %d" % m))
        top = sorted(cands, key=lambda c: c["ws"])[:5]
        for c in top:
            c["s2"] = _step2_score(c["vals"], long_valid)
        top = sorted(top, key=lambda c: c["s2"])
        p33_db = _quantile(long_sorted["DB_MEAN"], 1.0 / 3.0)
        p67_db = _quantile(long_sorted["DB_MEAN"], 2.0 / 3.0)
        p33_g = _quantile(long_sorted["GHI"], 1.0 / 3.0)
        p33_n = _quantile(long_sorted["DNI"], 1.0 / 3.0)
        for c in top:
            v = c["vals"]
            runs = [
                _runs([x is not None and x > p67_db for x in v["DB_MEAN"]]),
                _runs([x is not None and x < p33_db for x in v["DB_MEAN"]]),
                _runs([x is not None and x < p33_g for x in v["GHI"]]),
                _runs([x is not None and x < p33_n for x in v["DNI"]]),
            ]
            c["nruns"] = sum(r[0] for r in runs)
            c["longest"] = max(r[1] for r in runs)
        excluded = {}
        for c in top:
            others = [o for o in top if o is not c]
            if c["nruns"] == 0:
                excluded[c["year"]] = u"zero runs"
            elif others and c["nruns"] > max(o["nruns"] for o in others):
                excluded[c["year"]] = u"most runs"
            elif others and c["longest"] > max(o["longest"] for o in others):
                excluded[c["year"]] = u"longest run"
        keep = [c for c in top if c["year"] not in excluded]
        ignored = False
        if keep:
            chosen = keep[0]
        else:
            chosen = top[0]
            ignored = True
        out.append({"month": m, "year": chosen["year"], "ranked": [c["year"] for c in top],
                    "excluded": excluded, "persistence_ignored": ignored, "n_candidates": len(cands)})
    return out, pool


def _tmy_vs_longterm(pool, sel, years):
    """مقارنة (من البيانات اليومية) بين السنة النموذجية والمدى الطويل: متوسط الحرارة سنويًا، ومجموع GHI وDNI سنويًا."""
    dpm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def monthly_mean(key, m, ylist):
        v = [x for y in ylist for x in pool[(m, y)][key][:28 if m == 2 else None] if x is not None]
        return _mean(v) if v else None
    res = {}
    for key in ("DB_MEAN", "GHI", "DNI"):
        tmy_t = long_t = 0.0
        for m in range(1, 13):
            sy = sel[m - 1]["year"]
            a = monthly_mean(key, m, [sy])
            b = monthly_mean(key, m, years)
            if a is None or b is None:
                return None
            if key == "DB_MEAN":
                tmy_t += a * dpm[m - 1] / 365.0
                long_t += b * dpm[m - 1] / 365.0
            else:
                tmy_t += a * dpm[m - 1]
                long_t += b * dpm[m - 1]
        res[key] = (tmy_t, long_t)
    return res


def export_epw(loc, year, out_dir=None, city=None, site_elev=None):
    """يصدّر EPW لسنة فعلية. tz يؤخذ من loc (أداة GE Location). يرجع قاموسًا فيه المسار والتقارير.
    site_elev (اختياري، م): تصحيح بسيط لارتفاع الموقع (غير مُتحقَّق منه): الحرارة بتدرج 6.5 كلفن/كم، والضغط بالغلاف المعياري،
    ونقطة الندى بثبات نسبة الخلط (ضغط البخار يتناسب مع الضغط)، والرطوبة تُعاد من الحرارة المصححة. الرياح والإشعاع لا تُصحَّح."""
    notes = []
    q_lat, q_lon = loc["lat"], loc["lon"]
    if loc.get("tz") is None:
        raise ValueError(bi(u"EPW export needs a time zone: set tz in GE Location", u"تصدير EPW يحتاج المنطقة الزمنية: حدّد tz في GE Location"))
    tzv = float(loc["tz"])
    if abs(tzv - round(tzv)) > 1e-9:
        raise ValueError(bi(u"Non-integer UTC offsets (e.g. 5.5) are not supported yet", u"الإزاحة الزمنية غير الصحيحة (مثل 5.5) غير مدعومة بعد"))
    tzi = int(round(tzv))
    if year is None:
        raise ValueError(bi(u"Enter year (the actual year)", u"أدخل year (السنة الفعلية)"))
    Y = int(year)
    end_target = datetime.date.today() - datetime.timedelta(days=END_LAG_DAYS)
    if Y < 2002:
        raise ValueError(bi(u"Hourly data start in 2001; the earliest allowed year is 2002", u"البيانات الساعية تبدأ من 2001؛ أصغر سنة مسموحة 2002"))
    if datetime.date(Y + 1, 1, 1) > end_target:
        raise ValueError(bi(u"Year %d is not complete yet in NASA data" % Y, u"السنة %d غير مكتملة بعد في بيانات NASA" % Y))
    met = get_hourly("met", q_lat, q_lon, Y, notes)
    sol = get_hourly("sol", q_lat, q_lon, Y, notes)
    elev = met["elev"]
    se = None
    p_ratio = 1.0
    if site_elev is not None and len(u"%s" % site_elev) > 0:
        se = float(site_elev)
        if se < -400.0 or se > 6000.0:
            raise ValueError(bi(u"site_elev must be between -400 and 6000 m", u"site_elev يجب أن يكون بين -400 و6000 م"))
        if abs(elev - se) > 1500.0:
            raise ValueError(bi(u"site_elev differs from the grid-cell elevation (%.0f m) by more than 1500 m; the simple correction is not appropriate" % elev,
                                u"site_elev يختلف عن ارتفاع الخلية (%.0f م) بأكثر من 1500 م؛ التصحيح البسيط غير مناسب" % elev))
        if abs(elev - se) > 500.0:
            notes.append((u"Warning: the site differs from the grid-cell elevation by more than 500 m; the simple elevation correction is less reliable.",
                          u"تنبيه: ارتفاع الموقع يختلف عن ارتفاع الخلية بأكثر من 500 م؛ التصحيح البسيط أقل موثوقية."))
        p_ratio = ((1.0 - 2.25577e-5 * se) / (1.0 - 2.25577e-5 * elev)) ** 5.25588
    elev_out = se if se is not None else elev
    city_s = ascii_only(city) if (city is not None and len(u"%s" % city) > 0) else ascii_only(loc.get("name_en", u"site"))
    region = ascii_only(loc.get("gov_en", u"NA"))
    country = loc.get("country", "NA")

    hourly = {Y: (met, sol)}
    recs = _hourly_records(q_lat, q_lon, tzi, [Y] * 12, hourly, se, elev, p_ratio)
    miss = {}
    rows = _format_records(recs, miss)
    if len(rows) != 8760:
        raise ValueError(u"rows %d != 8760" % len(rows))
    T_m, GHI_m, ghi_ratio, rh_diff = _record_stats(recs)

    c1 = ("GoldenEagle %s: derived from NASA POWER hourly reanalysis (met cell approx 0.5x0.625 deg and solar cell approx 1x1 deg) "
          "NOT station measurements. Year %d. Standard time UTC%+d. UTC hour HH key = interval starting at HH." % (VERSION, Y, tzi))
    c2 = ("Missing: illuminance visibility ceiling weather codes snow aerosol opaque sky cover. Elevation and pressure are grid-cell values. "
          "Sky cover rounded to tenths. Extraterrestrial radiation computed (Gsc 1367).")
    if se is not None:
        c2 += (" Temperature, pressure and dew point adjusted from grid-cell elevation %.0f m to site elevation %.0f m "
               "(6.5 K/km lapse, standard-atmosphere pressure, constant mixing ratio); wind and solar not adjusted." % (elev, se))
    header = [
        "LOCATION,%s,%s,%s,NASA-POWER-reanalysis,999999,%.4f,%.4f,%.1f,%.1f" % (city_s, region, country, q_lat, q_lon, float(tzi), elev_out),
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,%s" % c1,
        "COMMENTS 2,%s" % c2,
        "DATA PERIODS,1,1,Data,%s,1/1,12/31" % WEEKDAYS[datetime.date(Y, 1, 1).weekday()],
    ]
    out_folder = str(out_dir) if (out_dir is not None and len(u"%s" % out_dir) > 0) else EPW_DIR
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    fn = ("GE_lat%.3f_lon%.3f_%d.epw" % (q_lat, q_lon, Y)).replace(".", "p").replace("-", "n")
    fn = fn.replace("pepw", ".epw")
    epw_path = os.path.join(out_folder, fn)
    f = open(epw_path, "w")
    try:
        f.write("\n".join(header + rows) + "\n")
    finally:
        f.close()

    mk, sk = met_key(q_lat, q_lon), sol_key(q_lat, q_lon)
    mc = (mk[0] * 0.5, -180.0 + 0.625 * mk[1])
    miss_txt = u" , ".join([u"%s=%d" % (k, miss[k]) for k in sorted(miss.keys())])
    tz_en = u"UTC%+d" % tzi
    if loc.get("tz_default"):
        tz_en += u" (default: Syria's official time since Oct 2022)"
    en = [u"EPW file created: %s" % epw_path,
          u"Location / Coordinates: %s" % loc.get("label_en", city_s),
          u"Latitude: %.4f" % q_lat, u"Longitude: %.4f" % q_lon, u"Time zone: %s" % tz_en,
          u"Actual year: %d" % Y, u"Rows: %d (Feb 29 removed)" % len(rows),
          (u"Elevation: site %.0f m (grid cell %.0f m); temperature, pressure and dew point adjusted with a simple method (6.5 K/km lapse, standard-atmosphere pressure, constant mixing ratio); wind and solar not adjusted; not validated." % (se, elev))
          if se is not None else (u"Elevation (weather-grid cell, not the actual site): %.0f m" % elev),
          u"Weather cell (~0.5 x 0.625 deg): center (%.2f, %.3f) | Solar cell (~1 x 1 deg): from (%d, %d) to (%d, %d)" % (
              mc[0], mc[1], sk[0], sk[1], sk[0] + 1, sk[1] + 1)]
    ar = [rtl(u"تم إنشاء ملف EPW: %s" % ltr(epw_path)),
          rtl(u"المنطقة / الإحداثيات: %s" % loc.get("name_ar", city_s)),
          rtl(u"خط العرض: %s" % ltr(u"%.4f" % q_lat)), rtl(u"خط الطول: %s" % ltr(u"%.4f" % q_lon)),
          rtl(u"المنطقة الزمنية: %s" % ltr(u"UTC%+d" % tzi)),
          rtl(u"السنة الفعلية: %s" % ltr(u"%d" % Y)), rtl(u"عدد الصفوف: %s (بعد حذف 29 شباط)" % ltr(u"%d" % len(rows))),
          (rtl(u"الارتفاع: الموقع %s م (خلية الأرصاد %s م)؛ صُحّحت الحرارة والضغط ونقطة الندى بطريقة بسيطة (تدرج 6.5 كلفن/كم، ضغط الغلاف المعياري، ثبات نسبة الخلط)؛ لا تصحيح للرياح والإشعاع؛ غير مُتحقَّق منه." % (ltr(u"%.0f" % se), ltr(u"%.0f" % elev))))
          if se is not None else rtl(u"الارتفاع (خلية الأرصاد، ليس الموقع الفعلي): %s م" % ltr(u"%.0f" % elev)),
          rtl(u"خلية الأرصاد: مركزها %s | خلية الإشعاع: من %s إلى %s" % (
              ltr(u"(%.2f, %.3f)" % mc), ltr(u"(%d, %d)" % (sk[0], sk[1])), ltr(u"(%d, %d)" % (sk[0] + 1, sk[1] + 1))))]
    if miss:
        en.append(u"Missing values written with the format's codes: %s" % miss_txt)
        ar.append(rtl(u"قيم مفقودة كُتبت برموز الصيغة: %s" % ltr(miss_txt)))
    else:
        en.append(u"No missing values in the variables taken from NASA.")
        ar.append(rtl(u"لا قيم مفقودة بالمتغيرات المأخوذة من NASA."))
    if ghi_ratio:
        inside = 100.0 * len([r for r in ghi_ratio if 0.85 <= r <= 1.15]) / len(ghi_ratio)
        mean_r = sum(ghi_ratio) / len(ghi_ratio)
        en.append(u"Radiation consistency: GHI/(DNI*cos z + DHI) averages %.3f, with %.0f%% of hours within +/-15%% (approximate)." % (mean_r, inside))
        ar.append(rtl(u"اتساق الإشعاع: نسبة GHI/(DNI*cos z + DHI) متوسطها %s، و%s من الساعات ضمن ±15%% (تقريبي)." % (
            ltr(u"%.3f" % mean_r), ltr(u"%.0f%%" % inside))))
    if rh_diff:
        md_ = sum(rh_diff) / len(rh_diff)
        en.append(u"Humidity vs dew point: mean absolute difference %.2f percentage points (Magnus formula)." % md_)
        ar.append(rtl(u"الرطوبة مقابل نقطة الندى: متوسط الفرق المطلق %s نقطة مئوية (معادلة Magnus)." % ltr(u"%.2f" % md_)))
    en += [u"", u"Ladybug: wire epw_path to the _epw_file input of Import EPW. Ladybug reads the format's missing codes (e.g. 999999) as ordinary numbers, so avoid the illuminance, visibility, ceiling, weather, snow, aerosol, opaque-sky-cover and night-albedo fields.",
           u"Not yet validated with EnergyPlus/Honeybee. Reanalysis data, not station measurements."]
    ar += [u"", rtl(u"Ladybug: وصّل epw_path بمدخل _epw_file في Import EPW. تقرأ Ladybug رموز المفقود بالصيغة (مثل 999999) كأرقام عادية، فتجنب حقول الإضاءة والرؤية وارتفاع الغيوم والطقس والثلج والهباء والغطاء المعتم وانعكاسية الليل."),
           rtl(u"لم يُتحقق منه بعد مع EnergyPlus/Honeybee. بيانات إعادة تحليل، وليست قياس محطات.")]
    for n_en, n_ar in notes:
        en.append(n_en)
        ar.append(rtl(n_ar))
    return {"epw_path": epw_path, "lat": q_lat, "lon": q_lon, "tz": float(tzi), "elev": elev_out, "city": city_s,
            "T_m": T_m, "GHI_m": GHI_m, "report_en": u"\n".join(en), "report_ar": u"\n".join(ar)}


def export_tmy(loc, y_from=None, y_to=None, out_dir=None, city=None, site_elev=None):
    """يصدّر EPW لسنة نموذجية (TMY) بطريقة NREL TMY3 من حوض سنوات (الافتراضي 2002 حتى آخر سنة مكتملة)."""
    notes = []
    q_lat, q_lon = loc["lat"], loc["lon"]
    if loc.get("tz") is None:
        raise ValueError(bi(u"EPW export needs a time zone: set tz in GE Location", u"تصدير EPW يحتاج المنطقة الزمنية: حدّد tz في GE Location"))
    tzv = float(loc["tz"])
    if abs(tzv - round(tzv)) > 1e-9:
        raise ValueError(bi(u"Non-integer UTC offsets (e.g. 5.5) are not supported yet", u"الإزاحة الزمنية غير الصحيحة (مثل 5.5) غير مدعومة بعد"))
    tzi = int(round(tzv))
    end_target = datetime.date.today() - datetime.timedelta(days=END_LAG_DAYS)
    last_year = end_target.year - 1
    y0 = int(y_from) if y_from is not None else TMY_POOL_START
    y1 = int(y_to) if y_to is not None else last_year
    if y0 < TMY_POOL_START:
        raise ValueError(bi(u"The year pool cannot start before %d (hourly data start in 2001 and need the previous Dec 31)" % TMY_POOL_START,
                            u"لا يمكن أن يبدأ حوض السنوات قبل %d (البيانات الساعية تبدأ 2001 وتحتاج 31 كانون الأول السابق)" % TMY_POOL_START))
    if y1 > last_year:
        raise ValueError(bi(u"The year pool must end at or before %d (last complete year)" % last_year,
                            u"يجب أن ينتهي حوض السنوات عند %d أو قبله (آخر سنة مكتملة)" % last_year))
    years = list(range(y0, y1 + 1))
    if len(years) < TMY_MIN_YEARS:
        raise ValueError(bi(u"The year pool must have at least %d years" % TMY_MIN_YEARS, u"يجب أن يضم حوض السنوات %d سنوات على الأقل" % TMY_MIN_YEARS))
    met_d, _n1 = ensure_group("met", q_lat, q_lon, False, notes)
    sol_d, _n2 = ensure_group("sol", q_lat, q_lon, False, notes)
    sel, pool = select_tmy_months(met_d, sol_d, years)
    src_years = [s["year"] for s in sel]
    hourly = {}
    for ys in sorted(set(src_years)):
        hourly[ys] = (get_hourly("met", q_lat, q_lon, ys, notes), get_hourly("sol", q_lat, q_lon, ys, notes))
    elev = hourly[src_years[0]][0]["elev"]
    se, p_ratio = _site_elev_setup(site_elev, elev, notes)
    elev_out = se if se is not None else elev
    city_s = ascii_only(city) if (city is not None and len(u"%s" % city) > 0) else ascii_only(loc.get("name_en", u"site"))
    region = ascii_only(loc.get("gov_en", u"NA"))
    country = loc.get("country", "NA")
    recs = _hourly_records(q_lat, q_lon, tzi, src_years, hourly, se, elev, p_ratio)
    n_sm = _smooth_interfaces(recs, src_years)
    miss = {}
    rows = _format_records(recs, miss)
    if len(rows) != 8760:
        raise ValueError(u"rows %d != 8760" % len(rows))
    T_m, GHI_m, ghi_ratio, rh_diff = _record_stats(recs)
    comp = _tmy_vs_longterm(pool, sel, years)
    yrs_txt = "; ".join(["%s=%d" % (MONTHS_EN[k][:3], src_years[k]) for k in range(12)])
    c1 = ("GoldenEagle %s: TYPICAL meteorological year (NREL TMY3/Sandia method) from NASA POWER reanalysis, year pool %d-%d. "
          "Months from years: %s. NOT station measurements. Standard time UTC%+d." % (VERSION, y0, y1, yrs_txt, tzi))
    c2 = ("Deviations from TMY3: daily dew point mean only; step-2 ranking, run definition and 6 h smoothing are GoldenEagle choices. "
          "Missing: illuminance visibility ceiling weather codes snow aerosol opaque sky cover. Elevation and pressure are grid-cell values. Not for extreme design or wind energy.")
    if se is not None:
        c2 += (" Temperature, pressure and dew point adjusted from grid-cell elevation %.0f m to site elevation %.0f m "
               "(6.5 K/km lapse, standard-atmosphere pressure, constant mixing ratio); wind and solar not adjusted." % (elev, se))
    header = [
        "LOCATION,%s,%s,%s,NASA-POWER-reanalysis,999999,%.4f,%.4f,%.1f,%.1f" % (city_s, region, country, q_lat, q_lon, float(tzi), elev_out),
        "DESIGN CONDITIONS,0", "TYPICAL/EXTREME PERIODS,0", "GROUND TEMPERATURES,0", "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,%s" % c1, "COMMENTS 2,%s" % c2, "DATA PERIODS,1,1,Data,Sunday,1/1,12/31",
    ]
    out_folder = str(out_dir) if (out_dir is not None and len(u"%s" % out_dir) > 0) else EPW_DIR
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    fn = ("GE_TMY_lat%.3f_lon%.3f_%d-%d.epw" % (q_lat, q_lon, y0, y1)).replace(".", "p").replace("-", "n")
    fn = fn.replace("pepw", ".epw")
    epw_path = os.path.join(out_folder, fn)
    f = open(epw_path, "w")
    try:
        f.write("\n".join(header + rows) + "\n")
    finally:
        f.close()

    mk, sk = met_key(q_lat, q_lon), sol_key(q_lat, q_lon)
    mc = (mk[0] * 0.5, -180.0 + 0.625 * mk[1])
    tz_en = u"UTC%+d" % tzi + (u" (default: Syria's official time since Oct 2022)" if loc.get("tz_default") else u"")
    en = [u"TMY file created: %s" % epw_path,
          u"Location / Coordinates: %s" % loc.get("label_en", city_s),
          u"Latitude: %.4f" % q_lat, u"Longitude: %.4f" % q_lon, u"Time zone: %s" % tz_en,
          u"Year pool: %d-%d (%d years)" % (y0, y1, len(years)), u"Rows: %d (Feb 29 removed)" % len(rows), u"",
          u"Month | Selected year | Candidates (best first) | Persistence"]
    ar = [rtl(u"تم إنشاء ملف TMY: %s" % ltr(epw_path)),
          rtl(u"المنطقة / الإحداثيات: %s" % loc.get("name_ar", city_s)),
          rtl(u"خط العرض: %s" % ltr(u"%.4f" % q_lat)), rtl(u"خط الطول: %s" % ltr(u"%.4f" % q_lon)),
          rtl(u"المنطقة الزمنية: %s" % ltr(u"UTC%+d" % tzi)),
          rtl(u"حوض السنوات: %s (%s سنة)" % (ltr(u"%d-%d" % (y0, y1)), ltr(u"%d" % len(years)))),
          rtl(u"عدد الصفوف: %s (بعد حذف 29 شباط)" % ltr(u"%d" % len(rows))), u"",
          rtl(u"الشهر | السنة المختارة | المرشحون (الأفضل أولًا) | الاستمرارية")]
    for s in sel:
        pers_en = u"ignored (all candidates excluded)" if s["persistence_ignored"] else (u"%d excluded" % len(s["excluded"]) if s["excluded"] else u"ok")
        pers_ar = u"أُهملت (استُبعد كل المرشحين)" if s["persistence_ignored"] else (u"%d مستبعدة" % len(s["excluded"]) if s["excluded"] else u"سليمة")
        en.append(u"%-10s | %d | %s | %s" % (MONTHS_EN[s["month"] - 1], s["year"], u",".join([u"%d" % y for y in s["ranked"]]), pers_en))
        ar.append(rtl(u"%s | %s | %s | %s" % (MONTHS_AR[s["month"] - 1].ljust(12), ltr(u"%d" % s["year"]),
                                              ltr(u",".join([u"%d" % y for y in s["ranked"]])), pers_ar)))
    if comp:
        dT = comp["DB_MEAN"][0] - comp["DB_MEAN"][1]
        dG = 100.0 * (comp["GHI"][0] / comp["GHI"][1] - 1.0)
        dN = 100.0 * (comp["DNI"][0] / comp["DNI"][1] - 1.0)
        en += [u"", u"TMY vs the pool's long-term values (daily data): mean temperature %+.2f degC; annual GHI %+.1f%%; annual DNI %+.1f%%." % (dT, dG, dN)]
        ar += [u"", rtl(u"السنة النموذجية مقابل المدى الطويل للحوض (بيانات يومية): متوسط الحرارة %s °م؛ GHI السنوي %s؛ DNI السنوي %s." % (
            ltr(u"%+.2f" % dT), ltr(u"%+.1f%%" % dG), ltr(u"%+.1f%%" % dN)))]
    en.append(u"Interfaces smoothed (6 h each side, only between months from different years): %d" % n_sm)
    ar.append(rtl(u"حدود الأشهر المنعَّمة (6 ساعات من كل جانب، فقط بين أشهر من سنوات مختلفة): %s" % ltr(u"%d" % n_sm)))
    en += [u"", u"Method: NREL TMY3 (Sandia): Finkelstein-Schafer statistic with TMY3 weights, five candidates, persistence of mean temperature and of global and direct radiation. Deviations: NASA gives no daily dew-point max/min, so the dew-point weight sits on its daily mean; the step-2 ranking metric, the run definition (2+ consecutive days) and the interface smoothing are GoldenEagle choices because the references do not specify them.",
           u"Limits: the pool (%d years) is shorter than the usual 30; months are chosen from NASA daily values; a TMY is not suited to extreme design conditions or wind-energy studies; elevation and pressure belong to the grid cell." % len(years)]
    ar += [u"", rtl(u"الطريقة: NREL TMY3 (Sandia): إحصائية Finkelstein-Schafer بأوزان TMY3، وخمسة مرشحين، واستمرارية متوسط الحرارة والإشعاع الكلي والمباشر. الانحرافات: لا توفر NASA نقطة الندى العظمى/الصغرى يوميًا فوضع وزن الندى على متوسطها اليومي؛ ومقياس ترتيب الخطوة 2 وتعريف السلسلة (يومان متتاليان فأكثر) وتنعيم الحدود خيارات GoldenEagle لأن المراجع لا تحددها."),
           rtl(u"الحدود: الحوض (%s سنة) أقصر من المعتاد (30)؛ الأشهر تُختار من القيم اليومية لـ NASA؛ السنة النموذجية لا تناسب ظروف التصميم القصوى ولا دراسات طاقة الرياح؛ الارتفاع والضغط لخلية الشبكة." % ltr(u"%d" % len(years)))]
    if miss:
        mt = u" , ".join([u"%s=%d" % (k, miss[k]) for k in sorted(miss.keys())])
        en.append(u"Missing values written with the format's codes: %s" % mt)
        ar.append(rtl(u"قيم مفقودة كُتبت برموز الصيغة: %s" % ltr(mt)))
    if ghi_ratio:
        inside = 100.0 * len([r for r in ghi_ratio if 0.85 <= r <= 1.15]) / len(ghi_ratio)
        mean_r = sum(ghi_ratio) / len(ghi_ratio)
        en.append(u"Radiation consistency: GHI/(DNI*cos z + DHI) averages %.3f, with %.0f%% of hours within +/-15%% (approximate)." % (mean_r, inside))
        ar.append(rtl(u"اتساق الإشعاع: نسبة GHI/(DNI*cos z + DHI) متوسطها %s، و%s من الساعات ضمن ±15%% (تقريبي)." % (ltr(u"%.3f" % mean_r), ltr(u"%.0f%%" % inside))))
    if se is not None:
        en.append(u"Elevation: site %.0f m (grid cell %.0f m); simple unvalidated correction applied to temperature, pressure and dew point." % (se, elev))
        ar.append(rtl(u"الارتفاع: الموقع %s م (الخلية %s م)؛ طُبّق تصحيح بسيط غير مُتحقَّق منه على الحرارة والضغط ونقطة الندى." % (ltr(u"%.0f" % se), ltr(u"%.0f" % elev))))
    else:
        en.append(u"Elevation (weather-grid cell, not the actual site): %.0f m" % elev)
        ar.append(rtl(u"الارتفاع (خلية الأرصاد، ليس الموقع الفعلي): %s م" % ltr(u"%.0f" % elev)))
    en.append(u"Weather cell (~0.5 x 0.625 deg): center (%.2f, %.3f) | Solar cell (~1 x 1 deg): from (%d, %d) to (%d, %d)" % (mc[0], mc[1], sk[0], sk[1], sk[0] + 1, sk[1] + 1))
    ar.append(rtl(u"خلية الأرصاد: مركزها %s | خلية الإشعاع: من %s إلى %s" % (ltr(u"(%.2f, %.3f)" % mc), ltr(u"(%d, %d)" % (sk[0], sk[1])), ltr(u"(%d, %d)" % (sk[0] + 1, sk[1] + 1)))))
    le, la = _ladybug_lines()
    en += le
    ar += la
    for n_en, n_ar in notes:
        en.append(n_en)
        ar.append(rtl(n_ar))
    return {"epw_path": epw_path, "lat": q_lat, "lon": q_lon, "tz": float(tzi), "elev": elev_out, "city": city_s,
            "T_m": T_m, "GHI_m": GHI_m, "years": src_years, "report_en": u"\n".join(en), "report_ar": u"\n".join(ar)}


# ====================================================================================
# الاختصاصات الهندسية: معماري، مدني، ميكانيكي، كهربائي، زراعي
# كل أداة: بيانات يومية من الكاش (افتراضيًا الفترة المعيارية 1991-2020) + تقرير بلغتين. التبسيطات مذكورة بالتقرير.
# ====================================================================================
DISC_Y0, DISC_Y1 = 1991, 2020
WIND_ALPHA = 0.14          # أُس قانون القدرة لتضاريس مفتوحة (تقريب)
ALBEDO = 0.2               # انعكاس الأرض المفترض
KAABA_LAT, KAABA_LON = 21.4225, 39.8262
KLEIN_DAYS = [17, 47, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344]   # أيام وسط الشهر (Klein 1977، Duffie & Beckman)
DPM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
COMPASS16_EN = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
COMPASS16_AR = [u"شمال", u"شمال شمال شرق", u"شمال شرق", u"شرق شمال شرق", u"شرق", u"شرق جنوب شرق", u"جنوب شرق", u"جنوب جنوب شرق",
                u"جنوب", u"جنوب جنوب غرب", u"جنوب غرب", u"غرب جنوب غرب", u"غرب", u"غرب شمال غرب", u"شمال غرب", u"شمال شمال غرب"]


class _Rep(object):
    """يجمع سطور تقرير بلغتين (العربي مغلّف برموز RTL والأرقام بـ LTR)."""
    def __init__(self):
        self.en = []
        self.ar = []

    def blank(self):
        self.en.append(u"")
        self.ar.append(u"")

    def title(self, en, ar):
        self.en.append(en)
        self.ar.append(rtl(ar))

    def line(self, en, ar, *vals):
        self.en.append(en % tuple(vals))
        self.ar.append(rtl(ar % tuple(ltr(u"%s" % v) for v in vals)))

    def text(self, en, ar):
        self.en.append(en)
        self.ar.append(rtl(ar))

    def table(self, head_en, head_ar, rows, w0=12, w=8):
        """rows: [(label_en, label_ar, [قيم نصية...])]"""
        def en_row(cells):
            return u" | ".join([(c.ljust(w0) if j == 0 else c.rjust(w)) for j, c in enumerate(cells)])

        def ar_row(cells):
            return rtl(u" | ".join([(c.ljust(w0) if j == 0 else ltr(c.rjust(w))) for j, c in enumerate(cells)]))
        self.en.append(en_row(head_en))
        self.ar.append(ar_row(head_ar))
        for le, la, vals in rows:
            self.en.append(en_row([le] + list(vals)))
            self.ar.append(ar_row([la] + list(vals)))

    def out(self, notes=None):
        for n_en, n_ar in (notes or []):
            self.en.append(n_en)
            self.ar.append(rtl(n_ar))
        return u"\n".join(self.en), u"\n".join(self.ar)


def disc_load(loc, y_from, y_to, update, notes, need_sol=True):
    """يحمّل (أو يقرأ من الكاش) المجموعتين اليوميتين ويجهّز فترة التحليل (سنوات كاملة)."""
    q_lat, q_lon = loc["lat"], loc["lon"]
    met, _m = ensure_group("met", q_lat, q_lon, bool(update), notes)
    sol, _s = ensure_group("sol", q_lat, q_lon, bool(update), notes)
    last = min(parse_yyyymmdd(met["last"]), parse_yyyymmdd(sol["last"]))
    lc = last_complete_month(last)
    last_full = lc[0] if lc[1] == 12 else lc[0] - 1
    y0 = int(y_from) if y_from is not None else DISC_Y0
    y1 = int(y_to) if y_to is not None else DISC_Y1
    if y0 < 1981:
        raise ValueError(bi(u"y_from cannot be before 1981", u"y_from لا يمكن أن يسبق 1981"))
    if y1 > last_full:
        raise ValueError(bi(u"y_to cannot be after the last complete year in the cache (%d)" % last_full,
                            u"y_to لا يمكن أن يتجاوز آخر سنة مكتملة بالكاش (%d)" % last_full))
    if y1 < y0:
        raise ValueError(bi(u"y_from is after y_to", u"y_from بعد y_to"))
    i0 = date_to_idx(datetime.date(y0, 1, 1))
    i1 = date_to_idx(datetime.date(y1, 12, 31))
    D = {"loc": loc, "met": met, "sol": sol, "y0": y0, "y1": y1, "n_years": y1 - y0 + 1, "i0": i0, "i1": i1,
         "dates": [ord_to_date(i) for i in range(i0, i1 + 1)], "elev": met.get("elev"), "last": last}
    if D["n_years"] < 10:
        notes.append((u"Warning: the period is under 10 years; statistics (especially extremes) are weak.",
                      u"تنبيه: الفترة أقل من 10 سنوات؛ الإحصاءات (خاصة القيم القصوى) ضعيفة."))
    return D


def _ser(D, grp, par):
    arr = (D["met"] if grp == "met" else D["sol"])["params"].get(par)
    if arr is None:
        return [None] * len(D["dates"])
    i0 = D["i0"]
    return [arr[i] if (0 <= i < len(arr)) else None for i in range(i0, D["i1"] + 1)]


def _valid(vals):
    return [v for v in vals if v is not None]


def _month_means(D, vals):
    s = [0.0] * 12
    n = [0] * 12
    for dte, v in zip(D["dates"], vals):
        if v is not None:
            s[dte.month - 1] += v
            n[dte.month - 1] += 1
    return [(s[k] / n[k]) if n[k] else None for k in range(12)]


def _extreme(D, vals, want_max=True):
    best = None
    for dte, v in zip(D["dates"], vals):
        if v is None:
            continue
        if best is None or (v > best[0] if want_max else v < best[0]):
            best = (v, dte)
    return best


def _per_year(D, vals, fn):
    """يطبّق fn على قائمة (تاريخ، قيمة) لكل سنة ويرجع قائمة النتائج (يتجاهل السنوات الناقصة أكثر من 10%)."""
    by = {}
    for dte, v in zip(D["dates"], vals):
        by.setdefault(dte.year, []).append((dte, v))
    out = []
    for y in sorted(by):
        items = by[y]
        if len([1 for _d, v in items if v is None]) > 0.1 * len(items):
            continue
        out.append(fn(items))
    return out


def _mean_or_none(v):
    return (sum(v) / float(len(v))) if v else None


def _dstr(x):
    return x.isoformat() if x is not None else u"-"


def _ms_to_kmh(v):
    return None if v is None else v * 3.6


# ---------------- فلك ومعادلات مشتركة ----------------
def decl_deg(n):
    eot, decl, e0 = sun_terms(n)
    return math.degrees(decl)


def tilted_beam_ratio(lat_deg, doy, beta_deg, gamma_deg, nsteps=100):
    """نسبة الإشعاع المباشر على سطح مائل (beta) متجه بسمت gamma (0=جنوب، غرب موجب) إلى الأفقي ليوم متوسط الشهر
    (Liu-Jordan / Klein / Duffie-Beckman). تكامل عددي على زاوية الساعة بين شروق وغروب الأفقي."""
    phi = math.radians(lat_deg)
    beta = math.radians(beta_deg)
    gamma = math.radians(gamma_deg)
    delta = math.radians(decl_deg(doy))
    cos_ws = max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta)))
    ws = math.acos(cos_ws)
    num = den = 0.0
    for i in range(nsteps + 1):
        w = -ws + 2 * ws * i / float(nsteps)
        cos_z = math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(w)
        cos_t = ((math.sin(phi) * math.cos(beta) - math.cos(phi) * math.sin(beta) * math.cos(gamma)) * math.sin(delta)
                 + (math.cos(phi) * math.cos(beta) + math.sin(phi) * math.sin(beta) * math.cos(gamma)) * math.cos(delta) * math.cos(w)
                 + math.cos(delta) * math.sin(beta) * math.sin(gamma) * math.sin(w))
        wgt = 0.5 if i in (0, nsteps) else 1.0
        num += wgt * max(cos_t, 0.0)
        den += wgt * max(cos_z, 0.0)
    return num / den if den > 0 else 0.0


def plane_irradiation_monthly(lat, ghi_m, dhi_m, beta_deg, gamma_deg, nsteps=100):
    """إشعاع شهري متوسط يومي (kWh/m2/day) على سطح مائل بنموذج السماء المتجانسة (Liu-Jordan) وانعكاس أرض ALBEDO."""
    out = []
    br = math.radians(beta_deg)
    for k in range(12):
        if ghi_m[k] is None or dhi_m[k] is None:
            out.append(None)
            continue
        H = ghi_m[k]
        Hd = min(dhi_m[k], H)
        Hb = H - Hd
        Rb = tilted_beam_ratio(lat, KLEIN_DAYS[k], beta_deg, gamma_deg, nsteps)
        out.append(Hb * Rb + Hd * (1 + math.cos(br)) / 2.0 + ALBEDO * H * (1 - math.cos(br)) / 2.0)
    return out


def _annual_from_monthly(vals):
    return sum(vals[k] * DPM[k] for k in range(12) if vals[k] is not None)


def extraterrestrial_mm(lat_deg, doy):
    """الإشعاع خارج الغلاف الأفقي اليومي معبَّرًا بالتبخر المكافئ (ملم/يوم)، معادلات FAO-56."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365.0)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365.0 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    return 0.408 * ra


def wet_bulb(t_c, rh_pct):
    """تقريب Stull (2011) لحرارة الترمومتر المبتل؛ صالح تقريبًا لـ -20..50°م و5..99% رطوبة."""
    rh = max(5.0, min(99.0, rh_pct))
    return (t_c * math.atan(0.151977 * math.sqrt(rh + 8.313659)) + math.atan(t_c + rh) - math.atan(rh - 1.676331)
            + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh) - 4.686035)


def sector16(deg):
    return int(((deg + 11.25) % 360.0) / 22.5)


# ---------------- مساعدات الاختصاصات (درجات يوم، أشهر، رياح ساعية) ----------------
def _month_totals(D, vals):
    """متوسط مجموع كل شهر تقويمي عبر السنوات (تُهمل الأشهر الناقصة أكثر من 10%)، وللهطول والدرجات-يوم."""
    sums = {}
    cnts = {}
    for dte, v in zip(D["dates"], vals):
        key = (dte.year, dte.month)
        cnts[key] = cnts.get(key, [0, 0])
        cnts[key][1] += 1
        if v is not None:
            sums[key] = sums.get(key, 0.0) + v
            cnts[key][0] += 1
    tot = [0.0] * 12
    n = [0] * 12
    for key, (ok, allc) in cnts.items():
        if ok >= 0.9 * allc and ok > 0:
            tot[key[1] - 1] += sums.get(key, 0.0) / ok * allc
            n[key[1] - 1] += 1
    return [(tot[k] / n[k]) if n[k] else None for k in range(12)]


def _degree_days(D, tvals, base, heating=True):
    dd = [(max(base - t, 0.0) if heating else max(t - base, 0.0)) if t is not None else None for t in tvals]
    monthly = _month_totals(D, dd)
    return monthly, sum([m for m in monthly if m is not None])


def _last_full_year(D):
    lc = last_complete_month(D["last"])
    return lc[0] if lc[1] == 12 else lc[0] - 1


def _recent_years(D, n):
    last = _last_full_year(D)
    ys = list(range(max(2002, last - int(n) + 1), last + 1))
    return ys


def _hourly_year_arrays(loc, years, notes, params):
    """بيانات ساعية (مجموعة الأرصاد) لسنوات كاملة؛ تُقتطع منها ساعات السنة نفسها (نافذة التحميل تضم 31 كانون الأول و1 كانون الثاني)."""
    out = dict((p, []) for p in params)
    for y in years:
        met = get_hourly("met", loc["lat"], loc["lon"], y, notes)
        for p in params:
            arr = met["params"][p]
            out[p].extend(arr[24:len(arr) - 24])
    return out


# ====================================================================================
# معماري
# ====================================================================================
def qibla_info(lat, lon):
    """اتجاه القبلة: السمت الابتدائي على الدائرة العظمى نحو الكعبة من الشمال الحقيقي (درجات مع عقارب الساعة) والمسافة بالكم."""
    phi1, phi2 = math.radians(lat), math.radians(KAABA_LAT)
    dlon = math.radians(KAABA_LON - lon)
    y = math.sin(dlon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlon)
    a = math.sin((phi2 - phi1) / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlon / 2) ** 2
    dist = 2 * 6371.0 * math.asin(math.sqrt(a))
    bearing = None if dist < 1.0 else (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    return bearing, dist


def sun_day_summary(lat, lon, tz, n):
    """ارتفاع الشمس عند الظهر وطول النهار وساعة الشروق والغروب (توقيت قياسي إن عُرف tz). شروق/غروب عند -0.833 درجة."""
    eot, decl, e0 = sun_terms(n)
    phi = math.radians(lat)
    alt_noon = 90.0 - abs(lat - math.degrees(decl))
    cos_ws = (math.sin(math.radians(-0.833)) - math.sin(phi) * math.sin(decl)) / (math.cos(phi) * math.cos(decl))
    if cos_ws >= 1.0:
        dl = 0.0
    elif cos_ws <= -1.0:
        dl = 24.0
    else:
        dl = 2.0 * math.degrees(math.acos(cos_ws)) / 15.0
    if tz is None:
        return alt_noon, dl, None, None
    noon_clock = 12.0 + tz - lon / 15.0 - eot / 60.0
    return alt_noon, dl, noon_clock - dl / 2.0, noon_clock + dl / 2.0


def _hhmm(h):
    if h is None:
        return u"-"
    h = h % 24.0
    mm = int(round(h * 60.0))
    return u"%02d:%02d" % ((mm // 60) % 24, mm % 60)


def wind_rose(loc, years, notes):
    """وردة رياح من بيانات ساعية (سرعة واتجاه على 10م). الاتجاه = الجهة التي تهب منها الرياح. السكون (<0.5 م/ث) يُعدّ منفصلًا."""
    arr = _hourly_year_arrays(loc, years, notes, ["WS10M", "WD10M"])
    cnt = [0] * 16
    spd = [0.0] * 16
    calm = 0
    n = 0
    for ws, wd in zip(arr["WS10M"], arr["WD10M"]):
        if ws is None or wd is None:
            continue
        n += 1
        if ws < 0.5:
            calm += 1
            continue
        k = sector16(wd)
        cnt[k] += 1
        spd[k] += ws
    total = float(sum(cnt)) if sum(cnt) else 1.0
    freq = [100.0 * c / (n if n else 1) for c in cnt]
    mean_spd = [(spd[k] / cnt[k]) if cnt[k] else None for k in range(16)]
    return {"freq": freq, "mean_speed": mean_spd, "calm_pct": (100.0 * calm / n) if n else None, "n": n}


def arch_report(loc, y_from=None, y_to=None, wind_years=3, overhang_depth=None, window_height=None, update=False):
    notes = []
    D = disc_load(loc, y_from, y_to, update, notes)
    lat, lon, tz = loc["lat"], loc["lon"], loc.get("tz")
    R = _Rep()
    # ---- القبلة
    qb, qd = qibla_info(lat, lon)
    qvec = None
    if qb is not None:
        vx, vy = math.sin(math.radians(qb)), math.cos(math.radians(qb))
        try:
            import Rhino.Geometry as rg
            qvec = rg.Vector3d(vx, vy, 0.0)
        except Exception:
            qvec = (vx, vy, 0.0)
    # ---- الشمس
    suns = [(u"Mar 21", u"21 آذار", 80), (u"Jun 21", u"21 حزيران", 172), (u"Sep 23", u"23 أيلول", 266), (u"Dec 21", u"21 كانون الأول", 355)]
    sun_rows = []
    noon_alt = []
    for le, la, n in suns:
        a_, dl, sr, ss = sun_day_summary(lat, lon, tz, n)
        noon_alt.append(a_)
        sun_rows.append((le, la, [u"%.1f" % a_, u"%.2f" % dl, _hhmm(sr), _hhmm(ss)]))
    # ---- بيانات مناخية
    t_d = _ser(D, "met", "T2M")
    T = _month_means(D, t_d)
    G = _month_means(D, _ser(D, "sol", "ALLSKY_SFC_SW_DWN"))
    F = _month_means(D, _ser(D, "sol", "ALLSKY_SFC_SW_DIFF"))
    hdd_m, hdd = _degree_days(D, t_d, 18.0, True)
    cdd_m, cdd = _degree_days(D, t_d, 24.0, False)
    gam = {"N": 180.0, "E": -90.0, "S": 0.0, "W": 90.0}
    fac_m = dict((f, plane_irradiation_monthly(lat, G, F, 90.0, g)) for f, g in gam.items())
    heat_idx = [k for k in range(12) if T[k] is not None and T[k] < 18.0]
    cool_idx = [k for k in range(12) if T[k] is not None and T[k] > 24.0]
    tot = hdd + cdd
    w_h, w_c = ((hdd / tot), (cdd / tot)) if tot > 0 else (0.5, 0.5)

    def season_mean(f, idxs):
        v = [fac_m[f][k] for k in idxs if fac_m[f][k] is not None]
        return (sum(v) / len(v)) if v else 0.0
    gw = dict((f, season_mean(f, heat_idx)) for f in gam)
    gs = dict((f, season_mean(f, cool_idx)) for f in gam)
    score = dict((f, w_h * gw[f] - w_c * gs[f]) for f in gam)
    rank = sorted(gam, key=lambda f: (round(score[f], 4), -1 if f == "W" else 0), reverse=True)
    fac_names = ["N", "E", "S", "W"]
    fac_kwh = [_annual_from_monthly(fac_m[f]) for f in fac_names]
    fac_en = {"N": u"North", "E": u"East", "S": u"South", "W": u"West"}
    fac_ar = {"N": u"الشمالية", "E": u"الشرقية", "S": u"الجنوبية", "W": u"الغربية"}
    # ---- الغيوم (مؤشر الصفاء Kt)
    ghi_d = _ser(D, "sol", "ALLSKY_SFC_SW_DWN")
    clr_d = _ser(D, "sol", "CLRSKY_SFC_SW_DWN")
    kt = [(g / c) if (g is not None and c not in (None, 0)) else None for g, c in zip(ghi_d, clr_d)]
    ktv = _valid(kt)
    sunny = 100.0 * len([k for k in ktv if k >= 0.7]) / len(ktv) if ktv else None
    partly = 100.0 * len([k for k in ktv if 0.4 <= k < 0.7]) / len(ktv) if ktv else None
    cloudy = 100.0 * len([k for k in ktv if k < 0.4]) / len(ktv) if ktv else None
    # ---- الرياح الساعية (اختياري)
    wr = None
    if wind_years is not None and int(wind_years) > 0:
        wy = _recent_years(D, int(wind_years))
        try:
            wr = wind_rose(loc, wy, notes)
        except Exception as ex:
            notes.append((u"Wind rose unavailable: %s" % msg(ex), u"وردة الرياح غير متاحة: %s" % msg(ex)))
    prev_k = None
    windward = []
    if wr and wr["n"] and max(wr["freq"]) > 0:
        prev_k = wr["freq"].index(max(wr["freq"]))
        th = prev_k * 22.5
        for f, ang in (("N", 0.0), ("E", 90.0), ("S", 180.0), ("W", 270.0)):
            dd = abs(((th - ang) + 180.0) % 360.0 - 180.0)
            if dd <= 67.5:
                windward.append(f)
    # ================= التقرير =================
    R.title(u"Location: %s | Latitude %.4f | Longitude %.4f" % (loc["label_en"], lat, lon),
            u"الموقع: %s | خط العرض %s | خط الطول %s" % (loc["name_ar"], ltr(u"%.4f" % lat), ltr(u"%.4f" % lon)))
    R.line(u"Climate period for the statistics: %s (%s years)", u"فترة الإحصاءات المناخية: %s (%s سنة)",
           u"%d-%d" % (D["y0"], D["y1"]), D["n_years"])
    R.blank()
    R.title(u"== Qibla ==", u"== القبلة ==")
    if qb is None:
        R.text(u"The site is at the Kaaba.", u"الموقع عند الكعبة.")
    else:
        k8 = sector16(qb)
        R.line(u"Bearing from TRUE north (clockwise): %s deg (%s)", u"الزاوية من الشمال الحقيقي (مع عقارب الساعة): %s درجة (%s)", u"%.1f" % qb, COMPASS16_EN[k8])
        R.line(u"Distance to the Kaaba: %s km", u"المسافة إلى الكعبة: %s كم", u"%.0f" % qd)
        R.text(u"A magnetic compass shows MAGNETIC north: correct by the local declination. In Rhino the output vector assumes true north = +Y; rotate it if your project north differs.",
               u"البوصلة المغناطيسية تعرض الشمال المغناطيسي: صحّح بانحراف الموقع. بمخرج المتجه لـ Rhino الشمال الحقيقي = +Y؛ دوّره إذا اختلف شمال مشروعك.")
    R.blank()
    R.title(u"== Sun (astronomical, standard time%s) ==" % (u"" if tz is not None else u"; set tz in GE Location for clock times"),
            u"== الشمس (حساب فلكي، التوقيت القياسي%s) ==" % (u"" if tz is not None else u"؛ حدّد tz في GE Location لأوقات الساعة"))
    R.table([u"Date", u"NoonAlt", u"DayLen h", u"Sunrise", u"Sunset"], [u"التاريخ", u"ارتفاع الظهر", u"طول النهار", u"الشروق", u"الغروب"], sun_rows, w0=15, w=9)
    R.blank()
    R.title(u"== Horizontal overhang on the equator-facing facade ==", u"== كاسر شمس أفقي على الواجهة المواجهة لخط الاستواء ==")
    hdr_en = [u"Month", u"NoonAlt", u"FullShade m/m"]
    hdr_ar = [u"الشهر", u"ارتفاع الظهر", u"عمق ظل كامل م/م"]
    wh = float(window_height) if window_height not in (None, 0) else 1.0
    od = float(overhang_depth) if overhang_depth is not None else None
    if od is not None:
        hdr_en.append(u"Shaded %")
        hdr_ar.append(u"المظلّل %")
    rows = []
    for k in range(12):
        a_ = 90.0 - abs(lat - decl_deg(KLEIN_DAYS[k]))
        depth = (1.0 / math.tan(math.radians(a_))) if a_ > 0.5 else None
        vals = [u"%.1f" % a_, (u"%.2f" % depth) if depth is not None else u"-"]
        if od is not None:
            sh = min(1.0, od * math.tan(math.radians(a_)) / wh) * 100.0 if a_ > 0.5 else 0.0
            vals.append(u"%.0f" % sh)
        rows.append((MONTHS_EN[k], MONTHS_AR[k], vals))
    R.table(hdr_en, hdr_ar, rows, w0=12, w=14)
    R.text(u"FullShade = overhang depth per 1 m of window height that fully shades the window at solar noon on the 21st (depth = height / tan(altitude)). Shaded %% uses depth %s m and window height %s m. Noon profile only: other hours and facade azimuths need more depth; no side fins, obstructions or setback." % (
        (u"%.2f" % od) if od is not None else u"-", u"%.2f" % wh),
        u"ظل كامل = عمق الكاسر لكل 1 م من ارتفاع النافذة اللازم لتظليلها كليًا عند الظهر الشمسي يوم 21 (العمق = الارتفاع / ظل زاوية الارتفاع). نسبة المظلّل بعمق %s م وارتفاع نافذة %s م. هذا للظهيرة فقط: بقية الساعات وسموت الواجهات تحتاج عمقًا أكبر؛ بلا زعانف جانبية أو عوائق أو تراجع." % (
        (u"%.2f" % od) if od is not None else u"-", u"%.2f" % wh))
    R.blank()
    R.title(u"== Facade guide (rule of thumb) ==", u"== دليل الواجهات (قاعدة إرشادية) ==")
    rows = [(fac_en[f], fac_ar[f], [u"%.2f" % gw[f], u"%.2f" % gs[f], u"%.2f" % score[f], u"%.0f" % fac_kwh[fac_names.index(f)]]) for f in rank]
    R.table([u"Facade", u"WinterGain", u"SummerLoad", u"Score", u"kWh/m2/yr"], [u"الواجهة", u"كسب شتوي", u"حمل صيفي", u"النقاط", u"kWh/m2/سنة"], rows, w0=12, w=11)
    R.text(
        u"Best facade for large windows: %s | Highest summer load (good for services/storage): %s" % (fac_en[rank[0]], fac_en[rank[-1]]),
        u"أفضل واجهة للنوافذ الكبيرة: %s | أعلى حمل صيفي (مناسبة للخدمات والمخازن): %s" % (fac_ar[rank[0]], fac_ar[rank[-1]]))
    R.text(u"Method: monthly mean GHI and DHI on vertical surfaces (Liu-Jordan isotropic sky, ground albedo %.1f, no obstructions, Klein mean days). Score = heating weight x winter gain - cooling weight x summer load, with weights from the degree-days (base 18/24 C), heating months = monthly mean T < 18 C, cooling months > 24 C (kWh/m2/day). A screening rule only: for real facades use Ladybug/Radiance." % ALBEDO,
           u"الطريقة: متوسط GHI وDHI الشهري على أسطح رأسية (سماء متجانسة Liu-Jordan، انعكاس أرض %s، بلا عوائق، أيام Klein). النقاط = وزن التدفئة × الكسب الشتوي - وزن التبريد × الحمل الصيفي، والأوزان من درجات اليوم (الأساس 18/24 °م)، وأشهر التدفئة = متوسط الحرارة الشهري < 18 °م والتبريد > 24 °م (kWh/m2/يوم). قاعدة فرز أولي فقط: للواجهات الفعلية استخدم Ladybug/Radiance." % ltr(u"%.1f" % ALBEDO))
    R.blank()
    R.title(u"== Sky conditions (daily clearness index Kt = GHI / clear-sky GHI) ==", u"== حالة السماء (مؤشر الصفاء اليومي Kt = GHI / GHI بسماء صافية) ==")
    R.line(u"Sunny (Kt>=0.7): %s%% | Partly cloudy (0.4-0.7): %s%% | Cloudy (<0.4): %s%% of days (thresholds are conventions)",
           u"مشمس (Kt>=0.7): %s%% | غائم جزئيًا (0.4-0.7): %s%% | غائم (<0.4): %s%% من الأيام (العتبات اصطلاحية)",
           fmt(sunny, 0), fmt(partly, 0), fmt(cloudy, 0))
    R.blank()
    R.title(u"== Wind ==", u"== الرياح ==")
    if wr and wr["n"]:
        R.line(u"Hourly sample years: %s (%s hours); calm (<0.5 m/s): %s%%", u"سنوات العينة الساعية: %s (%s ساعة)؛ سكون (<0.5 م/ث): %s%%",
               u"%d-%d" % (wy[0], wy[-1]), u"%d" % wr["n"], fmt(wr["calm_pct"], 1))
        R.line(u"Prevailing wind (most frequent, blowing FROM): %s (%s deg), %s%% of hours", u"الرياح السائدة (الأكثر تكرارًا، تهب من): %s (%s درجة)، %s%% من الساعات",
               COMPASS16_EN[prev_k], u"%.1f" % (prev_k * 22.5), fmt(wr["freq"][prev_k], 1))
        R.line(u"Windward facade(s): %s", u"الواجهات المواجهة للرياح: %s", u", ".join(windward) if windward else u"-")
        rows = [(COMPASS16_EN[k], COMPASS16_AR[k], [u"%.1f" % wr["freq"][k], fmt(wr["mean_speed"][k], 1)]) for k in range(16)]
        R.table([u"Sector", u"Freq %", u"Mean m/s"], [u"الجهة", u"التكرار %", u"متوسط م/ث"], rows, w0=16, w=9)
        R.text(u"Reanalysis 10 m winds on a coarse cell; local terrain and buildings change direction and speed.", u"رياح إعادة تحليل على 10 م بخلية خشنة؛ التضاريس والمباني المحلية تغيّر الاتجاه والسرعة.")
    else:
        R.text(u"Wind rose not computed (wind_years = 0 or unavailable). Daily wind direction is not provided by NASA, so it needs hourly data.",
               u"لم تُحسب وردة الرياح (wind_years = 0 أو غير متاحة). لا توفر NASA اتجاه الرياح يوميًا، فتحتاج بيانات ساعية.")
    rep_en, rep_ar = R.out(notes)
    return {"qibla_deg": qb, "qibla_km": qd, "qibla_vec": qvec, "noon_alt": noon_alt,
            "wind_dir": (prev_k * 22.5) if prev_k is not None else None, "wind_dir_name": COMPASS16_EN[prev_k] if prev_k is not None else None,
            "wind_rose": wr["freq"] if wr else None, "facades": fac_names, "facade_kwh": fac_kwh, "best_facade": rank[0],
            "sunny_pct": sunny, "report_en": rep_en, "report_ar": rep_ar}


# ====================================================================================
# مدني
# ====================================================================================
SOIL_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
TEXTURE_NAMES = {
    "sand": (u"Sand", u"رملية"), "loamy_sand": (u"Loamy sand", u"رملية مزيجية"), "sandy_loam": (u"Sandy loam", u"مزيج رملي"),
    "loam": (u"Loam", u"مزيج"), "silt_loam": (u"Silt loam", u"مزيج غريني"), "silt": (u"Silt", u"غرينية"),
    "sandy_clay_loam": (u"Sandy clay loam", u"مزيج طيني رملي"), "clay_loam": (u"Clay loam", u"مزيج طيني"),
    "silty_clay_loam": (u"Silty clay loam", u"مزيج طيني غريني"), "sandy_clay": (u"Sandy clay", u"طينية رملية"),
    "silty_clay": (u"Silty clay", u"طينية غرينية"), "clay": (u"Clay", u"طينية"), "unclassified": (u"Unclassified", u"غير مصنفة")}


def usda_texture_class(sand, silt, clay):
    """تصنيف قوام التربة حسب مثلث USDA (نسب مئوية مجموعها ~100)."""
    if silt + 1.5 * clay < 15:
        return "sand"
    if silt + 1.5 * clay >= 15 and silt + 2 * clay < 30:
        return "loamy_sand"
    if (7 <= clay < 20 and sand > 52 and silt + 2 * clay >= 30) or (clay < 7 and silt < 50 and silt + 2 * clay >= 30):
        return "sandy_loam"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52:
        return "loam"
    if (silt >= 50 and 12 <= clay < 27) or (50 <= silt < 80 and clay < 12):
        return "silt_loam"
    if silt >= 80 and clay < 12:
        return "silt"
    if 20 <= clay < 35 and silt < 28 and sand > 45:
        return "sandy_clay_loam"
    if 27 <= clay < 40 and 20 < sand <= 45:
        return "clay_loam"
    if 27 <= clay < 40 and sand <= 20:
        return "silty_clay_loam"
    if clay >= 35 and sand > 45:
        return "sandy_clay"
    if clay >= 40 and silt >= 40:
        return "silty_clay"
    if clay >= 40 and sand <= 45 and silt < 40:
        return "clay"
    return "unclassified"


def get_soil_profile(lat, lon, notes):
    """قوام التربة من SoilGrids v2.0 (ISRIC، تقدير نموذج عالمي 250م). يُخزَّن بالكاش. أي فشل يرجع None."""
    name = ("soil_%.4f_%.4f" % (lat, lon)).replace(".", "p").replace("-", "n")
    data = load_cache(name)
    if data:
        return data
    try:
        url = ("https://rest.isric.org/soilgrids/v2.0/properties/query?lon=%s&lat=%s&property=clay&property=sand&property=silt"
               "&depth=0-5cm&depth=5-15cm&depth=15-30cm&depth=30-60cm&depth=60-100cm&depth=100-200cm&value=mean" % (lon, lat))
        d = json.loads(http_get(url))
        out = {}
        for layer in d["properties"]["layers"]:
            nm = layer["name"]
            fac = (layer.get("unit_measure") or {}).get("d_factor") or 10
            for dep in layer["depths"]:
                v = (dep.get("values") or {}).get("mean")
                if v is not None:
                    out.setdefault(dep["label"], {})[nm] = v / float(fac)
        if out:
            save_cache(name, out)
            return out
    except Exception as ex:
        notes.append((u"Soil data unavailable: %s" % msg(ex), u"بيانات التربة غير متاحة: %s" % msg(ex)))
    return None


def civil_report(loc, y_from=None, y_to=None, soil=False, update=False):
    notes = []
    D = disc_load(loc, y_from, y_to, update, notes)
    lat, lon = loc["lat"], loc["lon"]
    R = _Rep()
    ws = _ser(D, "met", "WS10M")
    wsx = _ser(D, "met", "WS10M_MAX")
    tx = _ser(D, "met", "T2M_MAX")
    tn = _ser(D, "met", "T2M_MIN")
    pr = _ser(D, "met", "PRECTOTCORR")
    rh = _ser(D, "met", "RH2M")
    wmean = _mean_or_none(_valid(ws))
    wmax_d = _extreme(D, ws, True)
    wmax_h = _extreme(D, wsx, True)
    tx_rec = _extreme(D, tx, True)
    tn_rec = _extreme(D, tn, False)
    ann_tx = _mean_or_none(_per_year(D, tx, lambda items: max(v for _d, v in items if v is not None)))
    ann_tn = _mean_or_none(_per_year(D, tn, lambda items: min(v for _d, v in items if v is not None)))
    rng = [(a - b) for a, b in zip(tx, tn) if a is not None and b is not None]
    rng_mean = _mean_or_none(rng)
    rain_y = _mean_or_none(_per_year(D, pr, lambda items: sum(v for _d, v in items if v is not None)))
    rain_max = _extreme(D, pr, True)
    rain_ymax = _mean_or_none(_per_year(D, pr, lambda items: max(v for _d, v in items if v is not None)))
    frost = _mean_or_none(_per_year(D, tn, lambda items: len([1 for _d, v in items if v is not None and v < 0.0])))
    ftd = [(1 if (a is not None and b is not None and a > 0.0 and b < 0.0) else 0) for a, b in zip(tx, tn)]
    ft = _mean_or_none(_per_year(D, ftd, lambda items: sum(v for _d, v in items)))
    rh_m = _month_means(D, rh)
    rh_y = _mean_or_none(_valid(rh))
    heights = [10, 20, 50]
    f_h = lambda v, h: None if v is None else v * (h / 10.0) ** WIND_ALPHA
    soil_prof = get_soil_profile(lat, lon, notes) if soil else None
    R.title(u"Location: %s | Latitude %.4f | Longitude %.4f" % (loc["label_en"], lat, lon),
            u"الموقع: %s | خط العرض %s | خط الطول %s" % (loc["name_ar"], ltr(u"%.4f" % lat), ltr(u"%.4f" % lon)))
    R.line(u"Climate period for the statistics: %s (%s years)", u"فترة الإحصاءات المناخية: %s (%s سنة)", u"%d-%d" % (D["y0"], D["y1"]), D["n_years"])
    R.line(u"Elevation (weather-grid cell, not the actual site): %s m (standard-atmosphere pressure there ~ %s kPa)",
           u"الارتفاع (خلية الأرصاد، ليس الموقع الفعلي): %s م (الضغط المعياري هناك ~ %s كيلوباسكال)", fmt(D["elev"], 0),
           fmt(101.325 * (1 - 2.25577e-5 * (D["elev"] or 0.0)) ** 5.25588, 1))
    R.blank()
    R.title(u"== Wind (10 m, reanalysis; daily means / hourly means, NOT gusts) ==", u"== الرياح (10 م، إعادة تحليل؛ متوسطات يومية/ساعية وليست هبّات) ==")
    rows = []
    for h in heights:
        rows.append((u"%d m" % h, u"%d م" % h, [fmt(_ms_to_kmh(f_h(wmean, h)), 1), fmt(_ms_to_kmh(f_h(wmax_d[0] if wmax_d else None, h)), 1),
                                                    fmt(_ms_to_kmh(f_h(wmax_h[0] if wmax_h else None, h)), 1)]))
    R.table([u"Height", u"Mean km/h", u"MaxDayMean", u"MaxHourly"], [u"الارتفاع", u"المتوسط كم/سا", u"أعلى متوسط يومي", u"أعلى متوسط ساعي"], rows, w0=10, w=13)
    R.line(u"Record daily-mean wind: %s km/h on %s | record hourly-mean (daily max): %s km/h on %s",
           u"أعلى متوسط يومي: %s كم/سا بتاريخ %s | أعلى متوسط ساعي (أقصى يومي): %s كم/سا بتاريخ %s",
           fmt(_ms_to_kmh(wmax_d[0]) if wmax_d else None, 1), _dstr(wmax_d[1] if wmax_d else None),
           fmt(_ms_to_kmh(wmax_h[0]) if wmax_h else None, 1), _dstr(wmax_h[1] if wmax_h else None))
    R.text(u"Heights above 10 m use a power law with exponent %.2f (open terrain approximation). These are NOT structural design wind speeds: use the applicable Syrian/regional loading code." % WIND_ALPHA,
           u"الارتفاعات فوق 10 م بقانون القدرة بأُس %s (تقريب تضاريس مفتوحة). هذه ليست سرع الرياح التصميمية الإنشائية: استخدم كود الأحمال السوري/الإقليمي المعتمد." % ltr(u"%.2f" % WIND_ALPHA))
    R.blank()
    R.title(u"== Temperature (for expansion joints and cracking) ==", u"== الحرارة (لفواصل التمدد ومقاومة التشقق) ==")
    R.line(u"Record daily maximum: %s C on %s | record daily minimum: %s C on %s", u"أعلى حرارة عظمى مسجّلة: %s °م بتاريخ %s | أدنى حرارة صغرى مسجّلة: %s °م بتاريخ %s",
           fmt(tx_rec[0] if tx_rec else None, 1), _dstr(tx_rec[1] if tx_rec else None), fmt(tn_rec[0] if tn_rec else None, 1), _dstr(tn_rec[1] if tn_rec else None))
    R.line(u"Mean annual maximum: %s C | mean annual minimum: %s C | mean daily range: %s C", u"متوسط العظمى السنوية: %s °م | متوسط الصغرى السنوية: %s °م | المدى اليومي المتوسط: %s °م",
           fmt(ann_tx, 1), fmt(ann_tn, 1), fmt(rng_mean, 1))
    R.line(u"Frost days per year (daily min < 0 C): %s | freeze-thaw days per year (max > 0 and min < 0): %s", u"أيام الصقيع سنويًا (الصغرى < 0 °م): %s | أيام التجمد والذوبان سنويًا (العظمى > 0 والصغرى < 0): %s",
           fmt(frost, 1), fmt(ft, 1))
    R.blank()
    R.title(u"== Rainfall and humidity ==", u"== الهطول والرطوبة ==")
    R.line(u"Mean annual rainfall: %s mm | record daily rainfall: %s mm on %s | mean annual maximum daily rainfall: %s mm",
           u"متوسط الهطول السنوي: %s ملم | أعلى هطول يومي: %s ملم بتاريخ %s | متوسط الأعلى اليومي سنويًا: %s ملم",
           fmt(rain_y, 0), fmt(rain_max[0] if rain_max else None, 1), _dstr(rain_max[1] if rain_max else None), fmt(rain_ymax, 1))
    R.text(u"Reanalysis rainfall smooths extremes and is for preliminary estimates only: for drainage/gutter design use station intensity-duration data.",
           u"هطول إعادة التحليل يلطّف القيم القصوى وللتقدير الأولي فقط: لتصميم التصريف والمزاريب استخدم بيانات شدة-مدة من محطات.")
    R.table([u"Month", u"RH %"], [u"الشهر", u"الرطوبة %"], [(MONTHS_EN[k], MONTHS_AR[k], [fmt(rh_m[k], 0)]) for k in range(12)], w0=12, w=8)
    R.line(u"Mean annual relative humidity: %s%%. Higher humidity speeds concrete carbonation and rebar corrosion: set cover and waterproofing per the applicable code.",
           u"متوسط الرطوبة النسبية السنوي: %s%%. الرطوبة الأعلى تسرّع تكربن الخرسانة وتآكل الحديد: حدّد الغطاء الخرساني والعزل حسب الكود المعتمد.", fmt(rh_y, 0))
    R.blank()
    R.title(u"== Soil (indicative, global model) ==", u"== التربة (تقدير نموذج عالمي) ==")
    if soil_prof:
        rows = []
        for dpt in SOIL_DEPTHS:
            v = soil_prof.get(dpt)
            if v and all(k in v for k in ("sand", "silt", "clay")):
                cls = TEXTURE_NAMES[usda_texture_class(v["sand"], v["silt"], v["clay"])]
                rows.append((dpt, dpt, [u"%.0f" % v["sand"], u"%.0f" % v["silt"], u"%.0f" % v["clay"], cls[0]]))
        R.table([u"Depth", u"Sand %", u"Silt %", u"Clay %", u"Class"], [u"العمق", u"رمل %", u"غرين %", u"طين %", u"الصنف"], rows, w0=10, w=14)
        R.text(u"Soil texture (SoilGrids 250 m, to 2 m) is NOT a geotechnical report: no bearing capacity, expansive or gypsiferous soils. Foundations need a certified lab soil report. Groundwater depth: no verified open source, use local well records.",
               u"قوام التربة (SoilGrids بدقة 250 م حتى 2 م) ليس تقرير تربة هندسيًا: لا يعطي قدرة التحمل ولا التربة الانتفاشية/الجبسية. التأسيس يحتاج تقريرًا مخبريًا معتمدًا. عمق المياه الجوفية: لا مصدر مفتوح موثوق، استخدم بيانات الآبار المحلية.")
    else:
        R.text(u"Soil not requested (set soil = True) or unavailable. Groundwater depth is not available from a verified open source.",
               u"لم تُطلب التربة (فعّل soil = True) أو غير متاحة. عمق المياه الجوفية غير متاح من مصدر مفتوح موثوق.")
    rep_en, rep_ar = R.out(notes)
    soil_txt = None
    if soil_prof:
        soil_txt = [u"%s: sand %.0f silt %.0f clay %.0f -> %s" % (d, soil_prof[d]["sand"], soil_prof[d]["silt"], soil_prof[d]["clay"],
                    TEXTURE_NAMES[usda_texture_class(soil_prof[d]["sand"], soil_prof[d]["silt"], soil_prof[d]["clay"])][0]) for d in SOIL_DEPTHS
                    if d in soil_prof and all(k in soil_prof[d] for k in ("sand", "silt", "clay"))]
    return {"elev": D["elev"], "wind_mean": _ms_to_kmh(wmean), "wind_max": _ms_to_kmh(wmax_h[0]) if wmax_h else None,
            "tmax_rec": tx_rec[0] if tx_rec else None, "tmin_rec": tn_rec[0] if tn_rec else None, "range_mean": rng_mean,
            "rain_year": rain_y, "rain_max_day": rain_max[0] if rain_max else None, "frost_days": frost, "freeze_thaw": ft,
            "rh_mean": rh_y, "soil_info": soil_txt, "report_en": rep_en, "report_ar": rep_ar}


# ====================================================================================
# ميكانيكي
# ====================================================================================
def _design_hourly(loc, years, notes):
    arr = _hourly_year_arrays(loc, years, notes, ["T2M", "RH2M"])
    pairs = [(t, h) for t, h in zip(arr["T2M"], arr["RH2M"]) if t is not None and h is not None]
    ts = sorted([t for t, _h in pairs])
    if not ts:
        return None
    q = lambda p: _quantile(ts, p)
    cool = [q(0.98), q(0.99), q(0.996)]
    heat = [q(0.01), q(0.004)]
    mcwb = []
    for x in cool:
        w = [wet_bulb(t, h) for t, h in pairs if abs(t - x) <= 1.0]
        mcwb.append(_mean_or_none(w))
    return {"cool": cool, "heat": heat, "mcwb": mcwb, "n": len(ts)}


def mech_report(loc, y_from=None, y_to=None, base_heat=18.0, base_cool=24.0, hourly_years=0, update=False):
    notes = []
    D = disc_load(loc, y_from, y_to, update, notes)
    lat, lon = loc["lat"], loc["lon"]
    bh = float(base_heat) if base_heat is not None else 18.0
    bc = float(base_cool) if base_cool is not None else 24.0
    t = _ser(D, "met", "T2M")
    tx = _ser(D, "met", "T2M_MAX")
    tn = _ser(D, "met", "T2M_MIN")
    rh = _ser(D, "met", "RH2M")
    hdd_m, hdd = _degree_days(D, t, bh, True)
    cdd_m, cdd = _degree_days(D, t, bc, False)
    T_m = _month_means(D, t)
    wb = [(wet_bulb(a, b) if (a is not None and b is not None) else None) for a, b in zip(t, rh)]
    wb_m = _month_means(D, wb)
    wbd = [(a - w) if (a is not None and w is not None) else None for a, w in zip(t, wb)]
    wbd_m = _month_means(D, wbd)
    wbv = sorted(_valid(wb))
    wb99 = _quantile(wbv, 0.99) if wbv else None
    txs = sorted(_valid(tx))
    tns = sorted(_valid(tn))
    heat_d = [_quantile(tns, 0.01), _quantile(tns, 0.004)] if tns else [None, None]
    cool_d = [_quantile(txs, 0.99), _quantile(txs, 0.996)] if txs else [None, None]
    hd = None
    hy = None
    if hourly_years is not None and int(hourly_years) > 0:
        hy = _recent_years(D, int(hourly_years))
        try:
            hd = _design_hourly(loc, hy, notes)
        except Exception as ex:
            notes.append((u"Hourly design conditions unavailable: %s" % msg(ex), u"ظروف التصميم الساعية غير متاحة: %s" % msg(ex)))
    R = _Rep()
    R.title(u"Location: %s | Latitude %.4f | Longitude %.4f" % (loc["label_en"], lat, lon),
            u"الموقع: %s | خط العرض %s | خط الطول %s" % (loc["name_ar"], ltr(u"%.4f" % lat), ltr(u"%.4f" % lon)))
    R.line(u"Climate period for the statistics: %s (%s years)", u"فترة الإحصاءات المناخية: %s (%s سنة)", u"%d-%d" % (D["y0"], D["y1"]), D["n_years"])
    R.blank()
    R.title(u"== Degree-days (from daily mean temperature, mean per year) ==", u"== درجات اليوم (من متوسط الحرارة اليومي، متوسط سنوي) ==")
    R.line(u"Annual HDD (base %s C): %s | annual CDD (base %s C): %s degree-days", u"HDD السنوية (الأساس %s °م): %s | CDD السنوية (الأساس %s °م): %s درجة-يوم",
           fmt(bh, 1), fmt(hdd, 0), fmt(bc, 1), fmt(cdd, 0))
    R.text(u"The base temperatures are conventions (user inputs); they are not universal. Preliminary HVAC sizing only.",
           u"درجات الأساس اصطلاحية (مدخلات المستخدم) وليست عالمية. للتحجيم المبدئي لأنظمة التكييف فقط.")
    rows = [(MONTHS_EN[k], MONTHS_AR[k], [fmt(T_m[k], 1), fmt(hdd_m[k], 0), fmt(cdd_m[k], 0), fmt(wb_m[k], 1), fmt(wbd_m[k], 1)]) for k in range(12)]
    R.table([u"Month", u"T C", u"HDD", u"CDD", u"WetBulb C", u"WBdepr C"], [u"الشهر", u"الحرارة °م", u"HDD", u"CDD", u"المبتل °م", u"فرق المبتل °م"], rows, w0=12, w=11)
    R.text(u"Wet-bulb: Stull (2011) approximation from DAILY mean temperature and humidity (averaging bias possible). Wet-bulb depression = T - Twb: larger values mean more evaporative-cooling potential.",
           u"الترمومتر المبتل: تقريب Stull (2011) من متوسط الحرارة والرطوبة اليومي (قد يوجد انحياز متوسطات). فرق المبتل = T - Twb: القيمة الأكبر تعني إمكانية تبريد تبخيري أكبر.")
    R.blank()
    R.title(u"== Design temperatures ==", u"== درجات حرارة التصميم ==")
    R.line(u"From DAILY extremes: heating (daily minimum, 1%% / 0.4%% coldest days): %s / %s C | cooling (daily maximum, 1%% / 0.4%% hottest days): %s / %s C",
           u"من القيم اليومية القصوى: التدفئة (الصغرى اليومية، أبرد 1%% / 0.4%% من الأيام): %s / %s °م | التبريد (العظمى اليومية، أحرّ 1%% / 0.4%% من الأيام): %s / %s °م",
           fmt(heat_d[0], 1), fmt(heat_d[1], 1), fmt(cool_d[0], 1), fmt(cool_d[1], 1))
    R.line(u"99th percentile of daily wet-bulb: %s C", u"المئين 99 للترمومتر المبتل اليومي: %s °م", fmt(wb99, 1))
    if hd:
        R.line(u"From HOURLY data %s (%s hours): cooling dry-bulb 2%% / 1%% / 0.4%%: %s / %s / %s C with mean coincident wet-bulb %s / %s / %s C (within +/-1 K); heating 99%% / 99.6%%: %s / %s C",
               u"من بيانات ساعية %s (%s ساعة): التبريد 2%% / 1%% / 0.4%%: %s / %s / %s °م مع متوسط المبتل المتزامن %s / %s / %s °م (ضمن ±1 كلفن)؛ التدفئة 99%% / 99.6%%: %s / %s °م",
               u"%d-%d" % (hy[0], hy[-1]), u"%d" % hd["n"], fmt(hd["cool"][0], 1), fmt(hd["cool"][1], 1), fmt(hd["cool"][2], 1),
               fmt(hd["mcwb"][0], 1), fmt(hd["mcwb"][1], 1), fmt(hd["mcwb"][2], 1), fmt(hd["heat"][0], 1), fmt(hd["heat"][1], 1))
        R.text(u"Hourly values follow the ASHRAE-style annual percentile idea, but come from a short reanalysis sample: they are NOT official design conditions.",
               u"القيم الساعية تتبع فكرة المئينات السنوية بأسلوب ASHRAE، لكنها من عينة إعادة تحليل قصيرة: ليست ظروف تصميم رسمية.")
    else:
        R.text(u"Set hourly_years (e.g. 10) for hourly percentiles with coincident wet-bulb. Daily-extreme values above are NOT the hourly design conditions of ASHRAE/national codes.",
               u"ضع hourly_years (مثلًا 10) للحصول على مئينات ساعية مع المبتل المتزامن. قيم الأيام القصوى أعلاه ليست ظروف التصميم الساعية لـ ASHRAE أو الأكواد الوطنية.")
    rep_en, rep_ar = R.out(notes)
    return {"hdd": hdd, "cdd": cdd, "hdd_m": hdd_m, "cdd_m": cdd_m, "heat_design_daily": heat_d, "cool_design_daily": cool_d,
            "heat_design_hourly": hd["heat"] if hd else None, "cool_design_hourly": hd["cool"] if hd else None,
            "mcwb": hd["mcwb"] if hd else None, "wbt_m": wb_m, "wbd_m": wbd_m, "report_en": rep_en, "report_ar": rep_ar}


# ====================================================================================
# كهربائي
# ====================================================================================
def _run_lengths(flags):
    runs = []
    cur = 0
    for f in list(flags) + [False]:
        if f:
            cur += 1
        else:
            if cur > 0:
                runs.append(cur)
            cur = 0
    return runs


def elec_report(loc, y_from=None, y_to=None, noct=45.0, tcoef=0.35, update=False):
    notes = []
    D = disc_load(loc, y_from, y_to, update, notes)
    lat, lon = loc["lat"], loc["lon"]
    noct = float(noct) if noct is not None else 45.0
    tcoef = float(tcoef) if tcoef is not None else 0.35
    ghi_d = _ser(D, "sol", "ALLSKY_SFC_SW_DWN")
    dhi_d = _ser(D, "sol", "ALLSKY_SFC_SW_DIFF")
    clr_d = _ser(D, "sol", "CLRSKY_SFC_SW_DWN")
    tx = _ser(D, "met", "T2M_MAX")
    tn = _ser(D, "met", "T2M_MIN")
    ws = _ser(D, "met", "WS10M")
    G = _month_means(D, ghi_d)
    F = _month_means(D, dhi_d)
    if None in G or None in F:
        raise ValueError(bi(u"Solar data are incomplete for some months in this period", u"بيانات الإشعاع ناقصة لبعض الأشهر في هذه الفترة"))
    psh = _mean_or_none(_valid(ghi_d))
    best_m = G.index(max(G))
    worst_m = G.index(min(G))
    gamma_eq = 0.0 if lat >= 0 else 180.0
    winter_idx = [9, 10, 11, 0, 1, 2] if lat >= 0 else [3, 4, 5, 6, 7, 8]
    summer_idx = [k for k in range(12) if k not in winter_idx]
    table = {}
    for beta in range(0, 91, 2):
        table[beta] = plane_irradiation_monthly(lat, G, F, float(beta), gamma_eq, 60)
    ann = lambda v: sum(v[k] * DPM[k] for k in range(12))
    part = lambda v, idx: sum(v[k] * DPM[k] for k in idx)
    best_tilt = max(table, key=lambda b: ann(table[b]))
    tilt_w = max(table, key=lambda b: part(table[b], winter_idx))
    tilt_s = max(table, key=lambda b: part(table[b], summer_idx))
    y_best = ann(table[best_tilt])
    y_hor = ann(table[0])
    lat_t = int(round(abs(lat)))
    y_lat = ann(plane_irradiation_monthly(lat, G, F, float(lat_t), gamma_eq, 60))
    gain_h = 100.0 * (y_best / y_hor - 1.0)
    gain_l = 100.0 * (y_best / y_lat - 1.0)
    txs = sorted(_valid(tx))
    t99 = _quantile(txs, 0.99) if txs else None
    tcell_hot = (t99 + (noct - 20.0) / 800.0 * 1000.0) if t99 is not None else None
    derate_hot = (tcoef * (tcell_hot - 25.0)) if tcell_hot is not None else None
    txm = _month_means(D, tx)
    fac_m = [(1.0 - tcoef / 100.0 * (txm[k] + (noct - 20.0) - 25.0)) if txm[k] is not None else None for k in range(12)]
    tn_rec = _extreme(D, tn, False)
    tns = sorted(_valid(tn))
    tn1 = _quantile(tns, 0.01) if tns else None
    kt = [(g / c) if (g is not None and c not in (None, 0)) else None for g, c in zip(ghi_d, clr_d)]
    runs_c = sorted(_run_lengths([k is not None and k < 0.4 for k in kt]))
    runs_n = sorted(_run_lengths([k is not None and k < 0.7 for k in kt]))
    c_max = runs_c[-1] if runs_c else 0
    c_95 = _quantile(runs_c, 0.95) if runs_c else 0
    n_max = runs_n[-1] if runs_n else 0
    n_95 = _quantile(runs_n, 0.95) if runs_n else 0
    wmean = _mean_or_none(_valid(ws))
    w30 = wmean * (30.0 / 10.0) ** WIND_ALPHA if wmean is not None else None
    w50 = wmean * (50.0 / 10.0) ** WIND_ALPHA if wmean is not None else None
    R = _Rep()
    R.title(u"Location: %s | Latitude %.4f | Longitude %.4f" % (loc["label_en"], lat, lon),
            u"الموقع: %s | خط العرض %s | خط الطول %s" % (loc["name_ar"], ltr(u"%.4f" % lat), ltr(u"%.4f" % lon)))
    R.line(u"Climate period for the statistics: %s (%s years)", u"فترة الإحصاءات المناخية: %s (%s سنة)", u"%d-%d" % (D["y0"], D["y1"]), D["n_years"])
    R.blank()
    R.title(u"== Solar resource ==", u"== المورد الشمسي ==")
    R.text(
        u"Average daily peak sun hours (PSH = GHI in kWh/m2/day): %s h/day | best month: %s (%s) | weakest month: %s (%s)" % (
            fmt(psh, 2), MONTHS_EN[best_m], fmt(G[best_m], 2), MONTHS_EN[worst_m], fmt(G[worst_m], 2)),
        u"متوسط ساعات الذروة الشمسية اليومية (PSH = GHI بوحدة kWh/m2/يوم): %s ساعة/يوم | أفضل شهر: %s (%s) | أضعف شهر: %s (%s)" % (
            ltr(fmt(psh, 2)), MONTHS_AR[best_m], ltr(fmt(G[best_m], 2)), MONTHS_AR[worst_m], ltr(fmt(G[worst_m], 2))))
    rows = [(MONTHS_EN[k], MONTHS_AR[k], [fmt(G[k], 2), fmt(F[k], 2), fmt(table[best_tilt][k], 2), fmt(fac_m[k], 3)]) for k in range(12)]
    R.table([u"Month", u"GHI", u"DHI", u"OnTilt", u"TempFactor"], [u"الشهر", u"GHI", u"DHI", u"على الميل الأمثل", u"معامل الحرارة"], rows, w0=12, w=14)
    R.blank()
    R.title(u"== Panel tilt (fixed, facing the equator) ==", u"== ميلان الألواح (ثابت، متجه نحو خط الاستواء) ==")
    R.text(u"Best fixed tilt for maximum annual yield: %d deg (annual irradiation %s kWh/m2) | winter-optimised (%s): %d deg | summer-optimised: %d deg" % (
        best_tilt, fmt(y_best, 0), u"Oct-Mar" if lat >= 0 else u"Apr-Sep", tilt_w, tilt_s),
        u"أفضل ميلان ثابت لأعلى إنتاج سنوي: %s درجة (إشعاع سنوي %s kWh/m2) | الأمثل شتاءً (%s): %s درجة | الأمثل صيفًا: %s درجة" % (
            ltr(u"%d" % best_tilt), ltr(fmt(y_best, 0)), u"تشرين الأول-آذار" if lat >= 0 else u"نيسان-أيلول", ltr(u"%d" % tilt_w), ltr(u"%d" % tilt_s)))
    R.text(u"Gain vs a horizontal plane: %+.1f%% | vs the latitude-rule tilt (%d deg): %+.1f%%" % (gain_h, lat_t, gain_l),
           u"الزيادة مقارنة بسطح أفقي: %s | مقارنة بميلان قاعدة خط العرض (%s درجة): %s" % (ltr(u"%+.1f%%" % gain_h), ltr(u"%d" % lat_t), ltr(u"%+.1f%%" % gain_l)))
    R.text(u"Method: monthly mean GHI and DHI on a tilted plane (Liu-Jordan isotropic sky, ground albedo %.1f, Klein mean days, 2-degree search step). The isotropic model tends to under-estimate tilted irradiation compared with anisotropic models: use PVGIS/PVsyst for bankable yield." % ALBEDO,
           u"الطريقة: متوسط GHI وDHI الشهري على سطح مائل (سماء متجانسة Liu-Jordan، انعكاس أرض %s، أيام Klein، خطوة بحث درجتان). النموذج المتجانس يميل لتقدير إشعاع السطح المائل بأقل من النماذج غير المتجانسة: استخدم PVGIS/PVsyst للإنتاج المعتمد." % ltr(u"%.1f" % ALBEDO))
    R.blank()
    R.title(u"== Temperature effects on PV ==", u"== أثر الحرارة على الألواح ==")
    R.text(u"Hot case: 99th percentile of daily maximum %s C -> cell ~%s C at 1000 W/m2 (NOCT %.0f C) -> power loss ~%s%% (coefficient %.2f %%/K above 25 C)" % (
        fmt(t99, 1), fmt(tcell_hot, 0), noct, fmt(derate_hot, 1), tcoef),
        u"الحالة الحارة: المئين 99 للعظمى اليومية %s °م ← حرارة الخلية ~%s °م عند 1000 وات/م2 (NOCT %s °م) ← فقد القدرة ~%s%% (المعامل %s %%/كلفن فوق 25 °م)" % (
            ltr(fmt(t99, 1)), ltr(fmt(tcell_hot, 0)), ltr(u"%.0f" % noct), ltr(fmt(derate_hot, 1)), ltr(u"%.2f" % tcoef)))
    R.text(u"TempFactor (table): midday efficiency factor per month using the mean daily maximum, cell = ambient + (NOCT-20) at 800 W/m2. Coldest recorded daily minimum: %s C (1st percentile %s C): use it for the maximum open-circuit voltage (Voc) when selecting the inverter." % (
        fmt(tn_rec[0] if tn_rec else None, 1), fmt(tn1, 1)),
        u"معامل الحرارة (بالجدول): معامل كفاءة الظهيرة لكل شهر بمتوسط العظمى اليومية، الخلية = المحيط + (NOCT-20) عند 800 وات/م2. أبرد صغرى يومية مسجّلة: %s °م (المئين 1: %s °م): استخدمها لأقصى جهد دائرة مفتوحة (Voc) عند اختيار الإنفيرتر." % (
            ltr(fmt(tn_rec[0] if tn_rec else None, 1)), ltr(fmt(tn1, 1))))
    R.blank()
    R.title(u"== Battery autonomy (runs of low-irradiance days) ==", u"== استقلالية البطاريات (سلاسل أيام ضعيفة الإشعاع) ==")
    R.text(u"Consecutive cloudy days (Kt < 0.4): longest %d, 95th percentile of run lengths %s | consecutive non-sunny days (Kt < 0.7): longest %d, 95th percentile %s. Kt = daily GHI / clear-sky GHI (thresholds are conventions)." % (
        c_max, fmt(c_95, 0), n_max, fmt(n_95, 0)),
        u"أيام غائمة متتالية (Kt < 0.4): الأطول %s، والمئين 95 لأطوال السلاسل %s | أيام غير مشمسة متتالية (Kt < 0.7): الأطول %s، والمئين 95 %s. Kt = GHI اليومي / GHI بسماء صافية (العتبات اصطلاحية)." % (
            ltr(u"%d" % c_max), ltr(fmt(c_95, 0)), ltr(u"%d" % n_max), ltr(fmt(n_95, 0))))
    R.blank()
    R.title(u"== Small wind (estimate) ==", u"== رياح صغيرة (تقدير) ==")
    R.text(u"Mean wind speed: %s m/s at 10 m | ~%s m/s at 30 m | ~%s m/s at 50 m (power law, exponent %.2f: an approximation, not a measurement at that height)." % (
        fmt(wmean, 2), fmt(w30, 2), fmt(w50, 2), WIND_ALPHA),
        u"متوسط سرعة الرياح: %s م/ث على 10 م | ~%s م/ث على 30 م | ~%s م/ث على 50 م (قانون القدرة بأُس %s: تقريب وليس قياسًا بذلك الارتفاع)." % (
            ltr(fmt(wmean, 2)), ltr(fmt(w30, 2)), ltr(fmt(w50, 2)), ltr(u"%.2f" % WIND_ALPHA)))
    R.text(u"Hourly export for PVsyst/HOMER: use the EPW tools.", u"تصدير ساعي لـ PVsyst/HOMER: استخدم أدوات EPW.")
    rep_en, rep_ar = R.out(notes)
    return {"psh": psh, "psh_m": G, "best_tilt": best_tilt, "tilt_winter": tilt_w, "tilt_summer": tilt_s, "yield_opt": y_best,
            "gain_vs_horizontal": gain_h, "derate_hot": derate_hot, "temp_factor_m": fac_m, "voc_tmin": tn_rec[0] if tn_rec else None,
            "autonomy_days": c_95, "wind50": w50, "report_en": rep_en, "report_ar": rep_ar}


# ====================================================================================
# زراعي / حدائق
# ====================================================================================
def _doy_label(doy):
    d = datetime.date(2001, 1, 1) + datetime.timedelta(days=int(round(doy)) - 1)
    return d.strftime("%d %b"), u"%d %s" % (d.day, MONTHS_AR[d.month - 1])


def agri_report(loc, y_from=None, y_to=None, kc=1.0, base_gdd=10.0, update=False):
    notes = []
    D = disc_load(loc, y_from, y_to, update, notes)
    lat, lon = loc["lat"], loc["lon"]
    kc = float(kc) if kc is not None else 1.0
    base = float(base_gdd) if base_gdd is not None else 10.0
    tx = _ser(D, "met", "T2M_MAX")
    tn = _ser(D, "met", "T2M_MIN")
    pr = _ser(D, "met", "PRECTOTCORR")
    ra_cache = {}
    et0 = []
    for dte, a, b in zip(D["dates"], tx, tn):
        if a is None or b is None:
            et0.append(None)
            continue
        doy = dte.timetuple().tm_yday
        if doy not in ra_cache:
            ra_cache[doy] = extraterrestrial_mm(lat, doy)
        et0.append(0.0023 * ((a + b) / 2.0 + 17.8) * math.sqrt(max(a - b, 0.0)) * ra_cache[doy])
    et0_m = _month_means(D, et0)
    et0_tot = [(et0_m[k] * DPM[k]) if et0_m[k] is not None else None for k in range(12)]
    et0_year = sum(v for v in et0_tot if v is not None)
    p_m = _month_totals(D, pr)
    p_year = sum(v for v in p_m if v is not None)
    etc = [(kc * et0_tot[k]) if et0_tot[k] is not None else None for k in range(12)]
    deficit = [(max(etc[k] - (p_m[k] or 0.0), 0.0)) if etc[k] is not None else None for k in range(12)]
    ai = (p_year / et0_year) if et0_year > 0 else None
    gdd_d = [(max((a + b) / 2.0 - base, 0.0)) if (a is not None and b is not None) else None for a, b in zip(tx, tn)]
    gdd_m = _month_totals(D, gdd_d)
    gdd_year = sum(v for v in gdd_m if v is not None)
    hot = [(1 if (a is not None and a > 35.0) else 0) for a in tx]
    hot_days = _mean_or_none(_per_year(D, hot, lambda items: sum(v for _d, v in items)))
    frost_days = _mean_or_none(_per_year(D, tn, lambda items: len([1 for _d, v in items if v is not None and v < 0.0])))
    last_spring = []
    first_autumn = []
    no_frost_years = 0
    n_years = 0
    by = {}
    for dte, v in zip(D["dates"], tn):
        by.setdefault(dte.year, []).append((dte, v))
    if lat >= 0:
        for y in sorted(by):
            items = by[y]
            n_years += 1
            sp = [d.timetuple().tm_yday for d, v in items if v is not None and v < 0.0 and d.month <= 7]
            au = [d.timetuple().tm_yday for d, v in items if v is not None and v < 0.0 and d.month >= 8]
            if not sp and not au:
                no_frost_years += 1
            if sp:
                last_spring.append(max(sp))
            if au:
                first_autumn.append(min(au))
    ls = _mean_or_none(last_spring)
    fa = _mean_or_none(first_autumn)
    R = _Rep()
    R.title(u"Location: %s | Latitude %.4f | Longitude %.4f" % (loc["label_en"], lat, lon),
            u"الموقع: %s | خط العرض %s | خط الطول %s" % (loc["name_ar"], ltr(u"%.4f" % lat), ltr(u"%.4f" % lon)))
    R.line(u"Climate period for the statistics: %s (%s years)", u"فترة الإحصاءات المناخية: %s (%s سنة)", u"%d-%d" % (D["y0"], D["y1"]), D["n_years"])
    R.blank()
    R.title(u"== Water: reference evapotranspiration and a rough balance ==", u"== المياه: التبخر-نتح المرجعي وميزان تقريبي ==")
    rows = [(MONTHS_EN[k], MONTHS_AR[k], [fmt(et0_m[k], 2), fmt(et0_tot[k], 0), fmt(p_m[k], 0), fmt(etc[k], 0), fmt(deficit[k], 0), fmt(gdd_m[k], 0)]) for k in range(12)]
    R.table([u"Month", u"ET0 mm/d", u"ET0 mm", u"Rain mm", u"ETc mm", u"Deficit mm", u"GDD"], [u"الشهر", u"ET0 ملم/يوم", u"ET0 ملم", u"الهطول ملم", u"ETc ملم", u"العجز ملم", u"GDD"], rows, w0=12, w=11)
    R.text(u"Annual ET0 %s mm | annual rainfall %s mm | aridity index P/ET0 = %s | crop coefficient Kc = %.2f (ETc = Kc x ET0)" % (fmt(et0_year, 0), fmt(p_year, 0), fmt(ai, 2), kc),
           u"ET0 السنوي %s ملم | الهطول السنوي %s ملم | مؤشر الجفاف P/ET0 = %s | معامل المحصول Kc = %s (ETc = Kc × ET0)" % (ltr(fmt(et0_year, 0)), ltr(fmt(p_year, 0)), ltr(fmt(ai, 2)), ltr(u"%.2f" % kc)))
    R.text(u"Method: daily Hargreaves-Samani ET0 = 0.0023 (Tmean + 17.8) sqrt(Tmax - Tmin) Ra (FAO-56 extraterrestrial radiation), averaged by month. Deficit = max(Kc x ET0 - rainfall, 0) per month is a ROUGH indicator: it ignores effective rainfall, soil storage, leaching and irrigation efficiency. Reanalysis temperatures and rainfall are cell averages.",
           u"الطريقة: ET0 يومي بمعادلة Hargreaves-Samani = 0.0023 (Tmean + 17.8) جذر(Tmax - Tmin) Ra (إشعاع خارج الغلاف FAO-56)، ثم متوسط شهري. العجز = max(Kc × ET0 - الهطول، 0) لكل شهر مؤشر تقريبي: يتجاهل الهطول الفعّال وتخزين التربة والغسيل وكفاءة الري. درجات الحرارة والهطول متوسطات خلية.")
    R.blank()
    R.title(u"== Frost and heat ==", u"== الصقيع والحرارة ==")
    if lat < 0:
        R.text(u"Frost-date statistics are only implemented for the northern hemisphere.", u"إحصاءات تواريخ الصقيع منفّذة لنصف الكرة الشمالي فقط.")
    elif ls is None and fa is None:
        R.text(u"No frost (daily minimum below 0 C) occurred in the period.", u"لم يحدث صقيع (صغرى يومية دون 0 °م) خلال الفترة.")
    else:
        lse, lsa = _doy_label(ls) if ls is not None else (u"-", u"-")
        fae, faa = _doy_label(fa) if fa is not None else (u"-", u"-")
        R.text(u"Mean last spring frost: %s | mean first autumn frost: %s | years with no frost at all: %d of %d | frost days per year: %s" % (lse, fae, no_frost_years, n_years, fmt(frost_days, 1)),
               u"متوسط آخر صقيع ربيعي: %s | متوسط أول صقيع خريفي: %s | سنوات بلا صقيع إطلاقًا: %s من %s | أيام الصقيع سنويًا: %s" % (
                   lsa, faa, ltr(u"%d" % no_frost_years), ltr(u"%d" % n_years), ltr(fmt(frost_days, 1))))
    R.text(u"Frost uses the cell's daily minimum: local radiative frost in valleys and low spots can be colder. Growing degree-days GDD = sum of max((Tmax+Tmin)/2 - %.1f, 0): annual %s degree-days. Days above 35 C per year: %s." % (base, fmt(gdd_year, 0), fmt(hot_days, 1)),
           u"الصقيع من الصغرى اليومية للخلية: صقيع الإشعاع المحلي في الوديان والمنخفضات قد يكون أبرد. درجات النمو GDD = مجموع max((Tmax+Tmin)/2 - %s، 0): السنوي %s درجة-يوم. أيام فوق 35 °م سنويًا: %s." % (
               ltr(u"%.1f" % base), ltr(fmt(gdd_year, 0)), ltr(fmt(hot_days, 1))))
    rep_en, rep_ar = R.out(notes)
    return {"et0_m": et0_m, "et0_year": et0_year, "rain_year": p_year, "deficit_m": deficit, "aridity": ai,
            "frost_last": ls, "frost_first": fa, "frost_days": frost_days, "gdd_year": gdd_year, "hot_days": hot_days,
            "report_en": rep_en, "report_ar": rep_ar}
