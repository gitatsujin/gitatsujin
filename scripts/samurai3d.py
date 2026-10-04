"""
侍 Samurai 3D — renderiza no Blender (Cycles) um samurai low-poly que atravessa
o gráfico de contribuições em 3D, fatiando cada bloco com a katana.

Uso (precisa do módulo bpy):
  GITHUB_TOKEN=... python samurai3d.py --user gitatsujin --out dist
  python samurai3d.py --mock --out dist            # dados de exemplo
  python samurai3d.py --mock --still 60            # renderiza só o quadro 60
"""
import argparse, json, math, os, random, subprocess, sys, urllib.request
import bpy

# ------------------------------------------------------------------ dados --
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
weeks{contributionDays{contributionLevel weekday}}}}}}"""


def fetch_weeks(user, token):
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "samurai3d"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in data:
        raise SystemExit(f"Erro da API do GitHub: {data['errors']}")
    grid = []
    for w in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        col = [None] * 7
        for d in w["contributionDays"]:
            col[d["weekday"]] = LEVELS.get(d["contributionLevel"], 0)
        grid.append(col)
    return grid


def mock_weeks(seed=3, density=0.45):
    rnd = random.Random(seed)
    return [[None if (c == 52 and r > 3) else (rnd.choice([1, 1, 2, 2, 3, 4]) if rnd.random() < density else 0)
             for r in range(7)] for c in range(53)]

# --------------------------------------------------------------- materiais --


def hexrgb(h, a=1.0):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


def mat(name, color, rough=0.5, metal=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hexrgb(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = hexrgb(emit)
        bsdf.inputs["Emission Strength"].default_value = emit_str
    return m

# ----------------------------------------------------------------- malhas --


def mesh_obj(name, verts, faces, mats, mat_idx=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for m in mats:
        me.materials.append(m)
    if mat_idx:
        for poly, i in zip(me.polygons, mat_idx):
            poly.material_index = i
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return ob


def prim(kind, name, mat_, loc, scale=(1, 1, 1), rot=(0, 0, 0), parent=None, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(location=loc, rotation=rot, **kw)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(mat_)
    if parent:
        ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def key(ob, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame)
    if rot is not None:
        ob.rotation_euler = rot
        ob.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        ob.scale = scale
        ob.keyframe_insert("scale", frame=frame)

# ------------------------------------------------------------------ cena --


STEP, S = 1.25, 0.5                # passo da grade e meia largura do bloco
FPS = 18
RUN0, RUN1 = 8, 98                 # quadros em que o samurai corre
END = 142                          # último quadro
LANE_Y = -2.1                      # faixa onde o samurai corre (à frente da grade)
LEVEL_COL = ["#1c2029", "#4a0d14", "#7d111c", "#b3141f", "#ff2a2a"]
LEVEL_EMIT = [0.0, 0.04, 0.1, 0.25, 0.9]


def build(grid, zan):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, END
    rnd = random.Random(11)
    cols = len(grid)
    x_of = lambda c: c * STEP
    x_end = x_of(cols - 1)

    # mundo escuro com leve névoa avermelhada
    world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = hexrgb("#07080b")
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    M = {
        "ground": mat("ground", "#0b0d12", rough=0.28),
        "hot": mat("hot", "#ff9a7a", rough=0.3, emit="#ff2a14", emit_str=1.1),
        "washi": mat("washi", "#2b2c33", rough=0.55),
        "skin": mat("skin", "#e2b48c", rough=0.6),
        "hakama": mat("hakama", "#111217", rough=0.6),
        "red": mat("red", "#c8102e", rough=0.5, emit="#c8102e", emit_str=0.3),
        "hair": mat("hair", "#0b0b0d", rough=0.5),
        "steel": mat("steel", "#e8edf3", rough=0.12, metal=1.0),
        "gold": mat("gold", "#d4a017", rough=0.3, metal=1.0),
        "saya": mat("saya", "#141416", rough=0.25),
        "slash": mat("slash", "#ffffff", rough=1.0, emit="#ffe2e2", emit_str=14.0),
        "sun": mat("sun", "#c8102e", emit="#e0262f", emit_str=3.0),
        "zan": mat("zan", "#070708", rough=0.3),
        "petal": mat("petal", "#ffb7c5", rough=0.6, emit="#ff9fb4", emit_str=0.6),
    }
    lv = [mat(f"lv{i}", LEVEL_COL[i], rough=0.42, emit=LEVEL_COL[i], emit_str=LEVEL_EMIT[i]) for i in range(5)]

    # chão reflexivo e sol vermelho ao fundo
    mesh_obj("ground", [(-60, -60, 0), (x_end + 60, -60, 0), (x_end + 60, 80, 0), (-60, 80, 0)], [(0, 1, 2, 3)], [M["ground"]])
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=12, fill_type='NGON', location=(x_end / 2, 70, 6), rotation=(math.pi / 2, 0, 0))
    sun = bpy.context.active_object; sun.data.materials.append(M["sun"])

    # ---------------------------------------------------- blocos fatiados --
    cut_frame = {}
    for c, col in enumerate(grid):
        fc = RUN0 + (RUN1 - RUN0) * (c + 0.6) / cols
        cut_frame[c] = fc
        for r, lvl in enumerate(col):
            if lvl is None:
                continue
            h = 0.3 + lvl * 0.32
            x0, y0 = x_of(c), r * STEP
            k = min(0.42, 0.55 * h)                    # inclinação do corte
            zc = h * 0.52
            cz = lambda dx: zc + k * dx
            corners = [(-S, -S), (S, -S), (S, S), (-S, S)]
            low_v = [(dx, dy, 0) for dx, dy in corners] + [(dx, dy, cz(dx)) for dx, dy in corners]
            faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            low = mesh_obj(f"lo{c}_{r}", low_v, faces, [lv[lvl], M["hot"]], [0, 1, 0, 0, 0, 0], (x0, y0, 0))
            up_v = [(dx, dy, cz(dx)) for dx, dy in corners] + [(dx, dy, h) for dx, dy in corners]
            cxm, czm = 0.0, (zc + h) / 2
            up_v = [(vx - cxm, vy, vz - czm) for vx, vy, vz in up_v]
            up = mesh_obj(f"up{c}_{r}", up_v, faces, [lv[lvl], M["hot"]], [1, 0, 0, 0, 0, 0], (x0, y0, czm))
            # animação: a parte de cima desliza, voa e cai tombando
            f = fc + r * 0.35
            hup = h - zc
            dy = 0.8 + rnd.uniform(0, 0.8)
            dx = rnd.uniform(-0.2, 0.6)
            key(up, 1, loc=(x0, y0, czm), rot=(0, 0, 0))
            key(up, f, loc=(x0, y0, czm), rot=(0, 0, 0))
            key(up, f + 3, loc=(x0 + dx * 0.4, y0 + dy * 0.35, czm + 0.55), rot=(rnd.uniform(-.6, -.2), rnd.uniform(-.5, .5), rnd.uniform(-.4, .4)))
            land = (x0 + dx, y0 + dy, max(0.25, hup * 0.45))
            key(up, f + 11, loc=land, rot=(rnd.uniform(-1.8, -1.2), rnd.uniform(-.9, .9), rnd.uniform(-.8, .8)))
            key(up, END, loc=land, rot=up.rotation_euler[:])

    # pétalas de sakura
    for i in range(46):
        c = rnd.randrange(cols)
        f = cut_frame[c] + rnd.uniform(0, 3)
        p0 = (x_of(c) + rnd.uniform(-.3, .3), rnd.uniform(0, 6 * STEP), rnd.uniform(1.0, 2.4))
        bpy.ops.mesh.primitive_plane_add(size=0.16, location=p0)
        pt = bpy.context.active_object; pt.data.materials.append(M["petal"])
        key(pt, 1, scale=(0, 0, 0)); key(pt, f, scale=(0, 0, 0), loc=p0, rot=(0, 0, 0))
        key(pt, f + 1, scale=(1, 0.6, 1))
        key(pt, f + 30, loc=(p0[0] + rnd.uniform(1, 3), p0[1] + rnd.uniform(1, 3), 0.02), rot=(rnd.uniform(3, 9), rnd.uniform(3, 9), rnd.uniform(3, 9)))
        key(pt, END, scale=(1, 0.6, 1))

    # rastro do corte (lâminas de luz que cruzam cada coluna)
    pool = []
    for i in range(6):
        verts = [(-0.06, -0.8, -0.03), (0.06, -0.8, 0.03), (0.06, 7 * STEP, 0.03), (-0.06, 7 * STEP, -0.03)]
        ob = mesh_obj(f"slash{i}", verts, [(0, 1, 2, 3)], [M["slash"]], loc=(0, 0, 0))
        key(ob, 1, scale=(0, 0, 0))
        pool.append(ob)
    for c in range(cols):
        ob = pool[c % len(pool)]
        f = cut_frame[c]
        ob.rotation_euler = (0, -0.42, 0)
        key(ob, f - 0.6, scale=(0, 0, 0), loc=(x_of(c), 0, 0.7), rot=(0, -0.42, 0))
        key(ob, f, scale=(1, 0, 1))
        key(ob, f + 0.4, scale=(1.4, 1, 1))
        key(ob, f + 3.5, scale=(0, 1, 0))

    # -------------------------------------------------------------- samurai --
    root = empty("samurai"); root.scale = (1.55, 1.55, 1.55)
    lean = empty("lean", parent=root); lean.rotation_euler = (0, 0.32, 0)
    # pernas (hakama larga) com pivô no quadril
    legs = []
    for side, yy in (("L", 0.17), ("R", -0.17)):
        hip = empty(f"hip{side}", (0, yy, 1.0), parent=lean)
        prim("cone", f"leg{side}", M["hakama"], (0, 0, -0.5), parent=hip, vertices=7, radius1=0.3, radius2=0.17, depth=1.0)
        prim("cube", f"foot{side}", M["hair"], (0.12, 0, -0.98), scale=(0.16, 0.08, 0.04), parent=hip)
        legs.append(hip)
    prim("cone", "hakamaTop", M["hakama"], (0, 0, 1.05), parent=lean, vertices=8, radius1=0.42, radius2=0.3, depth=0.35)
    prim("cylinder", "obi", M["red"], (0, 0, 1.26), parent=lean, vertices=8, radius=0.31, depth=0.12)
    prim("cone", "torso", M["washi"], (0, 0, 1.6), parent=lean, vertices=8, radius1=0.3, radius2=0.42, depth=0.62)
    prim("cube", "collar", M["red"], (0.27, 0, 1.78), scale=(0.04, 0.16, 0.12), rot=(0, 0.3, 0), parent=lean)
    # mangas largas ao vento
    sleeve = prim("cone", "sleeve", M["washi"], (-0.25, 0.42, 1.68), parent=lean, vertices=6, radius1=0.24, radius2=0.08, depth=0.7, rot=(0.3, -1.2, 0))
    # cabeça
    prim("ico_sphere", "head", M["skin"], (0.05, 0, 2.12), scale=(0.21, 0.2, 0.23), parent=lean, subdivisions=2)
    prim("ico_sphere", "hairback", M["hair"], (-0.04, 0, 2.18), scale=(0.2, 0.2, 0.2), parent=lean, subdivisions=1)
    prim("cylinder", "topknot", M["hair"], (-0.08, 0, 2.42), scale=(0.11, 0.05, 0.05), rot=(0, 1.5708, 0), parent=lean, vertices=6)
    prim("torus", "band", M["red"], (0.03, 0, 2.2), rot=(0, 0.25, 0), parent=lean, major_radius=0.215, minor_radius=0.03, major_segments=12, minor_segments=4)
    tails = []
    for i, zz in enumerate((2.22, 2.16)):
        t = prim("cube", f"tail{i}", M["red"], (-0.45, 0.02 * i, zz), scale=(0.25, 0.012, 0.035), rot=(0.2 * i, -0.15, 0.1), parent=lean)
        tails.append(t)
    # bainha na cintura
    prim("cylinder", "saya", M["saya"], (-0.35, -0.33, 1.15), scale=(0.035, 0.035, 0.55), rot=(0, 1.9, 0.25), parent=lean, vertices=6)
    # braço da espada (pivô no ombro)
    sh = empty("shoulder", (0.1, -0.33, 1.82), parent=lean)
    prim("cylinder", "arm", M["washi"], (0.22, 0, -0.08), scale=(0.08, 0.08, 0.26), rot=(0, 1.9, 0), parent=sh, vertices=6)
    grip = empty("grip", (0.46, 0, -0.18), parent=sh)
    prim("cylinder", "tsuka", M["red"], (0.12, 0, 0), scale=(0.035, 0.035, 0.14), rot=(0, 1.5708, 0), parent=grip, vertices=6)
    prim("cylinder", "tsuba", M["gold"], (0.27, 0, 0), scale=(0.09, 0.09, 0.015), rot=(0, 1.5708, 0), parent=grip, vertices=10)
    blade_v = [(0.28, 0, -0.035), (0.28, 0, 0.05), (1.4, 0, 0.12), (2.25, 0, 0.0), (1.4, 0, 0.04)]
    blade_v = [(x, y + dy, z) for x, y, z in blade_v for dy in (0.02, -0.02)]
    bf = [(0, 2, 4, 6, 8), (1, 9, 7, 5, 3), (0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 7, 6), (6, 7, 9, 8), (8, 9, 1, 0)]
    blade = mesh_obj("blade", blade_v, bf, [M["steel"]]); blade.parent = grip
    # arco de energia que acompanha o golpe
    arc_v = []
    for i in range(13):
        a = -1.1 + 2.2 * i / 12
        arc_v += [(1.15 * math.cos(a) + 0.4, 0, 1.15 * math.sin(a)), (1.45 * math.cos(a) + 0.4, 0, 1.45 * math.sin(a) * 1.05)]
    arc_f = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(12)]
    arc = mesh_obj("arc", arc_v, arc_f, [M["slash"]]); arc.parent = sh

    # corrida (posição calculada quadro a quadro, sem interpolação ambígua)
    run_start_x, run_end_x = -2.5, x_end + 1.0

    def sam_x(f):
        if f <= RUN0:
            return run_start_x - 6 + 6 * (f - 1) / (RUN0 - 1)
        if f <= RUN1:
            return run_start_x + (run_end_x - run_start_x) * (f - RUN0) / (RUN1 - RUN0)
        return run_end_x + (f - RUN1) * 0.9
    for f in range(1, END + 1):
        key(root, f, loc=(sam_x(f), LANE_Y, 0))
    # passadas, golpes e tecido ao vento
    period = 6
    for f in range(1, END + 1, period // 2):
        ph = ((f - 1) // (period // 2)) % 2
        key(legs[0], f, rot=(0, (0.75 if ph else -0.75), 0))
        key(legs[1], f, rot=(0, (-0.75 if ph else 0.75), 0))
        key(tails[0], f, rot=(0.2, -0.15 + (0.25 if ph else -0.1), 0.1))
        key(tails[1], f, rot=(0.0, -0.1 + (-0.2 if ph else 0.15), 0.1))
        key(sleeve, f, rot=(0.3 + (0.25 if ph else -0.1), -1.2, 0))
    swing = 4
    for f in range(1, END + 1, swing):
        key(sh, f, rot=(0.2, -1.25, 0.3))                  # katana erguida
        key(sh, f + swing * 0.55, rot=(-0.1, 1.05, -0.2))  # golpe descendo
        key(arc, f, scale=(0.3, 1, 0.3))
        key(arc, f + swing * 0.3, scale=(1, 1, 1))
        key(arc, f + swing * 0.6, scale=(0, 0, 0))

    # ---------------------------------------------------- final: 斬 em 3D --
    cu = bpy.data.curves.new("zan", "CURVE"); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = 0.08; cu.bevel_depth = 0.015
    for cont in zan:
        sp = cu.splines.new('POLY'); sp.points.add(len(cont) - 1)
        for p, (x, y) in zip(sp.points, cont):
            p.co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    zo = bpy.data.objects.new("zan", cu); sc.collection.objects.link(zo)
    cu.materials.append(M["zan"])
    zo.rotation_euler = (math.pi / 2, 0, 0)
    zx, zy = x_end / 2, 7 * STEP + 3
    key(zo, 1, loc=(zx, zy, -6), scale=(4, 4, 4))
    key(zo, RUN1 + 6, loc=(zx, zy, -6), scale=(4, 4, 4))
    key(zo, RUN1 + 24, loc=(zx, zy, 9.0), scale=(5.2, 5.2, 5.2))

    # ---------------------------------------------------------------- luzes --
    def light(kind, name, energy, color, loc, rot, size=None):
        ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = hexrgb(color)[:3]
        if size and kind == 'AREA':
            ld.size = size
        lo = bpy.data.objects.new(name, ld); lo.location = loc; lo.rotation_euler = rot
        sc.collection.objects.link(lo)
        return lo
    light('SUN', "key", 1.3, "#ffe7cf", (0, 0, 10), (0.75, 0.15, -0.55))
    light('SUN', "rim", 3.0, "#ff3040", (0, 0, 10), (-1.0, 0, 3.3))
    light('SUN', "fill", 0.4, "#9fb7ff", (0, 0, 10), (0.9, 0, 0.6))

    # ---------------------------------------------------------------- câmera --
    cam = bpy.data.cameras.new("cam"); cam.lens = 30
    co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
    tgt = empty("target")
    tc = co.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

    def follow(f, x):
        key(co, f, loc=(x + 7.5, LANE_Y - 11.5, 4.6))
        key(tgt, f, loc=(x + 0.2, 1.2, 1.5))
    for f in range(1, RUN1 + 1):
        follow(f, min(sam_x(f), run_end_x))
    key(co, RUN1 + 22, loc=(x_end / 2, -31, 12))
    key(tgt, RUN1 + 22, loc=(x_end / 2, 8, 3.2))
    key(co, END, loc=(x_end / 2, -29, 11.5))
    key(tgt, END, loc=(x_end / 2, 8, 3.2))
    cam.lens = 30
    cam.keyframe_insert("lens", frame=RUN1)
    cam.lens = 24
    cam.keyframe_insert("lens", frame=RUN1 + 22)
    return sc


def render(sc, out, w, h, samples, still=None):
    r = sc.render
    r.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    r.resolution_x, r.resolution_y = w, h
    r.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'Medium High Contrast'
    r.image_settings.file_format = 'PNG'
    os.makedirs(out, exist_ok=True)
    if still:
        sc.frame_set(still)
        r.filepath = os.path.join(out, f"still_{still:03d}.png")
        bpy.ops.render.render(write_still=True)
    else:
        r.filepath = os.path.join(out, "frames", "f_")
        bpy.ops.render.render(animation=True)


def make_webp(out, fps):
    """Monta o WebP animado (bem menor e com mais cores que um GIF)."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    fade = f"fade=t=in:st=0:d=0.25,fade=t=out:st={END / fps - 0.35:.2f}:d=0.35"
    subprocess.run([ff, "-y", "-v", "error", "-framerate", str(fps),
                    "-i", os.path.join(out, "frames", "f_%04d.png"), "-vf", fade,
                    "-c:v", "libwebp", "-quality", "75", "-compression_level", "2", "-loop", "0",
                    os.path.join(out, "samurai3d.webp")], check=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER"))
    ap.add_argument("--out", default="dist")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--still", type=int)
    ap.add_argument("--width", type=int, default=880)
    ap.add_argument("--height", type=int, default=360)
    ap.add_argument("--samples", type=int, default=24)
    a = ap.parse_args(argv)
    grid = mock_weeks() if a.mock else fetch_weeks(a.user, os.environ["GITHUB_TOKEN"])
    sc = build(grid, ZAN)
    render(sc, a.out, a.width, a.height, a.samples, a.still)
    if not a.still:
        make_webp(a.out, FPS)
        print("Pronto:", os.path.join(a.out, "samurai3d.webp"))


# contornos do kanji 斬 (Noto Serif CJK JP, SIL Open Font License), normalizados
ZAN = [[[-0.4686,0.2263],[-0.4686,-0.1837],[-0.4526,-0.1837],[-0.437,-0.1827],[-0.4218,-0.1799],[-0.4074,-0.1758],[-0.3944,-0.1708],[-0.3834,-0.1654],[-0.3749,-0.1599],[-0.3694,-0.1549],[-0.3674,-0.1507],[-0.3674,-0.1273],[-0.3174,-0.1273],[-0.3174,-0.2508],[-0.5069,-0.2508],[-0.4984,-0.2817],[-0.3174,-0.2817],[-0.3174,-0.4979],[-0.2961,-0.4979],[-0.2745,-0.4968],[-0.2553,-0.4939],[-0.2387,-0.4897],[-0.2248,-0.4847],[-0.2138,-0.4793],[-0.2058,-0.4741],[-0.2008,-0.4694],[-0.1991,-0.4659],[-0.1991,-0.2817],[-0.0043,-0.2817],[0.0021,-0.2806],[-0.0057,-0.3087],[-0.0148,-0.3361],[-0.0252,-0.363],[-0.0371,-0.3892],[-0.0506,-0.4149],[-0.0657,-0.44],[-0.0825,-0.4644],[-0.1012,-0.4883],[-0.0895,-0.5],[-0.016,-0.4468],[0.0405,-0.3879],[0.0822,-0.3244],[0.1114,-0.2575],[0.1303,-0.1882],[0.141,-0.1178],[0.1458,-0.0474],[0.147,0.0218],[0.147,0.0783],[0.2524,0.0783],[0.2524,-0.4989],[0.2748,-0.4989],[0.2974,-0.498],[0.3174,-0.4953],[0.3346,-0.4915],[0.3489,-0.487],[0.3603,-0.4821],[0.3687,-0.4774],[0.3739,-0.4733],[0.3759,-0.4702],[0.3759,0.0783],[0.4771,0.0783],[0.4825,0.0785],[0.4876,0.0793],[0.4922,0.0806],[0.4964,0.0824],[0.5,0.0848],[0.503,0.0877],[0.5053,0.0912],[0.5069,0.0953],[0.489,0.1116],[0.4694,0.1286],[0.4495,0.1456],[0.4305,0.1615],[0.4136,0.1754],[0.4,0.1865],[0.3909,0.1938],[0.3876,0.1965],[0.3227,0.1092],[0.147,0.1092],[0.147,0.3264],[0.1839,0.3312],[0.2209,0.3368],[0.2575,0.343],[0.2931,0.3497],[0.3272,0.3567],[0.3593,0.364],[0.3889,0.3713],[0.4153,0.3786],[0.4279,0.3759],[0.4393,0.3743],[0.4496,0.3737],[0.4587,0.3741],[0.4668,0.3753],[0.4737,0.3774],[0.4797,0.3803],[0.4846,0.3839],[0.3355,0.4989],[0.3191,0.4829],[0.3,0.4655],[0.2784,0.4472],[0.2551,0.4282],[0.2303,0.4092],[0.2046,0.3904],[0.1784,0.3722],[0.1523,0.3552],[0.0298,0.3946],[0.0298,0.0229],[0.0296,-0.0122],[0.029,-0.0471],[0.0279,-0.0819],[0.026,-0.1163],[0.0232,-0.1505],[0.0195,-0.1844],[0.0146,-0.2178],[0.0085,-0.2508],[-0.0076,-0.237],[-0.0241,-0.2232],[-0.0404,-0.21],[-0.0555,-0.1978],[-0.0687,-0.1874],[-0.0791,-0.1792],[-0.0859,-0.1739],[-0.0884,-0.172],[-0.1502,-0.2508],[-0.1991,-0.2508],[-0.1991,-0.1273],[-0.1502,-0.1273],[-0.1502,-0.1667],[-0.1331,-0.1667],[-0.119,-0.1656],[-0.1042,-0.1629],[-0.0895,-0.1588],[-0.0757,-0.1539],[-0.0636,-0.1486],[-0.0539,-0.1433],[-0.0473,-0.1385],[-0.0447,-0.1347],[-0.0447,0.1816],[-0.0378,0.1834],[-0.0314,0.1855],[-0.0255,0.1878],[-0.0202,0.1904],[-0.0155,0.193],[-0.0115,0.1957],[-0.0081,0.1983],[-0.0053,0.2007],[-0.1108,0.2806],[-0.1597,0.2263],[-0.1991,0.2263],[-0.1991,0.32],[-0.0213,0.32],[-0.0159,0.3203],[-0.011,0.321],[-0.0065,0.3223],[-0.0025,0.3241],[0.0009,0.3265],[0.0037,0.3295],[0.0059,0.333],[0.0075,0.3371],[-0.0088,0.3518],[-0.0266,0.3674],[-0.0447,0.3831],[-0.062,0.3979],[-0.0775,0.411],[-0.0899,0.4214],[-0.0982,0.4283],[-0.1012,0.4308],[-0.1608,0.3498],[-0.1991,0.3498],[-0.1991,0.4595],[-0.1904,0.4611],[-0.1832,0.4633],[-0.1774,0.466],[-0.1728,0.4694],[-0.1693,0.4732],[-0.1668,0.4775],[-0.1651,0.4822],[-0.164,0.4872],[-0.3174,0.5],[-0.3174,0.3498],[-0.4995,0.3498],[-0.4909,0.32],[-0.3174,0.32],[-0.3174,0.2263],[-0.3621,0.2263],[-0.4686,0.271]],[[-0.3088,0.041],[-0.3088,-0.0964],[-0.3674,-0.0964],[-0.3674,0.041]],[[-0.2066,0.041],[-0.1502,0.041],[-0.1502,-0.0964],[-0.2066,-0.0964]],[[-0.3088,0.0708],[-0.3674,0.0708],[-0.3674,0.1965],[-0.3088,0.1965]],[[-0.2066,0.0708],[-0.2066,0.1965],[-0.1502,0.1965],[-0.1502,0.0708]]]

if __name__ == "__main__":
    main()
