# -*- coding: utf-8 -*-
"""تحقّق رقمي من أن الحركة حدثت فعلاً في مناطق محدّدة (بدون رؤية بصرية)"""
import sys, json
import numpy as np
from PIL import Image
R="/home/user/Animation-cartoon/تجربة/production_engine/_renders/SHOT01_talking_drive_frames"
N=74
def arr(i): return np.asarray(Image.open(f"{R}/f{i:04d}.png").convert("RGB")).astype(np.int16)

print("="*74)
print("تقرير التحقّق الرقمي من اللقطة 1")
print("="*74)

# مناطق الاهتمام (x0,y0,x1,y1)
REGIONS = {
  "نافذة 1 (فم الجد)":   (378, 372, 474, 458),
  "نافذة 2 (سلمى)":      (496, 372, 591, 458),
  "نافذة 3 (فارس)":      (613, 372, 698, 458),
  "العجلة الأمامية":     (555, 520, 700, 660),
  "مروحة الرياح":        (690, 250, 830, 390),
  "منطقة البخار":        (790,  40, 1000, 240),
  "سمسم على الطريق":     (780, 560, 1000, 720),
  "السماء (يجب أن تثبت)":(0,    40,  300,  200),
}
prev = arr(0)
d = np.abs(arr(1)-arr(0)).mean(axis=2)
for name,(x0,y0,x1,y1) in REGIONS.items():
    vals=[]
    for i in range(1,N):
        a0=np.asarray(Image.open(f"{R}/f{i-1:04d}.png").convert("RGB")).astype(np.int16)[y0:y1,x0:x1]
        a1=np.asarray(Image.open(f"{R}/f{i:04d}.png").convert("RGB")).astype(np.int16)[y0:y1,x0:x1]
        vals.append(np.abs(a1-a0).mean())
    vals=np.array(vals)
    print(f"{name:24s} متوسط التغيّر/إطار = {vals.mean():6.2f}   أقصاه = {vals.max():6.2f}   "
          f"{'✔ يتحرك' if vals.mean()>0.4 else '✘ ثابت'}")

# --- فحص تبديل الفم: هل اختلف بكسل منطقة الفم بين إطارات بحركات مختلفة؟ ---
tl=json.load(open("/home/user/Animation-cartoon/تجربة/production_engine/tests/lipsync_result_timeline.json",encoding="utf-8"))
mouth=tl["soufan.mouth"]
seq=sorted(int(k) for k in mouth)
changes=[(seq[i],mouth[str(seq[i])],mouth[str(seq[i-1])]) for i in range(1,len(seq)) if mouth[str(seq[i])]!=mouth[str(seq[i-1])]]
print("-"*74)
print("لحظات تغيّر حركة الفم (من تحليل الصوت):")
for f,a,b in changes:
    print(f"   إطار {f:3d} ({f/25:.2f}s):  {b}  →  {a}")
print(f"   عدد التبديلات: {len(changes)}")

# اختلاف بكسلي بين إطارين بحركتي فم مختلفتين
def mouthpix(f):
    a=np.asarray(Image.open(f"{R}/f{f:04d}.png").convert("RGB")).astype(np.int16)
    return a[405:445, 395:455]     # منطقة فم الجد داخل النافذة 1
if len(changes)>=2:
    f1,f2 = changes[0][0]-1, changes[0][0]+1
    if f2 < N:
        diff = np.abs(mouthpix(f1)-mouthpix(f2)).mean()
        print(f"\nفرق البكسل في منطقة الفم بين الإطار {f1} و {f2}: {diff:.2f}  "
              f"{'✔ الفم تغيّر فعلاً' if diff>1.0 else '✘ لا فرق'}")
print("="*74)
