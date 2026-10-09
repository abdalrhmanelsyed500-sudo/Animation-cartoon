# -*- coding: utf-8 -*-
"""
==============================================================================
  نظام مزامنة الشفاه — «رحلة الجد صوفان»
  Audio → Viseme Lip-Sync System · Phase 5
==============================================================================

يحلّل ملف الصوت المسجّل (حوار الشخصية) ويُخرج جدول تبديل طبقات الفم
إطاراً بإطار، جاهزاً ليُغذّي محرك التحريك مباشرة.

الطريقة (تحليل حقيقي، ليس تخميناً):
  1) RMS لكل نافذة 40ms                  → هل الفم مفتوح أم مغلق؟
  2) تقدير الترددات الرنينة F1 و F2 عبر LPC → أي حرف مدّ؟
  3) خرائط الفورمنت العربية:
       /a/ فتحة : F1 ≈ 800 Hz , F2 ≈ 1200 Hz
       /u/ ضمة  : F1 ≈ 330 Hz , F2 ≈  750 Hz
       /i/ كسرة : F1 ≈ 290 Hz , F2 ≈ 2200 Hz
  4) كشف الرمش العشوائي الطبيعي كل 2.5–5 ثوانٍ

المخرج: timeline.json بصيغة محرك التحريك.
==============================================================================
"""
import json, math
import numpy as np

# ---------------------------------------------------------------------------
# 1) قراءة الصوت
# ---------------------------------------------------------------------------
def load_audio(path, target_sr=11025):
    """يرجع (samples float32 mono, sample_rate)"""
    import scipy.io.wavfile as wf
    sr, data = wf.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    data = data.astype(np.float32)
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))
    if sr != target_sr:
        n = int(len(data) * target_sr / sr)
        idx = np.linspace(0, len(data) - 1, n)
        data = np.interp(idx, np.arange(len(data)), data).astype(np.float32)
        sr = target_sr
    return data, sr


# ---------------------------------------------------------------------------
# 2) تحليل LPC لاستخراج الفورمنتات
# ---------------------------------------------------------------------------
def levinson_durbin(r, order):
    """حلّ معادلات Wiener-Hopf: يعطي معاملات LPC من دالة الارتباط الذاتي"""
    a = np.zeros(order + 1, dtype=np.float64)
    a[0] = 1.0
    e = r[0] if r[0] > 1e-12 else 1e-12
    for i in range(1, order + 1):
        acc = r[i] + np.dot(a[1:i], r[i-1:0:-1]) if i > 1 else r[i]
        k = -acc / e
        a_new = a.copy()
        for j in range(1, i):
            a_new[j] = a[j] + k * a[i - j]
        a_new[i] = k
        a = a_new
        e *= (1 - k * k)
        if e <= 1e-12:
            e = 1e-12
    return a


def lpc_formants(frame, sr, order=12):
    """يُقدّر F1 و F2 من إطار صوتي قصير"""
    n = len(frame)
    if n < order + 2:
        return None, None
    # نافذة هامينغ + إزالة الميل (Pre-emphasis)
    w = np.hamming(n)
    x = frame * w
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])

    # الارتباط الذاتي
    r = np.correlate(x, x, mode="full")[n-1:n+order]
    if r[0] < 1e-12:
        return None, None
    r = r / r[0]

    try:
        a = levinson_durbin(r, order)
    except Exception:
        return None, None

    # جذور كثير الحدود → ترددات وعرض نطاق
    try:
        roots = np.roots(a)
    except Exception:
        return None, None

    cand = []
    for rt in roots:
        if rt.imag <= 1e-9:
            continue
        f = abs(np.angle(rt)) * sr / (2.0 * math.pi)
        bw = -0.5 * sr / math.pi * math.log(max(abs(rt), 1e-9))
        if 90 < f < (sr / 2 - 200) and 0 < bw < 900:
            cand.append((f, bw))
    if not cand:
        return None, None
    cand.sort()
    # دمج الفورمنتات المتقاربة جداً
    merged = [cand[0]]
    for f, bw in cand[1:]:
        if f - merged[-1][0] < 120:
            continue
        merged.append((f, bw))
    if len(merged) >= 2:
        return merged[0][0], merged[1][0]
    return merged[0][0], None


# ---------------------------------------------------------------------------
# 3) تصنيف حركة الفم (Viseme)
# ---------------------------------------------------------------------------
# (F1, F2) مرجعية للحركات العربية — قيم تقريبية لصوت بالغ/مراهق
VOWEL_TARGETS = {
    "A": (800, 1200),    # فتحة / أ
    "O": (330,  750),    # ضمة / و  (مدّ بالواو)
    "E": (290, 2200),    # كسرة / ي  (مدّ بالياء)
}

# عتبات القرار (مُعايرة على فضاء القياس الفعلي للمحلّل بعد الخفض إلى 11025Hz
# وترتيب LPC = 12). تُعاد معايرتها مرة واحدة على صوت الممثل الحقيقي.
F1_OPEN_THRESHOLD = 520      # أعلى من هذا => فتحة واسعة (أ)
F2_HIGH_THRESHOLD = 1150     # مع F1 منخفض => كسرة/ياء


def classify_vowel(f1, f2):
    """شجرة قرار فيزيولوجية + أقرب جار مرجّح كخطة بديلة"""
    if f1 is None or f2 is None:
        return "A"
    # 1) القرار الفيزيولوجي الأساسي
    if f1 >= F1_OPEN_THRESHOLD:
        return "A"
    if f2 >= F2_HIGH_THRESHOLD:
        return "E"
    if f2 < F2_HIGH_THRESHOLD * 0.82:
        return "O"
    # 2) منطقة غامضة => أقرب جار مرجّح
    best, best_d = "A", float("inf")
    for name, (tf1, tf2) in VOWEL_TARGETS.items():
        d = ((f1 - tf1) / 300.0) ** 2 + ((f2 - tf2) / 800.0) ** 2
        if d < best_d:
            best, best_d = name, d
    return best


# ---------------------------------------------------------------------------
# 4) الاستخراج الرئيسي
# ---------------------------------------------------------------------------
def analyze(path, fps=25, silence_db=-38, smoothing=2):
    """
    يحلّل ملف الصوت ويرجع:
      {
        "fps": 25,
        "frames": N,
        "mouth": {frame: "closed"|"A"|"O"|"E"|"frown"},
        "eyes":  {frame: "blink"},
        "envelope": [rms per frame],
        "F1": [...], "F2": [...]
      }
    """
    data, sr = load_audio(path)          # sr = 11025 Hz (معيار ملائم لتحليل الفورمنتات)
    hop = int(sr / fps)
    win = int(hop * 1.6)
    LPC_ORDER = 12                        # ≈ sr/1000 + 2  (قاعدة قياسية)

    n_frames = int(len(data) / hop)
    envelope, f1s, f2s = [], [], []

    for i in range(n_frames):
        s0 = i * hop
        s1 = min(len(data), s0 + win)
        seg = data[s0:s1]
        if len(seg) < 32:
            envelope.append(0.0); f1s.append(None); f2s.append(None)
            continue
        rms = float(np.sqrt(np.mean(seg ** 2)))
        envelope.append(rms)
        if rms > 0.012:
            f1, f2 = lpc_formants(seg, sr, order=LPC_ORDER)
        else:
            f1, f2 = None, None
        f1s.append(f1); f2s.append(f2)

    env = np.array(envelope)
    peak = float(env.max()) if len(env) and env.max() > 0 else 1.0
    thr = max(peak * 0.06, 10 ** (silence_db / 20.0))
    thr = min(thr, peak * 0.30)

    mouth = {}
    last_vis = "closed"
    hangover = 0                          # استمرار قصير بعد هبوط الطاقة (يمنع إغلاق الفم بين المقاطع)
    HANGOVER_FRAMES = 2                   # ≈ 80 مللي ثانية عند 25fps

    for i in range(n_frames):
        loud = env[i] > thr
        if loud:
            hangover = HANGOVER_FRAMES
            f1, f2 = f1s[i], f2s[i]
            if f1 is None or f2 is None:
                # صوت موجود لكن بدون فورمنت واضح (حرف ساكن/انفجاري)
                last_vis = "E"            # فتحة صغيرة تناسب الحروف الساكنة
            else:
                last_vis = classify_vowel(f1, f2)
            mouth[i] = last_vis
        else:
            if hangover > 0:
                hangover -= 1
                mouth[i] = last_vis if last_vis != "closed" else "E"
            else:
                mouth[i] = "closed"
                last_vis = "closed"

    # تنعيم: إزالة التذبذب السريع (حرف لا يدوم أقل من smoothing إطار)
    mouth = _smooth(mouth, n_frames, min_len=smoothing)

    # رمش طبيعي: أول رمشة بعد 1.2–2.2 ثانية، ثم كل 2.5–5 ثوانٍ
    eyes = {}
    rng = np.random.default_rng(1337)
    t = rng.uniform(1.2, 2.2)
    while t < n_frames / fps:
        fr = int(t * fps)
        if fr < n_frames - 1:
            eyes[fr] = "blink"
            if fr + 2 < n_frames:
                eyes[fr + 2] = "open"
        t += rng.uniform(2.5, 5.0)

    return {
        "fps": fps,
        "frames": n_frames,
        "threshold_rms": float(thr),
        "mouth": {str(k): v for k, v in mouth.items()},
        "eyes": {str(k): v for k, v in eyes.items()},
        "envelope": [round(float(e), 5) for e in envelope],
        "F1": [None if v is None else round(float(v), 1) for v in f1s],
        "F2": [None if v is None else round(float(v), 1) for v in f2s],
    }


def _smooth(mouth, n, min_len=2):
    """يحذف النقرات القصيرة: أي حركة لا تستمر min_len إطار تُدمج مع جارتها"""
    if n == 0:
        return mouth
    out = {}
    keys = [mouth.get(i, "closed") for i in range(n)]
    i = 0
    while i < n:
        j = i
        while j + 1 < n and keys[j + 1] == keys[i]:
            j += 1
        seg = keys[i]
        if (j - i + 1) < min_len:
            if j == n - 1:
                seg = keys[i]                     # مقطع أخير: لا شيء بعده للدمج معه
            else:
                prev = keys[i - 1] if i > 0 else seg
                nxt = keys[j + 1] if j + 1 < n else prev
                seg = prev if prev == nxt else (prev if i > 0 else nxt)
        for k in range(i, j + 1):
            out[k] = seg
        i = j + 1
    return out


def to_timeline(result, prefix):
    """يحوّل نتيجة التحليل إلى صيغة timeline.json لمحرك التحريك"""
    return {
        "duration": result["frames"],
        "swaps": {
            f"{prefix}.mouth": result["mouth"],
            f"{prefix}.eyes":  result["eyes"],
        },
        "tracks": {}
    }
