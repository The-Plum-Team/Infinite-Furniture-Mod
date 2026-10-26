"""Builds the mod's GeckoLib and item resources from the Blockbench models in art/.

Usage: python3 tools/convert_models.py [--check]

For each art/wardrobe/wardrobe_<shape>.bbmodel (Blockbench, Bedrock entity format) it writes:

- assets/infinitefurniture/geo/wardrobe_<shape>.geo.json (Bedrock geometry 1.12.0),
- assets/infinitefurniture/animations/wardrobe_<shape>.animation.json, with the animations
  renamed to animation.wardrobe.<open|close|open_idle> so every shape shares one controller,
- assets/infinitefurniture/textures/block/wardrobe_<shape>.png, the embedded texture.

The small wardrobe also becomes a plain Java block model (models/item/wardrobe.json) for the
item, so the inventory shows the real cabinet without a custom item renderer.

Blockbench keeps Bedrock models mirrored in X, and exports a down face with its V flipped;
this does the same: origin.x = -to.x, pivot x negated, rotation y and z negated (in keyframes
too, where positions negate x).
With --check it only reports whether the committed files are up to date.
"""
import base64
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "art", "wardrobe")
ASSETS = os.path.join(ROOT, "common", "src", "main", "resources", "assets", "infinitefurniture")
SHAPES = ("small", "tall", "wide", "big")
LOOP = {"hold": "hold_on_last_frame", "loop": True, "once": False}


def num(v):
    v = float(v)
    return int(v) if v.is_integer() else round(v, 4)


def geometry(model, name):
    els = {e["uuid"]: e for e in model["elements"]}
    bones = []

    def walk(group, parent):
        bone = {"name": group["name"], "pivot": [num(-group["origin"][0]), num(group["origin"][1]),
                                                 num(group["origin"][2])]}
        if parent:
            bone["parent"] = parent
        rot = group.get("rotation")
        if rot and any(rot):
            bone["rotation"] = [num(rot[0]), num(-rot[1]), num(-rot[2])]
        cubes = []
        children = []
        for child in group["children"]:
            if isinstance(child, dict):
                children.append(child)
                continue
            e = els[child]
            if e.get("rotation") and any(e["rotation"]):
                raise SystemExit(f"{name}: rotated cube {e['name']} is not supported")
            frm, to = e["from"], e["to"]
            size = [num(t - f) for f, t in zip(frm, to)]
            uv = {}
            for face, d in e["faces"].items():
                if d.get("texture") is None:
                    continue
                u0, v0, u1, v1 = d["uv"]
                if face == "down":
                    uv[face] = {"uv": [num(u0), num(v1)], "uv_size": [num(u1 - u0), num(v0 - v1)]}
                else:
                    uv[face] = {"uv": [num(u0), num(v0)], "uv_size": [num(u1 - u0), num(v1 - v0)]}
            cubes.append({"origin": [num(-to[0]), num(frm[1]), num(frm[2])], "size": size, "uv": uv})
        if cubes:
            bone["cubes"] = cubes
        bones.append(bone)
        for child in children:
            walk(child, group["name"])

    for group in model["outliner"]:
        walk(group, None)
    res = model["resolution"]
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.infinitefurniture.{name}",
                        "texture_width": res["width"], "texture_height": res["height"],
                        "visible_bounds_width": 4, "visible_bounds_height": 4,
                        "visible_bounds_offset": [0, 1, 0]},
        "bones": bones}]}


def animations(model):
    out = {}
    for a in model["animations"]:
        short = a["name"].rsplit(".", 1)[-1]
        bones = {}
        for animator in a["animators"].values():
            channels = bones.setdefault(animator["name"], {})
            for k in sorted(animator["keyframes"], key=lambda k: k["time"]):
                p = k["data_points"][0]
                x, y, z = float(p["x"]), float(p["y"]), float(p["z"])
                # The same X mirror as the geometry: positions flip x, rotations flip y and z.
                value = [-x, y, z] if k["channel"] == "position" else [x, -y, -z]
                channels.setdefault(k["channel"], {})[f"{num(k['time'])}"] = [num(v) + 0 for v in value]
        anim = {"loop": LOOP[a["loop"]], "bones": bones}
        if a["length"]:
            anim["animation_length"] = num(a["length"])
        out[f"animation.wardrobe.{short}"] = anim
    return {"format_version": "1.8.0", "animations": out}


def item_model(model):
    """The closed small wardrobe as a Java block model: Blockbench's scene coordinates are the
    Java ones shifted by 8 in x and z, and Java UVs are in sixteenths of the texture."""
    res = model["resolution"]
    su, sv = 16 / res["width"], 16 / res["height"]
    elements = []
    for e in model["elements"]:
        faces = {}
        for face, d in e["faces"].items():
            if d.get("texture") is None:
                continue
            u0, v0, u1, v1 = d["uv"]
            faces[face] = {"uv": [num(u0 * su), num(v0 * sv), num(u1 * su), num(v1 * sv)],
                           "texture": "#wardrobe"}
        elements.append({"from": [num(e["from"][0] + 8), num(e["from"][1]), num(e["from"][2] + 8)],
                         "to": [num(e["to"][0] + 8), num(e["to"][1]), num(e["to"][2] + 8)],
                         "faces": faces})
    return {"parent": "minecraft:block/block",
            "textures": {"wardrobe": "infinitefurniture:block/wardrobe_small",
                         "particle": "infinitefurniture:block/wardrobe_small"},
            "elements": elements}


def outputs():
    files = {}
    for shape in SHAPES:
        name = f"wardrobe_{shape}"
        with open(os.path.join(ART, f"{name}.bbmodel"), encoding="utf-8") as f:
            model = json.load(f)
        files[f"geo/{name}.geo.json"] = json.dumps(geometry(model, name), indent=1) + "\n"
        files[f"animations/{name}.animation.json"] = json.dumps(animations(model), indent=1) + "\n"
        src = model["textures"][0]["source"]
        files[f"textures/block/{name}.png"] = base64.b64decode(src.split(",", 1)[1])
        if shape == "small":
            files["models/item/wardrobe.json"] = json.dumps(item_model(model), indent=1) + "\n"
    return files


def main():
    check = "--check" in sys.argv[1:]
    stale = []
    for rel, data in outputs().items():
        path = os.path.join(ASSETS, rel)
        raw = data if isinstance(data, bytes) else data.encode("utf-8")
        if os.path.exists(path) and open(path, "rb").read() == raw:
            continue
        stale.append(rel)
        if not check:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(raw)
    if check and stale:
        raise SystemExit("out of date: " + ", ".join(stale))
    print(("stale: " if check else "written: ") + (", ".join(stale) or "nothing"))


if __name__ == "__main__":
    main()
