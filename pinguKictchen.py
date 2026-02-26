"""
╔══════════════════════════════════════════╗
║   🐧  WADDLE KITCHEN      ULTIMATE  🐧  ║
╠══════════════════════════════════════════╣
║  pip install pygame                      ║
║  python waddle_kitchen_v6.py             ║
╠══════════════════════════════════════════╣
║  CONTROLS                                ║
║  Mouse  — click everything               ║
║  R      — restart                        ║
║  ESC    — quit (ALWAYS WORKS)            ║
╠══════════════════════════════════════════╣
║  HOW TO PLAY                             ║
║  Orders show at the top.                 ║
║  Click ingredients on the LEFT.          ║
║  Click SERVE when bowl matches.          ║
║  5 fails = game over. 90s = win!         ║
╠══════════════════════════════════════════╣
║  MUSIC                                   ║
║  "Penguin Parade on the Frozen Shore"    ║
║  by Marick Booster — procedurally        ║
║  approximated in pure Python+pygame.     ║
║  Place the real MP3/OGG alongside this   ║
║  file as penguin_parade.ogg to use it.  ║
╚══════════════════════════════════════════╝
"""

import pygame, sys, random, math, struct, time

# ── SAFE INIT ─────────────────────────────────────────────────
pygame.init()
try:
    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.mixer.init()
    AUDIO_OK = True
except Exception:
    AUDIO_OK = False


SW, SH = 1280, 780
screen = pygame.display.set_mode((SW, SH), pygame.RESIZABLE)
pygame.display.set_caption("Pingu’s Cozy Kitchen 🐧👨‍🍳✨")
clock = pygame.time.Clock()
FPS   = 60

# ── MUSIC: try real file first, fall back to procedural BGM ───
MUSIC_FILE = "Penguins Parade on the Frozen Shore.mp3"   # drop your MP3/OGG here
_music_loaded = False
if AUDIO_OK:
    import os
    for _ext in ("Penguins Parade on the Frozen Shore.mp3","penguin_parade.mp3","penguin_parade.wav"):
        if os.path.exists(_ext):
            try:
                pygame.mixer.music.load(_ext)
                pygame.mixer.music.set_volume(0.22)
                pygame.mixer.music.play(loops=-1)
                _music_loaded = True
                print(f"🎵 Loaded real music: {_ext}")
                break
            except Exception as e:
                print(f"⚠ Could not load {_ext}: {e}")

# ── HELPERS ───────────────────────────────────────────────────
def v(n): return int(n)          # identity — we design at 1280×780 directly
def lerp(a, b, t): return a + (b - a) * t
def clamp(x, lo, hi): return max(lo, min(hi, x))
def lc(a, b, t):                 # lerp_color
    return tuple(max(0, min(255, int(a[i] + (b[i] - a[i]) * t))) for i in range(3))

# ── PALETTE ───────────────────────────────────────────────────
BG0   = (8,  14, 40)
BG1   = (14, 22, 58)
GLASS = (22, 34, 85)
WHITE = (255,255,255)
OFFWH = (215,230,255)
PINK  = (255, 60,175)
CYAN  = (  0,210,255)
LIME  = ( 55,255,115)
GOLD  = (255,210, 30)
CORAL = (255, 90, 70)
PURP  = (170, 55,255)
TEAL  = ( 30,215,185)
ORNGE = (255,148, 20)
GREEN = ( 48,215,105)
RED   = (255, 55, 55)

# ── FONT LOADER ───────────────────────────────────────────────
def load_font(size, bold=True):
    for name in ("comicsansms", "trebuchetms", "verdana", "arial"):
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f: return f
        except Exception:
            pass
    return pygame.font.SysFont(None, size, bold=bold)

F_TITLE = load_font(42)
F_LG    = load_font(30)
F_MD    = load_font(21)
F_SM    = load_font(17)
F_XS    = load_font(13)
# End-screen fonts
F_HERO  = load_font(68)   # giant headline
F_BIG   = load_font(46)
F_MED2  = load_font(28)

# ── DRAWING PRIMITIVES (NO per-frame surface alloc for simple shapes) ──────
def draw_glass(surf, x, y, w, h, r=14, alpha=170, border=None, glow=None):
    """Fast glass panel — one Surface, cached externally when possible."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*GLASS, alpha), (0, 0, w, h), border_radius=r)
    pygame.draw.rect(s, (255, 255, 255, 20), (2, 2, w-4, h//3), border_radius=r)
    if border:
        pygame.draw.rect(s, (*border, 200), (0, 0, w, h), 2, border_radius=r)
    surf.blit(s, (x, y))
    if glow:
        gs = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*glow, 35), (0, 0, w+20, h+20), border_radius=r+10)
        surf.blit(gs, (x-10, y-10))

def draw_ring(surf, cx, cy, r, ratio, full_c, empty_c=(25,38,80)):
    """Circular timer ring — fast arc via polygon segments."""
    pygame.draw.circle(surf, empty_c, (cx, cy), r, 5)
    if ratio <= 0:
        return
    segs = max(1, int(48 * ratio))
    pts = []
    for i in range(segs + 1):
        a = math.pi/2 - 2*math.pi * (i/48)
        pts.append((cx + math.cos(a)*r, cy - math.sin(a)*r))
    if len(pts) >= 2:
        pygame.draw.lines(surf, full_c, False, pts, 5)

def draw_btn(surf, x, y, w, h, color, text, font, active=True, hover=False):
    alpha = 200 if active else 90
    border = color if active else (40, 50, 80)
    draw_glass(surf, x, y, w, h, r=12, alpha=alpha, border=border,
               glow=color if (active and hover) else None)
    tc = lc(color, WHITE, 0.7) if active else (55, 70, 110)
    t = font.render(text, True, tc)
    surf.blit(t, t.get_rect(center=(x+w//2, y+h//2)))

def glow_dot(surf, color, cx, cy, r):
    """Small glowing circle — minimal surface."""
    g = r + 8
    s = pygame.Surface((g*2, g*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, 45), (g, g), g)
    pygame.draw.circle(s, color, (g, g), r)
    surf.blit(s, (cx-g, cy-g))

# ── SOUND (tiny, fast, procedural) ───────────────────────────
def _sine_buf(freq, dur, vol=0.32):
    sr = 44100; n = int(sr * dur)
    buf = bytearray(n * 2)
    for i in range(n):
        env = min(1.0, (n-i)/(n*0.25))          # simple decay
        val = int(math.sin(2*math.pi*freq*i/sr) * env * vol * 32767)
        struct.pack_into("<h", buf, i*2, clamp(val,-32767,32767))
    return bytes(buf)

def _chord_buf(freqs, dur=0.28, vol=0.28):
    sr = 44100; n = int(sr * dur)
    buf = bytearray(n * 2)
    for i in range(n):
        env = max(0, 1 - i/n)**0.6
        s = sum(math.sin(2*math.pi*f*i/sr) for f in freqs) / len(freqs)
        val = int(s * env * vol * 32767)
        struct.pack_into("<h", buf, i*2, clamp(val,-32767,32767))
    return bytes(buf)

def _bgm_buf():
    """Gentle pentatonic café loop — 80 BPM, sine only."""
    sr = 44100; bpm = 80; beat = 60/bpm
    bars = 8; total = int(sr * beat * 4 * bars)
    buf = bytearray(total * 2)
    penta = [261.63, 293.66, 329.63, 392.00, 440.00,
             523.25, 587.33, 659.25, 783.99, 880.00]
    # melody: pentatonic note indices, -1 = rest
    mel = [0,-1,2,-1,4,2,0,-1, 3,2,3,-1,5,4,3,-1,
           0,-1,2,4,5,4,2,-1,  3,-1,2,0,2,0,-1,-1]
    nd = int(beat * sr * 0.5)   # half-beat per note

    def add(gi, val):
        if 0 <= gi < total:
            ex = struct.unpack_from("<h", buf, gi*2)[0]
            struct.pack_into("<h", buf, gi*2, clamp(ex+val,-32767,32767))

    for idx, note in enumerate(mel):
        if note < 0: continue
        freq = penta[note % len(penta)]
        st = idx * nd
        atk = min(int(sr*0.04), nd//4)
        for i in range(min(nd, total-st)):
            env = (i/atk) if i < atk else max(0, 1-(i-atk)/max(1,nd-atk))**0.5
            s = math.sin(2*math.pi*freq*i/sr) * 0.10 * env
            s += math.sin(2*math.pi*freq*2*i/sr) * 0.022 * env
            add(st+i, int(s*32767))

    # soft bass every beat
    bass_p = [0,0,2,2,0,0,3,3]
    bd = int(beat * sr)
    for idx, note in enumerate(bass_p):
        freq = penta[note % len(penta)] / 2
        st = idx * bd
        for i in range(min(bd, total-st)):
            env = max(0, 1-i/bd)**0.35
            if i < int(sr*0.04): env *= i/max(1,int(sr*0.04))
            s = math.sin(2*math.pi*freq*i/sr) * 0.045 * env
            add(st+i, int(s*32767))
    return bytes(buf)

SFX = {}
if AUDIO_OK:
    try:
        print("🎵 Generating sounds...")
        SFX["pop"]   = pygame.mixer.Sound(buffer=_sine_buf(700, 0.08, 0.28))
        SFX["ok"]    = pygame.mixer.Sound(buffer=_chord_buf([523,659,784], 0.30, 0.32))
        SFX["wrong"] = pygame.mixer.Sound(buffer=_sine_buf(180, 0.20, 0.25))
        SFX["combo"] = pygame.mixer.Sound(buffer=_chord_buf([523,659,784,1047], 0.38, 0.34))
        SFX["expire"]= pygame.mixer.Sound(buffer=_sine_buf(280, 0.18, 0.20))
        SFX["lvl"]   = pygame.mixer.Sound(buffer=_chord_buf([392,494,587,784], 0.50, 0.35))
        SFX["click"] = pygame.mixer.Sound(buffer=_sine_buf(1050, 0.05, 0.15))
        print("🎵 Building BGM (procedural fallback)...")
        if not _music_loaded:
            bgm = pygame.mixer.Sound(buffer=_bgm_buf())
            bgm.set_volume(0.18)
            bgm.play(loops=-1)
            print("🎵 Procedural BGM playing!")
        else:
            print("🎵 Using real music file — skipping procedural BGM")
    except Exception as e:
        print(f"⚠ Audio skipped: {e}")
        AUDIO_OK = False

def sfx(name):
    if AUDIO_OK and name in SFX:
        try: SFX[name].play()
        except: pass

# ── DATA ──────────────────────────────────────────────────────
INGREDIENTS = [
    {"name":"Salmon",    "color":(255,110, 70), "short":"salmon",  "unlock":1},
    {"name":"Rice",      "color":(200,218,255), "short":"rice",    "unlock":1},
    {"name":"Avocado",   "color":( 65,185, 75), "short":"avocado", "unlock":1},
    {"name":"Ice",       "color":(115,200,255), "short":"ice",     "unlock":1},
    {"name":"Mango",     "color":(255,185, 35), "short":"mango",   "unlock":2},
    {"name":"Cream",     "color":(255,240,210), "short":"cream",   "unlock":2},
    {"name":"Boba",      "color":(120, 72, 32), "short":"boba",    "unlock":2},
    {"name":"Chocolate", "color":( 90, 52, 22), "short":"choco",   "unlock":3},
    {"name":"Shrimp",    "color":(235,115, 65), "short":"shrimp",  "unlock":3},
    {"name":"Seaweed",   "color":( 45,175, 75), "short":"seaweed", "unlock":3},
    {"name":"Cheese",    "color":(255,205, 45), "short":"cheese",  "unlock":4},
    {"name":"Squid",     "color":(185, 95,215), "short":"squid",   "unlock":4},
    {"name":"Strawberry","color":(255, 65, 95), "short":"strawb",  "unlock":5},
    {"name":"Krill",     "color":(215, 65, 85), "short":"krill",   "unlock":5},
]
IMAP = {i["short"]: i for i in INGREDIENTS}

# All recipes validated — ingredients unlock ≤ recipe unlock
RECIPES = [
    {"name":"Poke Bowl",   "unlock":1,"stars":1,"time":18,"ing":["salmon","rice","avocado"]},
    {"name":"Salmon Chill","unlock":1,"stars":1,"time":15,"ing":["salmon","rice","ice"]},
    {"name":"Avo Chill",   "unlock":1,"stars":1,"time":14,"ing":["avocado","ice","rice"]},
    {"name":"Mango Shake", "unlock":2,"stars":1,"time":16,"ing":["mango","cream","ice"]},
    {"name":"Bubble Tea",  "unlock":2,"stars":1,"time":15,"ing":["boba","cream","ice"]},
    {"name":"Mango Cream", "unlock":2,"stars":2,"time":18,"ing":["mango","cream","boba"]},
    {"name":"Avo Bowl",    "unlock":2,"stars":2,"time":19,"ing":["avocado","rice","mango"]},
    {"name":"Sushi Bowl",  "unlock":3,"stars":2,"time":20,"ing":["salmon","rice","seaweed"]},
    {"name":"Choco Dream", "unlock":3,"stars":2,"time":18,"ing":["choco","cream","boba"]},
    {"name":"Ramen Bowl",  "unlock":3,"stars":2,"time":22,"ing":["shrimp","seaweed","rice"]},
    {"name":"Protein Bowl","unlock":3,"stars":3,"time":25,"ing":["salmon","avocado","shrimp","rice"]},
    {"name":"Ice Cream",   "unlock":4,"stars":2,"time":16,"ing":["cream","choco","ice"]},
    {"name":"Cheese Ramen","unlock":4,"stars":3,"time":24,"ing":["cheese","shrimp","seaweed","rice"]},
    {"name":"Squid Ink",   "unlock":4,"stars":2,"time":20,"ing":["squid","seaweed","rice"]},
    {"name":"Milkshake",   "unlock":5,"stars":2,"time":16,"ing":["cream","strawb","ice"]},
    {"name":"Mocktail",    "unlock":5,"stars":3,"time":22,"ing":["mango","strawb","cream","ice"]},
    {"name":"Polar Plate", "unlock":5,"stars":3,"time":26,"ing":["salmon","krill","squid","seaweed"]},
]

# Sanity-check recipes at startup
for _r in RECIPES:
    for _i in _r["ing"]:
        _ing_unlock = IMAP[_i]["unlock"]
        assert _ing_unlock <= _r["unlock"], \
            f"Recipe '{_r['name']}' needs '{_i}' (unlock {_ing_unlock}) but recipe unlocks at {_r['unlock']}"

# ── INGREDIENT ICONS (procedural, drawn once into cached surfaces) ─────────
def _make_icon(short, size):
    s  = pygame.Surface((size, size), pygame.SRCALPHA)
    c  = size // 2
    r  = size // 2 - 2
    col = IMAP.get(short, {"color":(150,150,150)})["color"]
    dk  = lc(col, (10,10,30), 0.40)
    lt  = lc(col, (255,255,255), 0.55)

    def circ(x, y, rad, clr, a=255):
        if rad < 1: return
        ts = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*clr, a), (rad, rad), rad)
        s.blit(ts, (x-rad, y-rad))

    if short == "salmon":
        pts = [(c-12,c),(c-3,c-8),(c+10,c-3),(c+14,c),(c+10,c+3),(c-3,c+8)]
        pygame.draw.polygon(s, col, pts)
        pygame.draw.polygon(s, dk, [(c+10,c-3),(c+18,c-8),(c+18,c+8),(c+10,c+3)])
        pygame.draw.line(s, lt, (c-3,c-5),(c+7,c-1), 2)
        pygame.draw.circle(s, (30,20,20), (c-6,c-1), 2)
    elif short == "rice":
        pygame.draw.ellipse(s, dk, (c-12,c-2,24,15))
        pygame.draw.ellipse(s, (228,235,255), (c-11,c-3,22,13))
        for ox,oy in [(-4,-2),(0,-4),(4,-2),(-2,2),(2,2)]:
            circ(c+ox,c+oy,3,(248,252,255))
    elif short == "avocado":
        pygame.draw.ellipse(s, dk, (c-9,c-13,18,26))
        pygame.draw.ellipse(s, col, (c-8,c-12,16,24))
        pygame.draw.ellipse(s, lt,  (c-5,c-10,10,16))
        pygame.draw.ellipse(s, (100,62,30),(c-4,c-3,8,11))
    elif short == "ice":
        pts = [(c,c-13),(c+11,c-6),(c+11,c+6),(c,c+13),(c-11,c+6),(c-11,c-6)]
        pygame.draw.polygon(s, col, pts)
        pygame.draw.polygon(s, lt, pts, 2)
        pygame.draw.line(s, WHITE, (c-3,c-6),(c+3,c), 1)
        circ(c-4,c-4,2,WHITE,70)
    elif short == "mango":
        pygame.draw.ellipse(s, dk, (c-9,c-13,18,28))
        pygame.draw.ellipse(s, col, (c-8,c-12,16,26))
        pygame.draw.ellipse(s, (255,222,80),(c-4,c-9,8,18))
        pygame.draw.line(s, (90,140,55),(c,c-12),(c,c-17),2)
    elif short == "cream":
        circ(c,c+6,10,(255,248,235))
        for i in range(3):
            a2 = math.radians(-90+i*120)
            circ(c+int(math.cos(a2)*6),c+6+int(math.sin(a2)*6),6,(255,244,225))
        circ(c,c,6,WHITE)
        circ(c,c-9,4,(215,40,55))
        pygame.draw.line(s,(75,145,45),(c,c-9),(c+4,c-14),1)
    elif short == "boba":
        pygame.draw.rect(s, dk,  (c-9,c-8,18,20), border_radius=3)
        pygame.draw.rect(s, col, (c-8,c-7,16,18), border_radius=3)
        for ox,oy in [(-3,1),(1,4),(5,1),(-1,7),(4,7)]:
            circ(c-2+ox,c+oy,2,(55,32,12))
        pygame.draw.line(s,(195,95,45),(c+4,c-12),(c+6,c+3),2)
    elif short == "choco":
        for row in range(2):
            for col2 in range(2):
                rx2,ry2 = c-10+col2*10, c-8+row*10
                pygame.draw.rect(s, dk,  (rx2,ry2,9,9), border_radius=2)
                pygame.draw.rect(s, col, (rx2+1,ry2+1,7,7), border_radius=2)
        pygame.draw.line(s, dk,(c,c-8),(c,c+2),2)
        pygame.draw.line(s, dk,(c-10,c),(c+10,c),2)
    elif short == "shrimp":
        pts2 = []
        for i in range(10):
            a2 = math.radians(i*16-20)
            rad = 9-i*0.2
            pts2.append((c+int(math.cos(a2)*rad)-2, c+int(math.sin(a2)*rad+i*1.2)-6))
        if len(pts2)>1: pygame.draw.lines(s,col,False,pts2,4)
        if len(pts2)>1: pygame.draw.lines(s,lt, False,pts2[:5],2)
        if pts2: circ(pts2[0][0],pts2[0][1],3,dk)
    elif short == "seaweed":
        for st2 in range(3):
            sx2=c-7+st2*7; pts3=[]
            for j in range(7):
                w2=math.sin(j*0.9+st2)*4
                pts3.append((sx2+int(w2),c+10-j*4))
            if len(pts3)>1:
                pygame.draw.lines(s,dk, False,pts3,4)
                pygame.draw.lines(s,col,False,pts3,2)
    elif short == "cheese":
        pts4=[(c-12,c+8),(c+12,c+8),(c+6,c-10),(c-6,c-10)]
        pygame.draw.polygon(s,col,pts4)
        pygame.draw.polygon(s,dk, pts4,2)
        for hx2,hy2 in [(c-2,c+2),(c+5,c-3),(c-6,c-2)]:
            circ(hx2,hy2,2,dk)
    elif short == "squid":
        pygame.draw.ellipse(s,col,(c-7,c-12,14,16))
        pygame.draw.ellipse(s,lt, (c-4,c-10, 8, 9))
        pygame.draw.circle(s,(25,15,50),(c-3,c-7),2)
        pygame.draw.circle(s,(25,15,50),(c+3,c-7),2)
        for i2 in range(4):
            tx2=c-6+i2*4
            for j2 in range(3):
                py2=c+5+j2*4
                circ(tx2,int(py2),2,dk)
    elif short == "strawb":
        pygame.draw.ellipse(s,col,(c-8,c-8,16,17))
        pygame.draw.ellipse(s,dk, (c-8,c-8,16,17),2)
        for sx2,sy2 in [(-3,-3),(2,-1),(-1,2),(3,0),(0,4)]:
            circ(c+sx2,c+sy2,1,(255,238,238))
        pygame.draw.polygon(s,(70,170,40),[(c,c-8),(c-3,c-13),(c,c-10),(c+3,c-13)])
    elif short == "krill":
        for i3 in range(5):
            a3=math.radians(i3*20-40)
            circ(c+int(math.cos(a3)*8),c+int(math.sin(a3)*8),3,col)
        circ(c,c,3,dk)
    else:
        circ(c,c,r,col)
    # Sheen
    sh = pygame.Surface((size,size),pygame.SRCALPHA)
    pygame.draw.circle(sh,(255,255,255,22),(c-r//3,c-r//3),r//2)
    s.blit(sh,(0,0))
    return s

print("🎨 Rendering icons...")
ICONS    = {i["short"]: _make_icon(i["short"], 44) for i in INGREDIENTS}
ICONS_SM = {i["short"]: _make_icon(i["short"], 26) for i in INGREDIENTS}

# ── BACKGROUND (built once) ────────────────────────────────────
def _build_bg():
    surf = pygame.Surface((SW, SH))
    for y in range(SH):
        t = y/SH
        c = lc(BG0, BG1, t)
        pygame.draw.line(surf, c, (0, y), (SW, y))
    return surf
print("🖼 Building background...")
BG_SURF = _build_bg()

# ── PENGUIN (drawn procedurally, NO per-draw surface alloc) ───
class Penguin:
    def __init__(self, x, y):
        self.x=x; self.y=y
        self.bob_t=0; self.blink_t=3; self.blinking=False
        self.wing_t=0; self.idle_t=0; self.dance_t=0
        self.happy=False; self.happy_t=0
        self.sad=False;   self.sad_t=0
        self.bounce=0;    self.bounce_v=0
        self.outfit=0    # hat band colour index

    def react_happy(self):
        self.happy=True; self.happy_t=1.6; self.bounce_v=-9

    def react_sad(self):
        self.sad=True; self.sad_t=1.4

    def update(self, dt):
        self.bob_t  += dt*1.8
        self.wing_t += dt*3.2
        self.idle_t += dt*0.9
        self.dance_t += dt
        self.blink_t -= dt
        if self.blink_t <= 0:
            self.blinking = True
        if self.blinking and self.blink_t < -0.12:
            self.blinking = False
            self.blink_t = random.uniform(2, 5)
        if self.happy:
            self.happy_t -= dt
            if self.happy_t <= 0: self.happy = False
        if self.sad:
            self.sad_t -= dt
            if self.sad_t <= 0: self.sad = False
        self.bounce_v += (-self.bounce*580 - self.bounce_v*18)*dt
        self.bounce   += self.bounce_v*dt

    def draw(self, surf):
        x = self.x
        y = int(self.y + math.sin(self.bob_t)*4 + self.bounce*22)
        if self.happy:
            x += int(math.sin(self.dance_t*5)*9)

        wf = math.sin(self.wing_t) * (20 if self.happy else 5)

        # Shadow
        sh = pygame.Surface((90,18),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,40,80),(0,0,90,18))
        surf.blit(sh,(x-45,y+98))

        # Body
        pygame.draw.ellipse(surf,(20,20,52),(x-31,y+14,62,84))
        # Belly
        for i in range(8):
            t2=i/7
            bc=lc((242,250,255),(198,218,245),t2)
            bw=int(lerp(28,18,t2)); bh=int(lerp(64,42,t2))
            pygame.draw.ellipse(surf,bc,(x-bw//2,y+20+int(t2*12),bw,bh))

        # Wings
        lwx = x-31-22+int(wf)
        pygame.draw.polygon(surf,(16,16,48),[(x-29,y+30),(lwx,y+46),(x-25-18,y+80),(x-20,y+72)])
        rwx = x+31+22-int(wf)
        pygame.draw.polygon(surf,(16,16,48),[(x+29,y+30),(rwx,y+46),(x+25+18,y+80),(x+20,y+72)])

        # Feet
        fb = int(abs(math.sin(self.dance_t*5))*6) if self.happy else 0
        pygame.draw.ellipse(surf,(255,185,30),(x-25,y+97+fb,22,11))
        pygame.draw.ellipse(surf,(255,185,30),(x+3, y+97-fb,22,11))

        # Head
        pygame.draw.circle(surf,(20,20,52),(x,y+10),30)
        # Face patch
        fp=pygame.Surface((34,31),pygame.SRCALPHA)
        pygame.draw.ellipse(fp,(242,250,255,255),(0,0,34,31))
        surf.blit(fp,(x-17,y+2))

        # Cheeks
        if self.happy:
            ck=pygame.Surface((18,11),pygame.SRCALPHA)
            pygame.draw.ellipse(ck,(255,120,160,120),(0,0,18,11))
            surf.blit(ck,(x-26,y+20)); surf.blit(ck,(x+8,y+20))
        elif self.sad:
            ck=pygame.Surface((18,11),pygame.SRCALPHA)
            pygame.draw.ellipse(ck,(100,100,205,100),(0,0,18,11))
            surf.blit(ck,(x-26,y+20)); surf.blit(ck,(x+8,y+20))

        # Eyes
        eo = 2 if self.happy else 0
        if self.blinking:
            pygame.draw.ellipse(surf,(20,20,52),(x-12,y+7,10,4))
            pygame.draw.ellipse(surf,(20,20,52),(x+2, y+7,10,4))
        else:
            pygame.draw.circle(surf,(240,248,255),(x-9, y+10),7)
            pygame.draw.circle(surf,(240,248,255),(x+9, y+10),7)
            pygame.draw.circle(surf,(25,25,55),(x-8, y+10+eo),5)
            pygame.draw.circle(surf,(25,25,55),(x+10,y+10+eo),5)
            pygame.draw.circle(surf,WHITE,(x-6,y+8+eo),2)
            pygame.draw.circle(surf,WHITE,(x+12,y+8+eo),2)

        # Beak
        by2 = y+19
        pygame.draw.polygon(surf,(255,190,40),[(x-7,by2),(x+7,by2),(x,by2+11)])
        if self.happy:
            pygame.draw.arc(surf,(255,80,110),(x-8,by2+2,16,8),math.pi,2*math.pi,2)
        elif self.sad:
            pygame.draw.arc(surf,(80,80,165),(x-8,by2+7,16,8),0,math.pi,2)
            td=pygame.Surface((6,10),pygame.SRCALPHA)
            pygame.draw.ellipse(td,(140,180,255,165),(0,0,6,10))
            surf.blit(td,(x+11,y+15))

        # Chef hat
        pygame.draw.rect(surf,(246,246,252),(x-24,y-21,48,8),border_radius=4)
        hat=[(x-20,y-21),(x+20,y-21),(x+15,y-55),(x-15,y-55)]
        pygame.draw.polygon(surf,(246,246,252),hat)
        band_c=[PINK,CYAN,GOLD,LIME,PURP][self.outfit % 5]
        pygame.draw.polygon(surf,band_c,[(x-19,y-23),(x+19,y-23),(x+18,y-30),(x-18,y-30)])
        pygame.draw.polygon(surf,(235,235,248),hat,2)
        pygame.draw.circle(surf,(246,246,252),(x,y-55),8)

        # Happy sparkles (cheap — just lines/circles, no surface alloc)
        if self.happy:
            for i in range(3):
                a3 = self.dance_t*4 + i*2.1
                sx3 = x + int(math.cos(a3)*42)
                sy3 = (y-22) + int(math.sin(a3)*20)
                sc3 = [GOLD,PINK,CYAN][i]
                pygame.draw.circle(surf, sc3, (sx3,sy3), 4)
                pygame.draw.circle(surf, WHITE, (sx3,sy3), 2)

# ── PARTICLES (pooled, no per-update surface alloc) ───────────
class Particle:
    __slots__ = ["x","y","vx","vy","color","life","decay","r","label","star","grav"]
    def __init__(self,x,y,color,label=None,star=False,rise=False):
        self.x=x+random.uniform(-16,16); self.y=y+random.uniform(-8,8)
        spd=random.uniform(80,160)
        ang=random.uniform(0,math.pi*2)
        self.vx=math.cos(ang)*spd
        self.vy=(random.uniform(-140,-60) if rise else math.sin(ang)*spd)
        self.color=color; self.label=label; self.star=star
        self.life=1.0; self.decay=random.uniform(0.75,1.35)
        self.r=random.randint(3,8); self.grav=125
    def update(self,dt):
        self.x+=self.vx*dt; self.y+=self.vy*dt
        self.vy+=self.grav*dt; self.life-=self.decay*dt
    def draw(self,surf):
        if self.life<=0: return
        a=int(255*clamp(self.life,0,1)); r=max(1,int(self.r))
        ts=pygame.Surface((r*2+2,r*2+2),pygame.SRCALPHA)
        pygame.draw.circle(ts,(*self.color,a),(r+1,r+1),r)
        surf.blit(ts,(int(self.x)-r,int(self.y)-r))
        if self.label and self.life>0.3:
            la=int(255*clamp((self.life-0.3)/0.7,0,1))
            lt2=F_MD.render(self.label,True,self.color); lt2.set_alpha(la)
            surf.blit(lt2,lt2.get_rect(center=(int(self.x),int(self.y)-r-12)))

class FloatText:
    __slots__=["text","x","y","color","font","life","vy"]
    def __init__(self,text,x,y,color,large=False):
        self.text=text;self.x=x;self.y=y;self.color=color
        self.font=F_LG if large else F_MD
        self.life=1.0; self.vy=-68
    def update(self,dt):
        self.y+=self.vy*dt; self.vy*=0.90; self.life-=dt*0.8
    def draw(self,surf):
        if self.life<=0: return
        a=int(255*clamp(self.life,0,1))
        t=self.font.render(self.text,True,self.color); t.set_alpha(a)
        surf.blit(t,t.get_rect(center=(int(self.x),int(self.y))))

class DropAnim:
    __slots__=["icon","sx","sy","ex","ey","t","done"]
    def __init__(self,icon,start,end):
        self.icon=icon; self.sx,self.sy=start; self.ex,self.ey=end
        self.t=0; self.done=False
    def update(self,dt):
        self.t=min(1.0,self.t+dt/0.36)
        if self.t>=1.0: self.done=True
    def draw(self,surf):
        et=1-(1-self.t)**2          # ease-out quad
        x=lerp(self.sx,self.ex,et)
        y=lerp(self.sy,self.ey,et)-math.sin(self.t*math.pi)*60
        icon=pygame.transform.rotozoom(self.icon,lerp(20,0,et),lerp(1.3,1.0,et))
        surf.blit(icon,icon.get_rect(center=(int(x),int(y))))

# ── ORDER CARD ────────────────────────────────────────────────
class OrderCard:
    W=200; H=155
    def __init__(self,recipe,speed=1.0):
        self.recipe=recipe
        self.total=recipe["time"]/speed
        self.remain=self.total
        self.done=False; self.failed=False
        self.slide=0.0; self.done_t=1.5
    def update(self,dt):
        self.slide=min(1.0,self.slide+dt*5)
        if self.done:
            self.done_t=max(0,self.done_t-dt*1.2); return
        if self.failed: return
        self.remain=max(0,self.remain-dt)
        if self.remain<=0: self.failed=True; sfx("expire")
    @property
    def ratio(self): return clamp(self.remain/self.total,0,1)
    def draw(self,surf,ox,oy):
        W,H=self.W,self.H
        # slide in from top
        ease=1-(1-self.slide)**3
        ay=int(oy-(1-ease)*85)

        rat=self.ratio
        if   self.done:    bc=LIME
        elif self.failed:  bc=RED
        elif rat>0.5:      bc=lc(CYAN,PINK,1-rat)
        elif rat>0.25:     bc=ORNGE
        else:
            fl=0.5+0.5*math.sin(time.time()*11)
            bc=lc(RED,GOLD,fl)

        draw_glass(surf,ox,ay,W,H,r=16,alpha=195,border=bc,glow=bc)

        # Name
        nm=F_XS.render(self.recipe["name"],True,OFFWH)
        surf.blit(nm,nm.get_rect(centerx=ox+W//2,top=ay+7))

        # Stars
        strs=self.recipe["stars"]
        stx=ox+W//2-strs*10
        for si in range(strs):
            glow_dot(surf,GOLD,stx+si*20+10,ay+26,5)

        # Ingredient icons
        ingrs=self.recipe["ing"]; n=len(ingrs)
        sp=min((W-16)//n,36); isx=ox+W//2-sp*(n-1)//2
        for i,short in enumerate(ingrs):
            ix=isx+i*sp; iy=ay+52
            icon=ICONS_SM.get(short)
            if icon: surf.blit(icon,icon.get_rect(center=(ix,iy)))
            # step badge
            bdg=pygame.Surface((13,13),pygame.SRCALPHA)
            pygame.draw.circle(bdg,(*PURP,190),(6,6),6)
            ns=F_XS.render(str(i+1),True,WHITE)
            bdg.blit(ns,ns.get_rect(center=(6,6)))
            surf.blit(bdg,(ix-6,iy-20))

        # Ring timer
        rcx=ox+W//2; rcy=ay+H-26; rr=20
        pygame.draw.circle(surf,(18,28,65),(rcx,rcy),rr+4)
        pygame.draw.circle(surf,(28,42,90),(rcx,rcy),rr,5)
        if not self.done and not self.failed and rat>0:
            draw_ring(surf,rcx,rcy,rr,rat,lc(RED,GREEN,rat))
        ts=F_XS.render(
            "DONE!" if self.done else ("GONE!" if self.failed else f"{int(self.remain)+1}"),
            True, LIME if self.done else (RED if self.failed else WHITE))
        surf.blit(ts,ts.get_rect(center=(rcx,rcy)))

        # Done/fail overlay
        if self.done:
            ov=pygame.Surface((W,H),pygame.SRCALPHA)
            pygame.draw.rect(ov,(*GREEN,45),(0,0,W,H),border_radius=16)
            surf.blit(ov,(ox,ay))
        elif self.failed:
            ov=pygame.Surface((W,H),pygame.SRCALPHA)
            pygame.draw.rect(ov,(*RED,45),(0,0,W,H),border_radius=16)
            surf.blit(ov,(ox,ay))

# ── INGREDIENT BUTTON ─────────────────────────────────────────
class IngBtn:
    H=48
    def __init__(self,ing,x,y,w):
        self.ing=ing; self.rect=pygame.Rect(x,y,w,self.H)
        self.press_t=0; self.hover=False; self.locked=False
    def update(self,dt,mp,unlocked):
        self.locked = not unlocked
        self.hover  = self.rect.collidepoint(mp) and not self.locked
        if self.press_t>0: self.press_t-=dt
    def press(self): self.press_t=0.12
    def draw(self,surf):
        col=self.ing["color"]; rx,ry,rw,rh=self.rect
        if self.locked:
            draw_glass(surf,rx,ry,rw,rh,r=10,alpha=90,border=(38,48,88))
            lt2=F_XS.render("LOCKED",True,(55,75,115))
            surf.blit(lt2,lt2.get_rect(center=(rx+rw//2,ry+rh//2))); return
        pr=clamp(self.press_t/0.12,0,1)
        draw_glass(surf,rx,ry,rw,rh,r=10,alpha=215,border=col,
                   glow=col if (self.hover or pr>0) else None)
        icon=ICONS.get(self.ing["short"])
        if icon:
            ic=(pygame.transform.rotozoom(icon,0,1.0+0.08*pr) if pr>0.01 else icon)
            surf.blit(ic,ic.get_rect(center=(rx+26,ry+rh//2)))
        nc=lc(col,WHITE,0.72)
        nm=F_SM.render(self.ing["name"],True,nc)
        surf.blit(nm,nm.get_rect(midleft=(rx+52,ry+rh//2)))
    def is_clicked(self,pos): return self.rect.collidepoint(pos) and not self.locked

# ── BACKGROUND STARS (lightweight) ────────────────────────────
class Stars:
    def __init__(self,n=60):
        self.data=[(random.randint(0,SW),random.randint(0,SH),
                    random.uniform(0.8,2.2),random.uniform(0,math.pi*2),
                    random.uniform(1.5,3.5)) for _ in range(n)]
        self.t=0
    def update(self,dt): self.t+=dt
    def draw(self,surf):
        for (sx,sy,sr,sph,ssp) in self.data:
            a=int(160*(0.4+0.6*abs(math.sin(sph+self.t*ssp))))
            r=int(sr)
            if r<1: continue
            pygame.draw.circle(surf,(210,228,255,255)[:3],(sx,sy),r)

# ── AURORA (2 waves, cached surface updated every 6 frames) ───
class Aurora:
    def __init__(self):
        self.waves=[
            {"phase":random.uniform(0,math.pi*2),"speed":0.22,"y":int(SH*0.20),
             "amp":55,"color":(0,220,180),"width":280,"alpha":22},
            {"phase":random.uniform(0,math.pi*2),"speed":0.34,"y":int(SH*0.38),
             "amp":45,"color":(80,60,255),"width":240,"alpha":18},
        ]
        self._surf=pygame.Surface((SW,SH),pygame.SRCALPHA)
        self._frame=0
    def update(self,dt):
        for w in self.waves: w["phase"]+=w["speed"]*dt
    def draw(self,surf):
        self._frame+=1
        if self._frame%6==0:      # only redraw aurora every 6 frames
            self._surf.fill((0,0,0,0))
            for w in self.waves:
                top,bot=[],[]
                for x in range(0,SW+20,18):
                    off=math.sin(x*0.007+w["phase"])*w["amp"]
                    top.append((x,w["y"]+off))
                    bot.append((x,w["y"]+off+w["width"]))
                pts=top+list(reversed(bot))
                if len(pts)>=3:
                    pygame.draw.polygon(self._surf,(*w["color"],w["alpha"]),pts)
        surf.blit(self._surf,(0,0))

# ── SNOWFLAKES (simple dots) ───────────────────────────────────
class Snowflake:
    __slots__=["x","y","sp","dr","r","al"]
    def __init__(self,fresh=False):
        self.x=random.uniform(0,SW)
        self.y=random.uniform(0,SH) if not fresh else -10
        self.sp=random.uniform(18,55); self.dr=random.uniform(-12,12)
        self.r=random.uniform(1.5,3.5); self.al=random.randint(55,145)
    def update(self,dt):
        self.y+=self.sp*dt; self.x+=self.dr*dt
        if self.y>SH+10: self.__init__(fresh=True)
    def draw(self,surf):
        pygame.draw.circle(surf,(200,225,255),(int(self.x),int(self.y)),max(1,int(self.r)))

# ══════════════════════════════════════════════════════════════
#  END SCREEN  (animated win / lose — full procedural display)
# ══════════════════════════════════════════════════════════════

def _draw_outlined_text(surf, font, text, color, outline_col, cx, cy, outline=3):
    """Render text with a soft drop-shadow outline for readability."""
    for dx in range(-outline, outline+1):
        for dy in range(-outline, outline+1):
            if dx==0 and dy==0: continue
            sh = font.render(text, True, outline_col)
            surf.blit(sh, sh.get_rect(center=(cx+dx, cy+dy)))
    t = font.render(text, True, color)
    surf.blit(t, t.get_rect(center=(cx, cy)))

def _draw_gradient_rect(surf, rect, top_c, bot_c, radius=24):
    """Vertical gradient fill inside a rounded rect (cached per call)."""
    x,y,w,h = rect
    tmp = pygame.Surface((w,h), pygame.SRCALPHA)
    for row in range(h):
        t = row/h
        c = lc(top_c, bot_c, t)
        pygame.draw.line(tmp, (*c,225), (0,row), (w,row))
    # apply rounded mask
    mask = pygame.Surface((w,h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255,255),(0,0,w,h), border_radius=radius)
    tmp.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(tmp,(x,y))

class EndScreen:
    """Animated full-screen win or lose overlay."""

    # Cute penguin personality messages
    WIN_MSGS = [
        "You're a culinary genius, little penguin!",
        "The frozen kitchen bows to your greatness!",
        "Every dish was served with love and fish!",
        "Master Chef of the Antarctic! Bow down!",
        "Your cooking made the polar bears cry happy tears!",
    ]
    LOSE_MSGS = [
        "The fish got away... but penguins never give up!",
        "Oops! Even the best chefs burn the seaweed sometimes.",
        "The kitchen timer won this round. Not next time!",
        "Your wings tried so hard. Try again, little buddy!",
        "The orders were too spicy for today. Waddle back!",
    ]
    WIN_SUBS = [
        "All orders served fresh from the frozen shore!",
        "The customers are sliding with joy!",
        "90 seconds of pure penguin perfection!",
        "Arctic Michelin Star awarded!",
    ]
    LOSE_SUBS = [
        "5 expired orders... the kitchen needs you back!",
        "The hungry penguins are waiting for round two.",
        "Shake off the ice and try again!",
        "Every master chef had a bad day once.",
    ]

    def __init__(self, win: bool, score: int, stars: int, level: int):
        self.win   = win
        self.score = score
        self.stars = stars
        self.level = level
        self.t     = 0.0          # animation time
        self.phase = 0.0          # continuous oscillation

        # Pick random personality strings
        self.headline = random.choice(self.WIN_MSGS if win else self.LOSE_MSGS)
        self.subtitle  = random.choice(self.WIN_SUBS  if win else self.LOSE_SUBS)

        # Floating decoration elements (emoji-like drawn shapes)
        self.floaties = []
        symbols = ["star","heart","snowflake","fish","note"] if win else \
                  ["snowflake","fish","note","drop","zzz"]
        for i in range(18):
            self.floaties.append({
                "x": random.uniform(40, SW-40),
                "y": random.uniform(SH*0.05, SH*0.92),
                "sym": random.choice(symbols),
                "col": random.choice([PINK,CYAN,LIME,GOLD,PURP,TEAL,CORAL,OFFWH]),
                "size": random.randint(12, 26),
                "spd": random.uniform(18, 50),
                "phase": random.uniform(0, math.pi*2),
                "rot": random.uniform(0, 360),
                "rot_spd": random.uniform(-40, 40),
                "alpha": random.randint(140, 230),
            })

        # Two side penguins for the end screen
        self.peng_l = Penguin(SW//2 - 280, SH//2 + 80)
        self.peng_r = Penguin(SW//2 + 280, SH//2 + 80)
        self.peng_l.outfit = 2
        self.peng_r.outfit = 4
        if win:
            self.peng_l.react_happy()
            self.peng_r.react_happy()
        else:
            self.peng_l.react_sad()
            self.peng_r.react_sad()

        # Grade
        grade_idx = min(5, stars // 4)
        self.grade     = ["F","D","C","B","A","S"][grade_idx]
        self.grade_col = [RED,CORAL,ORNGE,GOLD,LIME,CYAN][grade_idx]

        # Pre-build panel gradient surfaces (cached)
        self._panel_surf = None

    def update(self, dt):
        self.t     += dt
        self.phase += dt
        for f in self.floaties:
            f["y"]   -= f["spd"] * dt
            f["rot"] += f["rot_spd"] * dt
            f["x"]   += math.sin(self.phase*0.8 + f["phase"]) * 18 * dt
            if f["y"] < -40:
                f["y"] = SH + 20
                f["x"] = random.uniform(40, SW-40)
        self.peng_l.update(dt)
        self.peng_r.update(dt)
        # Keep penguins reacting
        if self.win and self.t % 1.8 < dt*2:
            self.peng_l.react_happy(); self.peng_r.react_happy()
        elif not self.win and self.t % 2.2 < dt*2:
            self.peng_l.react_sad(); self.peng_r.react_sad()

    def _draw_floatie(self, surf, f):
        """Draw a floating decoration symbol."""
        cx, cy = int(f["x"]), int(f["y"])
        sz = f["size"]; col = f["col"]; a = f["alpha"]
        s = pygame.Surface((sz*4, sz*4), pygame.SRCALPHA)
        c2 = sz*2   # centre of surface
        sym = f["sym"]

        if sym == "star":
            for ang in range(0,360,72):
                r2 = math.radians(ang + f["rot"])
                pygame.draw.line(s,(*col,a),(c2,c2),
                    (c2+int(sz*1.7*math.cos(r2)), c2+int(sz*1.7*math.sin(r2))),max(1,sz//4))
            pygame.draw.circle(s,(*col,a),(c2,c2),sz//2)

        elif sym == "heart":
            # approximate heart with two circles + triangle
            r = sz//2
            pygame.draw.circle(s,(*col,a),(c2-r,c2-r//2),r)
            pygame.draw.circle(s,(*col,a),(c2+r,c2-r//2),r)
            pygame.draw.polygon(s,(*col,a),[
                (c2-sz,c2-r//2),(c2+sz,c2-r//2),(c2,c2+sz)])

        elif sym == "snowflake":
            for ang in range(0,360,60):
                r2 = math.radians(ang + f["rot"])
                ex = c2+int(sz*1.6*math.cos(r2)); ey = c2+int(sz*1.6*math.sin(r2))
                pygame.draw.line(s,(*col,a),(c2,c2),(ex,ey),max(1,sz//5))
                mx = c2+int(sz*0.8*math.cos(r2)); my = c2+int(sz*0.8*math.sin(r2))
                p2 = math.radians(ang+90+f["rot"])
                pygame.draw.line(s,(*col,a),
                    (mx-int(sz*0.4*math.cos(p2)),my-int(sz*0.4*math.sin(p2))),
                    (mx+int(sz*0.4*math.cos(p2)),my+int(sz*0.4*math.sin(p2))),max(1,sz//6))

        elif sym == "fish":
            pts = [(c2-sz,c2),(c2-sz//3,c2-sz//2),(c2+sz//2,c2-sz//3),
                   (c2+sz,c2),(c2+sz//2,c2+sz//3),(c2-sz//3,c2+sz//2)]
            pygame.draw.polygon(s,(*col,a),pts)
            pygame.draw.polygon(s,(*lc(col,WHITE,0.4),a),
                [(c2+sz//2,c2-sz//3),(c2+sz,c2-sz//2),(c2+sz,c2+sz//2),(c2+sz//2,c2+sz//3)])
            pygame.draw.circle(s,(*WHITE,a),(c2-sz//2,c2-sz//6),sz//6)

        elif sym == "note":
            pygame.draw.circle(s,(*col,a),(c2,c2+sz//2),sz//2)
            pygame.draw.rect(s,(*col,a),(c2+sz//2-sz//6,c2-sz,sz//5,sz+sz//2))
            pygame.draw.rect(s,(*col,a),(c2+sz//2-sz//6,c2-sz,sz//2,sz//5))

        elif sym == "drop":
            pts2=[(c2,c2-sz),(c2-sz//2,c2),(c2,c2+sz//2),(c2+sz//2,c2)]
            pygame.draw.polygon(s,(*col,a),pts2)

        elif sym == "zzz":
            for zi in range(3):
                zs = sz//2 + zi*sz//3
                zt = F_SM.render("z"*(zi+1), True, (*col, a))
                s.blit(zt,(c2-zt.get_width()//2+zi*4, c2-zs))

        surf.blit(s,(cx-c2, cy-c2))

    def draw(self, surf):
        ease = min(1.0, self.t * 2.8)   # fade-in
        ea   = int(ease * 255)

        # ── Full-screen dim overlay ──────────────────────────
        ov = pygame.Surface((SW,SH), pygame.SRCALPHA)
        ov.fill((3,5,18,int(ea*0.88)))
        surf.blit(ov,(0,0))

        # ── Floating decorations ─────────────────────────────
        for f in self.floaties:
            self._draw_floatie(surf, f)

        # ── Outer glow ring ──────────────────────────────────
        glow_c = LIME if self.win else CORAL
        ring_r = int(lerp(320, 295, 0.5+0.5*math.sin(self.phase*1.8)))
        for gr in range(30, 0, -4):
            ga = int(28*(1-gr/30)**1.5 * ease)
            gs2 = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs2,(*glow_c,ga),(gr,gr),gr)
            surf.blit(gs2,(SW//2-gr, SH//2-gr-60))

        # ── Main card ────────────────────────────────────────
        cw, ch = 720, 420
        cx_card, cy_card = SW//2 - cw//2, SH//2 - ch//2 - 40

        # Gradient background
        top_c = (18,38,88) if self.win else (55,12,18)
        bot_c = (10,22,58) if self.win else (30,8,12)
        _draw_gradient_rect(surf,(cx_card,cy_card,cw,ch),top_c,bot_c,radius=32)

        # Glowing border
        border_s = pygame.Surface((cw,ch),pygame.SRCALPHA)
        border_c = lc(glow_c,WHITE, 0.3+0.2*abs(math.sin(self.phase*2)))
        pygame.draw.rect(border_s,(*border_c,200),(0,0,cw,ch),3,border_radius=32)
        surf.blit(border_s,(cx_card,cy_card))

        # Inner shimmer line at top
        sh_s = pygame.Surface((cw-20,3),pygame.SRCALPHA)
        for sx in range(cw-20):
            t2=sx/(cw-20); ca=int(80*math.sin(math.pi*t2)*ease)
            pygame.draw.line(sh_s,(*glow_c,ca),(sx,0),(sx,3))
        surf.blit(sh_s,(cx_card+10,cy_card+12))

        # ── Win/Lose HEADLINE ────────────────────────────────
        ccx = SW//2
        if self.win:
            # Rainbow cycling headline for win
            hue_shift = self.phase * 80
            h_cols = [
                (int(255*abs(math.sin(math.radians(hue_shift+i*45)))),
                 int(200*abs(math.cos(math.radians(hue_shift+i*45)))),
                 int(255*abs(math.sin(math.radians(hue_shift+i*45+90)))))
                for i in range(6)]
            headline_text = "YOU WIN!"
            # Draw each letter in a different colour
            chars = list(headline_text)
            total_w = sum(F_HERO.size(c)[0] for c in chars)
            lx = ccx - total_w//2
            bob_y = cy_card + 60 + int(math.sin(self.phase*2.2)*7)
            for ci, ch2 in enumerate(chars):
                ccol = h_cols[ci % len(h_cols)]
                _draw_outlined_text(surf, F_HERO, ch2, ccol, (10,10,40),
                                    lx + F_HERO.size(ch2)[0]//2, bob_y, outline=4)
                lx += F_HERO.size(ch2)[0]
        else:
            # Sad wobble for lose
            wobble = int(math.sin(self.phase*3)*4)
            _draw_outlined_text(surf, F_HERO, "GAME OVER", RED, (30,5,5),
                                ccx, cy_card+65+wobble, outline=4)

        # ── Personality sub-message ──────────────────────────
        pulse_a = 180+int(75*abs(math.sin(self.phase*1.5)))
        sub_col = lc(glow_c, WHITE, 0.6)
        sub_s = F_MED2.render(self.headline, True, sub_col)
        sub_s.set_alpha(int(ease*255))
        surf.blit(sub_s, sub_s.get_rect(centerx=ccx, top=cy_card+140))

        sub2_s = F_MD.render(self.subtitle, True, OFFWH)
        sub2_s.set_alpha(int(ease*190))
        surf.blit(sub2_s, sub2_s.get_rect(centerx=ccx, top=cy_card+178))

        # ── Stats row ────────────────────────────────────────
        stat_y = cy_card+222
        # Score box
        for (label, val, col2, bx2) in [
            ("SCORE", f"{self.score:,}", GOLD,  ccx-200),
            ("STARS", str(self.stars),   CYAN,  ccx),
            ("LEVEL", str(self.level),   glow_c, ccx+200),
        ]:
            box_s = pygame.Surface((130,55),pygame.SRCALPHA)
            pygame.draw.rect(box_s,(*col2,45),(0,0,130,55),border_radius=14)
            pygame.draw.rect(box_s,(*col2,140),(0,0,130,55),2,border_radius=14)
            surf.blit(box_s,(bx2-65,stat_y))
            v_s = F_LG.render(val, True, col2)
            surf.blit(v_s, v_s.get_rect(centerx=bx2, top=stat_y+4))
            l_s = F_XS.render(label, True, lc(col2,WHITE,0.5))
            surf.blit(l_s, l_s.get_rect(centerx=bx2, top=stat_y+38))

        # ── Grade badge ──────────────────────────────────────
        grade_y = cy_card+295
        grade_r = int(34 + 4*abs(math.sin(self.phase*2.5)))
        glow_dot(surf, self.grade_col, ccx, grade_y, grade_r)
        pygame.draw.circle(surf, lc(self.grade_col,(5,5,20),0.5), (ccx,grade_y), grade_r)
        _draw_outlined_text(surf, F_BIG, self.grade, self.grade_col, (5,5,20),
                            ccx, grade_y, outline=3)
        gl2 = F_SM.render("CHEF GRADE", True, lc(self.grade_col,WHITE,0.55))
        surf.blit(gl2, gl2.get_rect(centerx=ccx, top=grade_y+40))

        # ── Restart prompt (pulsing) ─────────────────────────
        restart_y = cy_card + ch - 38
        pulse2 = 0.6 + 0.4*abs(math.sin(self.phase*2.5))
        r_col = lc(glow_c, WHITE, pulse2)
        r_text = "  Press  R  to help pingu waddle Again!  " if self.win else "  Press  R  to Try Again!  "
        r_s = F_MD.render(r_text, True, r_col)
        r_s.set_alpha(int(ease*230))
        surf.blit(r_s, r_s.get_rect(centerx=ccx, centery=restart_y))

        # ── ESC hint ────────────────────────────────────────
        esc_s = F_XS.render("ESC = quit", True, (60,80,130))
        surf.blit(esc_s, esc_s.get_rect(centerx=ccx, top=cy_card+ch+8))

        # ── Side penguins ────────────────────────────────────
        self.peng_l.draw(surf)
        self.peng_r.draw(surf)

        # ── Corner fish decorations ─────────────────────────
        for i, (fx, fy, flip) in enumerate([(55,55,False),(SW-55,55,True),
                                             (55,SH-55,False),(SW-55,SH-55,True)]):
            fish_s = pygame.Surface((48,28),pygame.SRCALPHA)
            col3 = [CYAN,PINK,GOLD,LIME][i]
            pts3 = [(2,14),(10,5),(38,9),(46,14),(38,19),(10,23)]
            pygame.draw.polygon(fish_s,(*col3,int(180*ease)),pts3)
            pygame.draw.polygon(fish_s,(*col3,int(180*ease)),
                [(38,9),(46,5),(46,23),(38,19)]) # tail
            pygame.draw.circle(fish_s,(*WHITE,int(200*ease)),(14,10),3)
            if flip:
                fish_s=pygame.transform.flip(fish_s,True,False)
            bob2 = int(math.sin(self.phase*1.8+i)*6)
            surf.blit(fish_s,(fx-24,fy-14+bob2))


# ══════════════════════════════════════════════════════════════
#  GAME
# ══════════════════════════════════════════════════════════════
class Game:
    MAX_ORDERS=4; MAX_FAILS=5

    # Per-level config: (duration_sec, score_target, label)
    LEVEL_CONFIG = [
        (60,  80,  "Apprentice Chef 🐣"),
        (70,  180, "Sous Chef 🐧"),
        (75,  320, "Head Chef 🎩"),
        (80,  500, "Master Chef ⭐"),
        (90,  750, "Legendary Pingu 👑"),
    ]

    # Layout constants (designed for 1280×780)
    LEFT_W    = 200          # ingredient panel width
    LEFT_X    = 8
    TOP_BAR_H = 50
    HUD_W     = 240
    HUD_H     = 210          # slightly taller for level progress bar
    HUD_MARG  = 10          # right margin for HUD
    ORDER_Y   = TOP_BAR_H+8
    BOWL_CX   = 620          # bowl centre x
    BOWL_CY   = 640          # bowl centre y
    BOWL_W    = 310
    BOWL_H    = 130

    def __init__(self):
        self.aurora    = Aurora()
        self.stars_bg  = Stars(60)
        self.snows     = [Snowflake() for _ in range(28)]
        self.penguin   = Penguin(SW-115, SH-185)
        self.particles = []; self.floats=[]; self.drops=[]
        self.end_screen = None
        self.level_complete = False
        self.level_screen_t = 0.0
        self.GAME_DUR = self.LEVEL_CONFIG[0][0]
        self.level_score_start = 0
        self._build_buttons()
        self.reset()

    def _build_buttons(self):
        self.buttons=[]
        bw = self.LEFT_W - 16
        for i,ing in enumerate(INGREDIENTS):
            self.buttons.append(IngBtn(ing, self.LEFT_X+8,
                                       self.TOP_BAR_H+50+i*52, bw))

    def reset(self):
        self.score=0; self.stars_earned=0; self.orders=[]; self.bowl=[]
        self.next_order_t=2.5; self.game_t=0.0
        self.game_over=False; self.win=False
        self.level=1; self.combo=0; self.combo_t=0
        self.failed_count=0
        self.particles=[]; self.floats=[]; self.drops=[]
        self.penguin.outfit=0
        self.end_screen = None
        self.level_complete = False
        self.level_screen_t = 0.0
        self.GAME_DUR = self.LEVEL_CONFIG[0][0]
        self.level_score_start = 0
        for _ in range(2): self.spawn_order()

    def unlocked(self):
        return {i["short"] for i in INGREDIENTS if i["unlock"]<=self.level}

    def speed(self): return 1.0+(self.level-1)*0.18

    def spawn_order(self):
        if len(self.orders)>=self.MAX_ORDERS: return
        ul=self.unlocked()
        avail=[r for r in RECIPES
               if r["unlock"]<=self.level and all(i in ul for i in r["ing"])]
        if avail:
            self.orders.append(OrderCard(random.choice(avail), self.speed()))

    def emit(self,cx,cy,color,n=12,rise=False,label=None):
        for i in range(min(n,14)):       # cap particles
            self.particles.append(Particle(cx,cy,color,
                                           label if i==n//2 else None,
                                           i%3==0, rise))

    def add_float(self,text,x,y,color,large=False):
        self.floats.append(FloatText(text,x,y,color,large))

    def try_serve(self):
        if not self.bowl: return
        bcx,bcy=self.BOWL_CX,self.BOWL_CY
        for o in self.orders:
            if o.done or o.failed: continue
            if self.bowl==o.recipe["ing"]:
                o.done=True; st=o.recipe["stars"]
                spd=clamp(o.remain/o.total,0,1)
                pts=int(st*20*(0.5+spd))
                if self.combo>=2: pts=int(pts*(1+self.combo*0.25))
                self.score+=pts; self.stars_earned+=st
                self.combo+=1; self.combo_t=2.2
                c=[GOLD,LIME,CYAN,PINK,PURP][self.combo%5]
                self.emit(bcx,bcy,c,14,rise=True)
                self.add_float(f"+{pts}",bcx,bcy-50,GOLD,large=True)
                if self.combo>1:
                    self.add_float(f"x{self.combo} COMBO!",bcx,bcy-90,c,True)
                    sfx("combo")
                else: sfx("ok")
                self.penguin.react_happy(); self.bowl=[]
                # Level up check (score target for this level)
                ol=self.level
                _, score_target, _ = self.LEVEL_CONFIG[self.level-1]
                level_score = self.score - self.level_score_start
                if level_score >= score_target and self.level < 5:
                    self.level_complete = True
                    self.level_screen_t = 3.5
                    sfx("lvl")
                    self.add_float(f"LEVEL {self.level} CLEAR!", self.BOWL_CX, bcy-130, LIME, True)
                    self.penguin.react_happy()
                elif self.level==5 and level_score >= score_target:
                    # Beat all 5 levels!
                    self.game_over=True; self.win=True; self.penguin.react_happy()
                else:
                    # Outfit changes with level
                    self.penguin.outfit = self.level - 1
                return
        # wrong
        self.combo=0
        self.emit(bcx,bcy,RED,8)
        self.add_float("WRONG!",bcx,bcy,RED)
        sfx("wrong"); self.penguin.react_sad(); self.bowl=[]

    def handle_click(self,pos):
        if self.game_over: return
        if self.level_complete: return
        for btn in self.buttons:
            if btn.is_clicked(pos):
                if len(self.bowl)<6:
                    self.bowl.append(btn.ing["short"])
                    btn.press()
                    icon=ICONS.get(btn.ing["short"])
                    if icon:
                        self.drops.append(DropAnim(icon,
                            (btn.rect.centerx,btn.rect.centery),
                            (self.BOWL_CX,self.BOWL_CY)))
                    self.emit(self.BOWL_CX,self.BOWL_CY,btn.ing["color"],5)
                    sfx("pop")
                return
        # Serve
        sv=self._serve_rect()
        cl=self._clear_rect()
        if sv.collidepoint(pos): self.try_serve()
        elif cl.collidepoint(pos):
            if self.bowl: self.bowl.pop(); sfx("click")

    def _serve_rect(self):
        return pygame.Rect(self.BOWL_CX-95,self.BOWL_CY+88,190,46)
    def _clear_rect(self):
        return pygame.Rect(self.BOWL_CX-95-58,self.BOWL_CY+88,50,46)

    def update(self,dt):
        # Always update end screen if active
        if self.game_over:
            if self.end_screen is None:
                self.end_screen = EndScreen(
                    self.win, self.score, self.stars_earned, self.level)
            self.end_screen.update(dt)
            # Keep background alive too
            self.aurora.update(dt); self.stars_bg.update(dt)
            for sn in self.snows: sn.update(dt)
            return

        # Level complete transition screen
        if self.level_complete:
            self.level_screen_t -= dt
            self.aurora.update(dt); self.stars_bg.update(dt)
            for sn in self.snows: sn.update(dt)
            self.penguin.update(dt)
            for p in self.particles: p.update(dt)
            self.particles=[p for p in self.particles if p.life>0]
            for f in self.floats: f.update(dt)
            self.floats=[f for f in self.floats if f.life>0]
            if self.level_screen_t <= 0:
                # Advance to next level
                self.level += 1
                self.penguin.outfit = self.level - 1
                self.level_score_start = self.score
                self.game_t = 0.0
                self.GAME_DUR = self.LEVEL_CONFIG[self.level-1][0]
                self.failed_count = 0
                self.orders = []; self.bowl = []
                self.next_order_t = 1.5
                self.level_complete = False
                for _ in range(2): self.spawn_order()
            return

        self.game_t+=dt
        if self.game_t>=self.GAME_DUR:
            # Time ran out — check if score target was met
            _, score_target, _ = self.LEVEL_CONFIG[self.level-1]
            level_score = self.score - self.level_score_start
            if level_score < score_target:
                self.game_over=True; self.win=False; self.penguin.react_sad()
            else:
                if self.level < 5:
                    self.level_complete = True
                    self.level_screen_t = 3.5
                    sfx("lvl"); self.penguin.react_happy()
                    self.add_float(f"LEVEL {self.level} CLEAR!", self.BOWL_CX, self.BOWL_CY-130, LIME, True)
                else:
                    self.game_over=True; self.win=True; self.penguin.react_happy()
            return

        self.aurora.update(dt); self.stars_bg.update(dt)
        for sn in self.snows: sn.update(dt)
        self.penguin.update(dt)

        # Handle expired orders
        expired=[o for o in self.orders if o.failed and not o.done]
        for o in expired:
            self.orders.remove(o)
            self.failed_count+=1; self.combo=0
            self.add_float("EXPIRED!",self.BOWL_CX,200,CORAL)
            self.penguin.react_sad()
        if self.failed_count>=self.MAX_FAILS:
            self.game_over=True; self.win=False; return

        for o in self.orders: o.update(dt)
        # Remove cards that finished their done animation
        self.orders=[o for o in self.orders
                     if not(o.done and o.slide>=1.0 and o.done_t<=0)]

        self.next_order_t-=dt
        if self.next_order_t<=0 and len(self.orders)<self.MAX_ORDERS:
            self.next_order_t=random.uniform(5,10)/self.speed()
            self.spawn_order()

        if self.combo_t>0: self.combo_t-=dt

        mp=pygame.mouse.get_pos(); ul=self.unlocked()
        for btn in self.buttons: btn.update(dt,mp,btn.ing["short"] in ul)

        self.particles=[p for p in self.particles if p.life>0]
        for p in self.particles: p.update(dt)
        self.floats=[f for f in self.floats if f.life>0]
        for f in self.floats: f.update(dt)
        self.drops=[d for d in self.drops if not d.done]
        for d in self.drops: d.update(dt)

    # ── DRAW ─────────────────────────────────────────────────
    def draw(self):
        # 1. Static background (pre-built, one blit)
        screen.blit(BG_SURF,(0,0))

        # 2. Stars + aurora
        self.stars_bg.draw(screen)
        self.aurora.draw(screen)

        # 3. Snowflakes (just circles now — super fast)
        for sn in self.snows: sn.draw(screen)

        # 4. Top bar
        self._draw_topbar()

        # 5. Orders
        self._draw_orders()

        # 6. Left panel
        self._draw_left_panel()

        # 7. Bowl
        self._draw_bowl()

        # 8. Penguin
        self.penguin.draw(screen)

        # 9. HUD
        self._draw_hud()

        # 10. Particles & float texts
        for p in self.particles: p.draw(screen)
        for f in self.floats:    f.draw(screen)
        for d in self.drops:     d.draw(screen)

        # 11. Bottom hint
        hb=pygame.Surface((SW,24),pygame.SRCALPHA)
        hb.fill((6,10,28,165)); screen.blit(hb,(0,SH-24))
        ht=F_XS.render(
            "Click ingredients in order  →  SERVE to match  │  R=restart  ESC=quit  │  Hit score target to advance levels!",
            True,(62,100,160))
        screen.blit(ht,ht.get_rect(centerx=SW//2,centery=SH-12))

        # 12. Game over overlay (last)
        if self.game_over: self._draw_gameover()

        # 13. Level complete overlay
        if self.level_complete: self._draw_level_complete()

    def _draw_topbar(self):
        draw_glass(screen,0,0,SW,self.TOP_BAR_H,r=0,alpha=195)
        # shimmer line
        for x in range(0,SW,3):
            t=x/SW; c=lc(CYAN,PINK,t); a=int(170*math.sin(math.pi*t))
            pygame.draw.line(screen,(*c,a),(x,self.TOP_BAR_H-1),(x,self.TOP_BAR_H))
        tt=F_TITLE.render("Pingu’s Cozy Kitchen",True,WHITE)
        screen.blit(tt,tt.get_rect(centerx=SW//2,centery=self.TOP_BAR_H//2))

    def _draw_left_panel(self):
        ph=len(INGREDIENTS)*52+60
        draw_glass(screen,self.LEFT_X,self.TOP_BAR_H+4,
                   self.LEFT_W,ph,r=16,alpha=178,border=CYAN,glow=CYAN)
        lbl=F_SM.render("INGREDIENTS",True,CYAN)
        screen.blit(lbl,lbl.get_rect(centerx=self.LEFT_X+self.LEFT_W//2,
                                      top=self.TOP_BAR_H+8))
        ul_lbl=F_XS.render(f"Level {self.level}  —  unlock more!",True,(72,120,175))
        screen.blit(ul_lbl,ul_lbl.get_rect(centerx=self.LEFT_X+self.LEFT_W//2,
                                             top=self.TOP_BAR_H+26))
        for btn in self.buttons: btn.draw(screen)

    def _draw_orders(self):
        lbl=F_SM.render("INCOMING ORDERS",True,GOLD)
        screen.blit(lbl,lbl.get_rect(x=self.LEFT_X+self.LEFT_W+10,y=self.TOP_BAR_H+4))

        active=self.orders[:self.MAX_ORDERS]
        if not active: return
        # Dynamic spacing: fill gap between left panel and HUD panel
        hud_left = SW - self.HUD_W - self.HUD_MARG
        area_left = self.LEFT_X + self.LEFT_W + 8
        area_w    = hud_left - area_left - 8
        cw        = OrderCard.W
        n         = len(active)
        total_cw  = n * cw
        gap       = max(8, (area_w - total_cw) // (n+1))
        for i,o in enumerate(active):
            ox = area_left + gap + i*(cw+gap)
            o.draw(screen, ox, self.ORDER_Y+18)

    def _draw_bowl(self):
        bcx,bcy=self.BOWL_CX,self.BOWL_CY
        bw,bh=self.BOWL_W,self.BOWL_H
        bc=TEAL if self.bowl else (28,58,98)
        # Glow
        gs=pygame.Surface((bw+30,bh+30),pygame.SRCALPHA)
        pygame.draw.ellipse(gs,(*bc,28),(0,0,bw+30,bh+30))
        screen.blit(gs,(bcx-bw//2-15,bcy-bh//2-15))
        draw_glass(screen,bcx-bw//2,bcy-bh//2,bw,bh,r=28,alpha=210,border=bc)
        bl=F_SM.render("YOUR MIXING BOWL",True,bc)
        screen.blit(bl,bl.get_rect(centerx=bcx,top=bcy-bh//2+8))

        if not self.bowl:
            ph=F_XS.render("← click ingredients",True,(45,75,125))
            screen.blit(ph,ph.get_rect(center=(bcx,bcy+10)))
        else:
            n=len(self.bowl); sp=min((bw-24)//n,50)
            sx=bcx-sp*(n-1)//2
            for i,short in enumerate(self.bowl):
                ing=IMAP[short]; ix=sx+i*sp; iy=bcy+10
                glow_dot(screen,ing["color"],ix,iy,18)
                icon=ICONS.get(short)
                if icon: screen.blit(icon,icon.get_rect(center=(ix,iy)))
                nm=F_XS.render(ing["name"],True,lc(ing["color"],WHITE,0.65))
                screen.blit(nm,nm.get_rect(centerx=ix,top=iy+20))

        for d in self.drops: d.draw(screen)

        # Buttons
        sv=self._serve_rect(); cl=self._clear_rect()
        mp=pygame.mouse.get_pos()
        draw_btn(screen,sv.x,sv.y,sv.w,sv.h,LIME,"SERVE ▲",F_MD,
                 active=bool(self.bowl),hover=sv.collidepoint(mp))
        draw_btn(screen,cl.x,cl.y,cl.w,cl.h,CORAL,"✕",F_MD,
                 active=bool(self.bowl),hover=cl.collidepoint(mp))

    def _draw_hud(self):
        # Anchored to right edge
        hx = SW - self.HUD_W - self.HUD_MARG
        hy = self.TOP_BAR_H + 4
        hw,hh = self.HUD_W, self.HUD_H
        draw_glass(screen,hx,hy,hw,hh,r=16,alpha=188,border=PURP,glow=PURP)

        # Score
        sc=F_LG.render(f"{self.score:,}",True,GOLD)
        screen.blit(sc,sc.get_rect(centerx=hx+hw//2,top=hy+8))
        sl=F_XS.render("SCORE",True,GOLD)
        screen.blit(sl,sl.get_rect(centerx=hx+hw//2,top=hy+40))

        # Divider
        dv=pygame.Surface((hw-28,1),pygame.SRCALPHA)
        dv.fill((*PURP,85)); screen.blit(dv,(hx+14,hy+55))

        # Stars
        stt=F_XS.render(f"Stars  {self.stars_earned}",True,GOLD)
        screen.blit(stt,(hx+12,hy+62))

        # Level badge
        lc2=[CYAN,LIME,GOLD,PINK,PURP][self.level-1]
        lb=pygame.Surface((68,22),pygame.SRCALPHA)
        pygame.draw.rect(lb,(*lc2,188),(0,0,68,22),border_radius=8)
        screen.blit(lb,(hx+hw-80,hy+60))
        lt=F_XS.render(f"LV {self.level}",True,(10,10,30))
        screen.blit(lt,lt.get_rect(center=(hx+hw-46,hy+71)))

        # Fails
        fc=RED if self.failed_count>=3 else OFFWH
        ft=F_XS.render(f"Fails  {'■'*self.failed_count}{'□'*(self.MAX_FAILS-self.failed_count)}",True,fc)
        screen.blit(ft,(hx+12,hy+88))

        # Combo
        if self.combo>=2 and self.combo_t>0:
            cc=[GOLD,PINK,CYAN,LIME][self.combo%4]
            ct=F_SM.render(f" x{self.combo} COMBO!",True,cc)
            screen.blit(ct,ct.get_rect(centerx=hx+hw//2,top=hy+112))

        # Level score progress bar
        _, score_target, _ = self.LEVEL_CONFIG[self.level-1]
        level_score = self.score - self.level_score_start
        ratio_score = min(1.0, level_score / max(1, score_target))
        pw, ph2 = hw-20, 12; px, py2 = hx+10, hy+136
        pygame.draw.rect(screen,(14,22,52),(px,py2,pw,ph2),border_radius=6)
        if ratio_score>0:
            col_prog = lc(CORAL, LIME, ratio_score)
            pygame.draw.rect(screen, col_prog, (px, py2, int(pw*ratio_score), ph2), border_radius=6)
        pygame.draw.rect(screen,(*lc2,100),(px,py2,pw,ph2),1,border_radius=6)
        pg_lbl = F_XS.render(f"Lvl goal  {level_score}/{score_target}", True, lc(lc2,WHITE,0.5))
        screen.blit(pg_lbl, pg_lbl.get_rect(centerx=hx+hw//2, top=py2+14))

        # Timer bar (fast — single rect)
        remaining=max(0,self.GAME_DUR-self.game_t); ratio=remaining/self.GAME_DUR
        tw,th=hw-20,16; tx,ty=hx+10,hy+hh-28
        pygame.draw.rect(screen,(14,22,52),(tx,ty,tw,th),border_radius=8)
        fill=int(tw*ratio)
        if fill>0:
            pygame.draw.rect(screen,lc(RED,LIME,ratio),(tx,ty,fill,th),border_radius=8)
        pygame.draw.rect(screen,(*PURP,100),(tx,ty,tw,th),1,border_radius=8)
        tl=F_XS.render(f"{int(remaining)}s",True,WHITE)
        screen.blit(tl,tl.get_rect(centerx=tx+tw//2,centery=ty+th//2))

    def _draw_gameover(self):
        if self.end_screen:
            self.end_screen.draw(screen)

    def _draw_level_complete(self):
        """Animated between-level interstitial."""
        t = max(0, 3.5 - self.level_screen_t)
        ease = min(1.0, t * 3.0)
        _, _, label = self.LEVEL_CONFIG[self.level-1]
        next_lv = self.level + 1 if self.level < 5 else 5

        # Dim overlay
        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((3, 8, 28, int(ease * 210)))
        screen.blit(ov, (0, 0))

        # Card
        cw, ch = 640, 320
        cx = SW//2 - cw//2; cy = SH//2 - ch//2
        _draw_gradient_rect(screen, (cx, cy, cw, ch), (18,55,22), (8,28,12), radius=28)
        border_s = pygame.Surface((cw,ch),pygame.SRCALPHA)
        pulse = 0.5+0.5*abs(math.sin(t*3))
        bc = lc(LIME, CYAN, pulse)
        pygame.draw.rect(border_s,(*bc,200),(0,0,cw,ch),3,border_radius=28)
        screen.blit(border_s,(cx,cy))

        # Text
        _draw_outlined_text(screen, F_HERO, f"LEVEL {self.level} CLEAR!", LIME, (5,20,5), SW//2, cy+72, outline=4)
        sub = F_LG.render(label, True, GOLD)
        screen.blit(sub, sub.get_rect(centerx=SW//2, top=cy+145))

        # Score earned this level
        _, score_target, _ = self.LEVEL_CONFIG[self.level-1]
        level_score = self.score - self.level_score_start
        sc_s = F_MD.render(f"Score this level: {level_score}  /  target {score_target}", True, OFFWH)
        screen.blit(sc_s, sc_s.get_rect(centerx=SW//2, top=cy+188))

        # Next level hint
        if next_lv <= 5:
            _, nt, nl = self.LEVEL_CONFIG[next_lv-1]
            nl_s = F_SM.render(f"▶  Next: Level {next_lv} — {nl}  (target: {nt} pts)", True, CYAN)
            screen.blit(nl_s, nl_s.get_rect(centerx=SW//2, top=cy+228))

        # Countdown bar
        ratio = max(0, self.level_screen_t / 3.5)
        bw=400; bh=10; bx=SW//2-bw//2; by=cy+ch-28
        pygame.draw.rect(screen,(14,35,18),(bx,by,bw,bh),border_radius=5)
        if ratio>0:
            pygame.draw.rect(screen,LIME,(bx,by,int(bw*ratio),bh),border_radius=5)
        pygame.draw.rect(screen,(*LIME,80),(bx,by,bw,bh),1,border_radius=5)

# ── MAIN LOOP ─────────────────────────────────────────────────
def main():
    print(f"Pingu’s Cozy Kitchen— {SW}×{SH} windowed (safe mode)")
    print("Controls: Mouse | R=restart | ESC=quit")
    game = Game()
    while True:
        dt = min(clock.tick(FPS)/1000.0, 0.05)   # cap dt — prevents spiral of death

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()        # ESC ALWAYS WORKS
                elif event.key == pygame.K_r:
                    game.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                game.handle_click(event.pos)
            elif event.type == pygame.VIDEORESIZE:
                pass  # handled by RESIZABLE flag automatically

        game.update(dt)
        game.draw()
        pygame.display.flip()

if __name__ == "__main__":
    main()
