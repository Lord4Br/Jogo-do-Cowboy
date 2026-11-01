#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEAD MAN'S DRAW  ·  estrelando ZÉ CAIXÃO
Duelo de faroeste em pixel art.  Python 3 + Pygame.

Controles:
  ESPAÇO / ENTER / CLIQUE ..... sacar e atirar  (clique no corpo do inimigo para mirar)
  A / D ....................... desviar na câmera lenta quando a arma falha
  SETAS / W S A D ............. navegar nos menus
  ESC ......................... voltar      M ... som liga/desliga      F11 ... tela cheia
"""
import os, sys, math, random, json

import pygame

W, H = 480, 270
GY = 226
SPW, SPH = 84, 100
AX, FY, T0, TB, HZ = 26, 99, 38, 63, 168
HERE = os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, 'frozen', False) else __file__))
ASSET = os.path.join(getattr(sys, '_MEIPASS', HERE), 'assets')
SAVEF = os.path.join(HERE, 'save.json')
RND = random.random
def pick(a): return a[int(RND() * len(a))]
def lerp(a, b, k): return a + (b - a) * k
def ease(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

# ------------------------------------------------------------------ cores
_CC = {}
def C(h):
    if isinstance(h, tuple): return h if len(h) == 4 else h + (255,)
    c = _CC.get(h)
    if c is None:
        s = h.lstrip('#'); c = (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255); _CC[h] = c
    return c
def shade(h, f):
    r, g, b, _ = C(h)
    if f > 1: r, g, b = r + (255 - r) * (f - 1) * .9, g + (255 - g) * (f - 1) * .9, b + (255 - b) * (f - 1) * .9
    else: r, g, b = r * f, g * f, b * f
    cl = lambda v: max(0, min(255, int(round(v))))
    return '#%02x%02x%02x' % (cl(r), cl(g), cl(b))
def ramp(h): return [shade(h, .5), shade(h, .74), h, shade(h, 1.2), shade(h, 1.42)]
def S(w, h): return pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)
def tob(s): return bytearray((pygame.image.tobytes if hasattr(pygame.image, 'tobytes') else pygame.image.tostring)(s, 'RGBA'))
def fromb(b, size):
    s = (pygame.image.frombytes if hasattr(pygame.image, 'frombytes') else pygame.image.fromstring)(bytes(b), size, 'RGBA')
    try: return s.convert_alpha()
    except Exception: return s

class Pt:
    """pintor de pixels com deslocamento"""
    def __init__(self, s): self.s = s; self.ox = 0; self.oy = 0
    def R(self, x, y, w, h, c):
        if not c: return
        x0 = int(math.floor(x + self.ox + .5)); y0 = int(math.floor(y + self.oy + .5)); w = int(math.floor(w + .5)); h = int(math.floor(h + .5))
        if w > 0 and h > 0: self.s.fill(C(c), (x0, y0, w, h))
    def P(self, x, y, c): self.R(x, y, 1, 1, c)
    def EL(self, cx, cy, rx, ry, c):
        for yy in range(-ry, ry + 1):
            w = int(round(rx * math.sqrt(max(0, 1 - (yy * yy) / (ry * ry + 1e-9)))))
            self.R(cx - w, cy + yy, w * 2 + 1, 1, c)
    def TL(self, x0, y0, x1, y1, th, c):
        n = max(abs(x1 - x0), abs(y1 - y0)) or 1
        for i in range(int(n) + 1): self.R(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, th, th, c)
def line(dst, x0, y0, x1, y1, col):
    c = C(col); x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, sx = abs(x1 - x0), (1 if x0 < x1 else -1); dy, sy = -abs(y1 - y0), (1 if y0 < y1 else -1); e = dx + dy
    for _ in range(3000):
        dst.fill(c, (x0, y0, 1, 1))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * e
        if e2 >= dy: e += dy; x0 += sx
        if e2 <= dx: e += dx; y0 += sy
_AC = {}
def arect(dst, col, x, y, w, h, a):
    """retângulo semitransparente"""
    w, h = int(w), int(h)
    if w <= 0 or h <= 0 or a <= 0: return
    a = max(0, min(255, int(a) // 8 * 8))
    k = (col, w, h, a)
    s = _AC.get(k)
    if s is None:
        if len(_AC) > 4000: _AC.clear()
        r, g, b, _ = C(col); s = S(w, h); s.fill((r, g, b, a)); _AC[k] = s
    dst.blit(s, (int(x), int(y)))

# ------------------------------------------------------------------ fonte 5x7
FONT = {}
for _l in """A 01110,10001,10001,11111,10001,10001,10001
B 11110,10001,10001,11110,10001,10001,11110
C 01110,10001,10000,10000,10000,10001,01110
D 11110,10001,10001,10001,10001,10001,11110
E 11111,10000,10000,11110,10000,10000,11111
F 11111,10000,10000,11110,10000,10000,10000
G 01110,10001,10000,10111,10001,10001,01111
H 10001,10001,10001,11111,10001,10001,10001
I 01110,00100,00100,00100,00100,00100,01110
J 00111,00010,00010,00010,00010,10010,01100
K 10001,10010,10100,11000,10100,10010,10001
L 10000,10000,10000,10000,10000,10000,11111
M 10001,11011,10101,10101,10001,10001,10001
N 10001,11001,10101,10011,10001,10001,10001
O 01110,10001,10001,10001,10001,10001,01110
P 11110,10001,10001,11110,10000,10000,10000
Q 01110,10001,10001,10001,10101,10010,01101
R 11110,10001,10001,11110,10100,10010,10001
S 01111,10000,10000,01110,00001,00001,11110
T 11111,00100,00100,00100,00100,00100,00100
U 10001,10001,10001,10001,10001,10001,01110
V 10001,10001,10001,10001,10001,01010,00100
W 10001,10001,10001,10101,10101,10101,01010
X 10001,10001,01010,00100,01010,10001,10001
Y 10001,10001,01010,00100,00100,00100,00100
Z 11111,00001,00010,00100,01000,10000,11111
0 01110,10001,10011,10101,11001,10001,01110
1 00100,01100,00100,00100,00100,00100,01110
2 01110,10001,00001,00010,00100,01000,11111
3 11110,00001,00001,01110,00001,00001,11110
4 00010,00110,01010,10010,11111,00010,00010
5 11111,10000,11110,00001,00001,10001,01110
6 00110,01000,10000,11110,10001,10001,01110
7 11111,00001,00010,00100,01000,01000,01000
8 01110,10001,10001,01110,10001,10001,01110
9 01110,10001,10001,01111,00001,00010,01100
! 00100,00100,00100,00100,00100,00000,00100
. 00000,00000,00000,00000,00000,01100,01100
: 00000,01100,01100,00000,01100,01100,00000
' 00100,00100,01000,00000,00000,00000,00000
- 00000,00000,00000,11111,00000,00000,00000
? 01110,10001,00001,00010,00100,00000,00100
/ 00001,00010,00010,00100,01000,01000,10000
$ 00100,01111,10100,01110,00101,11110,00100
+ 00000,00100,00100,11111,00100,00100,00000
, 00000,00000,00000,00000,01100,00100,01000
( 00010,00100,01000,01000,01000,00100,00010
) 01000,00100,00010,00010,00010,00100,01000
< 00010,00100,01000,10000,01000,00100,00010
> 01000,00100,00010,00001,00010,00100,01000
% 11001,11010,00010,00100,01000,01011,10011
= 00000,00000,11111,00000,11111,00000,00000
[ 01110,01000,01000,01000,01000,01000,01110
] 01110,00010,00010,00010,00010,00010,01110
" 01010,01010,00000,00000,00000,00000,00000
¡ 00100,00000,00100,00100,00100,00100,00100
¿ 00100,00000,00100,01000,10000,10001,01110
· 00000,00000,00000,01100,01100,00000,00000""".split('\n'):
    FONT[_l[0]] = _l[2:].split(',')
ACC = {'Ã': ('A', 'til'), 'Á': ('A', 'ac'), 'Â': ('A', 'cir'), 'À': ('A', 'gr'), 'É': ('E', 'ac'), 'Ê': ('E', 'cir'), 'Í': ('I', 'ac'),
       'Ó': ('O', 'ac'), 'Ô': ('O', 'cir'), 'Õ': ('O', 'til'), 'Ú': ('U', 'ac'), 'Ç': ('C', 'ced'), 'Ñ': ('N', 'til')}
ACCG = {'til': ['01101', '10110'], 'ac': ['00010', '00100'], 'cir': ['00100', '01010'], 'gr': ['01000', '00100'], 'ced': ['00100', '01000']}
def raw(dst, s, X, Y, sc, col):
    c = C(col); cx = X
    for c0 in s:
        ch, acc = ACC.get(c0, (c0, None))
        g = FONT.get(ch)
        if g:
            for r in range(7):
                row = g[r]
                for k in range(5):
                    if row[k] == '1': dst.fill(c, (cx + k * sc, Y + r * sc, sc, sc))
        if acc:
            a = ACCG[acc]; r0 = 7 if acc == 'ced' else -3
            for r in range(2):
                for k in range(5):
                    if a[r][k] == '1': dst.fill(c, (cx + k * sc, Y + (r0 + r) * sc, sc, sc))
        cx += 6 * sc
_TC = {}
def text_surf(s, sc, col, out, ot, sh, ext):
    key = (s, sc, col, out, ot, sh, ext)
    e = _TC.get(key)
    if e: return e
    ot_ = ot if out else 0; ext_ = ext if sh else 0
    tw = max(1, len(s) * 6 * sc - sc); th = 7 * sc
    pad = ot_ + ext_ + 1; padT = 3 * sc + ot_ + 1; padB = 2 * sc + ot_ + ext_ + 1
    surf = S(tw + pad * 2, th + padT + padB); ox, oy = pad, padT
    if out:
        for i in range(ext_ + 1):
            for dy in range(-ot_, ot_ + 1):
                for dx in range(-ot_, ot_ + 1):
                    if dx or dy: raw(surf, s, ox + i + dx, oy + i + dy, sc, out)
    for i in range(ext_, 0, -1): raw(surf, s, ox + i, oy + i, sc, sh)
    raw(surf, s, ox, oy, sc, col)
    e = (surf, ox, oy, tw)
    if len(_TC) > 900: _TC.clear()
    _TC[key] = e
    return e
CREAM, BROWN, DARK, GOLD = '#f2e4c0', '#6a3418', '#1a0a06', '#ffd060'
def dtext(dst, s, x, y, sc=1, col=CREAM, out=DARK, ot=1, sh=None, ext=0, align='left', alpha=255):
    s = str(s).upper(); surf, ox, oy, tw = text_surf(s, sc, col, out, ot, sh, ext)
    if align == 'center': x -= tw // 2
    elif align == 'right': x -= tw
    if alpha < 255:
        surf.set_alpha(max(0, int(alpha))); dst.blit(surf, (int(x - ox), int(y - oy))); surf.set_alpha(255)
    else: dst.blit(surf, (int(x - ox), int(y - oy)))
    return tw

# ------------------------------------------------------------------ armas
WEAP = [
    dict(id='rust', name='REVÓLVER ENFERRUJADO', dmg=1, cad=.32, saque=0, ammo=6, price=0, ln=9, metal='#8a7a6c', grip='#6a4226', desc=['O VELHO COMPANHEIRO DO ZÉ.', 'NÃO FALHA... QUASE NUNCA.']),
    dict(id='peace', name='COLT PEACEMAKER', dmg=1, cad=.2, saque=-.025, ammo=6, price=300, ln=11, metal='#aab4c2', grip='#ecdcbc', desc=['SAQUE MAIS RÁPIDO E', 'CADÊNCIA ALTA.']),
    dict(id='dual', name='SCHOFIELD DUPLA', dmg=1, cad=.26, saque=-.01, ammo=12, price=700, ln=10, metal='#d4d8e0', grip='#5a3420', dual=True, desc=['DUAS ARMAS: DOIS TIROS', 'A CADA DISPARO.']),
    dict(id='sawed', name='ESPINGARDA SERRADA', dmg=3, cad=.6, saque=.03, ammo=2, price=1000, ln=15, metal='#50505a', grip='#8a5226', shotgun=True, desc=['LENTA PRA SACAR, MAS UM', 'TIRO DERRUBA QUASE TUDO.']),
    dict(id='widow', name='A VIÚVA NEGRA', dmg=2, cad=.15, saque=-.045, ammo=6, price=2000, ln=12, metal='#24242c', grip='#e0b040', gold=True, desc=['LENDÁRIA. DANO DOBRADO', 'E SAQUE RELÂMPAGO.'])]
WMAP = {w['id']: w for w in WEAP}
WMAP['bossdual'] = dict(id='bossdual', dmg=1, cad=.2, saque=0, ammo=12, ln=10, metal='#3e3e46', grip='#ecdcbc', dual=True)
WMAP['rifle'] = dict(id='rifle', dmg=1, cad=.2, saque=0, ammo=30, ln=0, metal='#2a2c28', grip='#4a5a2e', rifle=True)
WMAP['priest'] = dict(id='priest', dmg=3, cad=.6, saque=0, ammo=2, ln=15, metal='#50505a', grip='#8a5226', shotgun=True)

class Gun:
    def __init__(self, s, tip, anchor): self.s = s; self.tip = tip; self.anchor = anchor
_GUNC = {}
def gun_sprite(w):
    g = _GUNC.get(w['id'])
    if g: return g
    if w['id'] in GUN_EXT: g = GUN_EXT[w['id']](w)
    elif w.get('rifle'):
        s = S(38, 13); p = Pt(s); m = ramp(w['metal']); o = ramp(w['grip'])
        p.R(0, 3, 9, 4, o[1]); p.R(0, 3, 9, 1, o[2]); p.R(0, 6, 3, 2, m[0]); p.R(6, 4, 4, 2, m[1])
        p.R(9, 2, 13, 5, m[2]); p.R(9, 2, 13, 1, m[3]); p.R(11, 6, 3, 5, o[0]); p.R(17, 7, 4, 5, m[1]); p.R(18, 11, 3, 1, m[0])
        p.R(22, 2, 10, 4, o[2]); p.R(22, 2, 10, 1, o[3]); p.R(23, 5, 8, 1, o[1]); [p.P(x, 4, o[0]) for x in range(23, 31, 2)]
        p.R(32, 3, 5, 2, m[1]); p.R(36, 2, 2, 4, m[0]); p.R(13, 0, 6, 2, '#141416'); p.P(18, 0, '#e02020'); p.R(14, 1, 1, 1, '#3a3a40')
        g = Gun(s, (38, 3), (12, 5))
    elif w.get('shotgun'):
        s = S(26, 10); p = Pt(s); m = ramp(w['metal']); gp = ramp(w['grip']); L = w['ln']
        p.R(5, 1, L, 2, m[2]); p.R(5, 1, L, 1, m[3]); p.R(5, 3, L, 2, m[1]); p.R(5, 3, L, 1, m[0]); p.P(4 + L, 1, m[4])
        p.R(8, 5, 7, 2, gp[2]); p.R(8, 6, 7, 1, gp[1]); p.R(1, 2, 5, 3, gp[2]); p.R(1, 2, 5, 1, gp[3]); p.R(0, 4, 3, 4, gp[2]); p.R(0, 7, 3, 1, gp[0])
        p.P(4, 0, m[0]); p.P(5, 0, m[1]); p.P(6, 5, m[0]); p.P(7, 6, m[0])
        g = Gun(s, (5 + L, 2), (3, 2))
    else:
        s = S(26, 10); p = Pt(s); m = ramp(w['metal']); gp = ramp(w['grip']); L = w['ln']
        p.P(3, 0, m[0]); p.P(3, 1, m[1]); p.R(4, 1, 4, 4, m[2]); p.R(4, 1, 4, 1, m[3]); p.P(5, 3, m[0]); p.P(7, 3, m[0])
        if w.get('gold'): p.R(4, 1, 4, 4, '#d8a830'); p.R(4, 1, 4, 1, '#f8e080'); p.P(5, 3, '#7a5410'); p.P(7, 3, '#7a5410')
        p.R(8, 1, L - 3, 2, m[2]); p.R(8, 1, L - 3, 1, m[3]); p.R(9, 3, max(1, L - 6), 1, m[1]); p.P(4 + L, 0, m[4])
        p.P(6, 5, m[0]); p.P(7, 5, m[0]); p.P(6, 4, m[0])
        p.R(2, 4, 3, 4, gp[2]); p.R(2, 4, 1, 4, gp[3]); p.P(1, 7, gp[1]); p.P(4, 7, gp[1])
        g = Gun(s, (4 + L, 1), (3, 2))
    _GUNC[w['id']] = g
    return g

def rot_blit(dst, src, pivot, ang, at):
    """gira src (graus, anti-horário) em torno de pivot e cola com o pivot em 'at'. Retorna função que mapeia pontos."""
    r = pygame.transform.rotate(src, ang)
    sw, sh = src.get_size(); rw, rh = r.get_size()
    t = math.radians(ang); c, s_ = math.cos(t), math.sin(t)
    def mp(px, py):
        vx, vy = px - sw / 2, py - sh / 2
        return (vx * c + vy * s_, -vx * s_ + vy * c)
    pvx, pvy = mp(*pivot)
    cx, cy = at[0] - pvx, at[1] - pvy
    dst.blit(r, (int(round(cx - rw / 2)), int(round(cy - rh / 2))))
    def f(px, py):
        vx, vy = mp(px, py); return (cx + vx, cy + vy)
    return f

# ------------------------------------------------------------------ personagens
def draw_hat(p, h, hx, b):
    if h['type'] in HAT_EXT: return HAT_EXT[h['type']](p, h, hx, b)
    c = ramp(h['col']); bd = h.get('band', '#1a1210'); t = h['type']
    if t == 'cowboy':
        for y in range(b - 10, b):
            hw = 4 if y < b - 8 else 6
            p.R(hx - hw, y, 2 * hw + 1, 1, c[2]); p.P(hx - hw, y, c[1]); p.P(hx + hw, y, c[3])
        p.P(hx, b - 10, c[0]); p.P(hx - 1, b - 10, c[1]); p.P(hx + 1, b - 9, c[1]); p.R(hx + 3, b - 8, 1, 5, c[3])
        p.R(hx - 6, b - 3, 13, 2, bd); p.R(hx - 12, b, 25, 2, c[2]); p.R(hx - 11, b, 23, 1, c[3]); p.R(hx - 11, b + 1, 23, 1, c[0])
        p.P(hx - 13, b - 1, c[2]); p.P(hx + 13, b - 1, c[2]); p.P(hx - 13, b, c[1]); p.P(hx + 13, b, c[1])
    elif t == 'fedora':
        for y in range(b - 9, b):
            hw = 4 if y < b - 7 else 5
            p.R(hx - hw, y, 2 * hw + 1, 1, c[2]); p.P(hx - hw, y, c[1]); p.P(hx + hw, y, c[3])
        p.P(hx + 1, b - 9, c[1]); p.P(hx, b - 8, c[1]); p.R(hx + 3, b - 7, 1, 4, c[4])
        p.R(hx - 5, b - 3, 11, 2, bd); p.R(hx - 10, b, 22, 2, c[2]); p.R(hx - 9, b, 20, 1, c[3]); p.R(hx - 10, b + 1, 22, 1, c[1]); p.R(hx + 9, b + 2, 4, 1, c[1]); p.P(hx - 11, b - 1, c[2])
    elif t == 'wide':
        for y in range(b - 8, b): p.R(hx - 5, y, 11, 1, c[2]); p.P(hx - 5, y, c[1]); p.P(hx + 5, y, c[3])
        p.R(hx - 5, b - 8, 11, 1, c[3]); p.R(hx - 5, b - 3, 11, 2, bd); p.R(hx - 16, b, 33, 2, c[2]); p.R(hx - 15, b, 31, 1, c[3]); p.R(hx - 16, b + 1, 33, 1, c[0])
    elif t == 'sombrero':
        for y in range(b - 17, b - 1):
            hw = min(6, 2 + int(round((y - (b - 17)) * .32))); p.R(hx - hw, y, 2 * hw + 1, 1, c[2]); p.P(hx - hw, y, c[1]); p.P(hx + hw, y, c[3])
        p.R(hx - 6, b - 5, 13, 2, bd)
        for i in range(-5, 6, 2): p.P(hx + i, b - 5, '#f0d060')
        p.R(hx - 20, b - 1, 41, 2, c[2]); p.R(hx - 19, b - 1, 39, 1, c[3]); p.R(hx - 20, b + 1, 41, 1, c[0]); p.R(hx - 23, b - 4, 3, 4, c[2]); p.R(hx + 21, b - 4, 3, 4, c[2])
        p.P(hx - 23, b - 4, c[3]); p.P(hx + 23, b - 4, c[3])
        for i in range(-18, 19, 4): p.P(hx + i, b, bd)
    elif t == 'bowler':
        p.EL(hx, b - 4, 6, 5, c[2]); p.R(hx - 6, b - 4, 1, 4, c[1]); p.P(hx + 3, b - 7, c[4]); p.P(hx + 2, b - 8, c[3])
        p.R(hx - 6, b - 2, 13, 1, bd); p.R(hx - 8, b, 17, 2, c[2]); p.R(hx - 8, b + 1, 17, 1, c[0]); p.P(hx - 9, b - 1, c[2]); p.P(hx + 9, b - 1, c[2])
    elif t == 'top':
        p.R(hx - 6, b - 17, 13, 17, c[2]); p.R(hx - 6, b - 17, 2, 17, c[1]); p.R(hx + 4, b - 17, 1, 17, c[3]); p.R(hx - 6, b - 17, 13, 1, c[3])
        p.R(hx - 6, b - 5, 13, 3, bd); p.R(hx - 9, b, 19, 2, c[2]); p.R(hx - 9, b + 1, 19, 1, c[0]); p.R(hx - 8, b, 17, 1, c[3])
    elif t == 'peaked':  # quepe de oficial
        p.R(hx - 7, b - 8, 16, 3, c[2]); p.R(hx - 8, b - 7, 18, 2, c[2]); p.R(hx - 7, b - 8, 16, 1, c[3]); p.R(hx - 8, b - 6, 18, 1, c[1])
        p.R(hx - 6, b - 5, 13, 4, c[1]); p.R(hx - 6, b - 4, 13, 2, bd); p.R(hx - 6, b - 4, 13, 1, shade(bd, 1.3))
        p.R(hx + 1, b - 1, 10, 2, '#0a0a0e'); p.R(hx + 2, b - 1, 8, 1, '#3a3a44'); p.P(hx + 11, b, '#0a0a0e')
        p.R(hx + 3, b - 7, 3, 3, '#d8d0b8'); p.P(hx + 3, b - 6, '#141010'); p.P(hx + 5, b - 6, '#141010')
    elif t == 'cap':  # boné militar
        p.R(hx - 6, b - 7, 13, 7, c[2]); p.R(hx - 6, b - 7, 13, 1, c[3]); p.R(hx - 6, b - 7, 2, 7, c[1]); p.R(hx - 6, b - 1, 13, 1, c[1])
        p.R(hx + 2, b, 10, 2, c[1]); p.R(hx + 2, b + 1, 10, 1, c[0])
        p.R(hx + 2, b - 6, 4, 4, '#1e3a24'); p.P(hx + 3, b - 5, '#e0c040'); p.P(hx + 4, b - 4, '#e0c040'); p.P(hx + 4, b - 5, '#e8e8e0')

def draw_head(p, s, hx, top, bn, sk, nohat):
    DK = '#140a0c'; kind = s.get('head', 'skull' if s['kind'] == 'skel' else 'face')
    if kind in ('skull', 'scream', 'gasmask'):
        p.EL(hx, top + 6, 6, 6, bn[1]); p.EL(hx + 1, top + 6, 5, 6, bn[2]); p.R(hx + 1, top + 1, 3, 1, bn[3]); p.P(hx + 4, top + 2, bn[4])
        jaw = 3 if kind == 'scream' else 0
        p.R(hx - 3, top + 11, 9, 4 + jaw, bn[2]); p.R(hx - 3, top + 11, 1, 4 + jaw, bn[1]); p.R(hx - 2, top + 15 + jaw, 7, 1, bn[1])
        p.R(hx - 3, top + 5, 3, 3, DK); p.R(hx + 2, top + 5, 3, 3, DK); e = s.get('eye', '#ff3a2a'); p.P(hx - 2, top + 6, e); p.P(hx + 3, top + 6, e)
        if s.get('eyeGlow'): p.P(hx - 2, top + 5, s['eyeGlow']); p.P(hx + 3, top + 5, s['eyeGlow'])
        p.P(hx + 1, top + 9, DK); p.P(hx + 2, top + 9, DK); p.P(hx + 2, top + 10, DK); p.P(hx - 5, top + 9, bn[1]); p.P(hx + 6, top + 9, bn[1]); p.P(hx - 4, top + 3, bn[1])
        p.R(hx - 2, top + 11, 8, 2, bn[3])
        for i in range(4): p.P(hx - 1 + i * 2, top + 12, bn[1])
        p.R(hx - 2, top + 13, 8, 1 + jaw, DK); p.R(hx - 2, top + 14 + jaw, 8, 1, bn[2])
        for i in range(4): p.P(hx - 1 + i * 2, top + 14 + jaw, bn[1])
        if kind == 'scream': p.P(hx - 4, top + 4, DK); p.P(hx + 5, top + 12, DK); p.P(hx - 1, top + 2, bn[1])
        if kind == 'gasmask':
            p.EL(hx + 1, top + 8, 6, 6, '#1c1c20'); p.R(hx - 4, top + 3, 11, 3, '#26262c'); p.R(hx - 5, top + 6, 3, 6, '#141418')
            for gx in (hx - 1, hx + 4):
                p.EL(gx, top + 7, 2, 2, '#c8a040'); p.R(gx - 1, top + 6, 3, 3, '#1a2626'); p.P(gx - 1, top + 6, '#a8d0c8'); p.P(gx + 1, top + 8, '#3a5a54')
            p.R(hx + 1, top + 11, 4, 4, '#c8a040'); p.R(hx + 1, top + 11, 4, 1, '#f0d070'); p.R(hx + 2, top + 15, 4, 3, '#8a6a20'); p.R(hx + 2, top + 18, 4, 1, '#3a2a10')
            p.P(hx - 5, top + 4, '#3a3a40'); p.P(hx - 6, top + 9, '#3a3a40')
        return
    hr = ramp(s.get('hair', '#3a2416'))
    if s.get('longHair'): p.R(hx - 7, top + 3, 4, 17, hr[1])
    p.EL(hx, top + 7, 6, 7, sk[1]); p.EL(hx + 1, top + 7, 5, 7, sk[2]); p.R(hx - 3, top + 12, 8, 3, sk[2]); p.P(hx + 3, top + 9, sk[3]); p.P(hx + 4, top + 3, sk[3])
    p.R(hx - 5, top + 6, 2, 4, sk[1]); p.P(hx - 5, top + 7, sk[0]); p.R(hx - 6, top + 1, 3, 7, hr[2]); p.P(hx - 4, top + 8, hr[1])
    p.R(hx + 6, top + 7, 1, 4, sk[2]); p.P(hx + 7, top + 9, sk[2]); p.P(hx + 7, top + 10, sk[1]); p.P(hx + 6, top + 11, sk[0])
    if nohat or s.get('slick'): p.R(hx - 5, top - 1, 11, 3, hr[2]); p.R(hx - 4, top - 2, 8, 1, hr[2]); p.P(hx + 3, top - 1, hr[3]); p.R(hx - 6, top + 1, 3, 4, hr[2])
    if s.get('eyepatch'): p.R(hx - 1, top + 6, 3, 3, '#141014'); p.TL(hx - 5, top + 4, hx + 6, top + 5, 1, '#141014')
    else: p.P(hx, top + 7, '#f0e8dc'); p.P(hx + 1, top + 7, s.get('eyeCol', '#1a0e0a'))
    p.P(hx + 3, top + 7, '#f0e8dc'); p.P(hx + 4, top + 7, s.get('eyeCol', '#1a0e0a'))
    p.R(hx - 1, top + 5, 3, 1, hr[1]); p.R(hx + 3, top + 5, 3, 1, hr[1]); p.P(hx + 2, top + 6, hr[1]); p.R(hx + 1, top + 12, 4, 1, sk[0])
    if s.get('glasses'):
        p.R(hx - 1, top + 6, 3, 3, '#9ab8c8'); p.R(hx + 3, top + 6, 3, 3, '#9ab8c8'); p.P(hx + 2, top + 7, '#2a2a2a'); p.P(hx, top + 7, '#1a0e0a'); p.P(hx + 4, top + 7, '#1a0e0a'); p.P(hx - 1, top + 6, '#ffffff')
    if s.get('freckles'):
        for q in ((-1, 9), (1, 10), (4, 9), (5, 10)): p.P(hx + q[0], top + q[1], '#b0603a')
    if s.get('scar'): p.TL(hx - 2, top + 3, hx + 1, top + 11, 1, '#8a2a2a')
    if s.get('stubble'):
        for yy in range(top + 10, top + 15):
            for xx in range(hx - 3, hx + 6):
                if (xx + yy) % 2 == 0: p.P(xx, yy, shade(sk[1], .8))
    if s.get('beard'): p.R(hx - 4, top + 10, 10, 5, hr[2]); p.R(hx - 3, top + 15, 8, 2, hr[2]); p.R(hx - 2, top + 17, 6, 1, hr[1]); p.R(hx - 4, top + 10, 1, 5, hr[1]); p.R(hx + 1, top + 12, 3, 1, '#3a1a10')
    m = s.get('must')
    if m == 'thin': p.R(hx + 1, top + 11, 5, 1, hr[1])
    if m == 'big': p.R(hx, top + 10, 7, 2, hr[2]); p.P(hx - 1, top + 12, hr[2]); p.P(hx + 7, top + 12, hr[2]); p.P(hx - 1, top + 13, hr[1]); p.P(hx + 7, top + 13, hr[1])
    if m == 'handle': p.R(hx, top + 10, 7, 2, hr[2]); p.P(hx - 1, top + 9, hr[2]); p.P(hx + 7, top + 9, hr[2]); p.P(hx - 2, top + 8, hr[1]); p.P(hx + 8, top + 8, hr[1])
    if s.get('charred'):
        p.TL(hx - 2, top + 2, hx, top + 8, 1, '#ff7a1a'); p.TL(hx + 3, top + 10, hx + 5, top + 13, 1, '#ffae3a'); p.P(hx - 4, top + 11, '#ff7a1a'); p.P(hx + 1, top + 3, '#ff9a2a')
        p.R(hx, top + 6, 2, 2, '#ffd040'); p.R(hx + 3, top + 6, 2, 2, '#ffd040'); p.P(hx, top + 6, '#ffffff'); p.P(hx + 3, top + 6, '#ffffff')
    if s.get('mask'):
        mk = ramp(s['mask']); p.R(hx - 6, top + 9, 13, 6, mk[2]); p.R(hx - 6, top + 10, 13, 1, mk[3]); p.P(hx + 6, top + 11, mk[1]); p.P(hx - 2, top + 13, mk[1])
        for r in range(5): p.R(hx - 4 + r, top + 15 + r, 9 - 2 * r, 1, mk[1])
    if s.get('cigar'):
        p.R(hx + 5, top + 12, 4, 1, '#f4f0e8'); p.P(hx + 9, top + 12, '#ff5a1a')
    if s.get('braid'):
        for i in range(13): p.R(hx - 8 + (i % 2), top + 17 + i, 3, 1, hr[1] if i % 2 else hr[2])

def finalize(surf):
    w, h = surf.get_size(); b = tob(surf)
    def A(x, y): return 0 if x < 0 or y < 0 or x >= w or y >= h else b[(y * w + x) * 4 + 3]
    rim = []
    for y in range(h):
        for x in range(w):
            if not b[(y * w + x) * 4 + 3]: continue
            if not A(x + 1, y): rim.append((x, y, .42))
            elif not A(x, y - 1): rim.append((x, y, .2))
    for x, y, k in rim:
        j = (y * w + x) * 4
        b[j] = int(b[j] + (255 - b[j]) * k); b[j + 1] = int(b[j + 1] + (205 - b[j + 1]) * k); b[j + 2] = int(b[j + 2] + (140 - b[j + 2]) * k)
    o = []
    for y in range(h):
        for x in range(w):
            if not b[(y * w + x) * 4 + 3] and (A(x - 1, y) or A(x + 1, y) or A(x, y - 1) or A(x, y + 1)): o.append((y * w + x) * 4)
    for j in o: b[j] = 20; b[j + 1] = 10; b[j + 2] = 12; b[j + 3] = 255
    return fromb(b, (w, h))

def camo(surf, bases, pal, seed):
    """troca as cores das roupas por camuflagem"""
    w, h = surf.get_size(); b = tob(surf); rr = random.Random(seed)
    look = {}
    for base in bases:
        for k, f in enumerate((.5, .74, 1, 1.2, 1.42)): look[C(shade(base, f))[:3]] = k
    grid = {}
    def cell(cx, cy):
        if (cx, cy) not in grid: grid[(cx, cy)] = rr.randrange(len(pal))
        return grid[(cx, cy)]
    fs = (.62, .8, 1, 1.12, 1.25)
    cols = [[C(shade(c, f))[:3] for f in fs] for c in pal]
    for y in range(h):
        for x in range(w):
            j = (y * w + x) * 4
            if not b[j + 3]: continue
            k = look.get((b[j], b[j + 1], b[j + 2]))
            if k is None: continue
            v = cell((x + (y // 3) % 2) // 3, (y + (x // 4) % 2) // 3)
            r, g, bb = cols[v][k]; b[j], b[j + 1], b[j + 2] = r, g, bb
    return fromb(b, (w, h))

class Spr:
    def __init__(self, s, muz, cig=None): self.s = s; self.muz = muz; self.cig = cig

WALK = [(-5, 0, 5, 0), (-1, 2, 1, 0), (5, 0, -5, 0), (1, 0, -1, 2)]
def build_char(s, pose, w, nohat=False, nohead=False):
    surf = S(SPW, SPH); p = Pt(surf)
    skel = s['kind'] == 'skel'; bo = 3 if s.get('build') == 'big' else 0; tw = 8 + bo; hx = AX + 1; top = 20
    bn = ramp(s.get('bone', '#efe6cd')); sk = bn if skel else ramp(s.get('skin', '#d89a68')); hd = ramp(s['gloves']) if s.get('gloves') else sk
    coat = ramp(s['coat']['col']) if s.get('coat') else None; shirt = ramp(s['shirt']) if s.get('shirt') else None; pon = ramp(s['poncho']) if s.get('poncho') else None
    sl = coat or pon or shirt or ramp('#6e4126'); slB = [sl[0], sl[0], sl[1], sl[2], sl[3]]
    g = gun_sprite(w); dual = w.get('dual'); rifle = w.get('rifle'); sx, sy = AX + 5 + bo, 40; muz = []; cig = None
    crouch = pose == 'crouch'; wf = int(pose[4]) if pose.startswith('walk') else None
    dyU = 12 if crouch else (-1 if wf in (1, 3) else 0)
    # ---------------- braço de trás
    p.oy = dyU
    if dual and pose in ('aim', 'recoil'):
        lift = -2 if pose == 'recoil' else 0
        p.R(sx - 4, sy + 3 + lift, 20, 4, slB[2]); p.R(sx - 4, sy + 6 + lift, 20, 1, slB[1]); surf.blit(g.s, (sx + 14, sy + 2 + lift + dyU))
        p.R(sx + 15, sy + 3 + lift, 4, 4, hd[1]); muz.append((sx + 14 + g.tip[0], sy + 2 + lift + g.tip[1] + dyU))
    elif dual and pose == 'draw':
        p.TL(sx - 5, sy + 1, sx, sy + 10, 4, slB[2]); p.TL(sx, sy + 10, sx + 7, sy + 15, 4, slB[2]); surf.blit(g.s, (sx + 7, sy + 14 + dyU)); p.R(sx + 9, sy + 15, 4, 4, hd[1])
        muz.append((sx + 7 + g.tip[0], sy + 14 + g.tip[1] + dyU))
    elif rifle and pose in ('aim', 'recoil'):
        p.R(sx - 4, sy + 3, 24, 4, slB[2]); p.R(sx - 4, sy + 6, 24, 1, slB[1]); p.R(sx + 19, sy + 2, 4, 4, hd[1])
    elif pose not in ('six0', 'six1'):
        bx = AX - tw - 3; swing = (-3, 0, 3, 0)[wf] if wf is not None else 0
        p.TL(bx, sy, bx + swing // 2, sy + 11, 4, slB[2]); p.TL(bx + swing // 2, sy + 11, bx + swing, sy + 18, 4, slB[2]); p.R(bx, sy, 1, 10, slB[1])
        p.R(bx + swing, sy + 19, 4, 1, slB[0]); p.R(bx + swing, sy + 20, 4, 3, hd[1]); p.P(bx + 1 + swing, sy + 23, hd[0])
        if s.get('cigarHand') and pose in ('idle', 'reach') and not crouch:
            p.R(bx + 3, sy + 21, 4, 1, '#f4f0e8'); p.P(bx + 7, sy + 21, '#ff5a1a'); cig = (bx + 8, sy + 20)
    # ---------------- pernas
    p.oy = 0
    lc = ramp(s['pants']) if s.get('pants') else None; shoe = s.get('shoes') == 'shoe'; bc = ramp(s.get('bootCol', '#2a1a12'))
    if crouch:
        legc = lc or [bn[1], bn[1], bn[2], bn[3], bn[3]]; th = 5 if lc else 2
        p.R(AX - 7, 78, 15, 4, legc[2]) if lc else p.R(AX - 5, 77, 12, 5, bn[2])
        p.TL(AX + 2, 78, AX + 12, 82, th, legc[2]); p.TL(AX + 12, 82, AX + 11, 92, th, legc[2])
        p.TL(AX - 6, 79, AX - 5, 91, th, legc[1]); p.TL(AX - 5, 91, AX - 14, 93, th, legc[1])
        p.R(AX + 9, 93, 6, 4, bc[2]); p.R(AX + 9, 97, 10, 2, bc[2]); p.R(AX + 9, 99, 11, 1, bc[0])
        p.R(AX - 22, 94, 9, 4, bc[1]); p.R(AX - 23, 97, 6, 2, bc[0])
    else:
        legs = WALK[wf] if wf is not None else (-3, 0, 3, 0)
        if not lc: p.R(AX - 5, TB + 1, 12, 5, bn[2]); p.R(AX - 1, TB + 2, 4, 2, '#1c1216')
        for li, (hip, dx, lift, front) in enumerate(((AX - 7, legs[0], legs[1], 0), (AX + 2, legs[2], legs[3], 1))):
            y1 = (95 if shoe else 91) - lift
            for y in range(66, y1):
                o = int(round(dx * (y - 66) / 30)); x = hip + o
                if lc:
                    if y < 71 and wf is None: continue
                    p.R(x, y, 6, 1, lc[2] if front else lc[1]); p.P(x, y, lc[1] if front else lc[0])
                    if front: p.P(x + 5, y, lc[3])
                else:
                    if y < 70: continue
                    p.R(x + 2, y, 2, 1, bn[2] if front else bn[1])
                    if y == 78 - lift: p.R(x + 1, y, 4, 2, bn[2] if front else bn[1])
            fx = hip + int(round(dx * (y1 - 66) / 30)) - (3 if not front else 3)
            fx = hip - 3 + int(round(dx * (y1 - 66) / 30)) + (0 if not front else 0)
            if shoe:
                yb = 95 - lift
                p.R(fx, yb, 9, 3, bc[2 if front else 1]); p.R(fx, yb, 9, 1, bc[3]); p.R(fx, yb + 3, 10, 1, bc[0]); p.P(fx + 9, yb + 2, bc[2])
            else:
                yb = 91 - lift
                p.R(fx, yb, 6, 6, bc[2 if front else 1]); p.R(fx, yb, 6, 1, bc[0]); p.R(fx + 1, yb + 1, 1, 5, bc[3]); p.R(fx, yb + 6, 9, 2, bc[2 if front else 1])
                p.R(fx, yb + 8, 10, 1, bc[0]); p.P(fx + 9, yb + 7, bc[1]); p.R(fx, yb + 6, 2, 3, bc[0])
                p.P(fx - 1, yb + 5, '#b8b8c0'); p.P(fx - 2, yb + 6, '#e0e0e8'); p.P(fx - 1, yb + 7, '#b8b8c0')
        if lc and wf is None:
            for y in range(66, 71): p.R(AX - 7, y, 15, 1, lc[2]); p.P(AX - 7, y, lc[1])
        elif lc:
            for y in range(66, 70): p.R(AX - 6, y, 13, 1, lc[2])
    if s.get('skirt'): body_ext_skirt(p, s, crouch)
    # ---------------- tronco
    p.oy = dyU
    if skel and not shirt:
        p.R(AX - tw + 1, T0, 2 * tw - 1, TB - T0, '#1c1216')
        for y in range(T0 + 3, TB - 5, 3): p.R(AX - 6, y, 13, 1, bn[2]); p.P(AX - 6, y, bn[1]); p.P(AX + 6, y, bn[3])
        p.R(AX, T0, 2, TB - T0, bn[1]); p.R(AX - 5, TB - 5, 12, 5, bn[2]); p.R(AX - 1, TB - 4, 4, 2, '#1c1216')
    elif shirt:
        p.R(AX - tw, T0, 2 * tw + 1, TB - T0, shirt[2]); p.R(AX - tw, T0, 2, TB - T0, shirt[1]); p.R(AX + tw, T0, 1, TB - T0, shirt[3])
        for y in range(T0 + 4, TB, 6): p.P(AX + 1, y, shirt[1])
    if skel: p.R(AX, 34, 2, 5, bn[1]); p.P(AX, 36, bn[3])
    else: p.R(AX - 1, 34, 5, 5, sk[1])
    if s.get('tie'): t = ramp(s['tie']); p.R(AX, T0, 3, 2, t[1]); p.R(AX, T0 + 2, 3, 15, t[2]); p.R(AX + 1, T0 + 2, 1, 14, t[3]); p.P(AX + 1, T0 + 17, t[2])
    if s.get('susp'): p.R(AX - 5, T0, 2, TB - T0, s['susp']); p.R(AX + 4, T0, 2, TB - T0, s['susp'])
    def garment(gr, y0, y1, of, flare):
        for y in range(y0, y1):
            op = of(y); f = max(0, (y - TB + 2) // 4) if flare else 0
            L0, L1, R0, R1 = AX - tw - 1 - f, AX + 1 - op, AX + 2 + op, AX + tw + 2 + f
            if L1 > L0: p.R(L0, y, L1 - L0, 1, gr[1]); p.P(L0, y, gr[0]); (p.P(L1 - 1, y, gr[3]) if L1 - 1 > L0 else None)
            if R1 > R0: p.R(R0, y, R1 - R0, 1, gr[2]); p.P(R1 - 1, y, gr[3]); p.P(R0, y, gr[4])
    def belt():
        p.R(AX - tw, TB, 2 * tw + 1, 3, '#2a1810'); p.R(AX - tw, TB, 2 * tw + 1, 1, '#4a2c18')
        if s.get('skullBuckle'): p.R(AX, TB - 1, 6, 5, bn[2]); p.P(AX + 1, TB + 1, '#140a0c'); p.P(AX + 3, TB + 1, '#140a0c'); p.R(AX + 1, TB + 3, 4, 1, bn[1])
        else: p.R(AX + 1, TB, 4, 3, '#d9aa3a'); p.P(AX + 2, TB + 1, '#7a5410')
    if s.get('vest'):
        v = ramp(s['vest']); garment(v, T0 + 1, TB + 1, lambda y: ((T0 + 8 - y) >> 1) if y < T0 + 8 else 0, False)
        for i in range(3): p.P(AX + 3, T0 + 10 + i * 5, '#d9aa3a')
    if s.get('bandolier'):
        for i in range(25):
            X, Y = AX + tw - 1 - i * .7, T0 + i; p.R(X, Y, 3, 2, '#5a3a1a')
            if i % 3 == 0: p.P(X + 1, Y, '#e8c050')
    ck = (s.get('coat') or {}).get('kind')
    if ck not in ('jacket', 'tunic', 'cassock'): belt()
    if pon:
        for y in range(T0 - 1, TB + 3):
            hw = min(16, 9 + ((y - T0) >> 1)); p.R(AX - hw + 1, y, 2 * hw, 1, pon[2]); p.R(AX - hw + 1, y, 2, 1, pon[1]); p.P(AX + hw, y, pon[3])
        pb = s.get('ponchoB', '#e8c060'); p.R(AX - 14, T0 + 12, 30, 1, pb); p.R(AX - 15, T0 + 14, 32, 1, '#2a1a14'); p.R(AX - 16, T0 + 18, 34, 1, pb)
        for X in range(AX - 15, AX + 17, 2): p.P(X, TB + 3, pon[1])
        p.R(AX - 1, T0 - 1, 4, 2, sk[1])
    if coat:
        gap = s['coat'].get('gap', 1)
        if ck == 'jacket':
            garment(coat, T0 - 1, TB + 6, lambda y: ((T0 + 13 - y) >> 1) if y < T0 + 13 else (1 if y >= TB + 3 else 0), False)
            p.P(AX + 2, T0 + 15, coat[0]); p.P(AX + 2, T0 + 20, coat[0])
            if s.get('pocket'):
                for q in ((6, 5), (7, 5), (6, 4), (8, 4)): p.P(AX + q[0], T0 + q[1], s['pocket'])
        elif ck == 'tunic':
            garment(coat, T0 - 1, TB + 8, lambda y: 1 if y < T0 + 3 else 0, False)
            for i in range(5): p.R(AX + 2, T0 + 4 + i * 5, 2, 2, '#e8e8e0'); p.P(AX + 2, T0 + 4 + i * 5, '#ffffff')
            p.R(AX - tw - 1, TB, 2 * tw + 3, 3, '#141014'); p.R(AX + 1, TB, 4, 3, '#a8a8b0')
        elif ck == 'dress':
            garment(coat, T0 - 1, 80, lambda y: 0, True)
            for X in range(AX - 15, AX + 18, 2): p.P(X, 80, '#f4f4f0'); p.P(X + 1, 81, '#d8d8d0')
        elif ck == 'cassock':
            garment(coat, T0 - 1, 92, lambda y: 0, True)
            for i in range(9): p.P(AX + 2, T0 + 3 + i * 4, coat[0])
        else:
            garment(coat, T0 - 1, 88, lambda y: ((T0 + 12 - y) >> 1) + gap if y < T0 + 12 else (gap if y < TB else gap + ((y - TB) >> 2)), True)
    if s.get('plate'):
        pl = ramp(s['plate']); p.R(AX - tw, T0 + 2, 2 * tw + 2, TB - T0 - 1, pl[2]); p.R(AX - tw, T0 + 2, 2, TB - T0 - 1, pl[1]); p.R(AX - tw, T0 + 2, 2 * tw + 2, 1, pl[3])
        for i in range(3): p.R(AX - 6 + i * 6, TB - 11, 5, 7, pl[1]); p.R(AX - 6 + i * 6, TB - 11, 5, 1, pl[3]); p.P(AX - 4 + i * 6, TB - 9, pl[0])
        p.R(AX - 4, T0 + 5, 10, 3, pl[1]); p.R(AX + 5, T0 + 3, 2, 8, '#141410')
        p.R(AX - tw, TB, 2 * tw + 2, 3, '#2a2a20'); p.R(AX + 1, TB, 4, 3, '#6a6a5a')
    if s.get('badge'):
        X, Y = AX + 6, T0 + 8; p.P(X, Y - 1, '#f8d060'); p.R(X - 1, Y, 3, 1, '#f8d060'); p.P(X, Y + 1, '#c8a030'); p.P(X - 1, Y + 2, '#c8a030'); p.P(X + 1, Y + 2, '#c8a030')
    if s.get('aiguillette'):
        for i in range(11): p.P(AX + 4 + i * .55, T0 + 1 + (i * i) // 9, '#f0eee6'); p.P(AX + 3 + i * .5, T0 + 3 + (i * i) // 7, '#d8d6ce')
    if s.get('insignia'): p.R(AX - 6, T0 + 6, 4, 2, '#d01818'); p.R(AX - 6, T0 + 9, 4, 1, '#d8d8d8')
    body_ext(p, s, tw)
    if s.get('collar'): p.R(AX, 35, 3, 2, '#f4f4f0')
    if s.get('cross'):
        p.TL(AX - 3, 37, AX + 1, T0 + 8, 1, '#c8a040'); p.TL(AX + 5, 37, AX + 2, T0 + 8, 1, '#c8a040')
        p.R(AX + 1, T0 + 8, 2, 7, '#e0b040'); p.R(AX - 1, T0 + 10, 6, 2, '#e0b040'); p.P(AX + 1, T0 + 8, '#fff0a0')
    # coldre
    if not rifle and not s.get('noHolster'):
        p.R(AX + 7 + bo, TB + 2, 5, 11, '#3a2214'); p.R(AX + 7 + bo, TB + 2, 1, 11, '#5a3420'); p.R(AX + 8 + bo, TB + 13, 3, 1, '#3a2214')
    if s.get('neck') == 'bandana':
        nb = ramp(s['neckCol']); big = s.get('bigBandana'); n = 9 if big else 6
        for r in range(n): p.R(AX - 4 - (2 if big else 0) + r, 35 + r, 11 + (4 if big else 0) - 2 * r, 1, nb[2])
        p.R(AX - 4, 35, 11, 1, nb[3]); p.P(AX + 1, 36, nb[0])
    if s.get('scarf'):
        sc = ramp(s['scarf']); p.R(AX - 4, 35, 11, 3, sc[2]); p.R(AX - 4, 35, 11, 1, sc[3]); p.R(AX - 3, 38, 3, 18, sc[1]); p.R(AX + 4, 38, 3, 22, sc[2]); p.P(AX + 4, 60, sc[1]); p.P(AX + 6, 60, sc[1])
    if nohead:
        p.R(AX - 1, 31, 5, 5, '#8a0a0a'); p.R(AX, 30, 3, 2, '#c01010'); p.P(AX + 1, 29, '#e02020'); p.R(AX - 2, 34, 7, 2, '#5a0404')
        if skel: p.R(AX, 31, 2, 4, bn[1]); p.P(AX + 1, 30, bn[0])
    else:
        draw_head(p, s, hx, top, bn, sk, nohat)
        head_ext(p, s, hx, top)
        if not nohat and s.get('hat'): draw_hat(p, s['hat'], hx, top + 2 - (3 if pose == 'tip' else 0))
    # ---------------- braço da frente
    gp = ramp(w['grip'])
    def grip():
        if rifle or s.get('noHolster'): return
        p.R(AX + 5 + bo, TB - 3, 3, 5, gp[2]); p.P(AX + 5 + bo, TB - 3, gp[3]); p.P(AX + 8 + bo, TB - 3, ramp(w['metal'])[0])
    def flag():
        if s.get('flag'):
            p.R(sx + 1, sy + 3, 4, 3, '#1e8a3a'); p.P(sx + 2, sy + 4, '#f0d020'); p.P(sx + 3, sy + 4, '#2a4aa0')
    if rifle and pose not in ('aim', 'recoil', 'up'):
        p.TL(sx, sy, sx + 3, sy + 10, 5, sl[2]); flag(); p.TL(sx + 3, sy + 10, sx + 8, sy + 16, 4, sl[2])
        f = rot_blit(surf, g.s, g.anchor, -32, (sx + 9, sy + 17 + dyU)); p.R(sx + 7, sy + 15, 4, 4, hd[2])
        p.R(AX - tw - 1, sy + 5, 4, 4, hd[1])
        mz = f(*g.tip); muz.insert(0, (mz[0], mz[1]))
    elif pose in ('idle', 'walk0', 'walk1', 'walk2', 'walk3') and s.get('priestGun'):
        f = rot_blit(surf, g.s, g.anchor, -35, (sx + 4, sy + 17 + dyU)); p.TL(sx, sy, sx + 2, sy + 10, 5, sl[2]); p.TL(sx + 2, sy + 10, sx + 4, sy + 16, 4, sl[2]); p.R(sx + 2, sy + 15, 4, 4, hd[2])
    elif pose == 'idle' or crouch:
        if crouch:
            p.TL(sx, sy, sx + 5, sy + 10, 5, sl[1]); p.TL(sx + 1, sy, sx + 6, sy + 9, 4, sl[2]); p.TL(sx + 5, sy + 9, sx + 13, sy + 13, 4, sl[2]); flag()
            surf.blit(g.s, (sx + 18 - g.anchor[0], sy + 14 - g.anchor[1] + dyU)); p.R(sx + 17, sy + 13, 4, 4, hd[2]); muz.insert(0, (sx + 18 - g.anchor[0] + g.tip[0], sy + 14 - g.anchor[1] + g.tip[1] + dyU))
        else:
            grip(); p.R(sx, sy, 5, 12, sl[2]); p.R(sx, sy, 1, 12, sl[1]); p.R(sx + 4, sy, 1, 12, sl[3]); flag()
            p.R(sx + 1, sy + 12, 5, 7, sl[2]); p.R(sx + 1, sy + 12, 1, 7, sl[1]); p.R(sx + 5, sy + 12, 1, 7, sl[3]); p.R(sx + 1, sy + 19, 5, 1, sl[0])
            p.R(sx + 2, sy + 20, 4, 4, hd[2]); p.P(sx + 2, sy + 23, hd[1]); p.R(sx + 6, sy + 21, 1, 2, hd[1])
    elif wf is not None:
        grip(); sw = (3, 0, -3, 0)[wf]
        p.TL(sx, sy, sx + 1 + sw // 2, sy + 11, 5, sl[2]); flag(); p.TL(sx + 1 + sw // 2, sy + 11, sx + 2 + sw, sy + 18, 4, sl[2]); p.R(sx + 2 + sw, sy + 19, 4, 1, sl[0])
        p.R(sx + 2 + sw, sy + 20, 4, 4, hd[2]); p.P(sx + 2 + sw, sy + 23, hd[1])
    elif pose == 'reach':
        grip(); p.TL(sx, sy, sx + 2, sy + 11, 5, sl[2]); flag(); p.TL(sx + 2, sy + 11, AX + 5 + bo, TB - 7, 4, sl[2]); p.R(AX + 4 + bo, TB - 5, 5, 4, hd[2]); p.P(AX + 4 + bo, TB - 2, hd[1])
    elif pose == 'draw':
        p.TL(sx, sy, sx + 5, sy + 10, 5, sl[1]); p.TL(sx + 1, sy, sx + 6, sy + 9, 4, sl[2]); flag(); p.TL(sx + 5, sy + 9, sx + 13, sy + 14, 4, sl[1]); p.TL(sx + 5, sy + 9, sx + 13, sy + 13, 3, sl[2])
        p.R(sx + 16, sy + 12, 1, 5, sl[0]); surf.blit(g.s, (sx + 18 - g.anchor[0], sy + 14 - g.anchor[1] + dyU)); p.R(sx + 17, sy + 13, 4, 4, hd[2]); p.P(sx + 17, sy + 16, hd[1])
        muz.insert(0, (sx + 18 - g.anchor[0] + g.tip[0], sy + 14 - g.anchor[1] + g.tip[1] + dyU))
    elif pose in ('aim', 'recoil') and rifle:
        up = -2 if pose == 'recoil' else 0
        surf.blit(g.s, (sx - 10, sy - 4 + up)); p.R(sx, sy, 6, 5, sl[2]); p.R(sx, sy, 6, 1, sl[3]); flag(); p.R(sx + 2, sy + 1 + up, 4, 4, hd[2])
        muz.insert(0, (sx - 10 + g.tip[0], sy - 4 + up + g.tip[1]))
    elif pose == 'aim':
        p.R(sx, sy - 1, 19, 5, sl[2]); p.R(sx, sy - 1, 19, 1, sl[3]); p.R(sx, sy + 3, 19, 1, sl[1]); flag(); p.R(sx + 18, sy - 1, 2, 5, sl[0])
        surf.blit(g.s, (sx + 22 - g.anchor[0], sy - g.anchor[1])); p.R(sx + 20, sy - 1, 4, 5, hd[2]); p.P(sx + 20, sy + 3, hd[1]); p.P(sx + 23, sy - 1, hd[3])
        muz.insert(0, (sx + 22 - g.anchor[0] + g.tip[0], sy - g.anchor[1] + g.tip[1]))
    elif pose == 'recoil':
        p.TL(sx, sy, sx + 15, sy - 4, 5, sl[2]); p.TL(sx, sy + 3, sx + 15, sy - 1, 1, sl[1]); flag(); p.R(sx + 16, sy - 5, 2, 5, sl[0])
        f = rot_blit(surf, g.s, g.anchor, 16, (sx + 20, sy - 4)); p.R(sx + 18, sy - 6, 4, 5, hd[2]); p.P(sx + 18, sy - 2, hd[1])
        mz = f(*g.tip); muz.insert(0, (mz[0], mz[1]))
    elif pose in ('six0', 'six1'):
        grip(); hi = pose == 'six0'; yy = sy + (5 if hi else 14); yb = sy + (14 if hi else 5)
        p.TL(AX - tw, sy + 2, AX - 1, sy + 11, 4, slB[2]); p.TL(AX - 1, sy + 11, AX + 9, yb, 4, slB[3]); p.R(AX + 9, yb - 2, 6, 3, hd[1]); p.R(AX + 9, yb - 3, 6, 1, hd[3])
        p.TL(sx, sy, sx + 2, sy + 9, 5, sl[2]); flag(); p.TL(sx + 2, sy + 9, sx + 12, yy, 4, sl[2]); p.R(sx + 12, yy - 2, 6, 3, hd[2]); p.R(sx + 12, yy - 3, 6, 1, hd[3])
    elif pose.startswith('twirl'):
        k = int(pose[5]); p.TL(sx, sy, sx + 2, sy + 10, 5, sl[2]); flag(); p.TL(sx + 2, sy + 10, sx + 10, sy + 13, 4, sl[2]); p.R(sx + 10, sy + 11, 1, 5, sl[0])
        rot_blit(surf, g.s, (g.anchor[0] + 1, g.anchor[1]), k * 90, (sx + 13, sy + 13 + dyU)); p.R(sx + 11, sy + 11, 4, 4, hd[2]); p.P(sx + 11, sy + 14, hd[1])
    elif pose == 'blow':
        p.TL(sx, sy, sx + 5, sy + 9, 5, sl[2]); flag(); p.TL(sx + 5, sy + 9, sx + 6, sy - 3, 4, sl[2]); p.R(sx + 5, sy - 4, 5, 1, sl[0])
        f = rot_blit(surf, g.s, g.anchor, 90, (sx + 7, sy - 6)); p.R(sx + 5, sy - 8, 5, 4, hd[2]); p.P(sx + 5, sy - 5, hd[1]); mz = f(*g.tip); muz.insert(0, (mz[0], mz[1]))
    elif pose == 'tip':
        grip(); p.TL(sx, sy, sx + 4, sy - 6, 5, sl[2]); flag(); p.TL(sx + 4, sy - 6, AX + 11, 21, 4, sl[2]); p.R(AX + 10, 17, 5, 4, hd[2]); p.P(AX + 10, 20, hd[1])
    elif pose == 'up':
        ux = sx + 4; p.R(sx, sy, 6, 5, sl[2]); p.R(ux, sy - 18, 5, 21, sl[2]); p.R(ux, sy - 18, 1, 21, sl[1]); p.R(ux + 4, sy - 18, 1, 21, sl[3]); p.R(ux, sy - 19, 5, 1, sl[0])
        rot_blit(surf, g.s, g.anchor, 90, (ux + 2, sy - 21)); p.R(ux, sy - 23, 5, 4, hd[2]); p.P(ux, sy - 20, hd[1])
    if s.get('camo'):
        surf = camo(surf, [x for x in (s.get('coat', {}).get('col'), s.get('shirt'), s.get('pants')) if x], s['camo'], 77)
    return Spr(finalize(surf), muz, cig)

def build_hat(s):
    surf = S(SPW, 30); draw_hat(Pt(surf), s['hat'], AX + 1, 22); return finalize(surf)
def build_pile(s):
    surf = S(70, 24); p = Pt(surf); bn = ramp(s.get('bone', '#efe6cd')); cl = ramp((s.get('coat') or {}).get('col') or s.get('shirt') or '#6e4126')
    p.EL(30, 19, 24, 4, cl[1]); p.EL(31, 18, 21, 3, cl[2]); p.R(12, 17, 8, 1, cl[3]); p.R(36, 16, 10, 1, cl[3])
    if s.get('tie'): p.R(30, 16, 2, 5, s['tie'])
    if s.get('scarf'): p.R(20, 15, 14, 2, s['scarf'])
    def bone(X, Y, l, v):
        if v: p.R(X, Y, 2, l, bn[2]); p.P(X - 1, Y, bn[2]); p.P(X + 2, Y + l - 1, bn[2])
        else: p.R(X, Y, l, 2, bn[2]); p.P(X, Y - 1, bn[2]); p.P(X + l - 1, Y + 2, bn[2]); p.R(X, Y + 1, l, 1, bn[1])
    bone(6, 14, 9, False); bone(50, 15, 10, False); bone(24, 12, 7, False); bone(58, 11, 2, True); bone(16, 9, 2, True)
    for i in range(4): p.R(36 + i * 3, 12, 1, 4, bn[2])
    hs = dict(s); hs['head'] = 'skull' if s.get('head') == 'gasmask' else s.get('head', 'skull'); hs['kind'] = 'skel'
    draw_head(p, hs, 48, 4, bn, bn, True)
    if s.get('hat'): draw_hat(p, s['hat'], 18, 12)
    if s.get('camo'): surf = camo(surf, [x for x in ((s.get('coat') or {}).get('col'),) if x], s['camo'], 5)
    return finalize(surf)

# ------------------------------------------------------------------ Zé Caixão: visuais
SKINS = [
    dict(id='classic', name='CLÁSSICO', price=0, desc='O PISTOLEIRO MORTO DE SEMPRE.', s=dict(kind='skel', eye='#ff3a2a', hat=dict(type='cowboy', col='#1c1822', band='#7a1f24'), coat=dict(col='#6e4126', gap=3), bootCol='#2a1a12')),
    dict(id='malandro', name='MALANDRO', price=500, desc='TERNO BRANCO, GRAVATA VERMELHA E UM CIGARRO.', s=dict(kind='skel', eye='#ff3a2a', hat=dict(type='fedora', col='#f2f0ea', band='#d01818'), coat=dict(col='#eeece6', kind='jacket'), shirt='#ffffff', tie='#d01818', pocket='#e01818', pants='#e8e6de', bootCol='#f0eee8', shoes='shoe', cigarHand=True)),
    dict(id='agente', name='AGENTE FUNERÁRIO', price=800, desc='CHAPÉU LARGO, SOBRETUDO E CACHECOL.', s=dict(kind='skel', eye='#ff8a1a', eyeGlow='#ffd080', hat=dict(type='wide', col='#34343a', band='#8a8a90'), coat=dict(col='#4a4a54', gap=1), shirt='#d8d4cc', tie='#141418', scarf='#9a9aa2', gloves='#2a2a30', pants='#26262c', bootCol='#141414', shoes='shoe')),
    dict(id='gas', name='MÁSCARA DE GÁS', price=1200, desc='QUEPE, MÁSCARA DE GÁS E FARDA DE GALA.', s=dict(kind='skel', head='gasmask', hat=dict(type='peaked', col='#1a181e', band='#e8e6dc'), coat=dict(col='#1c1a20', kind='tunic'), shirt='#1c1a20', aiguillette=True, insignia=True, gloves='#141216', pants='#1a181e', bootCol='#0e0c10')),
    dict(id='ouro', name='CAVEIRA DOURADA', price=-1, desc='DERROTE EL DERECHA IZQUIERDA PARA LIBERAR.', s=dict(kind='skel', bone='#f2c84a', eye='#40e8ff', eyeGlow='#b0f8ff', hat=dict(type='cowboy', col='#141216', band='#f2c84a'), coat=dict(col='#1e1c22', gap=3), bootCol='#141216'))]
SKMAP = {k['id']: k for k in SKINS}
_ZC = {}
def ze(pose, skin=None, wid=None):
    skin = skin or SAVE['eqS']; wid = wid or SAVE['eqW']; k = (skin, wid, pose)
    if k not in _ZC: _ZC[k] = build_char(SKMAP[skin]['s'], pose, WMAP[wid])
    return _ZC[k]
_PILE = {}
def ze_pile():
    k = SAVE['eqS']
    if k not in _PILE: _PILE[k] = build_pile(SKMAP[k]['s'])
    return _PILE[k]

# ------------------------------------------------------------------ inimigos
def EN(name, delay, hp, wid, s, **k): d = dict(name=name, delay=delay, hp=hp, wid=wid, s=s); d.update(k); return d
ENEMIES = [
    EN('BANDIDO PETE', .62, 1, 'rust', dict(kind='human', skin='#d89a68', hair='#4a2a16', hat=dict(type='cowboy', col='#7a4a28', band='#3a2010'), mask='#c42a1a', shirt='#e6dccb', vest='#2a2228', pants='#3a3a4e', bootCol='#3a2414')),
    EN('KID CASCAVEL', .56, 1, 'rust', dict(kind='human', skin='#ecb48a', hair='#c87a30', freckles=True, hat=dict(type='cowboy', col='#c8a062', band='#5a3a1a'), neck='bandana', neckCol='#3e8a3a', shirt='#c8b48a', vest='#7a4a26', pants='#5a4a3a', bootCol='#6a3a1a')),
    EN('DOLORES VÍBORA', .52, 1, 'peace', dict(kind='human', skin='#c08058', hair='#1a1014', longHair=True, braid=True, hat=dict(type='wide', col='#5a1a2a', band='#c8a040'), neck='bandana', neckCol='#d02a2a', shirt='#6a3a8a', pants='#2a2230', bootCol='#1a1214', eyeCol='#2a6a2a')),
    EN('XERIFE TORTO', .49, 1, 'peace', dict(kind='human', skin='#d89a68', hair='#9a9a9a', must='handle', eyepatch=True, hat=dict(type='cowboy', col='#9a9088', band='#2a2a2a'), shirt='#e0d8c8', coat=dict(col='#6a4a30', gap=1), badge=True, pants='#3a3a40', bootCol='#3a2414')),
    EN('EL SOMBRERO', .46, 1, 'rust', dict(kind='human', skin='#b07048', hair='#1a1210', must='big', hat=dict(type='sombrero', col='#d8b070', band='#c83020'), poncho='#b83a2a', ponchoB='#e8c060', shirt='#e0d0b0', bandolier=True, pants='#4a3a2a', bootCol='#3a2414'), lang='es'),
    EN('O GRANDALHÃO', .50, 2, 'sawed', dict(kind='human', build='big', skin='#e0a478', hair='#6a3a1a', beard=True, hat=dict(type='bowler', col='#3a2a20', band='#1a1210'), shirt='#c8c0b0', susp='#5a3418', pants='#4a4038', bootCol='#2a1a12'), stagger=.42),
    EN('BLACK JACK', .42, 1, 'peace', dict(kind='human', skin='#e8c8a8', hair='#141014', must='thin', hat=dict(type='wide', col='#16141a', band='#c8a040'), shirt='#d8d0c0', vest='#8a1a1e', coat=dict(col='#1a181e', gap=2), pants='#16141a', bootCol='#0e0c10')),
    EN('O COVEIRO', .39, 1, 'rust', dict(kind='human', skin='#b8b4a8', hair='#3a3a3a', stubble=True, scar=True, hat=dict(type='top', col='#1e1c22', band='#4a1a2a'), shirt='#8a8478', coat=dict(col='#26242a', gap=1), pants='#26242a', bootCol='#141214')),
    EN('DOC MORFINA', .36, 2, 'widow', dict(kind='human', skin='#e0b090', hair='#5a4a3a', glasses=True, must='big', hat=dict(type='bowler', col='#6a6a70', band='#2a2a2e'), shirt='#ece6da', vest='#9a2020', tie='#141414', pants='#4a4a50', bootCol='#1a1416', shoes='shoe'), stagger=.36)]
BOSS1 = EN('EL DERECHA IZQUIERDA', .33, 6, 'bossdual', dict(kind='human', skin='#3a2622', charred=True, hair='#100808', hat=dict(type='cowboy', col='#16121a', band='#5a1010'), neck='bandana', neckCol='#a01818', bigBandana=True, shirt='#2a1e1e', coat=dict(col='#1e181e', gap=4), skullBuckle=True, pants='#1a161a', bootCol='#100c0e'),
           boss='fire', lang='es', stagger=.34, voice='boss10', music='boss1', tag='CHEFÃO')
BOSS2 = EN('BOSSE KRIEGER', .30, 8, 'rifle', dict(kind='skel', head='scream', eye='#ff3a1a', eyeGlow='#ffb080', hat=dict(type='cap', col='#4e5a34', band='#4e5a34'), shirt='#4e5a34', coat=dict(col='#4e5a34', kind='tunic'), plate='#3e4628', pants='#4e5a34', gloves='#2e3222', bootCol='#1e1a14', flag=True, camo=['#4e5a34', '#2e3a22', '#6a6a44', '#3a2e1e'], noHolster=True),
           boss='krieger', stagger=.32, voice='boss20', music='boss2', tag='CHEFÃO', lore=['MORTO EM COMBATE NA', 'GUERRA DO NORDESTE, 2030'])
NAMES = ['JOHNNY RINGO', 'CALAMITY JOE', 'BILLY BOCA-SUJA', 'TEX MORTALHA', 'JESSE SEM-DEDO', 'RED SIMPSON', 'MULA MANCA', 'JIMMY CORVO', 'NED OLHO-ROXO', 'ZECA PÓLVORA', 'LOBO SOLITÁRIO', 'CORONEL BALA']
def gen_enemy(L):
    r = random.Random(L * 7919 + 13); ch = lambda a: a[r.randrange(len(a))]
    s = dict(kind='human', skin=ch(['#d89a68', '#ecb48a', '#b07048', '#8a5a3a', '#e8c8a8', '#c08058']), hair=ch(['#1a1014', '#4a2a16', '#c87a30', '#9a9a9a', '#6a3a1a']),
             hat=dict(type=ch(['cowboy', 'wide', 'bowler', 'top', 'sombrero', 'fedora']), col=ch(['#7a4a28', '#2a2228', '#9a9088', '#c8a062', '#3a2a4a', '#16141a', '#6a2a1a', '#4a5a3a']), band=ch(['#3a2010', '#c8a040', '#a01818', '#1a1210'])),
             shirt=ch(['#e6dccb', '#c8b48a', '#8a8478', '#6a3a8a', '#a8b8c8']), pants=ch(['#3a3a4e', '#4a3a2a', '#26242a', '#5a4a3a']), bootCol=ch(['#2a1a12', '#3a2414', '#141214']))
    f = r.random()
    if f < .3: s['mask'] = ch(['#c42a1a', '#2a4a8a', '#1a1a1a'])
    elif f < .6: s['neck'] = 'bandana'; s['neckCol'] = ch(['#3e8a3a', '#d02a2a', '#e8c040'])
    g = r.random()
    if g < .33: s['vest'] = ch(['#2a2228', '#7a4a26', '#8a1a1e'])
    elif g < .66: s['coat'] = dict(col=ch(['#6a4a30', '#26242a', '#1a181e', '#5a3a2a']), gap=2)
    else: s['poncho'] = ch(['#b83a2a', '#3a6a8a', '#6a5a2a']); s['ponchoB'] = ch(['#e8c060', '#e0e0d0'])
    s['must'] = ch(['none', 'thin', 'big', 'handle', 'none'])
    if r.random() < .3: s['beard'] = True
    if r.random() < .25: s['scar'] = True
    if r.random() < .2: s['eyepatch'] = True
    if r.random() < .25: s['bandolier'] = True
    if r.random() < .2: s['build'] = 'big'
    hp = 1 + (1 if r.random() < .35 + L * .01 else 0) + (1 if L > 25 and r.random() < .3 else 0)
    return EN(ch(NAMES), max(.25, .34 - .006 * (L - 10)), hp, ch(['rust', 'peace', 'widow', 'sawed']), s, stagger=.36)
def enemy_for(L):
    if L % 10 == 0:
        b = dict(BOSS1 if (L // 10) % 2 == 1 else BOSS2)
        if L > 20: b['name'] = b['name'] + (' II' if L <= 40 else ' III'); b['hp'] = b['hp'] + 2 * ((L - 1) // 20); b['delay'] = max(.26, b['delay'] - .02 * ((L - 1) // 20))
        return b
    if L <= 9: return ENEMIES[L - 1]
    return gen_enemy(L)
EPOSES = ['idle', 'walk0', 'walk1', 'walk2', 'walk3', 'reach', 'draw', 'aim', 'recoil']
class ESprites: pass
def enemy_sprites(op):
    w = WMAP[op['wid']]; e = ESprites(); e.d = {}
    for q in EPOSES: e.d[q] = build_char(op['s'], q, w)
    for q in ('idle', 'reach', 'draw', 'aim', 'recoil'):
        e.d[q + '_nh'] = build_char(op['s'], q, w, nohat=True); e.d[q + '_x'] = build_char(op['s'], q, w, nohead=True)
    e.hat = build_hat(op['s']) if op['s'].get('hat') else None
    b = tob(e.d['idle_nh'].s); e.mask = bytearray(SPW * SPH)
    for i in range(SPW * SPH): e.mask[i] = 1 if b[i * 4 + 3] else 0
    e.hatmask = bytearray(SPW * 30)
    if e.hat:
        hb = tob(e.hat)
        for i in range(SPW * 30): e.hatmask[i] = 1 if hb[i * 4 + 3] else 0
    e.torso = []; e.edge = []
    for y in range(SPH):
        for x in range(SPW):
            if not e.mask[y * SPW + x]: continue
            if T0 + 2 <= y <= TB - 2 and AX - 6 <= x <= AX + 8: e.torso.append((x, y))
            if y < 80 and (not e.mask[y * SPW + x - 1] or not e.mask[(y - 1) * SPW + x]): e.edge.append((x, y))
    e.pile = build_pile(op['s']) if op['s']['kind'] == 'skel' else None
    return e

PRIEST_S = dict(kind='human', skin='#d8a888', hair='#16141a', slick=True, cigar=True, coat=dict(col='#16141a', kind='cassock'), shirt='#16141a', collar=True, cross=True, pants='#16141a', bootCol='#0e0c10', shoes='shoe', priestGun=True, noHolster=True)

# ------------------------------------------------------------------ cenários
THEMES = {
    'sunset': dict(sky=['#1c0b24', '#2a0f2e', '#3e1534', '#581b36', '#782234', '#9a2e30', '#ba3e2c', '#d6542a', '#ea6e2c', '#f48a32', '#f8a63c'], sun='sun', m1=['#8a3446', '#c8604a', '#782c40'], m2=['#5c2234', '#9a4a3e', '#4e1c2e'], gr=['#b86c3c', '#ac6238', '#a05834', '#94502e'], road='#b4723e', cl=['#3e1436', '#8a2e3a', '#5a1c36', '#d8643a'], ov=None, stars=20),
    'dusk': dict(sky=['#0e0a24', '#1a1036', '#2a1446', '#3e1a52', '#58205a', '#78285e', '#98325e', '#b8405a', '#d05656', '#e07050', '#ec8a50'], sun='low', m1=['#4a1e44', '#8a3a5a', '#3e1a3a'], m2=['#2e1430', '#5a2a48', '#24102a'], gr=['#8a5048', '#7e4842', '#72403c', '#683a36'], road='#8e5a4a', cl=['#24103a', '#5a2a5a', '#3a1a46', '#e07a6a'], ov=((40, 10, 60), 40), stars=60),
    'night': dict(sky=['#04060e', '#060a18', '#0a1022', '#0e162c', '#121c36', '#162240', '#1a2848', '#1e2e50', '#243458', '#2a3a5e', '#304066'], sun='moon', m1=['#1a2034', '#3a4a6a', '#141a2c'], m2=['#10141f', '#2a3448', '#0c101a'], gr=['#4a4650', '#423e4a', '#3a3644', '#34303e'], road='#4c4852', cl=['#0c1020', '#2a3450', '#141a30', '#5a6a8a'], ov=((10, 20, 70), 76), stars=160),
    'inferno': dict(sky=['#080204', '#120406', '#1e0608', '#2c080a', '#3e0a0a', '#560e0a', '#701408', '#8a1c06', '#a42806', '#be3806', '#d44a08'], sun='hell', m1=['#2a0a0c', '#8a2010', '#1e0608'], m2=['#160406', '#5a140a', '#100304'], gr=['#4a1a12', '#401610', '#38130e', '#30100c'], road='#52201a', cl=['#1a0406', '#5a1008', '#2a0608', '#ff6a1a'], ov=((90, 0, 0), 30), stars=0),
    'amazon': dict(sky=['#06110e', '#091711', '#0c1d15', '#102419', '#142c1d', '#183422', '#1d3c27', '#24462c', '#2c5032', '#365a38', '#40643e'], sun=None, gr=['#2a2416', '#262014', '#221c12', '#1e1810'], road='#3a2e1e', cl=['#2a4a3a', '#3a5a48', '#4a6a54', '#6a8a70'], ov=((0, 30, 20), 30), stars=0)}
def theme_for(L):
    if L % 10 == 0: return 'inferno' if (L // 10) % 2 == 1 else 'amazon'
    if L > 10: return ['sunset', 'dusk', 'night', 'amazon'][L % 4]
    return 'sunset' if L <= 3 else 'dusk' if L <= 6 else 'night'
def saguaro(p, X, B, h, dark=False):
    c1, c2, c3 = ('#2a3426', '#202a1e', '#36402e') if dark else ('#2e5030', '#1e3a22', '#4a7040')
    p.R(X, B - h, 7, h, c2); p.R(X + 1, B - h, 5, h, c1); p.R(X + 2, B - h + 1, 1, h - 2, c3); p.R(X + 1, B - h - 1, 5, 1, c2)
    ay = B - int(round(h * .55)); p.R(X - 6, ay, 6, 4, c2); p.R(X - 6, ay - 10, 4, 11, c2); p.R(X - 5, ay - 10, 2, 11, c1); p.R(X - 4, ay + 1, 4, 2, c1)
    by = B - int(round(h * .72)); p.R(X + 7, by, 6, 4, c2); p.R(X + 9, by - 8, 4, 9, c2); p.R(X + 10, by - 8, 2, 9, c1); p.R(X + 7, by + 1, 4, 2, c1)
    for y in range(B - h + 2, B, 3): p.P(X + 3, y, c2); p.P(X + 5, y + 1, c2)
MINI = {'W': ['101', '101', '101', '111', '101'], 'A': ['010', '101', '111', '101', '101'], 'N': ['101', '111', '111', '111', '101'], 'T': ['111', '010', '010', '010', '010'], 'E': ['111', '100', '110', '100', '111'], 'D': ['110', '101', '101', '101', '110'],
        '$': ['011', '110', '010', '011', '110'], '5': ['111', '100', '111', '001', '111'], '0': ['111', '101', '101', '101', '111']}
def mini(p, s, X, Y, col):
    for ch in s:
        g = MINI.get(ch)
        if g:
            for r in range(5):
                for k in range(3):
                    if g[r][k] == '1': p.P(X + k, Y + r, col)
        X += 4
SKYC, BGC, CLOUDC = {}, {}, {}
def build_bg(th):
    if th in BGC: return BGC[th]
    T = THEMES[th]; rr = random.Random(1337); rnd = rr.random
    sky = S(W, H); p = Pt(sky)
    bh = HZ / len(T['sky'])
    for i, col in enumerate(T['sky']):
        y0, y1 = int(round(i * bh)), int(round((i + 1) * bh)); p.R(0, y0, W, y1 - y0, col)
        if i > 0:
            prev = T['sky'][i - 1]
            for X in range(0, W, 2): p.P(X, y0, prev)
            for X in range(1, W, 4): p.P(X, y0 + 1, prev)
            for X in range(3, W, 8): p.P(X, y0 + 2, prev)
    for i in range(T['stars']):
        yy = int(rnd() * (140 if th == 'night' else 50)); p.P(int(rnd() * W), yy, '#f0e8d8' if rnd() < .3 else '#8a8aaa')
        if th == 'night' and rnd() < .08:
            X, Y = int(rnd() * W), int(rnd() * 90); p.P(X, Y, '#ffffff'); [p.P(X + a, Y + b, '#8a9ac0') for a, b in ((-1, 0), (1, 0), (0, -1), (0, 1))]
    def disc(sx, sy, sr, cols, stripes, glow):
        if glow:
            for Y in range(sy - sr - 14, HZ):
                for X in range(sx - sr - 14, sx + sr + 15):
                    d = math.hypot(X - sx, Y - sy)
                    if sr < d < sr + 14 and (d < sr + 4 or ((X + Y) % 2 == 0 and d < sr + 9) or (X % 3 == 0 and Y % 2 == 0)): p.P(X, Y, glow[0] if d < sr + 4 else glow[1])
        for Y in range(sy - sr, min(HZ, sy + sr + 1)):
            dy = Y - sy
            if stripes and dy > 0 and (6 <= dy <= 7 or 12 <= dy <= 14 or 18 <= dy <= 21): continue
            for X in range(sx - sr, sx + sr + 1):
                d = math.hypot(X - sx, Y - sy)
                if d <= sr: p.P(X, Y, cols[0] if d > sr - 3 else cols[1] if d > sr - 10 else cols[2])
    if T['sun'] == 'sun': disc(240, 146, 44, ['#f8b84a', '#fbd462', '#fde88a'], True, ['#f9b850', '#f6a040'])
    if T['sun'] == 'low': disc(240, 166, 40, ['#e0604a', '#f07a5a', '#ff9a70'], True, ['#d85a5a', '#b8485a'])
    if T['sun'] == 'moon':
        disc(360, 52, 24, ['#c8c6c0', '#dcdad2', '#ecebe4'], False, ['#3a4a6a', '#2a3858'])
        for X, Y, r in ((352, 46, 5), (368, 58, 4), (362, 40, 2), (350, 62, 3)):
            for yy in range(-r, r + 1):
                for xx in range(-r, r + 1):
                    if xx * xx + yy * yy <= r * r: p.P(X + xx, Y + yy, '#b8b6b0')
    if T['sun'] == 'hell': disc(240, 140, 64, ['#a01808', '#d83010', '#ff6020'], True, ['#8a1008', '#5a0806'])
    if th == 'amazon':
        for i in range(10):  # raios de luz
            x0 = 60 + i * 42 + int(rnd() * 20)
            for y in range(0, HZ + 40):
                X = x0 + y // 3
                if (X + y) % 3 == 0: p.R(X, y, 6, 1, '#4a7a58')
    cl = S(W * 2, 120); cp = Pt(cl)
    def cloud(X, Y, ln, t, col, hi):
        for r in range(t):
            w = int(round(ln * (1 - abs(r - (t - 1) / 2) / t * .8))); cp.R(X - w / 2 + (rnd() - .5) * 8, Y + r, w, 1, col)
        cp.R(X - ln * .35, Y + t, ln * .6, 1, hi)
    for i in range(14):
        X, ln, t = rnd() * W * 2, 60 + int(rnd() * 150), 2 + int(rnd() * 4)
        Y = (100 + int(rnd() * 18)) if th == 'amazon' else 10 + int(rnd() * 80)
        cloud(X, Y, ln, t, T['cl'][0] if Y < 45 else T['cl'][2], T['cl'][1] if Y < 45 else T['cl'][3])
    if th == 'amazon': cl.set_alpha(150)
    CLOUDC[th] = cl
    bg = S(W, H); p = Pt(bg)
    if th == 'amazon': _jungle(p, rnd, T)
    elif th in BGX: BGX[th](bg, p, rnd, T)
    else: _western(bg, p, rnd, T, th)
    if T['ov']:
        (r, g, b), a = T['ov']; o = S(W, H); o.fill((r, g, b, a)); bg.blit(o, (0, 0)); sky.blit(o, (0, 0))
    SKYC[th] = sky; BGC[th] = bg
    return bg
def _western(bg, p, rnd, T, th):
    def mesa(lst, col, rim, strata):
        for X in range(W):
            h = 0
            for m in lst:
                dx = abs(X - m[0]); v = m[2] if dx <= m[1] else m[2] - (dx - m[1]) * (m[3] if len(m) > 3 else 1.6); h = max(h, v)
            h = int(round(h))
            if h > 0:
                p.R(X, HZ - h, 1, h, col); p.P(X, HZ - h, rim)
                if rnd() < .5: p.P(X, HZ - h + 1, rim)
                for y in range(HZ - h + 4, HZ, 5):
                    if rnd() < .8: p.P(X, y, strata)
    mesa([(26, 32, 44), (142, 14, 26), (300, 38, 50), (368, 10, 68, 3), (450, 38, 38)], *T['m1'])
    mesa([(76, 26, 18), (226, 44, 9), (420, 44, 24)], *T['m2'])
    g = T['gr']; p.R(0, HZ, W, 9, g[0]); p.R(0, HZ + 9, W, 12, g[1]); p.R(0, HZ + 21, W, 18, g[2]); p.R(0, HZ + 39, W, H - HZ - 39, g[3])
    for X in range(0, W, 2): p.P(X, HZ + 9, g[0]); p.P(X + 1, HZ + 21, g[1]); p.P(X, HZ + 39, g[2])
    _road(p, rnd, T)
    for X, B, h in ((176, 181, 13), (282, 177, 10), (338, 183, 14), (46, 186, 11), (250, 180, 8)):
        k = '#3a2228'; p.R(X, B - h, 3, h, k); p.R(X - 3, B - h + 4, 3, 3, k); p.R(X - 3, B - h + 1, 2, 4, k); p.R(X + 3, B - h + 6, 3, 2, k); p.R(X + 4, B - h + 3, 2, 4, k)
    tw = '#2a160e'
    for X in (114, 153, 133): p.R(X, 141, 3, 70, tw)
    for k in range(3): line(bg, 117, 146 + k * 21, 153, 164 + k * 21, tw); line(bg, 153, 146 + k * 21, 117, 164 + k * 21, tw)
    p.R(110, 105, 50, 37, '#5a3220')
    for X in range(112, 160, 4): p.R(X, 105, 1, 37, '#46261a')
    p.R(111, 105, 3, 37, '#7a4a2a')
    for y in (110, 122, 134): p.R(110, y, 50, 2, '#24120a')
    p.R(110, 141, 50, 1, '#24120a')
    for r in range(15): w = int(round(r * 1.75)); p.R(135 - w, 90 + r, w * 2, 1, '#3a1e12'); p.R(135 - w, 90 + r, 2, 1, '#5a3220')
    p.R(134, 86, 2, 4, '#3a1e12')
    mw = '#24120f'
    for a, b in ((374, 386), (375, 387), (406, 394), (405, 393)): line(bg, a, 212, b, 96, mw)
    for k in range(6):
        y = 110 + k * 17; sp = k * 1.7; line(bg, 384 - sp, y, 397 + sp, y + 15, mw); line(bg, 397 + sp, y, 384 - sp, y + 15, mw)
    saguaro(p, 452, 190, 46); saguaro(p, 200, 198, 36); saguaro(p, 270, 183, 20, True)
    for X, Y in ((318, 190), (338, 194), (356, 188)):
        p.R(X, Y, 2, 14, '#3a2414'); p.R(X - 3, Y + 3, 8, 2, '#3a2414'); p.R(X, Y, 1, 14, '#5a3a20'); p.R(X - 4, Y + 14, 10, 2, '#4a3a2a')
    for X in range(282, W, 20): p.R(X, 180, 4, 33, '#3a2012'); p.R(X, 180, 4, 1, '#6a3e24'); p.R(X, 181, 1, 32, '#5a3420')
    p.R(280, 187, 200, 3, '#4a2a18'); p.R(280, 187, 200, 1, '#7a4a2a'); p.R(280, 199, 200, 3, '#4a2a18'); p.R(280, 199, 200, 1, '#7a4a2a')
    # saloon
    p.R(0, 69, 93, 142, '#5a3220')
    for X in range(0, 93, 5): p.R(X, 69, 1, 142, '#46261a')
    for X in range(2, 93, 5): p.R(X, 69, 1, 142, '#6c3e26')
    p.R(12, 58, 69, 11, '#5a3220'); p.R(12, 58, 69, 1, '#3a1e12'); p.R(0, 69, 12, 1, '#3a1e12'); p.R(81, 69, 12, 1, '#3a1e12'); p.R(93, 69, 1, 142, '#3a1e12')
    p.R(13, 73, 67, 19, '#2a160c'); p.R(14, 74, 65, 17, '#8a5a30'); p.R(16, 76, 61, 13, '#3a2010'); raw(bg, 'SALOON', 12, 79, 2, '#f0c060')
    for wx in (8, 38, 68):
        p.R(wx, 98, 16, 19, '#2a140c'); p.R(wx + 1, 99, 14, 17, '#f0a040'); p.R(wx + 1, 108, 14, 8, '#c86a28'); p.R(wx + 8, 99, 1, 17, '#2a140c'); p.R(wx + 1, 106, 14, 1, '#2a140c')
    p.R(0, 123, 96, 4, '#3a2010')
    for X in range(1, 96, 5): p.R(X, 127, 2, 11, '#4a2a18')
    p.R(0, 138, 96, 3, '#3a2010'); p.R(0, 123, 96, 1, '#7a4a2a'); p.R(0, 147, 102, 6, '#2e180e'); p.R(0, 147, 102, 1, '#6a3e24')
    o = S(94, 57); o.fill((20, 6, 6, 97)); bg.blit(o, (0, 153))
    for q in (3, 48, 96): p.R(q, 153, 4, 57, '#3a2012'); p.R(q, 153, 1, 57, '#6a3e24')
    p.R(33, 165, 24, 45, '#1c0e08'); p.R(33, 174, 11, 23, '#7a4a28'); p.R(46, 174, 11, 23, '#7a4a28')
    for y in range(177, 196, 4): p.R(33, y, 11, 1, '#4a2a18'); p.R(46, y, 11, 1, '#4a2a18')
    p.R(66, 168, 18, 21, '#2a140c'); p.R(67, 169, 16, 19, '#e08a34'); p.R(67, 178, 16, 10, '#b05a24'); p.R(75, 169, 1, 19, '#2a140c')
    # cartaz PROCURADO (corrigido: texto cabe no papel)
    p.R(6, 160, 26, 34, '#2a1a10'); p.R(7, 161, 24, 32, '#e8d8a8'); p.R(7, 161, 24, 1, '#f8ecc0'); p.P(18, 160, '#8a8a8a')
    mini(p, 'WANTED', 8, 163, '#3a2010'); p.R(12, 170, 14, 13, '#2a1a10'); p.R(13, 171, 12, 11, '#c8b890')
    p.EL(19, 175, 3, 3, '#efe6cd'); p.R(17, 175, 2, 1, '#2a1a10'); p.R(20, 175, 2, 1, '#2a1a10'); p.R(17, 179, 5, 2, '#efe6cd'); p.R(14, 172, 10, 1, '#1c1822'); p.R(16, 171, 6, 1, '#1c1822')
    mini(p, '$500', 12, 185, '#7a1a10')
    p.R(0, 210, 102, 4, '#4a2a18'); p.R(0, 210, 102, 1, '#7a4a2a')
    wx0, wy0 = 88, 199
    for a in range(80):
        t = a / 80 * 6.283; p.P(wx0 + round(math.cos(t) * 12), wy0 + round(math.sin(t) * 12), '#3a2012'); p.P(wx0 + round(math.cos(t) * 11), wy0 + round(math.sin(t) * 11), '#6a4224')
    for k in range(10): t = k / 10 * 6.283; line(bg, wx0, wy0, wx0 + math.cos(t) * 11, wy0 + math.sin(t) * 11, '#4a2a18')
    p.R(wx0 - 2, wy0 - 2, 4, 4, '#2a140c')
    p.R(452, 195, 28, 34, '#2a160c'); p.R(453, 196, 26, 32, '#6a3a1c')
    for X in range(456, 478, 4): p.R(X, 196, 1, 32, '#4e2a14')
    p.R(454, 196, 3, 32, '#8a5228')
    for y in (200, 211, 222): p.R(453, y, 26, 2, '#2a1a10')
    p.R(453, 200, 26, 1, '#9a9a9a'); p.R(454, 195, 24, 3, '#3a2414')
    p.R(400, 214, 24, 20, '#5a3a1c'); p.R(400, 214, 24, 1, '#2a160c'); p.R(400, 224, 24, 1, '#2a160c'); line(bg, 400, 214, 424, 234, '#2a160c'); p.R(401, 215, 22, 1, '#7a5228')
    _grass(p, rnd)
def _road(p, rnd, T):
    g = T['gr']; p.R(0, 211, W, 36, T['road'])
    for X in range(0, W, 2): p.P(X, 210, T['road']); p.P(X + 1, 247, g[3])
    for X in range(0, W, 4): p.P(X + 1, 209, T['road'])
    rd = shade(T['road'], .88)
    for X in range(W):
        if rnd() < .7: p.P(X, 220, rd)
        if rnd() < .7: p.P(X, 236, rd)
    for i in range(3200):
        X, Y = int(rnd() * W), HZ + int(rnd() * (H - HZ))
        p.P(X, Y, shade(g[2] if Y < 211 else T['road'], .8 if rnd() < .5 else 1.15))
def _grass(p, rnd, cols=('#6a5a28', '#7e6c30', '#5a4a20')):
    for i in range(60):
        X, Y = int(rnd() * W), 250 + int(rnd() * 18)
        p.R(X, Y, 1, 4, cols[0]); p.R(X - 1, Y + 1, 1, 3, cols[1]); p.R(X + 1, Y + 1, 1, 3, cols[1]); p.R(X - 2, Y + 2, 1, 2, cols[2]); p.R(X + 2, Y + 2, 1, 2, cols[2])
    for i in range(30): X, Y = int(rnd() * W), 212 + int(rnd() * 56); p.R(X, Y, 4, 2, '#5a3a2a'); p.R(X, Y, 3, 1, '#8a6a50')
def _jungle(p, rnd, T):
    g = T['gr']
    # árvores distantes (névoa)
    for layer, (col, top, n, wmin) in enumerate((('#1e3e34', 40, 14, 6), ('#14302a', 20, 10, 9))):
        for i in range(n):
            X = int(rnd() * W); wd = wmin + int(rnd() * 6)
            p.R(X, top + int(rnd() * 30), wd, HZ + 10, col); p.R(X, 0, wd, HZ, col)
            for k in range(6):
                cx, cy = X + int((rnd() - .5) * 50), top + int(rnd() * 60); p.EL(cx, cy, 14 + int(rnd() * 10), 8 + int(rnd() * 5), shade(col, 1.06 + layer * .05))
    p.R(0, HZ, W, H - HZ, g[0]); p.R(0, HZ + 18, W, H - HZ - 18, g[1]); p.R(0, HZ + 40, W, H - HZ - 40, g[2])
    for i in range(1200):
        X, Y = int(rnd() * W), HZ + int(rnd() * (H - HZ)); p.P(X, Y, pick(['#3a4a22', '#2a3a1a', '#4a3a1e', '#5a4a26', '#1a2410']))
    _road(p, rnd, T)
    for i in range(6):  # poças
        X, Y = 60 + int(rnd() * 360), 214 + int(rnd() * 28); p.EL(X, Y, 8 + int(rnd() * 8), 1, '#2a4a44'); p.R(X - 3, Y, 6, 1, '#4a7a70')
    # troncos grandes nas bordas e árvores médias
    for X, wd in ((-6, 30), (60, 14), (176, 10), (300, 12), (448, 34)):
        c0, c1, c2 = '#0e1a12', '#16261a', '#22362a'
        p.R(X, 0, wd, 222, c1); p.R(X, 0, 3, 222, c0); p.R(X + wd - 3, 0, 2, 222, c2)
        for y in range(0, 222, 7):
            p.R(X + 3 + int(rnd() * (wd - 6)), y, 2, 4, c0)
        p.TL(X - 8, 222, X + 2, 200, 4, c1); p.TL(X + wd + 6, 222, X + wd - 2, 200, 4, c1)
        for k in range(3):  # cipós
            vx = X + int(rnd() * wd) + 4; ln = 40 + int(rnd() * 90)
            for y in range(0, ln): p.P(vx + int(math.sin(y / 9) * 2), y, '#2e4a22' if y % 5 else '#4a6a30')
    for i in range(8):  # folhagens no alto
        cx = int(rnd() * W); p.EL(cx, int(rnd() * 20), 30 + int(rnd() * 20), 12 + int(rnd() * 8), pick(['#0c1a10', '#102214', '#14281a']))
    for i in range(30):  # samambaias em primeiro plano
        X, Y = int(rnd() * W), 246 + int(rnd() * 20); col = pick(['#1e3a18', '#2a4a20', '#16301a'])
        for k in range(-4, 5): p.TL(X, Y, X + k * 3, Y - 8 - abs(k), 1, col)
    for i in range(40):
        X, Y = int(rnd() * W), 200 + int(rnd() * 14); p.R(X, Y, 1, 5, '#2a4a20'); p.R(X - 1, Y + 2, 1, 3, '#2a4a20'); p.R(X + 1, Y + 1, 1, 3, '#3a5a26')
    # cruz de madeira e capacete (memorial)
    p.R(380, 186, 3, 24, '#3a2a18'); p.R(374, 192, 15, 3, '#3a2a18'); p.EL(381, 184, 5, 3, '#3e4628'); p.R(376, 186, 11, 1, '#2a3018')
def build_church():
    bg = S(W, H); p = Pt(bg); rr = random.Random(9); rnd = rr.random
    p.R(0, 0, W, H, '#241c22')
    for y in range(0, 214, 12):
        off = 0 if (y // 12) % 2 else 14
        for X in range(-off, W, 28):
            p.R(X, y, 27, 11, pick(['#3a3036', '#362c32', '#3e3439'])); p.R(X, y, 27, 1, '#4a4046'); p.R(X, y + 11, 28, 1, '#1a1418')
    def window(x, y, w, h, big=False):
        p.R(x - 2, y - 2, w + 4, h + 4, '#141014')
        for r in range(w // 2 + 2): p.R(x + r - 2 + (w // 2 - r) * 0, y - 2 - int(math.sqrt(max(0, (w / 2 + 2) ** 2 - (r - w / 2 - 2) ** 2)) / 1.4), 1, 1, '#141014')
        cols = ['#c02828', '#2848b0', '#e0b030', '#2a8a4a', '#8a2aa0']
        for yy in range(y, y + h, 6):
            for xx in range(x, x + w, 6): p.R(xx, yy, 5, 5, pick(cols)); p.P(xx, yy, '#ffffff')
        for yy in range(h // 2 + 1):
            ww = int(round(math.sqrt(max(0, (w / 2) ** 2 - (yy * 1.4) ** 2 / 1.0))))
            p.R(x + w // 2 - ww, y - yy, ww * 2, 1, pick(cols))
        if big: p.R(x + w // 2 - 1, y - h // 2, 3, h + h // 2, '#141014'); p.R(x, y + h // 3, w, 3, '#141014')
    window(60, 50, 30, 70); window(390, 50, 30, 70); window(222, 26, 36, 60, True)
    # luz
    for wx, ww in ((60, 30), (390, 30), (222, 36)):
        for y in range(120, 226):
            X = wx + (y - 120) // 2
            for xx in range(X, X + ww, 2):
                if (xx + y) % 4 == 0: p.P(xx, y, '#5a4c48')
    # cruz e altar
    p.R(236, 92, 8, 60, '#4a2a16'); p.R(222, 104, 36, 8, '#4a2a16'); p.R(236, 92, 2, 60, '#6a4024'); p.R(222, 104, 36, 2, '#6a4024')
    p.R(196, 168, 88, 44, '#4a2a16'); p.R(192, 164, 96, 6, '#5a3420'); p.R(196, 170, 88, 30, '#e8e0d0'); p.R(196, 170, 88, 2, '#ffffff'); p.R(232, 172, 16, 24, '#c8a040'); p.R(238, 176, 4, 16, '#8a1818'); p.R(234, 182, 12, 4, '#8a1818')
    # chão e tapete
    for y in range(212, H, 6):
        for X in range(0, W, 12): p.R(X + (6 if (y // 6) % 2 else 0), y, 12, 6, '#2e262a' if (X // 12 + y // 6) % 2 else '#3a3036')
    p.R(0, 218, W, 16, '#7a1418'); p.R(0, 218, W, 2, '#a02028'); p.R(0, 232, W, 2, '#5a0e10')
    # porta
    p.R(8, 128, 46, 86, '#1a1014'); p.R(10, 130, 42, 84, '#4a2a16')
    for X in range(12, 52, 6): p.R(X, 130, 1, 84, '#2e180c')
    p.R(28, 130, 2, 84, '#1a1014'); p.R(22, 170, 2, 3, '#c8a040'); p.R(34, 170, 2, 3, '#c8a040')
    # bancos (fundo)
    for X in (80, 130, 300, 350):
        p.R(X, 186, 40, 4, '#3a2012'); p.R(X, 190, 40, 14, '#4a2a16'); p.R(X, 190, 40, 1, '#6a4024'); p.R(X + 2, 204, 3, 10, '#2a160c'); p.R(X + 35, 204, 3, 10, '#2a160c')
    return bg
_CHURCH = None
def church_bg():
    global _CHURCH
    if _CHURCH is None: _CHURCH = build_church()
    return _CHURCH
TUMB = None
def tumbleweed():
    global TUMB
    if TUMB is None:
        s = S(17, 17); rr = random.Random(99)
        for i in range(120):
            a, r = rr.random() * 6.28, rr.random() * 7.5; s.fill(C('#9a7840' if rr.random() < .5 else '#6a4e28'), (8 + int(math.cos(a) * r), 8 + int(math.sin(a) * r), 1, 1))
        for i in range(7): a = rr.random() * 6.28; line(s, 8 + math.cos(a) * 8, 8 + math.sin(a) * 8, 8 - math.cos(a) * 7, 8 - math.sin(a) * 7, '#7e6034')
        TUMB = [finalize(s)]
        for k in (1, 2, 3): TUMB.append(pygame.transform.rotate(TUMB[0], 90 * k))
    return TUMB

# ------------------------------------------------------------------ áudio
VDEF = dict(master=.9, music=.7, sfx=.9, voice=1.0, amb=.5)
def VOL(k):
    v = SAVE.get('vol') or {}
    return v.get(k, VDEF[k]) * v.get('master', VDEF['master'])
def on_voice(name, n): pass
SUBS = {}
def load_subs():
    SUBS.clear(); cur = None
    try:
        with open(os.path.join(ASSET, 'legendas.txt'), 'r', encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith('#'): continue
                if ln.startswith('[') and ln.endswith(']'): cur = ln[1:-1].strip(); SUBS[cur] = []; continue
                if cur: SUBS[cur].append(ln.upper())
    except Exception: pass
class Audio:
    def __init__(self):
        self.ok = False; self.snd = {}; self.muted = False; self.cur = None; self.vol = .6; self.tmpv = None; self.ambname = None; self.duckUntil = 0
        try:
            if pygame.mixer.get_init():
                self.ok = True; pygame.mixer.set_num_channels(40); pygame.mixer.set_reserved(2)
                self.ambch = pygame.mixer.Channel(0); self.voicech = pygame.mixer.Channel(1)
                for f in os.listdir(ASSET):
                    if f.endswith(('.ogg', '.wav')) and not f.startswith('mus_'):
                        try: self.snd[f.rsplit('.', 1)[0]] = pygame.mixer.Sound(os.path.join(ASSET, f))
                        except Exception: pass
        except Exception: self.ok = False
    def _mv(self):
        if self.muted: return 0
        v = (self.tmpv if self.tmpv is not None else self.vol) * VOL('music')
        return min(1, v * (.15 if self.duckUntil else 1))
    def _av(self): return 0 if self.muted else (.01 if self.duckUntil else .18 * VOL('amb'))
    def apply(self):
        if not self.ok: return
        try: pygame.mixer.music.set_volume(self._mv()); self.ambch.set_volume(self._av()); self.voicech.set_volume(0 if self.muted else min(1, VOL('voice')))
        except Exception: pass
    def play(self, name, vol=1.0):
        if not self.ok or self.muted: return
        s = self.snd.get(name)
        if s:
            try: s.set_volume(min(1, vol * VOL('sfx'))); s.play()
            except Exception: pass
    def rnd(self, base, n, vol=1.0): self.play('%s%d' % (base, random.randint(1, n)), vol)
    def music(self, name, vol=.6, fade=700):
        if not self.ok: return
        self.vol = vol; self.tmpv = None
        try:
            if name == self.cur: self.apply(); return
            self.cur = name
            if name is None: pygame.mixer.music.fadeout(fade); return
            pygame.mixer.music.load(os.path.join(ASSET, 'mus_%s.ogg' % name)); pygame.mixer.music.set_volume(self._mv()); pygame.mixer.music.play(-1, fade_ms=fade)
        except Exception: pass
    def music_vol(self, v): self.tmpv = v; self.apply()
    def ambient(self, name, vol=.5):
        if not self.ok or name == self.ambname: return
        self.ambname = name
        try:
            if name is None: self.ambch.fadeout(800); return
            s = self.snd.get(name)
            if s: self.ambch.play(s, loops=-1, fade_ms=800); self.ambch.set_volume(self._av())
        except Exception: pass
    def voice(self, name):
        s = self.snd.get(name) if self.ok else None
        n = 0
        try: n = s.get_length() if s else 0
        except Exception: n = 0
        if s and not self.muted:
            try:
                s.set_volume(1.0); self.voicech.play(s); self.duckUntil = pygame.time.get_ticks() + n * 1000 + 250; self.apply()
            except Exception: pass
        on_voice(name, n or 2.5)
        return n
    def tick(self):
        if self.ok and self.duckUntil and pygame.time.get_ticks() > self.duckUntil: self.duckUntil = 0; self.apply()
    def stop_voice(self):
        try: self.voicech.stop()
        except Exception: pass
        self.duckUntil = 0; self.apply(); on_voice(None, 0)
    def length(self, name):
        s = self.snd.get(name)
        try: return s.get_length() if s else 0
        except Exception: return 0
    def toggle(self):
        self.muted = not self.muted; self.apply()
        if self.muted:
            try: self.voicech.stop()
            except Exception: pass

# ------------------------------------------------------------------ progresso salvo
SAVE = dict(money=0, ownW=['rust'], eqW='rust', ownS=['classic'], eqS='classic', best=None, maxLevel=1, sp=0, skills={}, bless=1, active=None, boss1=False, boss2=False, muted=False, vol=dict(VDEF), subs=True)
def load_save():
    try:
        with open(SAVEF, 'r', encoding='utf-8') as f: SAVE.update(json.load(f))
    except Exception: pass
def save():
    try:
        with open(SAVEF, 'w', encoding='utf-8') as f: json.dump(SAVE, f)
    except Exception: pass

SKILLS = [  # (id, nome, máximo, custo base, requisito, coluna, linha, descrição por nível)
    dict(id='reflexo', name='REFLEXO', mx=5, cost=1, req=None, col=0, row=0, desc='+12 MS DE VANTAGEM NO SAQUE'),
    dict(id='recarga', name='MÃO RÁPIDA', mx=3, cost=1, req='reflexo', col=0, row=1, desc='-8% NO TEMPO ENTRE TIROS'),
    dict(id='mira', name='OLHO DE ÁGUIA', mx=4, cost=2, req='recarga', col=0, row=2, desc='+10% CABEÇA NO TIRO PELO TECLADO'),
    dict(id='coracao', name='CORAÇÃO DE PEDRA', mx=2, cost=3, req=None, col=1, row=0, desc='+1 CORAÇÃO MÁXIMO'),
    dict(id='bala', name='TEMPO DE BALA', mx=3, cost=1, req='coracao', col=1, row=1, desc='+25% DE TEMPO PRA DESVIAR'),
    dict(id='sorte', name='SORTE DE DEFUNTO', mx=4, cost=2, req='bala', col=1, row=2, desc='-1% DE CHANCE DA ARMA FALHAR'),
    dict(id='ganancia', name='GANÂNCIA', mx=4, cost=1, req=None, col=2, row=0, desc='+15% DE DINHEIRO'),
    dict(id='carnificina', name='CARNIFICINA', mx=3, cost=2, req='ganancia', col=2, row=1, desc='+8% DE EXPLODIR A CABEÇA'),
    dict(id='pavor', name='PAVOR', mx=3, cost=2, req='carnificina', col=2, row=2, desc='+40 MS DE ATORDOAMENTO NO INIMIGO')]
SKMAP2 = {s['id']: s for s in SKILLS}
def sk(i): return SAVE['skills'].get(i, 0)
def max_hearts(): return 3 + sk('coracao')
CARDS = [dict(id='tempo', rar='LENDÁRIA', name='TEMPO MORTO', col='#f0b830', desc=['INIMIGOS', '35% MAIS', 'LENTOS POR', '3 RODADAS']),
         dict(id='dupla', rar='RARA', name='BALA DUPLA', col='#4a8ae0', desc=['DISPARA 2', 'BALAS DE UMA', 'VEZ POR', '3 RODADAS']),
         dict(id='fe', rar='COMUM', name='FÉ NO AÇO', col='#b8b8c0', desc=['SUA ARMA', 'NÃO FALHA', 'POR', '3 RODADAS'])]
def bless(i): a = SAVE.get('active'); return bool(a and a.get('type') == i and a.get('rounds', 0) > 0)

# ------------------------------------------------------------------ estado do jogo
class Actor:
    def __init__(self, kind, x, face):
        self.kind, self.x, self.face = kind, x, face
        self.pose = 'idle'; self.poseT = 0; self.rot = 0.; self.rotV = 0.; self.dying = False; self.dead = False; self.landed = False; self.flash = 0.
        self.hat = True; self.bob = 0; self.recoil = 0.; self.offX = 0.; self.gone = False; self.pool = 0.; self.headless = False
        self.dodge = None; self.dodgeT = 0.; self.jy = 0.; self.hidden = False; self.ammo = 0; self.nextShot = 0; self.fount = 0.
class G: pass
g = G()
g.S = 'title'; g.T = 0.; g.time = 0.; g.D = None; g.P = None; g.E = None; g.parts = []; g.tumble = None; g.shake = 0.; g.fade = 0.; g.fadeDir = 0; g.fadeTo = None
g.menu = None; g.mouse = (-99, -99); g.mouse_in = False; g.returnTo = 'title'; g.shopSel = 0; g.wardSel = 0; g.skillSel = 0; g.toast = None; g.theme = 'sunset'
g.tscale = 1.; g.buttons = []; g.ch = None; g.lvsel = 0
RUN = dict(level=1, hearts=3, wins=0)
audio = None
canvas = None
DEC = None
SPR_TOP = GY - FY - 1

def st(s): g.S = s; g.T = 0.
def fmt(t): return ('%.3f' % t).replace('.', ',') + ' S'
def rating(t): return 'RELÂMPAGO!' if t < .2 else 'MÃO LIGEIRA!' if t < .25 else 'BELO SAQUE!' if t < .32 else 'NADA MAL' if t < .42 else 'POR UM TRIZ'
def say(t): g.D.say = t; g.D.sayT = 0.
def addp(**o):
    p = dict(x=0., y=0., vx=0., vy=0., g=0., life=1., c=(255, 255, 255, 255), s=1, type='px', rot=0., vr=0., ground=None)
    p.update(o)
    if isinstance(p['c'], str): p['c'] = C(p['c'])
    p['max'] = p['life']; g.parts.append(p)
def cur_w():
    w = dict(WMAP[SAVE['eqW']]); w['cad'] = w['cad'] * (1 - .08 * sk('recarga')); return w
def toast(t, bad=False): g.toast = dict(t=t, time=1.4, bad=bad)

class Duel: pass
def demo_scene():
    g.theme = 'sunset'; op = ENEMIES[0]; D = Duel(); D.op = op; D.es = enemy_sprites(op); D.ev = []; D.flashes = []; D.tracers = []; D.wounds = []; D.L = 1; D.hp = 1; D.hpMax = 1
    D.say = ''; D.sayT = 9; D.coffin = None; D.bullet = None
    g.D = D; g.P = Actor('skel', 118, 1); g.E = Actor('enemy', 362, -1); g.parts = []; g.tumble = None; DEC.fill((0, 0, 0, 0))
def start_duel():
    L = RUN['level']; op = enemy_for(L); g.theme = theme_for(L); build_bg(g.theme)
    SAVE['maxLevel'] = max(SAVE['maxLevel'], L); save()
    D = Duel(); D.L = L; D.op = op; D.es = enemy_sprites(op); D.ev = []; D.goTime = 0; D.enemyAt = 1e18; D.result = None; D.rt = None; D.say = ''; D.sayT = 9
    D.nextStep = 0; D.beat = 0; D.flashes = []; D.tracers = []; D.big = None; D.slow = 1.35 if bless('tempo') else 1.0
    D.delay = (op['delay'] + (RND() * .05 - .025)) * D.slow; D.hp = op['hp']; D.hpMax = op['hp']; D.wounds = []; D.shots = 0; D.heads = 0; D.missed = 0; D.bonus = []
    D.shown = False; D.coffin = None; D.bullet = None; D.jam = None; D.msg = None; D.msgT = 0; D.walkf = -1
    g.D = D; P = Actor('skel', -30, 1); E = Actor('enemy', W + 30, -1); P.ammo = cur_w()['ammo']; P.nextShot = 0
    if op.get('boss') == 'krieger': E.x = 362; E.hidden = True; E.rot = math.pi / 2
    g.P, g.E = P, E; g.parts = []; g.tumble = None; DEC.fill((0, 0, 0, 0))
    for q in ('idle', 'walk0', 'walk1', 'walk2', 'walk3', 'reach', 'draw', 'aim', 'recoil', 'crouch'): ze(q)
    st('intro'); g.tscale = 1.
    if op.get('boss'): audio.music(op['music'], .55)
    else: audio.music('western' if g.theme in ('night', 'dusk', 'amazon') else 'country', .4)
    audio.ambient('amb_jungle' if g.theme == 'amazon' else 'amb_wind', .5)
    if op.get('boss') == 'fire': D.ev.append(dict(at=.9, fn=lambda: audio.play('roar')))
def goto(s):
    if g.fadeDir: return
    g.fadeTo = s; g.fadeDir = 1
def on_enter(s):
    g.menu = None; g.sub = None
    if s == 'title': demo_scene(); st('title'); audio.music('country', .6); audio.ambient('amb_wind', .4)
    elif s == 'intro': start_duel()
    elif s in ('win', 'lose'):
        D = g.D; first = not D.shown; D.shown = True; st(s)
        if first:
            a = SAVE.get('active')
            if a: a['rounds'] -= 1; SAVE['active'] = a if a['rounds'] > 0 else None; save()
            audio.ambient(None)
            if s == 'win':
                audio.play('win'); audio.music(None)
                D.ev2 = [dict(at=.7, fn=lambda: audio.voice('ze'))] if RUN['wins'] % 3 == 0 else []
                D.ev2.append(dict(at=3.2, fn=lambda: audio.music('country', .45)))
            else:
                audio.play('lose'); audio.music(None); D.ev2 = [dict(at=2.6, fn=lambda: audio.music('western', .32))]
    elif s == 'shop': st('shop'); g.shopSel = max(0, [w['id'] for w in WEAP].index(SAVE['eqW']) if SAVE['eqW'] in [w['id'] for w in WEAP] else 0)
    elif s == 'wardrobe': st('wardrobe'); g.wardSel = max(0, [k['id'] for k in SKINS].index(SAVE['eqS']))
    elif s == 'skills': st('skills')
    elif s == 'levelsel': st('levelsel'); g.lvsel = 0
    elif s == 'church': start_church()
    elif s == 'settings': st('settings'); g.setSel = 0
    elif s == 'debug': st('debug')
def new_run(level=1):
    RUN['level'] = level; RUN['hearts'] = max_hearts(); RUN['wins'] = 0; goto('intro')
def play_pressed():
    if SAVE['maxLevel'] >= 10: goto('levelsel')
    else: new_run(1)

# ------------------------------------------------------------------ combate
def eSpr():
    E = g.E; d = g.D.es.d; q = E.pose
    if E.headless and q + '_x' in d: q += '_x'
    elif not E.hat and q + '_nh' in d: q += '_nh'
    return d.get(q, d['idle'])
def to_world(a, lx, ly): return (a.x + a.face * (lx - AX) + a.offX, SPR_TOP + ly + a.bob - a.jy)
def muzzle_fx(a, spr, i=0):
    m = spr.muz[i] if i < len(spr.muz) else (spr.muz[0] if spr.muz else (AX + 30, 40))
    x, y = to_world(a, m[0], m[1]); g.D.flashes.append(dict(x=x, y=y, d=a.face, t=.08))
    for k in range(10): addp(type='smoke', x=x + a.face * 2, y=y, vx=a.face * (10 + RND() * 30), vy=-8 - RND() * 14, life=.9 + RND() * .6, s=2, c='#d8d0c4')
    for k in range(6): addp(x=x, y=y, vx=a.face * (60 + RND() * 140), vy=(RND() - .5) * 80, life=.15 + RND() * .15, c='#fff4a0' if k % 2 else '#f8a030')
    return x, y
BLOOD = ['#c01010', '#9a0a0a', '#e01a1a', '#6a0606']
def blood_spray(x, y, d, n, head, fire=False):
    for i in range(n):
        back = i < n * .65; sp = (60 + RND() * 170) if back else (20 + RND() * 60); ang = (RND() - .5) * (1.6 if head else 1.1) - (.35 if head else .1)
        addp(type='blood', x=x, y=y, vx=(d if back else -d) * sp * math.cos(ang), vy=sp * math.sin(ang) - RND() * 60, g=430, life=2, s=2 if RND() < .3 else 1,
             c='#ff7a1a' if fire and RND() < .4 else pick(BLOOD), ground=GY + (RND() * 10 - 4))
    for i in range(5): addp(type='smoke', x=x, y=y, vx=d * (20 + RND() * 30), vy=-RND() * 10, life=.5, s=2, c='#8a1010')
def bone_chips(x, y, d, n):
    for i in range(n): addp(x=x, y=y, vx=d * (40 + RND() * 150), vy=-40 - RND() * 100, g=400, life=1.5, s=2 if RND() < .4 else 1, c=pick(['#efe6cd', '#c8bea4', '#ffffff']), ground=GY + (RND() * 6 - 2))
def hit_test(sx, sy):
    E = g.E; es = g.D.es
    lx = int(round(AX + (sx - E.x - E.offX) * E.face)); ly = int(round(sy - SPR_TOP - E.bob))
    def at(m, X, Y, h): return 0 <= X < SPW and 0 <= Y < h and m[Y * SPW + X]
    for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        if at(es.mask, lx + ox, ly + oy, SPH):
            if E.headless and ly + oy <= 36: continue
            return dict(type='head' if ly + oy <= 36 else 'body', lx=lx + ox, ly=ly + oy)
    if E.hat and es.hat:
        for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if at(es.hatmask, lx + ox, ly + oy, 30): return dict(type='hat', lx=lx, ly=ly)
    return dict(type='miss', lx=lx, ly=ly)
def misfire_chance():
    if bless('fe'): return 0
    return max(0., .05 - .01 * sk('sorte'))
def player_fire(aim):
    D, P, E = g.D, g.P, g.E; now = pygame.time.get_ticks(); w = cur_w()
    if now < P.nextShot: return
    if P.ammo <= 0: audio.play('empty'); P.nextShot = now + 150; return
    if D.rt is None: D.rt = (now - D.goTime) / 1000
    if RND() < misfire_chance(): start_jam(); return
    P.ammo -= 1; D.shots += 1; P.nextShot = now + w['cad'] * 1000; P.pose = 'recoil'; P.poseT = .09
    audio.play('holster', .7); audio.play('shot_heavy' if w.get('shotgun') else 'shot')
    spr = ze('recoil'); n = (2 if w.get('dual') else 1) + (1 if bless('dupla') else 0) + (w.get('multi', 1) - 1)
    for k in range(n):
        mx, my = muzzle_fx(P, spr, k % max(1, len(spr.muz)))
        if aim:
            jx, jy = ((RND() - .5) * 8, (RND() - .5) * 10) if k else (0, 0)
            hit = hit_test(aim[0] + jx, aim[1] + jy)
            if w.get('shotgun') and hit['type'] == 'miss': hit = hit_test(aim[0] + (RND() - .5) * 14, aim[1] + (RND() - .5) * 14)
        else:
            if (bless('lince') or RND() < .10 * sk('mira')) and not E.headless:
                hl = [t for t in D.es.edge if t[1] <= 34 and t[1] >= 22] or [(AX, 28)]; t = pick(hl); hit = dict(type='head', lx=t[0], ly=t[1])
            else: t = pick(D.es.torso); hit = dict(type='body', lx=t[0], ly=t[1])
        if hit['type'] in ('miss', 'hat'):
            tx, ty = aim if aim else (E.x, GY - 50)
            D.tracers.append(dict(x1=mx, y1=my, x2=tx + (tx - mx) * .6, y2=ty + (ty - my) * .6, t=.06)); D.missed += 1
            if hit['type'] == 'hat' and E.hat: E.hat = False; hat_fly(); D.bonus.append('CHAPÉU NO CHÃO!')
            elif RND() < .6: D.ev.append(dict(at=g.T + .1 + RND() * .1, fn=lambda: audio.play('ricochet')))
            continue
        wx, wy = to_world(E, hit['lx'], hit['ly']); D.tracers.append(dict(x1=mx, y1=my, x2=wx, y2=wy, t=.06))
        apply_hit(hit, w['dmg'] * (2 if hit['type'] == 'head' else 1), now)
        if D.hp <= 0: break
def hat_fly():
    es = g.D.es
    if not es.hat: return
    E = g.E; x, y = to_world(E, AX + 1, 16)
    addp(type='spr', spr=es.hat, x=x, y=y, vx=-E.face * (40 + RND() * 40), vy=-140, vr=-E.face * 8, g=340, life=5, ground=GY - 6, face=E.face, ox=AX + 1, oy=16)
    audio.play('hat')
def apply_hit(hit, dmg, now):
    D, E = g.D, g.E; head = hit['type'] == 'head'; wx, wy = to_world(E, hit['lx'], hit['ly']); skel = D.op['s']['kind'] == 'skel'
    lethal = D.hp - dmg <= 0
    explode = head and (RND() < .25 + .08 * sk('carnificina') or cur_w().get('boom') or getattr(g, 'forceExplode', False)) and (not D.op.get('boss') or lethal or getattr(g, 'forceExplode', False))
    D.wounds.append(dict(x=hit['lx'], y=hit['ly'], t=g.time, head=head))
    D.hp = 0 if explode else D.hp - dmg
    if head: D.heads += 1
    E.flash = .08; E.recoil = 1.; g.shake = 6 if head else 4; audio.play('flesh_head' if head else 'flesh')
    if skel: bone_chips(wx, wy, -E.face, 30 if head else 18); [addp(type='smoke', x=wx, y=wy, vx=-E.face * 20, vy=-10, life=.6, s=2, c='#6a6a5a') for i in range(6)]
    else: blood_spray(wx, wy, -E.face, 70 if head else 44, head, D.op.get('boss') == 'fire')
    if explode: explode_head(skel)
    elif head and E.hat: E.hat = False; hat_fly()
    if D.hp <= 0: enemy_die(head, explode); return
    D.enemyAt = max(D.enemyAt, now + (D.op.get('stagger', .36) + .04 * sk('pavor')) * 1000); E.pose = 'idle'
    say('¡AARGH!' if D.op.get('lang') == 'es' else 'ARGH!')
def explode_head(skel):
    D, E = g.D, g.E; x, y = to_world(E, AX + 1, 27)
    if E.hat: E.hat = False; hat_fly()
    E.headless = True; E.fount = 1.2; g.shake = 9; audio.play('explode')
    for i in range(36 if not skel else 10):
        addp(type='blood', x=x, y=y, vx=(RND() - .5) * 260, vy=-60 - RND() * 220, g=430, life=2.5, s=2 if RND() < .5 else 1, c=pick(BLOOD), ground=GY + (RND() * 12 - 5))
    for i in range(16):
        addp(type='chunk', x=x, y=y, vx=(RND() - .5) * 220 - E.face * 60, vy=-80 - RND() * 200, g=430, life=4, s=2 + int(RND() * 2), vr=(RND() - .5) * 20,
             c=pick(['#efe6cd', '#d8cfb6', '#c8bea4']) if skel or RND() < .3 else pick(['#8a0a0a', '#c02a2a', '#e07070', '#5a0404']), ground=GY + (RND() * 10 - 4))
    for i in range(10): addp(type='smoke', x=x, y=y, vx=(RND() - .5) * 60, vy=-RND() * 30, life=.9, s=3, c='#9a1010' if not skel else '#8a8a7a')
    D.bonus.append('CABEÇA EXPLODIU!')
def enemy_die(head, explode=False):
    D, E = g.D, g.E; D.result = 'win'; st('resolve'); L = D.L; boss = D.op.get('boss')
    reward = 60 + 30 * L; bon = []; extra = 0
    if explode: extra += 100; bon.append('CABEÇA EXPLODIU +$100')
    elif head: extra += 50; bon.append('TIRO NA CABEÇA +$50')
    if D.rt is not None and D.rt < .25: extra += 80; bon.append('MÃO LIGEIRA +$80')
    if not D.missed and D.shots > 0: extra += 30; bon.append('SEM ERRAR +$30')
    if boss: extra += 1000; bon.append('CHEFÃO DERROTADO +$1000')
    D.reward = int((reward + extra) * (1 + .15 * sk('ganancia')) * (1.5 if bless('bolso') else 1)); D.bonusList = bon; SAVE['money'] += D.reward; RUN['wins'] += 1
    SAVE['sp'] += 1 + (3 if boss else 0); D.heal = False
    if RUN['wins'] % 5 == 0 and RUN['hearts'] < max_hearts(): RUN['hearts'] += 1; D.heal = True
    if D.rt is not None and (SAVE['best'] is None or D.rt < SAVE['best']): SAVE['best'] = D.rt; D.newBest = True
    else: D.newBest = False
    D.unlock = False
    if boss:
        SAVE['bless'] += 1
        if boss == 'fire' and not SAVE['boss1']:
            SAVE['boss1'] = True; D.unlock = True
            if 'ouro' not in SAVE['ownS']: SAVE['ownS'].append('ouro')
        if boss == 'krieger': SAVE['boss2'] = True
    save()
    D.big = dict(txt=fmt(D.rt or 0), sub='CABEÇA EXPLODIU!' if explode else 'TIRO NA CABEÇA!' if head else rating(D.rt if D.rt is not None else 1))
    if boss == 'fire':
        D.ev = [dict(at=.4, fn=lambda: say('¡NO... PUEDE... SER!')), dict(at=1.4, fn=disintegrate)]; D.endAt = 4.2
    elif D.op['s']['kind'] == 'skel':
        D.ev = [dict(at=.25, fn=lambda: say('...')), dict(at=.6, fn=crumble)]; D.endAt = 3.6
    else:
        def discharge():
            mx, my = muzzle_fx(E, eSpr()); audio.play('shot'); audio.play('ricochet'); sparks(mx - E.face * 14, GY - 1)
        D.ev = [dict(at=.1, fn=lambda: setattr(E, 'pose', 'draw')), dict(at=.2, fn=lambda: setattr(E, 'dying', True)), dict(at=.36, fn=discharge)]; D.endAt = 3.2
def crumble():
    E = g.E; E.dead = True; audio.play('rattle'); g.shake = 5
    x, y = to_world(E, AX, 50); dust_puff(E.x, GY - 2, 20)
    for i in range(16): addp(type='bone', x=x + (RND() - .5) * 20, y=y + (RND() - .5) * 40, vx=(RND() - .5) * 160, vy=-60 - RND() * 120, vr=(RND() - .5) * 20, g=400, life=5, ground=GY - 1)
def disintegrate():
    E = g.E; spr = eSpr().s; b = tob(spr); audio.play('burst'); g.shake = 6
    for y in range(SPH):
        for x in range(SPW):
            j = (y * SPW + x) * 4
            if not b[j + 3] or RND() < .45: continue
            px, py = to_world(E, x, y)
            c = pick(['#ff7a1a', '#ffc040', '#ff4a10']) if RND() < .25 else (b[j] >> 1, b[j + 1] >> 1, b[j + 2] >> 1, 255)
            addp(type='ash', x=px, y=py, vx=30 + RND() * 90, vy=-20 - RND() * 60, g=-15, life=1 + RND() * 2.2, c=c)
    E.gone = True
def sparks(x, y):
    for i in range(14): addp(x=x, y=y, vx=(RND() - .5) * 160, vy=-40 - RND() * 120, g=300, life=.4 + RND() * .3, c='#ffe080' if i % 3 else '#ffffff', ground=GY + 4)
    for i in range(6): addp(type='smoke', x=x, y=y, vx=(RND() - .5) * 20, vy=-10 - RND() * 10, life=.8, s=2, c='#c89870')
def dust_puff(x, y, n=14):
    for i in range(n): addp(type='smoke', x=x + (RND() - .5) * 30, y=y, vx=(RND() - .5) * 50, vy=-5 - RND() * 20, life=.8 + RND() * .5, s=3, c='#d4a070')
def skel_die():
    P, D = g.P, g.D; P.flash = .12; g.shake = 6; t = pick([(AX + 1, 48), (AX + 2, 54), (AX, 44), (AX + 1, 26)]); x, y = to_world(P, *t); bone_chips(x, y, 1, 20)
    def fall():
        P.dead = True; P.dodge = None; P.jy = 0; audio.play('rattle'); dust_puff(P.x, GY - 2, 10)
        for i in range(12): addp(type='bone', x=P.x + (RND() - .5) * 10, y=GY - 40 + RND() * 24, vx=(RND() - .5) * 140, vy=-60 - RND() * 100, vr=(RND() - .5) * 20, g=400, life=4, ground=GY - 1)
    D.ev.append(dict(at=g.T + .1, fn=fall))
def enemy_fire(kill=True):
    D, E, P = g.D, g.E, g.P; E.pose = 'recoil'; E.poseT = .1; spr = eSpr(); n = len(spr.muz) or 1
    rifle = D.op['wid'] == 'rifle'
    shots = 3 if rifle else n
    for k in range(shots):
        def f(k=k):
            if not g.D: return
            audio.play('rifle' if rifle else 'shot'); mx, my = muzzle_fx(E, eSpr(), k % n); D.tracers.append(dict(x1=mx, y1=my, x2=P.x + 2, y2=GY - 52 + k * 6, t=.06))
        D.ev.append(dict(at=g.T + k * (.07 if rifle else .09), fn=f))
    if kill: RUN['hearts'] = max(0, RUN['hearts'] - 1); skel_die()
def enemy_shoots():
    D = g.D; D.result = 'slow'; st('resolve'); D.ev = []; D.big = dict(txt='LENTO DEMAIS!', red=True); enemy_fire(); D.endAt = 3.0
    D.ev.append(dict(at=.3, fn=lambda: (audio.play('ricochet'), sparks(466, 204))))
    if D.op.get('boss') == 'fire': D.ev.append(dict(at=.6, fn=lambda: say('¡ADIÓS, CALAVERA!')))
    if D.op.get('boss') == 'krieger': D.ev.append(dict(at=.6, fn=lambda: say('ALVO ABATIDO.')))
def foul():
    D, E, P = g.D, g.E, g.P; D.result = 'foul'; st('resolve'); D.ev = []; P.pose = 'aim'; audio.play('holster')
    say('¡TRAMPOSO!' if D.op.get('lang') == 'es' else 'TRAPAÇA!'); D.big = dict(txt='CEDO DEMAIS!', red=True)
    D.ev += [dict(at=.22, fn=lambda: setattr(E, 'pose', 'draw')), dict(at=.36, fn=enemy_fire), dict(at=.68, fn=lambda: (audio.play('ricochet'), sparks(466, 204)))]; D.endAt = 3.0
# ---- arma falhou: câmera lenta + desvio
def start_jam():
    D, E, P = g.D, g.E, g.P; st('jam'); audio.play('jam'); audio.play('slowmo_in'); audio.music_vol(.12)
    key = random.choice(['a', 'd']); win = .8 * (1 + .25 * sk('bala'))
    D.jam = dict(real=0., key=key, res=None, win=win, fired=False, prog=0., passed=False, endAt=None, y=GY - 74 if key == 'a' else GY - 16)
    D.msg = 'FALHOU!'; D.msgT = 0; P.pose = 'aim'
def jam_fire():
    D, E = g.D, g.E; j = D.jam; j['fired'] = True; E.pose = 'recoil'; E.poseT = .25; spr = eSpr()
    audio.play('rifle' if D.op['wid'] == 'rifle' else 'shot'); mx, my = muzzle_fx(E, spr, 0); j['x0'] = mx; j['y0'] = my
def jam_dodge(key):
    D, P = g.D, g.P; j = D.jam
    if not j or j['res'] is not None: return
    j['res'] = 'ok' if key == j['key'] else 'bad'; P.dodge = 'duck' if key == 'a' else 'jump'; P.dodgeT = 0.; audio.play('whoosh')
def jam_update(rdt):
    D, E, P = g.D, g.E, g.P; j = D.jam; j['real'] += rdt
    g.tscale = max(.12, g.tscale - rdt * 6) if not j['endAt'] else min(1., g.tscale + rdt * 4)
    if not j['fired'] and j['real'] >= .18: jam_fire()
    if j['fired'] and not j['endAt']:
        j['prog'] = (j['real'] - .18) / j['win']
        if j['prog'] >= 1 and not j['passed']:
            j['passed'] = True
            if j['res'] == 'ok':
                D.msg = 'DESVIOU!'; D.msgT = 0; audio.play('whoosh'); j['endAt'] = j['real'] + .55
            else:
                j['endAt'] = 1e9; audio.music_vol(None); audio.play('slowmo_out'); g.tscale = 1.
                jam_fail(); return
    if j['passed'] and j['res'] == 'ok':
        j['prog'] += rdt / j['win']
        if j['endAt'] and j['real'] >= j['endAt']:
            now = pygame.time.get_ticks(); audio.play('slowmo_out'); audio.music_vol(None)
            D.jam = None; st('go'); g.tscale = 1.; P.pose = 'aim'; P.dodge = None; P.jy = 0; P.nextShot = now + 250; E.pose = 'idle'
            D.enemyAt = now + (D.delay + .25 - cur_w()['saque']) * 1000 + 12 * sk('reflexo'); D.msg = 'ARMA DESTRAVADA!'; D.msgT = 0

# ------------------------------------------------------------------ igreja
def start_church():
    st('church'); g.ch = dict(phase='enter', t=0., slots=draw_cards(), swaps=[], sel=1, picked=None, flipped=[False, False, False], fl=[0., 0., 0.], cardY=-200., zx=20.)
    g.chP = Actor('skel', 20, 1); g.chPriest = Actor('enemy', 330, -1); g.parts = []
    audio.music('church', .5); audio.ambient(None)
    if not hasattr(g, 'priest'): g.priest = build_char(PRIEST_S, 'idle', WMAP['priest'])
SLOTX = (150, 240, 330)
def church_update(dt):
    c = g.ch; c['t'] += dt; ph = c['phase']; t = c['t']; Z = g.chP
    if ph == 'enter':
        Z.x = lerp(20, 170, ease(min(1, t / 3.))); Z.pose = 'walk%d' % (int(t * 8) % 4) if t < 3 else 'idle'
        f = int(t * 8) % 4
        if t < 3 and f in (0, 2) and c.get('lf') != f: audio.play('step', .6)
        c['lf'] = f
        if t > 3.4: c['phase'] = 'bless'; c['t'] = 0; audio.play('bless')
    elif ph == 'bless':
        if t > 2.6: c['phase'] = 'show'; c['t'] = 0
    elif ph == 'show':
        c['cardY'] = lerp(300, 16, ease(min(1, t / 1.)));
        if t > 2.2: c['phase'] = 'flip'; c['t'] = 0; audio.play('card')
    elif ph == 'flip':
        if t > .5: c['phase'] = 'shuffle'; c['t'] = 0; c['swaps'] = []
    elif ph == 'shuffle':
        n = int(t / .24)
        if n > len(c['swaps']) - 1 and len(c['swaps']) < c.setdefault('nsw', random.randint(11, 15)):
            i, j = random.sample([0, 1, 2], 2); c['swaps'].append((i, j, t)); audio.play('shuffle')
            s = c['slots']; s[i], s[j] = s[j], s[i]
        if t > c['nsw'] * .24 + .4: random.shuffle(c['slots']); c['phase'] = 'pick'; c['t'] = 0
    elif ph == 'reveal':
        if t > 1.6: c['phase'] = 'done'; c['t'] = 0
    if random.random() < dt * 6:
        x, y = to_world_c(g.chPriest, AX + 10, 32); addp(type='smoke', x=x, y=y, vx=4 + RND() * 6, vy=-12 - RND() * 8, life=1.4, s=1, c='#d8d4cc')
def to_world_c(a, lx, ly): return (a.x + a.face * (lx - AX), SPR_TOP + ly)
def church_pick(slot):
    c = g.ch
    if c['phase'] != 'pick': return
    card = c['slots'].index(slot) if False else None
    c['picked'] = slot; c['phase'] = 'reveal'; c['t'] = 0; audio.play('card')
    ci = c['slots'][slot]; cd = CARDS[ci]
    SAVE['active'] = dict(type=cd['id'], rounds=3); SAVE['bless'] = max(0, SAVE['bless'] - 1); save()
    audio.play('bless' if CARDS[ci]['rar'] in ('LENDÁRIA', 'ÉPICA') else 'buy')
def card_pos(slot):
    """posição x de uma carta durante o embaralhar"""
    c = g.ch; x = SLOTX[slot]; y = c['cardY']
    return x, y
DUEL_STATES = ('intro', 'rise', 'dialog', 'standoff', 'count', 'go', 'resolve', 'jam')

# ------------------------------------------------------------------ atualização
def begin_count():
    D = g.D; L = D.L; iv = max(.42, 1.05 - .07 * (L - 1)); es = D.op.get('lang') == 'es'
    wd = ['UNO...', 'DOS...', '¡TRES!', 'DOS Y MEDIO...'] if es else ['1...', '2...', '3!', '2 E MEIO...']
    seq = [dict(t=0., txt=wd[0], num='1')]; t = iv * (.9 + RND() * .2); seq.append(dict(t=t, txt=wd[1], num='2'))
    if L >= 3 and RND() < min(.5, .12 + .04 * L): t += iv * (.9 + RND() * .2); seq.append(dict(t=t, txt=wd[3], num='2,5'))
    t += iv * .5 + RND() * max(.5, 2.3 - .15 * L); seq.append(dict(t=t, txt=wd[2], go=True))
    D.seq = seq; D.beat = seq[1]['t'] + .35; D.num = None; st('count')
def update(rdt):
    g.time += rdt
    if g.toast: g.toast['time'] -= rdt
    if g.fadeDir == 1:
        g.fade += rdt * 3.2
        if g.fade >= 1: g.fade = 1; g.fadeDir = -1; on_enter(g.fadeTo)
    elif g.fadeDir == -1:
        g.fade -= rdt * 3.2
        if g.fade <= 0: g.fade = 0; g.fadeDir = 0
    D, P, E = g.D, g.P, g.E
    if g.S == 'jam' and D and D.jam: jam_update(rdt)
    extra_update(rdt)
    dt = rdt * g.tscale; g.T += dt
    now = pygame.time.get_ticks()
    if g.S == 'church': church_update(rdt)
    if g.S == 'intro': intro_update(dt, now)
    elif g.S == 'rise':
        T = g.T; c = D.coffin; g.shake = max(g.shake, 2.2 if T < 1.6 else 0)
        c['y'] = lerp(GY + 26, GY, ease(min(1, T / 1.4)))
        if T < 1.5 and RND() < .5: dust_puff(E.x + 40 + (RND() - .5) * 90, GY - 2, 1)
        if T > 1.6 and c['lid']:
            c['lid'] = False; audio.play('lid'); g.shake = 5
            addp(type='lid', x=E.x + 40, y=GY - 14, vx=70, vy=-160, vr=4, g=380, life=6, ground=GY - 3)
            for i in range(20): addp(type='smoke', x=E.x + 40 + (RND() - .5) * 80, y=GY - 8, vx=(RND() - .5) * 40, vy=-10 - RND() * 30, life=1.4, s=3, c='#5a6a4a')
        if T > 1.8:
            E.hidden = False; E.rot = (math.pi / 2) * (1 - ease(min(1, (T - 1.8) / 1.4)))
        if T > 1.8 and not D.__dict__.get('rattled'): D.rattled = True; audio.play('rattle')
        if T > 3.8: E.rot = 0; start_dialog()
    elif g.S == 'dialog':
        if g.T > D.dlgLen: begin_standoff()
    elif g.S == 'standoff':
        if g.T > 2.0: begin_count()
    elif g.S == 'count':
        for q in D.seq:
            if not q.get('done') and g.T >= q['t']:
                q['done'] = True
                if q.get('go'):
                    D.goTime = now; D.enemyAt = now + (D.delay - cur_w()['saque']) * 1000 + 12 * sk('reflexo'); say(q['txt']); D.num = None; audio.play('bell_hi'); st('go'); g.shake = 1.5; break
                say(q['txt']); D.num = q['num']; audio.play('bell')
        if g.S == 'count' and D.seq[1].get('done') and g.T >= D.beat: audio.play('heart'); D.beat += .72
    elif g.S == 'go':
        tl = D.enemyAt - now
        if tl < 170 and E.pose == 'idle': E.pose = 'reach'
        if tl < 90 and E.pose == 'reach': E.pose = 'draw'
        if now >= D.enemyAt: enemy_shoots()
    if g.S == 'resolve':
        for ev in D.ev:
            if not ev.get('done') and g.T >= ev['at']: ev['done'] = True; ev['fn']()
        if g.T > D.endAt: goto('win' if D.result == 'win' else 'lose')
    elif D and g.S in ('intro', 'rise', 'dialog', 'go', 'count', 'standoff', 'jam'):
        for ev in D.ev:
            if not ev.get('done') and g.T >= ev['at']: ev['done'] = True; ev['fn']()
    if g.S in ('win', 'lose') and D and getattr(D, 'ev2', None):
        for ev in D.ev2:
            if not ev.get('done') and g.T >= ev['at']: ev['done'] = True; ev['fn']()
    if E and E.dying and not E.landed:
        E.rotV += 10 * dt; E.rot = min(math.pi / 2, E.rot + E.rotV * dt)
        if E.rot >= math.pi / 2: E.landed = True; audio.play('thud'); g.shake = 3; dust_puff(E.x - E.face * 40, GY - 2, 18)
    if E and E.landed: E.pool = min(1, E.pool + dt * .35)
    for a in (P, E):
        if not a: continue
        a.recoil = max(0, a.recoil - dt * 5); a.offX = -a.face * a.recoil * 3; a.flash = max(0, a.flash - dt)
        if a.poseT > 0:
            a.poseT -= dt
            if a.poseT <= 0 and a.pose == 'recoil': a.pose = 'aim'
    if P and P.dodge:
        P.dodgeT += rdt
        if P.dodge == 'jump': k = min(1, P.dodgeT / .7); P.jy = math.sin(math.pi * k) * 30
        if P.dodgeT > .75 and g.S != 'jam': P.dodge = None; P.jy = 0
    if D:
        D.flashes = [f for f in D.flashes if (f.__setitem__('t', f['t'] - dt) or f['t'] > 0)]
        D.tracers = [f for f in D.tracers if (f.__setitem__('t', f['t'] - dt) or f['t'] > 0)]
        D.sayT = getattr(D, 'sayT', 0) + dt
        if getattr(D, 'msg', None): D.msgT += rdt
        if D.wounds and E and not E.gone and not E.dead and D.op['s']['kind'] != 'skel':
            for w in D.wounds:
                if RND() < dt * (1.5 if E.landed else 4):
                    x, y = (E.x - E.face * (FY + 1 - w['y']), GY - 8) if E.landed else to_world(E, w['x'], w['y'])
                    addp(type='blood', x=x, y=y + 1, vx=(RND() - .5) * 8, vy=10, g=300, life=2, c='#9a0a0a', ground=GY + (RND() * 6 - 2))
        if E and E.fount > 0 and not E.gone:
            E.fount -= dt
            for i in range(3):
                if E.landed: x, y = E.x - E.face * 64, GY - 10
                else: x, y = to_world(E, AX + 1, 33)
                addp(type='blood', x=x, y=y, vx=(RND() - .5) * 40 - E.face * 20, vy=-90 - RND() * 90, g=430, life=2, c=pick(BLOOD), ground=GY + (RND() * 8 - 3))
        if D.op and D.op.get('boss') == 'fire' and E and not E.gone and g.S in DUEL_STATES:
            fp = D.es.edge
            for i in range(3):
                q = pick(fp)
                if E.rot: x, y = E.x - E.face * (FY + 1 - q[1]) * math.sin(E.rot), GY - 6
                else: x, y = to_world(E, q[0], q[1])
                addp(type='fire', x=x + (RND() - .5) * 2, y=y, vx=(RND() - .5) * 10 + 8, vy=-30 - RND() * 40, life=.35 + RND() * .4, s=2 if RND() < .5 else 1)
            if RND() < dt * 8: audio.rnd('crackle', 3, .5)
    if g.theme == 'inferno' and g.S in DUEL_STATES and RND() < dt * 20: addp(type='ember', x=RND() * W, y=H + 2, vx=10 + RND() * 30, vy=-30 - RND() * 50, life=4, c=pick(['#ff7a1a', '#ffc040', '#ff4a10']))
    if g.theme == 'amazon' and g.S not in ('title', 'shop', 'wardrobe', 'skills', 'levelsel', 'church', 'win', 'lose') and RND() < dt * 4:
        addp(type='firefly', x=RND() * W, y=120 + RND() * 110, vx=(RND() - .5) * 12, vy=(RND() - .5) * 8, life=3 + RND() * 3, c='#d8f060', ph=RND() * 6)
    if g.tumble:
        g.tumble['t'] += dt; g.tumble['x'] += g.tumble['vx'] * dt
        if g.tumble['x'] > W + 20: g.tumble = None
    g.shake = max(0, g.shake - rdt * 14)
    if RND() < dt * 16 and g.theme != 'amazon' and g.S in DUEL_STATES + ('title',): addp(type='dust', x=-2, y=140 + RND() * 125, vx=28 + RND() * 40, vy=0, life=16, c='#f0c080' if RND() < .5 else '#d89860', ph=RND() * 6)
    if P and not P.dead and SKMAP[SAVE['eqS']]['s'].get('cigarHand') and P.pose == 'idle' and RND() < dt * 10 and g.S not in ('church',):
        c = ze('idle').cig
        if c: x, y = to_world(P, *c); addp(type='smoke', x=x, y=y, vx=4 + RND() * 6, vy=-12 - RND() * 8, life=1.4, s=1, c='#e8e4dc')
    keep = []
    for p in g.parts:
        p['vy'] += p['g'] * dt; p['x'] += p['vx'] * dt; p['y'] += p['vy'] * dt; p['rot'] += p['vr'] * dt
        t = p['type']
        if t == 'dust': p['y'] += math.sin(g.time * 3 + p['ph']) * .2
        elif t == 'smoke': p['vx'] *= .96; p['vy'] *= .96; p['s'] += dt * 3
        elif t == 'firefly': p['vx'] += (RND() - .5) * 20 * dt; p['vy'] += (RND() - .5) * 20 * dt
        gr = p['ground']
        if gr is not None and p['y'] > gr:
            if t == 'blood':
                DEC.fill(p['c'], (int(p['x']), int(gr), p['s'] + 1 + (1 if RND() < .5 else 0), 2 if RND() < .3 else 1)); continue
            p['y'] = gr; p['vy'] *= -.25; p['vx'] *= .55; p['vr'] *= .4
            if t == 'chunk' and RND() < .5: DEC.fill(C('#6a0606'), (int(p['x']), int(gr) + 1, 2, 1))
            if abs(p['vy']) < 12: p['vy'] = 0; p['g'] = 0; p['vx'] *= .8; p['vr'] = 0
        p['life'] -= dt
        if p['life'] > 0 and -30 < p['x'] < W + 30 and p['y'] > -60: keep.append(p)
    if len(keep) > 1600: keep = keep[-1600:]
    g.parts = keep
def start_dialog():
    D = g.D; g.horse = None; st('dialog'); n = audio.voice(D.op['voice']) if D.op.get('voice') else 0
    D.dlgLen = max(2.2, n + .4)
def begin_standoff():
    D = g.D; st('standoff'); audio.music_vol(None)
    if not D.op.get('boss'): audio.music(None)
    else: audio.music_vol(.3)
    if g.theme not in ('inferno', 'amazon', 'city', 'suburb'): g.tumble = dict(x=-14., vx=62., t=0.)

# ------------------------------------------------------------------ desenho
_FLIP = {}
def flipped(s):
    k = id(s); f = _FLIP.get(k)
    if f is None or f[0] is not s:
        f = (s, pygame.transform.flip(s, True, False)); _FLIP[k] = f
        if len(_FLIP) > 600: _FLIP.clear(); _FLIP[k] = f
    return f[1]
_TINT = {}
def tinted(s, col):
    k = (id(s), col); t = _TINT.get(k)
    if t is None or t[0] is not s:
        b = tob(s); r, gg, bb, _ = C(col)
        for i in range(0, len(b), 4):
            if b[i + 3]: b[i] = r; b[i + 1] = gg; b[i + 2] = bb
        t = (s, fromb(b, s.get_size())); _TINT[k] = t
        if len(_TINT) > 300: _TINT.clear(); _TINT[k] = t
    return t[1]
def draw_wounds(img, wounds, skel):
    img = img.copy(); p = Pt(img)
    for w in wounds:
        age = g.time - w['t']; X, Y = w['x'], w['y']; r = int(min(4 if w['head'] else 3, 1 + age * 4))
        if skel:
            p.P(X, Y, '#1a1214'); p.P(X + 1, Y - 1, '#1a1214'); p.P(X - 1, Y + 1, '#1a1214'); p.P(X + 2, Y - 2, '#3a3230'); continue
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r and ((xx + yy) & 1 or xx * xx + yy * yy <= 2): p.P(X + xx, Y + yy, '#7a0808')
        dl = int(min(16 if w['head'] else 12, age * 9))
        p.R(X, Y, 1, dl, '#a00c0c'); p.R(X + 1, Y + 1, 1, int(dl * .6), '#6a0606')
        if dl > 2: p.P(X, Y + dl, '#c01010')
        p.R(X - 1, Y - 1, 2, 2, '#1a0000'); p.P(X + 1, Y - 1, '#e02020')
    return img
def draw_actor(a, spr, wounds=None, skel=False, pile=None):
    if not a or a.gone or a.hidden: return
    if a.dead:
        pl = pile if pile is not None else ze_pile()
        if a.face < 0: pl = flipped(pl)
        canvas.blit(pl, (int(a.x - 30), GY - 23)); return
    img = spr.s; temp = False
    if wounds: img = draw_wounds(img, wounds, skel); temp = True
    if a.flash > 0:
        if temp:
            b = tob(img)
            for i in range(0, len(b), 4):
                if b[i + 3]: b[i] = b[i + 1] = b[i + 2] = 255
            img = fromb(b, img.get_size())
        else: img = tinted(img, '#ffffff')
    if a.face < 0: img = pygame.transform.flip(img, True, False) if temp else flipped(img); px = SPW - 1 - AX
    else: px = AX
    ang = a.rot + a.recoil * .1; lift = math.sin(a.rot) * 10
    bx, by = a.x + a.offX, GY + a.bob - lift - a.jy
    if abs(ang) < .001: canvas.blit(img, (int(round(bx - px)), int(round(by - FY - 1))))
    else: rot_blit(canvas, img, (px, FY + 1), math.degrees(a.face * ang), (bx, by))
def shadow_at(x, w): arect(canvas, '#1e0a06', x - w / 2, GY - 1, w, 2, 90); arect(canvas, '#1e0a06', x - w / 2 + 3, GY + 1, w - 6, 1, 90)
def draw_pool():
    E = g.E
    if not E or not E.landed or E.gone: return
    cx = E.x - E.face * 44; rx = int(10 + E.pool * 30); ry = int(2 + E.pool * 4)
    for yy in range(-ry, ry + 1):
        w = int(rx * math.sqrt(max(0, 1 - (yy * yy) / (ry * ry + .01)))); canvas.fill(C('#5a0404' if yy < 0 else '#7a0808'), (int(cx - w), GY + 2 + yy, w * 2, 1))
    canvas.fill(C('#b01818'), (int(cx - rx * .4), GY + 1, int(rx * .5), 1))
def draw_windmill():
    cx, cy, a0 = 390, 92, g.time * 1.4
    for i in range(12):
        a = a0 + i * math.pi / 6; c, s = math.cos(a), math.sin(a)
        line(canvas, cx + c * 4, cy + s * 4, cx + c * 25, cy + s * 25, '#24120f'); line(canvas, cx + c * 7 - s, cy + s * 7 + c, cx + c * 24 - s, cy + s * 24 + c, '#3a1c16')
    canvas.fill(C('#24120f'), (cx - 3, cy - 3, 7, 7)); canvas.fill(C('#24120f'), (cx + 3, cy - 1, 20, 3)); canvas.fill(C('#24120f'), (cx + 18, cy - 7, 8, 12)); canvas.fill(C('#3a1c16'), (cx + 19, cy - 6, 6, 10))
def draw_vultures():
    for i in range(3):
        a = g.time * .4 + i * 2.1; x, y = int(300 + math.cos(a) * (40 + i * 12)), int(40 + math.sin(a) * 12 + i * 6); f = int(g.time * 4 + i) % 2; c = C('#1a0a0c')
        canvas.fill(c, (x - 1, y, 3, 1))
        if f: canvas.fill(c, (x - 4, y - 1, 3, 1)); canvas.fill(c, (x + 2, y - 1, 3, 1)); canvas.fill(c, (x - 5, y - 2, 1, 1)); canvas.fill(c, (x + 5, y - 2, 1, 1))
        else: canvas.fill(c, (x - 4, y + 1, 3, 1)); canvas.fill(c, (x + 2, y + 1, 3, 1))
_ROT = {}
def rotq(s, deg):
    k = (id(s), int(deg)); r = _ROT.get(k)
    if r is None or r[0] is not s:
        r = (s, pygame.transform.rotate(s, int(deg))); _ROT[k] = r
        if len(_ROT) > 500: _ROT.clear(); _ROT[k] = r
    return r[1]
_LID = None
def lid_spr():
    global _LID
    if _LID is None:
        s = S(92, 8); p = Pt(s); p.R(0, 0, 92, 8, '#3a2a18'); p.R(0, 0, 92, 1, '#6a4a2a'); p.R(40, 2, 12, 2, '#c8b890'); p.R(45, 0, 2, 8, '#c8b890'); _LID = finalize(s)
    return _LID
def draw_coffin():
    c = g.D.coffin if g.D else None
    if not c: return
    E = g.E; x0 = int(E.x - 8); y = int(c['y']); s = S(96, 22); p = Pt(s)
    p.R(0, 4, 96, 18, '#2a1e12'); p.R(2, 6, 92, 14, '#140e08'); p.R(0, 4, 96, 1, '#5a4028'); p.R(0, 20, 96, 2, '#1a120a')
    for X in (6, 30, 60, 88): p.R(X, 4, 2, 18, '#4a3420')
    if c['lid']: p.R(-2, 0, 100, 6, '#3a2a18'); p.R(-2, 0, 100, 1, '#6a4a2a'); p.R(44, 1, 12, 2, '#c8b890'); p.R(49, 0, 2, 6, '#c8b890')
    vis = GY + 3 - (y - 22)
    if vis > 0: canvas.blit(s, (x0, y - 22), (0, 0, 96, min(22, vis)))
def draw_parts(front):
    cv = canvas
    for p in g.parts:
        t = p['type']; k = p['life'] / p['max']
        if t == 'dust':
            if front: continue
            arect(cv, p['c'], p['x'], p['y'], 1, 1, min(1, k * 3) * 130); continue
        if not front: continue
        x, y = int(p['x']), int(p['y'])
        if t == 'smoke': s = int(p['s']); arect(cv, p['c'], x - s // 2, y - s // 2, s, s, k * 130)
        elif t == 'fire':
            c = '#fff0a0' if k > .7 else '#ffb030' if k > .45 else '#ff5a10' if k > .25 else '#5a2a20'
            arect(cv, c, x, y, p['s'], p['s'], 255 if k > .25 else k * 760)
        elif t in ('ember', 'ash'): arect(cv, p['c'], x, y, 1, 1, min(1, k * 2) * 255)
        elif t == 'firefly':
            on = .5 + .5 * math.sin(g.time * 6 + p['ph'])
            if on > .4: arect(cv, '#f0ff80', x, y, 1, 1, 255 * on); arect(cv, '#a0c040', x - 1, y - 1, 3, 3, 60 * on)
        elif t == 'spr':
            img = p['spr'] if p['face'] > 0 else flipped(p['spr']); deg = round(math.degrees(-p['rot']) / 22.5) * 22.5
            r = rotq(img, deg); px_ = p['ox'] if p['face'] > 0 else SPW - 1 - p['ox']
            cv.blit(r, (x - r.get_width() // 2, y - r.get_height() // 2))
        elif t == 'lid':
            r = rotq(lid_spr(), round(math.degrees(-p['rot']) / 22.5) * 22.5); cv.blit(r, (x - r.get_width() // 2, y - r.get_height() // 2))
        elif t == 'bone':
            q = int(round(p['rot'] / (math.pi / 4))) % 4
            o, c = C('#140a0a'), C('#efe6cd')
            if q in (0, 2): cv.fill(o, (x - 4, y - 2, 9, 4)); cv.fill(c, (x - 3, y - 1, 7, 2)); cv.fill(c, (x - 4, y - 2, 2, 1)); cv.fill(c, (x + 3, y + 1, 2, 1))
            else: cv.fill(o, (x - 2, y - 4, 4, 9)); cv.fill(c, (x - 1, y - 3, 2, 7)); cv.fill(c, (x - 2, y - 4, 1, 2)); cv.fill(c, (x + 1, y + 3, 1, 2))
        elif t == 'chunk': cv.fill(C('#140606'), (x - 1, y - 1, p['s'] + 2, p['s'] + 2)); cv.fill(p['c'], (x, y, p['s'], p['s']))
        elif t in PART_EXT: PART_EXT[t](cv, p, x, y, k)
        else: cv.fill(p['c'], (x, y, p['s'], p['s']))
def draw_scene():
    th = THEMES.get(g.theme); bg = build_bg(g.theme)
    canvas.blit(SKYC[g.theme], (0, 0)); cl = CLOUDC[g.theme]; off = int(g.time * 4) % (W * 2)
    canvas.blit(cl, (-off, 0)); canvas.blit(cl, (W * 2 - off, 0)); canvas.blit(bg, (0, 0))
    if g.theme not in ('amazon', 'city', 'suburb'): draw_windmill()
    if g.theme not in ('night', 'amazon', 'city', 'suburb'): draw_vultures()
    draw_bg_extras()
    canvas.blit(DEC, (0, 0)); draw_parts(False)
    D, P, E = g.D, g.P, g.E
    if P and E:
        draw_coffin(); draw_pool(); shadow_at(P.x, 40 if P.dead else 22)
        if not E.gone and not E.hidden: shadow_at(E.x - (E.face * 40 if E.landed else 0), 60 if E.landed else 22)
        draw_actor(E, eSpr(), D.wounds if D else None, D.op['s']['kind'] == 'skel', D.es.pile)
        draw_horse(); draw_fg_extras()
        pz = 'crouch' if P.dodge else P.pose
        draw_actor(P, ze(pz))
    if g.tumble:
        tb = g.tumble; y = GY + 12 - abs(math.sin(tb['t'] * 5)) * 9; canvas.blit(tumbleweed()[int(tb['t'] * 8 / (math.pi / 2)) % 4], (int(tb['x']) - 8, int(y) - 8))
    if D:
        for t in D.tracers: line(canvas, t['x1'], t['y1'], t['x2'], t['y2'], '#fff2a0')
        for f in D.flashes:
            d = f['d']; x, y = int(f['x']), int(f['y'])
            canvas.fill(C('#fff8d0'), (x - 1, y - 2, 3, 5)); canvas.fill(C('#fff8d0'), (x - 2, y - 1, 5, 3))
            canvas.fill(C('#ffd040'), (x + 2 if d > 0 else x - 10, y - 1, 9, 3)); canvas.fill(C('#ffd040'), (x + d * 2, y - 5, 1, 11))
            canvas.fill(C('#ff8020'), (x + 11 if d > 0 else x - 14, y, 4, 1))
    draw_parts(True)
    if th and th['ov'] and g.theme != 'inferno': (r, gg, b), a = th['ov']; arect(canvas, '#%02x%02x%02x' % (r, gg, b), 0, 0, W, H, a // 2)
def heart(x, y, full):
    m = ['.11.11.', '1111111', '1111111', '.11111.', '..111..', '...1...']; o = C('#140808')
    for r_ in ((x - 1, y, 9, 4), (x, y - 1, 3, 1), (x + 4, y - 1, 3, 1), (x, y + 4, 7, 1), (x + 1, y + 5, 5, 1), (x + 2, y + 6, 3, 1)): canvas.fill(o, r_)
    for r in range(6):
        for c in range(7):
            if m[r][c] == '1': canvas.fill(C(('#ffb0a0' if r == 1 and c == 1 else '#e02a2a') if full else '#3a1418'), (x + c, y + r, 1, 1))
def draw_hud():
    D, P, E = g.D, g.P, g.E
    canvas.fill(C('#140808'), (3, 3, 32, 32)); canvas.fill(C('#8a5a30'), (4, 4, 30, 30)); canvas.fill(C('#3a1810'), (5, 5, 28, 28))
    canvas.blit(ze('idle').s, (6, 5), (AX - 13, 8, 26, 28))
    for i in range(max_hearts()): heart(41 + i * 11, 6, i < RUN['hearts'])
    w = cur_w(); n = w['ammo']; step = 5 if n <= 12 else 2
    for i in range(min(n, 30)):
        x, on = 41 + i * step, i < (P.ammo if P else n)
        canvas.fill(C('#140808'), (x - 1, 16, 4 if step == 5 else 2, 9)); canvas.fill(C('#e0b040' if on else '#4a3a30'), (x, 18, 2 if step == 5 else 1, 6))
    dtext(canvas, WMAP[SAVE['eqW']]['name'], 41, 28, col='#c8a890')
    dtext(canvas, 'NÍVEL %d' % D.L, 476, 6, align='right', col=GOLD); dtext(canvas, '$ %d' % SAVE['money'], 476, 17, align='right')
    if SAVE['best'] is not None: dtext(canvas, 'RECORDE ' + fmt(SAVE['best']), 476, 28, align='right', col='#c8b090')
    a = SAVE.get('active')
    if a: cd = [c for c in CARDS if c['id'] == a['type']][0]; dtext(canvas, '%s (%d)' % (cd['name'], a['rounds']), 476, 39, align='right', col=cd['col'])
    if D.hpMax > 1 and not E.gone and not E.hidden and not E.dead and not E.dying and g.S not in ('intro', 'rise'):
        x = int(E.x - 20); y = SPR_TOP + (-2 if (D.op['s'].get('hat') or {}).get('type') == 'sombrero' else 2)
        canvas.fill(C(DARK), (x - 1, y - 1, 42, 6)); sw = 40 // D.hpMax
        for i in range(D.hpMax): canvas.fill(C('#e02a2a' if i < D.hp else '#3a1418'), (x + i * sw, y, sw - 1, 4))
def bubble(txt, x, y, tail_x=None):
    w = len(txt) * 6 + 9; h = 15; x = int(min(W - w - 2, max(2, x - w / 2))); o = C('#140a0a'); f = C('#f4ecd8')
    canvas.fill(o, (x + 1, y, w - 2, h)); canvas.fill(o, (x, y + 1, w, h - 2)); canvas.fill(f, (x + 1, y + 1, w - 2, h - 2))
    tx = int(min(x + w - 12, max(x + 4, (tail_x if tail_x is not None else g.E.x) - 6)))
    for r_ in ((tx, y + h - 1, 6, 1), (tx + 1, y + h, 5, 1), (tx + 3, y + h + 1, 3, 1), (tx + 5, y + h + 2, 1, 1)): canvas.fill(o, r_)
    for r_ in ((tx + 1, y + h - 1, 4, 1), (tx + 2, y + h, 3, 1), (tx + 4, y + h + 1, 1, 1)): canvas.fill(f, r_)
    dtext(canvas, txt, x + 5, y + 4, col='#2a1410', out=None)
def crosshair():
    if not g.mouse_in: return
    x, y = int(g.mouse[0]), int(g.mouse[1]); c = C('#ff3a2a' if g.S == 'go' else CREAM); o = C(DARK)
    parts = ((-7, 0, 5, 1), (3, 0, 5, 1), (0, -7, 1, 5), (0, 3, 1, 5))
    for dx, dy, w, h in parts: canvas.fill(o, (x + dx - 1, y + dy - 1, w + 2, h + 2))
    for dx, dy, w, h in parts: canvas.fill(c, (x + dx, y + dy, w, h))
    canvas.fill(c, (x, y, 1, 1))
def key_icon(k, x, y, sc=3):
    w = 7 * sc + 8; canvas.fill(C(DARK), (x - 2, y - 2, w + 4, w + 6)); canvas.fill(C('#d8d0c0'), (x, y, w, w + 2)); canvas.fill(C('#f8f4ea'), (x, y, w, w - 2))
    dtext(canvas, k, x + w // 2, y + 4, sc=sc, col='#2a1410', out=None, align='center')
def draw_duel():
    D, P, E = g.D, g.P, g.E
    draw_scene(); draw_hud()
    if g.S in ('intro',):
        a = min(1, g.T * 2) * min(1, (3.0 - g.T) * 2.5)
        if a > 0:
            if D.op.get('boss'):
                dtext(canvas, 'CHEFÃO', 240, 44, sc=2, col='#ff4a1c', align='center', alpha=255 * a)
                dtext(canvas, D.op['name'], 240, 64, sc=3, col='#ffb040', sh='#7a1408', ext=2, ot=2, out=DARK, align='center', alpha=255 * a)
                for i, l in enumerate(D.op.get('lore', [])): dtext(canvas, l, 240, 94 + i * 10, col='#e8d8b8', align='center', alpha=255 * a)
            else:
                dtext(canvas, 'NÍVEL %d' % D.L, 240, 52, col=GOLD, align='center', alpha=255 * a)
                dtext(canvas, D.op['name'], 240, 64, sc=3, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center', alpha=255 * a)
                if D.op['hp'] > 1: dtext(canvas, 'RESISTENTE: %d TIROS' % D.op['hp'], 240, 92, col='#ff8a6a', align='center', alpha=255 * a)
    if g.S == 'rise':
        dtext(canvas, D.op['name'], 240, 50, sc=3, col='#9ac070', sh='#2a3a18', ext=2, ot=2, out=DARK, align='center')
        for i, l in enumerate(D.op.get('lore', [])): dtext(canvas, l, 240, 80 + i * 10, col='#e8d8b8', align='center')
    if g.S == 'dialog':
        dots = '.' * (1 + int(g.T * 3) % 3)
        bubble(('¡' if D.op.get('lang') == 'es' else '') + dots.ljust(3), E.x - 10, SPR_TOP - 16)
        dtext(canvas, D.op['name'], 240, 40, sc=2, col='#ffb040', align='center')
        if int(g.time * 2) % 2 == 0: dtext(canvas, 'ENTER: PULAR', 240, 250, col='#c8a890', align='center')
    if g.S == 'standoff' and int(g.T * 3) % 2 == 0:
        dtext(canvas, 'NÃO SAQUE ANTES DO 3!', 240, 64, sc=2, col=GOLD, align='center')
        dtext(canvas, 'CLIQUE NO INIMIGO PARA MIRAR · CABEÇA = DANO DOBRADO', 240, 86, col='#e8d8b8', align='center')
    if getattr(D, 'say', None) and g.S in ('count', 'go', 'resolve', 'jam') and D.sayT < 1.6 and not E.gone and not E.dying and not E.dead: bubble(D.say, E.x - 10, SPR_TOP - 16)
    draw_duel_extras()
    if g.S == 'count' and D.num and D.num != 'ATIRE!':
        pop = max(0, 1 - D.sayT * 6); dtext(canvas, D.num, 240, 36 - int(pop * 5), sc=8, col=CREAM, sh=BROWN, ext=3, ot=2, out=DARK, align='center')
    if g.S == 'go':
        j = int((RND() - .5) * 4) if g.T < .15 else 0
        dtext(canvas, 'ATIRE!', 240 + j, 44, sc=7, col='#ff4a1c', sh='#7a1408', ext=3, ot=2, out=DARK, align='center')
        for r_ in ((140, 104, 84, 5), (256, 104, 84, 5)): canvas.fill(C(DARK), r_)
        for r_ in ((141, 105, 82, 3), (257, 105, 82, 3)): canvas.fill(C('#d83018'), r_)
    if g.S == 'jam' and D.jam:
        j = D.jam
        arect(canvas, '#14203a', 0, 0, W, H, 90); canvas.fill(C('#000000'), (0, 0, W, 18)); canvas.fill(C('#000000'), (0, H - 18, W, 18))
        if j['fired'] and not (j['passed'] and j['prog'] > 1.6):
            x = lerp(j['x0'], P.x - 40, j['prog']); y = lerp(j['y0'], j['y'], min(1, j['prog']))
            for k in range(14): arect(canvas, '#ffe8a0', x + k * 3 * (-E.face), y, 3, 1, 200 - k * 13)
            canvas.fill(C('#fff8e0'), (int(x) - 1, int(y) - 1, 4, 3)); canvas.fill(C('#c8a040'), (int(x) + 2, int(y) - 1, 2, 3))
        if j['res'] is None and int(g.time * 6) % 2 == 0:
            key_icon(j['key'].upper(), 210, 40); dtext(canvas, 'ABAIXE!' if j['key'] == 'a' else 'PULE!', 250, 50, sc=3, col='#ff4a1c', sh='#7a1408', ext=1)
        dtext(canvas, 'A = ABAIXAR   ·   D = PULAR', 240, 256, col='#c8c0e0', align='center')
    if getattr(D, 'msg', None) and D.msgT < 1.2 and g.S in ('jam', 'go'):
        dtext(canvas, D.msg, 240, 14 if g.S == 'jam' else 120, sc=3 if g.S == 'jam' else 2, col='#ffd060' if D.msg != 'FALHOU!' else '#ff4a1c', sh=BROWN, ext=1, align='center')
    if g.S == 'resolve' and D.big:
        if D.big.get('red'): dtext(canvas, D.big['txt'], 240, 44, sc=4, col='#ff4a1c', sh='#7a1408', ext=2, ot=2, out=DARK, align='center')
        else:
            dtext(canvas, D.big['txt'], 240, 40, sc=4, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center'); dtext(canvas, D.big['sub'], 240, 80, sc=2, col=GOLD, align='center')
            if D.newBest and int(g.T * 4) % 2 == 0: dtext(canvas, 'NOVO RECORDE!', 240, 100, col='#ffffff', align='center')
            if getattr(D, 'heal', False): dtext(canvas, '+1 VIDA! (5 VITÓRIAS)', 240, 112, col='#ff8a8a', align='center')
    if g.S in ('count', 'go', 'standoff'): crosshair()
def skull_div(cx, y, col):
    canvas.fill(C(DARK), (cx - 70, y, 140, 3)); canvas.fill(C(col), (cx - 69, y + 1, 138, 1)); x = cx - 6
    canvas.fill(C(DARK), (x - 1, y - 6, 14, 14))
    for r_ in ((x + 1, y - 5, 10, 7), (x, y - 4, 12, 5), (x + 2, y + 2, 8, 4)): canvas.fill(C(col), r_)
    for r_ in ((x + 2, y - 3, 3, 3), (x + 7, y - 3, 3, 3), (x + 5, y + 1, 2, 1), (x + 4, y + 3, 1, 3), (x + 7, y + 3, 1, 3)): canvas.fill(C(DARK), r_)
_SCR = {}
def screens():
    if _SCR: return _SCR
    rr = random.Random(7)
    s = S(W, H); p = Pt(s)
    for i, c in enumerate(['#1a0608', '#240a0c', '#300e10', '#3e1214', '#4e1818']): p.R(0, i * 42, W, 42, c)
    p.R(0, 210, W, 60, '#4e1818')
    for i in range(70): p.P(int(rr.random() * W), int(rr.random() * 130), '#8a4a40')
    mx, my, r = 110, 92, 58
    for Y in range(my - r - 8, my + r + 9):
        for X in range(mx - r - 8, mx + r + 9):
            d = math.hypot(X - mx, Y - my)
            if d <= r: p.P(X, Y, '#e06048' if d > r - 3 else '#c84a3a')
            elif d < r + 8 and (X + Y) % 2 == 0: p.P(X, Y, '#6a2420')
    for X, Y, sz in ((92, 70, 9), (134, 104, 12), (100, 124, 6), (140, 64, 4)): p.EL(X, Y, sz, sz, '#b03e32')
    for X in range(W): h = int(round(20 + math.sin(X * .04) * 6 + math.sin(X * .11) * 4)); p.R(X, 224 - h, 1, h + 50, '#1a0606')
    saguaro(p, 206, 226, 56, True); saguaro(p, 24, 228, 36, True); _SCR['win'] = s
    s = S(W, H); p = Pt(s)
    for i, c in enumerate(['#16161c', '#1c1c22', '#22222a', '#2a2a32', '#32323a']): p.R(0, i * 39, W, 39, c)
    p.R(0, 195, W, 75, '#3a3640'); p.EL(60, 54, 30, 30, '#7a7680')
    for r_ in ((0, 105, 90, 96), (12, 93, 60, 12), (105, 135, 60, 66), (117, 126, 36, 9), (180, 144, 45, 57)): p.R(*r_, '#1e1c22')
    p.R(9, 120, 15, 15, '#2a2830'); p.R(45, 120, 15, 15, '#2a2830')
    for X in range(225, W, 18): p.R(X, 168, 3, 30, '#1e1c22')
    p.R(225, 177, 255, 3, '#1e1c22')
    for i in range(1400): p.P(int(rr.random() * W), 195 + int(rr.random() * 75), '#2e2c34' if rr.random() < .5 else '#46424c')
    _SCR['lose'] = s
    s = S(W, H); p = Pt(s)
    for y in range(0, H, 14):
        p.R(0, y, W, 14, '#4a2a18' if y % 28 else '#52301c'); p.R(0, y, W, 1, '#2a160c'); p.R(0, y + 1, W, 1, '#6a4024'); X = int(rr.random() * 60)
        while X < W: p.R(X, y, 1, 14, '#2a160c'); X += 60 + int(rr.random() * 80)
        for i in range(40): p.R(int(rr.random() * W), y + 2 + int(rr.random() * 11), 4 + int(rr.random() * 10), 1, '#3e2214')
    o = S(W, H); o.fill((10, 4, 2, 90)); s.blit(o, (0, 0)); _SCR['wood'] = s
    return _SCR
class Menu:
    def __init__(self, items, x, y, sc=2, gap=20): self.items = items; self.sel = 0; self.x = x; self.y = y; self.sc = sc; self.gap = gap; self.rects = []
def draw_menu(m):
    m.rects = []
    for i, (label, fn) in enumerate(m.items):
        y = m.y + i * m.gap; sel = i == m.sel; w = len(label) * 6 * m.sc
        m.rects.append((m.x - w / 2 - 14, y - 4, w + 28, 7 * m.sc + 8))
        if sel:
            bl = int(g.time * 4) % 2; dtext(canvas, '>', m.x - w / 2 - 14 - bl, y, sc=m.sc, col='#ff5a24'); dtext(canvas, '<', m.x + w / 2 + 4 + bl, y, sc=m.sc, col='#ff5a24')
        dtext(canvas, label, m.x, y, sc=m.sc, col=GOLD if sel else CREAM, sh=BROWN if sel else None, ext=1 if sel else 0, align='center')
def menu_input(m, code):
    if code == 'up': m.sel = (m.sel - 1) % len(m.items); audio.play('blip', .5)
    elif code == 'down': m.sel = (m.sel + 1) % len(m.items); audio.play('blip', .5)
    elif code == 'ok':
        if g.T < .35: return
        audio.play('blip', .5); m.items[m.sel][1]()
def go_sub(s, back): g.returnTo = back; goto(s)
def church_item(back):
    def f():
        if SAVE['bless'] > 0: go_sub('church', back)
        else: toast('DERROTE UM CHEFÃO PARA GANHAR UMA BÊNÇÃO', True); audio.play('nope')
    return ('IGREJA (%d)' % SAVE['bless'], f)
def std_items(first, back, extra=None):
    return [first] + ([extra] if extra else []) + [('ARMARIA', lambda: go_sub('shop', back)), ('GUARDA-ROUPA', lambda: go_sub('wardrobe', back)), ('HABILIDADES' + (' (%d)' % SAVE['sp'] if SAVE['sp'] else ''), lambda: go_sub('skills', back)), church_item(back), ('CONFIGURAÇÕES', lambda: go_sub('settings', back))]
def draw_title():
    draw_scene(); arect(canvas, '#10040a', 0, 0, W, H, 104)
    dtext(canvas, "DEAD MAN'S", 240, 8, sc=3, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center')
    dtext(canvas, 'DRAW', 240, 34, sc=7, col='#ff5a24', sh='#7a1408', ext=3, ot=2, out=DARK, align='center')
    dtext(canvas, 'ESTRELANDO ZÉ CAIXÃO', 240, 98, col=GOLD, align='center')
    its = std_items(('JOGAR', play_pressed), 'title')
    if not g.menu: g.menu = Menu(its, 240, 112, 2, 17)
    else: g.menu.items = its
    draw_menu(g.menu)
    dtext(canvas, 'ESPAÇO/CLIQUE: SACAR · CLIQUE NO CORPO: MIRAR · A/D: DESVIAR', 240, 226, col='#c8a890', align='center')
    dtext(canvas, 'M: SOM · F11: TELA CHEIA · ESC: VOLTAR', 240, 235, col='#c8a890', align='center')
    dtext(canvas, '$ %d  ·  PONTOS %d' % (SAVE['money'], SAVE['sp']) + ('  ·  RECORDE ' + fmt(SAVE['best']) if SAVE['best'] is not None else ''), 240, 246, col=GOLD, align='center')
    draw_toast()
def draw_toast(y=258):
    if g.toast and g.toast['time'] > 0: dtext(canvas, g.toast['t'], 240, y, sc=1, col='#ff6a4a' if g.toast['bad'] else '#9ae07a', align='center')
def draw_win():
    canvas.blit(screens()['win'], (0, 0)); D = g.D; bob = int(round(math.sin(g.time * 2)))
    draw_win_ze(bob)
    boss = D.op.get('boss'); cx = 322
    dtext(canvas, 'LENDA DO OESTE!' if boss else 'YOU WIN', cx, 10, sc=3 if boss else 5, col='#ffb040' if boss else CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center')
    skull_div(cx, 48 if boss else 56, CREAM); y = [62 if boss else 66]
    def L(t, c=CREAM): dtext(canvas, t, cx, y[0], col=c, align='center'); y[0] += 10
    L(D.big['sub'] if D.big else '', GOLD); (L('SEU SAQUE  ' + fmt(D.rt)), L('%s  %s' % (D.op['name'], fmt(D.delay)), '#c8a890')) if D.rt is not None else None
    for b in getattr(D, 'bonusList', [])[:4]: L(b, '#9ae07a')
    L('RECOMPENSA  +$ %d   ·   +%d PONTO%s' % (D.reward, 1 + (3 if boss else 0), 'S' if boss else ''), '#9ae07a'); L('CARTEIRA  $ %d' % SAVE['money'])
    if getattr(D, 'heal', False): L('+1 VIDA RECUPERADA!', '#ff8a8a')
    if boss: L('+1 BÊNÇÃO NA IGREJA', '#ffd060')
    if getattr(D, 'unlock', False) and int(g.time * 3) % 2 == 0: L('VISUAL %s LIBERADO!' % getattr(D, 'unlockName', 'CAVEIRA DOURADA'), '#ffe060')
    def nxt(): RUN['level'] += 1; goto('intro')
    if not g.menu: g.menu = Menu(std_items(('PRÓXIMO DUELO', nxt), 'win', ('REPETIR LUTA', lambda: goto('intro'))), cx, 172, 1, 12)
    else: g.menu.items = std_items(('PRÓXIMO DUELO', nxt), 'win', ('REPETIR LUTA', lambda: goto('intro')))
    draw_menu(g.menu); dtext(canvas, 'PRÓXIMO: ' + enemy_for(RUN['level'] + 1)['name'], cx, 158, col='#c8a890', align='center'); draw_toast(262)
def draw_lose():
    canvas.blit(screens()['lose'], (0, 0)); D = g.D; es = D.es.d['aim'].s
    canvas.blit(pygame.transform.scale(flipped(tinted(es, '#0c0b10')), (SPW * 2, SPH * 2)), (int(178 - (SPW - 1 - AX) * 2), 226 - (FY + 1) * 2))
    canvas.blit(pygame.transform.scale(ze_pile(), (140, 48)), (2, 190)); cx = 330
    dtext(canvas, 'YOU LOSE', cx, 10, sc=5, col='#e8e0d0', sh='#4a4450', ext=2, ot=2, out='#0c0b10', align='center'); skull_div(cx, 56, '#e8e0d0'); y = [68]
    def L(t, c='#e8e0d0'): dtext(canvas, t, cx, y[0], col=c, out='#0c0b10', align='center'); y[0] += 10
    if D.result == 'foul': L('VOCÊ SACOU ANTES DO 3!', '#ff6a4a'); L('NO OESTE, ISSO É TRAPAÇA.', '#a8a2b0')
    elif D.result == 'jam': L('A ARMA FALHOU E VOCÊ NÃO DESVIOU!', '#ff6a4a'); L('USE A OU D NA CÂMERA LENTA.', '#a8a2b0')
    else:
        L('LENTO DEMAIS, PARCEIRO.', '#ff6a4a'); L('%s  %s' % (D.op['name'], fmt(D.delay)), '#a8a2b0')
        if D.hpMax > 1: L('VIDA DELE: %d/%d' % (max(0, D.hp), D.hpMax), '#a8a2b0')
    y[0] += 3
    for i in range(max_hearts()): heart(cx - 16 + i * 11, y[0], i < RUN['hearts'])
    y[0] += 14
    if RUN['hearts'] <= 0:
        dtext(canvas, 'FIM DA LINHA', cx, y[0], sc=3, col='#ff6a4a', out='#0c0b10', ot=2, align='center'); y[0] += 28
        L('DUELOS VENCIDOS: %d   ·   NÍVEL %d' % (RUN['wins'], RUN['level'])); L('DINHEIRO, ARMAS E CHECKPOINTS FICAM SALVOS.', '#a8a2b0')
        if not g.menu: g.menu = Menu([('VOLTAR AO INÍCIO', lambda: goto('title'))], cx, 232, 2, 18)
    else:
        if not g.menu: g.menu = Menu(std_items(('TENTAR DE NOVO', lambda: goto('intro')), 'lose'), cx, 176, 1, 12)
        else: g.menu.items = std_items(('TENTAR DE NOVO', lambda: goto('intro')), 'lose')
    draw_menu(g.menu); draw_toast(262)
def button(label, x, y, fn, sc=1, align='left', bg='#4a2414', hot='#8a3a18', col=CREAM):
    w = len(label) * 6 * sc + 12; h = 7 * sc + 10; X = x - w if align == 'right' else x - w // 2 if align == 'center' else x
    hov = X <= g.mouse[0] < X + w and y <= g.mouse[1] < y + h
    canvas.fill(C(DARK), (X, y, w, h)); canvas.fill(C(hot if hov else bg), (X + 1, y + 1, w - 2, h - 2)); arect(canvas, '#ffdca0', X + 1, y + 1, w - 2, 1, 64)
    dtext(canvas, label, X + 6, y + 5, sc=sc, col=col); g.buttons.append((X, y, w, h, fn))
def back(): goto(g.returnTo)
def stat_bar(label, v, mx, x, y, col, txt):
    dtext(canvas, label, x, y, col='#c8a890'); bx = x + 70
    for i in range(mx): canvas.fill(C(DARK), (bx + i * 9 - 1, y - 1, 8, 9)); canvas.fill(C(col if i < v else '#3a2418'), (bx + i * 9, y, 6, 7))
    dtext(canvas, txt, bx + mx * 9 + 6, y)
def shop_act():
    w = WEAP[g.shopSel]
    if w['id'] in SAVE['ownW']: SAVE['eqW'] = w['id']; save(); audio.play('holster'); toast('EQUIPADA!')
    elif SAVE['money'] >= w['price']: SAVE['money'] -= w['price']; SAVE['ownW'].append(w['id']); SAVE['eqW'] = w['id']; save(); audio.play('buy'); toast('COMPRADA!')
    else: audio.play('nope'); toast('DINHEIRO INSUFICIENTE', True)
def draw_shop():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'ARMARIA', 240, 8, sc=4, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center'); dtext(canvas, '$ %d' % SAVE['money'], 470, 38, sc=1, col=GOLD, align='right')
    for i, w in enumerate(WEAP):
        y = 56 + i * 36; sel = i == g.shopSel; own = w['id'] in SAVE['ownW']; eq = SAVE['eqW'] == w['id']; hov = 10 <= g.mouse[0] < 200 and y - 4 <= g.mouse[1] < y + 28
        canvas.fill(C(DARK), (10, y - 4, 190, 32)); canvas.fill(C('#7a3a18' if sel else '#4a2a18' if hov else '#2e180e'), (11, y - 3, 188, 30))
        if sel: canvas.fill(C(GOLD), (11, y - 3, 2, 30))
        canvas.blit(pygame.transform.scale(gun_sprite(w).s, (52, 20)), (16, y + 4)); dtext(canvas, w['name'], 74, y + 2, col=GOLD if sel else CREAM)
        dtext(canvas, 'EQUIPADA' if eq else 'COMPRADA' if own else '$ %d' % w['price'], 74, y + 14, col='#9ae07a' if eq else '#c8a890' if own else (GOLD if SAVE['money'] >= w['price'] else '#a06050'))
        def f(i=i):
            if g.shopSel == i: shop_act()
            else: g.shopSel = i; audio.play('blip', .5)
        g.buttons.append((10, y - 4, 190, 32, f))
    w = WEAP[g.shopSel]; px = 216; canvas.fill(C(DARK), (px, 52, 256, 186)); canvas.fill(C('#2a160c'), (px + 1, 53, 254, 184))
    gs = gun_sprite(w).s; sc = 7 if w.get('shotgun') else 8; big = pygame.transform.scale(gs, (gs.get_width() * sc, gs.get_height() * sc))
    canvas.blit(tinted(big, '#000000'), (px + 128 - big.get_width() // 2 + 3, 63)); canvas.blit(big, (px + 128 - big.get_width() // 2, 60))
    dtext(canvas, w['name'], px + 128, 146, sc=2, col=GOLD, align='center')
    stat_bar('DANO', w['dmg'], 3, px + 12, 168, '#e04a2a', '%dX' % w['dmg']); stat_bar('CADÊNCIA', int(round((.7 - w['cad']) * 10)), 6, px + 12, 180, '#e0b040', ('%.2fS' % w['cad']).replace('.', ','))
    stat_bar('SAQUE', int(round(3 - w['saque'] * 60)), 6, px + 12, 192, '#6ac0e0', ('-' if w['saque'] <= 0 else '+') + '%dMS' % abs(round(w['saque'] * 1000)))
    stat_bar('BALAS', min(6, (w['ammo'] + 1) // 2), 6, px + 12, 204, '#c8c8c8', str(w['ammo']))
    for i, l in enumerate(w['desc']): dtext(canvas, l, px + 128, 216 + i * 9, col='#c8a890', align='center')
    own = w['id'] in SAVE['ownW']; eq = SAVE['eqW'] == w['id']
    button('EQUIPADA' if eq else 'EQUIPAR' if own else 'COMPRAR $%d' % w['price'], px + 128, 241, shop_act, align='center', bg='#2a4a1a' if eq else '#6a2a10')
    button('VOLTAR', 10, 244, back); dtext(canvas, 'SETAS: ESCOLHER · ENTER: COMPRAR/EQUIPAR · ESC: VOLTAR', 105, 262, col='#8a7058')
    if g.toast and g.toast['time'] > 0: dtext(canvas, g.toast['t'], 344, 130, sc=2, col='#ff6a4a' if g.toast['bad'] else '#9ae07a', align='center')
def ward_act():
    k = SKINS[g.wardSel]
    if k['id'] in SAVE['ownS']: SAVE['eqS'] = k['id']; save(); audio.voice('ze'); toast('EQUIPADO!')
    elif k['price'] < 0: audio.play('nope'); toast('BLOQUEADO', True)
    elif SAVE['money'] >= k['price']: SAVE['money'] -= k['price']; SAVE['ownS'].append(k['id']); SAVE['eqS'] = k['id']; save(); audio.play('buy'); toast('COMPRADO!')
    else: audio.play('nope'); toast('DINHEIRO INSUFICIENTE', True)
def draw_ward():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'GUARDA-ROUPA', 240, 8, sc=4, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center'); dtext(canvas, '$ %d' % SAVE['money'], 470, 38, sc=1, col=GOLD, align='right')
    k = SKINS[g.wardSel]; own = k['id'] in SAVE['ownS']; eq = SAVE['eqS'] == k['id']
    for r in range(6): arect(canvas, '#ffc878', 240 - 30 - r * 8, 44, 60 + r * 16, 190, 20)
    arect(canvas, '#000000', 170, 232, 140, 4, 100)
    sp = ze('idle', k['id']).s; big = pygame.transform.scale(sp if own or k['price'] >= 0 else tinted(sp, '#0c0806'), (SPW * 2, SPH * 2))
    canvas.blit(big, (240 - AX * 2 - 2, 236 - SPH * 2)); g.buttons.append((180, 40, 120, 196, lambda: audio.voice('ze') if own else None))
    dtext(canvas, 'ZÉ CAIXÃO', 240, 44, col='#c8a890', align='center'); dtext(canvas, k['name'], 240, 56, sc=2, col=GOLD, sh=BROWN, ext=1, align='center')
    bl = int(g.time * 3) % 2; dtext(canvas, '<', 70 - bl, 120, sc=5, col='#ff5a24', sh='#7a1408', ext=2); dtext(canvas, '>', 386 + bl, 120, sc=5, col='#ff5a24', sh='#7a1408', ext=2)
    g.buttons.append((50, 100, 70, 70, lambda: ward_input('left'))); g.buttons.append((370, 100, 70, 70, lambda: ward_input('right')))
    dtext(canvas, k['desc'], 240, 240, col='#e8d8b8', align='center')
    button('EQUIPADO' if eq else 'EQUIPAR' if own else 'BLOQUEADO' if k['price'] < 0 else 'COMPRAR $%d' % k['price'], 470, 212, ward_act, align='right', bg='#2a4a1a' if eq else '#6a2a10')
    button('VOLTAR', 10, 244, back); dtext(canvas, 'SETAS: TROCAR · ENTER: EQUIPAR · CLIQUE NO ZÉ PARA OUVIR', 105, 262, col='#8a7058'); dtext(canvas, '%d/%d' % (g.wardSel + 1, len(SKINS)), 470, 246, col='#8a7058', align='right')
    if g.toast and g.toast['time'] > 0: dtext(canvas, g.toast['t'], 240, 196, sc=2, col='#ff6a4a' if g.toast['bad'] else '#9ae07a', align='center')
def ward_input(code):
    if code == 'left': g.wardSel = (g.wardSel - 1) % len(SKINS); audio.play('blip', .5)
    elif code == 'right': g.wardSel = (g.wardSel + 1) % len(SKINS); audio.play('blip', .5)
    elif code == 'back': back()
    elif code == 'ok' and g.T > .3: ward_act()
def shop_input(code):
    if code == 'up': g.shopSel = (g.shopSel - 1) % len(WEAP); audio.play('blip', .5)
    elif code == 'down': g.shopSel = (g.shopSel + 1) % len(WEAP); audio.play('blip', .5)
    elif code == 'back': back()
    elif code == 'ok' and g.T > .3: shop_act()
SKCOL = ('PISTOLEIRO', 'SOBREVIVENTE', 'FORA-DA-LEI')
def skill_cost(s): return s['cost'] * (sk(s['id']) + 1)
def skill_ok(s): return (s['req'] is None or sk(s['req']) >= 1) and sk(s['id']) < s['mx']
def skill_act():
    s = SKILLS[g.skillSel]
    if sk(s['id']) >= s['mx']: toast('NÍVEL MÁXIMO', True); audio.play('nope'); return
    if s['req'] and sk(s['req']) < 1: toast('PRECISA DE %s' % SKMAP2[s['req']]['name'], True); audio.play('nope'); return
    c = skill_cost(s)
    if SAVE['sp'] < c: toast('PONTOS INSUFICIENTES', True); audio.play('nope'); return
    SAVE['sp'] -= c; SAVE['skills'][s['id']] = sk(s['id']) + 1
    if s['id'] == 'coracao': RUN['hearts'] = min(max_hearts(), RUN['hearts'] + 1)
    save(); audio.play('levelup'); toast('%s NÍVEL %d!' % (s['name'], sk(s['id'])))
def node_xy(s): return 22 + s['col'] * 152, 58 + s['row'] * 52
def draw_skills():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'HABILIDADES', 240, 8, sc=4, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center')
    dtext(canvas, 'PONTOS: %d' % SAVE['sp'], 470, 36, sc=1, col=GOLD, align='right')
    for c in range(3): dtext(canvas, SKCOL[c], 22 + c * 152 + 66, 44, col='#c8a890', align='center')
    for s in SKILLS:
        if s['req']:
            r = SKMAP2[s['req']]; x0, y0 = node_xy(r); x1, y1 = node_xy(s)
            canvas.fill(C('#e0b040' if sk(r['id']) else '#3a2418'), (x0 + 64, y0 + 34, 4, y1 - y0 - 34))
    for i, s in enumerate(SKILLS):
        x, y = node_xy(s); sel = i == g.skillSel; lv = sk(s['id']); avail = skill_ok(s)
        canvas.fill(C(GOLD if sel else DARK), (x - 2, y - 2, 136, 38)); canvas.fill(C('#5a2a12' if lv else '#2e180e'), (x, y, 132, 34))
        dtext(canvas, s['name'], x + 6, y + 5, col=GOLD if lv else (CREAM if avail else '#7a6050'))
        for k in range(s['mx']): canvas.fill(C(DARK), (x + 6 + k * 10, y + 19, 8, 8)); canvas.fill(C('#e0b040' if k < lv else '#3a2418'), (x + 7 + k * 10, y + 20, 6, 6))
        if lv < s['mx']: dtext(canvas, '%dP' % skill_cost(s), x + 126, y + 21, col='#9ae07a' if avail and SAVE['sp'] >= skill_cost(s) else '#8a6050', align='right')
        def f(i=i):
            if g.skillSel == i: skill_act()
            else: g.skillSel = i; audio.play('blip', .5)
        g.buttons.append((x - 2, y - 2, 136, 38, f))
    s = SKILLS[g.skillSel]; canvas.fill(C(DARK), (20, 212, 440, 26)); canvas.fill(C('#2a160c'), (21, 213, 438, 24))
    dtext(canvas, '%s  (%d/%d)' % (s['name'], sk(s['id']), s['mx']), 30, 217, col=GOLD); dtext(canvas, 'POR NÍVEL: ' + s['desc'], 30, 228, col='#e8d8b8')
    button('VOLTAR', 10, 244, back); dtext(canvas, 'ENTER: MELHORAR · 1 PONTO POR VITÓRIA, +3 POR CHEFÃO', 105, 262, col='#8a7058')
    if g.toast and g.toast['time'] > 0: dtext(canvas, g.toast['t'], 240, 196, sc=1, col='#ff6a4a' if g.toast['bad'] else '#9ae07a', align='center')
def skills_input(code):
    s = SKILLS[g.skillSel]; c, r = s['col'], s['row']
    if code in ('left', 'right'): c = (c + (1 if code == 'right' else -1)) % 3
    elif code in ('up', 'down'): r = (r + (1 if code == 'down' else -1)) % 3
    elif code == 'back': back(); return
    elif code == 'ok':
        if g.T > .3: skill_act()
        return
    for i, q in enumerate(SKILLS):
        if q['col'] == c and q['row'] == r: g.skillSel = i; audio.play('blip', .5)
def checkpoints(): return [1] + list(range(10, SAVE['maxLevel'] + 1, 10))
def draw_levelsel():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'ESCOLHA A FASE', 240, 10, sc=4, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center')
    dtext(canvas, 'CHECKPOINTS A CADA 10 NÍVEIS · MAIS LONGE: NÍVEL %d' % SAVE['maxLevel'], 240, 46, col='#c8a890', align='center')
    cps = checkpoints(); items = []
    for c in cps:
        op = enemy_for(c); items.append(('NÍVEL %d%s' % (c, ' · ' + op['name'] if c % 10 == 0 else ''), lambda c=c: new_run(c)))
    items.append(('VOLTAR', lambda: goto('title')))
    if not g.menu or len(g.menu.items) != len(items): g.menu = Menu(items, 240, 70, 2, 20)
    else: g.menu.items = items
    draw_menu(g.menu)
def draw_card(cx, y, ci, face, scalex=1., hl=False):
    w = max(1, int(84 * abs(scalex))); h = 112; x = int(cx - w / 2)
    if hl: canvas.fill(C('#fff0a0'), (x - 3, y - 3, w + 6, h + 6))
    canvas.fill(C(DARK), (x - 1, y - 1, w + 2, h + 2))
    if w < 6: return
    s = S(84, 112); p = Pt(s)
    if face:
        cd = CARDS[ci]; col = cd['col']; p.R(0, 0, 84, 112, shade(col, .45)); p.R(2, 2, 80, 108, '#f2e8d2'); p.R(4, 4, 76, 104, '#e8dcc0'); p.R(4, 4, 76, 12, col)
        raw(s, cd['rar'], 42 - len(cd['rar']) * 3, 7, 1, '#1a0a06')
        cx_, cy_ = 42, 38
        if cd['id'] == 'tempo':
            p.R(cx_ - 9, cy_ - 13, 18, 3, '#6a4a20'); p.R(cx_ - 9, cy_ + 11, 18, 3, '#6a4a20')
            for r in range(10): ww = 8 - r * .8; p.R(cx_ - ww, cy_ - 10 + r, ww * 2, 1, '#c8e0f0'); p.R(cx_ - ww, cy_ + 10 - r, ww * 2, 1, '#c8e0f0')
            p.R(cx_ - 4, cy_ + 5, 8, 4, '#e0b040'); p.R(cx_ - 1, cy_ - 2, 2, 6, '#e0b040')
        elif cd['id'] == 'dupla':
            for bx in (cx_ - 9, cx_ + 3): p.R(bx, cy_ - 6, 6, 16, '#d8a830'); p.R(bx, cy_ - 12, 6, 6, '#a8a8b0'); p.R(bx + 1, cy_ - 14, 4, 2, '#a8a8b0'); p.R(bx, cy_ - 6, 2, 16, '#f8e080')
        else:
            p.EL(cx_, cy_, 11, 12, '#8a8a92'); p.EL(cx_, cy_, 9, 10, '#c8c8d0'); p.R(cx_ - 1, cy_ - 7, 3, 14, '#8a1818'); p.R(cx_ - 5, cy_ - 3, 11, 3, '#8a1818')
        raw(s, cd['name'], 42 - len(cd['name']) * 3, 58, 1, '#2a1410')
        for i, l in enumerate(cd['desc']): raw(s, l, 42 - len(l) * 3, 70 + i * 9, 1, '#4a3020')
    else:
        p.R(0, 0, 84, 112, '#5a1014'); p.R(3, 3, 78, 106, '#7a1a1e'); p.R(6, 6, 72, 100, '#5a1014')
        for yy in range(10, 104, 8):
            for xx in range(10 + (yy // 8) % 2 * 4, 76, 8): p.P(xx, yy, '#9a2a2a')
        p.R(38, 30, 8, 52, '#e0b040'); p.R(24, 44, 36, 8, '#e0b040'); p.R(38, 30, 2, 52, '#f8e080'); p.EL(42, 92, 7, 6, '#efe6cd'); p.R(39, 91, 2, 2, '#1a0a06'); p.R(43, 91, 2, 2, '#1a0a06')
    if w != 84: s = pygame.transform.scale(s, (w, 112))
    canvas.blit(s, (x, y))
def draw_church():
    canvas.blit(church_bg(), (0, 0)); c = g.ch; t = c['t']; ph = c['phase']
    for X in (205, 275):
        fl = int(g.time * 10 + X) % 3; canvas.fill(C('#f0ead8'), (X, 156, 3, 10)); canvas.fill(C('#ffd060' if fl else '#ffa030'), (X, 151 - fl, 3, 4)); arect(canvas, '#ffd060', X - 4, 146, 11, 12, 40)
    if ph == 'enter': canvas.fill(C('#f8e8c0'), (10, 130, 42, 84)); arect(canvas, '#ffe0a0', 52, 130, 60, 84, 60)
    if ph in ('bless', 'show'):
        a = min(1, t / .6) * 70
        for k in range(20): arect(canvas, '#fff4c0', 150 + k - 10, 0, 1, 226, a * (1 - abs(k - 10) / 10))
    pr = g.priest; canvas.blit(flipped(pr.s), (int(g.chPriest.x - (SPW - 1 - AX)), GY - FY - 1))
    Z = g.chP; zs = ze(Z.pose).s; canvas.blit(zs, (int(Z.x - AX), GY - FY - 1))
    draw_parts(True)
    if ph == 'bless': bubble('QUE A SORTE TE ABENÇOE, FILHO.', 300, SPR_TOP - 4, tail_x=g.chPriest.x)
    if ph in ('show', 'flip', 'shuffle', 'pick', 'reveal', 'done'):
        y = int(c['cardY'])
        for slot in range(3):
            ci = c['slots'][slot]; x = SLOTX[slot]; yy = y; face = True; sx_ = 1.
            if ph == 'flip': k = min(1, t / .5); sx_ = math.cos(k * math.pi); face = sx_ > 0
            elif ph in ('shuffle', 'pick'): face = False
            elif ph in ('reveal', 'done'):
                dly = 0 if slot == c['picked'] else .7; k = 1 if ph == 'done' else min(1, max(0, (t - dly) / .5)); sx_ = -math.cos(k * math.pi); face = sx_ > 0
            if ph == 'shuffle':
                for (i, j, t0) in c['swaps'][-1:]:
                    k = (t - t0) / .24
                    if 0 <= k < 1 and slot in (i, j):
                        other = j if slot == i else i; x = lerp(SLOTX[other], SLOTX[slot], ease(k)); yy = y - math.sin(math.pi * k) * (24 if slot == i else -24)
            hl = ph == 'pick' and slot == c['sel'] or (ph in ('reveal', 'done') and slot == c['picked'])
            draw_card(x, int(yy), ci, face, sx_, hl)
            if ph == 'pick': g.buttons.append((x - 42, y, 84, 112, lambda s=slot: church_pick(s)))
    if ph == 'pick': dtext(canvas, 'ESCOLHA UMA CARTA', 240, 138, sc=2, col=GOLD, sh=BROWN, ext=1, align='center')
    if ph == 'done':
        cd = CARDS[c['slots'][c['picked']]]; dtext(canvas, 'VOCÊ RECEBEU: %s (%s)' % (cd['name'], cd['rar']), 240, 136, sc=1, col=cd['col'], align='center')
        button('SAIR DA IGREJA', 240, 236, back, align='center')
    dtext(canvas, 'IGREJA DO PADRE DON SANTIAGO', 240, 258, col='#c8b8a0', align='center')
def church_input(code):
    c = g.ch
    if c['phase'] == 'pick':
        if code == 'left': c['sel'] = (c['sel'] - 1) % 3; audio.play('blip', .5)
        elif code == 'right': c['sel'] = (c['sel'] + 1) % 3; audio.play('blip', .5)
        elif code == 'ok': church_pick(c['sel'])
    elif c['phase'] == 'done' and code in ('ok', 'back'): back()
    elif code == 'ok' and c['phase'] in ('enter', 'bless'): c['phase'] = 'show'; c['t'] = 0; g.chP.x = 170; g.chP.pose = 'idle'

# ------------------------------------------------------------------ entrada
DUEL_STATES = ('intro', 'rise', 'dialog', 'standoff', 'count', 'go', 'resolve', 'jam')
def duel_press(aim):
    if g.fadeDir: return
    if g.S == 'count': foul()
    elif g.S == 'go': player_fire(aim)
def ui(code):
    if g.fadeDir: return
    s = g.S
    if s == 'shop': shop_input(code)
    elif s == 'wardrobe': ward_input(code)
    elif s == 'skills': skills_input(code)
    elif s == 'church': church_input(code)
    elif s == 'settings': settings_input(code)
    elif g.menu:
        if code == 'back' and s == 'levelsel': goto('title')
        elif code == 'back' and s == 'debug': goto('settings')
        else: menu_input(g.menu, code)
KEYMAP = {}
def on_key(k):
    if k == pygame.K_m: audio.toggle(); SAVE['muted'] = audio.muted; save(); return
    if k == pygame.K_F11: toggle_full(); return
    if g.S == 'jam':
        if k in (pygame.K_a, pygame.K_LEFT): jam_dodge('a')
        elif k in (pygame.K_d, pygame.K_RIGHT): jam_dodge('d')
        return
    if g.S == 'dialog' and k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
        audio.stop_voice(); begin_standoff(); return
    if g.S in DUEL_STATES:
        if k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_f, pygame.K_j): duel_press(None)
        return
    m = {pygame.K_UP: 'up', pygame.K_w: 'up', pygame.K_DOWN: 'down', pygame.K_s: 'down', pygame.K_LEFT: 'left', pygame.K_a: 'left', pygame.K_RIGHT: 'right', pygame.K_d: 'right',
         pygame.K_RETURN: 'ok', pygame.K_KP_ENTER: 'ok', pygame.K_SPACE: 'ok', pygame.K_ESCAPE: 'back', pygame.K_BACKSPACE: 'back'}
    if k in m: ui(m[k])
def on_move(p):
    g.mouse = p; g.mouse_in = 0 <= p[0] < W and 0 <= p[1] < H
    if g.menu and g.S in ('title', 'win', 'lose', 'levelsel', 'debug'):
        for i, r in enumerate(g.menu.rects):
            if r[0] <= p[0] < r[0] + r[2] and r[1] <= p[1] < r[1] + r[3] and g.menu.sel != i: g.menu.sel = i; audio.play('blip', .4)
    if g.S == 'church' and g.ch and g.ch['phase'] == 'pick':
        for s in range(3):
            if SLOTX[s] - 42 <= p[0] < SLOTX[s] + 42 and g.ch['cardY'] <= p[1] < g.ch['cardY'] + 112: g.ch['sel'] = s
def on_click(p):
    g.mouse = p
    if g.S == 'jam': return
    if g.S == 'dialog': on_key(pygame.K_RETURN); return
    if g.S in DUEL_STATES: duel_press(p); return
    if g.fadeDir: return
    for (x, y, w, h, fn) in list(g.buttons):
        if x <= p[0] < x + w and y <= p[1] < y + h: fn(); return
    if g.menu:
        for i, r in enumerate(g.menu.rects):
            if r[0] <= p[0] < r[0] + r[2] and r[1] <= p[1] < r[1] + r[3]: g.menu.sel = i; menu_input(g.menu, 'ok'); return
    if g.S == 'church': church_input('ok')

# ------------------------------------------------------------------ janela / laço principal
screen = None; full = False
def toggle_full():
    global screen, full
    full = not full
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if full else pygame.display.set_mode((960, 540), pygame.RESIZABLE)
def present():
    sw, sh = screen.get_size(); s = min(sw / W, sh / H); s = int(s) if s >= 1 else s
    dw, dh = int(W * s), int(H * s); ox, oy = (sw - dw) // 2, (sh - dh) // 2
    screen.fill((0, 0, 0)); screen.blit(pygame.transform.scale(canvas, (dw, dh)), (ox, oy)); g.view = (ox, oy, s)
def to_canvas(pos):
    ox, oy, s = getattr(g, 'view', (0, 0, 2)); return ((pos[0] - ox) / s, (pos[1] - oy) / s)
def render():
    g.buttons = []
    s = g.S
    if s == 'title': draw_title()
    elif s == 'win': draw_win()
    elif s == 'lose': draw_lose()
    elif s == 'shop': draw_shop()
    elif s == 'wardrobe': draw_ward()
    elif s == 'skills': draw_skills()
    elif s == 'levelsel': draw_levelsel()
    elif s == 'church': draw_church()
    elif s == 'settings': draw_settings()
    elif s == 'debug': draw_debug()
    else: draw_duel()
    draw_subs()
    if g.shake > 0:
        dx, dy = int((RND() - .5) * g.shake * 2), int((RND() - .5) * g.shake * 2)
        if dx or dy: c2 = canvas.copy(); canvas.fill((0, 0, 0)); canvas.blit(c2, (dx, dy))
    if g.fade > 0: arect(canvas, '#080204', 0, 0, W, H, g.fade * 255)
def init():
    global audio, canvas, DEC, screen
    try: pygame.mixer.pre_init(44100, -16, 2, 512)
    except Exception: pass
    pygame.init()
    try: pygame.mixer.init()
    except Exception: pass
    screen = pygame.display.set_mode((960, 540), pygame.RESIZABLE); pygame.display.set_caption("Dead Man's Draw — Zé Caixão")
    canvas = pygame.Surface((W, H)); DEC = S(W, H)
    load_save(); load_subs(); audio = Audio()
    if SAVE.get('muted'): audio.toggle()
    canvas.fill((0, 0, 0)); dtext(canvas, 'CARREGANDO...', 240, 130, sc=2, align='center'); present(); pygame.display.flip()
    screens(); build_bg('sunset'); demo_scene(); st('title'); audio.music('country', .6); audio.ambient('amb_wind', .4)
def main():
    init(); clock = pygame.time.Clock(); run = True
    while run:
        rdt = min(.05, clock.tick(60) / 1000)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: run = False
            elif ev.type == pygame.KEYDOWN: on_key(ev.key)
            elif ev.type == pygame.MOUSEMOTION: on_move(to_canvas(ev.pos))
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1: on_click(to_canvas(ev.pos))
        try: pygame.mouse.set_visible(g.S not in DUEL_STATES)
        except Exception: pass
        audio.tick(); update(rdt); render(); present(); pygame.display.flip()
    save(); pygame.quit()

# ------------------------------------------------------------------ cavalo em chamas (entrada do El Derecha)
GALLOP = [[(10, 0), (5, 0), (-10, 0), (-5, 0)], [(3, 6), (-2, 2), (6, 4), (2, 0)], [(-6, 0), (-3, 0), (9, 0), (4, 0)], [(5, 8), (9, 10), (-2, 8), (-7, 6)]]
HIPS = [(62, 36), (58, 36), (30, 36), (26, 36)]
def leg_feet(frame):
    legs = GALLOP[frame] if frame >= 0 else [(2, 0), (-2, 0), (2, 0), (-2, 0)]
    return [(hx + dx, 60 - lift) for (hx, hy), (dx, lift) in zip(HIPS, legs)]
_HORSE = {}
def horse_spr(frame, rider):
    k = (frame, rider)
    if k in _HORSE: return _HORSE[k]
    s = S(120, 112); p = Pt(s); p.oy = 46; b = ramp('#2a2026')
    legs = GALLOP[frame] if frame >= 0 else [(2, 0), (-2, 0), (2, 0), (-2, 0)]
    for idx, ((hx, hy), (dx, lift)) in enumerate(zip(HIPS, legs)):
        far = idx in (0, 2); col = b[1] if far else b[2]
        kx, ky = hx + dx * .5 + (2 if idx < 2 else -2), 48 - lift * .6; fx, fy = hx + dx, 60 - lift
        p.TL(hx, hy, kx, ky, 4, col); p.TL(kx, ky, fx, fy, 3, col)
        p.R(fx - 1, fy, 5, 3, '#3a1a10'); p.R(fx - 1, fy + 2, 5, 1, '#ff9a20'); p.P(fx + 1, fy + 2, '#fff0a0')
    p.EL(44, 30, 22, 10, b[2]); p.EL(46, 27, 18, 6, b[3]); p.R(30, 24, 26, 1, b[4])
    p.TL(60, 30, 70, 12, 9, b[2]); p.TL(62, 26, 70, 12, 3, b[3])
    p.R(66, 5, 10, 10, b[2]); p.TL(70, 9, 82, 19, 6, b[2]); p.R(79, 17, 4, 4, b[1]); p.P(81, 18, '#100808'); p.R(68, 1, 3, 5, b[2]); p.P(69, 2, b[3])
    p.R(72, 9, 2, 2, '#ff3a1a'); p.P(73, 9, '#ffe080'); p.TL(70, 18, 77, 22, 1, '#5a3018')
    for i in range(10): p.R(66 - i * .6, 6 + i * 2, 3, 2, '#ff5a10' if i % 2 else '#ffb030')
    p.TL(23, 27, 12, 40, 4, '#c03010'); p.TL(23, 27, 14, 38, 2, '#ffb030'); p.P(11, 41, '#ff5a10')
    p.R(36, 18, 14, 4, '#5a3018'); p.R(34, 21, 18, 2, '#3a1e10'); p.R(44, 23, 1, 9, '#3a1e10'); p.R(43, 31, 3, 2, '#8a8a8a')
    if rider:
        r = g.D.es.d['idle'].s; s.blit(r, (44 - AX, 46 + 24 - 66), (0, 0, SPW, 66))
        p.oy = 46; p.R(38, 20, 8, 10, '#1a161a'); p.R(40, 28, 5, 6, '#1a161a'); p.R(39, 33, 7, 3, '#100c0e')
    s = finalize(s); _HORSE[k] = s; return s
def horse_update(dt):
    D, E = g.D, g.E; T = g.T
    if not getattr(g, 'horse', None) or g.horse.get('D') is not D:
        g.horse = dict(D=D, x=W + 70., face=-1, rider=True, rear=0., f=0, lf=-1, hoofs=[]); E.hidden = True; E.x = 362
        for fr in range(-1, 4): horse_spr(fr, True); horse_spr(fr, False)
    h = g.horse
    if T < 2.4: h['x'] = lerp(W + 70, 392, ease(min(1, T / 2.4))); h['f'] = int(T * 12) % 4
    elif T < 3.3:
        k = (T - 2.4) / .9; h['rear'] = math.sin(math.pi * k) * 24; h['f'] = -1
        if not h.get('neigh'): h['neigh'] = True; audio.play('neigh'); audio.play('burst', .7); g.shake = 4
    elif T < 3.9:
        h['rear'] = 0; h['f'] = -1
        if h['rider']: h['rider'] = False; E.hidden = False; E.pose = 'idle'; h['jx'] = h['x'] - 2; audio.play('whoosh')
        k = (T - 3.3) / .6; E.x = lerp(h['jx'], 362, k); E.jy = math.sin(math.pi * k) * 26
        if k > .95 and not h.get('land'): h['land'] = True; audio.play('thud'); dust_puff(362, GY - 2, 12)
    else:
        E.jy = 0; E.x = 362
        if h['face'] < 0: h['face'] = 1; audio.play('neigh', .6)
        h['x'] += 260 * dt; h['f'] = int(T * 12) % 4
    if h['f'] >= 0 and h['f'] in (0, 2) and h['lf'] != h['f'] and -40 < h['x'] < W + 40: audio.play('hoof', .8)
    h['lf'] = h['f']
    if -60 < h['x'] < W + 60:
        for fx, fy in leg_feet(h['f']):
            wx = h['x'] + h['face'] * (fx - 45)
            for i in range(2): addp(type='fire', x=wx + (RND() - .5) * 3, y=GY - (63 - fy) - 1, vx=(RND() - .5) * 14, vy=-20 - RND() * 40, life=.3 + RND() * .4, s=2 if RND() < .5 else 1)
            if RND() < .08: DEC.fill(C('#1a0c08'), (int(wx) - 1, GY + int(RND() * 4) - 1, 3, 1))
        for q in ((66, 8), (63, 14), (60, 20), (14, 38), (18, 33)):
            if RND() < .5:
                wx = h['x'] + h['face'] * (q[0] - 45); addp(type='fire', x=wx, y=GY - (63 - q[1]) - 2, vx=-h['face'] * 30 + (RND() - .5) * 10, vy=-30 - RND() * 30, life=.3 + RND() * .4, s=2)
        if RND() < dt * 10: audio.rnd('crackle', 3, .4)
def draw_horse():
    h = getattr(g, 'horse', None)
    if not h or g.S != 'intro' or h.get('D') is not g.D: return
    img = horse_spr(h['f'], h['rider'])
    if h['face'] < 0: img = flipped(img); ax = 120 - 1 - 45
    else: ax = 45
    if h['rear'] > .5:
        bx = 26 if h['face'] > 0 else 120 - 1 - 26
        rot_blit(canvas, img, (bx, 109), h['face'] * h['rear'], (h['x'] + h['face'] * (26 - 45), GY))
    else: canvas.blit(img, (int(h['x'] - ax), GY - 109))

# ------------------------------------------------------------------ legendas
def on_voice(name, n):
    if name is None: g.sub = None; return
    lines = SUBS.get(name) or []
    g.sub = dict(lines=lines, t0=pygame.time.get_ticks(), n=max(.5, n)) if lines else None
def draw_subs():
    sb = getattr(g, 'sub', None)
    if not sb or not SAVE.get('subs', True): return
    el = (pygame.time.get_ticks() - sb['t0']) / 1000
    if el > sb['n'] + .4: g.sub = None; return
    i = min(len(sb['lines']) - 1, int(el / sb['n'] * len(sb['lines'])))
    t = sb['lines'][i]; w = len(t) * 6 + 12
    arect(canvas, '#000000', 240 - w // 2, 230, w, 15, 200); dtext(canvas, t, 240, 234, col='#ffffff', out=None, align='center')

# ------------------------------------------------------------------ configurações
VOLS = [('master', 'VOLUME GERAL'), ('music', 'MÚSICA'), ('sfx', 'EFEITOS'), ('voice', 'VOZES'), ('amb', 'VENTO / AMBIENTE')]
def set_vol(k, v):
    SAVE.setdefault('vol', dict(VDEF)); SAVE['vol'][k] = max(0., min(1., round(v, 2))); audio.apply(); save()
    if k in ('sfx', 'master'): audio.play('bell', .8)
    if k == 'voice': audio.voice('ze')
def settings_input(code):
    n = len(VOLS) + 2; i = getattr(g, 'setSel', 0)
    if code == 'up': g.setSel = (i - 1) % n; audio.play('blip', .5)
    elif code == 'down': g.setSel = (i + 1) % n; audio.play('blip', .5)
    elif code == 'back': back()
    elif i < len(VOLS) and code in ('left', 'right'):
        k = VOLS[i][0]; set_vol(k, (SAVE.get('vol') or VDEF).get(k, VDEF[k]) + (.1 if code == 'right' else -.1))
    elif i == len(VOLS) and code in ('left', 'right', 'ok'): SAVE['subs'] = not SAVE.get('subs', True); save(); audio.play('blip', .5)
    elif i == len(VOLS) + 1 and code == 'ok': back()
def draw_settings():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'CONFIGURAÇÕES', 240, 8, sc=4, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center')
    sel = getattr(g, 'setSel', 0); vol = SAVE.get('vol') or VDEF
    for i, (k, name) in enumerate(VOLS):
        y = 54 + i * 28; hl = i == sel
        dtext(canvas, name, 60, y + 2, sc=1, col=GOLD if hl else CREAM)
        v = vol.get(k, VDEF[k]); bx = 200
        for j in range(10):
            canvas.fill(C(DARK), (bx + j * 18 - 1, y - 1, 16, 12)); canvas.fill(C(('#ffd060' if hl else '#e0a040') if j < round(v * 10) else '#3a2418'), (bx + j * 18, y, 14, 10))
            g.buttons.append((bx + j * 18 - 1, y - 3, 18, 16, lambda k=k, j=j, i=i: (setattr(g, 'setSel', i), set_vol(k, (j + 1) / 10))))
        dtext(canvas, '%d%%' % round(v * 100), 400, y + 2, col=GOLD if hl else CREAM)
        dtext(canvas, '<', 184, y + 2, col='#ff5a24' if hl else '#7a5040'); dtext(canvas, '>', 386, y + 2, col='#ff5a24' if hl else '#7a5040')
        g.buttons.append((176, y - 3, 14, 16, lambda k=k, i=i: (setattr(g, 'setSel', i), set_vol(k, (SAVE.get('vol') or VDEF).get(k, VDEF[k]) - .1))))
        g.buttons.append((380, y - 3, 14, 16, lambda k=k, i=i: (setattr(g, 'setSel', i), set_vol(k, (SAVE.get('vol') or VDEF).get(k, VDEF[k]) + .1))))
    y = 54 + len(VOLS) * 28; hl = sel == len(VOLS)
    dtext(canvas, 'LEGENDAS DAS FALAS', 60, y + 2, col=GOLD if hl else CREAM)
    button('LIGADAS' if SAVE.get('subs', True) else 'DESLIGADAS', 200, y - 3, lambda: (setattr(g, 'setSel', len(VOLS)), settings_input('ok')), bg='#2a4a1a' if SAVE.get('subs', True) else '#6a2a10')
    hl = sel == len(VOLS) + 1
    button('VOLTAR', 10, 244, back, bg='#8a3a18' if hl else '#4a2414')
    dtext(canvas, 'SETAS: ESCOLHER E AJUSTAR · CLIQUE NAS BARRAS · ESC: VOLTAR', 105, 262, col='#8a7058')


# ==================================================================== EXPANSÃO: NPCs, chefões 30/40, eventos
BGX = {}
# ---------------------------------------------------------------- chapéus, armas e roupas extras
def hat_straw(p, h, hx, b):
    c = ramp(h.get('col', '#d8b860'))
    for y in range(b - 8, b): p.R(hx - 5, y, 11, 1, c[2]); p.P(hx - 5, y, c[1]); p.P(hx + 5, y, c[3])
    for y in range(b - 7, b, 2):
        for x in range(hx - 4, hx + 5, 2): p.P(x + (y % 4 == 0), y, c[1])
    p.R(hx - 5, b - 3, 11, 2, h.get('band', '#7a3a1a')); p.R(hx - 15, b, 31, 2, c[2]); p.R(hx - 14, b, 29, 1, c[3]); p.R(hx - 15, b + 1, 31, 1, c[1])
    for x in range(hx - 15, hx + 16, 3): p.P(x, b + 2, c[1])
def hat_gaucho(p, h, hx, b):
    c = ramp(h.get('col', '#2a2420'))
    for y in range(b - 6, b): p.R(hx - 5, y, 11, 1, c[2]); p.P(hx - 5, y, c[1]); p.P(hx + 5, y, c[3])
    p.R(hx - 5, b - 6, 11, 1, c[3]); p.R(hx - 5, b - 2, 11, 1, h.get('band', '#a01818')); p.R(hx - 14, b, 29, 2, c[2]); p.R(hx - 13, b, 27, 1, c[3])
    p.TL(hx - 4, b + 2, hx - 1, b + 16, 1, '#3a2a18')
def hat_maid(p, h, hx, b):
    p.R(hx - 6, b - 4, 13, 3, '#f8f8f4'); p.R(hx - 6, b - 1, 13, 1, '#d8d8d0')
    for x in range(hx - 6, hx + 7, 2): p.P(x, b - 5, '#f8f8f4'); p.P(x + 1, b - 4, '#c8c8c0')
    p.R(hx - 1, b - 6, 3, 2, '#141414')
HAT_EXT = {'straw': hat_straw, 'gaucho': hat_gaucho, 'maidband': hat_maid}
def gun_bricks(w):
    s = S(26, 10); p = Pt(s); p.R(4, 2, 9, 5, '#d02a2a'); p.R(4, 2, 9, 1, '#ff6a5a'); p.R(5, 0, 2, 2, '#d02a2a'); p.R(9, 0, 2, 2, '#d02a2a'); p.R(4, 6, 9, 1, '#8a1010')
    return Gun(s, (13, 3), (3, 2))
def gun_pans(w):
    s = S(26, 10); p = Pt(s); p.R(0, 3, 9, 2, '#3a2a20'); p.R(9, 1, 14, 6, '#2a2a30'); p.R(9, 1, 14, 1, '#6a6a74'); p.R(10, 6, 12, 1, '#141418')
    return Gun(s, (22, 3), (3, 2))
GUN_EXT = {'bricks': gun_bricks, 'pans': gun_pans}
WMAP['bricks'] = dict(id='bricks', dmg=1, cad=.2, saque=0, ammo=12, ln=0, metal='#d02a2a', grip='#d02a2a')
WMAP['pans'] = dict(id='pans', dmg=1, cad=.2, saque=0, ammo=12, ln=0, metal='#2a2a30', grip='#3a2a20')
def body_ext_skirt(p, s, crouch):
    k = ramp(s['skirt']); oy = 12 if crouch else 0; end = 84 if crouch else 92
    for y in range(TB + oy, end + oy if not crouch else 99):
        hw = 8 + (y - TB - oy) // 3; p.R(AX - hw, y, 2 * hw + 2, 1, k[2]); p.P(AX - hw, y, k[1]); p.P(AX + hw + 1, y, k[3])
        for fx in range(AX - hw + 4, AX + hw, 5): p.P(fx, y, k[1])
    y = (end + oy if not crouch else 99) - 1; hw = 8 + (y - TB - oy) // 3; p.R(AX - hw, y, 2 * hw + 2, 1, k[1])
def body_ext(p, s, tw):
    if s.get('plaid'):
        for y in range(T0 + 2, TB, 4): p.R(AX - tw, y, 2 * tw + 1, 1, s['plaid'])
        for x in range(AX - tw + 1, AX + tw, 4): p.R(x, T0, 1, TB - T0, shade(s['plaid'], 1.3))
    if s.get('apron'):
        p.R(AX - 3, T0 + 2, 8, 10, '#f8f8f4'); p.R(AX - 6, TB - 3, 14, 18, '#f8f8f4'); p.R(AX - 6, TB - 3, 1, 18, '#d8d8d0')
        for x in range(AX - 6, AX + 8, 2): p.P(x, TB + 15, '#d8d8d0')
        for y in range(T0 + 2, T0 + 12, 2): p.P(AX - 4, y, '#d8d8d0'); p.P(AX + 5, y, '#d8d8d0')
        p.TL(AX - 3, T0 + 2, AX - 6, T0 - 1, 1, '#f8f8f4'); p.TL(AX + 4, T0 + 2, AX + 7, T0 - 1, 1, '#f8f8f4'); p.R(AX - tw, TB - 4, 2 * tw + 1, 2, '#f8f8f4')
    if s.get('goldButtons'):
        for i in range(4): p.P(AX + 2, T0 + 6 + i * 5, '#e0b040')
    if s.get('collarW'): p.R(AX - 2, T0 - 1, 3, 3, '#f4ecd8'); p.R(AX + 3, T0 - 1, 3, 3, '#f4ecd8')
    if s.get('bag'):
        p.TL(AX + 4, T0, AX - tw - 3, TB - 8, 1, '#c8bca0'); p.R(AX - tw - 8, TB - 8, 10, 14, '#e8dcc0'); p.R(AX - tw - 8, TB - 8, 10, 1, '#f8ecd0'); p.R(AX - tw - 8, TB + 5, 10, 1, '#b8ac90')
        p.R(AX - tw - 4, TB - 5, 1, 6, '#1a2a5a'); p.R(AX - tw - 6, TB - 4, 5, 1, '#1a2a5a'); p.R(AX - tw - 6, TB, 5, 1, '#1a2a5a')
def head_ext(p, s, hx, top):
    if s.get('curly'):
        hr = ramp(s.get('hair', '#a8401a'))
        for cx, cy in ((-6, 1), (-3, -2), (1, -3), (5, -1), (-8, 5), (-8, 10), (-7, 15), (-6, 19), (7, 3), (-4, 22)):
            p.EL(hx + cx, top + cy, 2, 2, hr[2]); p.P(hx + cx, top + cy - 1, hr[3])
    if s.get('lips'): p.R(hx + 1, top + 12, 4, 1, '#d01828'); p.P(hx + 2, top + 11, '#e04050')
    if s.get('shades'):
        if s['kind'] == 'skel': p.R(hx - 4, top + 5, 10, 3, '#0a0a0e'); p.P(hx - 3, top + 5, '#6a6a7a'); p.P(hx + 2, top + 5, '#6a6a7a')
        else: p.R(hx - 1, top + 6, 7, 2, '#0a0a0e'); p.P(hx, top + 6, '#6a6a7a'); p.TL(hx - 1, top + 6, hx - 5, top + 7, 1, '#0a0a0e')
    if s.get('earpiece'): p.P(hx - 5, top + 8, '#d8d8d8'); p.TL(hx - 5, top + 9, hx - 3, top + 16, 1, '#c8c8d0')

# ---------------------------------------------------------------- visuais novos do Zé
FARDA = dict(BOSS2['s']); FARDA.pop('noHolster', None); FARDA['eye'] = '#ff3a2a'; FARDA['head'] = 'skull'
SKINS += [dict(id='farda', name='FARDA DO KRIEGER', price=-1, desc='DERROTE O BOSSE KRIEGER (NÍVEL 20) PARA LIBERAR.', s=FARDA),
          dict(id='especial', name='AGENTE ESPECIAL', price=-1, desc='DERROTE O AGENTE ARTHUR (NÍVEL 30) PARA LIBERAR.',
               s=dict(kind='skel', eye='#ff3a2a', shades=True, earpiece=True, coat=dict(col='#16161c', kind='jacket'), shirt='#f0f0f0', tie='#101014', pants='#16161c', bootCol='#0a0a0c', shoes='shoe')),
          dict(id='maid', name='MAID', price=-1, desc='VENÇA A LUTA CONTRA A LOUÇAS GIRL (NÍVEL 40).',
               s=dict(kind='skel', eye='#ff3a2a', hat=dict(type='maidband', col='#f8f8f4'), coat=dict(col='#141216', kind='dress'), apron=True, bootCol='#0e0c10', shoes='shoe'))]
SKMAP.update({k['id']: k for k in SKINS})

# ---------------------------------------------------------------- vozes dos NPCs
VG = {'npc': ['npc1', 'npc2', 'npc3'], 'mineiro': ['mineiro1', 'mineiro2'], 'sulista': ['sulista1', 'sulista2', 'sulista3', 'sulista4'], 'chileno': ['chileno1']}
VOICE_CHANCE = .65
for e, vg in zip(ENEMIES, ['npc', 'mineiro', 'npc', 'sulista', 'chileno', 'mineiro', 'npc', 'npc', 'npc']): e['vg'] = vg
ENEMIES[1]['s'].update(hat=dict(type='straw', col='#d8b860', band='#7a3a1a'), plaid='#8a2a2a', shirt='#d8c8a8')
ENEMIES[5]['s'].update(hat=dict(type='straw', col='#c8a850', band='#3a2a1a'))
ENEMIES[3]['s'].update(hat=dict(type='gaucho', col='#2a2420', band='#a01818'), neck='bandana', neckCol='#c01818')
NAMES_VG = {'mineiro': ['ZÉ DO QUEIJO', 'TONHO CAIPIRA', 'SÔ JOÃO', 'CHICO PAMONHA'], 'sulista': ['BAGUAL', 'TCHÊ BENTO', 'GURI DO PAMPA', 'XIRU VALDEMAR'],
            'chileno': ['EL HUASO', 'DON PANCHO'], 'npc': NAMES}
_gen_orig = gen_enemy
def gen_enemy(L):
    e = _gen_orig(L); r = random.Random(L * 31 + 7); vg = ['npc', 'npc', 'mineiro', 'sulista', 'chileno'][r.randrange(5)]; s = e['s']; e['vg'] = vg
    if vg == 'mineiro': s['hat'] = dict(type='straw', col='#d8b860', band='#7a3a1a'); s['plaid'] = r.choice(['#8a2a2a', '#2a4a8a', '#3a6a2a']); s.pop('poncho', None); s.pop('coat', None); s.pop('mask', None)
    elif vg == 'sulista': s['hat'] = dict(type='gaucho', col=r.choice(['#2a2420', '#5a3a20']), band='#a01818'); s['neck'] = 'bandana'; s['neckCol'] = '#c01818'; s.pop('mask', None); s['pants'] = '#2a2420'
    elif vg == 'chileno': s['hat'] = dict(type='wide', col='#3a2a1a', band='#c8a040'); s['poncho'] = r.choice(['#7a2a2a', '#2a3a6a']); s['ponchoB'] = '#e8d8b0'; s.pop('coat', None); s.pop('vest', None)
    e['name'] = r.choice(NAMES_VG[vg]); return e

# ---------------------------------------------------------------- chefões 30 e 40
BOSS3 = EN('AGENTE ARTHUR', .30, 7, 'bricks', dict(kind='human', skin='#c88a60', hair='#e0e0e8', slick=True, shades=True, earpiece=True, coat=dict(col='#16161c', kind='jacket'), shirt='#f0f0f0', tie='#101014',
           pants='#16161c', shoes='shoe', bootCol='#0a0a0c', noHolster=True), boss='arthur', stagger=.33, music='arthur', tag='CHEFÃO', lore=['AGENTE ESPECIAL', 'ELE NÃO PEGOU O AVIÃO. ELE É O AVIÃO.'])
BOSS4 = EN('LOUÇAS GIRL', .29, 6, 'pans', dict(kind='human', skin='#f0c0a0', hair='#a8401a', longHair=True, curly=True, lips=True, slick=True, coat=dict(col='#1a2a5a', kind='jacket'), goldButtons=True, collarW=True,
           shirt='#f4ecd8', skirt='#f4f0e6', pants='#f0c0a0', shoes='shoe', bootCol='#3a2a20', bag=True, noHolster=True), boss='loucas', stagger=.32, music='boss1', tag='CHEFE', lore=['A DONA AMANDA,', 'DAS PANELAS E DAS BUCHAS'])
def enemy_for(L):
    if L % 10 == 0:
        b = dict([BOSS1, BOSS2, BOSS3, BOSS4][((L // 10) - 1) % 4]); tier = (L - 1) // 40
        if tier: b['name'] = b['name'] + ' ' + 'I' * (tier + 1); b['hp'] = b['hp'] + 2 * tier; b['delay'] = max(.25, b['delay'] - .02 * tier)
        return b
    if L <= 9: return ENEMIES[L - 1]
    return gen_enemy(L)
def theme_for(L):
    if L % 10 == 0: return ['inferno', 'amazon', 'city', 'suburb'][((L // 10) - 1) % 4]
    if L > 10: return ['sunset', 'dusk', 'night', 'amazon', 'city', 'suburb'][L % 6]
    return 'sunset' if L <= 3 else 'dusk' if L <= 6 else 'night'

# ---------------------------------------------------------------- cenários: cidade e bairro
THEMES['city'] = dict(sky=['#0a0820', '#120c2c', '#1a1038', '#241444', '#30184e', '#3e1c56', '#4e225c', '#602a60', '#743262', '#8a3c62', '#a04a60'], sun='low', gr=['#2a2834'] * 4, road='#2e2e36',
                      cl=['#1a1030', '#4a2a50', '#2a1a40', '#a05a70'], ov=((20, 10, 60), 24), stars=80)
THEMES['suburb'] = dict(sky=['#3a6ac0', '#4274c6', '#4a7ecc', '#5288d2', '#5a92d6', '#649cda', '#70a6de', '#7eb0e2', '#8cbae6', '#9cc4ea', '#acceee'], sun=None, gr=['#6aaa5a'] * 4, road='#4a4a52',
                        cl=['#e8f0f8', '#ffffff', '#f0f4fa', '#ffffff'], ov=None, stars=0)
def _street(p, rnd, road, side, line):
    p.R(0, 199, W, 12, side); p.R(0, 199, W, 1, shade(side, 1.2)); p.R(0, 209, W, 2, shade(side, .7))
    for X in range(0, W, 16): p.R(X, 199, 1, 10, shade(side, .85))
    p.R(0, 211, W, 36, road)
    for i in range(1500): p.P(int(rnd() * W), 211 + int(rnd() * 36), shade(road, .85 if rnd() < .5 else 1.15))
    for X in range(0, W, 40): p.R(X + 10, 228, 20, 2, line)
    p.R(0, 247, W, 23, side); p.R(0, 247, W, 1, shade(side, 1.2))
    for X in range(8, W, 16): p.R(X, 247, 1, 23, shade(side, .85))
def _city(bg, p, rnd, T):
    X = 0
    while X < W:
        w = 14 + int(rnd() * 26); h = 50 + int(rnd() * 70); p.R(X, HZ - h, w, h + 40, '#2a2448')
        for yy in range(HZ - h + 4, HZ + 30, 6):
            for xx in range(X + 2, X + w - 2, 4):
                if rnd() < .25: p.P(xx, yy, '#e8c060')
        X += w + int(rnd() * 4)
    X = -10
    while X < W:
        w = 34 + int(rnd() * 40); h = 70 + int(rnd() * 90); top = HZ + 30 - h; col = pick(['#1c1830', '#221c38', '#18162a'])
        p.R(X, top, w, 200 - top, col); p.R(X, top, w, 2, shade(col, 1.4)); p.R(X, top, 2, 200 - top, shade(col, .8))
        for yy in range(top + 6, 192, 8):
            for xx in range(X + 4, X + w - 5, 7):
                lit = rnd() < .45; p.R(xx, yy, 4, 5, '#f0c860' if lit else '#2e2a48')
                if lit: p.P(xx, yy, '#fff0b0')
        if rnd() < .5: p.R(X + w // 2, top - 14, 1, 14, '#3a3450'); p.P(X + w // 2, top - 15, '#ff3030')
        if rnd() < .4: p.R(X + 6, top - 8, 10, 8, '#2a2438'); p.R(X + 7, top - 10, 8, 2, '#3a3450')
        X += w + int(rnd() * 6)
    p.R(150, 150, 60, 22, '#1a1626'); p.R(152, 152, 56, 18, '#c02a5a'); raw(bg, 'HOTEL', 165, 157, 1, '#ffe0f0')
    _street(p, rnd, T['road'], '#3a3846', '#d8d8c8')
    for lx in (40, 236, 340):
        p.R(lx, 140, 3, 60, '#1a1a22'); p.R(lx, 140, 14, 3, '#1a1a22'); p.R(lx + 10, 143, 6, 3, '#f8e8a0')
        o = S(30, 60); o.fill((255, 230, 150, 18)); bg.blit(o, (lx - 2, 146))
def _suburb(bg, p, rnd, T):
    for X in range(0, W, 2): h = int(16 + 6 * math.sin(X * .03) + 4 * math.sin(X * .11)); p.R(X, HZ - h, 2, h + 40, '#5a9a6a')
    for i in range(14): cx = int(rnd() * W); p.EL(cx, HZ - 10, 12 + int(rnd() * 10), 8, '#4a8a5a')
    p.R(0, HZ, W, 40, '#6aaa5a')
    for hx0, wd in ((-14, 92), (96, 84), (206, 90), (318, 84), (424, 80)):
        wall = pick(['#f0d8a8', '#e8b8b8', '#b8d0e8', '#f0e8d0', '#c8e0b8']); roof = pick(['#a03a2a', '#6a3a2a', '#3a4a6a', '#8a4a2a']); top = 138
        p.R(hx0, top, wd, 62, wall); p.R(hx0, top, 2, 62, shade(wall, .85))
        for r in range(24): w = int(3 + r * (wd / 2 + 3) / 24); p.R(hx0 + wd // 2 - w, top - 24 + r, 2 * w, 1, roof if r % 4 else shade(roof, .8))
        p.R(hx0 + wd - 18, top - 30, 8, 16, '#8a5a4a')
        for wx in (hx0 + 10, hx0 + wd - 28):
            p.R(wx - 1, top + 12, 20, 16, '#f8f8f0'); p.R(wx + 1, top + 14, 7, 12, '#6aa0d0'); p.R(wx + 10, top + 14, 7, 12, '#6aa0d0'); p.P(wx + 2, top + 15, '#ffffff')
        dx = hx0 + wd // 2 - 6; p.R(dx, top + 30, 12, 32, '#7a4a2a'); p.P(dx + 9, top + 46, '#e0c040')
    for tx in (86, 196, 308, 414):
        p.R(tx, 150, 6, 50, '#5a3a20'); p.EL(tx + 3, 140, 18, 15, '#2e7a3a'); p.EL(tx - 3, 134, 11, 9, '#3a9a46'); p.EL(tx + 9, 132, 8, 7, '#4aaa52')
    for X in range(0, W, 6): p.R(X, 186, 3, 13, '#f8f8f0'); p.P(X + 1, 185, '#f8f8f0')
    p.R(0, 189, W, 2, '#e8e8e0'); p.R(0, 195, W, 2, '#e8e8e0')
    _street(p, rnd, T['road'], '#c8c8c0', '#e8c840')
    for i in range(30): p.R(int(rnd() * W), 262 + int(rnd() * 6), 1, 3, '#4a8a3a')
BGX['city'] = _city; BGX['suburb'] = _suburb

# ---------------------------------------------------------------- cartas da bênção (6)
CARDS[:] = [dict(id='tempo', rar='LENDÁRIA', name='TEMPO MORTO', col='#f0b830', w=1, desc=['INIMIGOS', '35% MAIS', 'LENTOS POR', '3 RODADAS']),
            dict(id='anjo', rar='ÉPICA', name='ANJO DA GUARDA', col='#b050e0', w=2, desc=['TE SALVA DE', '1 TIRO FATAL', '(VALE POR', '3 RODADAS)']),
            dict(id='dupla', rar='RARA', name='BALA DUPLA', col='#4a8ae0', w=3, desc=['DISPARA 2', 'BALAS DE UMA', 'VEZ POR', '3 RODADAS']),
            dict(id='lince', rar='INCOMUM', name='OLHO DE LINCE', col='#40b060', w=4, desc=['TIRO PELO', 'TECLADO VAI', 'NA CABEÇA', '3 RODADAS']),
            dict(id='bolso', rar='COMUM', name='BOLSO DO PADRE', col='#c8a878', w=5, desc=['+50% DE', 'DINHEIRO', 'POR', '3 RODADAS']),
            dict(id='fe', rar='COMUM', name='FÉ NO AÇO', col='#b8b8c0', w=5, desc=['SUA ARMA', 'NÃO FALHA', 'POR', '3 RODADAS'])]
def draw_cards():
    pool = list(range(len(CARDS))); out = []
    for _ in range(3):
        tot = sum(CARDS[i]['w'] for i in pool); r = RND() * tot
        for i in pool:
            r -= CARDS[i]['w']
            if r <= 0: out.append(i); pool.remove(i); break
        else: out.append(pool.pop())
    random.shuffle(out); return out
def card_icon(p, cid, cx_, cy_):
    if cid == 'tempo':
        p.R(cx_ - 9, cy_ - 13, 18, 3, '#6a4a20'); p.R(cx_ - 9, cy_ + 11, 18, 3, '#6a4a20')
        for r in range(10): ww = 8 - r * .8; p.R(cx_ - ww, cy_ - 10 + r, ww * 2, 1, '#c8e0f0'); p.R(cx_ - ww, cy_ + 10 - r, ww * 2, 1, '#c8e0f0')
        p.R(cx_ - 4, cy_ + 5, 8, 4, '#e0b040'); p.R(cx_ - 1, cy_ - 2, 2, 6, '#e0b040')
    elif cid == 'dupla':
        for bx in (cx_ - 9, cx_ + 3): p.R(bx, cy_ - 6, 6, 16, '#d8a830'); p.R(bx, cy_ - 12, 6, 6, '#a8a8b0'); p.R(bx + 1, cy_ - 14, 4, 2, '#a8a8b0'); p.R(bx, cy_ - 6, 2, 16, '#f8e080')
    elif cid == 'anjo':
        p.EL(cx_, cy_ - 11, 7, 2, '#f8e060'); p.EL(cx_, cy_ - 11, 5, 1, '#e8dcc0')
        for d in (-1, 1):
            for r in range(8): p.R(cx_ + d * (4 + r) - (2 if d < 0 else 0), cy_ - 6 + r, 3, 10 - r, '#f8f8ff' if r % 2 else '#d8d8f0')
        p.EL(cx_, cy_ + 2, 4, 6, '#efe6cd'); p.R(cx_ - 2, cy_, 2, 2, '#1a0a06'); p.R(cx_ + 1, cy_, 2, 2, '#1a0a06')
    elif cid == 'lince':
        p.EL(cx_, cy_, 13, 7, '#f8f4e0'); p.EL(cx_, cy_, 6, 6, '#40b060'); p.EL(cx_, cy_, 2, 5, '#0a1a0a'); p.P(cx_ + 2, cy_ - 3, '#ffffff')
        for k in (-12, 12): p.TL(cx_ + k, cy_, cx_ + k * 1.2, cy_ - 4, 1, '#2a2010')
    elif cid == 'bolso':
        p.EL(cx_, cy_ + 3, 10, 9, '#a07848'); p.R(cx_ - 4, cy_ - 9, 8, 4, '#a07848'); p.R(cx_ - 5, cy_ - 6, 10, 2, '#5a3a20'); raw(p.s, '$', cx_ - 2, cy_ - 1, 1, '#f0d040')
    else:
        p.EL(cx_, cy_, 11, 12, '#8a8a92'); p.EL(cx_, cy_, 9, 10, '#c8c8d0'); p.R(cx_ - 1, cy_ - 7, 3, 14, '#8a1818'); p.R(cx_ - 5, cy_ - 3, 11, 3, '#8a1818')
def draw_card(cx, y, ci, face, scalex=1., hl=False):
    w = max(1, int(84 * abs(scalex))); h = 112; x = int(cx - w / 2)
    if hl: canvas.fill(C('#fff0a0'), (x - 3, y - 3, w + 6, h + 6))
    canvas.fill(C(DARK), (x - 1, y - 1, w + 2, h + 2))
    if w < 6: return
    s = S(84, 112); p = Pt(s)
    if face:
        cd = CARDS[ci]; col = cd['col']; p.R(0, 0, 84, 112, shade(col, .45)); p.R(2, 2, 80, 108, '#f2e8d2'); p.R(4, 4, 76, 104, '#e8dcc0'); p.R(4, 4, 76, 12, col)
        raw(s, cd['rar'], 42 - len(cd['rar']) * 3, 7, 1, '#1a0a06'); card_icon(p, cd['id'], 42, 38)
        raw(s, cd['name'], 42 - len(cd['name']) * 3, 58, 1, '#2a1410')
        for i, l in enumerate(cd['desc']): raw(s, l, 42 - len(l) * 3, 70 + i * 9, 1, '#4a3020')
    else:
        p.R(0, 0, 84, 112, '#5a1014'); p.R(3, 3, 78, 106, '#7a1a1e'); p.R(6, 6, 72, 100, '#5a1014')
        for yy in range(10, 104, 8):
            for xx in range(10 + (yy // 8) % 2 * 4, 76, 8): p.P(xx, yy, '#9a2a2a')
        p.R(38, 30, 8, 52, '#e0b040'); p.R(24, 44, 36, 8, '#e0b040'); p.R(38, 30, 2, 52, '#f8e080'); p.EL(42, 92, 7, 6, '#efe6cd'); p.R(39, 91, 2, 2, '#1a0a06'); p.R(43, 91, 2, 2, '#1a0a06')
    if w != 84: s = pygame.transform.scale(s, (w, 112))
    canvas.blit(s, (x, y))

# ---------------------------------------------------------------- duelo: início, contagem, diálogo
_start_duel_orig = start_duel
def start_duel():
    _start_duel_orig(); D, E = g.D, g.E; b = D.op.get('boss')
    D.loucasFight = b == 'loucas' and RND() < .05; D.caption = None; D.long = False; D.six = False; D.coco = None
    g.plane = None; g.car = None; g.heli = None; g.horse = None; g.bgpl = []
    for q in ('six0', 'six1'): ze(q)
    if b in ('arthur', 'loucas'): E.hidden = True; E.x = 430
    if g.theme in ('city', 'suburb'): audio.ambient(None)
    if b == 'arthur': audio.music('arthur', .75)
def intro_update(dt, now):
    D, P, E = g.D, g.P, g.E; boss = D.op.get('boss'); fx = {'fire': (horse_update, 5.4), 'arthur': (plane_update, 5.0), 'loucas': (car_update, 4.4)}.get(boss)
    k = ease(min(1, g.T / 2.6)); walking = g.T < 2.6; P.x = lerp(-30, 118, k)
    if fx: fx[0](dt)
    elif boss != 'krieger': E.x = lerp(W + 30, 362, k)
    f = int(g.T * 8) % 4
    if walking:
        P.pose = 'walk%d' % f
        if not boss: E.pose = 'walk%d' % ((f + 1) % 4)
        if f in (0, 2) and D.walkf != f: audio.play('step', .7)
        D.walkf = f
    else:
        P.pose = 'idle'
        if not boss: E.pose = 'idle'
    if g.S != 'intro': return
    end = fx[1] if fx else 3.0
    if boss == 'loucas' and not D.loucasFight: end = 99
    if g.T > end:
        g.horse = None
        if boss == 'krieger': st('rise'); D.coffin = dict(y=GY + 26, lid=True); audio.play('rumble')
        elif D.op.get('voice'): start_dialog()
        elif not boss and D.op.get('vg') and RND() < VOICE_CHANCE: start_dialog(pick(VG[D.op['vg']]))
        else: begin_standoff()
def start_dialog(vname=None):
    D = g.D; g.horse = None; st('dialog'); vname = vname or D.op.get('voice'); n = audio.voice(vname) if vname else 0
    D.dlgLen = max(2.2 if D.op.get('boss') else 1.2, n + .3)
def begin_count():
    D = g.D; L = D.L; iv = max(.42, 1.05 - .07 * (L - 1)); es = D.op.get('lang') == 'es'
    if D.op.get('boss') == 'arthur':
        seq = [dict(t=0., txt='1...', num='1')]; t = 0.
        for txt, num in (('2...', '2'), ('3! ATIRE!', 'ATIRE!'), ('4...', '4')):
            t += iv * (.95 + RND() * .15); seq.append(dict(t=t, txt=txt, num=num))
        t += iv * .6 + RND() * .9; seq.append(dict(t=t, txt='5! AGORA SIM!', go=True))
        D.seq = seq; D.beat = seq[1]['t'] + .35; D.num = None; st('count'); return
    wd = ['UNO...', 'DOS...', '¡TRES!', 'DOS Y MEDIO...'] if es else ['1...', '2...', '3!', '2 E MEIO...']
    seq = [dict(t=0., txt=wd[0], num='1')]; t = iv * (.9 + RND() * .2); seq.append(dict(t=t, txt=wd[1], num='2'))
    if L >= 3 and RND() < min(.5, .12 + .04 * L): t += iv * (.9 + RND() * .2); seq.append(dict(t=t, txt=wd[3], num='2,5'))
    t += iv * .5 + RND() * max(.5, 2.3 - .15 * L); seq.append(dict(t=t, txt=wd[2], go=True))
    D.seq = seq; D.beat = seq[1]['t'] + .35; D.num = None; st('count')

# ---------------------------------------------------------------- tiros do inimigo, anjo da guarda
THROWN = ('bricks', 'pans')
_PROJ = {}
def proj_spr(wid, k):
    key = (wid, k % 4)
    if key in _PROJ: return _PROJ[key]
    if wid == 'bricks':
        col = ['#d02a2a', '#2a5ad0', '#f0d020', '#3aa03a'][k % 4]; s = S(12, 9); p = Pt(s)
        p.R(1, 3, 10, 6, col); p.R(1, 3, 10, 1, shade(col, 1.3)); p.R(2, 1, 3, 2, col); p.R(7, 1, 3, 2, col); p.R(1, 8, 10, 1, shade(col, .6))
    elif k % 2 == 0:
        s = S(22, 10); p = Pt(s); p.R(0, 4, 9, 2, '#3a2a20'); p.EL(15, 5, 6, 4, '#2a2a30'); p.EL(15, 4, 5, 2, '#5a5a64')
    else:
        s = S(10, 7); p = Pt(s); p.R(0, 0, 10, 4, '#f0d040'); p.R(0, 4, 10, 3, '#3a8a3a'); p.P(2, 1, '#c8a830'); p.P(6, 2, '#c8a830')
    s = finalize(s); _PROJ[key] = s; return s
def part_proj(cv, p, x, y, k):
    r = rotq(p['spr'], round(math.degrees(p['rot']) / 30) * 30); cv.blit(r, (x - r.get_width() // 2, y - r.get_height() // 2))
def part_coco(cv, p, x, y, k): cv.fill(C('#140a06'), (x - 3, y - 3, 7, 7)); cv.fill(C('#6a3a1a'), (x - 2, y - 2, 5, 5)); cv.fill(C('#8a5a2a'), (x - 1, y - 2, 2, 1))
PART_EXT = {'proj': part_proj, 'coco': part_coco}
def enemy_fire(kill=True):
    D, E, P = g.D, g.E, g.P; E.pose = 'recoil'; E.poseT = .12; spr = eSpr(); n = len(spr.muz) or 1; wid = D.op['wid']
    rifle = wid == 'rifle'; thrown = wid in THROWN; shots = 3 if (rifle or thrown) else n
    for k in range(shots):
        def f(k=k):
            if not g.D: return
            if thrown:
                m = eSpr().muz[0] if eSpr().muz else (AX + 30, 40); mx, my = to_world(E, *m); tx, ty = P.x + 2 + RND() * 4, GY - 64 + k * 12; life = .2
                audio.play('whoosh', .6); addp(type='proj', spr=proj_spr(wid, k + (0 if wid == 'bricks' else int(RND() * 2))), x=mx, y=my, vx=(tx - mx) / life, vy=(ty - my) / life, vr=14 * (1 if k % 2 else -1), life=life)
                def hit(tx=tx, ty=ty):
                    audio.play('pan' if wid == 'pans' else 'brick')
                    for i in range(8): addp(x=tx, y=ty, vx=(RND() - .5) * 140, vy=-RND() * 120, g=320, life=.7, s=2, ground=GY,
                                            c=pick(['#d02a2a', '#2a5ad0', '#f0d020', '#3aa03a']) if wid == 'bricks' else pick(['#f0d040', '#3a8a3a', '#8a8a90', '#ffffff']))
                D.ev.append(dict(at=g.T + life, fn=hit))
            else:
                audio.play('rifle' if rifle else 'shot'); mx, my = muzzle_fx(E, eSpr(), k % n); D.tracers.append(dict(x1=mx, y1=my, x2=P.x + 2, y2=GY - 52 + k * 6, t=.06))
        D.ev.append(dict(at=g.T + k * (.07 if rifle else .13 if thrown else .09), fn=f))
    if kill:
        RUN['hearts'] = max(0, RUN['hearts'] - 1)
        if thrown: D.ev.append(dict(at=g.T + .2, fn=skel_die))
        else: skel_die()
def angel_ready(): return bless('anjo') and not getattr(g.D, 'angelUsed', False)
def angel_save():
    D, P, E = g.D, g.P, g.E; D.angelUsed = True; SAVE['active'] = None; save(); now = pygame.time.get_ticks()
    P.flash = .3; D.msg = 'ANJO DA GUARDA!'; D.msgT = 0; audio.play('bless')
    for i in range(40): addp(type='ember', x=P.x + (RND() - .5) * 30, y=GY - 40 + (RND() - .5) * 60, vy=-20 - RND() * 30, life=1.4, c=pick(['#ffffff', '#fff0a0', '#f8d8ff']))
    st('go'); D.enemyAt = now + (D.delay + .7) * 1000; E.pose = 'idle'
def enemy_shoots():
    D = g.D
    if D.op.get('boss') == 'krieger' and not getattr(D, 'brk', False):
        D.brk = True
        if RND() < .10: krieger_break(); return
    if angel_ready(): angel_save(); enemy_fire(kill=False); return
    D.result = 'slow'; st('resolve'); D.ev = []; D.big = dict(txt='LENTO DEMAIS!', red=True); enemy_fire(); D.endAt = 3.0
    if D.op['wid'] not in THROWN: D.ev.append(dict(at=.3, fn=lambda: (audio.play('ricochet'), sparks(466, 204))))
    ln = {'fire': '¡ADIÓS, CALAVERA!', 'krieger': 'ALVO ABATIDO.', 'arthur': 'MISSÃO CUMPRIDA.', 'loucas': 'VAI LAVAR LOUÇA NO INFERNO!'}.get(D.op.get('boss'))
    if ln: D.ev.append(dict(at=.6, fn=lambda: say(ln)))
def jam_fail():
    D, P, E = g.D, g.P, g.E
    if angel_ready():
        D.jam = None; P.dodge = None; P.jy = 0; P.pose = 'aim'; P.nextShot = pygame.time.get_ticks() + 250; g.tscale = 1.; angel_save(); return
    D.result = 'jam'; st('resolve'); D.ev = []; D.big = dict(txt='ACERTADO!', red=True); RUN['hearts'] = max(0, RUN['hearts'] - 1); skel_die(); D.endAt = 3.0; D.jam = None
def duel_press(aim):
    if g.fadeDir: return
    D = g.D
    if g.S == 'count': foul()
    elif g.S == 'go': player_fire(aim)
    elif g.S == 'resolve' and D and getattr(D, 'long', False) and D.result == 'win' and g.T > 1.5: goto('win')

# ---------------------------------------------------------------- vitória: roupas, 67, helicóptero
_enemy_die_orig = enemy_die
def enemy_die(head, explode=False):
    D = g.D; boss = D.op.get('boss'); _enemy_die_orig(head, explode)
    unlock = {'krieger': 'farda', 'arthur': 'especial', 'loucas': 'maid'}.get(boss)
    if unlock and unlock not in SAVE['ownS']: SAVE['ownS'].append(unlock); D.unlock = True; D.unlockName = SKMAP[unlock]['name']; save()
    if D.rt is not None and '67' in ('%.3f' % D.rt).replace('.', ''): D.six = True; audio.play('aura')
    if getattr(D, 'coco', None):
        D.bonusList.insert(0, 'MORTE POR COCO +$300'); SAVE['money'] += 300; D.reward += 300; D.big = dict(txt='BONK!', sub='MORTE POR COCO!'); D.endAt = 4.2; save()
    elif boss == 'krieger': D.endAt = 11.5; D.long = True; D.ev.append(dict(at=1.8, fn=heli_start))
def krieger_break():
    D, E = g.D, g.E; st('resolve'); D.result = 'pending'; D.ev = []; D.big = None; D.long = False; D.endAt = 99; D.coco = dict(walk=None, y=None)
    audio.play('jam'); E.pose = 'aim'; say('ARMA QUEBROU?!')
    def toss():
        E.pose = 'idle'; x, y = to_world(E, AX + 30, 40); gs = gun_sprite(WMAP['rifle']).s
        addp(type='spr', spr=gs, x=x, y=y, vx=40, vy=-140, vr=10, g=380, life=6, ground=GY - 3, face=1, ox=19, oy=5); say('LIXO!')
    def walk(): D.coco['walk'] = g.T; E.face = 1
    def kick(): E.recoil = 1.; g.shake = 4; audio.play('thud'); say('ÁRVORE MALDITA!'); D.coco['shake'] = g.T
    def fall(): D.coco['y'] = 104.; D.coco['t0'] = g.T
    D.ev = [dict(at=.6, fn=toss), dict(at=1.1, fn=walk), dict(at=2.3, fn=kick), dict(at=2.7, fn=fall)]
def heli_start():
    E = g.E; g.heli = dict(D=g.D, t0=g.T, x=W + 90., y=-50., coffin=False, cx=E.x + 5, cy=GY - 2., snd=0); audio.play('heli')
def heli_update(dt):
    h = g.heli; D, E = g.D, g.E
    if not h or h['D'] is not D: return
    t = g.T - h['t0']; tx = h['cx']
    lx = tx + 78
    if t < 2.6: k = ease(t / 2.6); h['x'] = lerp(W + 90, lx, k); h['y'] = lerp(-50, GY - 90, k)
    elif t < 3.4: h['x'] = lx; h['y'] = lerp(GY - 90, GY - 44, ease((t - 2.6) / .8))
    elif t < 4.6:
        h['y'] = GY - 44
        if not h['coffin']: h['coffin'] = True; E.gone = True; D.caption = 'HONRAS MILITARES'; audio.play('bless', .7); dust_puff(tx, GY - 2, 20)
    elif t < 5.6: k = ease((t - 4.6) / 1.); h['x'] = lerp(lx, tx, k); h['y'] = lerp(GY - 44, GY - 120, k)
    elif t < 6.6: k = ease((t - 5.6) / 1.); h['x'] = tx; h['y'] = GY - 120; h['cy'] = lerp(GY - 2, GY - 120 + 44 + 34, k); h['cable'] = True
    else: h['x'] += 120 * dt; h['y'] -= 60 * dt; h['cy'] = h['y'] + 78; h['cx'] = h['x']
    if 2.0 < t < 4.8 and RND() < .6: addp(type='smoke', x=tx + (RND() - .5) * 120, y=GY - 2, vx=(RND() - .5) * 160, vy=-RND() * 20, life=.8, s=3, c='#c8a878')
    if g.time > h['snd']: h['snd'] = g.time + 1.4; audio.play('heli', .7)

# ---------------------------------------------------------------- intros: avião e carro
_SPR = {}
def spr_plane():
    if 'plane' in _SPR: return _SPR['plane']
    s = S(70, 26); p = Pt(s); p.R(8, 10, 54, 7, '#d8d8dc'); p.EL(9, 13, 5, 3, '#d8d8dc'); p.R(8, 13, 54, 1, '#c02020'); p.R(8, 16, 54, 1, '#a8a8b0')
    p.R(14, 10, 9, 2, '#3a5a7a'); p.R(25, 10, 3, 2, '#3a5a7a'); p.R(30, 10, 3, 2, '#3a5a7a'); p.R(24, 16, 22, 3, '#b8b8c0'); p.TL(58, 10, 64, 2, 3, '#d8d8dc'); p.R(56, 11, 12, 2, '#c8c8d0')
    p.R(2, 6, 2, 14, '#8a8a90'); p.R(1, 12, 4, 3, '#4a4a50'); s = finalize(s); _SPR['plane'] = s; return s
def spr_wreck():
    if 'wreck' in _SPR: return _SPR['wreck']
    s = S(80, 24); p = Pt(s); p.EL(40, 16, 34, 7, '#2a2a2e'); p.R(10, 10, 40, 6, '#4a4a50'); p.R(52, 4, 4, 14, '#3a3a40'); p.TL(58, 18, 76, 8, 3, '#5a5a62'); p.R(20, 12, 10, 2, '#8a2a20')
    for i in range(10): p.P(8 + i * 6, 14 + (i % 3), '#ff7a1a')
    s = finalize(s); _SPR['wreck'] = s; return s
def spr_car(burnt=False):
    k = 'carb' if burnt else 'car'
    if k in _SPR: return _SPR[k]
    s = S(80, 36); p = Pt(s); b = ramp('#2a2426' if burnt else '#e890b0')
    p.R(4, 17, 70, 10, b[2]); p.EL(39, 16, 24, 12, b[2]); p.EL(40, 12, 20, 8, b[3]); p.R(4, 17, 70, 1, b[3])
    p.EL(15, 21, 11, 7, b[2]); p.EL(63, 21, 11, 7, b[2]); p.R(4, 26, 70, 2, b[1])
    gl = '#3a3a40' if burnt else '#a8d0e8'; p.R(26, 7, 14, 8, gl); p.R(42, 7, 13, 8, gl); p.R(40, 6, 2, 10, b[1])
    if not burnt:
        p.P(28, 8, '#ffffff'); p.EL(8, 18, 4, 4, '#f0f0e0'); p.P(7, 17, '#ffffff')
        for i in range(5): p.TL(5 + i * 2, 14, 2 + i * 3, 9, 1, '#141414')
    else:
        for i in range(12): p.P(6 + i * 6, 18 + i % 4, '#ff7a1a')
    p.R(0, 24, 10, 3, '#d8d8e0' if not burnt else '#3a3a3a'); p.R(70, 24, 10, 3, '#d8d8e0' if not burnt else '#3a3a3a')
    for wx in (16, 62): p.EL(wx, 29, 6, 6, '#141414'); p.EL(wx, 29, 3, 3, '#c0c0c8' if not burnt else '#4a4a4a')
    s = finalize(s); _SPR[k] = s; return s
def spr_heli():
    if 'heli' in _SPR: return _SPR['heli']
    s = S(112, 46); p = Pt(s); o = ramp('#4e5a34')
    p.R(58, 20, 42, 5, o[2]); p.R(58, 20, 42, 1, o[3]); p.R(96, 6, 6, 16, o[2]); p.EL(40, 24, 24, 12, o[2]); p.EL(42, 20, 20, 7, o[3])
    p.EL(24, 22, 10, 8, '#8ab0c0'); p.EL(22, 20, 6, 4, '#c0e0f0'); p.R(40, 8, 4, 6, o[1])
    p.EL(50, 26, 5, 5, '#1e8a3a'); p.EL(50, 26, 3, 3, '#f0d020'); p.EL(50, 26, 1, 1, '#2a3a9a')
    p.R(22, 40, 46, 2, '#2a2a20'); p.R(28, 34, 2, 6, '#2a2a20'); p.R(58, 34, 2, 6, '#2a2a20')
    s = finalize(s); _SPR['heli'] = s; return s
def spr_flagcoffin():
    if 'flag' in _SPR: return _SPR['flag']
    s = S(92, 22); p = Pt(s); p.R(0, 8, 92, 14, '#4a3020'); p.R(0, 8, 92, 1, '#6a4a30')
    p.R(-1, 3, 94, 11, '#1e8a3a'); p.R(0, 3, 92, 1, '#2aa04a')
    for dy in range(-5, 6): w = int(17 * (1 - abs(dy) / 5.6)); p.R(46 - w, 8 + dy, 2 * w, 1, '#f0d020')
    p.EL(46, 8, 5, 4, '#2a3a9a'); p.R(41, 8, 10, 1, '#f0f0f0')
    s = finalize(s); _SPR['flag'] = s; return s
def plane_update(dt):
    D, E = g.D, g.E; T = g.T
    if not getattr(g, 'plane', None) or g.plane.get('D') is not D: g.plane = dict(D=D, x=W + 80., y=20., ang=0., crashed=False); E.hidden = True; E.x = 430
    pl = g.plane
    if T < 2.2:
        k = max(0., (T - .2) / 2.); pl['x'] = lerp(W + 80, 400, k); pl['y'] = lerp(20, GY - 12, k * k); pl['ang'] = lerp(5, 32, k)
        if T > .2 and not pl.get('snd'): pl['snd'] = True; audio.play('plane')
        if RND() < .8: addp(type='smoke', x=pl['x'] + 30, y=pl['y'] - 4, vx=20, vy=-10, life=1.4, s=3, c='#5a5a5a')
        if k > .5 and RND() < .5: addp(type='fire', x=pl['x'] + 20, y=pl['y'], vx=30, vy=-20, life=.4, s=2)
    elif not pl['crashed']:
        pl['crashed'] = True; audio.play('explode'); audio.play('burst'); audio.play('crash'); g.shake = 11
        for i in range(70): addp(type='fire', x=400 + (RND() - .5) * 50, y=GY - 10 - RND() * 30, vx=(RND() - .5) * 200, vy=-60 - RND() * 160, life=.5 + RND() * .6, s=2 + int(RND() * 2))
        for i in range(25): addp(type='chunk', x=400, y=GY - 15, vx=(RND() - .5) * 260, vy=-80 - RND() * 200, g=420, life=4, s=2 + int(RND() * 2), c=pick(['#8a8a90', '#5a5a60', '#c02020', '#d8d8dc']), ground=GY + (RND() * 8 - 3))
        for i in range(25): addp(type='smoke', x=400 + (RND() - .5) * 60, y=GY - 20, vx=(RND() - .5) * 60, vy=-20 - RND() * 40, life=2, s=4, c='#3a3a3a')
    if pl['crashed']:
        if RND() < .6: addp(type='fire', x=385 + RND() * 40, y=GY - 8 - RND() * 8, vx=(RND() - .5) * 10, vy=-30 - RND() * 30, life=.5, s=2)
        if RND() < .3: addp(type='smoke', x=395 + RND() * 20, y=GY - 20, vx=10, vy=-25, life=2, s=3, c='#2a2a2a')
    if 2.8 < T < 4.2: E.hidden = False; k = (T - 2.8) / 1.4; E.x = lerp(430, 362, k); E.pose = 'walk%d' % (int(T * 8) % 4)
    elif T >= 4.2: E.hidden = False; E.x = 362; E.pose = 'idle'
def car_update(dt):
    D, E = g.D, g.E; T = g.T
    if not getattr(g, 'car', None) or g.car.get('D') is not D: g.car = dict(D=D, x=W + 60., burnt=False, hit=False, pole=0.); E.hidden = True; E.x = 420
    c = g.car
    if D.loucasFight:
        if T < 1.8: c['x'] = lerp(W + 60, 432, ease(T / 1.8))
        if T > .1 and not c.get('snd'): c['snd'] = True; audio.play('engine')
        if 1.6 < T < 1.7 and not c.get('br'): c['br'] = True; audio.play('screech', .6)
        if 2.2 < T < 3.6: E.hidden = False; k = (T - 2.2) / 1.4; E.x = lerp(420, 362, k); E.pose = 'walk%d' % (int(T * 8) % 4)
        elif T >= 3.6: E.hidden = False; E.x = 362; E.pose = 'idle'
        if T > 2.2: D.caption = 'ELA CHEGOU INTEIRA... DESSA VEZ.'
        return
    if T < 1.3:
        c['x'] = lerp(W + 60, 338, (T / 1.3) ** 1.1)
        if not c.get('snd'): c['snd'] = True; audio.play('engine')
        if T > .9 and not c.get('sc'): c['sc'] = True; audio.play('screech')
    elif not c['hit']:
        c['hit'] = True; c['x'] = 338; c['pole'] = 1.; audio.play('crash'); audio.play('glass'); g.shake = 9
        for i in range(24): addp(x=304 + RND() * 6, y=GY - 18 - RND() * 10, vx=(RND() - .5) * 160, vy=-40 - RND() * 120, g=380, life=1.2, c=pick(['#c8e8f8', '#ffffff', '#a8d0e8']), ground=GY + RND() * 6)
    if c['hit'] and not c['burnt'] and RND() < .5: addp(type='smoke', x=310 + RND() * 10, y=GY - 22, vx=(RND() - .5) * 10, vy=-25, life=1.5, s=3, c='#8a8a8a')
    if T > 3.0 and not c['burnt']:
        c['burnt'] = True; audio.play('explode'); audio.play('burst'); g.shake = 13
        for i in range(90): addp(type='fire', x=338 + (RND() - .5) * 70, y=GY - 10 - RND() * 30, vx=(RND() - .5) * 240, vy=-60 - RND() * 200, life=.5 + RND() * .7, s=2 + int(RND() * 2))
        for i in range(30): addp(type='chunk', x=338, y=GY - 15, vx=(RND() - .5) * 300, vy=-80 - RND() * 240, g=420, life=4, s=2, c=pick(['#e890b0', '#141414', '#d8d8e0', '#ffffff']), ground=GY + (RND() * 8 - 3))
        for i in range(10): addp(type='proj', spr=proj_spr('pans', i), x=338, y=GY - 20, vx=(RND() - .5) * 260, vy=-120 - RND() * 160, vr=(RND() - .5) * 20, g=420, life=1.6)
    if c['burnt']:
        if RND() < .7: addp(type='fire', x=310 + RND() * 60, y=GY - 10 - RND() * 14, vx=(RND() - .5) * 10, vy=-30 - RND() * 40, life=.6, s=2)
        if RND() < .3: addp(type='smoke', x=320 + RND() * 40, y=GY - 30, vx=8, vy=-25, life=2.2, s=4, c='#2a2a2a')
    if T > 3.4: D.caption = 'A LOUÇAS GIRL BATEU NO POSTE!'
    if T > 5.8 and g.S == 'intro': crash_win()
def crash_win():
    D, E = g.D, g.E; D.result = 'win'; D.crash = True; st('resolve'); D.ev = []; D.endAt = 2.4; D.rt = None; E.gone = True
    D.reward = int((60 + 30 * D.L + 500) * (1 + .15 * sk('ganancia'))); SAVE['money'] += D.reward; RUN['wins'] += 1; SAVE['sp'] += 3; SAVE['bless'] += 1
    D.heal = False
    if RUN['wins'] % 5 == 0 and RUN['hearts'] < max_hearts(): RUN['hearts'] += 1; D.heal = True
    D.bonusList = ['ACIDENTE FATAL +$500']; D.big = dict(txt='KABUM!', sub='VITÓRIA POR ACIDENTE'); D.newBest = False; D.unlock = False; save()

# ---------------------------------------------------------------- atualização e desenho extras
def extra_update(rdt):
    D, P, E = g.D, g.P, g.E
    if not D or g.S not in DUEL_STATES: return
    dt = rdt * g.tscale
    if g.heli: heli_update(dt)
    if getattr(D, 'six', False) and g.S == 'resolve' and P and not P.dead:
        P.pose = 'six%d' % (int(g.T * 6) % 2)
        if RND() < .7: addp(type='ember', x=P.x + (RND() - .5) * 40, y=GY - 20 - RND() * 70, vy=-30 - RND() * 30, life=1.2, c=pick(['#c060ff', '#ffd060', '#60e0ff', '#ffffff']))
    co = getattr(D, 'coco', None)
    if co and g.S == 'resolve':
        if co.get('walk') is not None and E.x < 420 and not E.dead:
            E.x = min(420, E.x + 60 * dt); E.pose = 'walk%d' % (int(g.T * 8) % 4)
            if E.x >= 420: E.pose = 'idle'
        if co.get('y') is not None and not co.get('bonk'):
            t = g.T - co['t0']; co['y'] = 104 + 220 * t * t
            hy = SPR_TOP + 20
            if co['y'] >= hy:
                co['bonk'] = True; co['y'] = hy; audio.play('bonk'); g.shake = 6; say('...')
                hx = E.x + 1
                for i in range(12): addp(type='ember', x=hx + (RND() - .5) * 16, y=hy - 4 + (RND() - .5) * 8, vx=(RND() - .5) * 60, vy=-30 - RND() * 30, life=.9, c=pick(['#ffff60', '#ffffff']))
                addp(type='coco', x=hx, y=hy, vx=50, vy=-120, g=420, life=4, ground=GY - 3)
                D.ev.append(dict(at=g.T + .5, fn=lambda: enemy_die(True)))
    if g.theme == 'city':
        if RND() < rdt * .25 and len(g.bgpl) < 2:
            x0 = -30. if RND() < .5 else W + 30.; g.bgpl.append(dict(x=x0, y=20 + RND() * 50, v=40. if x0 < 0 else -40.))
        for pl in g.bgpl: pl['x'] += pl['v'] * rdt
        g.bgpl = [pl for pl in g.bgpl if -40 < pl['x'] < W + 40]
def draw_bg_extras():
    D = g.D
    if g.theme == 'city':
        for pl in getattr(g, 'bgpl', []):
            x, y = int(pl['x']), int(pl['y']); c = C('#100c1c'); canvas.fill(c, (x - 6, y, 13, 2)); canvas.fill(c, (x - 1, y - 2, 4, 6)); canvas.fill(c, (x + (5 if pl.get('v', 1) < 0 else -7), y - 2, 2, 3))
            if int(g.time * 3) % 2: canvas.fill(C('#ff3030'), (x, y + 2, 1, 1))
    if g.theme == 'suburb':
        car = getattr(g, 'car', None); ang = 22 if car and car.get('D') is D and car.get('pole') else 0
        ps = _SPR.get('pole')
        if ps is None:
            ps = S(30, 100); pp = Pt(ps); pp.R(12, 0, 5, 100, '#5a3a20'); pp.R(12, 0, 1, 100, '#7a5a30'); pp.R(2, 8, 26, 3, '#4a2a18'); pp.P(3, 7, '#d8d8d0'); pp.P(26, 7, '#d8d8d0'); pp.R(16, 30, 6, 8, '#6a6a70'); ps = finalize(ps); _SPR['pole'] = ps
        line(canvas, 0, 128, 300, 120 + (8 if ang else 0), '#2a2a2a'); line(canvas, 300, 120 + (8 if ang else 0), W, 132, '#2a2a2a')
        if ang: rot_blit(canvas, ps, (14, 99), ang, (300, GY - 12))
        else: canvas.blit(ps, (286, GY - 112))
    if g.theme == 'amazon' and D and D.op.get('boss') == 'krieger':
        sh = 0
        co = getattr(D, 'coco', None)
        if co and co.get('shake') and g.T - co['shake'] < .6: sh = int(math.sin(g.T * 60) * 2)
        for i in range(12):
            y = 212 - i * 9; x = 446 - int((i / 12) ** 2 * 14) + (sh if i > 6 else 0); canvas.fill(C('#5a4a2a'), (x, y - 9, 6, 10)); canvas.fill(C('#3a2e1a'), (x, y - 1, 6, 1))
        tx, ty = 432 + sh, 104
        for a in range(-60, 241, 30):
            r = math.radians(a); line(canvas, tx, ty, tx + math.cos(r) * 26, ty - math.sin(r) * 10 + 12, '#2a6a2a'); line(canvas, tx, ty + 1, tx + math.cos(r) * 24, ty - math.sin(r) * 9 + 13, '#3a8a3a')
        n = 3 if not (co and co.get('y') is not None) else 2
        for i in range(n): canvas.fill(C('#140a06'), (tx - 6 + i * 5, ty + 1, 6, 6)); canvas.fill(C('#6a3a1a'), (tx - 5 + i * 5, ty + 2, 4, 4))
def draw_fg_extras():
    D = g.D
    pl = getattr(g, 'plane', None)
    if pl and pl.get('D') is D:
        if not pl['crashed']: r = rotq(spr_plane(), round(pl['ang'] / 5) * 5); canvas.blit(r, (int(pl['x'] - r.get_width() / 2), int(pl['y'] - r.get_height() / 2)))
        else: canvas.blit(spr_wreck(), (396, GY - 22))
    car = getattr(g, 'car', None)
    if car and car.get('D') is D: canvas.blit(spr_car(car['burnt']), (int(car['x'] - 40), GY - 34))
    co = getattr(D, 'coco', None) if D else None
    if co and co.get('y') is not None and not co.get('bonk'): part_coco(canvas, None, int(432), int(co['y']), 1)
    h = getattr(g, 'heli', None)
    if h and h['D'] is D:
        hs = spr_heli(); hx, hy = int(h['x'] - 44), int(h['y'])
        if h['coffin']:
            cx, cy = int(h['cx']), int(h['cy'])
            if h.get('cable'): line(canvas, hx + 30, hy + 42, cx - 30, cy - 18, '#141414'); line(canvas, hx + 60, hy + 42, cx + 30, cy - 18, '#141414')
            canvas.blit(spr_flagcoffin(), (cx - 46, cy - 20))
        canvas.blit(hs, (hx, hy)); rl = 50 if int(g.time * 20) % 2 else 18; canvas.fill(C('#1a1a14'), (hx + 42 - rl, hy + 7, rl * 2, 2))
        tr = 6 if int(g.time * 24) % 2 else 2; canvas.fill(C('#1a1a14'), (hx + 99 - tr // 2, hy + 4, tr, 1)); canvas.fill(C('#1a1a14'), (hx + 99, hy + 4 - tr // 2, 1, tr))
def draw_duel_extras():
    D, P = g.D, g.P
    if g.S == 'count' and D.num == 'ATIRE!':
        dtext(canvas, 'ATIRE!', 240, 44, sc=7, col='#ff4a1c', sh='#7a1408', ext=3, ot=2, out=DARK, align='center')
        for r_ in ((140, 104, 84, 5), (256, 104, 84, 5)): canvas.fill(C(DARK), r_)
        for r_ in ((141, 105, 82, 3), (257, 105, 82, 3)): canvas.fill(C('#d83018'), r_)
    if getattr(D, 'six', False) and g.S == 'resolve':
        cols = ['#ff60c0', '#ffd060', '#60e0ff', '#a0ff60', '#c080ff']; col = cols[int(g.time * 8) % len(cols)]
        dtext(canvas, 'FARMANDO AURA', P.x, SPR_TOP - 16 + int(math.sin(g.time * 8) * 2), sc=2, col=col, sh='#2a0a3a', ext=1, align='center')
        dtext(canvas, '6 7', P.x, SPR_TOP - 30, sc=1, col='#ffffff', align='center')
    if getattr(D, 'caption', None) and (g.S == 'intro' or (g.S == 'resolve' and (getattr(D, 'crash', False) or (getattr(g, 'heli', None) and g.heli['D'] is D)))):
        dtext(canvas, D.caption, 240, 120, sc=2, col=GOLD, sh=BROWN, ext=1, align='center')
    if g.S == 'resolve' and getattr(D, 'long', False) and g.T > 1.5 and int(g.time * 2) % 2 == 0: dtext(canvas, 'ENTER: PULAR', 240, 256, col='#c8a890', align='center')


# ==================================================================== EXPANSÃO 2: debug, armas, tamanhos, ajustes
# ---------------------------------------------------------------- escala por personagem
def to_world(a, lx, ly):
    sc = getattr(a, 'scale', 1.)
    return (a.x + a.face * (lx - AX) * sc + a.offX, GY + a.bob - a.jy - (FY + 1 - ly) * sc)
def hit_test(sx, sy):
    E = g.E; es = g.D.es; sc = getattr(E, 'scale', 1.)
    lx = int(round(AX + (sx - E.x - E.offX) * E.face / sc)); ly = int(round(FY + 1 - (GY + E.bob - sy) / sc))
    def at(m, X, Y, h): return 0 <= X < SPW and 0 <= Y < h and m[Y * SPW + X]
    for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        if at(es.mask, lx + ox, ly + oy, SPH):
            if E.headless and ly + oy <= 36: continue
            return dict(type='head' if ly + oy <= 36 else 'body', lx=lx + ox, ly=ly + oy)
    if E.hat and es.hat:
        for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if at(es.hatmask, lx + ox, ly + oy, 30): return dict(type='hat', lx=lx, ly=ly)
    return dict(type='miss', lx=lx, ly=ly)
def draw_actor(a, spr, wounds=None, skel=False, pile=None):
    if not a or a.gone or a.hidden: return
    if a.dead:
        pl = pile if pile is not None else ze_pile()
        if a.face < 0: pl = flipped(pl)
        canvas.blit(pl, (int(a.x - 30), GY - 23)); return
    img = spr.s; temp = False; sc = getattr(a, 'scale', 1.)
    if wounds: img = draw_wounds(img, wounds, skel); temp = True
    if a.flash > 0:
        if temp:
            b = tob(img)
            for i in range(0, len(b), 4):
                if b[i + 3]: b[i] = b[i + 1] = b[i + 2] = 255
            img = fromb(b, img.get_size())
        else: img = tinted(img, '#ffffff')
    if a.face < 0: img = pygame.transform.flip(img, True, False) if temp else flipped(img); px = SPW - 1 - AX
    else: px = AX
    if sc != 1.: img = pygame.transform.scale(img, (int(SPW * sc), int(SPH * sc))); px = px * sc
    ang = a.rot + a.recoil * .1; lift = math.sin(a.rot) * 10 * sc
    bx, by = a.x + a.offX, GY + a.bob - lift - a.jy
    if abs(ang) < .001: canvas.blit(img, (int(round(bx - px)), int(round(by - (FY + 1) * sc))))
    else: rot_blit(canvas, img, (px, (FY + 1) * sc), math.degrees(a.face * ang), (bx, by))

# ---------------------------------------------------------------- armas novas
def gun_derringer(w):
    s = S(26, 10); p = Pt(s); m = ramp(w['metal']); gp = ramp(w['grip'])
    p.R(4, 1, 8, 2, m[2]); p.R(4, 1, 8, 1, m[3]); p.R(4, 3, 8, 1, m[1]); p.P(3, 0, m[0]); p.R(2, 4, 3, 3, gp[2]); p.P(1, 6, gp[1]); p.P(5, 4, m[0])
    return Gun(s, (12, 2), (3, 2))
def gun_pepper(w):
    s = S(26, 10); p = Pt(s); m = ramp(w['metal']); gp = ramp(w['grip'])
    p.R(4, 0, 11, 6, m[2]); p.R(4, 0, 11, 1, m[3]); p.R(4, 2, 11, 1, m[1]); p.R(4, 4, 11, 1, m[1]); p.R(15, 1, 1, 4, m[0]); p.R(2, 5, 3, 4, gp[2]); p.R(2, 5, 1, 4, gp[3]); p.P(6, 6, m[0])
    return Gun(s, (16, 2), (3, 3))
def gun_winchester(w):
    s = S(40, 10); p = Pt(s); m = ramp(w['metal']); wd = ramp(w['grip'])
    p.R(0, 3, 10, 4, wd[2]); p.R(0, 3, 10, 1, wd[3]); p.R(0, 6, 3, 2, wd[1]); p.R(10, 2, 7, 4, '#c8a040'); p.R(10, 2, 7, 1, '#f0d070')
    p.R(11, 6, 6, 1, m[1]); p.P(11, 7, m[1]); p.P(16, 7, m[1]); p.R(12, 8, 4, 1, m[1])
    p.R(17, 2, 20, 2, m[2]); p.R(17, 2, 20, 1, m[3]); p.R(17, 4, 17, 1, m[1]); p.R(18, 4, 8, 2, wd[2]); p.P(36, 1, m[4])
    return Gun(s, (37, 2), (12, 4))
def gun_cannon(w):
    s = S(26, 12); p = Pt(s); m = ramp(w['metal']); gp = ramp(w['grip'])
    p.R(4, 1, 16, 7, m[2]); p.R(4, 1, 16, 1, m[3]); p.R(4, 7, 16, 1, m[0]); p.R(19, 0, 3, 9, m[1]); p.R(8, 1, 1, 7, '#c8a040'); p.R(14, 1, 1, 7, '#c8a040')
    p.R(2, 6, 4, 5, gp[2]); p.R(2, 6, 1, 5, gp[3]); p.P(3, 0, m[0])
    return Gun(s, (22, 4), (3, 3))
GUN_EXT.update(derringer=gun_derringer, pepper=gun_pepper, winchester=gun_winchester, cannon=gun_cannon)
WEAP += [dict(id='derringer', name='DERRINGER DE BOLSO', dmg=1, cad=.14, saque=-.06, ammo=2, price=500, ln=5, metal='#c8b070', grip='#e8dcc0', desc=['O SAQUE MAIS RÁPIDO', 'DO OESTE. SÓ 2 BALAS.']),
         dict(id='pepper', name='PEPPERBOX', dmg=1, cad=.3, saque=0, ammo=12, price=900, ln=8, metal='#8a8a96', grip='#5a3420', multi=2, desc=['VÁRIOS CANOS: SAEM', '2 BALAS POR TIRO.']),
         dict(id='winchester', name='WINCHESTER 1873', dmg=2, cad=.42, saque=.02, ammo=8, price=1500, ln=0, metal='#3a3a42', grip='#9a6030', desc=['RIFLE DE ALAVANCA:', 'DANO DOBRADO, 8 BALAS.']),
         dict(id='cannon', name='CANHÃO DE MÃO', dmg=4, cad=1., saque=.06, ammo=1, price=2500, ln=0, metal='#2a2a2e', grip='#7a4a20', boom=True, desc=['UM TIRO SÓ. ACERTOU', 'A CABEÇA, EXPLODIU.'])]
WMAP.update({w['id']: w for w in WEAP})
_pf5 = player_fire
def player_fire(aim):
    before = g.P.ammo if g.P else 0; _pf5(aim)
    if g.P and g.P.ammo < before and cur_w().get('boom'): g.shake = 11; audio.play('explode', .5)
def misfire_chance():
    if g.D and getattr(g.D, 'noJam', False): return 0
    if bless('fe'): return 0
    return max(0., .05 - .01 * sk('sorte'))
def draw_shop():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'ARMARIA', 240, 8, sc=4, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center'); dtext(canvas, '$ %d' % SAVE['money'], 470, 38, sc=1, col=GOLD, align='right')
    n = len(WEAP); first = max(0, min(n - 5, g.shopSel - 2))
    for row, i in enumerate(range(first, min(n, first + 5))):
        w = WEAP[i]; y = 56 + row * 36; sel = i == g.shopSel; own = w['id'] in SAVE['ownW']; eq = SAVE['eqW'] == w['id']; hov = 10 <= g.mouse[0] < 200 and y - 4 <= g.mouse[1] < y + 28
        canvas.fill(C(DARK), (10, y - 4, 190, 32)); canvas.fill(C('#7a3a18' if sel else '#4a2a18' if hov else '#2e180e'), (11, y - 3, 188, 30))
        if sel: canvas.fill(C(GOLD), (11, y - 3, 2, 30))
        gs = gun_sprite(w).s; canvas.blit(pygame.transform.scale(gs, (52, int(52 * gs.get_height() / gs.get_width()))), (16, y + 4))
        dtext(canvas, w['name'], 74, y + 2, col=GOLD if sel else CREAM)
        dtext(canvas, 'EQUIPADA' if eq else 'COMPRADA' if own else '$ %d' % w['price'], 74, y + 14, col='#9ae07a' if eq else '#c8a890' if own else (GOLD if SAVE['money'] >= w['price'] else '#a06050'))
        def f(i=i):
            if g.shopSel == i: shop_act()
            else: g.shopSel = i; audio.play('blip', .5)
        g.buttons.append((10, y - 4, 190, 32, f))
    if first > 0: dtext(canvas, 'MAIS ACIMA', 105, 46, col='#c8a890', align='center')
    if first + 5 < n: dtext(canvas, 'MAIS ABAIXO', 105, 236, col='#c8a890', align='center')
    w = WEAP[g.shopSel]; px = 216; canvas.fill(C(DARK), (px, 52, 256, 186)); canvas.fill(C('#2a160c'), (px + 1, 53, 254, 184))
    gs = gun_sprite(w).s; sc = max(3, min(8, 220 // gs.get_width())); big = pygame.transform.scale(gs, (gs.get_width() * sc, gs.get_height() * sc))
    canvas.blit(tinted(big, '#000000'), (px + 128 - big.get_width() // 2 + 3, 63)); canvas.blit(big, (px + 128 - big.get_width() // 2, 60))
    dtext(canvas, w['name'], px + 128, 146, sc=2, col=GOLD, align='center')
    stat_bar('DANO', w['dmg'], 4, px + 12, 168, '#e04a2a', '%dX' % w['dmg']); stat_bar('CADÊNCIA', max(0, int(round((.7 - w['cad']) * 10))), 6, px + 12, 180, '#e0b040', ('%.2fS' % w['cad']).replace('.', ','))
    stat_bar('SAQUE', int(round(3 - w['saque'] * 60)), 6, px + 12, 192, '#6ac0e0', ('-' if w['saque'] <= 0 else '+') + '%dMS' % abs(round(w['saque'] * 1000)))
    stat_bar('BALAS', min(6, (w['ammo'] + 1) // 2), 6, px + 12, 204, '#c8c8c8', str(w['ammo']))
    for i, l in enumerate(w['desc']): dtext(canvas, l, px + 128, 216 + i * 9, col='#c8a890', align='center')
    own = w['id'] in SAVE['ownW']; eq = SAVE['eqW'] == w['id']
    button('EQUIPADA' if eq else 'EQUIPAR' if own else 'COMPRAR $%d' % w['price'], px + 128, 241, shop_act, align='center', bg='#2a4a1a' if eq else '#6a2a10')
    button('VOLTAR', 10, 244, back); dtext(canvas, 'SETAS: ESCOLHER · ENTER: COMPRAR/EQUIPAR · ESC: VOLTAR', 105, 262, col='#8a7058')
    if g.toast and g.toast['time'] > 0: dtext(canvas, g.toast['t'], 344, 130, sc=2, col='#ff6a4a' if g.toast['bad'] else '#9ae07a', align='center')

# ---------------------------------------------------------------- óculos do agente e cabelo rosa da maid
_he5 = head_ext
def head_ext(p, s, hx, top):
    sh = s.get('shades'); s2 = dict(s); s2['shades'] = False; _he5(p, s2, hx, top)
    if sh:
        if s['kind'] == 'skel': L1, L2, y = hx - 4, hx + 1, top + 5
        else: L1, L2, y = hx - 1, hx + 3, top + 6
        p.R(L1 - 1, y - 1, (L2 + 4) - (L1 - 1), 1, '#2a2a34'); p.R(L1 - 2, y, 2, 1, '#2a2a34')
        for L in (L1, L2):
            p.R(L, y, 4, 3, '#0e0e16'); p.R(L, y, 4, 1, '#1e2230'); p.P(L, y, '#9ac0e0'); p.P(L + 1, y + 1, '#4a6a9a'); p.P(L + 3, y + 2, '#2a3a5a')
        p.P(L1 + 4, y, '#2a2a34')
    if s.get('pinkHair'):
        hr = ramp('#ff8ac8')
        p.EL(hx, top + 1, 7, 3, hr[2]); p.R(hx - 6, top + 1, 13, 3, hr[2]); p.R(hx - 6, top + 1, 13, 1, hr[3])
        for x in range(hx - 6, hx + 7, 2): p.P(x, top + 4, hr[2])
        p.R(hx - 8, top + 2, 3, 12, hr[1]); p.TL(hx - 8, top + 6, hx - 12, top + 26, 3, hr[2]); p.TL(hx - 7, top + 6, hx - 10, top + 25, 1, hr[3])
        p.R(hx + 6, top + 2, 2, 6, hr[2]); p.P(hx - 3, top + 1, hr[4]); p.P(hx + 2, top, hr[4])
SKMAP['maid']['s']['pinkHair'] = True

# ---------------------------------------------------------------- entradas maiores: avião, carro, helicóptero
_BIG = {}
def big(key, f, sc):
    if key not in _BIG: s = f(); _BIG[key] = pygame.transform.scale(s, (int(s.get_width() * sc), int(s.get_height() * sc)))
    return _BIG[key]
def plane_update(dt):
    D, E = g.D, g.E; T = g.T
    if not getattr(g, 'plane', None) or g.plane.get('D') is not D: g.plane = dict(D=D, x=W + 150., y=6., ang=0., crashed=False); E.hidden = True; E.x = 440
    pl = g.plane; t0, t1 = .3, 4.3
    if T < t1:
        k = max(0., (T - t0) / (t1 - t0)); pl['x'] = lerp(W + 150, 410, k); pl['y'] = lerp(6, GY - 26, k ** 1.8); pl['ang'] = lerp(4, 28, k)
        if not pl.get('snd'): pl['snd'] = True; audio.play('plane')
        if RND() < .9: addp(type='smoke', x=pl['x'] + 60, y=pl['y'] - 6, vx=20, vy=-10, life=1.6, s=4, c='#5a5a5a')
        if k > .5 and RND() < .7: addp(type='fire', x=pl['x'] + 40, y=pl['y'], vx=30, vy=-20, life=.5, s=3)
    elif not pl['crashed']:
        pl['crashed'] = True; audio.play('explode'); audio.play('burst'); audio.play('crash'); g.shake = 13
        for i in range(110): addp(type='fire', x=410 + (RND() - .5) * 90, y=GY - 10 - RND() * 50, vx=(RND() - .5) * 260, vy=-60 - RND() * 200, life=.5 + RND() * .7, s=2 + int(RND() * 3))
        for i in range(35): addp(type='chunk', x=410, y=GY - 20, vx=(RND() - .5) * 320, vy=-80 - RND() * 240, g=420, life=4, s=2 + int(RND() * 3), c=pick(['#8a8a90', '#5a5a60', '#c02020', '#d8d8dc']), ground=GY + (RND() * 8 - 3))
        for i in range(35): addp(type='smoke', x=410 + (RND() - .5) * 90, y=GY - 30, vx=(RND() - .5) * 70, vy=-20 - RND() * 40, life=2.2, s=5, c='#3a3a3a')
    if pl['crashed']:
        if RND() < .8: addp(type='fire', x=370 + RND() * 90, y=GY - 8 - RND() * 14, vx=(RND() - .5) * 10, vy=-30 - RND() * 40, life=.6, s=2)
        if RND() < .4: addp(type='smoke', x=390 + RND() * 50, y=GY - 30, vx=10, vy=-25, life=2.4, s=4, c='#2a2a2a')
    if 4.9 < T < 6.3: E.hidden = False; k = (T - 4.9) / 1.4; E.x = lerp(440, 362, k); E.pose = 'walk%d' % (int(T * 8) % 4)
    elif T >= 6.3: E.hidden = False; E.x = 362; E.pose = 'idle'
CAR_SC = 1.6
def car_update(dt):
    D, E = g.D, g.E; T = g.T
    if not getattr(g, 'car', None) or g.car.get('D') is not D: g.car = dict(D=D, x=W + 90., burnt=False, hit=False, pole=0.); E.hidden = True; E.x = 420
    c = g.car
    if D.loucasFight:
        if T < 1.8: c['x'] = lerp(W + 90, 446, ease(T / 1.8))
        if not c.get('snd'): c['snd'] = True; audio.play('engine')
        if 1.6 < T and not c.get('br'): c['br'] = True; audio.play('screech', .6)
        if 2.2 < T < 3.6: E.hidden = False; k = (T - 2.2) / 1.4; E.x = lerp(420, 362, k); E.pose = 'walk%d' % (int(T * 8) % 4)
        elif T >= 3.6: E.hidden = False; E.x = 362; E.pose = 'idle'
        if T > 2.2: D.caption = 'ELA CHEGOU INTEIRA... DESSA VEZ.'
        return
    if T < 1.3:
        c['x'] = lerp(W + 90, 366, (T / 1.3) ** 1.1)
        if not c.get('snd'): c['snd'] = True; audio.play('engine')
        if T > .9 and not c.get('sc'): c['sc'] = True; audio.play('screech')
    elif not c['hit']:
        c['hit'] = True; c['x'] = 366; c['pole'] = 1.; audio.play('crash'); audio.play('glass'); g.shake = 10
        for i in range(30): addp(x=304 + RND() * 8, y=GY - 26 - RND() * 14, vx=(RND() - .5) * 180, vy=-40 - RND() * 130, g=380, life=1.2, c=pick(['#c8e8f8', '#ffffff', '#a8d0e8']), ground=GY + RND() * 6)
    if c['hit'] and not c['burnt'] and RND() < .6: addp(type='smoke', x=310 + RND() * 20, y=GY - 34, vx=(RND() - .5) * 10, vy=-25, life=1.6, s=4, c='#8a8a8a')
    if T > 3.0 and not c['burnt']:
        c['burnt'] = True; audio.play('explode'); audio.play('burst'); g.shake = 14
        for i in range(120): addp(type='fire', x=366 + (RND() - .5) * 110, y=GY - 10 - RND() * 46, vx=(RND() - .5) * 260, vy=-60 - RND() * 220, life=.5 + RND() * .8, s=2 + int(RND() * 3))
        for i in range(35): addp(type='chunk', x=366, y=GY - 20, vx=(RND() - .5) * 320, vy=-80 - RND() * 260, g=420, life=4, s=2 + int(RND() * 2), c=pick(['#e890b0', '#141414', '#d8d8e0', '#ffffff']), ground=GY + (RND() * 8 - 3))
        for i in range(12): addp(type='proj', spr=proj_spr('pans', i), x=366, y=GY - 26, vx=(RND() - .5) * 280, vy=-120 - RND() * 170, vr=(RND() - .5) * 20, g=420, life=1.6)
    if c['burnt']:
        if RND() < .8: addp(type='fire', x=306 + RND() * 120, y=GY - 10 - RND() * 22, vx=(RND() - .5) * 10, vy=-30 - RND() * 40, life=.6, s=2)
        if RND() < .35: addp(type='smoke', x=330 + RND() * 70, y=GY - 44, vx=8, vy=-25, life=2.4, s=4, c='#2a2a2a')
    if T > 3.4: D.caption = 'A LOUÇAS GIRL BATEU NO POSTE!'
    if T > 5.8 and g.S == 'intro': crash_win()
HSC = 1.6
def heli_start():
    E = g.E; g.heli = dict(D=g.D, t0=g.T, x=W + 160., y=-80., coffin=False, cx=E.x + 5, cy=GY - 2., snd=0); audio.play('heli')
def heli_update(dt):
    h = g.heli; D, E = g.D, g.E
    if not h or h['D'] is not D: return
    t = g.T - h['t0']; tx = h['cx'] if not h.get('cable') else h['cx']; lx = tx + 118
    if t < 2.6: k = ease(t / 2.6); h['x'] = lerp(W + 160, lx, k); h['y'] = lerp(-80, GY - 140, k)
    elif t < 3.4: h['x'] = lx; h['y'] = lerp(GY - 140, GY - 66, ease((t - 2.6) / .8))
    elif t < 4.6:
        h['y'] = GY - 66
        if not h['coffin']: h['coffin'] = True; E.gone = True; D.caption = 'HONRAS MILITARES'; audio.play('bless', .7); dust_puff(tx, GY - 2, 24)
    elif t < 5.6: k = ease((t - 4.6) / 1.); h['x'] = lerp(lx, tx, k); h['y'] = lerp(GY - 66, GY - 175, k)
    elif t < 6.6: k = ease((t - 5.6) / 1.); h['x'] = tx; h['y'] = GY - 175; h['cy'] = lerp(GY - 2, GY - 175 + 66 + 40, k); h['cable'] = True
    else: h['x'] += 120 * dt; h['y'] -= 60 * dt; h['cy'] = h['y'] + 106; h['cx'] = h['x']
    if 2.0 < t < 4.8 and RND() < .7: addp(type='smoke', x=h['x'] + (RND() - .5) * 180, y=GY - 2, vx=(RND() - .5) * 200, vy=-RND() * 20, life=.8, s=3, c='#c8a878')
    if g.time > h['snd']: h['snd'] = g.time + 1.4; audio.play('heli', .8)
def draw_fg_extras():
    D = g.D
    pl = getattr(g, 'plane', None)
    if pl and pl.get('D') is D:
        if not pl['crashed']:
            r = rotq(big('plane', spr_plane, 2.0), round(pl['ang'] / 4) * 4); canvas.blit(r, (int(pl['x'] - r.get_width() / 2), int(pl['y'] - r.get_height() / 2)))
        else: wk = big('wreck', spr_wreck, 1.7); canvas.blit(wk, (410 - wk.get_width() // 2, GY - wk.get_height() + 4))
    car = getattr(g, 'car', None)
    if car and car.get('D') is D:
        cs = big('carb' if car['burnt'] else 'car', (lambda: spr_car(True)) if car['burnt'] else spr_car, CAR_SC); canvas.blit(cs, (int(car['x'] - 64), GY - cs.get_height() + 2))
    co = getattr(D, 'coco', None) if D else None
    if co and co.get('y') is not None and not co.get('bonk'): part_coco(canvas, None, 432, int(co['y']), 1)
    h = getattr(g, 'heli', None)
    if h and h['D'] is D:
        hs = big('heli', spr_heli, HSC); hx, hy = int(h['x'] - 70), int(h['y'])
        if h['coffin']:
            cx, cy = int(h['cx']), int(h['cy'])
            if h.get('cable'): line(canvas, hx + 48, hy + 66, cx - 30, cy - 18, '#141414'); line(canvas, hx + 96, hy + 66, cx + 30, cy - 18, '#141414')
            canvas.blit(spr_flagcoffin(), (cx - 46, cy - 20))
        canvas.blit(hs, (hx, hy)); rl = 80 if int(g.time * 20) % 2 else 28; canvas.fill(C('#1a1a14'), (hx + 67 - rl, hy + 11, rl * 2, 3))
        tr = 10 if int(g.time * 24) % 2 else 3; canvas.fill(C('#1a1a14'), (hx + 158 - tr // 2, hy + 6, tr, 2)); canvas.fill(C('#1a1a14'), (hx + 158, hy + 6 - tr // 2, 2, tr))
def intro_update(dt, now):
    D, P, E = g.D, g.P, g.E; boss = D.op.get('boss'); fx = {'fire': (horse_update, 5.4), 'arthur': (plane_update, 7.0), 'loucas': (car_update, 4.4)}.get(boss)
    k = ease(min(1, g.T / 2.6)); walking = g.T < 2.6; P.x = lerp(-30, 118, k)
    if fx: fx[0](dt)
    elif boss != 'krieger': E.x = lerp(W + 30, 362, k)
    f = int(g.T * 8) % 4
    if walking:
        P.pose = 'walk%d' % f
        if not boss: E.pose = 'walk%d' % ((f + 1) % 4)
        if f in (0, 2) and D.walkf != f: audio.play('step', .7)
        D.walkf = f
    else:
        P.pose = 'idle'
        if not boss: E.pose = 'idle'
    if g.S != 'intro': return
    end = fx[1] if fx else 3.0
    if boss == 'loucas' and not D.loucasFight: end = 99
    if g.T > end:
        g.horse = None
        if boss == 'krieger': st('rise'); D.coffin = dict(y=GY + 26, lid=True); audio.play('rumble')
        elif D.op.get('voice'): start_dialog()
        elif not boss and D.op.get('vg') and RND() < VOICE_CHANCE: start_dialog(pick(VG[D.op['vg']]))
        else: begin_standoff()

# ---------------------------------------------------------------- MENU DEBUG
_sd5 = start_duel
def start_duel():
    _sd5(); D, E, P = g.D, g.E, g.P
    if D.op.get('boss') == 'loucas': E.scale = .85
    dbg = getattr(g, 'dbg', None); g.dbg = None
    if not dbg: return
    D.dbg = True
    if 'loucasFight' in dbg: D.loucasFight = dbg['loucasFight']
    if dbg.get('skip'):
        P.x = 118; P.pose = 'idle'; E.x = 362; E.hidden = False; E.rot = 0; E.pose = 'idle'; D.coffin = None; g.horse = None; g.plane = None; g.car = None
        now = pygame.time.get_ticks(); st('go'); D.goTime = now; D.enemyAt = now + 9e8; D.noJam = True; D.walkf = 0
        audio.music(D.op.get('music', 'western'), .4) if D.op.get('boss') else audio.music(None)
        if dbg.get('action'): D.ev.append(dict(at=.5, fn=dbg['action']))
def dbg_run(level, **flags): g.dbg = flags; RUN['level'] = level; RUN['hearts'] = max_hearts(); goto('intro')
def _dbg67():
    g.D.goTime = pygame.time.get_ticks() - 267; g.D.hp = 1; player_fire(None)
def _dbg_kill(): g.D.hp = 1; player_fire((g.E.x, SPR_TOP + 55))
def _dbg_explode():
    g.forceExplode = True; x, y = to_world(g.E, AX + 1, 27); player_fire((x, y)); g.forceExplode = False
def _dbg_angel():
    SAVE['active'] = dict(type='anjo', rounds=3); g.D.enemyAt = pygame.time.get_ticks() + 150
def _dbg_give(k, v, msg):
    def f():
        SAVE[k] = SAVE.get(k, 0) + v; save(); audio.play('buy'); toast(msg)
    return f
def _dbg_unlock():
    for w in WEAP:
        if w['id'] not in SAVE['ownW']: SAVE['ownW'].append(w['id'])
    for k in SKINS:
        if k['id'] not in SAVE['ownS']: SAVE['ownS'].append(k['id'])
    SAVE['maxLevel'] = max(SAVE['maxLevel'], 40); save(); audio.play('levelup'); toast('TUDO LIBERADO!')
DEBUG_ITEMS = [
    ('67 - FARMANDO AURA', lambda: dbg_run(1, skip=True, action=_dbg67)),
    ('COCO NO KRIEGER', lambda: dbg_run(20, skip=True, action=krieger_break)),
    ('HELICÓPTERO DO EXÉRCITO', lambda: dbg_run(20, skip=True, action=_dbg_kill)),
    ('KRIEGER SAINDO DO CAIXÃO', lambda: dbg_run(20)),
    ('EL DERECHA NO CAVALO', lambda: dbg_run(10)),
    ('ARTHUR CHEGANDO DE AVIÃO', lambda: dbg_run(30)),
    ('ARTHUR: CONTAGEM ATÉ 5', lambda: dbg_run(30, skip=True, action=lambda: (st('standoff'), setattr(g.D, 'noJam', True)))),
    ('AMANDA BATENDO O CARRO', lambda: dbg_run(40, loucasFight=False)),
    ('AMANDA LUTANDO (5%)', lambda: dbg_run(40, loucasFight=True)),
    ('ARMA FALHANDO (A/D)', lambda: dbg_run(3, skip=True, action=start_jam)),
    ('CABEÇA EXPLODINDO', lambda: dbg_run(2, skip=True, action=_dbg_explode)),
    ('ANJO DA GUARDA', lambda: dbg_run(3, skip=True, action=_dbg_angel)),
    ('EL DERECHA VIRANDO CINZAS', lambda: dbg_run(10, skip=True, action=_dbg_kill)),
    ('+$5000', _dbg_give('money', 5000, '+$5000')), ('+10 PONTOS DE HABILIDADE', _dbg_give('sp', 10, '+10 PONTOS')), ('+3 BÊNÇÃOS', _dbg_give('bless', 3, '+3 BÊNÇÃOS')),
    ('LIBERAR TODAS AS ARMAS E ROUPAS', _dbg_unlock), ('VOLTAR', lambda: goto('settings'))]
def draw_debug():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'MENU DEBUG', 240, 6, sc=3, col='#7ae0ff', sh='#1a3a5a', ext=2, ot=2, out=DARK, align='center')
    if not g.menu or len(g.menu.items) != len(DEBUG_ITEMS): g.menu = Menu(DEBUG_ITEMS, 240, 38, 1, 12)
    draw_menu(g.menu)
    dtext(canvas, '$ %d · PONTOS %d · BÊNÇÃOS %d' % (SAVE['money'], SAVE['sp'], SAVE['bless']), 240, 258, col=GOLD, align='center'); draw_toast(248)


# ==================================================================== EXPANSÃO 3: comemoração, configurações com debug
WIN_SEQ = [('twirl0', .07), ('twirl1', .07), ('twirl2', .07), ('twirl3', .07)] * 4 + [('blow', 1.4), ('tip', 1.2), ('up', 1.0)]
WIN_LEN = sum(d for _, d in WIN_SEQ)
def draw_win_ze(bob):
    t = (g.time - getattr(g, 'winT0', 0)) % WIN_LEN; acc = 0; pose = 'up'; pt = 0
    for q, d in WIN_SEQ:
        if t < acc + d: pose = q; pt = t - acc; break
        acc += d
    spr = ze(pose); x0, y0 = 4, H - SPH * 2 + 2 + bob
    hop = int(abs(math.sin(pt / 1.0 * math.pi)) * 6) if pose == 'tip' else 0
    canvas.blit(pygame.transform.scale(spr.s, (SPW * 2, SPH * 2)), (x0, y0 - hop))
    ws = getattr(g, 'wsmoke', [])
    if pose == 'blow' and spr.muz and RND() < .5:
        mx, my = spr.muz[0]; ws.append(dict(x=x0 + mx * 2, y=y0 + my * 2, t=0., vx=(RND() - .5) * 10))
    if pose.startswith('twirl'):
        k = int(pose[5]); cx, cy = x0 + (AX + 18) * 2, y0 + 53 * 2
        for i in range(6):
            a = math.radians(-k * 90 - i * 18); arect(canvas, '#fff4c0', cx + math.cos(a) * 22, cy - math.sin(a) * 22, 2, 2, 200 - i * 30)
    nws = []
    for s in ws:
        s['t'] += 1 / 60; s['y'] -= 22 / 60; s['x'] += s['vx'] / 60
        if s['t'] < 1.4: arect(canvas, '#d8d0c4', s['x'], s['y'], 2 + int(s['t'] * 4), 2 + int(s['t'] * 4), 150 * (1 - s['t'] / 1.4)); nws.append(s)
    g.wsmoke = nws[-80:]
    if pose == 'tip' and pt < .1 and not getattr(g, 'tipSnd', False): g.tipSnd = True; audio.play('hat', .6)
    if pose != 'tip': g.tipSnd = False
_oe6 = on_enter
def on_enter(s):
    _oe6(s)
    if s == 'win': g.winT0 = g.time; g.wsmoke = []
SET_EXTRA = ['LEGENDAS', 'MENU DEBUG', 'MENU PRINCIPAL', 'VOLTAR']
def settings_input(code):
    n = len(VOLS) + len(SET_EXTRA); i = getattr(g, 'setSel', 0)
    if code == 'up': g.setSel = (i - 1) % n; audio.play('blip', .5)
    elif code == 'down': g.setSel = (i + 1) % n; audio.play('blip', .5)
    elif code == 'back': back()
    elif i < len(VOLS) and code in ('left', 'right'):
        k = VOLS[i][0]; set_vol(k, (SAVE.get('vol') or VDEF).get(k, VDEF[k]) + (.1 if code == 'right' else -.1))
    elif i >= len(VOLS) and code in ('ok', 'left', 'right'):
        e = SET_EXTRA[i - len(VOLS)]
        if e == 'LEGENDAS': SAVE['subs'] = not SAVE.get('subs', True); save(); audio.play('blip', .5)
        elif code != 'ok': return
        elif e == 'MENU DEBUG': goto('debug')
        elif e == 'MENU PRINCIPAL': goto('title')
        else: back()
def draw_settings():
    canvas.blit(screens()['wood'], (0, 0)); dtext(canvas, 'CONFIGURAÇÕES', 240, 6, sc=3, col=CREAM, sh=BROWN, ext=2, ot=2, out=DARK, align='center')
    sel = getattr(g, 'setSel', 0); vol = SAVE.get('vol') or VDEF
    for i, (k, name) in enumerate(VOLS):
        y = 42 + i * 24; hl = i == sel
        dtext(canvas, name, 60, y + 2, col=GOLD if hl else CREAM)
        v = vol.get(k, VDEF[k]); bx = 200
        for j in range(10):
            canvas.fill(C(DARK), (bx + j * 18 - 1, y - 1, 16, 12)); canvas.fill(C(('#ffd060' if hl else '#e0a040') if j < round(v * 10) else '#3a2418'), (bx + j * 18, y, 14, 10))
            g.buttons.append((bx + j * 18 - 1, y - 3, 18, 16, lambda k=k, j=j, i=i: (setattr(g, 'setSel', i), set_vol(k, (j + 1) / 10))))
        dtext(canvas, '%d%%' % round(v * 100), 400, y + 2, col=GOLD if hl else CREAM)
        dtext(canvas, '<', 184, y + 2, col='#ff5a24' if hl else '#7a5040'); dtext(canvas, '>', 386, y + 2, col='#ff5a24' if hl else '#7a5040')
        g.buttons.append((176, y - 3, 14, 16, lambda k=k, i=i: (setattr(g, 'setSel', i), set_vol(k, (SAVE.get('vol') or VDEF).get(k, VDEF[k]) - .1))))
        g.buttons.append((380, y - 3, 14, 16, lambda k=k, i=i: (setattr(g, 'setSel', i), set_vol(k, (SAVE.get('vol') or VDEF).get(k, VDEF[k]) + .1))))
    y = 42 + len(VOLS) * 24; i0 = len(VOLS)
    dtext(canvas, 'LEGENDAS DAS FALAS', 60, y + 2, col=GOLD if sel == i0 else CREAM)
    button('LIGADAS' if SAVE.get('subs', True) else 'DESLIGADAS', 200, y - 3, lambda: (setattr(g, 'setSel', i0), settings_input('ok')), bg='#2a4a1a' if SAVE.get('subs', True) else '#6a2a10')
    for j, (lab, fn, x) in enumerate((('MENU DEBUG', lambda: goto('debug'), 60), ('MENU PRINCIPAL', lambda: goto('title'), 180), ('VOLTAR', back, 330))):
        hl = sel == i0 + 1 + j
        button(lab, x, 200, fn, bg='#8a3a18' if hl else '#4a2414', col=GOLD if hl else CREAM)
    dtext(canvas, 'SETAS: ESCOLHER E AJUSTAR · ENTER: CONFIRMAR · ESC: VOLTAR', 240, 256, col='#8a7058', align='center')

if __name__ == '__main__':
    main()
