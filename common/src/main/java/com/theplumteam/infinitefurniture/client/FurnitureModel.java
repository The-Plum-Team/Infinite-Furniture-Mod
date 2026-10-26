package com.theplumteam.infinitefurniture.client;

import java.io.IOException;
import java.io.Reader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.Nullable;
import org.joml.Matrix3f;
import org.joml.Matrix4f;

/**
 * A piece of furniture as tools/convert_models.py writes it from Blockbench: bones of cubes with a
 * pixel rectangle of the texture per face, and keyframed animations. Coordinates are Blockbench's
 * scene ones, in pixels, with the floor centre of the model at the origin and its front facing
 * north. Keyframes are in those same coordinates: a bone moves by its position and turns by its
 * rotation in degrees, about its pivot, in Z, Y, X order (Blockbench's own Euler order), so the
 * game shows what Blockbench shows. (Only a Bedrock export mirrors them, with the geometry.)
 */
public final class FurnitureModel {
    private final float textureWidth;
    private final float textureHeight;
    private final List<Bone> roots;
    private final Map<String, Animation> animations;

    private FurnitureModel(float textureWidth, float textureHeight, List<Bone> roots, Map<String, Animation> animations) {
        this.textureWidth = textureWidth;
        this.textureHeight = textureHeight;
        this.roots = roots;
        this.animations = animations;
    }

    @Nullable
    public Animation animation(String name) {
        return animations.get(name);
    }

    /**
     * Draws the model in the current pose, in pixels (the caller scales by 1/16). {@code pose} gives
     * each animated bone its offset; bones named in {@code hidden} are skipped with their children.
     */
    public void render(PoseStack poseStack, VertexConsumer buffer, Pose pose, Set<String> hidden,
                       int light, int overlay, float red, float green, float blue, float alpha) {
        for (Bone bone : roots) {
            bone.render(poseStack, buffer, pose, hidden, light, overlay, red, green, blue, alpha, this);
        }
    }

    // ------------------------------------------------------------------ loading

    public static FurnitureModel load(ResourceLocation location) {
        try (Reader reader = Minecraft.getInstance().getResourceManager().openAsReader(location)) {
            return parse(JsonParser.parseReader(reader).getAsJsonObject());
        } catch (IOException | RuntimeException e) {
            throw new IllegalStateException("Couldn't load furniture model " + location, e);
        }
    }

    private static FurnitureModel parse(JsonObject json) {
        JsonArray size = json.getAsJsonArray("texture_size");
        Map<String, Bone> byName = new HashMap<>();
        List<Bone> roots = new ArrayList<>();
        for (JsonElement element : json.getAsJsonArray("bones")) {
            JsonObject b = element.getAsJsonObject();
            List<Cube> cubes = new ArrayList<>();
            for (JsonElement c : b.getAsJsonArray("cubes")) cubes.add(Cube.parse(c.getAsJsonObject()));
            Bone bone = new Bone(b.get("name").getAsString(), vec(b.getAsJsonArray("pivot")),
                    b.has("rotation") ? vec(b.getAsJsonArray("rotation")) : new float[3], cubes);
            byName.put(bone.name, bone);
            // The converter writes a parent before its children.
            if (b.has("parent")) byName.get(b.get("parent").getAsString()).children.add(bone);
            else roots.add(bone);
        }
        Map<String, Animation> animations = new HashMap<>();
        for (Map.Entry<String, JsonElement> entry : json.getAsJsonObject("animations").entrySet()) {
            animations.put(entry.getKey(), Animation.parse(entry.getValue().getAsJsonObject()));
        }
        return new FurnitureModel(size.get(0).getAsFloat(), size.get(1).getAsFloat(), roots, animations);
    }

    private static float[] vec(JsonArray array) {
        float[] out = new float[array.size()];
        for (int i = 0; i < out.length; i++) out[i] = array.get(i).getAsFloat();
        return out;
    }

    // ------------------------------------------------------------------ bones and cubes

    private static final class Bone {
        final String name;
        final float[] pivot;
        final float[] rotation;
        final List<Cube> cubes;
        final List<Bone> children = new ArrayList<>();

        Bone(String name, float[] pivot, float[] rotation, List<Cube> cubes) {
            this.name = name;
            this.pivot = pivot;
            this.rotation = rotation;
            this.cubes = cubes;
        }

        void render(PoseStack poseStack, VertexConsumer buffer, Pose pose, Set<String> hidden, int light,
                    int overlay, float red, float green, float blue, float alpha, FurnitureModel model) {
            if (hidden.contains(name)) return;
            float[] move = pose.position(name);
            float[] turn = pose.rotation(name);
            poseStack.pushPose();
            poseStack.translate(pivot[0] + move[0], pivot[1] + move[1], pivot[2] + move[2]);
            float rx = rotation[0] + turn[0], ry = rotation[1] + turn[1], rz = rotation[2] + turn[2];
            if (rz != 0) poseStack.mulPose(Axis.ZP.rotationDegrees(rz));
            if (ry != 0) poseStack.mulPose(Axis.YP.rotationDegrees(ry));
            if (rx != 0) poseStack.mulPose(Axis.XP.rotationDegrees(rx));
            poseStack.translate(-pivot[0], -pivot[1], -pivot[2]);
            PoseStack.Pose last = poseStack.last();
            for (Cube cube : cubes) {
                cube.render(last.pose(), last.normal(), buffer, light, overlay, red, green, blue, alpha, model);
            }
            for (Bone child : children) {
                child.render(poseStack, buffer, pose, hidden, light, overlay, red, green, blue, alpha, model);
            }
            poseStack.popPose();
        }
    }

    /** The six faces in Minecraft's own vertex order (as block models bake them), with their normals. */
    private enum Face {
        DOWN("down", 0, -1, 0, new int[][]{{0, 0, 1}, {0, 0, 0}, {1, 0, 0}, {1, 0, 1}}),
        UP("up", 0, 1, 0, new int[][]{{0, 1, 0}, {0, 1, 1}, {1, 1, 1}, {1, 1, 0}}),
        NORTH("north", 0, 0, -1, new int[][]{{1, 1, 0}, {1, 0, 0}, {0, 0, 0}, {0, 1, 0}}),
        SOUTH("south", 0, 0, 1, new int[][]{{0, 1, 1}, {0, 0, 1}, {1, 0, 1}, {1, 1, 1}}),
        WEST("west", -1, 0, 0, new int[][]{{0, 1, 0}, {0, 0, 0}, {0, 0, 1}, {0, 1, 1}}),
        EAST("east", 1, 0, 0, new int[][]{{1, 1, 1}, {1, 0, 1}, {1, 0, 0}, {1, 1, 0}});

        /** Which corner of the face's UV rectangle each vertex takes: (u0, v0), (u0, v1), (u1, v1), (u1, v0). */
        private static final int[][] UV_CORNERS = {{0, 1}, {0, 3}, {2, 3}, {2, 1}};

        final String key;
        final float nx, ny, nz;
        final int[][] corners;

        Face(String key, float nx, float ny, float nz, int[][] corners) {
            this.key = key;
            this.nx = nx;
            this.ny = ny;
            this.nz = nz;
            this.corners = corners;
        }
    }

    private static final class Cube {
        final float[] from;
        final float[] to;
        final float[][] uvs = new float[Face.values().length][];

        Cube(float[] from, float[] to) {
            this.from = from;
            this.to = to;
        }

        static Cube parse(JsonObject json) {
            Cube cube = new Cube(vec(json.getAsJsonArray("from")), vec(json.getAsJsonArray("to")));
            JsonObject faces = json.getAsJsonObject("faces");
            for (Face face : Face.values()) {
                if (faces.has(face.key)) cube.uvs[face.ordinal()] = vec(faces.getAsJsonArray(face.key));
            }
            return cube;
        }

        void render(Matrix4f pose, Matrix3f normal, VertexConsumer buffer, int light, int overlay,
                    float red, float green, float blue, float alpha, FurnitureModel model) {
            for (Face face : Face.values()) {
                float[] uv = uvs[face.ordinal()];
                if (uv == null) continue;
                for (int i = 0; i < 4; i++) {
                    int[] corner = face.corners[i];
                    float x = corner[0] == 0 ? from[0] : to[0];
                    float y = corner[1] == 0 ? from[1] : to[1];
                    float z = corner[2] == 0 ? from[2] : to[2];
                    int[] uvCorner = Face.UV_CORNERS[i];
                    buffer.vertex(pose, x, y, z)
                            .color(red, green, blue, alpha)
                            .uv(uv[uvCorner[0]] / model.textureWidth, uv[uvCorner[1]] / model.textureHeight)
                            .overlayCoords(overlay)
                            .uv2(light)
                            .normal(normal, face.nx, face.ny, face.nz)
                            .endVertex();
                }
            }
        }
    }

    // ------------------------------------------------------------------ animation

    /** Where every animated bone is at one moment. */
    public static final class Pose {
        public static final Pose REST = new Pose();
        private static final float[] ZERO = new float[3];

        private final Map<String, float[]> positions = new HashMap<>();
        private final Map<String, float[]> rotations = new HashMap<>();

        float[] position(String bone) {
            return positions.getOrDefault(bone, ZERO);
        }

        float[] rotation(String bone) {
            return rotations.getOrDefault(bone, ZERO);
        }
    }

    /** Linear keyframes per bone and channel; past its last keyframe a channel holds that value. */
    public static final class Animation {
        public final float length;
        private final Map<String, float[][]> positions = new HashMap<>();
        private final Map<String, float[][]> rotations = new HashMap<>();

        private Animation(float length) {
            this.length = length;
        }

        static Animation parse(JsonObject json) {
            Animation animation = new Animation(json.get("length").getAsFloat());
            for (Map.Entry<String, JsonElement> bone : json.getAsJsonObject("bones").entrySet()) {
                JsonObject channels = bone.getValue().getAsJsonObject();
                if (channels.has("position")) animation.positions.put(bone.getKey(), keys(channels.getAsJsonArray("position")));
                if (channels.has("rotation")) animation.rotations.put(bone.getKey(), keys(channels.getAsJsonArray("rotation")));
            }
            return animation;
        }

        private static float[][] keys(JsonArray array) {
            float[][] keys = new float[array.size()][];
            for (int i = 0; i < keys.length; i++) keys[i] = vec(array.get(i).getAsJsonArray());
            return keys;
        }

        public Pose sample(float seconds) {
            Pose pose = new Pose();
            positions.forEach((bone, keys) -> pose.positions.put(bone, at(keys, seconds)));
            rotations.forEach((bone, keys) -> pose.rotations.put(bone, at(keys, seconds)));
            return pose;
        }

        /** Each key is {time, x, y, z}. */
        private static float[] at(float[][] keys, float t) {
            float[] first = keys[0];
            if (t <= first[0]) return new float[]{first[1], first[2], first[3]};
            for (int i = 1; i < keys.length; i++) {
                float[] a = keys[i - 1], b = keys[i];
                if (t <= b[0]) {
                    float f = b[0] == a[0] ? 1 : (t - a[0]) / (b[0] - a[0]);
                    return new float[]{a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f};
                }
            }
            float[] last = keys[keys.length - 1];
            return new float[]{last[1], last[2], last[3]};
        }
    }
}
