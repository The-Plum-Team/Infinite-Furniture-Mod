"""Builds the mod's model resources from the Blockbench models in art/.

Usage: python3 tools/convert_models.py [--check]

For each art/wardrobe/wardrobe_<shape>.bbmodel (Blockbench, Bedrock entity format) it writes:

- assets/infinitefurniture/furniture/wardrobe_<shape>.json, read by the mod's FurnitureModel:
  the bones (pivot, rotation, parent) with their cubes (from, to and a [u0, v0, u1, v1] pixel
  rectangle per face) and the open, close and open_idle animations as keyframe lists;
- assets/infinitefurniture/textures/block/wardrobe_<shape>.png, the embedded texture.

Everything stays in Blockbench's own scene coordinates and keyframe values, which are
Minecraft's block coordinates in pixels with the model's floor centre at the origin; the mod
applies Blockbench's display conventions when it draws them.

The small wardrobe also becomes a plain Java block model (models/item/wardrobe.json) for the
item, so the inventory shows the real cabinet without a custom item renderer.
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
FACES = ("north", "east", "south", "west", "up", "down")


def num(v):
    v = float(v)
    return int(v) if v.is_integer() else round(v, 4)


def furniture(model, name):
    els = {e["uuid"]: e for e in model["elements"]}
    bones = []

    def walk(group, parent):
        cubes = []
        children = []
        for child in group["children"]:
            if isinstance(child, dict):
                children.append(child)
                continue
            e = els[child]
            if e.get("rotation") and any(e["rotation"]):
                raise SystemExit(f"{name}: rotated cube {e['name']} is not supported")
            faces = {}
            for face in FACES:
                d = e["faces"].get(face)
                if d and d.get("texture") is not None:
                    faces[face] = [num(c) for c in d["uv"]]
            cubes.append({"from": [num(c) for c in e["from"]], "to": [num(c) for c in e["to"]],
                          "faces": faces})
        bone = {"name": group["name"], "pivot": [num(c) for c in group["origin"]]}
        if parent:
            bone["parent"] = parent
        if group.get("rotation") and any(group["rotation"]):
            bone["rotation"] = [num(c) for c in group["rotation"]]
        bone["cubes"] = cubes
        bones.append(bone)
        for child in children:
            walk(child, group["name"])

    for group in model["outliner"]:
        walk(group, None)

    animations = {}
    for a in model["animations"]:
        short = a["name"].rsplit(".", 1)[-1]
        anim_bones = {}
        for animator in a["animators"].values():
            channels = anim_bones.setdefault(animator["name"], {})
            for k in sorted(animator["keyframes"], key=lambda k: k["time"]):
                if k.get("interpolation", "linear") != "linear":
                    raise SystemExit(f"{name}: only linear keyframes are supported")
                p = k["data_points"][0]
                channels.setdefault(k["channel"], []).append(
                    [num(k["time"]), num(p["x"]), num(p["y"]), num(p["z"])])
        animations[short] = {"length": num(a["length"]), "bones": anim_bones}

    res = model["resolution"]
    return {"texture_size": [res["width"], res["height"]], "bones": bones, "animations": animations}


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
        files[f"furniture/{name}.json"] = json.dumps(furniture(model, name), indent=1) + "\n"
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
