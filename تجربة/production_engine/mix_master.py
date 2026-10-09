# -*- coding: utf-8 -*-
"""بناء الشريط الصوتي النهائي ودمجه مع الفيديو — بلا أي موسيقى"""
import sys, subprocess, json
sys.path.insert(0,"/home/user/Animation-cartoon/تجربة/production_engine")
import numpy as np
from audio_ambience import build_ambience, mix_dialogue, SR
import imageio_ffmpeg

R="/home/user/Animation-cartoon/تجربة/production_engine/_renders"
DIALOGUE="/home/user/Animation-cartoon/تجربة/production_engine/tests/test_speech_synthetic.wav"

# منحنى سرعة القاطرة عبر اللقطة (يحرّك هَمهمة المحرك وأزيز المروحة فعلياً)
speed=[0.80,0.88,0.96,1.04,1.08,1.04,0.96,0.88]
mix, stems = build_ambience(3.2, speed_curve=speed, out_dir=f"{R}/stems")

final = mix_dialogue(DIALOGUE, mix, dialogue_gain=1.0, ambience_gain=0.40,
                     ducking=0.55, out_path=f"{R}/SHOT01_AUDIO_MASTER.wav")
print(f"✔ الشريط الصوتي: {len(final)/SR:.2f}s  peak={np.max(np.abs(final)):.3f}  RMS={np.sqrt(np.mean(final**2)):.4f}")

exe = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([exe,"-y","-i",f"{R}/SHOT01_talking_drive.mp4",
                "-i",f"{R}/SHOT01_AUDIO_MASTER.wav",
                "-c:v","copy","-c:a","aac","-b:a","192k","-shortest",
                f"{R}/SHOT01_FINAL_with_audio.mp4"], check=True, capture_output=True)
print("✔ SHOT01_FINAL_with_audio.mp4")

# بطاقة طبقات الصوت
import os
rows = [("حوار (Dialogue)","ملف الممثل — يُستبدل بالصوت الحقيقي"),
        ("wind — ريح","طبقة محيطية"),
        ("engine_hum — هَمهمة المحرك","طبقة ميكانيكية"),
        ("turbine_whine — أزيز المروحة","طبقة ميكانيكية"),
        ("wheel_rumble — دمدمة العجلات","طبقة ميكانيكية"),
        ("steam_hiss — فحيح البخار","طبقة ميكانيكية"),
        ("❌ موسيقى","محظورة بسياسة المسلسل")]
with open(f"{R}/SHOT01_audio_stems_manifest.txt","w",encoding="utf-8") as f:
    f.write("بطاقة طبقات الصوت — اللقطة 1\n"+"="*46+"\n")
    for a,b in rows: f.write(f"  {a:34s} {b}\n")
    f.write("\nالملفات المستقلة (Stems) في مجلد stems/ :\n")
    for k in stems: f.write(f"  stem_{k}.wav\n")
print("✔ manifest")
