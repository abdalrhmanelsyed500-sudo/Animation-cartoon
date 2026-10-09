# -*- coding: utf-8 -*-
"""
==============================================================================
  مولّد صوت اختباري بتخليق الفورمنتات (Formant Synthesis)
==============================================================================
الغرض: نحتاج صوتاً نعرف "حقيقته" مسبقاً لكي نُثبت أن محلّل مزامنة الشفاه
يعمل فعلاً — بدل أن نختبره على صوت مجهول ونصدّق النتيجة.

هذا المولّد يبني إشارة كلام اصطناعية تحتوي حركات عربية معروفة:
    أ  (فتحة)  →  يجب أن يُكتشف كـ "A"
    و  (ضمة)   →  يجب أن يُكتشف كـ "O"
    ي  (كسرة)  →  يجب أن يُكتشف كـ "E"
    صمت        →  يجب أن يُكتشف كـ "closed"

الإشارة الناتجة اصطناعية تماماً (وليست تسجيلاً بشرياً)، وتُستعمل
للتحقّق من النظام فقط — الصوت الحقيقي سيأتي منك في مرحلة الإنتاج.
==============================================================================
"""
import json
import numpy as np
import scipy.io.wavfile as wf

SR = 16000

# جدول الفورمنتات للحركات العربية (F1, F2, F3)
VOWELS = {
    "A": (800, 1150, 2900),   # فتحة
    "O": (330,  700, 2530),   # ضمة
    "E": (290, 2250, 2890),   # كسرة
}


def resonator(x, f, bw, sr=SR):
    """مرشّح رنيني ذو قطبين (two-pole resonator)"""
    r = np.exp(-np.pi * bw / sr)
    theta = 2 * np.pi * f / sr
    a1 = 2 * r * np.cos(theta)
    a2 = -r * r
    g = (1 - r) * np.sqrt(1 - 2 * r * np.cos(2 * theta) + r * r)
    y = np.zeros_like(x)
    for n in range(2, len(x)):
        y[n] = g * x[n] + a1 * y[n-1] + a2 * y[n-2]
    # تطبيع تقريبي
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
    return y


def glottal_source(n, f0, sr=SR):
    """قطار نبضات الحبال الصوتية مع اهتزاز طبيعي (jitter)"""
    t = np.arange(n) / sr
    phase = 2 * np.pi * f0 * t + 0.25 * np.sin(2 * np.pi * 4.7 * t)
    sig = np.zeros(n)
    # نبضة عند كل عبور للصفر الموجي
    ph = np.floor(phase / (2 * np.pi))
    idx = np.where(np.diff(ph) > 0)[0]
    sig[idx] = 1.0
    # تنعيم النبضة
    k = np.exp(-np.arange(0, 60) / 12.0)
    sig = np.convolve(sig, k, mode="same")
    return sig


def synth_vowel(vowel, dur, f0=140, sr=SR):
    n = int(dur * sr)
    src = glottal_source(n, f0, sr)
    f1, f2, f3 = VOWELS[vowel]
    out = np.zeros(n)
    for f, amp, bw in [(f1, 1.0, 90), (f2, 0.55, 110), (f3, 0.22, 160)]:
        out += amp * resonator(src, f, bw, sr)
    out /= (np.max(np.abs(out)) + 1e-9)

    # مغلّف المقطع: صعود 15% / هبوط 25%
    env = np.ones(n)
    a = int(n * 0.15); b = int(n * 0.25)
    env[:a] = np.linspace(0, 1, a)
    env[-b:] = np.linspace(1, 0, b)
    return out * env


def build_sequence(plan, sr=SR):
    """
    plan = [("A", 0.35), (None, 0.20), ("O", 0.35), ...]
    None = صمت
    """
    chunks, truth = [], []
    for item in plan:
        vowel, dur = item
        if vowel is None:
            chunks.append(np.zeros(int(dur * sr)))
            truth.append(("closed", dur))
        else:
            chunks.append(synth_vowel(vowel, dur, f0=140, sr=sr))
            truth.append((vowel, dur))
    sig = np.concatenate(chunks)
    # ضجيج تنفّس خفيف جداً في الخلفية (واقعية)
    sig += np.random.default_rng(7).normal(0, 0.004, len(sig))
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * 0.92
    return sig, truth


if __name__ == "__main__":
    # خطة الاختبار: تُشبه إيقاع جملة عربية قصيرة
    plan = [
        ("A", 0.34), (None, 0.16),
        ("O", 0.36), (None, 0.18),
        ("E", 0.34), (None, 0.16),
        ("A", 0.30), ("O", 0.30),
        (None, 0.25),
        ("E", 0.40), (None, 0.20),
    ]
    sig, truth = build_sequence(plan)
    out = "/home/user/Animation-cartoon/تجربة/production_engine/tests/test_speech_synthetic.wav"
    wf.write(out, SR, (sig * 32767).astype(np.int16))

    # كتابة الحقيقة الأرضية للتحقّق
    gt, t = [], 0.0
    for v, d in truth:
        gt.append({"vowel": v, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    with open("/home/user/Animation-cartoon/تجربة/production_engine/tests/test_speech_ground_truth.json",
              "w", encoding="utf-8") as f:
        json.dump({"total_duration": round(t, 3), "segments": gt}, f, ensure_ascii=False, indent=2)
    import json as _j
    print(f"✔ WAV مكتوب: {out}  ({t:.2f} ثانية)")
    for g in gt:
        print(f"   {g['start']:.2f}s → {g['end']:.2f}s : {g['vowel']}")
