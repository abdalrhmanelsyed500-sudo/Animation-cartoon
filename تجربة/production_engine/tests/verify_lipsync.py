# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, "/home/user/Animation-cartoon/تجربة/production_engine")
import numpy as np
from audio_lipsync import analyze

WAV = "/home/user/Animation-cartoon/تجربة/production_engine/tests/test_speech_synthetic.wav"
GT  = "/home/user/Animation-cartoon/تجربة/production_engine/tests/test_speech_ground_truth.json"

gt = json.load(open(GT, encoding="utf-8"))
res = analyze(WAV, fps=25)
fps = res["fps"]

def truth_at(t):
    for s in gt["segments"]:
        if s["start"] <= t < s["end"]:
            return s["vowel"]
    return "closed"

rows = []
for i in range(res["frames"]):
    t = i / fps
    exp = truth_at(t)
    got = res["mouth"].get(str(i), "closed")
    rows.append((i, round(t,2), exp, got, exp == got))

correct = sum(1 for r in rows if r[4])
acc = 100.0 * correct / len(rows)

print("="*78)
print("تقرير التحقّق من نظام مزامنة الشفاه  (Audio → Viseme)")
print("="*78)
print(f"ملف الاختبار : صوت مُخلَّق بالفورمنتات (حقيقة أرضية معلومة)")
print(f"المدة        : {gt['total_duration']} ثانية  |  {res['frames']} إطار @ {fps}fps")
print(f"عتبة الصمت   : RMS = {res['threshold_rms']:.4f}")
print("-"*78)
print("الإطار | الزمن | المتوقّع | المُكتشَف | صح؟")
print("-"*78)
for i,t,e,g,ok in rows:
    print(f"{i:5d} | {t:5.2f} |   {e:^6s} |  {g:^6s}   | {'✔' if ok else '✘'}")
print("-"*78)
print(f"الدقّة الإجمالية: {acc:.1f}%  ({correct}/{len(rows)} إطار)")

# دقة استبعاد مناطق الانتقال (أول وآخر إطارين من كل مقطع)
mask = []
segs = gt["segments"]
for i,t,e,g,ok in rows:
    transition = False
    for s in segs:
        if s["start"] <= t < s["end"]:
            if (t - s["start"]) < 0.06 or (s["end"] - t) < 0.06:
                transition = True
    if not transition: mask.append((e,g))
c2 = sum(1 for e,g in mask if e==g)
print(f"الدقّة باستبعاد لحظات الانتقال (±60ms): {100.0*c2/len(mask):.1f}%  ({c2}/{len(mask)})")

# دقة الحركات المتكلَّمة فقط (بدون الصمت)
sp = [(e,g) for e,g in mask if e != "closed"]
c3 = sum(1 for e,g in sp if e==g)
print(f"الدقّة على المقاطع المتكلَّمة فقط: {100.0*c3/len(sp):.1f}%  ({c3}/{len(sp)})")

# كشف الفورمنتات
f1 = [v for v in res["F1"] if v is not None]
f2 = [v for v in res["F2"] if v is not None]
print("-"*78)
print(f"الفورمنتات المُقدَّرة: F1 متوسط {np.mean(f1):.0f} Hz | F2 متوسط {np.mean(f2):.0f} Hz")
print(f"أحداث الرمش المولّدة: {sorted(int(k) for k in res['eyes'].keys())}")
print("="*78)

json.dump(res, open("/home/user/Animation-cartoon/تجربة/production_engine/tests/lipsync_result.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
