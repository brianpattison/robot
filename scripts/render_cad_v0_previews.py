#!/usr/bin/env python3
"""Generate lightweight colored CAD preview renders for PR review.

These are design-review illustrations derived from the OpenSCAD parameters, not
manufacturing exports. They intentionally show color, assembly, service zones,
and print orientation. Requires Pillow while keeping the source CAD in cad/openscad/.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path('docs/images')
OUT.mkdir(parents=True, exist_ok=True)
W,H=1400,900
COL={
 'cream':(245,240,230),'teal':(19,200,195),'blue':(47,107,255),'charcoal':(36,40,50),
 'lime':(185,255,102),'orange':(255,159,28),'bumper':(43,47,58),'red':(220,40,38),
 'rubber':(20,20,22),'grey':(150,160,170),'bg':(248,250,252),'line':(30,35,42)
}
font=ImageFont.load_default()

def label(d,xy,text,fill=COL['line']): d.text(xy,text,font=font,fill=fill)
def shadow(d,box,r=18):
    x0,y0,x1,y1=box
    d.rounded_rectangle((x0+10,y0+12,x1+10,y1+12),radius=r,fill=(210,218,225))

def hero():
    im=Image.new('RGB',(W,H),COL['bg']); d=ImageDraw.Draw(im)
    d.text((40,30),'Codex Rover Bean - assembled color preview',font=font,fill=COL['line'])
    # base perspective-ish
    shadow(d,(270,460,1090,675),38)
    d.rounded_rectangle((250,430,1070,660),radius=42,fill=COL['cream'],outline=COL['line'],width=4)
    d.rounded_rectangle((220,405,1100,500),radius=48,fill=COL['bumper'],outline=COL['line'],width=3)
    d.rounded_rectangle((295,440,1025,630),radius=32,fill=COL['teal'],outline=COL['line'],width=3)
    # wheels
    for x in (330,940):
        d.ellipse((x-70,585,x+70,725),fill=COL['rubber'],outline=COL['line'],width=5)
        d.ellipse((x-35,620,x+35,690),fill=COL['grey'],outline=COL['line'],width=3)
    # mast head
    d.rounded_rectangle((545,270,635,470),radius=18,fill=COL['teal'],outline=COL['line'],width=4)
    d.rounded_rectangle((450,210,730,330),radius=34,fill=COL['charcoal'],outline=COL['line'],width=4)
    d.polygon([(465,222),(535,190),(545,222)],fill=COL['blue'],outline=COL['line'])
    d.polygon([(715,222),(645,190),(635,222)],fill=COL['blue'],outline=COL['line'])
    d.ellipse((575,242,625,292),fill=(10,12,18),outline=COL['line'],width=3)
    d.ellipse((505,260,530,285),fill=COL['lime']); d.ellipse((650,260,675,285),fill=COL['lime'])
    # sensors/estop
    for x in (300,395,980): d.rounded_rectangle((x,398,x+54,430),radius=8,fill=COL['blue'],outline=COL['line'],width=2)
    d.ellipse((1015,350,1085,420),fill=COL['red'],outline=COL['line'],width=4); d.rectangle((1035,415,1065,455),fill=COL['red'],outline=COL['line'])
    label(d,(1025,330),'E-stop')
    label(d,(455,340),'camera head @ ~205 mm')
    label(d,(165,382),'soft bumper halo with travel')
    label(d,(720,675),'80 mm wheels + guarded side pods')
    im.save(OUT/'codex_body_hero.png')

def service():
    im=Image.new('RGB',(W,H),COL['bg']); d=ImageDraw.Draw(im)
    d.text((40,30),'Top-off service view - low battery, Pi deck, cable channels',font=font,fill=COL['line'])
    d.rounded_rectangle((200,150,1200,760),radius=50,fill=COL['cream'],outline=COL['line'],width=4)
    d.rounded_rectangle((235,185,1165,725),radius=35,fill=(255,255,250),outline=COL['grey'],width=2)
    # battery
    d.rounded_rectangle((760,500,1110,645),radius=18,fill=COL['orange'],outline=COL['line'],width=4)
    d.rounded_rectangle((795,525,1075,620),radius=10,fill=(35,35,35),outline=COL['line'],width=3)
    for x in (835,1035): d.rounded_rectangle((x,485,x+28,660),radius=6,fill=COL['charcoal'])
    # deck/pi
    d.rounded_rectangle((300,230,720,560),radius=20,fill=COL['teal'],outline=COL['line'],width=4)
    d.rounded_rectangle((365,290,575,425),radius=8,fill=(48,126,88),outline=COL['line'],width=3)
    d.rectangle((380,440,565,510),fill=(130,210,220),outline=COL['line'],width=2)
    for x in range(610,690,22):
        for y in range(300,520,38): d.rounded_rectangle((x,y,x+12,y+26),radius=4,fill=COL['bg'])
    # channels + labels
    d.line((575,470,760,560),fill=COL['line'],width=6); d.line((520,560,520,680),fill=COL['line'],width=6)
    for p,t in [((792,466),'strap-retained battery cradle'),((365,265),'Raspberry Pi 5 + HAT keepout'),((600,575),'wire channels / zip ties'),((215,115),'base tray bosses for inserts')]: label(d,p,t)
    im.save(OUT/'codex_body_service.png')

def exploded():
    im=Image.new('RGB',(W,H),COL['bg']); d=ImageDraw.Draw(im)
    d.text((40,30),'Exploded printable assembly - flat-bottom modules, screw-together service',font=font,fill=COL['line'])
    layers=[('soft bumper carrier',COL['bumper'],(250,650,1150,720)),('lower base tray',COL['cream'],(280,540,1120,625)),('motor pods + battery cradle',COL['orange'],(350,410,1050,490)),('electronics deck',COL['teal'],(380,285,1020,355)),('mast + camera head',COL['charcoal'],(560,95,840,205))]
    for name,c,box in layers:
        d.rounded_rectangle(box,radius=25,fill=c,outline=COL['line'],width=4); label(d,(box[2]+20,box[1]+25),name)
    for x in (375,1025): d.ellipse((x-50,430,x+50,530),fill=COL['rubber'],outline=COL['line'],width=4)
    d.line((700,210,700,285),fill=COL['grey'],width=3); d.line((700,355,700,410),fill=COL['grey'],width=3); d.line((700,490,700,540),fill=COL['grey'],width=3); d.line((700,625,700,650),fill=COL['grey'],width=3)
    im.save(OUT/'codex_body_exploded.png')


def safety():
    im=Image.new('RGB',(W,H),COL['bg']); d=ImageDraw.Draw(im)
    d.text((40,30),'Safety planning preview - stop hardware zones and protected energy paths',font=font,fill=COL['line'])
    d.rounded_rectangle((230,170,1170,720),radius=48,fill=COL['cream'],outline=COL['line'],width=4)
    d.rounded_rectangle((205,145,1195,245),radius=48,fill=COL['bumper'],outline=COL['line'],width=4)
    d.arc((200,140,1200,730),180,360,fill=COL['teal'],width=10)
    # wheels / guarded pinch zones
    for x in (330,1030):
        d.ellipse((x-62,610,x+62,734),fill=COL['rubber'],outline=COL['line'],width=4)
        d.rounded_rectangle((x-88,570,x+88,680),radius=24,outline=COL['blue'],width=5)
    # battery, fuse, estop path
    d.rounded_rectangle((740,520,1090,650),radius=16,fill=COL['orange'],outline=COL['line'],width=4)
    for x in (805,1030): d.rectangle((x,500,x+28,670),fill=COL['charcoal'])
    d.rectangle((610,545,680,610),fill=COL['red'],outline=COL['line'],width=3)
    d.line((740,585,680,585),fill=COL['line'],width=5); d.line((610,585,505,585),fill=COL['line'],width=5)
    d.ellipse((1015,235,1095,315),fill=COL['red'],outline=COL['line'],width=4); d.rectangle((1042,315,1068,350),fill=COL['red'],outline=COL['line'])
    # tof coverage cones
    for xy,ang in [((300,245),-25),((430,245),0),((560,245),25),((245,430),-90),((1155,430),90)]:
        x,y=xy; d.polygon([(x,y),(x+110*math.cos(math.radians(ang-12)),y-110*math.sin(math.radians(ang-12))),(x+110*math.cos(math.radians(ang+12)),y-110*math.sin(math.radians(ang+12)))],fill=(210,235,255),outline=COL['blue'])
    # labels
    for xy,text in [((920,335),'reachable E-stop mount zone'),((745,675),'strap-retained battery plan'),((505,615),'planned fuse / motor cutoff zone'),((150,115),'planned bumper + switch travel'),((170,690),'pinch-zone / wheel-guard review'),((350,330),'front + side ToF coverage plan')]: label(d,xy,text)
    im.save(OUT/'codex_body_safety.png')

def print_layout():
    im=Image.new('RGB',(W,H),COL['bg']); d=ImageDraw.Draw(im)
    d.text((40,30),'Print layout preview - minimal supports / flat on bed',font=font,fill=COL['line'])
    d.rectangle((80,95,1320,820),outline=COL['grey'],width=3); label(d,(95,105),'nominal 220 x 220 mm bed tiles shown conceptually')
    boxes=[('base tray',COL['cream'],(130,160,560,475)),('electronics deck',COL['teal'],(640,170,1070,405)),('bumper carrier',COL['bumper'],(140,540,590,725)),('battery cradle',COL['orange'],(690,500,955,610)),('motor pods x2',COL['charcoal'],(1010,500,1230,625)),('ToF pods / head face',COL['blue'],(760,650,1210,745))]
    for name,c,box in boxes:
        d.rounded_rectangle(box,radius=22,fill=c,outline=COL['line'],width=3); label(d,(box[0]+12,box[1]+12),name,fill=(255,255,255) if c in (COL['charcoal'],COL['bumper'],COL['blue']) else COL['line'])
    im.save(OUT/'codex_body_print_layout.png')

import math
for f in (hero,service,exploded,safety,print_layout): f()
pillow_outputs = [
    OUT/'codex_body_hero.png',
    OUT/'codex_body_service.png',
    OUT/'codex_body_exploded.png',
    OUT/'codex_body_safety.png',
    OUT/'codex_body_print_layout.png',
]
print('generated', ', '.join(str(p) for p in pillow_outputs))
