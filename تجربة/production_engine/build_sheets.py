# -*- coding: utf-8 -*-
"""لوحات إثبات بصرية للمرحلة 5"""
import sys, os, json, math
sys.path.insert(0,"/home/user/Animation-cartoon/تجربة/production_engine")
from PIL import Image, ImageDraw, ImageFont
from rig_engine import Rig
from motion_cycles import sample_cycle, CYCLE_SHEEP_WALK, CYCLE_PUPPY_TROT, CYCLE_IDLE_BREATH, CYCLE_TAIL_WAG
from render_shot import cycle_to_rot, render_character

R="/home/user/Animation-cartoon/تجربة/production_engine/_renders"
FB="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# =========================================================================
# 1) شريط حركات الفم — التسلسل الذي ولّده تحليل الصوت
# =========================================================================
tl=json.load(open("tests/lipsync_result_timeline.json",encoding="utf-8"))
mouth=tl["soufan.mouth"]
frames=sorted(int(k) for k in mouth)
rig=Rig("soufan")

# نأخذ إطاراً واحداً كل 40 مللي ثانية لتقليل العدد
step=1
seq=[(f, mouth[str(f)]) for f in frames][::step]

CELL=118
cols=25
rows=math.ceil(len(seq)/cols)
sheet=Image.new("RGB",(cols*CELL+40, rows*CELL+150),(250,248,243))
d=ImageDraw.Draw(sheet)
d.text((cols*CELL//2+20,32),"شريط مزامنة الشفاه — تسلسل حركات الفم المولَّد تلقائياً من تحليل ملف الصوت",
       font=ImageFont.truetype(FB,25),fill=(35,25,21),anchor="mm")
d.text((cols*CELL//2+20,68),"كل خلية = إطار واحد (40 مللي ثانية). الحروف: أ = فتحة | و = ضمة | ي = كسرة | مغلق = صمت",
       font=ImageFont.truetype(FR,18),fill=(90,70,60),anchor="mm")

COL={"A":(232,214,190),"O":(206,226,238),"E":(214,232,210),"closed":(240,236,228)}
LBL={"A":"أ","O":"و","E":"ي","closed":"—"}
for i,(f,mv) in enumerate(seq):
    r,c=divmod(i,cols)
    x0=20+c*CELL; y0=100+r*CELL
    d.rounded_rectangle([x0+2,y0+2,x0+CELL-4,y0+CELL-4],outline=(200,192,178),width=2,radius=8)
    pose={"pos":[350,470],"scale":0.72,"rot":{},"swaps":{"mouth":mv}}
    img=render_character(rig,pose)
    img.thumbnail((CELL-16,CELL-40),Image.LANCZOS)
    sheet.paste(img,(x0+(CELL-img.width)//2,y0+8),img)
    d.text((x0+CELL//2-2,y0+CELL-26),LBL.get(mv,mv),font=ImageFont.truetype(FB,20),fill=(60,45,38),anchor="mm")
    d.text((x0+CELL//2-2,y0+CELL-10),str(f),font=ImageFont.truetype(FR,11),fill=(140,125,112),anchor="mm")
sheet.save(f"{R}/SHEET_lipsync_strip.png")
print("✔ SHEET_lipsync_strip.png")

# =========================================================================
# 2) مقارنة المشية: الخروف (24 إطار) مقابل الجرو (16 إطار)
# =========================================================================
def pose_from_cycle(cyc, f, base, scale, extra_rot=None):
    s=sample_cycle(cyc,f)
    rot=cycle_to_rot(s)
    if extra_rot: rot.update(extra_rot)
    return {"pos":[base[0], base[1]+s.get("bob",0)], "scale":scale, "rot":rot, "swaps":{}}

sheet=Image.new("RGB",(1240,700),(250,248,243))
d=ImageDraw.Draw(sheet)
d.text((620,30),"التمييز الحركي: مشية الخروف مقابل خبب الجرو",
       font=ImageFont.truetype(FB,26),fill=(35,25,21),anchor="mm")
d.text((620,64),"الأعلى: سلمى (دورة 24 إطار — ثقيلة ومتزنة)   |   الأسفل: سمسم (دورة 16 إطار — أسرع بـ1.5× وأعلى نطّاً + ذيل وأذنان)",
       font=ImageFont.truetype(FR,17),fill=(90,70,60),anchor="mm")

rigS=Rig("salma"); rigP=Rig("simsim")
nShow=8
CW=140
# صف الخروف
for i in range(nShow):
    f=i*3   # 3 إطارات بين كل خلية
    x=60+i*CW
    img=render_character(rigS, pose_from_cycle(CYCLE_SHEEP_WALK,f,[350,500],0.95))
    img.thumbnail((CW-24,240),Image.LANCZOS)
    sheet.paste(img,(x+12, 300-img.height),img)
# صف الجرو
for i in range(nShow):
    f=i*2
    x=60+i*CW
    img=render_character(rigP, pose_from_cycle(CYCLE_PUPPY_TROT,f,[350,520],0.85))
    img.thumbnail((CW-24,240),Image.LANCZOS)
    sheet.paste(img,(x+12, 650-img.height),img)

d.line([40,305,1200,305],fill=(190,182,168),width=2)
d.line([40,655,1200,655],fill=(190,182,168),width=2)
d.text((30,180),"سلمى",font=ImageFont.truetype(FB,20),fill=(60,45,38))
d.text((30,530),"سمسم",font=ImageFont.truetype(FB,20),fill=(60,45,38))
d.text((620,682),"← إطار 0                                                    إطار 14/21 →",
       font=ImageFont.truetype(FR,15),fill=(130,115,100),anchor="mm")
sheet.save(f"{R}/SHEET_walk_vs_trot.png")
print("✔ SHEET_walk_vs_trot.png")

# =========================================================================
# 3) بطاقة مفاصل الشخصيات (مرجع للمحرِّك)
# =========================================================================
chars=["soufan","salma","fares","simsim"]
sheet=Image.new("RGB",(1200,560),(250,248,243))
d=ImageDraw.Draw(sheet)
d.text((600,32),"بطاقة مفاصل دمى التحريك — لكل شخصية (مرجع المحرِّك)",
       font=ImageFont.truetype(FB,26),fill=(35,25,21),anchor="mm")
names={"soufan":"الجد صوفان","salma":"سلمى","fares":"فارس","simsim":"سمسم (الجرو)"}
col_x=[150,450,750,1050]
for cid,cx in zip(chars,col_x):
    spec=Rig(cid).spec
    bones=[b for b in spec["bones"] if b["part"]]
    d.text((cx,80),names[cid],font=ImageFont.truetype(FB,22),fill=(35,25,21),anchor="mm")
    d.line([cx-80,96,cx+80,96],fill=(200,120,90),width=3)
    y=120
    d.text((cx,y),"المفصل / الطبقة",font=ImageFont.truetype(FB,15),fill=(90,70,60))
    d.text((cx+230,y),"Pivot",font=ImageFont.truetype(FB,15),fill=(90,70,60))
    y+=22
    for b in bones:
        d.text((cx-110,y),b["id"],font=ImageFont.truetype(FR,15),fill=(45,35,30))
        d.text((cx+230,y),str(b["pivot"]),font=ImageFont.truetype(FR,14),fill=(110,95,85))
        y+=22
    y+=10
    d.text((cx-110,y),"أشكال الفم:",font=ImageFont.truetype(FB,15),fill=(60,45,38)); y+=20
    d.text((cx-110,y),"closed / أ / و / ي / عبوس",font=ImageFont.truetype(FR,14),fill=(110,95,85)); y+=20
    d.text((cx-110,y),"العينان: open / blink",font=ImageFont.truetype(FR,14),fill=(110,95,85)); y+=20
    d.text((cx-110,y),f"المقياس الافتراضي: {spec['default_scale']}",font=ImageFont.truetype(FR,14),fill=(110,95,85))
sheet.save(f"{R}/SHEET_rig_reference_card.png")
print("✔ SHEET_rig_reference_card.png")
