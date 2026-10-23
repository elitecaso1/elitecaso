"""Shared helpers for THE GHOST shorts.

Every shortN/build.py imports this file and builds one complete .blend:
    blender -b -P short1/build.py                 # build + save short1/short1.blend
    blender -b -P short1/build.py -- --preview    # 540x960, every 2nd frame, low samples
    blender -b -P short1/build.py -- --render     # build, save and render the MP4

Rules (from the doc): hard-surface cars only, procedural world,
animation through keyframes / Follow Path, one camera per shot bound
to timeline markers, Eevee, 1080x1920 @ 30 fps.
Tested API target: Blender 4.2 - 4.5 (5.x paths are handled where they differ).
"""
import bisect
import math
import os
import random
import sys

import bpy  # first: bmesh/mathutils come with it when bpy is a pip module
import bmesh
from mathutils import Matrix, Vector, noise

FPS = 30
ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
PREVIEW = False


# ----------------------------------------------------------------- basics

def cli():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return {"preview": "--preview" in argv, "render": "--render" in argv}


def f(t):
    """Seconds -> frame number (frame 1 is t=0)."""
    return int(round(t * FPS)) + 1


def q(n):
    """Scale particle counts etc. down in preview mode."""
    return max(1, int(n * (0.3 if PREVIEW else 1.0)))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    random.seed(13)


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def empty(name, loc=(0, 0, 0), parent=None):
    o = link(bpy.data.objects.new(name, None))
    o.location = loc
    o.empty_display_size = 0.5
    if parent:
        o.parent = parent
    return o


def hidden_collection(name="_instances"):
    """Collection excluded from the view layer: holds particle instance objects."""
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        bpy.context.view_layer.layer_collection.children[name].exclude = True
    return c


# ----------------------------------------------------------------- scene

def setup(name, seconds, preview=False):
    global PREVIEW
    PREVIEW = preview
    sc = bpy.context.scene
    sc.name = name
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    r = sc.render
    r.resolution_x, r.resolution_y = 1080, 1920
    r.resolution_percentage = 50 if preview else 100
    sc.frame_start, sc.frame_end = 1, f(seconds) - 1
    sc.frame_step = 2 if preview else 1
    r.fps = FPS // sc.frame_step
    r.use_motion_blur = True
    ee = sc.eevee
    for attr, val in (("taa_render_samples", 16 if preview else 48),
                      ("use_raytracing", True),
                      ("use_gtao", True),
                      ("use_bloom", True),           # legacy Eevee only
                      ("volumetric_start", 0.1),
                      ("volumetric_end", 600.0),
                      ("volumetric_tile_size", "8" if preview else "4")):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, val)
            except Exception:
                pass
    vs = sc.view_settings
    for attr, val in (("view_transform", "AgX"), ("look", "AgX - Medium High Contrast")):
        try:
            setattr(vs, attr, val)
        except TypeError:
            pass

    out = os.path.join(ROOT, "renders")
    os.makedirs(out, exist_ok=True)
    base = os.path.join(out, name + ("_preview" if preview else ""))
    try:
        im = r.image_settings
        if hasattr(im, "media_type"):          # Blender 5.x
            im.media_type = "VIDEO"
        im.file_format = "FFMPEG"
        r.ffmpeg.format = "MPEG4"
        r.ffmpeg.codec = "H264"
        r.ffmpeg.constant_rate_factor = "MEDIUM" if preview else "HIGH"
        r.ffmpeg.audio_codec = "NONE"
        r.use_file_extension = False
        r.filepath = base + ".mp4"
    except Exception as e:
        print("MP4 output unavailable, writing PNG frames:", e)
        r.image_settings.file_format = "PNG"
        r.filepath = base + "_frames/"
    bloom()
    return sc


def bloom():
    """Eevee Next has no bloom toggle: add a compositor Glare node instead."""
    sc = bpy.context.scene
    try:
        if hasattr(sc, "compositing_node_group"):          # Blender 5.x
            nt = bpy.data.node_groups.new("Bloom", "CompositorNodeTree")
            nt.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            out = nt.nodes.new("NodeGroupOutput")
            sc.compositing_node_group = nt
        else:
            sc.use_nodes = True
            nt = sc.node_tree
            nt.nodes.clear()
            out = nt.nodes.new("CompositorNodeComposite")
        rl = nt.nodes.new("CompositorNodeRLayers")
        nt.links.new(rl.outputs["Image"], out.inputs[0])
    except Exception as e:
        print("compositor skipped:", e)
        return
    try:
        g = nt.nodes.new("CompositorNodeGlare")
        for kind in ("BLOOM", "FOG_GLOW"):
            try:
                g.glare_type = kind
                break
            except Exception:
                pass
        nt.links.new(rl.outputs["Image"], g.inputs["Image"])
        nt.links.new(g.outputs["Image"], out.inputs[0])
    except Exception as e:
        print("glare skipped:", e)


def world(color=(0.004, 0.005, 0.009), strength=1.0, fog=0.0, fog_color=(0.6, 0.65, 0.75),
          top=None):
    """Plain or two-tone (horizon->top gradient) world, optional volumetric fog."""
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    if top is not None:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*color, 1)
        ramp.color_ramp.elements[1].position = 0.5
        ramp.color_ramp.elements[1].color = (*top, 1)
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    if fog:
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = fog
        vol.inputs["Color"].default_value = (*fog_color, 1)
        nt.links.new(vol.outputs[0], nt.nodes["World Output"].inputs["Volume"])
    return w


def world_hdri(file, strength=1.0, rot=0.0, fog=0.0, fog_color=(0.6, 0.65, 0.75), **fallback):
    """HDRI environment from assets/hdri (Poly Haven, CC0); falls back to world() if missing."""
    path = os.path.join(ASSETS, "hdri", file)
    if not os.path.exists(path):
        return world(fog=fog, fog_color=fog_color, **fallback)
    w = world(fog=fog, fog_color=fog_color)
    nt = w.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    return w


def sun(energy=2.0, rot=(0.9, 0.2, 0.6), color=(1, 1, 1)):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = energy
    d.color = color
    o = link(bpy.data.objects.new("Sun", d))
    o.rotation_euler = rot
    return o


def light(name, kind="POINT", energy=500, loc=(0, 0, 5), color=(1, 1, 1), size=None,
          rot=(0, 0, 0), parent=None, spot=None):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    d.color = color
    if size is not None:
        if kind == "AREA":
            d.size = size
        else:
            d.shadow_soft_size = size
    if spot is not None and kind == "SPOT":
        d.spot_size = spot
        d.spot_blend = 0.4
    o = link(bpy.data.objects.new(name, d))
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    return o


# ----------------------------------------------------------------- materials

def _sock(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    return None


def mat(name, color=(0.5, 0.5, 0.5), metallic=0.0, rough=0.5, coat=0.0, emit=None,
        strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    s = _sock(p, "Coat Weight", "Clearcoat")
    if s:
        s.default_value = coat
    if emit is not None:
        _sock(p, "Emission Color", "Emission").default_value = (*emit, 1)
        _sock(p, "Emission Strength").default_value = strength
    if alpha < 1.0:
        p.inputs["Alpha"].default_value = alpha
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            if hasattr(m, attr):
                try:
                    setattr(m, attr, val)
                except Exception:
                    pass
    return m


def surface(name, color, color2=None, rough=(0.45, 0.85), bump=0.25, coarse=0.04, fine=25.0,
            metallic=0.0, puddles=False):
    """Procedural PBR-ish surface: large-scale colour/roughness variation + fine grain bump.
    puddles=True drives roughness from the coarse noise (wet road with glossy patches)."""
    m = mat(name, color, metallic, rough[0])
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    big = nt.nodes.new("ShaderNodeTexNoise")
    big.inputs["Scale"].default_value = coarse
    big.inputs["Detail"].default_value = 6
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = fine
    grain.inputs["Detail"].default_value = 10
    grain.inputs["Roughness"].default_value = 0.7
    for n in (big, grain):
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*color, 1)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (*(color2 or [c * 1.6 for c in color]), 1)
    nt.links.new(big.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["From Min"].default_value = 0.4 if puddles else 0.3
    rr.inputs["From Max"].default_value = 0.55 if puddles else 0.7
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = rough
    nt.links.new((big if puddles else grain).outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], p.inputs["Roughness"])
    bm = nt.nodes.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value = bump
    nt.links.new(grain.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
    return m


def glow(name, color, strength=10.0):
    """Emission-only material (lights, signs, dials). Black base so it reads as pure light."""
    return mat(name, color=(0, 0, 0), rough=1.0, emit=color, strength=strength)


def emission(m):
    return _sock(m.node_tree.nodes["Principled BSDF"], "Emission Strength")


def key_emit(m, pairs, interp=None):
    s = emission(m)
    for fr, v in pairs:
        s.default_value = v
        s.keyframe_insert("default_value", frame=fr)
    if interp:
        set_interp(m.node_tree, interp)


def volume_mat(name, density=0.05, color=(0.8, 0.82, 0.85), noisy=True, scale=0.05):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Density"].default_value = density
    if noisy:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 6
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.inputs["From Min"].default_value = 0.45
        ramp.inputs["From Max"].default_value = 0.7
        ramp.inputs["To Max"].default_value = density
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Value"])
        nt.links.new(ramp.outputs["Result"], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m


def image_mat(name, path, strength=1.0):
    m = mat(name, color=(1, 1, 1), rough=0.6)
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    p = nt.nodes["Principled BSDF"]
    nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], _sock(p, "Emission Color", "Emission"))
    emission(m).default_value = strength
    return m


# ----------------------------------------------------------------- meshes

def mesh_obj(name, verts, faces, m=None, loc=(0, 0, 0), rot=(0, 0, 0), parent=None,
             smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    o = link(bpy.data.objects.new(name, me))
    if m:
        me.materials.append(m)
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    if smooth:
        try:
            me.shade_smooth()
        except AttributeError:
            for p in me.polygons:
                p.use_smooth = True
    return o


def _bm_obj(name, bm, m, loc, rot, parent, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if m:
        me.materials.append(m)
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return o


def box(name, size, loc=(0, 0, 0), m=None, rot=(0, 0, 0), parent=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    o = _bm_obj(name, bm, m, loc, rot, parent)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    return o


def cylinder(name, r, depth, loc=(0, 0, 0), m=None, axis="Z", segments=24, r2=None,
             rot=(0, 0, 0), parent=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    return _bm_obj(name, bm, m, loc, rot, parent, smooth)


def sphere(name, r, loc=(0, 0, 0), m=None, parent=None, segs=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(6, segs // 2), radius=r)
    return _bm_obj(name, bm, m, loc, (0, 0, 0), parent, smooth=True)


def plane(name, sx, sy, loc=(0, 0, 0), m=None, rot=(0, 0, 0), parent=None):
    v = [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)]
    return mesh_obj(name, v, [(0, 1, 2, 3)], m, loc, rot, parent)


def annulus(name, r_in, r_out, a0=-210, a1=30, segs=48, loc=(0, 0, 0), m=None, parent=None):
    """Flat arc ring in the XZ plane, facing -Y (dials). Angles in degrees, 0 = +X."""
    verts, faces = [], []
    for i in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * i / segs)
        verts += [(math.cos(a) * r_in, 0, math.sin(a) * r_in), (math.cos(a) * r_out, 0, math.sin(a) * r_out)]
        if i:
            k = 2 * i
            faces.append((k - 2, k - 1, k + 1, k))
    return mesh_obj(name, verts, faces, m, loc, (0, 0, 0), parent)


def grid(name, sx, sy, nx, ny, height, loc=(0, 0, 0), m=None, smooth=True):
    """Terrain from a height function height(x, y) in world units."""
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -sx / 2 + sx * i / nx + loc[0]
            y = -sy / 2 + sy * j / ny + loc[1]
            verts.append((x, y, height(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return mesh_obj(name, verts, faces, m, (0, 0, loc[2]), smooth=smooth)


def fbm(x, y, scale=0.01, octaves=4):
    return noise.fractal(Vector((x * scale, y * scale, 0.37)), 0.6, 2.0, octaves)


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def corridor_terrain(name, path, sx, sy, nx, ny, center=(0, 0), flat=18.0, ramp=120.0, hmax=45.0,
                     m=None, base=-0.3, extra=None):
    """Hills on both sides of a path that runs roughly along +Y; flat strip under the road."""
    ys = [p.y for p in path.pts]
    xs = [p.x for p in path.pts]

    def road_x(y):
        i = min(max(bisect.bisect_left(ys, y), 1), len(ys) - 1)
        y0, y1 = ys[i - 1], ys[i]
        t = 0.0 if y1 == y0 else max(0.0, min(1.0, (y - y0) / (y1 - y0)))
        return xs[i - 1] + (xs[i] - xs[i - 1]) * t

    def h(x, y):
        dist = abs(x - road_x(y))
        z = base + smoothstep(flat, flat + ramp, dist) * hmax * max(0.1, 0.6 + fbm(x, y, 0.004))
        return extra(x, y, z, dist) if extra else z

    return grid(name, sx, sy, nx, ny, h, (center[0], center[1], 0), m)


def text(name, body, loc=(0, 0, 0), size=1.0, m=None, rot=(math.pi / 2, 0, 0), parent=None,
         extrude=0.02):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = extrude
    o = link(bpy.data.objects.new(name, cu))
    if m:
        cu.materials.append(m)
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    return o


def wedge(name, L, W, h_front, h_rear, z0, m, parent, taper=0.0):
    """Car body block: rear (−Y) height h_rear, front (+Y) height h_front."""
    w2, wt = W / 2, W / 2 - taper
    v = [(-w2, -L / 2, z0), (w2, -L / 2, z0), (w2, L / 2, z0), (-w2, L / 2, z0),
         (-wt, -L / 2, z0 + h_rear), (wt, -L / 2, z0 + h_rear), (wt, L / 2, z0 + h_front), (-wt, L / 2, z0 + h_front)]
    fcs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = mesh_obj(name, v, fcs, m, parent=parent)
    b = o.modifiers.new("bevel", "BEVEL")
    b.width = 0.07
    b.segments = 3
    return o


def prism(name, wb, lb, wt, lt, h, z0, y0, m, parent, top_shift=0.0):
    """Cabin / greenhouse: bottom rect wb x lb, top rect wt x lt, height h."""
    v = [(-wb / 2, y0 - lb / 2, z0), (wb / 2, y0 - lb / 2, z0), (wb / 2, y0 + lb / 2, z0), (-wb / 2, y0 + lb / 2, z0),
         (-wt / 2, y0 + top_shift - lt / 2, z0 + h), (wt / 2, y0 + top_shift - lt / 2, z0 + h),
         (wt / 2, y0 + top_shift + lt / 2, z0 + h), (-wt / 2, y0 + top_shift + lt / 2, z0 + h)]
    fcs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = mesh_obj(name, v, fcs, m, parent=parent)
    b = o.modifiers.new("bevel", "BEVEL")
    b.width = 0.05
    b.segments = 2
    return o


# ----------------------------------------------------------------- animation

def fcurves(idblock):
    ad = getattr(idblock, "animation_data", None)
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        try:
            return list(act.fcurves)
        except Exception:
            pass
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out += list(cb.fcurves)
    return out


def set_interp(idblock, kind="LINEAR", contains=None):
    for fc in fcurves(idblock):
        if contains and contains not in fc.data_path:
            continue
        for k in fc.keyframe_points:
            k.interpolation = kind


def key(idblock, attr, pairs, interp=None):
    for fr, v in pairs:
        setattr(idblock, attr, v)
        idblock.keyframe_insert(attr, frame=fr)
    if interp:
        set_interp(idblock, interp, attr)


def visible(objs, pairs):
    """pairs: [(frame, True/False)] for every object (and its children)."""
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    allobj = []
    for o in objs:
        allobj += [o] + list(o.children_recursive)
    for o in allobj:
        for fr, v in pairs:
            o.hide_render = not v
            o.hide_viewport = not v
            o.keyframe_insert("hide_render", frame=fr)
            o.keyframe_insert("hide_viewport", frame=fr)


def shake(obj, strength=0.05, scale=3.0, f0=None, f1=None):
    obj.keyframe_insert("location", frame=f0 or 1)
    for fc in fcurves(obj):
        if fc.data_path != "location":
            continue
        mod = fc.modifiers.new("NOISE")
        mod.strength = strength
        mod.scale = scale
        mod.phase = random.uniform(0, 100)
        if f0 is not None and f1 is not None:
            mod.use_restricted_range = True
            mod.frame_start, mod.frame_end = f0, f1
            mod.blend_in = mod.blend_out = 3


def glitch_in(m, f0, peak=12.0, frames=18):
    """Flickering emission fade-in for title text."""
    pairs = [(f0 - 1, 0.0)]
    for i in range(frames):
        pairs.append((f0 + i, random.choice((0.0, peak * 0.3, peak * 1.4, peak)) if i < frames - 4 else peak))
    key_emit(m, pairs, "CONSTANT")


# ----------------------------------------------------------------- paths & roads

class Path:
    """Bezier path with arc-length helpers. Cars ride it with Follow Path."""

    def __init__(self, name, pts, res=24):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.twist_mode = "Z_UP"
        cu.resolution_u = res
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cu.use_path = True
        cu.path_duration = 1000
        self.obj = link(bpy.data.objects.new(name, cu))
        self.obj.hide_render = True
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = self.obj.evaluated_get(dg)
        me = ev.to_mesh()
        self.pts = [Vector(v.co) for v in me.vertices]
        ev.to_mesh_clear()
        self.cum = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.cum.append(self.cum[-1] + (b - a).length)
        self.length = self.cum[-1]

    def at(self, d):
        d = max(0.0, min(d, self.length))
        i = min(max(bisect.bisect_right(self.cum, d) - 1, 0), len(self.pts) - 2)
        a, b = self.pts[i], self.pts[i + 1]
        seg = (self.cum[i + 1] - self.cum[i]) or 1.0
        return a.lerp(b, (d - self.cum[i]) / seg), (b - a).normalized()

    def frame(self, d):
        p, t = self.at(d)
        flat = Vector((t.x, t.y, 0)).normalized()
        return p, flat, Vector((flat.y, -flat.x, 0))       # pos, forward, right

    def point(self, d, lateral=0.0, up=0.0, ahead=0.0):
        p, fwd, side = self.frame(d)
        return p + side * lateral + fwd * ahead + Vector((0, 0, up))

    def nearest(self, q):
        q = Vector(q)
        i = min(range(len(self.pts)), key=lambda k: (self.pts[k] - q).length)
        return self.cum[i]


def loft(name, path, profile, d0=0.0, d1=None, step=2.0, m=None, smooth=False):
    """Sweep a 2D profile [(lateral, up), ...] along a Path (road, walls, rails, tunnels)."""
    d1 = path.length if d1 is None else d1
    n = max(2, int((d1 - d0) / step) + 1)
    k = len(profile)
    verts, faces = [], []
    for i in range(n):
        p, _, side = path.frame(d0 + (d1 - d0) * i / (n - 1))
        for x, z in profile:
            verts.append(p + side * x + Vector((0, 0, z)))
    for i in range(n - 1):
        for j in range(k - 1):
            a = i * k + j
            faces.append((a, a + 1, a + k + 1, a + k))
    return mesh_obj(name, verts, faces, m, smooth=smooth)


def road(name, path, width=8.0, m=None, d0=0.0, d1=None, shoulder=0.6):
    w = width / 2
    return loft(name, path, [(-w - shoulder, -0.25), (-w, 0.0), (w, 0.0), (w + shoulder, -0.25)],
                d0, d1, 2.0, m)


def dashes(name, path, lateral=0.0, every=12.0, length=4.0, width=0.15, m=None, d0=0.0, d1=None,
           z=0.02):
    d1 = path.length if d1 is None else d1
    verts, faces = [], []
    d = d0
    while d + length < d1:
        for dd in (d, d + length):
            p, _, side = path.frame(dd)
            c = p + side * lateral + Vector((0, 0, z))
            verts += [c - side * width / 2, c + side * width / 2]
        a = len(verts) - 4
        faces.append((a, a + 1, a + 3, a + 2))
        d += every
    return mesh_obj(name, verts, faces, m)


def along(path, every, d0=0.0, d1=None):
    d1 = path.length if d1 is None else d1
    d = d0
    while d <= d1:
        yield d
        d += every


# ----------------------------------------------------------------- cars

STYLES = {
    #            length width front rear   cabin: bottom len, top len, height, centre y   paint
    "charger":  dict(L=5.0, W=1.95, hf=0.52, hr=0.66, cab=(2.4, 1.5, 0.50, -0.25), color=(0.42, 0.01, 0.01), metal=0.6, rough=0.22),
    "roadster": dict(L=4.4, W=1.85, hf=0.40, hr=0.52, cab=(1.6, 0.9, 0.42, -0.50), color=(0.75, 0.72, 0.66), metal=0.7, rough=0.18),
    "pickup":   dict(L=5.5, W=2.00, hf=0.78, hr=0.62, cab=(1.9, 1.5, 0.78, 0.55), color=(0.06, 0.16, 0.32), metal=0.3, rough=0.45),
    "ghost":    dict(L=4.9, W=1.98, hf=0.44, hr=0.58, cab=(2.1, 1.2, 0.44, -0.30), color=(0.003, 0.003, 0.004), metal=0.85, rough=0.10),
}
WHEEL_R = 0.36
Z0 = 0.30


def _is_ferrari_wheel(n):
    return n.split(".")[0] in ("tire", "wheel", "brake", "nuts", "centre") or n.startswith("rim_")


def _is_concept_wheel(n):
    return n in ("Mesh_89", "Mesh_91", "Mesh_93", "Mesh_95") or "Rim" in n or "BrakeDisc" in n


# Real car models (assets/fetch_assets.sh). Missing file -> procedural box car.
MODELS = {
    "ferrari": dict(file="ferrari.glb", flip=False, paint=("Body_Color",), head=("Projector_Glass",),
                    tail=("Taillight_Glass",), glass=("Glass_Gray",), wheel=_is_ferrari_wheel),
    "concept": dict(file="CarConcept.glb", flip=True, paint=("Paint",), head=("Headlight",),
                    tail=("Brakelight",), glass=("Glass", "Mirror"), wheel=_is_concept_wheel),
}
STYLE_MODEL = {"charger": "ferrari", "roadster": "ferrari", "pickup": "ferrari", "ghost": "concept"}


def _principled(m):
    if not m or not m.use_nodes:
        return None
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def _unlink(m, sock):
    for l in list(m.node_tree.links):
        if l.to_socket == sock:
            m.node_tree.links.remove(l)


class Car:
    """Car rig: root empty (Follow Path), body, 4 spinning wheel pivots, head/tail light materials,
    real spot lights. Front = +Y, origin on the ground.

    Uses the real glTF model for its style when assets/ has it, else a low-poly box car.
    """

    def __init__(self, name, style="charger", head_color=(1.0, 0.92, 0.75), head_on=True,
                 head_strength=40.0, tail_strength=12.0, spots=True):
        s = STYLES[style]
        self.name, self.s, self.style = name, s, style
        self.root = empty(name)
        self.wheels = []
        self.wheel_r = WHEEL_R
        spec = MODELS.get(STYLE_MODEL.get(style, ""))
        path = os.path.join(ASSETS, spec["file"]) if spec else ""
        if spec and os.path.exists(path):
            L, W, zl_f, zl_r = self._import_model(spec, path, s, head_color, head_on, head_strength, tail_strength)
        else:
            L, W, zl_f, zl_r = self._procedural(s, head_color, head_on, head_strength, tail_strength)
        self.L, self.W = L, W
        self.spots = []
        if spots:
            for sx in (-1, 1):
                sp = light(f"{name}_spot{sx}", "SPOT", 1800 if head_on else 0, (sx * (W / 2 - 0.36), L / 2 + 0.1, zl_f),
                           head_color, 0.05, (math.pi / 2 - 0.07, 0, 0), self.root, spot=0.95)
                self.spots.append(sp)
        self.exhausts = [Vector((sx * 0.5, -L / 2 - 0.05, Z0 + 0.06)) for sx in (-1, 1)]
        self.constraint = None
        self.path = None

    def _import_model(self, spec, path, s, head_color, head_on, head_strength, tail_strength):
        name = self.name
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        holder = empty(name + "_model", parent=self.root)
        for o in new:
            if o.parent is None:
                o.parent = holder
        if spec["flip"]:
            holder.rotation_euler.z = math.pi
        meshes = [o for o in new if o.type == "MESH"]
        bpy.context.view_layer.update()
        pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        holder.location.z = -lo.z
        bpy.context.view_layer.update()

        # per-car copies of the materials we restyle / animate
        made = {}

        def restyle(m):
            nm = m.name.split(".")[0]
            if any(nm.startswith(p) for p in spec["paint"]):
                kind = "paint"
            elif nm in spec["head"]:
                kind = "head"
            elif nm in spec["tail"]:
                kind = "tail"
            elif self.style == "ghost" and any(nm.startswith(g) for g in spec["glass"]):
                kind = "glass"
            else:
                return m
            if kind in made:
                return made[kind]
            c = m.copy()
            c.name = f"{name}_{kind}"
            p = _principled(c)
            if p is None:
                return m
            if kind == "paint":
                _unlink(c, p.inputs["Base Color"])
                p.inputs["Base Color"].default_value = (*s["color"], 1)
                p.inputs["Metallic"].default_value = s["metal"]
                p.inputs["Roughness"].default_value = s["rough"]
                cw = _sock(p, "Coat Weight", "Clearcoat")
                if cw:
                    _unlink(c, cw)
                    cw.default_value = 1.0
            elif kind == "glass":                       # tinted black: nobody visible inside
                for sn in ("Transmission Weight", "Transmission"):
                    if sn in p.inputs:
                        _unlink(c, p.inputs[sn])
                        p.inputs[sn].default_value = 0.0
                _unlink(c, p.inputs["Base Color"])
                p.inputs["Base Color"].default_value = (0.002, 0.002, 0.003, 1)
                p.inputs["Roughness"].default_value = 0.02
                p.inputs["Alpha"].default_value = 1.0
            else:
                col = head_color if kind == "head" else (1.0, 0.02, 0.01)
                ec = _sock(p, "Emission Color", "Emission")
                es = _sock(p, "Emission Strength")
                _unlink(c, ec)
                _unlink(c, es)
                ec.default_value = (*col, 1)
                es.default_value = (head_strength if head_on else 0.0) if kind == "head" else tail_strength
            made[kind] = c
            return c

        for o in meshes:
            for slot in o.material_slots:
                if slot.material:
                    slot.material = restyle(slot.material)
        self.paint = made.get("paint") or mat(name + "_paint", s["color"], s["metal"], s["rough"], coat=1.0)
        self.head = made.get("head") or glow(name + "_head", head_color, head_strength if head_on else 0.0)
        self.tail = made.get("tail") or glow(name + "_tail", (1.0, 0.02, 0.01), tail_strength)

        # wheel pivots: group wheel parts per corner, spin the pivot about X
        groups = {}
        for o in meshes:
            if spec["wheel"](o.name):
                c = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
                groups.setdefault((c.x > 0, c.y > 0), []).append((o, c))
        for i, (k, parts) in enumerate(sorted(groups.items())):
            centre = sum((c for _, c in parts), Vector()) / len(parts)
            pivot = empty(f"{name}_wheel{i}", centre, self.root)
            bpy.context.view_layer.update()
            for o, _ in parts:
                mw = o.matrix_world.copy()
                o.parent = pivot
                o.matrix_world = mw
            self.wheels.append(pivot)
            self.wheel_r = centre.z
        L, W = hi.y - lo.y, hi.x - lo.x
        return L, W, (hi.z - lo.z) * 0.5, (hi.z - lo.z) * 0.6

    def _procedural(self, s, head_color, head_on, head_strength, tail_strength):
        name = self.name
        L, W = s["L"], s["W"]
        self.paint = mat(name + "_paint", s["color"], s["metal"], s["rough"], coat=1.0)
        glass = mat(name + "_glass", (0.005, 0.006, 0.008), 0.0, 0.03)
        rubber = mat(name + "_rubber", (0.02, 0.02, 0.02), 0.0, 0.8)
        rim = mat(name + "_rim", (0.6, 0.6, 0.62), 1.0, 0.25)
        self.head = glow(name + "_head", head_color, head_strength if head_on else 0.0)
        self.tail = glow(name + "_tail", (1.0, 0.02, 0.01), tail_strength)
        wedge(name + "_body", L, W, s["hf"], s["hr"], Z0, self.paint, self.root, taper=0.08)
        lb, lt, ch, cy = s["cab"]
        hb = s["hr"] + (s["hf"] - s["hr"]) * (cy + L / 2) / L
        prism(name + "_cabin", W * 0.86, lb, W * 0.74, lt, ch, Z0 + hb - 0.04, cy, glass, self.root,
              top_shift=-0.15)
        box(name + "_roof", (W * 0.72, lt * 0.92, 0.04), (0, cy - 0.15, Z0 + hb + ch - 0.02),
            self.paint, parent=self.root, bevel=0.015)
        box(name + "_splitter", (W * 0.9, 0.3, 0.06), (0, L / 2 - 0.1, Z0 - 0.02), rubber, parent=self.root)
        for sx in (-1, 1):
            for sy in (-1, 1):
                w = cylinder(f"{name}_wheel{len(self.wheels)}", WHEEL_R, 0.28,
                             (sx * (W / 2 - 0.12), sy * (L / 2 - 0.85), WHEEL_R), rubber, axis="X",
                             parent=self.root)
                cylinder(w.name + "_rim", WHEEL_R * 0.62, 0.30, (0, 0, 0), rim, axis="X", segments=12,
                         parent=w)
                self.wheels.append(w)
        zl_f, zl_r = Z0 + s["hf"] - 0.16, Z0 + s["hr"] - 0.16
        for sx in (-1, 1):
            box(f"{name}_headlight{sx}", (0.42, 0.06, 0.10), (sx * (W / 2 - 0.36), L / 2 + 0.005, zl_f),
                self.head, parent=self.root)
            box(f"{name}_taillight{sx}", (0.55, 0.06, 0.08), (sx * (W / 2 - 0.40), -L / 2 - 0.005, zl_r),
                self.tail, parent=self.root)
        return L, W, zl_f, zl_r

    # -- lights -------------------------------------------------------
    def headlights(self, pairs, strength=40.0, spot=1800.0):
        """pairs: [(frame, 0..1)] — fades body emission and the real spot lights together."""
        key_emit(self.head, [(fr, v * strength) for fr, v in pairs])
        for sp in self.spots:
            key(sp.data, "energy", [(fr, v * spot) for fr, v in pairs])

    def rim_light(self, energy=40, color=(0.6, 0.7, 1.0)):
        return light(self.name + "_rim", "AREA", energy, (0, 0, 3.2), color, 4.0, parent=self.root)

    # -- motion -------------------------------------------------------
    def drive(self, path, keys, lane=0.0, interp="LINEAR"):
        """keys: [(frame, metres along path)]. Wheels spin to match the distance."""
        c = self.root.constraints.new("FOLLOW_PATH")
        c.target = path.obj
        c.use_curve_follow = True
        c.use_fixed_location = True
        c.forward_axis = "FORWARD_Y"
        c.up_axis = "UP_Z"
        self.constraint, self.path = c, path
        self.root.location.x = lane
        dp = f'constraints["{c.name}"].offset_factor'
        for fr, d in keys:
            c.offset_factor = max(0.0, min(1.0, d / path.length))
            self.root.keyframe_insert(dp, frame=fr)
        set_interp(self.root, interp, "offset_factor")
        for w in self.wheels:
            for fr, d in keys:
                w.rotation_euler.x = -d / self.wheel_r
                w.keyframe_insert("rotation_euler", index=0, frame=fr)
            set_interp(w, interp)

    def vibrate(self, f0, f1, strength=0.008):
        """Engine idle shake on the body (not the wheels)."""
        for o in self.root.children:
            if "_wheel" in o.name or "_spot" in o.name:
                continue
            o.keyframe_insert("location", frame=f0)
            for fc in fcurves(o):
                if fc.data_path == "location" and fc.array_index == 2:
                    mod = fc.modifiers.new("NOISE")
                    mod.strength, mod.scale = strength, 0.6
                    mod.use_restricted_range = True
                    mod.frame_start, mod.frame_end = f0, f1

    def local(self, x, y, z):
        return Vector((x, y, z))

    def all_objects(self):
        return [self.root] + list(self.root.children_recursive)


# ----------------------------------------------------------------- cameras

def target(name, loc, parent=None):
    return empty(name + "_target", loc, parent)


def camera(name, loc, look=None, lens=35.0, parent=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 6000
    c = link(bpy.data.objects.new(name, cd))
    c.location = loc
    if parent:
        c.parent = parent
    if look is not None:
        tgt = look if isinstance(look, bpy.types.Object) else target(name, look, parent)
        con = c.constraints.new("TRACK_TO")
        con.target = tgt
        con.track_axis = "TRACK_NEGATIVE_Z"
        con.up_axis = "UP_Y"
        c["target"] = tgt.name
    return c


def cam_target(c):
    return bpy.data.objects[c["target"]]


def cut(cam, t):
    """Camera becomes active at time t (seconds) via a bound timeline marker."""
    sc = bpy.context.scene
    m = sc.timeline_markers.new(cam.name, frame=f(t))
    m.camera = cam
    if sc.camera is None or f(t) <= 1:
        sc.camera = cam


# ----------------------------------------------------------------- effects

def particles(name, emitter, inst, count, f0, f1, life, vel=(0, 0, 0), normal=0.0, gravity=1.0,
              size=1.0, rand=0.4, align_vel=False, rand_vel=0.0):
    mod = emitter.modifiers.new(name, "PARTICLE_SYSTEM")
    ps = mod.particle_system
    s = ps.settings
    s.count = q(count)
    s.frame_start, s.frame_end = f0, f1
    s.lifetime = life
    s.lifetime_random = 0.3
    s.emit_from = "FACE"
    s.normal_factor = normal
    s.object_align_factor = vel
    s.factor_random = rand_vel
    s.render_type = "OBJECT"
    s.instance_object = inst
    s.particle_size = size
    s.size_random = rand
    s.effector_weights.gravity = gravity
    if align_vel:
        s.use_rotations = True
        s.rotation_mode = "VEL"
    ps.seed = random.randint(0, 9999)
    emitter.show_instancer_for_render = False
    emitter.show_instancer_for_viewport = False
    return ps


def instance(name, kind, m, size):
    """Particle instance (lives in the excluded _instances collection)."""
    c = hidden_collection()
    o = sphere(name, size, m=m, segs=16) if kind == "sphere" else box(name, size, m=m)
    for col in list(o.users_collection):
        col.objects.unlink(o)
    c.objects.link(o)
    return o


def rain(parent, f0, f1, area=(40, 70), height=14, ahead=10, count=40000, origin=(0, 0, 0), name="rain"):
    m = bpy.data.materials.get("rain_mat") or glow("rain_mat", (0.55, 0.65, 0.85), 0.35)
    drop = bpy.data.objects.get("raindrop") or instance("raindrop", "box", m, (0.3, 0.004, 0.004))
    loc = (origin[0], origin[1] + ahead, origin[2] + height)
    em = plane(name + "_emitter", area[0], area[1], loc, rot=(math.pi, 0, 0), parent=parent)
    return particles(name, em, drop, count, f0, f1, 22, vel=(0, 0, 0), normal=18.0, gravity=1.0,
                     size=1.0, rand=0.5, align_vel=True, rand_vel=0.1)


def soft_mat(name, color, alpha):
    """Smoke puff: opacity falls off towards the silhouette so overlapping spheres read as soft smoke."""
    m = mat(name, color, 0, 1.0, alpha=alpha)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, 1.0
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = alpha, 0.0
    nt.links.new(lw.outputs["Facing"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], p.inputs["Alpha"])
    return m


def smoke(name, loc, parent, f0, f1, count=600, color=(0.55, 0.55, 0.58), vel=(0, -3, 1.2), size=0.6,
          life=45, alpha=0.12, emitter_size=0.3):
    m = soft_mat(name + "_mat", color, alpha)
    puff = instance(name + "_puff", "sphere", m, 1.0)
    em = plane(name + "_emitter", emitter_size, emitter_size, loc, parent=parent)
    return particles(name, em, puff, count, f0, f1, life, vel=vel, gravity=-0.05, size=size, rand=0.6,
                     rand_vel=0.4)


def fog_box(name, size, loc, density=0.05, color=(0.75, 0.78, 0.82), noisy=True, scale=0.05):
    return box(name, size, loc, volume_mat(name + "_vol", density, color, noisy, scale))


def dashboard(name, loc, max_kmh=240, color=(1.0, 0.38, 0.06)):
    """Speedometer set, facing -Y. Returns (needle_pivot, camera_spot)."""
    root = empty(name, loc)
    box(name + "_panel", (2.6, 0.3, 1.6), (0, 0.25, 0), mat(name + "_panel_m", (0.01, 0.01, 0.012), 0.2, 0.5),
        parent=root, bevel=0.05)
    ring = glow(name + "_ring", color, 6.0)
    annulus(name + "_arc", 0.52, 0.56, -30, 210, 64, (0, 0.08, 0), ring, root)
    tick = glow(name + "_tick", (0.9, 0.9, 0.9), 3.0)
    font = glow(name + "_font", (0.9, 0.9, 0.9), 2.0)
    for v in range(0, max_kmh + 1, 20):
        a = math.radians(210 - 240 * v / max_kmh)
        r0 = 0.44 if v % 40 == 0 else 0.47
        verts = [(math.cos(a) * r0 - 0.008, 0.07, math.sin(a) * r0), (math.cos(a) * 0.51, 0.07, math.sin(a) * 0.51)]
        box(f"{name}_tick{v}", (0.012, 0.01, 0.06 if v % 40 == 0 else 0.035),
            ((verts[0][0] + verts[1][0]) / 2, 0.07, (verts[0][2] + verts[1][2]) / 2), tick,
            rot=(0, math.pi / 2 - a, 0), parent=root)
        if v % 40 == 0:
            text(f"{name}_n{v}", str(v), (math.cos(a) * 0.35, 0.06, math.sin(a) * 0.35 - 0.02), 0.07, font,
                 parent=root, extrude=0.0)
    text(name + "_unit", "km/h", (0, 0.06, -0.22), 0.07, font, parent=root, extrude=0.0)
    pivot = empty(name + "_pivot", (0, 0.05, 0), root)
    box(name + "_needle", (0.018, 0.01, 0.46), (0, 0, 0.2), glow(name + "_needle_m", (1, 0.1, 0.05), 12.0),
        parent=pivot)
    cylinder(name + "_cap", 0.05, 0.03, (0, 0.04, 0), mat(name + "_cap_m", (0.1, 0.1, 0.1), 1, 0.3), "Y",
             parent=root)
    light(name + "_fill", "POINT", 3, (0, -0.6, 0.4), color, 0.3, parent=root)
    pivot["max"] = max_kmh
    return pivot


def needle(pivot, pairs):
    """pairs: [(frame, km/h)]."""
    mx = pivot["max"]
    for fr, v in pairs:
        pivot.rotation_euler.y = math.radians(-120 + 240 * v / mx)
        pivot.keyframe_insert("rotation_euler", index=1, frame=fr)


def save(name):
    path = os.path.join(ROOT, name, name + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    print("saved", path)
    return path


def finish(name, opts):
    save(name)
    if opts["render"] or opts["preview"]:
        bpy.ops.render.render(animation=True)
        print("rendered", bpy.context.scene.render.filepath)
