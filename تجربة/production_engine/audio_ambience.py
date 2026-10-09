# -*- coding: utf-8 -*-
"""
==============================================================================
  نظام الصوت المحيطي والمؤثرات — «رحلة الجد صوفان»
  Ambience & SFX System · Phase 5
==============================================================================

⚠ سياسة المسلسل الثابتة: **لا موسيقى على الإطلاق**
   لا موسيقى تصويرية · لا لحن مقدمة · لا لحن خاتمة · لا إيقاع
   المسموح فقط: حوار + مؤثرات صوتية (SFX) + أصوات محيطية (Ambience)

هذا النظام يبني "طبقة الصوت المحيطي" إجرائياً (Procedural)،
بحيث تتغيّر مع حالة المشهد بدل أن تكون شريطاً ثابتاً مكرّراً:

  1) wind          — ريح خفيفة متغيّرة (ضجيج مُرشَّح بتغيير بطيء)
  2) engine_hum    — هَمهمة المحرك النظيفة (نغمة أساسية + توافقيات)
  3) turbine_whine — أزيز مروحة الرياح النحاسية (يرتفع مع السرعة)
  4) wheel_rumble  — دمدمة العجلات المطاطية على الطريق
  5) steam_hiss    — فحيح البخار النظيف عند النفث

كل طبقة تُنتج كملف مستقل (Stem) ثم تُمزج — وهو نفس أسلوب الاستوديو،
ويسمح بتعديل مستوى أي طبقة دون لمس البقية.
==============================================================================
"""
import numpy as np
import scipy.io.wavfile as wf
import scipy.signal as sig

SR = 44100


# ---------------------------------------------------------------------------
# أدوات أساسية
# ---------------------------------------------------------------------------
def noise(n, seed=0):
    return np.random.default_rng(seed).normal(0, 1, n).astype(np.float32)


def lp(x, cutoff, sr=SR, order=4):
    b, a = sig.butter(order, cutoff / (sr / 2), btype="low")
    return sig.filtfilt(b, a, x).astype(np.float32)


def hp(x, cutoff, sr=SR, order=4):
    b, a = sig.butter(order, cutoff / (sr / 2), btype="high")
    return sig.filtfilt(b, a, x).astype(np.float32)


def bp(x, lo, hi, sr=SR, order=4):
    b, a = sig.butter(order, [lo / (sr / 2), hi / (sr / 2)], btype="band")
    return sig.filtfilt(b, a, x).astype(np.float32)


def norm(x, peak=0.9):
    m = np.max(np.abs(x))
    return (x / m * peak).astype(np.float32) if m > 0 else x.astype(np.float32)


def env_smooth(n, values, sr=SR):
    """يُحوّل قائمة قيم (مستويات عبر الزمن) إلى مغلّف ناعم بنفس الطول"""
    t = np.linspace(0, 1, len(values))
    x = np.arange(n) / n
    return np.interp(x, t, np.array(values, dtype=np.float32)).astype(np.float32)


# ---------------------------------------------------------------------------
# 1) الريح — ضجيج منخفض التردد بمغلّف بطيء
# ---------------------------------------------------------------------------
def wind(dur, sr=SR, seed=11):
    n = int(dur * sr)
    base = lp(noise(n, seed), 420, sr)
    # تذبذب بطيء في الشدة (0.35 → 1.0 → 0.55)
    vals = [0.35, 0.8, 0.45, 1.0, 0.5, 0.75, 0.4]
    return base * env_smooth(n, vals, sr) * 0.55


# ---------------------------------------------------------------------------
# 2) هَمهمة المحرك النظيف — نغمة أساسية + توافقيات (بلا إيقاع)
# ---------------------------------------------------------------------------
def engine_hum(dur, sr=SR, base_hz=58, speed_curve=None):
    n = int(dur * sr)
    t = np.arange(n) / sr
    if speed_curve is None:
        speed_curve = [1.0] * 8
    f = base_hz * env_smooth(n, speed_curve, sr)
    phase = 2 * np.pi * np.cumsum(f) / sr
    out = (1.00 * np.sin(phase)
           + 0.42 * np.sin(2 * phase)
           + 0.18 * np.sin(3 * phase)
           + 0.08 * np.sin(4 * phase))
    out = lp(out, 900, sr)
    # اهتزاز خفيف جداً في الشدة (حيوية بلا إيقاع)
    out *= (1.0 + 0.06 * np.sin(2 * np.pi * 3.3 * t))
    return out * 0.30


# ---------------------------------------------------------------------------
# 3) أزيز مروحة الرياح النحاسية
# ---------------------------------------------------------------------------
def turbine_whine(dur, sr=SR, speed_curve=None):
    n = int(dur * sr)
    t = np.arange(n) / sr
    if speed_curve is None:
        speed_curve = [1.0] * 8
    f = 620 * env_smooth(n, speed_curve, sr)
    phase = 2 * np.pi * np.cumsum(f) / sr
    tone = np.sin(phase) + 0.25 * np.sin(2.01 * phase)
    # تعديل حلقي (AM) يحاكي دوران الريش
    am = 1.0 + 0.22 * np.sin(2 * np.pi * 11.0 * env_smooth(n, speed_curve, sr) * t)
    return bp(tone * am, 400, 2600, sr) * 0.10


# ---------------------------------------------------------------------------
# 4) دمدمة العجلات المطاطية على الطريق
# ---------------------------------------------------------------------------
def wheel_rumble(dur, sr=SR, speed_curve=None, seed=5):
    n = int(dur * sr)
    if speed_curve is None:
        speed_curve = [1.0] * 8
    src = noise(n, seed)
    # القالب الترددي ثابت، لكن الشدة تتغيّر مع السرعة
    body = bp(src, 70, 320, sr)
    grit = bp(noise(n, seed + 1), 900, 3200, sr) * 0.25
    return (body + grit) * env_smooth(n, speed_curve, sr) * 0.34


# ---------------------------------------------------------------------------
# 5) فحيح البخار النظيف
# ---------------------------------------------------------------------------
def steam_hiss(dur, sr=SR, puffs_per_sec=1.4, seed=9):
    n = int(dur * sr)
    src = hp(noise(n, seed), 1800, sr, order=2)
    src = lp(src, 9000, sr)
    t = np.arange(n) / sr
    # نفثات دورية قصيرة
    gate = 0.5 * (1 + np.sign(np.sin(2 * np.pi * puffs_per_sec * t)))
    gate = sig.convolve(gate, np.exp(-np.arange(0, int(sr*0.12)) / (sr*0.035)),
                        mode="same")
    gate = gate / (np.max(np.abs(gate)) + 1e-9)
    gate = np.clip(gate, 0.0, 1.0)          # يمنع القيم السالبة المجهرية من إنتاج NaN
    gate = gate ** 1.6
    return src * gate * 0.13


# ---------------------------------------------------------------------------
# المزج النهائي
# ---------------------------------------------------------------------------
def build_ambience(dur, speed_curve=None, out_dir=None):
    """
    يبني طبقة الصوت المحيطي الكاملة ويرجع (mix, stems)
    stems = dict بكل طبقة على حدة
    """
    stems = {
        "wind":          wind(dur, SR),
        "engine_hum":    engine_hum(dur, SR, speed_curve=speed_curve),
        "turbine_whine": turbine_whine(dur, SR, speed_curve=speed_curve),
        "wheel_rumble":  wheel_rumble(dur, SR, speed_curve=speed_curve),
        "steam_hiss":    steam_hiss(dur, SR),
    }
    mix = np.zeros(int(dur * SR), dtype=np.float32)
    for v in stems.values():
        mix += v
    mix = norm(mix, 0.55)

    if out_dir:
        import os
        os.makedirs(out_dir, exist_ok=True)
        for k, v in stems.items():
            wf.write(f"{out_dir}/stem_{k}.wav", SR, (norm(v, 0.8) * 32767).astype(np.int16))
        wf.write(f"{out_dir}/AMBIENCE_MIX.wav", SR, (mix * 32767).astype(np.int16))
    return mix, stems


def mix_dialogue(dialogue_wav, ambience, dialogue_gain=1.0, ambience_gain=0.42,
                 ducking=0.55, out_path=None):
    """
    يمزج الحوار مع المحيطي مع "تفادي التغطية" (Ducking):
    مستوى المحيطي ينخفض تلقائياً أثناء الكلام.
    """
    d, sr_d = (None, None)
    import scipy.io.wavfile as _wf
    sr_d, d = _wf.read(dialogue_wav)
    if d.ndim > 1:
        d = d.mean(axis=1)
    d = d.astype(np.float32) / 32768.0
    if sr_d != SR:
        n = int(len(d) * SR / sr_d)
        d = np.interp(np.linspace(0, len(d) - 1, n), np.arange(len(d)), d).astype(np.float32)

    n = max(len(d), len(ambience))
    d = np.pad(d, (0, n - len(d)))
    a = np.pad(ambience, (0, n - len(ambience)))

    # مغلّف طاقة الحوار (ناعم) → يخفض المحيطي أثناء الكلام
    win = int(SR * 0.05)
    env = np.sqrt(np.convolve(d ** 2, np.ones(win) / win, mode="same"))
    env = env / (np.max(env) + 1e-9)
    duck = 1.0 - ducking * np.clip(env * 3.0, 0, 1)
    duck = np.convolve(duck, np.exp(-np.arange(0, int(SR*0.08)) / (SR*0.03)), mode="same")
    duck = duck / (np.max(np.abs(duck)) + 1e-9)

    out = d * dialogue_gain + a * ambience_gain * duck
    out = norm(out, 0.92)
    if out_path:
        wf.write(out_path, SR, (out * 32767).astype(np.int16))
    return out
