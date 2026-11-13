"""Marlin previz: Blender blockout scenes for the 3D shots of Storyboard V5.

Builds every scene from code (models, night ocean, moonlight, spray, animated vessels and camera),
renders an image sequence with Cycles (CPU), writes per-frame screen tracks for overlays and saves
the .blend so the camera and blocking can be opened and reused.

  /opt/venv-blender/bin/python blender/previz.py --shot 01 --out blender/out
  /opt/venv-blender/bin/python blender/previz.py --shot 07 --still 2.0 --res 960x540   # one look-dev frame
  /opt/venv-blender/bin/python blender/previz.py --shot 10 --ir                        # thermal pass

Shots: 01 the boat · 03 infrared ID (--ir implied) · 06 loiter · 07 lift · 09 the run · 10 eyes on
Units are metres; +X is the direction of travel; the camera sits on the -Y side so bows point screen-right.
"""
import argparse, json, math, os, sys, time
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

FPS = 24
KT = 0.514444
IR = False  # thermal "white-hot" look: every material becomes a grey emitter
TILE = 80.0  # ocean tile period (m)
HAZE_COLOR = (0.02, 0.034, 0.066)  # set per shot from the sky's horizon colour
FAR_SEA = 0.5  # far-sea tone as a fraction of the haze colour
SHEET_GLOW = 0.85  # brightness of the spray sheets
SPRAY_GLOW = 0.5  # backlit spray reads as silver (droplets are too small to light properly at this sample count)
SPRAY_SCALE = 0.42  # global droplet size multiplier
SPRAY_COUNT = 4.0  # global droplet count multiplier

rad = math.radians


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else float(t >= b)


def lerp(a, b, k):
    return a + (b - a) * k


def vlerp(a, b, k):
    return tuple(lerp(x, y, k) for x, y in zip(a, b))


def wobble(t, seed, freqs=(0.7, 1.3, 2.9)):
    """Small smooth pseudo-random signal in [-1, 1]."""
    return sum(math.sin(2 * math.pi * f * t + seed * (i + 1) * 1.7) / (i + 1) for i, f in enumerate(freqs)) / 1.83


# ----------------------------------------------------------------------------- scene basics
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.unit_settings.system = 'METRIC'
    return sc


def link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def empty(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = 0.5
    ob.location = loc
    ob.rotation_euler = rot
    return link(ob, parent)


def mesh_obj(name, bm, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), smooth=False, sharp=None, bevel=0.0, subsurf=0,
             solidify=0.0):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        if sharp:
            me.set_sharp_from_angle(angle=rad(sharp))
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    if mat is not None:
        me.materials.append(mat)
    if solidify:
        md = ob.modifiers.new('solid', 'SOLIDIFY')
        md.thickness = solidify
        md.offset = 0
    if bevel:
        md = ob.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = 2
        md.limit_method = 'ANGLE'
    if subsurf:
        md = ob.modifiers.new('sub', 'SUBSURF')
        md.levels = md.render_levels = subsurf
    return link(ob, parent)


def box(name, size, mat, **kw):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    return mesh_obj(name, bm, mat, **kw)


def sphere(name, radius, mat, scale=(1, 1, 1), seg=24, **kw):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=radius)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return mesh_obj(name, bm, mat, smooth=True, **kw)


def cyl(name, r, h, mat, r2=None, seg=28, caps=True, **kw):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    kw.setdefault('smooth', True)
    kw.setdefault('sharp', 50)
    return mesh_obj(name, bm, mat, **kw)


def plate(name, pts, mat, thickness, **kw):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in pts])
    return mesh_obj(name, bm, mat, solidify=thickness, **kw)


# ----------------------------------------------------------------------------- materials
class NT:
    """Tiny helper for wiring shader nodes."""

    def __init__(self, tree):
        self.t = tree
        self.n = tree.nodes
        self.l = tree.links

    def node(self, typ, **props):
        n = self.n.new(typ)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.l.new(a, b)

    def set(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        else:
            self.link(v, sock)

    def val(self, v, name=None):
        n = self.node('ShaderNodeValue')
        n.outputs[0].default_value = v
        if name:
            n.name = n.label = name
        return n.outputs[0]

    def math(self, op, a, b=None, c=None, clamp_=False):
        n = self.node('ShaderNodeMath', operation=op)
        n.use_clamp = clamp_
        for i, x in enumerate((a, b, c)):
            if x is not None:
                self.set(n.inputs[i], x)
        return n.outputs[0]

    def sstep(self, x, e0, e1):
        n = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        self.set(n.inputs['Value'], x)
        self.set(n.inputs['From Min'], e0)
        self.set(n.inputs['From Max'], e1)
        n.inputs['To Min'].default_value = 0.0
        n.inputs['To Max'].default_value = 1.0
        return n.outputs['Result']


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    # glow here is a look, not lighting: keep emissive surfaces (spray, haze, thermal) out of light sampling
    try:
        m.cycles.emission_sampling = 'NONE'
    except Exception:
        pass
    nt = NT(m.node_tree)
    out = nt.node('ShaderNodeOutputMaterial')
    return m, nt, out


def ir_emission(nt, level):
    """Thermal look: brighter facing the sensor, darker at grazing angles so shapes still read."""
    lw = nt.node('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.3
    k = nt.math('SUBTRACT', 1.0, nt.math('MULTIPLY', lw.outputs['Facing'], 0.6))
    em = nt.node('ShaderNodeEmission')
    nt.set(em.inputs['Strength'], nt.math('MULTIPLY', k, level))
    return em.outputs[0]


_mats = {}


def M(name, color, rough=0.6, metal=0.0, ir=0.5, emit=0.0):
    key = (name, IR)
    if key in _mats:
        return _mats[key]
    m, nt, out = new_mat(name + ('_ir' if IR else ''))
    if IR:
        nt.link(ir_emission(nt, ir), out.inputs['Surface'])
    else:
        b = nt.node('ShaderNodeBsdfPrincipled')
        b.inputs['Base Color'].default_value = (*color, 1)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if emit:
            b.inputs['Emission Color'].default_value = (*color, 1)
            b.inputs['Emission Strength'].default_value = emit
        nt.link(b.outputs[0], out.inputs['Surface'])
    _mats[key] = m
    return m


def marlin_pod_material():
    """Defense grey with a darker band and charcoal underside (no white, no blue)."""
    key = ('marlin_pod', IR)
    if key in _mats:
        return _mats[key]
    m, nt, out = new_mat('marlin_pod' + ('_ir' if IR else ''))
    if IR:
        nt.link(ir_emission(nt, 0.5), out.inputs['Surface'])
    else:
        tc = nt.node('ShaderNodeTexCoord')
        sep = nt.node('ShaderNodeSeparateXYZ')
        nt.link(tc.outputs['Object'], sep.inputs[0])
        rampn = nt.node('ShaderNodeValToRGB')
        rampn.color_ramp.interpolation = 'CONSTANT'
        e = rampn.color_ramp.elements
        e[0].position = 0.0
        e[0].color = (0.045, 0.048, 0.052, 1)  # charcoal underside
        e[1].position = 0.40
        e[1].color = (0.13, 0.14, 0.15, 1)  # darker band
        e2 = e.new(0.52)
        e2.color = (0.26, 0.28, 0.30, 1)  # haze grey topsides
        nt.link(nt.math('ADD', nt.math('MULTIPLY', sep.outputs['Z'], 0.9), 0.5), rampn.inputs['Fac'])
        b = nt.node('ShaderNodeBsdfPrincipled')
        nt.link(rampn.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.5
        nt.link(b.outputs[0], out.inputs['Surface'])
    _mats[key] = m
    return m


def water_material(vessels, foam_attr=True, far=False):
    """Night ocean. Wakes and bow waves are painted in the shader from each vessel's local coordinates,
    so the foam sits exactly on the displaced surface and stays behind as the vessel moves on.
    Animatable per vessel: wake_strength_<name>, wake_w0_<name>, wake_side_<name>."""
    m, nt, out = new_mat(('water_far' if far else 'water') + ('_ir' if IR else ''))
    geo = nt.node('ShaderNodeNewGeometry')
    pos = geo.outputs['Position']

    def noise(scale, detail, lo, hi):
        n = nt.node('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        nt.link(pos, n.inputs['Vector'])
        return nt.sstep(n.outputs['Fac'], lo, hi)

    nz1 = nz2 = None
    if vessels:
        nz1 = noise(0.9, 2.0, 0.36, 0.62)
        nz2 = noise(2.8, 1.5, 0.40, 0.66)
    total = None
    for v in vessels:
        name, xs, xb, beam, length = v['name'], v['xs'], v['xb'], v['beam'], v.get('wake_len', 90.0)
        tc = nt.node('ShaderNodeTexCoord')
        tc.object = v['root']
        sep = nt.node('ShaderNodeSeparateXYZ')
        nt.link(tc.outputs['Object'], sep.inputs[0])
        x, y = sep.outputs['X'], sep.outputs['Y']
        ay = nt.math('ABSOLUTE', y)
        d = nt.math('SUBTRACT', xs, x)  # distance astern of the transom
        dpos = nt.math('MAXIMUM', d, 0.0)
        strength = nt.val(v.get('strength', 1.0), f'wake_strength_{name}')
        w0 = nt.val(v.get('w0', beam * 0.5), f'wake_w0_{name}')
        side_k = nt.val(v.get('side', 1.0), f'wake_side_{name}')
        w = nt.math('ADD', w0, nt.math('MULTIPLY', dpos, 0.10))
        core = nt.math('MULTIPLY', nt.sstep(nt.math('DIVIDE', ay, w), 1.0, 0.35),
                       nt.math('MULTIPLY', nt.sstep(d, -0.3, 1.5), nt.sstep(d, length, length * 0.35)))
        core = nt.math('MULTIPLY', core, nt.math('ADD', 0.35, nt.math('MULTIPLY', nz1, 0.65)))
        # churned water hugging the hull (bow wave / spray zone)
        side = nt.math('MULTIPLY', nt.sstep(ay, beam * 0.5 + 1.0, beam * 0.5 - 0.1),
                       nt.math('MULTIPLY', nt.sstep(x, xs - 1.0, xs + 1.0), nt.sstep(x, xb + 0.8, xb - 1.5)))
        side = nt.math('MULTIPLY', nt.math('MULTIPLY', side, side_k), nt.math('ADD', 0.45, nt.math('MULTIPLY', nz2, 0.55)))
        # diverging (Kelvin) arms
        q = nt.math('DIVIDE', nt.math('SUBTRACT', ay, nt.math('ADD', nt.math('MULTIPLY', dpos, 0.34), beam * 0.5)),
                    nt.math('ADD', 0.35, nt.math('MULTIPLY', dpos, 0.035)))
        kel = nt.math('EXPONENT', nt.math('MULTIPLY', nt.math('MULTIPLY', q, q), -1.0))
        kel = nt.math('MULTIPLY', nt.math('MULTIPLY', kel, nt.math('MULTIPLY', nt.sstep(d, 0.0, 3.0), nt.sstep(d, length * 0.6, 4.0))),
                      nt.math('MULTIPLY', nz2, nt.math('MULTIPLY', side_k, 0.55)))
        wake = nt.math('MULTIPLY', nt.math('ADD', nt.math('ADD', core, side), kel), strength)
        total = wake if total is None else nt.math('MAXIMUM', total, wake)
    if total is None:
        total = nt.val(0.0)
    if foam_attr:
        at = nt.node('ShaderNodeAttribute')
        at.attribute_name = 'foam'
        caps = nt.math('MULTIPLY', nt.sstep(at.outputs['Fac'], 0.25, 0.9), 0.12 if IR else 0.55)
        total = nt.math('MAXIMUM', total, caps)
    foam = nt.math('MINIMUM', total, 1.0)

    if IR:
        lw = nt.node('ShaderNodeLayerWeight')
        lw.inputs['Blend'].default_value = 0.5
        base = nt.math('ADD', 0.012, nt.math('MULTIPLY', nt.math('SUBTRACT', 1.0, lw.outputs['Facing']), 0.05))
        level = nt.math('ADD', base, nt.math('MULTIPLY', foam, 0.85))
        em = nt.node('ShaderNodeEmission')
        nt.link(level, em.inputs['Strength'])
        nt.link(em.outputs[0], out.inputs['Surface'])
    else:
        wb = nt.node('ShaderNodeBsdfPrincipled')
        wb.inputs['Base Color'].default_value = (0.004, 0.012, 0.028, 1)
        wb.inputs['Roughness'].default_value = 0.10 if far else 0.07
        wb.inputs['IOR'].default_value = 1.33
        # micro ripples so the moon glitter sparkles
        bn = nt.node('ShaderNodeTexNoise')
        bn.inputs['Scale'].default_value = 0.35 if far else 3.2
        bn.inputs['Detail'].default_value = 1.0
        nt.link(pos, bn.inputs['Vector'])
        bump = nt.node('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.22
        bump.inputs['Distance'].default_value = 0.12
        nt.link(bn.outputs['Fac'], bump.inputs['Height'])
        if not far:
            nt.link(bump.outputs['Normal'], wb.inputs['Normal'])
        fb = nt.node('ShaderNodeBsdfPrincipled')
        fb.inputs['Base Color'].default_value = (0.62, 0.70, 0.80, 1)
        fb.inputs['Roughness'].default_value = 0.65
        mix = nt.node('ShaderNodeMixShader')
        nt.link(foam, mix.inputs['Fac'])
        nt.link(wb.outputs[0], mix.inputs[1])
        nt.link(fb.outputs[0], mix.inputs[2])
        if far:
            fe = nt.node('ShaderNodeEmission')
            fe.inputs['Color'].default_value = (*[c * FAR_SEA for c in HAZE_COLOR], 1)
            gl = nt.node('ShaderNodeBsdfGlossy')
            gl.inputs['Roughness'].default_value = 0.2
            mix = nt.node('ShaderNodeMixShader')
            mix.inputs['Fac'].default_value = 0.12
            nt.link(fe.outputs[0], mix.inputs[1])
            nt.link(gl.outputs[0], mix.inputs[2])
        if far:
            nt.link(mix.outputs[0], out.inputs['Surface'])
            return m
        # sea haze: far water fades toward the horizon colour (hides where the simulated sea ends)
        cd = nt.node('ShaderNodeCameraData')
        hz = nt.node('ShaderNodeEmission')
        hz.inputs['Color'].default_value = (*[c * FAR_SEA for c in HAZE_COLOR], 1)
        hz.inputs['Strength'].default_value = 1.0
        hmix = nt.node('ShaderNodeMixShader')
        nt.link(nt.math('MULTIPLY', nt.sstep(cd.outputs['View Distance'], 45.0, 135.0), 0.88), hmix.inputs['Fac'])
        nt.link(mix.outputs[0], hmix.inputs[1])
        nt.link(hz.outputs[0], hmix.inputs[2])
        nt.link(hmix.outputs[0], out.inputs['Surface'])
    return m


def spray_material():
    m, nt, out = new_mat('spray' + ('_ir' if IR else ''))
    if IR:
        em = nt.node('ShaderNodeEmission')
        em.inputs['Strength'].default_value = 0.7
        nt.link(em.outputs[0], out.inputs['Surface'])
    else:
        b = nt.node('ShaderNodeBsdfPrincipled')
        b.inputs['Base Color'].default_value = (0.8, 0.86, 0.95, 1)
        b.inputs['Roughness'].default_value = 0.4
        b.inputs['Emission Color'].default_value = (0.62, 0.74, 0.95, 1)
        b.inputs['Emission Strength'].default_value = SPRAY_GLOW
        nt.link(b.outputs[0], out.inputs['Surface'])
    return m


# ----------------------------------------------------------------------------- world, light, ocean
def night_sky_image(w=4096, h=2048, n_stars=1700, seed=11):
    """Equirectangular night sky baked once: hazy horizon to near-black zenith, plus stars."""
    import numpy as np
    rng = np.random.default_rng(seed)
    el = (np.linspace(0, 1, h)[:, None] - 0.5) * math.pi  # -90..+90 deg, bottom row first
    up = np.clip(np.sin(el), 0, 1) ** 0.55
    k = np.clip(up / 0.45, 0, 1)[..., None]
    horizon, zenith = np.array([0.030, 0.050, 0.095]), np.array([0.0045, 0.008, 0.02])
    img = np.ones((h, w, 4), dtype=np.float32)
    img[..., :3] = (horizon * (1 - k) + zenith * k) * np.ones((1, w, 1))
    # stars only above the haze, a few bright ones and many faint
    z = rng.uniform(0.05, 1.0, n_stars)
    az = rng.uniform(0, 2 * math.pi, n_stars)
    ys = ((np.arcsin(z) / math.pi + 0.5) * (h - 1)).astype(int)
    xs = (az / (2 * math.pi) * (w - 1)).astype(int)
    mag = rng.pareto(2.2, n_stars) * 0.5 + 0.25
    fade = np.clip((z - 0.05) / 0.2, 0, 1)
    tint = np.stack([rng.uniform(0.85, 1.0, n_stars), rng.uniform(0.9, 1.0, n_stars), rng.uniform(0.95, 1.15, n_stars)], axis=1)
    for dy, dx, wgt in ((0, 0, 1.0), (0, 1, 0.16), (1, 0, 0.16), (0, -1, 0.16), (-1, 0, 0.16)):
        yy, xx = np.clip(ys + dy, 0, h - 1), (xs + dx) % w
        np.add.at(img, (yy, xx, slice(0, 3)), (mag * fade * wgt)[:, None] * tint * 1.1)
    im = bpy.data.images.new('night_sky', w, h, alpha=False, float_buffer=True)
    im.pixels.foreach_set(img.ravel())
    im.pack()
    return im


def setup_world(moon_az, moon_el, moon_strength=2.2, moon_disc=True, ambient=1.0, fill=None):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('night')
    sc.world = w
    w.use_nodes = True
    nt = NT(w.node_tree)
    nt.n.clear()
    out = nt.node('ShaderNodeOutputWorld')
    bg = nt.node('ShaderNodeBackground')
    if IR:
        bg.inputs['Color'].default_value = (0.012, 0.012, 0.012, 1)
        nt.link(bg.outputs[0], out.inputs['Surface'])
        return
    # Lighting and reflections use a constant night-sky colour (cheap to sample). The star field the camera
    # sees is a camera-only dome, so it costs nothing on bounce rays.
    bg.inputs['Color'].default_value = (0.017, 0.029, 0.056, 1)
    dm, dnt, dout = new_mat('sky_dome')
    dgeo = dnt.node('ShaderNodeNewGeometry')
    denv = dnt.node('ShaderNodeTexEnvironment')
    denv.image = night_sky_image()
    dnt.link(dgeo.outputs['Position'], denv.inputs['Vector'])
    dem = dnt.node('ShaderNodeEmission')
    dnt.link(denv.outputs['Color'], dem.inputs['Color'])
    dem.inputs['Strength'].default_value = ambient
    dnt.link(dem.outputs[0], dout.inputs['Surface'])
    dome = sphere('sky_dome', 20000.0, dm, seg=48)
    dome.visible_diffuse = dome.visible_glossy = dome.visible_transmission = dome.visible_shadow = False
    try:
        dome.visible_volume_scatter = False
    except Exception:
        pass
    bg.inputs['Strength'].default_value = ambient
    nt.link(bg.outputs[0], out.inputs['Surface'])

    # moon: a "sun" lamp for the key light, plus a visible disc
    d = Vector((math.cos(rad(moon_el)) * math.cos(rad(moon_az)), math.cos(rad(moon_el)) * math.sin(rad(moon_az)), math.sin(rad(moon_el))))
    ld = bpy.data.lights.new('moon_key', 'SUN')
    ld.energy = moon_strength
    ld.color = (0.70, 0.82, 1.0)
    ld.angle = rad(1.2)
    lo = bpy.data.objects.new('moon_key', ld)
    lo.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    link(lo)
    if fill:  # soft, shadowless skylight from the camera side so shapes read
        fd = Vector((math.cos(rad(fill[1])) * math.cos(rad(fill[0])), math.cos(rad(fill[1])) * math.sin(rad(fill[0])), math.sin(rad(fill[1]))))
        fl = bpy.data.lights.new('sky_fill', 'SUN')
        fl.energy = fill[2]
        fl.color = (0.55, 0.70, 1.0)
        fl.angle = rad(70)
        fl.use_shadow = False
        fo = bpy.data.objects.new('sky_fill', fl)
        fo.rotation_euler = (-fd).to_track_quat('-Z', 'Y').to_euler()
        link(fo)
    if moon_disc:
        mm, mnt, mout = new_mat('moon')
        em = mnt.node('ShaderNodeEmission')
        em.inputs['Color'].default_value = (0.85, 0.92, 1.0, 1)
        em.inputs['Strength'].default_value = 14.0
        mnt.link(em.outputs[0], mout.inputs['Surface'])
        disc = sphere('moon_disc', 5000 * math.tan(rad(0.75)), mm, seg=32, loc=tuple(d * 5000))
        disc.visible_shadow = False


OCEAN_CENTER = (0.0, 0.0)  # where the generated patch's centre sits relative to its object origin


def build_ocean(wave_scale=1.0, choppiness=1.0, wind=10.0, repeat=3, alignment=0.2, smallest=0.01, resolution=11,
                direction=0.0, seed=1, material=None, far_material=None):
    global OCEAN_CENTER
    rx, ry = repeat if isinstance(repeat, (tuple, list)) else (repeat, repeat)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    oc = mesh_obj('ocean', bm, material)
    md = oc.modifiers.new('Ocean', 'OCEAN')
    md.geometry_mode = 'GENERATE'
    md.resolution = md.viewport_resolution = resolution
    md.spatial_size = int(TILE)
    md.repeat_x, md.repeat_y = rx, ry
    md.wave_scale = wave_scale
    md.choppiness = choppiness
    md.wind_velocity = wind
    md.wave_alignment = alignment
    md.wave_direction = direction
    md.wave_scale_min = smallest
    md.random_seed = seed
    md.use_foam = True
    md.foam_coverage = 0.12
    md.foam_layer_name = 'foam'
    md.use_normals = True
    oc.cycles.use_deform_motion = False
    for f in (1, 400):
        md.time = (f - 1) / FPS
        md.keyframe_insert('time', frame=f)
    for fc in _fcurves(oc):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.extrapolation = 'LINEAR'
    # the generated patch is not centred on the object: measure it, so the follow logic and the far sea line up
    bpy.context.view_layer.update()
    ev = oc.evaluated_get(bpy.context.evaluated_depsgraph_get())
    xs = [c[0] for c in ev.bound_box]
    ys = [c[1] for c in ev.bound_box]
    OCEAN_CENTER = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    hx, hy = (max(xs) - min(xs)) / 2 - 3.0, (max(ys) - min(ys)) / 2 - 3.0
    cx, cy = OCEAN_CENTER
    # flat sea out to the horizon, with a hole where the simulated ocean sits
    R = 30000.0
    bm = bmesh.new()
    o = [bm.verts.new(p) for p in ((-R, -R, -0.05), (R, -R, -0.05), (R, R, -0.05), (-R, R, -0.05))]
    i = [bm.verts.new(p) for p in ((cx - hx, cy - hy, -0.05), (cx + hx, cy - hy, -0.05), (cx + hx, cy + hy, -0.05), (cx - hx, cy + hy, -0.05))]
    for k in range(4):
        bm.faces.new((o[k], o[(k + 1) % 4], i[(k + 1) % 4], i[k]))
    mesh_obj('ocean_far', bm, far_material or material, parent=oc)
    return oc


def _fcurves(idblock):
    """All F-curves of an ID, across Blender's old (action.fcurves) and layered-action APIs."""
    ad = idblock.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    out = []
    try:
        out = list(act.fcurves)
    except Exception:
        out = []
    if not out:
        try:
            for layer in act.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        out.extend(cb.fcurves)
        except Exception:
            pass
    return out


def ocean_follow(oc, path_xy, f0, f1):
    """Keep the simulated tile under the action by jumping whole tile periods (the surface is periodic,
    so the jump is invisible). Keys are CONSTANT and the shutter opens on the frame, so motion blur
    never sees the jump."""
    for f in range(f0, f1 + 1):
        x, y = path_xy((f - 1) / FPS)
        oc.location = (round(x / TILE) * TILE - OCEAN_CENTER[0], round(y / TILE) * TILE - OCEAN_CENTER[1], 0)
        oc.keyframe_insert('location', frame=f)
    for fc in _fcurves(oc):
        if fc.data_path == 'location':
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


def ocean_height(oc_eval, mw, mwi, x, y):
    o = mwi @ Vector((x, y, 40.0))
    hit, loc, _n, _i = oc_eval.ray_cast(o, Vector((0, 0, -1)))
    return (mw @ loc).z if hit else 0.0


# ----------------------------------------------------------------------------- models
def build_marlin(name='marlin'):
    """Marlin blockout from the client reference sheet: pod hull, big ducted fan at the stern, V tail on a
    pylon, short sensor mast on top of the duct, single raked hydrofoil strut. Defense grey, no lights.
    Local origin = hull-borne waterline amidships; +X is the bow. Overall length about 7.2 m (under 24 ft)."""
    root = empty(name)
    root.rotation_mode = 'ZYX'
    grey = M('marlin_grey', (0.26, 0.28, 0.30), rough=0.5, ir=0.5)
    dark = M('marlin_dark', (0.07, 0.075, 0.08), rough=0.55, ir=0.62)
    # pod hull: superellipsoid, slightly finer toward the nose
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rad(90), 3, 'Y'), verts=bm.verts)
    for v in bm.verts:
        x, y, z = v.co
        sx = math.copysign(abs(x) ** 0.62, x)
        sy = math.copysign(abs(y) ** 0.85, y)
        sz = math.copysign(abs(z) ** 0.80, z)
        taper = 1.0 - 0.22 * max(0.0, sx) ** 2.2
        v.co = (sx * 2.8, sy * 1.1 * taper, sz * 0.525 * (taper if sz > 0 else 1.0))
    mesh_obj(name + '_pod', bm, marlin_pod_material(), parent=root, loc=(0.4, 0, 0.175), smooth=True)
    # ducted fan
    RC = (-1.75, 0.0, 1.72)  # ring centre
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=1.12, radius2=1.12, depth=0.9)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rad(90), 3, 'Y'), verts=bm.verts)
    ring = mesh_obj(name + '_duct', bm, grey, parent=root, loc=RC, smooth=True, sharp=60, solidify=0.16, bevel=0.03)
    sphere(name + '_hub', 0.30, grey, scale=(1.9, 1.0, 1.0), parent=root, loc=(RC[0] + 0.05, 0, RC[2]))
    for k in range(3):  # stators holding the motor pod
        box(name + f'_stator{k}', (0.07, 0.12, 1.02), grey, parent=empty(name + f'_st{k}', root, (RC[0] - 0.22, 0, RC[2]), (rad(60 + 120 * k), 0, 0)),
            loc=(0, 0, 0.52))
    prop = empty(name + '_prop', root, (RC[0] + 0.12, 0, RC[2]))
    for k in range(3):
        piv = empty(name + f'_bladepiv{k}', prop, rot=(rad(120 * k), 0, 0))
        box(name + f'_blade{k}', (0.05, 0.36, 0.86), dark, parent=piv, loc=(0, 0, 0.60), rot=(0, 0, rad(28)), bevel=0.012)
    # tail: pylon + V fins
    box(name + '_pylon', (0.50, 0.46, 2.0), grey, parent=root, loc=(-2.92, 0, 0.92), bevel=0.05)
    box(name + '_boom', (0.75, 0.30, 0.34), grey, parent=root, loc=(-2.45, 0, 1.75), bevel=0.05)
    for s in (1, -1):
        plate(name + f'_vfin{s}', [(-2.25, 0, 1.92), (-3.30, 0, 1.92), (-3.85, s * 1.45, 2.42), (-3.38, s * 1.45, 2.42)], dark, 0.09, parent=root)
    # sensor mast on top of the duct (the bar turns)
    top = RC[2] + 1.2
    cyl(name + '_mast', 0.09, 0.42, grey, parent=root, loc=(RC[0], 0, top + 0.16))
    sensor = empty(name + '_sensor', root, (RC[0], 0, top + 0.42))
    box(name + '_sensorbar', (0.17, 1.36, 0.11), grey, parent=sensor, bevel=0.02)
    cyl(name + '_sensordome', 0.11, 0.16, grey, parent=sensor, loc=(0, 0, 0.13))
    cyl(name + '_antenna', 0.014, 0.75, dark, parent=root, loc=(RC[0] + 0.3, -0.3, top + 0.42))
    # single raked hydrofoil strut + lifting foil
    box(name + '_strut', (0.50, 0.085, 1.56), dark, parent=root, loc=(0.92, 0, -1.02), rot=(0, rad(19.5), 0), bevel=0.02)
    box(name + '_foil', (0.36, 1.55, 0.055), dark, parent=root, loc=(0.64, 0, -1.76), bevel=0.02)
    return dict(root=root, prop=prop, sensor=sensor, name=name, xs=-2.4, xb=3.2, beam=2.2, length=7.2)


FOIL_RIDE = 1.2  # how far the hull rises when foil-borne (hull bottom ~0.85 m clear of the water)


def build_man(name, parent, loc, yaw=0.0, lean=40.0, crouch=0.0):
    """Blocky figure, hunched forward (lean in degrees), dark clothing."""
    cloth = M('man_cloth', (0.022, 0.025, 0.032), rough=0.9, ir=0.92)
    skin = M('man_skin', (0.16, 0.11, 0.085), rough=0.7, ir=1.0)
    r = empty(name, parent, loc, (0, 0, rad(yaw)))
    hip = 0.86 - crouch
    box(name + '_legs', (0.30, 0.40, hip), cloth, parent=r, loc=(-0.05, 0, hip / 2), bevel=0.05)
    piv = empty(name + '_hip', r, (0, 0, hip), (0, rad(lean), 0))
    box(name + '_torso', (0.27, 0.50, 0.64), cloth, parent=piv, loc=(0, 0, 0.30), bevel=0.09)
    sphere(name + '_hood', 0.145, cloth, scale=(1.05, 1.0, 1.08), seg=16, parent=piv, loc=(0.035, 0, 0.74))
    sphere(name + '_face', 0.10, skin, seg=12, parent=piv, loc=(0.085, 0, 0.72))
    for s in (1, -1):
        box(name + f'_arm{s}', (0.11, 0.11, 0.58), cloth, parent=empty(name + f'_sh{s}', piv, (0.02, s * 0.29, 0.54), (0, rad(118), 0)),
            loc=(0, 0, 0.27), bevel=0.04)
    return r


def build_gofast(name='gofast'):
    """Low open go-fast: long narrow hull, low console, twin outboards, bales lashed down under straps,
    three men hunched behind the console. No lights, no markings. Local origin = waterline amidships, +X bow."""
    root = empty(name)
    root.rotation_mode = 'ZYX'
    hullm = M('gf_hull', (0.045, 0.06, 0.085), rough=0.45, ir=0.5)
    deckm = M('gf_deck', (0.06, 0.065, 0.07), rough=0.8, ir=0.42)
    engm = M('gf_engine', (0.03, 0.03, 0.035), rough=0.35, ir=1.0)
    balem = M('gf_bale', (0.34, 0.32, 0.27), rough=0.9, ir=0.72)
    strapm = M('gf_strap', (0.02, 0.02, 0.02), rough=0.8, ir=0.3)
    drumm = M('gf_drum', (0.03, 0.06, 0.10), rough=0.5, ir=0.55)
    DECK = 0.16
    # (x, half-beam, sheer z, keel z)
    stations = [(-6.0, 1.15, 0.62, -0.42), (-4.0, 1.28, 0.62, -0.46), (-2.0, 1.32, 0.64, -0.48), (0.0, 1.30, 0.68, -0.48),
                (2.0, 1.18, 0.74, -0.44), (4.0, 0.86, 0.84, -0.30), (5.2, 0.46, 0.93, -0.02), (6.0, 0.05, 1.02, 0.78)]
    bm = bmesh.new()
    rings = []
    for x, b, zs, zk in stations:
        zc = zk + (zs - zk) * 0.38
        zd = DECK if x < 4.4 else zs - 0.04  # short closed foredeck
        half = [(0.0, zk), (0.80 * b, zc), (b, zs), (b - 0.12, zs), (max(b - 0.16, 0.0), zd), (0.0, zd)]
        loop = [bm.verts.new((x, y, z)) for y, z in half] + [bm.verts.new((x, -y, z)) for y, z in reversed(half[1:-1])]
        rings.append(loop)
    for a, b_ in zip(rings, rings[1:]):
        n = len(a)
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b_[(i + 1) % n], b_[i]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    mesh_obj(name + '_hull', bm, hullm, parent=root)
    box(name + '_deck', (10.2, 2.1, 0.02), deckm, parent=root, loc=(-0.9, 0, DECK + 0.005))
    # low console, no T-top
    box(name + '_console', (0.85, 0.86, 0.92), deckm, parent=root, loc=(-2.75, 0, DECK + 0.46), bevel=0.05)
    box(name + '_screen', (0.05, 0.80, 0.30), M('gf_screen', (0.02, 0.03, 0.04), rough=0.15, ir=0.35), parent=root,
        loc=(-2.40, 0, DECK + 1.04), rot=(0, rad(-22), 0))
    # twin outboards
    for s in (1, -1):
        box(name + f'_cowl{s}', (0.82, 0.50, 0.62), engm, parent=root, loc=(-6.45, s * 0.52, 0.98), bevel=0.09)
        box(name + f'_leg{s}', (0.30, 0.20, 1.15), engm, parent=root, loc=(-6.50, s * 0.52, 0.18), bevel=0.03)
    # bales, two layers, lashed down
    import random
    rnd = random.Random(7)
    xs = [3.75 - 0.76 * i for i in range(8)]
    for i, x in enumerate(xs):
        cols = (0.0,) if x > 3.0 else (-0.43, 0.43)
        for y in cols:
            for layer in range(2):
                if layer == 1 and x > 3.4:
                    continue
                box(name + f'_bale{i}{int(y * 10)}{layer}', (0.70, 0.80, 0.40), balem, parent=root,
                    loc=(x + rnd.uniform(-0.03, 0.03), y + rnd.uniform(-0.02, 0.02), DECK + 0.21 + 0.41 * layer),
                    rot=(rad(rnd.uniform(-2, 2)), rad(rnd.uniform(-2, 2)), rad(rnd.uniform(-4, 4))), bevel=0.07)
    for x in (-5.25,):
        for y in (-0.78, 0.78):
            box(name + f'_abale{int(x * 10)}{int(y * 10)}', (0.70, 0.56, 0.40), balem, parent=root, loc=(x, y, DECK + 0.21), bevel=0.07)
    top = DECK + 0.83
    for x in (2.6, 1.1, -0.4):  # transverse straps over the stack and down to the gunwales
        box(name + f'_strapT{int(x * 10)}', (0.07, 1.74, 0.025), strapm, parent=root, loc=(x, 0, top + 0.02))
        for s in (1, -1):
            box(name + f'_strapS{int(x * 10)}{s}', (0.07, 0.025, 0.46), strapm, parent=root, loc=(x, s * 0.87, top - 0.2))
    for y in (-0.43, 0.43):
        box(name + f'_strapL{int(y * 10)}', (4.9, 0.06, 0.025), strapm, parent=root, loc=(0.95, y, top + 0.035))
    for y in (-0.5, 0.5):  # fuel drums against the transom
        cyl(name + f'_drum{int(y * 10)}', 0.28, 0.85, drumm, parent=root, loc=(-5.55, y * 0.2, DECK + 0.43 + 0.0))
    # three men hunched behind the console
    men = empty(name + '_men', root)
    build_man(name + '_helm', men, (-3.38, 0.05, DECK), yaw=0, lean=36)
    build_man(name + '_crew1', men, (-4.55, 0.42, DECK), yaw=-6, lean=50, crouch=0.20)
    build_man(name + '_crew2', men, (-3.98, -0.60, DECK), yaw=8, lean=46, crouch=0.26)
    return dict(root=root, name=name, xs=-6.0, xb=6.0, beam=2.6, length=12.0)


# ----------------------------------------------------------------------------- spray
def sheet_material(name, strength=1.0):
    """Soft sheet of spray: a noisy, see-through silver veil. The noise lives in world space, so as the vessel
    moves the pattern streams aft through the sheet. Animatable: sheet_strength_<name>."""
    m, nt, out = new_mat('sheet_' + name + ('_ir' if IR else ''))
    uv = nt.node('ShaderNodeUVMap')
    sep = nt.node('ShaderNodeSeparateXYZ')
    nt.link(uv.outputs['UV'], sep.inputs[0])
    u, v = sep.outputs['X'], sep.outputs['Y']
    geo = nt.node('ShaderNodeNewGeometry')
    # streaks: noise stretched along the direction of travel (+X)
    mp = nt.node('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (0.45, 4.2, 4.2)
    nt.link(geo.outputs['Position'], mp.inputs['Vector'])
    n1 = nt.node('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 1.0
    n1.inputs['Detail'].default_value = 2.0
    n1.inputs['Roughness'].default_value = 0.6
    nt.link(mp.outputs['Vector'], n1.inputs['Vector'])
    body = nt.sstep(n1.outputs['Fac'], 0.44, 0.60)
    # dense at the root where the hull throws it, thinning toward the outer edge and aft
    fade_v = nt.math('MULTIPLY', nt.sstep(v, 1.0, 0.25), nt.sstep(v, 0.0, 0.08))
    fade_u = nt.math('MULTIPLY', nt.sstep(u, 0.0, 0.07), nt.sstep(u, 1.0, 0.30))
    st = nt.val(strength, f'sheet_strength_{name}')
    alpha = nt.math('MULTIPLY', nt.math('MULTIPLY', nt.math('MULTIPLY', fade_u, fade_v), nt.math('ADD', 0.02, nt.math('MULTIPLY', body, 0.98))), st)
    alpha = nt.math('MINIMUM', nt.math('MULTIPLY', alpha, 0.72), 0.7)  # a veil: the hull still reads through it
    em = nt.node('ShaderNodeEmission')
    em.inputs['Color'].default_value = (1, 1, 1, 1) if IR else (0.66, 0.78, 0.98, 1)
    em.inputs['Strength'].default_value = 0.75 if IR else SHEET_GLOW
    tr = nt.node('ShaderNodeBsdfTransparent')
    mix = nt.node('ShaderNodeMixShader')
    nt.link(alpha, mix.inputs['Fac'])
    nt.link(tr.outputs[0], mix.inputs[1])
    nt.link(em.outputs[0], mix.inputs[2])
    nt.link(mix.outputs[0], out.inputs['Surface'])
    return m


def spray_sheet(name, parent, side, x0, length, height, spread, y0, mat, z0=0.0, nu=22, nv=7):
    """Curved sheet thrown outward and aft from the hull side at the waterline (one side). Parented to the vessel."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    grid = []
    for i in range(nu + 1):
        u = i / nu
        hump = math.sin(math.pi * min(1.0, u ** 0.55)) * (1 - 0.35 * u)
        row = []
        for j in range(nv + 1):
            v = j / nv
            x = x0 - u * length - 0.5 * v * u * length * 0.25
            y = side * (y0 + (0.12 + spread * (0.35 + 0.65 * u ** 0.8)) * v)
            z = z0 + height * hump * (v ** 0.75) * (1.0 - 0.38 * v)
            row.append((bm.verts.new((x, y, z)), (u, v)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            quad = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
            f = bm.faces.new([q[0] for q in quad])
            for loop, q in zip(f.loops, quad):
                loop[uvl].uv = q[1]
    ob = mesh_obj(name, bm, mat, parent=parent, smooth=True)
    ob.visible_shadow = False
    return ob


def rooster_tail(name, parent, x0, length, height, width, mat):
    """Plume kicked up astern (outboards, or a strut cutting the surface): an arched sheet on the centreline."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    nu, nv = 18, 8
    grid = []
    for i in range(nu + 1):
        u = i / nu
        row = []
        for j in range(nv + 1):
            v = j / nv
            w = (v - 0.5) * 2
            x = x0 - u * length
            y = w * width * (0.25 + 0.75 * u ** 0.7)
            z = height * math.sin(math.pi * min(1.0, u ** 0.6 * 1.05)) * (1 - 0.55 * w * w)
            # uv.v runs 0 (edge) .. 0.5 (crest) so the shared sheet material fades both edges
            row.append((bm.verts.new((x, y, z)), (u, 0.12 + 0.5 * abs(w))))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            quad = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
            f = bm.faces.new([q[0] for q in quad])
            for loop, q in zip(f.loops, quad):
                loop[uvl].uv = q[1]
    ob = mesh_obj(name, bm, mat, parent=parent, smooth=True)
    ob.visible_shadow = False
    return ob


# ----------------------------------------------------------------------------- spray (particles)
_drop = None


def spray_emitter(name, frames, count, life, vel_normal, inherit, size=0.045, rand=1.2, drag=0.02, quad=(0.6, 0.3)):
    """A small invisible quad that throws spray. Position/orientation are keyed per frame by the shot."""
    global _drop
    if _drop is None:
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        _drop = mesh_obj('drop', bm, spray_material(), smooth=True)
        _drop.location = (0, 0, -500)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bmesh.ops.scale(bm, vec=Vector((quad[0], quad[1], 1.0)), verts=bm.verts)
    em = mesh_obj(name, bm, None)
    em.rotation_mode = 'ZYX'
    return dict(ob=em, frames=frames, count=count, life=life, vel=vel_normal, inherit=inherit, size=size, rand=rand, drag=drag)


def activate_emitter(e):
    em = e['ob']
    md = em.modifiers.new('spray', 'PARTICLE_SYSTEM')
    ps = em.particle_systems[-1].settings
    ps.count = int(e['count'] * SPRAY_COUNT)
    ps.frame_start, ps.frame_end = e['frames']
    ps.lifetime = e['life'] * FPS
    ps.lifetime_random = 0.55
    ps.emit_from = 'FACE'
    ps.normal_factor = e['vel']
    ps.factor_random = e['rand']
    ps.object_factor = e['inherit']
    ps.physics_type = 'NEWTON'
    ps.drag_factor = e['drag']
    ps.render_type = 'OBJECT'
    ps.instance_object = _drop
    ps.particle_size = e['size'] * SPRAY_SCALE
    ps.size_random = 0.7
    em.show_instancer_for_render = False
    em.show_instancer_for_viewport = False


# ----------------------------------------------------------------------------- shots
class Shot:
    """A shot = vessels with state functions, a camera function, an ocean and a moon."""
    duration = 4.0
    ocean = dict()
    moon = dict(az=80.0, el=14.0)
    exposure = 0.0
    lens_clip = (0.2, 60000.0)

    def build(self):
        raise NotImplementedError


def keyed(ob, frame, loc=None, rot=None):
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert('location', frame=frame)
    if rot is not None:
        ob.rotation_euler = rot
        ob.keyframe_insert('rotation_euler', frame=frame)


def look_rotation(cam_pos, target, roll=0.0):
    d = Vector(target) - Vector(cam_pos)
    q = d.to_track_quat('-Z', 'Y')
    e = q.to_euler('XYZ')
    m = q.to_matrix().to_4x4() @ Matrix.Rotation(roll, 4, 'Z')
    return m.to_euler('XYZ')


def run_shot(shot, args):
    global IR
    IR = bool(args.ir or getattr(shot, 'force_ir', False))
    sc = reset_scene()
    n_frames = int(round(shot.duration * FPS))
    f0, f1 = 1, n_frames
    sc.frame_start, sc.frame_end = f0, f1
    scene = shot.build()  # dict(vessels=[...], emitters=[...], camera=fn, tracks={name: fn})
    vessels = scene['vessels']
    global HAZE_COLOR
    amb = shot.moon.get('ambient', 1.0)
    HAZE_COLOR = tuple(c * amb for c in (0.030, 0.050, 0.095))
    setup_world(shot.moon['az'], shot.moon['el'], moon_strength=shot.moon.get('strength', 2.2), moon_disc=shot.moon.get('disc', True),
                ambient=amb, fill=shot.moon.get('fill'))
    wm = water_material([] if os.environ.get('PV_SIMPLEWATER') else [dict(name=v['name'], root=v['root'], xs=v['xs'], xb=v['xb'], beam=v['beam'], **v.get('wake', {})) for v in vessels],
                        foam_attr=not os.environ.get('PV_SIMPLEWATER'))
    oc = build_ocean(material=wm, far_material=water_material([], foam_attr=False, far=True), **shot.ocean)
    ocean_follow(oc, scene['focus'], f0, f1)
    if 'ocean_anim' in scene:
        md = oc.modifiers['Ocean']
        for f in range(f0, f1 + 1):
            for k, fn in scene['ocean_anim'].items():
                setattr(md, k, fn((f - 1) / FPS))
                md.keyframe_insert(k, frame=f)
    cam_data = bpy.data.cameras.new('cam')
    cam = bpy.data.objects.new('cam', cam_data)
    link(cam)
    sc.camera = cam
    cam_data.sensor_width = 36.0
    cam_data.clip_start, cam_data.clip_end = shot.lens_clip

    # ---- bake vessel and camera motion (rides the simulated sea where a vessel is hull-borne)
    state = {v['name']: {} for v in vessels}
    lp = {v['name']: None for v in vessels}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        t = (f - 1) / FPS
        dg = bpy.context.evaluated_depsgraph_get()
        oce = oc.evaluated_get(dg)
        mw = oce.matrix_world.copy()
        mwi = mw.inverted()
        h = lambda x, y: ocean_height(oce, mw, mwi, x, y)
        for v in vessels:
            s = v['state'](t)  # x, y, heading(rad), foil(0..1), pitch, roll (rad), dz
            hd = s.get('heading', 0.0)
            c, sn = math.cos(hd), math.sin(hd)
            L = v['length']
            hb, hs, hc = h(s['x'] + c * L * 0.35, s['y'] + sn * L * 0.35), h(s['x'] - c * L * 0.35, s['y'] - sn * L * 0.35), h(s['x'], s['y'])
            follow = s.get('follow', 1.0)  # how much the hull rides the waves
            zt = (hc * 0.5 + (hb + hs) * 0.25) * follow
            pt = clamp(math.atan2(hb - hs, L * 0.7) * follow * s.get('pitch_follow', 0.4), -rad(4.5), rad(4.5))
            a = 0.35
            lp[v['name']] = (zt, pt) if lp[v['name']] is None else (lerp(lp[v['name']][0], zt, a), lerp(lp[v['name']][1], pt, a))
            zs_, ps_ = lp[v['name']]
            k = s.get('foil', 0.0)
            z = lerp(zs_, FOIL_RIDE, k) + s.get('dz', 0.0)
            pitch = lerp(ps_, 0.0, k) + s.get('pitch', 0.0)
            keyed(v['root'], f, (s['x'], s['y'], z), (s.get('roll', 0.0), -pitch, hd))
            state[v['name']][f] = dict(x=s['x'], y=s['y'], z=z, heading=hd, foil=k, sea=hc)
            if v.get('prop') is not None:
                keyed(v['prop'], f, rot=(s.get('prop_angle', t * 70.0), 0, 0))
            if v.get('sensor') is not None:
                keyed(v['sensor'], f, rot=(0, 0, t * 2 * math.pi * 0.45))
        for e in scene.get('emitters', []):
            loc, rot = e['place'](t, state, f)
            loc = (loc[0], loc[1], h(loc[0], loc[1]) + loc[2]) if e.get('on_sea', True) else loc
            keyed(e['ob'], f, loc, rot)
        cpos, ctgt, lens, roll = scene['camera'](t, state, f)
        floor = h(cpos[0], cpos[1]) + scene.get('cam_clearance', 0.35)
        cpos = (cpos[0], cpos[1], max(cpos[2], floor))
        keyed(cam, f, cpos, look_rotation(cpos, ctgt, roll))
        cam_data.lens = lens
        cam_data.keyframe_insert('lens', frame=f)
        for name, fn in scene.get('wake_anim', {}).items():
            for mat in bpy.data.materials:
                node = mat.node_tree.nodes.get(name) if mat.node_tree else None
                if node is not None:
                    node.outputs[0].default_value = fn(t)
                    node.outputs[0].keyframe_insert('default_value', frame=f)
    for ob in [v['root'] for v in vessels] + [cam] + [e['ob'] for e in scene.get('emitters', [])]:
        for fc in _fcurves(ob):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    if not os.environ.get('PV_NOPART'):
        for e in scene.get('emitters', []):
            activate_emitter(e)

    # ---- render settings
    W, H = (int(x) for x in args.res.split('x'))
    r = sc.render
    r.engine = 'CYCLES'
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.use_motion_blur = not IR and not os.environ.get('PV_NOMB')
    r.motion_blur_shutter = 0.5
    try:
        r.motion_blur_position = 'START'
    except Exception:
        sc.cycles.motion_blur_position = 'START'
    r.use_persistent_data = True
    c = sc.cycles
    c.samples = 4 if IR else args.samples
    c.use_adaptive_sampling = False
    c.use_denoising = not IR and not os.environ.get('PV_NODENOISE')
    try:
        c.denoiser = 'OPENIMAGEDENOISE'
        c.denoising_quality = 'HIGH' if args.hq_denoise else 'FAST'
        c.denoising_prefilter = 'FAST'
    except Exception as ex:
        print('denoise settings:', ex)
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = (int(x) for x in os.environ.get('PV_BOUNCES', '3,1,2,1,4').split(','))
    c.caustics_reflective = c.caustics_refractive = False
    c.sample_clamp_indirect = 4.0
    c.sample_clamp_direct = 0.0
    vs = sc.view_settings
    vs.view_transform = 'Standard' if IR else 'AgX'
    if not IR:
        for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'AgX - Punchy'):
            try:
                vs.look = look
                break
            except Exception:
                continue
    vs.exposure = 0.0 if IR else shot.exposure
    try:
        r.image_settings.media_type = 'IMAGE'
    except Exception:
        pass
    r.image_settings.file_format = 'JPEG'
    r.image_settings.quality = 95

    tag = f"shot{shot.id}{'_ir' if IR and not getattr(shot, 'force_ir', False) else ''}"
    outdir = os.path.join(args.out, tag)
    os.makedirs(outdir, exist_ok=True)
    if args.save_blend:
        os.makedirs(args.save_blend, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(args.save_blend, tag + '.blend')), compress=True)

    if args.still is not None:
        targets = [int(round(args.still * FPS)) + 1]
    else:
        a, b = (int(x) for x in args.frames.split('-')) if args.frames else (f0, f1)
        targets = list(range(max(a, f0), min(b, f1) + 1))
    first = getattr(shot, 'first_frame', f0) if not IR else f0
    targets = [f for f in targets if f >= first]
    tracks = {}
    t_start = time.time()
    done = 0
    for f in range(f0, max(targets) + 1):
        sc.frame_set(f)  # particles simulate frame by frame
        if f not in targets:
            continue
        if 'tracks' in scene:
            tr = {}
            for name, fn in scene['tracks'].items():
                p = world_to_camera_view(sc, cam, Vector(fn((f - 1) / FPS, state, f)))
                tr[name] = [round(p.x, 5), round(1 - p.y, 5), round(p.z, 2)]
            tracks[f] = tr
        path = os.path.join(outdir, f'{f:04d}.jpg') if args.still is None else os.path.join(outdir, f'still_{args.still:.2f}.jpg')
        if args.still is None and os.path.exists(path) and not args.force:
            continue
        r.filepath = path
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        done += 1
        print(f'RENDER {tag} frame {f}/{f1} {time.time() - t1:.1f}s (avg {(time.time() - t_start) / done:.1f}s)', flush=True)
    if tracks and args.still is None:
        json.dump(dict(fps=FPS, first=first, frames=n_frames, tracks=tracks), open(os.path.join(outdir, 'tracks.json'), 'w'))
    print('DONE', tag, 'frames', len(targets), 'in', round(time.time() - t_start), 's', flush=True)


# ---- helpers shared by shots
def gofast_state(v=30 * KT, y=0.0, x0=0.0, seed=1.0):
    """Planing flat out in chop: bow slamming, a little roll, mostly riding over the waves."""
    def f(t):
        pitch = rad(2.4) + rad(2.0) * math.sin(2 * math.pi * 1.15 * t + seed) + rad(0.8) * wobble(t, seed + 3, (2.3, 3.7, 5.1))
        return dict(x=x0 + v * t, y=y, heading=0.0, follow=0.45, dz=0.14 + 0.05 * math.sin(2 * math.pi * 1.15 * t + seed + 1.2),
                    pitch=pitch, roll=rad(1.6) * wobble(t, seed + 9, (0.6, 1.1, 1.9)))
    return f


def gofast_sheets(gf):
    """Spray sheeting off the bow on both sides plus the outboards' rooster tail (meshes riding with the boat)."""
    mat = sheet_material(gf['name'])
    for s in (1, -1):
        spray_sheet(f"{gf['name']}_sheet{s}", gf['root'], -s, x0=3.9, length=6.4, height=1.25, spread=2.3, y0=0.92, mat=mat, z0=-0.1)
    rooster_tail(f"{gf['name']}_rooster_sheet", gf['root'], x0=-6.5, length=7.5, height=1.25, width=1.5, mat=mat)
    return mat


def gofast_spray(gname='gofast', frames=(1, 400), density=1.0):
    """Fine droplets flying off the bow sheets and the rooster tail."""
    ems = []
    for s in (1, -1):
        e = spray_emitter(f'{gname}_bowspray{s}', frames, int(2600 * density), life=0.42, vel_normal=4.2, inherit=0.86, size=0.05, rand=1.3, quad=(2.4, 0.4))

        def place(t, state, f, s=s):
            st = state[gname][f]
            return (st['x'] + 2.4, st['y'] - s * 1.25, 0.35), (rad(s * 50), rad(-14), 0)
        e['place'] = place
        ems.append(e)
    e = spray_emitter(f'{gname}_rooster', frames, int(1800 * density), life=0.5, vel_normal=4.5, inherit=0.82, size=0.055, rand=1.4, quad=(0.7, 1.5))
    e['place'] = lambda t, state, f: ((state[gname][f]['x'] - 6.9, state[gname][f]['y'], 0.25), (0, rad(-38), 0))
    ems.append(e)
    return ems


def shake(t, seed, amp_deg=0.25):
    return (rad(amp_deg) * wobble(t, seed, (1.1, 2.7, 5.3)), rad(amp_deg) * wobble(t, seed + 5, (0.9, 3.1, 6.1)))


def jitter(target, t, seed, amp):
    return (target[0] + amp * wobble(t, seed, (1.3, 2.9, 4.7)), target[1] + amp * wobble(t, seed + 2, (1.7, 3.3, 5.9)),
            target[2] + amp * 0.6 * wobble(t, seed + 4, (1.1, 2.3, 6.3)))


class Shot01(Shot):
    """01 · The boat (0:00-0:04). Night, open sea. A low go-fast runs flat out with no lights, spray sheeting
    off the bow, bales lashed down, men hunched behind the console. Tight and moving with it."""
    id = '01'
    duration = 4.0
    ocean = dict(wave_scale=0.85, choppiness=1.15, wind=9.0, repeat=3)
    moon = dict(az=114.0, el=15.0, strength=4.2, disc=False, ambient=1.25, fill=(-70.0, 40.0, 0.55))
    exposure = 1.35

    def build(self):
        gf = build_gofast()
        gofast_sheets(gf)
        gf['state'] = gofast_state()
        gf['wake'] = dict(strength=1.0, w0=1.25, side=1.0, wake_len=110.0)
        V = 30 * KT

        def camera(t, state, f):
            k = smooth(t / self.duration)
            gx = state['gofast'][f]['x']
            # starts off the bow in the spray, the boat gains on us and we end tight on the men at the console
            rel = vlerp((8.2, -7.4, 1.35), (-1.0, -8.4, 1.95), k)
            tgt = vlerp((2.4, 0.0, 0.75), (-2.5, 0.0, 0.95), smooth(ramp(t, 0.4, 3.6)))
            pos = (gx + rel[0] + 0.05 * wobble(t, 1), rel[1] + 0.05 * wobble(t, 2), rel[2] + 0.06 * wobble(t, 3, (1.4, 2.2, 3.9)))
            return pos, jitter((gx + tgt[0], tgt[1], tgt[2]), t, 11, 0.07), lerp(36.0, 46.0, k), rad(1.2) * wobble(t, 21, (0.5, 1.2, 2.2))
        return dict(vessels=[gf], emitters=gofast_spray(), camera=camera, focus=lambda t: (V * t, 0.0), cam_clearance=0.38,
                    tracks=dict(toi=lambda t, st, f: (st['gofast'][f]['x'], 0, 0.9)))


class Shot03(Shot):
    """03 · Infrared ID (0:07-0:10). The aircraft's infrared camera slews onto the contact: a white-hot go-fast,
    twin wakes, bales on deck. Positive ID. (Rendered as a thermal pass; the sensor overlay is added in the edit.)"""
    id = '03'
    duration = 3.0
    force_ir = True
    ocean = dict(wave_scale=0.85, choppiness=1.15, wind=9.0, repeat=3)
    moon = dict(az=62.0, el=15.0)

    def build(self):
        gf = build_gofast()
        gofast_sheets(gf)
        gf['state'] = gofast_state()
        gf['wake'] = dict(strength=1.0, w0=1.25, side=1.0, wake_len=160.0)
        V = 30 * KT

        def camera(t, state, f):
            gx = state['gofast'][f]['x']
            # patrol aircraft on the boat's beam, 900 m slant range, looking 38 degrees down, slowly orbiting
            az = rad(-98 + 4.0 * t)
            rng, el = 900.0, rad(38)
            pos = (gx + rng * math.cos(el) * math.cos(az), rng * math.cos(el) * math.sin(az), rng * math.sin(el))
            # the slew: starts off the contact, swings on with a small overshoot, then holds
            k = 1 - math.exp(-t * 5.2) * (math.cos(t * 7.0) + 0.35 * math.sin(t * 7.0))
            off = (lerp(-34.0, 0.0, k), lerp(17.0, 0.0, k))
            tgt = (gx + off[0] + 0.25 * wobble(t, 4, (2.1, 3.3, 5.2)), off[1] + 0.25 * wobble(t, 6, (1.8, 2.9, 4.6)), 0.6)
            return pos, tgt, 1050.0, 0.0
        return dict(vessels=[gf], emitters=gofast_spray(density=0.8), camera=camera, focus=lambda t: (V * t, 0.0), cam_clearance=0.4,
                    tracks=dict(toi=lambda t, st, f: (st['gofast'][f]['x'], 0, 0.9)))


class Shot06(Shot):
    """06 · Loiter (0:20-0:23). Open ocean, night, long swell. A defense-gray Marlin sits hull-borne, alone,
    sensor mast turning. It has been out here for days."""
    id = '06'
    duration = 3.0
    ocean = dict(wave_scale=0.85, choppiness=0.6, wind=13.0, repeat=3, alignment=0.7, smallest=0.9, seed=3)
    moon = dict(az=97.0, el=11.5, strength=2.4, disc=True, ambient=1.1)
    exposure = 0.8

    def build(self):
        m = build_marlin()
        m['state'] = lambda t: dict(x=0.25 * t, y=0.0, heading=0.0, follow=1.0, foil=0.0, roll=rad(1.5) * wobble(t, 2, (0.21, 0.37, 0.6)),
                                    prop_angle=t * 1.2)
        m['wake'] = dict(strength=0.0, w0=1.0, side=0.0)

        def camera(t, state, f):
            k = t / self.duration
            pos = vlerp((4.6, -17.0, 1.35), (3.8, -14.2, 1.3), k)
            pos = (pos[0], pos[1], pos[2] + 0.10 * wobble(t, 5, (0.2, 0.33, 0.5)))
            return pos, (-1.9, 0.0, 2.1 + 0.05 * wobble(t, 8, (0.2, 0.3, 0.45))), 35.0, rad(0.5) * wobble(t, 3, (0.15, 0.28, 0.4))
        return dict(vessels=[m], camera=camera, focus=lambda t: (0.0, 0.0), cam_clearance=0.55,
                    tracks=dict(marlin=lambda t, st, f: (st['marlin'][f]['x'], 0, 1.5)))


class Shot07(Shot):
    """07 · Lift (0:23-0:28). Camera at the waterline. The Marlin spools up, climbs onto its foils and the spray
    falls away. It is out of frame in seconds."""
    id = '07'
    duration = 5.0
    ocean = dict(wave_scale=0.8, choppiness=0.75, wind=12.0, repeat=3, alignment=0.6, smallest=0.5, seed=3)
    moon = dict(az=78.0, el=13.0, strength=2.6, disc=False, ambient=1.1)
    exposure = 0.85
    X0, ACC, T0 = -12.0, 8.0, 0.45

    def build(self):
        X0, ACC, T0 = self.X0, self.ACC, self.T0
        m = build_marlin()

        def st(t):
            tt = max(0.0, t - T0)
            foil = smooth(ramp(t, 1.25, 2.55))
            squat = math.sin(math.pi * ramp(t, 0.45, 2.2))  # bow rides up as it digs in, then levels on the foil
            spin = 2.0 * t + 55.0 * (smooth(ramp(t, 0.1, 1.6)) * t)
            return dict(x=X0 + 0.5 * ACC * tt * tt, y=0.0, heading=0.0, follow=1.0, foil=foil, pitch=rad(5.5) * squat,
                        roll=rad(0.8) * wobble(t, 4), prop_angle=spin)
        m['state'] = st
        m['wake'] = dict(strength=1.0, w0=1.1, side=1.0, wake_len=70.0)
        vel = lambda t: ACC * max(0.0, t - T0)

        ems = []
        for s in (1, -1):  # hull ploughing before it lifts
            e = spray_emitter(f'hullspray{s}', (int(0.5 * FPS), int(2.35 * FPS)), 5200, life=0.9, vel_normal=5.0, inherit=0.55, size=0.055, rand=2.4, quad=(3.2, 0.5))
            e['place'] = lambda t, state, f, s=s: ((state['marlin'][f]['x'] + 1.2, -s * 1.0, 0.15), (rad(s * 58), rad(-10), 0))
            ems.append(e)
        e = spray_emitter('fanwash', (int(0.15 * FPS), int(2.2 * FPS)), 5200, life=1.3, vel_normal=8.5, inherit=0.15, size=0.05, rand=2.6, quad=(1.2, 2.2))
        e['place'] = lambda t, state, f: ((state['marlin'][f]['x'] - 4.2, 0.0, 0.3), (0, rad(-62), 0))
        ems.append(e)
        e = spray_emitter('strutplume', (int(2.2 * FPS), int(5.0 * FPS)), 3000, life=0.7, vel_normal=4.5, inherit=0.75, size=0.045, rand=1.6, quad=(0.5, 0.35))
        e['place'] = lambda t, state, f: ((state['marlin'][f]['x'] + 0.55, 0.0, 0.1), (0, rad(-40), 0))
        ems.append(e)

        def camera(t, state, f):
            mx = state['marlin'][f]['x']
            # locked off at the waterline; pans with the Marlin, then lets it leave frame
            follow_x = lerp(X0 + 2.5, mx + 0.8, smooth(ramp(t, 0.0, 1.0)))
            tx = lerp(follow_x, 8.5, smooth(ramp(t, 2.15, 3.0)))  # the pan gives up and the Marlin runs out of frame
            tgt = (tx, 0.0, lerp(1.3, 2.35, smooth(ramp(t, 1.2, 2.3))) - 1.1 * smooth(ramp(t, 2.9, 4.2)))
            pos = (2.2 + 0.02 * wobble(t, 1), -9.6, 0.05)  # cam_clearance keeps it just above the surface
            return pos, jitter(tgt, t, 7, 0.03), 30.0, rad(0.9) * wobble(t, 9, (0.3, 0.7, 1.3))
        wake_anim = {
            'wake_w0_marlin': lambda t: lerp(1.1, 0.22, smooth(ramp(t, 1.5, 2.6))),
            'wake_side_marlin': lambda t: (1 - smooth(ramp(t, 1.5, 2.5))) * smooth(ramp(t, 0.4, 0.9)),
            'wake_strength_marlin': lambda t: smooth(ramp(t, 0.35, 0.9)),
        }
        return dict(vessels=[m], emitters=ems, camera=camera, focus=lambda t: (0.0, 0.0), cam_clearance=0.30, wake_anim=wake_anim,
                    tracks=dict(marlin=lambda t, st, f: (st['marlin'][f]['x'], 0, st['marlin'][f]['z'] + 1.5)))


class Shot09(Shot):
    """09 · The run (0:34-0:40). Drone tracking shot alongside a Marlin flying level over night chop, hull clear
    of the water and steady as the sea builds."""
    id = '09'
    duration = 6.0
    ocean = dict(wave_scale=0.75, choppiness=1.1, wind=10.0, repeat=3, seed=5)
    moon = dict(az=108.0, el=13.0, strength=2.3, disc=False, ambient=1.1)
    exposure = 0.85

    def build(self):
        V = 100 * KT
        m = build_marlin()
        m['state'] = lambda t: dict(x=V * t, y=0.0, heading=0.0, follow=0.0, foil=1.0, dz=0.025 * wobble(t, 3), pitch=rad(0.5 + 0.15 * wobble(t, 5)),
                                    roll=rad(0.35) * wobble(t, 7), prop_angle=t * 95.0)
        m['wake'] = dict(strength=0.9, w0=0.22, side=0.0, wake_len=60.0)
        e = spray_emitter('strutplume', (1, 400), 9000, life=0.6, vel_normal=5.5, inherit=0.86, size=0.05, rand=1.5, quad=(0.5, 0.35))
        e['place'] = lambda t, state, f: ((state['marlin'][f]['x'] + 0.55, 0.0, 0.1), (0, rad(-35), 0))

        def camera(t, state, f):
            k = smooth(t / self.duration)
            mx = state['marlin'][f]['x']
            rel = vlerp((11.0, -12.0, 2.5), (2.2, -15.5, 3.4), k)  # slides from the bow quarter to the beam, rising a little
            pos = (mx + rel[0] + 0.08 * wobble(t, 1), rel[1] + 0.08 * wobble(t, 2), rel[2] + 0.06 * wobble(t, 3))
            tgt = (mx + lerp(0.5, 0.4, k), 0.0, FOIL_RIDE + 0.9)  # a little lead room ahead of the bow
            return pos, jitter(tgt, t, 13, 0.035), lerp(44.0, 40.0, k), rad(0.5) * wobble(t, 17, (0.3, 0.8, 1.7))
        return dict(vessels=[m], emitters=[e], camera=camera, focus=lambda t: (V * t, 0.0), cam_clearance=1.0,
                    ocean_anim=dict(wave_scale=lambda t: lerp(0.75, 1.75, smooth(t / self.duration))),
                    tracks=dict(marlin=lambda t, st, f: (st['marlin'][f]['x'], 0, FOIL_RIDE + 0.8)))


class Shot10(Shot):
    """10 · Eyes on (0:40-0:46). Marlin's own infrared view of the go-fast (thermal pass, --ir), then pull out:
    the Marlin comes about, drops off its foils and settles hull-borne at standoff, pacing the boat, with the
    second Marlin holding its flank."""
    id = '10'
    duration = 6.0
    ocean = dict(wave_scale=0.9, choppiness=1.05, wind=9.5, repeat=3, seed=5)
    moon = dict(az=74.0, el=13.0, strength=2.3, disc=False, ambient=1.15)
    exposure = 0.9
    first_frame = 34  # the thermal view is on screen before this
    VG = 28 * KT
    A_END = (-10.0, -40.0)
    B_POS = (-27.0, 52.0)
    T_TURN0, T_TURN1 = 1.5, 3.1  # the turn onto the boat's course
    T_DROP0, T_DROP1 = 2.9, 4.0  # off the foil, settling hull-borne

    def build(self):
        VG, (ax, ay) = self.VG, self.A_END
        gf = build_gofast()
        gofast_sheets(gf)
        gf['state'] = gofast_state(v=VG)
        gf['wake'] = dict(strength=1.0, w0=1.25, side=1.0, wake_len=140.0)
        a = build_marlin('marlin') if not IR else dict(root=empty('marlin'), name='marlin', xs=-2.4, xb=3.2, beam=2.2, length=7.2)
        b = build_marlin('marlin2') if not IR else dict(root=empty('marlin2'), name='marlin2', xs=-2.4, xb=3.2, beam=2.2, length=7.2)
        for mm in (a, b):
            mm['root'].rotation_mode = 'ZYX'
        Rt = 11.0
        cx, cy = ax, ay - Rt  # turn centre (relative to the go-fast)

        def a_state(t):
            gx = VG * t
            if t <= self.T_TURN0:  # running in on a straight line before the turn (not seen: the IR view is on screen)
                th = math.pi
                rx, ry = cx - Rt, cy - (self.T_TURN0 - t) * 22.0
                hd = math.pi / 2
            else:
                k = smooth(ramp(t, self.T_TURN0, self.T_TURN1))
                th = math.pi - k * math.pi / 2  # west point -> north point, clockwise
                rx, ry = cx + Rt * math.cos(th), cy + Rt * math.sin(th)
                hd = th - math.pi / 2
            foil = 1 - smooth(ramp(t, self.T_DROP0, self.T_DROP1))
            bank = rad(-13) * math.sin(math.pi * ramp(t, self.T_TURN0 - 0.2, self.T_TURN1 + 0.1))
            settle = math.sin(math.pi * ramp(t, self.T_DROP0 + 0.5, self.T_DROP1 + 0.9))
            return dict(x=gx + rx, y=ry, heading=hd, follow=1.0, foil=foil, roll=bank * foil + rad(1.2) * wobble(t, 3) * (1 - foil),
                        pitch=rad(-2.2) * settle, dz=-0.10 * settle, prop_angle=t * lerp(85.0, 42.0, 1 - foil))
        a['state'] = a_state
        a['wake'] = dict(strength=0.0 if IR else 1.0, w0=0.22, side=0.0, wake_len=60.0)
        b['state'] = lambda t: dict(x=VG * t + self.B_POS[0], y=self.B_POS[1], heading=0.0, follow=0.9, foil=0.0, pitch=rad(1.0),
                                    roll=rad(1.0) * wobble(t, 12), prop_angle=t * 42.0)
        b['wake'] = dict(strength=0.0 if IR else 0.9, w0=1.1, side=1.0, wake_len=70.0)
        ems = gofast_spray(density=1.4)
        if not IR:
            e = spray_emitter('strutplume', (1, int(self.T_DROP0 * FPS) + 6), 3400, life=0.6, vel_normal=5.0, inherit=0.8, size=0.05, rand=1.5, quad=(0.5, 0.35))

            def plume(t, state, f):
                s = state['marlin'][f]
                c, sn = math.cos(s['heading']), math.sin(s['heading'])
                return (s['x'] + 0.55 * c, s['y'] + 0.55 * sn, 0.1), (0, rad(-38), s['heading'])
            e['place'] = plume
            ems.append(e)
            for sgn in (1, -1):  # splash as the hull comes down
                e = spray_emitter(f'settle{sgn}', (int((self.T_DROP0 + 0.45) * FPS), int((self.T_DROP1 + 0.5) * FPS)), 5000, life=0.85, vel_normal=5.5,
                                  inherit=0.5, size=0.055, rand=2.4, quad=(3.4, 0.5))

                def splash(t, state, f, sgn=sgn):
                    s = state['marlin'][f]
                    c, sn = math.cos(s['heading']), math.sin(s['heading'])
                    return (s['x'] + 1.0 * c + sgn * 1.0 * sn, s['y'] + 1.0 * sn - sgn * 1.0 * c, 0.15), (rad(sgn * 58), rad(-10), s['heading'])
                e['place'] = splash
                ems.append(e)

        if IR:
            def camera(t, state, f):
                gx = state['gofast'][f]['x']
                pos = (gx - 52.0, -100.0, 3.4)  # Marlin's mast sensor at standoff
                tgt = (gx + 0.6 + 0.10 * wobble(t, 4, (2.3, 3.9, 6.1)), 0.0, 0.85 + 0.08 * wobble(t, 6, (2.1, 3.4, 5.7)))
                return pos, tgt, lerp(215.0, 190.0, smooth(ramp(t, 0.0, 6.0))), rad(0.25) * wobble(t, 2)
        else:
            def camera(t, state, f):
                gx = state['gofast'][f]['x']
                k = smooth(ramp(t, 1.3, 6.0))
                rel = vlerp((-2.5, -62.0, 2.1), (-2.0, -70.0, 2.9), k)  # the pull-out
                pos = (gx + rel[0] + 0.06 * wobble(t, 1), rel[1] + 0.06 * wobble(t, 2), rel[2] + 0.05 * wobble(t, 3))
                tgt = (gx - 9.5, -10.0, 1.9)
                return pos, jitter(tgt, t, 5, 0.06), lerp(60.0, 54.0, k), rad(0.5) * wobble(t, 9, (0.3, 0.7, 1.5))
        wake_anim = {
            'wake_w0_marlin': lambda t: lerp(0.22, 1.1, smooth(ramp(t, self.T_DROP0 + 0.3, self.T_DROP1 + 0.2))),
            'wake_side_marlin': lambda t: smooth(ramp(t, self.T_DROP0 + 0.4, self.T_DROP1 + 0.3)),
        }

        def mast(t, st, f):
            s = st['marlin'][f]
            c, sn = math.cos(s['heading']), math.sin(s['heading'])
            return (s['x'] - 1.75 * c, s['y'] - 1.75 * sn, s['z'] + 3.35)
        return dict(vessels=[gf, a, b], emitters=ems, camera=camera, focus=lambda t: (VG * t - 4.0, -30.0), cam_clearance=0.9, wake_anim=wake_anim if not IR else {},
                    tracks=dict(toi=lambda t, st, f: (st['gofast'][f]['x'], 0, 0.95), mast=mast,
                                marlin=lambda t, st, f: (st['marlin'][f]['x'], st['marlin'][f]['y'], st['marlin'][f]['z'] + 1.2),
                                marlin2=lambda t, st, f: (st['marlin2'][f]['x'], st['marlin2'][f]['y'], st['marlin2'][f]['z'] + 1.5)))


# ---- v4 proposal stills (new shots asked for in the 13 Nov audio note; used in the structure PDF)
class Shot06B(Shot):
    """v4 · Marlin waits. Close, low angle from off the bow: the duct and sensor mast against the moon.
    Sitting there, waiting, always ready."""
    id = '06b'
    duration = 4.0
    ocean = dict(wave_scale=0.8, choppiness=0.6, wind=13.0, repeat=3, alignment=0.7, smallest=0.9, seed=3)
    moon = dict(az=143.0, el=10.5, strength=2.6, disc=True, ambient=1.1, fill=(-40.0, 35.0, 0.35))
    exposure = 0.85

    def build(self):
        m = build_marlin()
        m['state'] = lambda t: dict(x=0.0, y=0.0, heading=0.0, follow=1.0, foil=0.0, roll=rad(1.2) * wobble(t, 2, (0.21, 0.37, 0.6)), prop_angle=t * 1.2)
        m['wake'] = dict(strength=0.0, w0=1.0, side=0.0)

        def camera(t, state, f):
            k = t / self.duration
            pos = vlerp((7.6, -4.9, 0.85), (7.0, -4.4, 0.85), k)
            return pos, (-1.3, 0.0, 2.05), 40.0, rad(0.4) * wobble(t, 3, (0.15, 0.28, 0.4))
        return dict(vessels=[m], camera=camera, focus=lambda t: (0.0, 0.0), cam_clearance=0.45)


class ShotVector(Shot):
    """v4 · Multiple Marlins vectoring in. Three Marlins on their foils converging on one point, seen from a
    drone above and behind the nearest."""
    id = 'v1'
    duration = 4.0
    ocean = dict(wave_scale=0.8, choppiness=1.05, wind=10.0, repeat=3, seed=5)
    moon = dict(az=-5.0, el=11.0, strength=2.5, disc=True, ambient=1.15, fill=(200.0, 40.0, 0.3))
    exposure = 0.9

    def build(self):
        V = 100 * KT
        fleet = [('marlin', 0.0, 0.0, 0.0), ('marlin2', 52.0, 23.0, rad(-9)), ('marlin3', 74.0, -31.0, rad(11))]
        vessels, ems = [], []
        for i, (name, x0, y0, hd) in enumerate(fleet):
            m = build_marlin(name)
            m['state'] = (lambda t, x0=x0, y0=y0, hd=hd, i=i: dict(
                x=x0 + V * math.cos(hd) * t, y=y0 + V * math.sin(hd) * t, heading=hd, follow=0.0, foil=1.0,
                dz=0.02 * wobble(t, 3 + i), pitch=rad(0.5), roll=rad(0.4) * wobble(t, 7 + i), prop_angle=t * 95.0 + i))
            m['wake'] = dict(strength=1.0, w0=0.3, side=0.0, wake_len=90.0)
            vessels.append(m)
            e = spray_emitter(f'plume_{name}', (1, 400), 7000, life=0.7, vel_normal=5.5, inherit=0.86, size=0.06, rand=1.6, quad=(0.5, 0.35))

            def place(t, state, f, name=name):
                st = state[name][f]
                c, sn = math.cos(st['heading']), math.sin(st['heading'])
                return (st['x'] + 0.55 * c, st['y'] + 0.55 * sn, 0.1), (0, rad(-35), st['heading'])
            e['place'] = place
            ems.append(e)

        def camera(t, state, f):
            mx = state['marlin'][f]['x']
            pos = (mx - 15.5, -1.2, 5.6 + 0.05 * wobble(t, 1))
            return pos, jitter((mx + 40.0, -1.5, 1.2), t, 5, 0.04), 30.0, rad(0.5) * wobble(t, 9, (0.3, 0.7, 1.5))
        return dict(vessels=vessels, emitters=ems, camera=camera, focus=lambda t: (V * t + 25.0, 0.0), cam_clearance=1.0)


SHOTS = {s.id: s for s in (Shot01, Shot03, Shot06, Shot07, Shot09, Shot10, Shot06B, ShotVector)}

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True, choices=sorted(SHOTS))
    ap.add_argument('--ir', action='store_true', help='thermal (white-hot) pass')
    ap.add_argument('--out', default='blender/out')
    ap.add_argument('--res', default='1920x1080')
    ap.add_argument('--samples', type=int, default=10)
    ap.add_argument('--frames', help='a-b (1-based)')
    ap.add_argument('--still', type=float, help='render one frame at this time (s)')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--hq-denoise', action='store_true')
    ap.add_argument('--save-blend', help='directory to save the .blend scene into')
    run_shot(SHOTS[ap.parse_args(argv).shot](), ap.parse_args(argv))
