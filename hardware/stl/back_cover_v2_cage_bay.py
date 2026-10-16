"""Rework back_cover_v2's battery bay to hold the Meshnology standoff cage.

Coordinates are the STL's (mm): x across the cover (131 wide), y along it (174.5), z with the
cover plate at 4.5 (outer face) .. 6.0 (inner face, device side); the bay protrudes toward -z.
The 3MF object mesh is the same geometry shifted +1.25 in z.
"""
import sys, numpy as np, trimesh, manifold3d as mf

SRC = sys.argv[1]          # back_cover_v2.stl (the unmodified MakerWorld original in this folder)
OUT = sys.argv[2]          # output STL path

# --- cage (from meshnology-10000mah-battery-standoffs.3mf) ---------------------------------
CAGE_L, CAGE_W, CAGE_T = 120.0, 70.0, 35.0
SF_X = 44.55               # short-frame band centre, +-x (notch 13.35..17.55 from long-frame end)
SF_BAND = 4.0              # short-frame band width along x
SF_INSET = 2.5             # short-frame faces sit 2.5 in from both cage faces
POUCH_HALF_W = 31.0        # 62 mm slot length

# --- bay ---------------------------------------------------------------------------------
Z_PLATE_OUT, Z_PLATE_IN = 4.5, 6.0
YC = -40.7                 # bay centre (same as the original bay)
HX, HY = 61.0, 35.5        # interior half-sizes: 122 x 71 (cage 120 x 70)
WALL, FLOOR = 2.0, 2.0
CORNER_R = 6.0             # outer vertical-corner radius, as on the original bay (inner = CORNER_R - WALL)
ZF = Z_PLATE_OUT - CAGE_T  # floor inner face: cage inner face lands flush with plate outer face
SF_TOP = ZF + CAGE_T - SF_INSET   # top (+z) edge of each short-frame end wall when seated

# rails (guide channel around each short-frame end wall)
CH_CLR, RIB_W, RIB_D = 0.3, 1.6, 2.0
RIB_TOP = SF_TOP - 0.8     # ribs stop below the latch zone; 45 deg lead-in chamfer at the top
# latch beams
BEAM_T, SLOT, BEAM_FREE = 1.6, 1.2, 20.0
BARB_D, BARB_H, BARB_W = 1.5, 1.5, 3.0
BARB_Z = SF_TOP + 0.2      # catch face, 0.2 above the end wall's top edge

def box(x0, x1, y0, y1, z0, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def prism_x(x0, x1, pts_yz):
    """Extrude a (y, z) polygon along x from x0 to x1."""
    # extrude in z over the (u=y, v=z) plane then map (u, v, w) -> (x=w, y=u, z=v)
    cs = mf.CrossSection([[(float(u), float(v)) for u, v in pts_yz]])
    m = mf.Manifold.extrude(cs, x1 - x0)                 # points (u, v, w)
    m = m.warp(lambda p: (p[2] + x0, p[0], p[1]))        # vertex map; mirror-free permutation
    return m

def rounded_box(hx, hy, r, cy, z0, z1):
    """Box of half-sizes hx, hy centred on (0, cy), vertical edges rounded to radius r."""
    cs = mf.CrossSection.square([2 * (hx - r), 2 * (hy - r)], True).offset(r, mf.JoinType.Round, 2, 128)
    return mf.Manifold.extrude(cs, z1 - z0).translate([0, cy, z0])

def load(path):
    t = trimesh.load(path)
    mesh = mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                   tri_verts=np.asarray(t.faces, np.uint32))
    return mf.Manifold(mesh)

cover = load(SRC)

# 1. remove the old bay (walls and floor below the plate)
cover = cover - box(-62.7, 62.7, -76.1, -5.3, -9.6, Z_PLATE_OUT)

# 2. new bay shell, merged into the plate, then the through-opening
y0, y1 = YC - HY, YC + HY
DECOR = True               # cyberpunk exterior detailing on the battery bay (2026-10-12)
FLOOR_CH = 2.5 if DECOR else 0.0   # 45 deg chamfer round the bay floor's outer edge
z_fo = ZF - FLOOR                  # floor outer face
cover = cover + rounded_box(HX + WALL, HY + WALL, CORNER_R, YC, z_fo + FLOOR_CH, Z_PLATE_OUT + 0.1)
if FLOOR_CH:
    top = rounded_box(HX + WALL, HY + WALL, CORNER_R, YC, z_fo + FLOOR_CH, z_fo + FLOOR_CH + 0.01)
    bot = rounded_box(HX + WALL - FLOOR_CH, HY + WALL - FLOOR_CH, CORNER_R - FLOOR_CH, YC, z_fo, z_fo + 0.01)
    cover = cover + mf.Manifold.batch_hull([top, bot])
cover = cover - rounded_box(HX, HY, CORNER_R - WALL, YC, ZF, Z_PLATE_IN + 1.0)

feats_add, feats_cut = [], []
for sx in (-1, 1):
    xc = sx * SF_X
    for sy in (-1, 1):
        wall_face = YC + sy * HY                       # interior wall face
        inward = -sy                                   # +1 means toward +y
        def yy(d):                                      # y at inward distance d from the wall face
            return wall_face + inward * d
        # --- guide ribs, both sides of the channel
        for side in (-1, 1):
            xa = xc + side * (SF_BAND / 2 + CH_CLR)
            xb = xa + side * RIB_W
            prof = [(yy(0), ZF), (yy(RIB_D), ZF), (yy(RIB_D), RIB_TOP - RIB_D), (yy(0), RIB_TOP)]
            if inward < 0:
                prof = prof[::-1]
            feats_add.append(prism_x(min(xa, xb), max(xa, xb), prof))
        # --- latch beam: root toward the bay centre, free tip just past the band
        x_root = xc - sx * (BEAM_FREE + SF_BAND / 2 + 2.0)
        x_tip = xc + sx * (SF_BAND / 2)
        bx0, bx1 = sorted((x_root, x_tip))
        # pocket through wall and plate behind the beam, leaving the root end attached
        px0, px1 = sorted((x_root + sx * 2.0, x_tip + sx * 1.0))
        pya, pyb = sorted((yy(0), yy(-(BEAM_T + SLOT))))
        feats_cut.append(box(px0, px1, pya, pyb, RIB_TOP + 0.4, Z_PLATE_IN + 1.0))
        # local bulge keeping a 2 mm wall outside the pocket
        gx0, gx1 = sorted((x_root, x_tip + sx * 3.0))
        gya, gyb = sorted((yy(-(BEAM_T + SLOT)), yy(-(BEAM_T + SLOT + WALL))))
        gya2, gyb2 = sorted((yy(-WALL + 0.01), yy(-(BEAM_T + SLOT + WALL))))
        feats_add.append(box(gx0, gx1, gya2, gyb2, RIB_TOP - 2.0, Z_PLATE_OUT + 0.1))
        # the beam itself
        bya, byb = sorted((yy(0), yy(-BEAM_T)))
        beam = box(bx0, bx1, bya, byb, BARB_Z, Z_PLATE_IN)
        # barb: ramp faces +z (incoming cage), flat catch at BARB_Z faces -z
        prof = [(yy(0), BARB_Z), (yy(BARB_D), BARB_Z), (yy(0), BARB_Z + BARB_H)]
        if inward < 0:
            prof = prof[::-1]
        barb = prism_x(xc - BARB_W / 2, xc + BARB_W / 2, prof)
        feats_add.append(('beam', beam + barb))

# bulges first, then pockets, then beams/ribs (beams must survive the pocket cut)
for f in feats_add:
    if not isinstance(f, tuple):
        cover = cover + f
for f in feats_cut:
    cover = cover - f
for f in feats_add:
    if isinstance(f, tuple):
        cover = cover + f[1]

# --- heat-sink pockets in place of the fin field and fan mount ---------------------------
# Over the CM4 the original has a recessed pan: floor z 1.9..3.15 (inside x +-57.7, y 5.05..65.45,
# open to the device side up to the plate's inner face for component clearance), fins hanging
# off its outer face, vent slots and a fan opening through it, and a screw post at (0, 6.45).
# Two 100 x 25 x 10 mm aluminium heat sinks go in side by side along y, dropped in from outside
# onto a ledge round one open window, so the CM4's thermal pad reaches their bases. Snug fit.
Z_PAN_OUT, Z_PAN_IN = 1.9, 3.15
HS_L, HS_W, HS_H = 100.0, 25.0, 10.0
HS_CLR = 0.15              # per side: snug; printed pockets usually come out slightly small
HS_LEDGE_W, HS_LEDGE_T = 1.5, 1.0
HS_DIV = 1.2               # locating stub between the two sinks (ends only, window stays open)
HS_STUB_L = 6.5
HS_WALL = 1.6
HS_WALL_H = 3.0            # owner: frame walls no more than 3 mm above the cover's outer surface
                           # around them (the pan floor's outer face); fins run lengthwise (x)
HS_Y0 = 11.2               # pocket inner edge nearest the bay; clear of the screw post (y <= 8.25)

# remove the fins and fan boss: everything outside the pan floor in the fin field
cover = cover - box(-59.3, 59.3, 3.5, 67.0, -12.0, Z_PAN_OUT)

px = HS_L / 2 + HS_CLR                     # pocket inner half-length
py0 = HS_Y0
py1 = py0 + 2 * (HS_W + 2 * HS_CLR) + HS_DIV
z_seat = Z_PAN_IN - HS_LEDGE_T            # sink base rests here (ledge inner face = pan inner face)
z_rim = Z_PAN_OUT - HS_WALL_H              # low rim: the fins stand clear above it
# close the pan floor's vent slots and fan opening under the pockets so the ledge is continuous;
# the outermost vent slots (|x| 53.3..54.7) stay open
cover = cover + box(-px - HS_WALL, px + HS_WALL, py0 - HS_WALL, py1 + HS_WALL, Z_PAN_OUT, Z_PAN_IN)
cover = cover + box(-px - HS_WALL, px + HS_WALL, py0 - HS_WALL, py1 + HS_WALL, z_rim, Z_PAN_OUT + 0.1)
cover = cover - box(-px, px, py0, py1, z_rim - 1.0, z_seat)                       # pocket
cover = cover - box(-px + HS_LEDGE_W, px - HS_LEDGE_W, py0 + HS_LEDGE_W, py1 - HS_LEDGE_W,
                    z_seat - 0.1, Z_PAN_IN + 0.2)                                  # open window
ym = py0 + HS_W + 2 * HS_CLR                                                       # stub position
for sx in (-1, 1):
    xa, xb = sorted((sx * px, sx * (px - HS_STUB_L)))
    cover = cover + box(xa, xb, ym, ym + HS_DIV, z_rim, Z_PAN_IN)
print('sink tops at z', z_seat - HS_H, '; side engagement', round(z_seat - z_rim, 2), 'mm')
print('heat-sink pockets: inner', round(2 * px, 2), 'x', round(py1 - py0, 2), 'y', round(py0, 2), '..', round(py1, 2),
      'seat z', z_seat, 'rim z', z_rim)

# --- cyberpunk exterior detailing on the battery bay ---------------------------------------
# Raised and recessed surface detail only: no openings, nothing inside the bay, walls and floor
# never thinner than 1.4 mm. Floor art is laid out as seen from outside, (a right, b up), then
# mirrored onto the model (x = -a, y = YC + b) so it reads the right way round from outside.
def thick_path(pts, w):
    """Polyline -> CrossSection with stroke width w, square caps (crisp, angular joins)."""
    out = mf.CrossSection()
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        L = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / L * w / 2, dy / L * w / 2
        nx, ny = -uy, ux
        poly = [(x0 - ux + nx, y0 - uy + ny), (x0 - ux - nx, y0 - uy - ny),
                (x1 + ux - nx, y1 + uy - ny), (x1 + ux + nx, y1 + uy + ny)]
        out = out + mf.CrossSection([poly])
    return out

def floor_layer(cs, z0, z1):
    """2D art in (a, b) -> solid between z0 and z1 on the bay floor (mirrored to read from outside)."""
    return mf.Manifold.extrude(cs.mirror([1, 0]).translate([0, YC]), z1 - z0).translate([0, 0, z0])

# copper name plate (owner, 2026-10-12): an 85 x 53 mm plate sits in a rounded recess in the armour plate
CU_W, CU_H, CU_R = 85.0, 53.0, 3.0   # plate size and corner radius
CU_CLR = 0.2                         # per side
CU_DEPTH = 1.0                       # recess depth = plate thickness (+ adhesive); floor stays 2 mm under it
CU_A = 3.5                           # recess centre along a (b = 0)

if DECOR:
    zf = z_fo
    # raised armour plate with clipped corners, framed by a recessed panel line
    pw, ph = CU_W + 2 * CU_CLR + 4.0, CU_H + 2 * CU_CLR + 4.0     # 2 mm border round the recess
    a0, a1, b0, b1 = CU_A - pw / 2, CU_A + pw / 2, -ph / 2, ph / 2
    clip = 4.0
    plate = mf.CrossSection([[(a0, b0), (a1 - clip, b0), (a1, b0 + clip), (a1, b1),
                              (a0 + clip, b1), (a0, b1 - clip)]])
    ring = plate.offset(2.0, mf.JoinType.Miter) - plate.offset(1.2, mf.JoinType.Miter)
    cover = cover - floor_layer(ring, zf - 0.1, zf + 0.5)
    cover = cover + floor_layer(plate, zf - 1.0, zf + 0.01)
    # rounded recess for the copper plate
    rw, rh, rr = CU_W / 2 + CU_CLR, CU_H / 2 + CU_CLR, CU_R + CU_CLR
    recess = mf.CrossSection.square([2 * (rw - rr), 2 * (rh - rr)], True).offset(rr, mf.JoinType.Round, 2, 96) \
        .translate([CU_A, 0])
    cover = cover - floor_layer(recess, zf - 1.1, zf - 1.0 + CU_DEPTH)
    # hazard stripes, recessed, in a clipped panel at the left end
    zone = mf.CrossSection([[(-59, -26), (-50, -26), (-46.5, -22.5), (-46.5, 30), (-55.5, 30), (-59, 26.5)]])
    stripes = mf.CrossSection()
    for k in range(-12, 14):
        x0 = -60 + k * 6.0
        stripes = stripes + mf.CrossSection([[(x0, -30), (x0 + 3.0, -30), (x0 + 3.0 + 60, 30), (x0 + 60, 30)]])
    cover = cover - floor_layer(stripes ^ zone, zf - 0.1, zf + 0.5)
    cover = cover - floor_layer(zone.offset(1.0, mf.JoinType.Miter) - zone.offset(0.5, mf.JoinType.Miter),
                                zf - 0.1, zf + 0.5)
    # fake vent slots at the right end
    for a in (53.6, 55.8, 58.0):
        cover = cover - floor_layer(mf.CrossSection([[(a - 0.6, -18), (a + 0.6, -18), (a + 0.6, 18), (a - 0.6, 18)]]),
                                    zf - 0.1, zf + 0.6)
    # circuit traces with via pads, raised 0.5 mm, in the margins above and below the plate
    traces = [[(-30, 28.7), (-30, 31), (-28, 33), (-12, 33)],
              [(20, 28.7), (20, 31), (22, 33), (42, 33)],
              [(-10, -28.7), (-10, -31), (-12, -33), (-30, -33)],
              [(36, -28.7), (36, -31), (38, -33), (50, -33)]]
    tr = mf.CrossSection()
    for t_ in traces:
        tr = tr + thick_path(t_, 0.8)
        tr = tr + mf.CrossSection.circle(1.2, 24).translate(list(t_[-1]))
    vias = mf.CrossSection()
    for t_ in traces:
        vias = vias + mf.CrossSection.circle(0.5, 16).translate(list(t_[-1]))
    cover = cover + floor_layer(tr - vias, zf - 0.5, zf + 0.01)

    # walls: (s, z) art, recessed 0.5 mm into the outer face
    def long_wall(cs, sy):
        # (s, z) -> x = s, y on the outer face of the +-y wall
        m_ = mf.Manifold.extrude(cs, 0.6).rotate([90, 0, 0])          # (s, z, w) -> (s, -w, z)
        y_out = YC + sy * (HY + WALL)
        return m_.translate([0, y_out + 0.5, 0]) if sy < 0 else m_.translate([0, y_out + 0.1, 0])
    def end_wall(cs, sx):
        m_ = mf.Manifold.extrude(cs, 0.6).rotate([90, 0, 0]).rotate([0, 0, 90])   # -> (w, s, z)
        x_out = sx * (HX + WALL)
        return m_.translate([x_out - 0.5, YC, 0]) if sx > 0 else m_.translate([x_out - 0.1, YC, 0])
    kink = thick_path([(-54, -20), (-30, -20), (-24, -14), (24, -14), (30, -20), (54, -20)], 1.0)
    slots = mf.CrossSection()
    for s0 in (-9, -4.5, 0, 4.5, 9):
        slots = slots + thick_path([(s0 - 1.5, -27), (s0 + 1.5, -22)], 1.2)
    for sy in (-1, 1):
        cover = cover - long_wall(kink + slots, sy)
    ends = mf.CrossSection()
    for t0 in (-8, -3, 2, 7):
        ends = ends + thick_path([(t0, -26), (t0, -8)], 1.2)
    ends = ends + thick_path([(-14, -5), (14, -5)], 0.8)
    for sx in (-1, 1):
        cover = cover - end_wall(ends, sx)

m = cover.to_mesh()
out = trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts), process=True)
print('watertight', out.is_watertight, 'volume', round(out.volume, 1), 'bounds', out.bounds.round(2).tolist(),
      'genus', cover.genus(), 'faces', len(out.faces))
out.export(OUT)

# --- clearance check against a seated cage envelope ----------------------------------------
cz0 = ZF
env = (box(-CAGE_L / 2, CAGE_L / 2, YC - POUCH_HALF_W, YC + POUCH_HALF_W, cz0, cz0 + CAGE_T)  # pouches + long frames, worst case
       + box(-SF_X - SF_BAND / 2, -SF_X + SF_BAND / 2, YC - CAGE_W / 2, YC + CAGE_W / 2, cz0 + SF_INSET, cz0 + CAGE_T - SF_INSET)
       + box(SF_X - SF_BAND / 2, SF_X + SF_BAND / 2, YC - CAGE_W / 2, YC + CAGE_W / 2, cz0 + SF_INSET, cz0 + CAGE_T - SF_INSET))
print('seated cage / cover overlap volume', round((env ^ cover).volume(), 4))
# insertion path: the end walls must pass the barbs (intended overlap = barb engagement)
ins = env.translate([0, 0, 3.0])
print('overlap 3 mm before seated (barbs engaged, expect >0)', round((ins ^ cover).volume(), 3))
print('SF_TOP', SF_TOP, 'ZF', ZF, 'BARB_Z', BARB_Z)
# heat sinks seated on the ledge must not touch the cover (beyond the snug side clearance)
sinks = (box(-HS_L / 2, HS_L / 2, py0 + HS_CLR, py0 + HS_CLR + HS_W, z_seat - HS_H, z_seat)
         + box(-HS_L / 2, HS_L / 2, ym + HS_DIV + HS_CLR, ym + HS_DIV + HS_CLR + HS_W, z_seat - HS_H, z_seat))
print('seated heat sinks / cover overlap volume', round((sinks ^ cover).volume(), 4))
print('heat sinks 0.2 mm lower (into the ledge), expect >0:', round((sinks.translate([0, 0, 0.2]) ^ cover).volume(), 2))
