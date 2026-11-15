"""Flachbandkabel-Simulationen: 2D-Elektrostatik (Linienladungen + Spiegelung),
Imbalance-Faktor h, Schleifeninduktivitaet, Uebersprechen, Gleichtakt-Leitungsmodell.
Alle Abbildungen als PDF (fuer LaTeX) und PNG.
"""
import numpy as np, json, os
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch

OUT = os.path.join(os.path.dirname(__file__), "..", "abbildungen")
os.makedirs(OUT, exist_ok=True)
mpl.rcParams.update({
    "font.family": "Inter", "font.size": 11, "axes.titlesize": 12.5, "axes.titleweight": "semibold",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e1dc",
    "grid.linewidth": 0.8, "axes.edgecolor": "#7d8188", "axes.labelcolor": "#2a2c30",
    "xtick.color": "#4a4e55", "ytick.color": "#4a4e55", "legend.frameon": False,
    "savefig.bbox": "tight", "pdf.fonttype": 42,
})
BAD, GOOD, MID, MID2, GREY, INK = "#d64545", "#2f9e5a", "#e0902f", "#3a6fb0", "#9aa0a6", "#2a2c30"
def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf")); fig.savefig(os.path.join(OUT, name + ".png"), dpi=200); plt.close(fig)

EPS0, MU0, C0 = 8.854e-12, 4e-7*np.pi, 2.998e8
PITCH, A = 1.27e-3, 0.19e-3            # Rastermass, Leiterradius (AWG 28)
NPIN = 20
H_PCB = 0.02                           # Imbalance-Faktor Leiterbahn ueber Massefl.

# ---------------------------------------------------------------- Pinbelegungen
# Takt = 'T', Masse = 'G', Analog-Opfer = 'A', uebrige Signale = 'S'
def layout(gnd, clk, vic):
    s = ["S"]*NPIN
    for g in gnd: s[g-1] = "G"
    s[clk-1] = "T"; s[vic-1] = "A"
    return s
VARIANTS = {
    "V1": dict(name="1 × GND am Rand, Takt am Gegenrand", short="1 GND, Takt fern", col=BAD,
               pins=layout([1], 20, 19)),
    "V2": dict(name="1 × GND am Rand, Takt daneben", short="1 GND, Takt daneben", col=MID,
               pins=layout([1], 2, 3)),
    "V3": dict(name="3 × GND (Ränder + Mitte)", short="3 GND", col=MID2,
               pins=layout([1, 10, 20], 5, 6)),
    "V4": dict(name="S-G-S-G (jede 2. Ader GND)", short="S-G-S-G", col=GOOD,
               pins=layout(list(range(2, 21, 2)) + [1], 11, 13)),
}
# V4: Ader 1 zusaetzlich GND -> Raender beide GND

def xs():
    return (np.arange(NPIN) - (NPIN-1)/2) * PITCH

def potential_matrix(x, y):
    """P_ij fuer duenne Draehte ueber leitender Ebene y=0 (Spiegelladungen)."""
    n = len(x); P = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            d = A if i == j else np.hypot(x[i]-x[j], y[i]-y[j])
            D = np.hypot(x[i]-x[j], y[i]+y[j])
            P[i, j] = np.log(D/d) / (2*np.pi*EPS0)
    return P

def reduce_group(M, idx_s, idx_g):
    """2x2-Reduktion: Leiter S und Gruppe G (gleiches Potential)."""
    a = M[idx_s, idx_s]; b = M[idx_s, idx_g].sum(); c = M[np.ix_(idx_g, [idx_s])].sum(); d = M[np.ix_(idx_g, idx_g)].sum()
    return np.array([[a, b], [c, d]])

def analyze(pins, H):
    """H = Hoehe der Leitermitte ueber dem Blech."""
    act = [i for i, p in enumerate(pins) if p in "TG"]
    x = xs()[act]; y = np.full(len(act), H)
    P = potential_matrix(x, y)
    C = np.linalg.inv(P)
    s = [k for k, i in enumerate(act) if pins[i] == "T"][0]
    g = [k for k, i in enumerate(act) if pins[i] == "G"]
    K = reduce_group(C, s, g)                       # Maxwell 2x2
    cS0, cR0 = K[0].sum(), K[1].sum()               # Kapazitaet zum Blech
    h = cS0 / (cS0 + cR0)
    L2 = MU0*EPS0*np.linalg.inv(K)                   # homogen (Luft)
    Lloop = L2[0, 0] + L2[1, 1] - 2*L2[0, 1]
    return dict(h=h, Lloop=Lloop, cS0=cS0, cR0=cR0)

def crosstalk(pins, H):
    """Rueckwaerts-Uebersprechkoeffizient Takt -> Analog, Referenz = GND-Adern + Blech."""
    act = [i for i, p in enumerate(pins) if p in "TGA"]
    x = xs()[act]; y = np.full(len(act), H)
    C = np.linalg.inv(potential_matrix(x, y))
    t = [k for k, i in enumerate(act) if pins[i] == "T"][0]
    v = [k for k, i in enumerate(act) if pins[i] == "A"][0]
    # GND-Adern liegen auf 0 V -> 2x2 Teilmatrix (Kurzschluss der Referenzleiter)
    Cs = C[np.ix_([t, v], [t, v])]
    Ls = MU0*EPS0*np.linalg.inv(Cs)
    Cm, Cv = -Cs[0, 1], Cs[1, 1]
    Lm, Lv = Ls[0, 1], Ls[1, 1]
    return 0.25*(Lm/Lv + Cm/Cv)

def sep(pins):
    """Abstand Takt zur naechsten GND-Ader (fuer Gegentakt-Schleifenflaeche)."""
    t = pins.index("T"); g = [i for i, p in enumerate(pins) if p == "G"]
    return min(abs(t-i) for i in g)*PITCH

RES = {}
heights = np.geomspace(0.6e-3, 60e-3, 80)
for k, v in VARIANTS.items():
    hs = np.array([analyze(v["pins"], H)["h"] for H in heights])
    a3, a40 = analyze(v["pins"], 3e-3), analyze(v["pins"], 40e-3)
    RES[k] = dict(h_curve=hs, h3=a3["h"], h40=a40["h"], L40=a40["Lloop"], L3=a3["Lloop"],
                  xt3=crosstalk(v["pins"], 3e-3), xt40=crosstalk(v["pins"], 40e-3), sep=sep(v["pins"]))

# ---------------------------------------------------------------- Abb. 1: Pinbelegungen
fig, axs = plt.subplots(4, 1, figsize=(9, 4.6))
for ax, (k, v) in zip(axs, VARIANTS.items()):
    ax.set_xlim(-0.5, NPIN+3.5); ax.set_ylim(-0.9, 0.9); ax.axis("off"); ax.set_aspect("equal")
    ax.add_patch(FancyBboxPatch((0.45, -0.62), NPIN+0.1, 1.24, boxstyle="round,pad=0,rounding_size=0.5",
                                fc="#eceae5", ec="#b9b6ae", lw=0.8))
    for i, p in enumerate(v["pins"]):
        c = {"G": "#2b2b2b", "T": BAD, "A": MID2, "S": "#c9ccd1"}[p]
        ax.add_patch(Circle((i+1, 0), 0.36, fc=c, ec="white", lw=0.8))
        if p in "TA": ax.text(i+1, 0, p, ha="center", va="center", color="white", fontsize=8, weight="bold")
        if p == "G": ax.text(i+1, 0, "G", ha="center", va="center", color="white", fontsize=7.5)
    ax.text(NPIN+1.2, 0, f"{k}  {v['name']}", va="center", fontsize=10.5, color=INK)
axs[0].text(1, 0.78, "Ader 1", fontsize=8.5, color="#6b6f76", ha="center")
fig.text(0.02, 0.01, "T = Takt (Aggressor) · A = Analogsignal (Opfer) · G = Masse · grau = übrige Signale", fontsize=9, color="#6b6f76")
fig.subplots_adjust(left=0.01, right=0.99, hspace=0.05)
save(fig, "01_pinbelegungen")

# ---------------------------------------------------------------- Abb. 2: Feldbilder
def field_map(ax, pins, H, title, xlim=14e-3, ytop=12e-3):
    act = [i for i, p in enumerate(pins) if p in "TG"]
    x = xs()[act]; y = np.full(len(act), H)
    V = np.array([1.0 if pins[i] == "T" else 0.0 for i in act])
    q = np.linalg.solve(potential_matrix(x, y), V)
    X, Y = np.meshgrid(np.linspace(-xlim, xlim, 500), np.linspace(1e-5, ytop, 260))
    phi = np.zeros_like(X)
    for xi, yi, qi in zip(x, y, q):
        d = np.maximum(np.hypot(X-xi, Y-yi), A); D = np.hypot(X-xi, Y+yi)
        phi += qi*np.log(D/d)/(2*np.pi*EPS0)
    Ey, Ex = np.gradient(-phi, Y[:, 0], X[0])
    im = ax.pcolormesh(X*1e3, Y*1e3, np.clip(phi, 0, 1), cmap="magma_r", vmin=0, vmax=0.35, shading="auto", rasterized=True)
    ax.streamplot(X*1e3, Y*1e3, Ex, Ey, color="#ffffff", linewidth=0.6, density=1.3, arrowsize=0.6)
    ax.axhline(0, color="#555", lw=4)
    for i, p in enumerate(pins):
        c = {"G": "#2b2b2b", "T": BAD, "A": "#c9ccd1", "S": "#c9ccd1"}[p]
        ax.add_patch(Circle((xs()[i]*1e3, H*1e3), A*1e3*1.6, fc=c, ec="white", lw=0.4, zorder=5))
    ax.set_xlim(-xlim*1e3, xlim*1e3); ax.set_ylim(-0.6, ytop*1e3); ax.set_aspect("equal")
    ax.set_title(title, loc="left"); ax.grid(False); ax.set_xlabel("x / mm"); ax.set_ylabel("Höhe über Blech / mm")
    return im
fig, axs = plt.subplots(1, 2, figsize=(11, 4.0))
field_map(axs[0], VARIANTS["V1"]["pins"], 6e-3, "V1: Takt fern vom einzigen GND")
im = field_map(axs[1], VARIANTS["V4"]["pins"], 6e-3, "V4: S-G-S-G")
cb = fig.colorbar(im, ax=axs, shrink=0.8, pad=0.02); cb.set_label("Potential / V (Takt = 1 V)")
fig.text(0.01, -0.02, "Gegentaktanregung, Kabel 6 mm über dem Blech. Weiße Linien: elektrisches Feld. Feld, das auf dem Blech endet, ist der Gleichtaktanteil.", fontsize=9, color="#6b6f76")
save(fig, "02_feldbilder")

# ---------------------------------------------------------------- Abb. 3: h ueber Hoehe
fig, ax = plt.subplots(figsize=(8, 4.5))
for k, v in VARIANTS.items():
    ax.semilogx(heights*1e3, RES[k]["h_curve"], color=v["col"], lw=2.2, label=f"{k}: {v['short']}")
ax.axhline(H_PCB, color=GREY, ls="--", lw=1.4); ax.text(0.65, H_PCB+0.012, "Leiterbahn auf Platine (h ≈ 0,02)", color="#6b6f76", fontsize=9.5)
ax.axvspan(0.6, 5, color=GOOD, alpha=0.07); ax.axvspan(20, 60, color=BAD, alpha=0.06)
ax.text(1.7, 0.45, "flach auf Blech", color=GOOD, ha="center", fontsize=10); ax.text(35, 0.45, "frei im Raum", color=BAD, ha="center", fontsize=10)
ax.set_xlabel("Höhe des Flachbands über dem Gehäuseblech / mm"); ax.set_ylabel("Imbalance-Faktor h")
ax.set_ylim(0, 0.56); ax.set_xlim(0.6, 60)
ax.text(8, 0.515, "V1 und V2 liegen übereinander: h = 0,5 (Signal + ein GND = symmetrisches Paar)", fontsize=9, color=BAD, ha="center")
ax.set_xticks([1, 2, 3, 5, 10, 20, 40]); ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())
ax.set_title("Die Pinbelegung bestimmt h, die Höhe über dem Blech kaum", loc="left")
ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.6), fontsize=9.5)
save(fig, "03_h_ueber_hoehe")

# ---------------------------------------------------------------- Abb. 4: Uebersprechen + Schleifeninduktivitaet
VDD = 3.3
fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
keys = list(VARIANTS); lab = [f"{k}\n" + VARIANTS[k]['short'].replace(", ", "\n") for k in keys]; cols = [VARIANTS[k]["col"] for k in keys]
xt = np.array([RES[k]["xt40"]*VDD*1e3 for k in keys]); xt3 = np.array([RES[k]["xt3"]*VDD*1e3 for k in keys])
w = 0.38; xx = np.arange(len(keys))
axs[0].bar(xx-w/2, xt, w, color=cols, alpha=0.45, label="frei im Raum (40 mm)")
axs[0].bar(xx+w/2, xt3, w, color=cols, label="auf Blech (3 mm)")
for i in range(len(keys)):
    axs[0].text(xx[i]-w/2, xt[i]+5, f"{xt[i]:.0f}", ha="center", fontsize=9); axs[0].text(xx[i]+w/2, xt3[i]+5, f"{xt3[i]:.0f}", ha="center", fontsize=9)
axs[0].set_xticks(xx, lab, fontsize=9); axs[0].set_ylabel("Übersprechen auf Nachbarader / mV")
axs[0].set_title("Übersprechen Takt → Analogsignal", loc="left"); axs[0].grid(axis="x", visible=False); axs[1].grid(axis="x", visible=False); axs[0].legend(fontsize=9)
L = np.array([RES[k]["L40"]*1e9*0.25 for k in keys])
axs[1].bar(xx, L, 0.6, color=cols)
for i in range(len(keys)): axs[1].text(xx[i], L[i]+3, f"{L[i]:.0f} nH", ha="center", fontsize=9)
axs[1].set_xticks(xx, lab, fontsize=9); axs[1].set_ylabel("Schleifeninduktivität (25 cm) / nH")
axs[1].set_title("Schleifeninduktivität Takt ↔ Rückleiter", loc="left"); fig.subplots_adjust(wspace=0.28)
save(fig, "04_uebersprechen_induktivitaet")

# ---------------------------------------------------------------- Simulation 4: Gleichtakt-Leitungsmodell
LEN = 0.25
D_BOX = 100e-3          # lichte Hoehe Boden -> Deckel; Deckel als zweite leitende Ebene
_Z0C = {}
def z0_cm(H, w=NPIN*PITCH, n=41, K=30):
    """Gleichtakt-Wellenwiderstand des Flachbands zwischen Boden (y=0) und Deckel (y=D_BOX),
    Spiegelladungen beider Ebenen (Reihe bis |k| = K)."""
    key = round(H*1e6)
    if key in _Z0C: return _Z0C[key]
    xw = np.linspace(-w/2, w/2, n); P = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dx = xw[i]-xw[j]; acc = 0.0
            for k in range(-K, K+1):
                yp = 2*k*D_BOX + H; ym = 2*k*D_BOX - H
                dp = A if (k == 0 and i == j) else np.hypot(dx, H-yp)
                acc += np.log(np.hypot(dx, H-ym)/dp) if k != 0 or i != j else np.log(np.hypot(dx, H-ym)/A)
            P[i, j] = acc/(2*np.pi*EPS0)
    C = np.linalg.inv(P).sum()
    _Z0C[key] = 1/(C0*C)
    return _Z0C[key]
Z_EXT = 150.0           # Gleichtaktimpedanz externes Kabel (CDN-typisch)
C_BOARD = 30e-12        # Platine ~100 cm^2 in 3 mm Abstand zum Blech
L_BOLT = 4e-9           # zwei Bolzen a 8 nH parallel, direkt am Stecker
Q_LINE = 10             # Verluste/Abstrahlung: Guete der Kabelresonanzen
def par(*z):
    return 1/sum(1/zi for zi in z)
def board_potential(f, H, bonded, dh, vdm=1.0):
    w = 2*np.pi*f; b = w/C0*(1 - 1j/(2*Q_LINE)); Z0 = z0_cm(H)
    zc = 1/(1j*w*C_BOARD)
    zb = (1j*w*L_BOLT + 5e-3) if bonded else np.inf
    ZA = par(zc, Z_EXT, zb) if bonded else par(zc, Z_EXT)
    ZB = par(zc, zb) if bonded else zc
    y11 = -1j/(Z0*np.tan(b*LEN)); y12 = 1j/(Z0*np.sin(b*LEN))
    vs = dh*vdm
    # Unbekannte UA, UB:  UA + ZA*(y11*(UA+vs) + y12*(UB+vs)) = 0 ; UB + ZB*(y12*(UA+vs)+y11*(UB+vs)) = 0
    M = np.array([[1 + ZA*y11, ZA*y12], [ZB*y12, 1 + ZB*y11]])
    r = -np.array([ZA*(y11+y12)*vs, ZB*(y11+y12)*vs])
    UA, UB = np.linalg.solve(M, r)
    I1 = y11*(UA+vs) + y12*(UB+vs)
    V1 = UA + vs
    z = np.linspace(0, LEN, 21)
    Iz = I1*np.cos(b*z) - 1j*V1/Z0*np.sin(b*z)
    Vz = V1*np.cos(b*z) - 1j*Z0*I1*np.sin(b*z)
    board_potential.line = (np.mean(np.abs(Iz)), np.mean(np.abs(Vz)))
    return UA, I1

# ---- Pfad 2: direkte Feldkopplung Flachband -> interne Verdrahtung des externen Kabels
# Kabelbaum (Leiterradius 0,5 mm) laeuft 30 mm neben dem Flachband, 10 mm ueber dem Blech,
# auf L_PAR = 10 cm parallel zur Rueckwand-Buchse. Gleiche Lage in allen Faellen.
L_PAR, HV, DXV, AV = 0.10, 10e-3, 30e-3, 0.5e-3
def harness_coupling(H, n=31):
    w = NPIN*PITCH
    xw = np.r_[np.linspace(-w/2, w/2, n), w/2 + DXV]; yw = np.r_[np.full(n, H), HV]
    nn_ = len(xw); P = np.zeros((nn_, nn_))
    for i in range(nn_):
        for j in range(nn_):
            ai = AV if i == nn_-1 else A
            d = ai if i == j else np.hypot(xw[i]-xw[j], yw[i]-yw[j]); D = np.hypot(xw[i]-xw[j], yw[i]+yw[j])
            P[i, j] = np.log(D/d)/(2*np.pi*EPS0)
    C = np.linalg.inv(P)
    K = np.array([[C[:n, :n].sum(), C[:n, n].sum()], [C[n, :n].sum(), C[n, n]]])
    L = MU0*EPS0*np.linalg.inv(K)
    return -K[0, 1], L[0, 1]            # Cm, M je Meter
HC = {H: harness_coupling(H) for H in (3e-3, 40e-3)}
# ---- Pfad 3: Anregung des ganzen Geraets gegen die Umgebung (Imbalance-Faktor mit Bezug "unendlich")
# Mit Anbindung gehoert das Blech zur Rueckleitergruppe; ohne Anbindung nicht.
# K_LEAK: Anteil, der durch Display-Fenster, Kunststofffront, Schlitze und Buchsen ohne
# 360-Grad-Schirmanbindung nach aussen wirkt (Annahme, 0,1 = -20 dB).
K_LEAK = 0.1
R_INF, W_PLATE, NPL = 1.0, 0.20, 200
_HINF = {}
def h_inf(var, H, plate):
    key = (var, round(H*1e6), plate)
    if key in _HINF: return _HINF[key]
    pins = VARIANTS[var]["pins"]; x = xs()
    act = [i for i, p in enumerate(pins) if p in "TG"]
    X = list(x[act]); Y = [H]*len(act); R = [A]*len(act); G = ["S" if pins[i] == "T" else "R" for i in act]
    if plate:
        xp = np.linspace(-W_PLATE/2, W_PLATE/2, NPL); dx = xp[1]-xp[0]
        X += list(xp); Y += [0.0]*NPL; R += [dx/4]*NPL; G += ["R"]*NPL
    X, Y = np.array(X), np.array(Y)
    d = np.hypot(X[:, None]-X[None, :], Y[:, None]-Y[None, :]); np.fill_diagonal(d, R)
    C = np.linalg.inv(np.log(R_INF/d)/(2*np.pi*EPS0))
    s_ = [i for i, g in enumerate(G) if g == "S"]; r_ = [i for i, g in enumerate(G) if g == "R"]
    cS = C[np.ix_(s_, s_+r_)].sum(); cR = C[np.ix_(r_, s_+r_)].sum()
    _HINF[key] = cS/(cS+cR); return _HINF[key]
H_PCB_INF = 0.002          # Leiterbahn 0,2 mm ueber 100 mm breiter Masseflaeche, Bezug unendlich
def dh_inf(var, H, bonded):
    return abs(h_inf(var, H, bonded) - H_PCB_INF)
def ext_currents(f, H, bonded, dh, vdm, var="V1"):
    UA, _ = board_potential(f, H, bonded, dh, vdm)
    Iavg, Vavg = board_potential.line
    Cm, Mm = HC[H] if H in HC else harness_coupling(H)
    w = 2*np.pi*f
    i1 = abs(UA)/Z_EXT                                   # Pfad 1: Platinenpotential
    i2 = w*Mm*L_PAR*Iavg/(2*Z_EXT) + w*Cm*L_PAR*Vavg/2   # Pfad 2: Feldkopplung
    i3 = K_LEAK*dh_inf(var, H, bonded)*vdm/Z_EXT         # Pfad 3: Geraet gegen Umgebung
    return i1, i2, i3
CASES = [
    ("Frei im Raum, ohne Anbindung", 40e-3, False, BAD, "-"),
    ("Frei im Raum, mit Anbindung", 40e-3, True, MID, "--"),
    ("Auf Blech, ohne Anbindung", 3e-3, False, MID2, "--"),
    ("Auf Blech, mit Anbindung", 3e-3, True, GOOD, "-"),
]
def dh_for(var, H):
    return analyze(VARIANTS[var]["pins"], H)["h"] - H_PCB

# Abb. 5: Uebertragungsfunktion |U_A / V_DM| (Pinbelegung V1)
fr = np.geomspace(10e6, 1e9, 600)
fig, ax = plt.subplots(figsize=(8, 4.5))
TF = {}
for name, H, bd, col, ls in CASES:
    u = np.array([abs(board_potential(f, H, bd, dh_for("V1", H))[0]) for f in fr])
    TF[name] = u
    ax.loglog(fr/1e6, u, color=col, lw=2.2, ls=ls, label=name)
ax.set_xlabel("Frequenz / MHz"); ax.set_ylabel("|U Platine–Chassis| / |V_DM|")
ax.set_title("Platinenmasse gegenüber Chassis: Anbindung entscheidet bis ca. 200 MHz", loc="left")
ax.set_xticks([10, 30, 100, 300, 1000]); ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())
ax.legend(fontsize=9.5, loc="lower right"); ax.set_ylim(1e-4, 1)
fig.text(0.01, -0.05, f"Pinbelegung V1, Kabel 25 cm, externes Kabel {Z_EXT:.0f} Ω an Platine A, Platinen je {C_BOARD*1e12:.0f} pF zum Blech, Anbindung = {L_BOLT*1e9:.0f} nH.", fontsize=9, color="#6b6f76")
save(fig, "05_uebertragung_platinenpotential")

# Abb. 6: Spektrum -> Feldstaerke 10 m (Takt 50 MHz, 3,3 V, tr 1 ns)
F_CLK, T_R = 50e6, 1e-9
n = np.arange(1, 21, 2); fh = n*F_CLK
def vharm(nn):
    x = np.pi*nn*T_R*F_CLK
    return 2*VDD/(nn*np.pi)*abs(np.sinc(x/np.pi))
def efield(I, f, Lc=1.0, d=10.0):
    return np.minimum(1.257e-6*f*I*Lc/d, 60*I/d)
def limit(f, cls="B"):
    base = 30 if cls == "B" else 40
    return np.where(f <= 230e6, base, base+7)
E = {}
for var in ["V1", "V4"]:
    for name, H, bd, col, ls in CASES:
        e = []
        for nn, f in zip(n, fh):
            e.append(20*np.log10(efield(sum(ext_currents(f, H, bd, dh_for(var, H), vharm(nn), var)), f)/1e-6))
        E[(var, name)] = np.array(e)
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
sel = [0, 1, 2]                          # 50, 150, 250 MHz (unterhalb der Kabelresonanzen)
for ax, var in zip(axs, ["V1", "V4"]):
    xx = np.arange(len(sel)); w = 0.2
    for j, (name, H, bd, col, ls) in enumerate(CASES):
        vals = E[(var, name)][sel]
        ax.bar(xx + (j-1.5)*w, vals + 20, w, bottom=-20, color=col, label=name)
        for xi, vv in zip(xx + (j-1.5)*w, vals): ax.text(xi, max(vv, -18) + 1.5, f"{vv:.0f}", ha="center", fontsize=8)
    for xi, f in zip(xx, fh[sel]):
        lb = 30 if f <= 230e6 else 37
        ax.hlines(lb, xi-0.45, xi+0.45, color=INK, lw=1.6)
    ax.set_xticks(xx, [f"{int(f/1e6)} MHz" for f in fh[sel]]); ax.set_ylim(-20, 95)
    ax.set_title(f"Pinbelegung {var}: {VARIANTS[var]['short']}", loc="left"); ax.grid(axis="x", visible=False)
axs[0].set_ylabel("E-Feld 10 m (externes Kabel) / dBµV/m")
from matplotlib.lines import Line2D
h_, l_ = axs[1].get_legend_handles_labels(); h_.append(Line2D([], [], color=INK, lw=1.6)); l_.append("Grenzwert Klasse B")
axs[1].legend(h_, l_, fontsize=9, loc="upper right")
fig.text(0.01, -0.03, "50-MHz-Takt, 3,3 V, 1 ns Flanke. Externes Kabel 1 m, gespeist über Platinenpotential, Feldkopplung und Geräteanregung (h gegen unendlich, Leckfaktor 0,1); ±10 dB.", fontsize=9, color="#6b6f76")
save(fig, "06_feldstaerke_spektrum")

# ---------------------------------------------------------------- Abb. 7: Seitenansicht der beiden Faelle (Skizze)
fig, axs = plt.subplots(2, 1, figsize=(10, 5.6))
for ax, good in zip(axs, [False, True]):
    ax.set_xlim(0, 100); ax.set_ylim(-8, 34); ax.axis("off")
    ax.add_patch(Rectangle((2, -2), 96, 2, fc="#8f949b"))                       # Bodenblech
    ax.add_patch(Rectangle((2, 30), 96, 1.5, fc="#c9ccd1"))                     # Deckel
    for x0 in (6, 62):
        ax.add_patch(Rectangle((x0, 8), 32, 1.6, fc="#2f6b45"))                  # Platinen
        for bx in (x0+1.5, x0+29):
            ax.add_patch(Rectangle((bx, 0), 1.2, 8, fc="#cfc59a"))               # Eckbolzen
    ax.add_patch(Rectangle((33, 9.6), 4, 2, fc="#222")); ax.add_patch(Rectangle((63, 9.6), 4, 2, fc="#222"))
    if not good:
        t = np.linspace(0, 1, 100); xc = 35 + 30*t; yc = 11.6 + 15*np.sin(np.pi*t)
        ax.plot(xc, yc, color=BAD, lw=4, solid_capstyle="round")
        ax.annotate("", xy=(50, 0.6), xytext=(50, 25), arrowprops=dict(arrowstyle="->", color=BAD, ls="--", lw=1.2))
        ax.text(49, 16, "C Kabel→Blech", color=BAD, fontsize=9.5, ha="right"); ax.text(22, 3.5, "Kunststoff-Abstandshalter", color="#8a8160", fontsize=8.5, ha="center")
        ax.text(3, -6.5, "Platinen nur kapazitiv (~30 pF) zum Chassis · Rückstrom über Platinenmasse und externe Kabel", fontsize=9.5, color=BAD)
        ax.text(2, 32.8, "Schlecht: Flachband frei im Raum, Platinen ohne Chassisanbindung", fontsize=11.5, weight="semibold", color=INK)
        ax.add_patch(Rectangle((0, 3), 2, 6, fc="#3a6fb0")); ax.text(0.2, 10, "ext. Kabel", fontsize=8.5, color="#3a6fb0")
        ax.annotate("", xy=(-1, 6), xytext=(8, 6), arrowprops=dict(arrowstyle="->", color=BAD, lw=1.6))
    else:
        ax.plot([37, 39, 39, 61, 61, 63], [10.6, 10.6, 0.9, 0.9, 10.6, 10.6], color=GOOD, lw=4, solid_capstyle="round")
        for bx in (34.5, 63.5):
            ax.add_patch(Rectangle((bx, 0), 1.6, 8, fc=GOOD))
        ax.text(50, 3.2, "≤ 3 mm über Blech", color=GOOD, ha="center", fontsize=9.5)
        ax.text(3, -6.5, "Bolzen direkt neben jedem Stecker · Rückstrom auf kürzestem Weg über das Blech", fontsize=9.5, color=GOOD)
        ax.text(2, 32.8, "Gut: Flachband flach auf Blech, Platinen am Stecker angebunden", fontsize=11.5, weight="semibold", color=INK)
        ax.add_patch(Rectangle((0, 3), 2, 6, fc="#3a6fb0"))
fig.subplots_adjust(hspace=0.15)
save(fig, "07_seitenansicht")

# ---------------------------------------------------------------- Abb. 8: Magnetische Kopplung auf Nachbarkabel ueber Hoehe
# Gegentaktstrom Takt -> Rueckleiter, Blech als idealer Leiter (Spiegelstroeme).
# Nachbarkabel (Leiter + Blech als Schleife) liegt 30 mm seitlich in gleicher Hoehe.
def mutual(var, H, dx=30e-3):
    pins = VARIANTS[var]["pins"]; x = xs()
    t = pins.index("T"); g = [i for i, p in enumerate(pins) if p == "G"]
    gn = sorted(g, key=lambda i: abs(i-t))
    ret = gn[:2] if len(gn) > 1 and abs(gn[0]-t) == abs(gn[1]-t) else gn[:1]
    src = [(x[t], 1.0)] + [(x[i], -1.0/len(ret)) for i in ret]
    xn = x[-1] + dx
    M = 0.0
    for x0, I in src:
        M += I*MU0/(2*np.pi)*np.log(np.hypot(xn-x0, 2*H)/abs(xn-x0))
    return abs(M)
hh = np.geomspace(1e-3, 60e-3, 60)
fig, ax = plt.subplots(figsize=(8, 4.5))
ref = mutual("V1", 40e-3); MK = {}
for var in ["V1", "V3", "V4"]:
    m = np.array([mutual(var, H) for H in hh])
    ax.semilogx(hh*1e3, 20*np.log10(m/ref), color=VARIANTS[var]["col"], lw=2.3, label=f"{var}: {VARIANTS[var]['short']}")
    MK[var] = dict(m40_dB=round(float(20*np.log10(mutual(var, 40e-3)/ref)), 1), m3_dB=round(float(20*np.log10(mutual(var, 3e-3)/ref)), 1))
ax.axvspan(1, 5, color=GOOD, alpha=0.08); ax.axvspan(20, 60, color=BAD, alpha=0.06)
ax.set_xlabel("Höhe von Flachband und Nachbarkabel über dem Blech / mm"); ax.set_ylabel("Magnetische Kopplung / dB (Bezug V1, 40 mm)")
ax.set_xticks([1, 2, 3, 5, 10, 20, 40]); ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())
ax.set_title("Am Blech und mit GND neben dem Takt koppelt das Kabel kaum noch", loc="left")
ax.legend(fontsize=9.5, loc="lower right")
fig.text(0.01, -0.05, "Nachbarkabel 30 mm neben der letzten Ader, gleiche Höhe; Blech als idealer Leiter (Spiegelströme), 2D-Rechnung.", fontsize=9, color="#6b6f76")
save(fig, "08_magnetische_kopplung")
KC = MK

# ---------------------------------------------------------------- Abb. 9: Einfluss der Anbindungsinduktivitaet
fig, ax = plt.subplots(figsize=(8, 4.5))
L_SAVE = L_BOLT
bad = [20*np.log10(efield(sum(ext_currents(f, 40e-3, False, dh_for("V1", 40e-3), vharm(nn))), f)/1e-6) for nn, f in zip(n, fh)]
ax.plot(fh/1e6, bad, "o-", color=BAD, lw=2.4, label="Frei im Raum, ohne Anbindung")
SENS = {}
for LB, a in zip([4e-9, 2e-9, 1e-9, 0.5e-9], [0.35, 0.55, 0.8, 1.0]):
    L_BOLT = LB
    e = [20*np.log10(efield(sum(ext_currents(f, 3e-3, True, dh_for("V1", 3e-3), vharm(nn))), f)/1e-6) for nn, f in zip(n, fh)]
    SENS[f"{LB*1e9:g}nH"] = [round(float(v), 1) for v in e[:5]]
    ax.plot(fh/1e6, e, "o-", color=GOOD, alpha=a, lw=2, label=f"Auf Blech, Anbindung {LB*1e9:g} nH")
L_BOLT = L_SAVE
ff = np.array([30e6, 230e6, 230e6, 1e9]); ax.plot(ff/1e6, [30, 30, 37, 37], color=INK, lw=1.4, label="Grenzwert Klasse B")
ax.set_xlabel("Frequenz / MHz"); ax.set_ylabel("E-Feld 10 m / dBµV/m"); ax.set_xlim(0, 1000); ax.set_ylim(-10, 95)
ax.set_title("Flach am Blech hilft nur mit sehr niederinduktiver Anbindung", loc="left")
ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)
fig.text(0.01, -0.2, "Pinbelegung V1, sonst wie Abb. 6. 4 nH ≈ zwei Bolzen; ≤ 1 nH ≈ mehrere Bolzen plus flächiger Kontakt (Federleiste, Schirmklemme).", fontsize=9, color="#6b6f76")
save(fig, "09_anbindungsinduktivitaet")

# ---------------------------------------------------------------- Abb. 10: Magnetfeld an einer Deckeloeffnung
# Gleichtaktstrom bei gleichem V_CM: I ~ 1/Z0(H) (kapazitiver Ladestrom); Feld an Deckel in Y = 100 mm
# aus Kabelstrom und Spiegelstrom im Bodenblech.
Y_LID = 100e-3
def lid_field(H):
    I = 1/z0_cm(H)
    return I*(1/(Y_LID-H) - 1/(Y_LID+H))
hh = np.linspace(1e-3, 90e-3, 200)
ref = lid_field(3e-3)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(hh*1e3, 20*np.log10(np.array([lid_field(h) for h in hh])/ref), color=INK, lw=2.4)
LID = {}
for Hm, col, lab in [(3, GOOD, "flach am Blech"), (40, BAD, "Bogen 40 mm"), (80, BAD, "Bogen 2 cm unter Deckel")]:
    v = 20*np.log10(lid_field(Hm*1e-3)/ref); LID[f"{Hm}mm"] = round(float(v), 1)
    ax.plot([Hm], [v], "o", color=col, ms=7)
    txt = f"{lab}: Bezug" if Hm == 3 else f"{lab}: {v:+.0f} dB"
    pos = {3: (6, 2.5), 40: (43, 7), 80: (48, 28)}[Hm]
    ax.annotate(txt, (Hm, v), pos, color=col, fontsize=10)
ax.set_xlabel("Höhe des Flachbands über dem Boden / mm (Deckel bei 100 mm)"); ax.set_ylabel("Magnetfeld an der Deckelöffnung / dB")
ax.set_title("Je höher das Kabel, desto stärker wird die Deckelöffnung gespeist", loc="left")
ax.set_xlim(0, 92)
fig.text(0.01, -0.05, "Gleiche Gleichtaktspannung V_CM; Strom aus dem Gleichtakt-Wellenwiderstand, Feld aus Kabelstrom und Spiegelstrom im Bodenblech. Bezug: flach, 3 mm.", fontsize=9, color="#6b6f76")
save(fig, "10_deckeloeffnung")

# ---------------------------------------------------------------- Abb. 11: h mit Bezug unendlich
hh = np.geomspace(1e-3, 60e-3, 25)
fig, ax = plt.subplots(figsize=(8, 4.5))
HINF = {}
for var in ["V1", "V4"]:
    c = VARIANTS[var]["col"]
    v = np.array([h_inf(var, H, True) for H in hh])
    ax.loglog(hh*1e3, v, color=c, lw=2.4, label=f"{var} {VARIANTS[var]['short']}: mit Anbindung (Blech = Rückleiter)")
    u = h_inf(var, 40e-3, False)
    ax.axhline(u, color=c, lw=1.4, ls="--", label=f"{var}: ohne Anbindung (h = {u:.2f})".replace(".", ","))
    HINF[var] = dict(flat=round(h_inf(var, 3e-3, True), 4), air=round(h_inf(var, 40e-3, True), 4), unbonded=round(u, 3))
ax.axhline(H_PCB_INF, color=GREY, ls=":", lw=1.4); ax.text(8, H_PCB_INF*1.12, "Leiterbahn auf Platine (h ≈ 0,002)", fontsize=9.5, color="#6b6f76")
ax.axvspan(1, 5, color=GOOD, alpha=0.08); ax.axvspan(20, 60, color=BAD, alpha=0.06)
ax.set_xlabel("Höhe des Flachbands über dem Blech / mm"); ax.set_ylabel("Imbalance-Faktor h (Bezug: Umgebung)")
ax.set_xticks([1, 2, 3, 5, 10, 20, 40]); ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())
ax.set_title("Mit Anbindung wird das Blech Rückleiter: h hängt stark von der Höhe ab", loc="left")
ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)
save(fig, "11_h_bezug_unendlich")

# ---------------------------------------------------------------- Abb. 12: Pfadbilanz flach vs. frei (mit Anbindung)
f0 = 150e6; nn0 = 3
pa = ext_currents(f0, 40e-3, True, dh_for("V1", 40e-3), vharm(nn0), "V1")
pf = ext_currents(f0, 3e-3, True, dh_for("V1", 3e-3), vharm(nn0), "V1")
db = lambda a, b: 20*np.log10(b/a)
PATHS = [
    ("Platinenpotential → externes Kabel", db(pa[0], pf[0])),
    ("Feldkopplung auf interne Verdrahtung", db(pa[1], pf[1])),
    ("Gerät gegen Umgebung (h∞-Sprung)", db(pa[2], pf[2])),
    ("Deckelöffnung (Schleifenformel)", -LID["40mm"]),
    ("Nachbarkabel in gleicher Höhe", KC["V1"]["m3_dB"] - KC["V1"]["m40_dB"]),
]
fig, ax = plt.subplots(figsize=(9, 4.4))
labs = [p[0] for p in PATHS]; vals = [p[1] for p in PATHS]
ax.barh(range(len(vals)), vals, color=[GOOD if v < 0 else BAD for v in vals], height=0.6)
for i, v in enumerate(vals): ax.text(v + (-1 if v < 0 else 1), i, f"{v:+.0f} dB", va="center", ha="right" if v < 0 else "left", fontsize=10)
ax.set_yticks(range(len(vals)), labs); ax.invert_yaxis(); ax.axvline(0, color=INK, lw=1)
ax.set_xlim(min(vals)-8, max(8, max(vals)+8)); ax.grid(axis="y", visible=False)
ax.set_xlabel("flach am Blech gegenüber frei im Raum / dB (negativ = flach besser)")
ax.set_title("Flach am Blech gewinnt in fast jedem Pfad", loc="left")
fig.text(0.01, -0.06, "Pinbelegung V1, 150 MHz, beide mit Anbindung (4 nH). Platinenpotential: mit 1 nH etwa 12 dB weniger. Deckelöffnung: Bogen 40 mm (2 cm unter Deckel: −27 dB).", fontsize=9, color="#6b6f76")
save(fig, "12_pfadbilanz")
PB = {p[0]: round(float(p[1]), 1) for p in PATHS}

# ---------------------------------------------------------------- Abb. 13: Einfluss des Leckfaktors (Gehaeuseoeffnungen)
kk = np.geomspace(0.01, 1, 40); f0 = 150e6; nn0 = 3
fig, ax = plt.subplots(figsize=(8, 4.5))
KL = {}
K_SAVE = K_LEAK
for name, H, bd, col, ls in CASES:
    vals = []
    for kv in kk:
        K_LEAK = kv
        vals.append(20*np.log10(efield(sum(ext_currents(f0, H, bd, dh_for("V1", H), vharm(nn0), "V1")), f0)/1e-6))
    ax.semilogx(kk, vals, color=col, ls=ls, lw=2.3, label=name)
    KL[name] = dict(k001=round(vals[0], 1), k01=round(float(np.interp(np.log(0.1), np.log(kk), vals)), 1), k1=round(vals[-1], 1))
L_SAVE2 = L_BOLT; L_BOLT = 1e-9; vals = []
for kv in kk:
    K_LEAK = kv
    vals.append(20*np.log10(efield(sum(ext_currents(f0, 3e-3, True, dh_for("V1", 3e-3), vharm(nn0), "V1")), f0)/1e-6))
ax.semilogx(kk, vals, color=GOOD, ls=":", lw=2.3, label="Auf Blech, Anbindung 1 nH")
KL["Auf Blech, Anbindung 1 nH"] = dict(k001=round(vals[0], 1), k01=round(float(np.interp(np.log(0.1), np.log(kk), vals)), 1), k1=round(vals[-1], 1))
L_BOLT = L_SAVE2; K_LEAK = K_SAVE
ax.axhline(30, color=INK, lw=1.2); ax.text(0.011, 31, "Grenzwert Klasse B", fontsize=9)
ax.set_xlabel("Leckfaktor des Gehäuses (Anteil der Geräteanregung, der nach außen wirkt)")
ax.set_ylabel("E-Feld 10 m bei 150 MHz / dBµV/m")
ax.set_xticks([0.01, 0.03, 0.1, 0.3, 1]); ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())
ax.set_title("Offenes Gehäuse oder Anbindung ≤ 1 nH: dann gewinnt „flach am Blech“", loc="left")
ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)
fig.text(0.01, -0.2, "Pinbelegung V1, 3. Harmonische. 0,01 ≈ dichtes Metallgehäuse; 0,1 ≈ Display-Fenster und Lüftung; 1 ≈ offene Front oder Kunststoffgehäuse.", fontsize=9, color="#6b6f76")
save(fig, "13_leckfaktor")

# ---------------------------------------------------------------- Kennzahlen exportieren
summary = {k: dict(name=VARIANTS[k]["name"], h3=round(RES[k]["h3"], 3), h40=round(RES[k]["h40"], 3),
                   dh3=round(RES[k]["h3"]-H_PCB, 3), dh40=round(RES[k]["h40"]-H_PCB, 3),
                   L_loop_nH_25cm=round(RES[k]["L40"]*0.25e9, 1), sep_mm=round(RES[k]["sep"]*1e3, 2),
                   xt40_mV=round(RES[k]["xt40"]*VDD*1e3, 1), xt3_mV=round(RES[k]["xt3"]*VDD*1e3, 1))
           for k in VARIANTS}
z0 = dict(Z0_3mm=round(z0_cm(3e-3), 1), Z0_40mm=round(z0_cm(40e-3), 1))
tf = {name: {f"{int(f/1e6)}MHz": float(np.interp(f, fr, TF[name])) for f in [50e6, 150e6, 250e6, 450e6]} for name in TF}
emax = {f"{v}|{c}": dict(max_dB=round(float(E[(v, c)].max()), 1),
                         over_B=round(float((E[(v, c)] - limit(fh)).max()), 1)) for (v, c) in E}
json.dump(dict(variants=summary, z0=z0, tf=tf, emax=emax, kc=KC, sens=SENS, lid=LID, hinf=HINF, pb=PB, kl=KL, emax_full={f'{v}|{c}': [round(float(x),1) for x in E[(v,c)][:4]] for (v,c) in E}), open(os.path.join(OUT, "kennzahlen.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(dict(z0=z0, tf=tf, emax=emax, kc=KC), indent=1, ensure_ascii=False))
