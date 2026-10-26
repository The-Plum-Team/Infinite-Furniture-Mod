package com.theplumteam.infinitefurniture.block;

import net.minecraft.util.StringRepresentable;

/**
 * The four wardrobes the pieces can form. A shape is {@code width} blocks along the wardrobe's
 * side axis and {@code height} blocks up; its storage grows with it, up to a double chest.
 */
public enum WardrobeShape implements StringRepresentable {
    SMALL("small", 1, 1, 3),
    TALL("tall", 1, 2, 6),
    WIDE("wide", 2, 1, 6),
    BIG("big", 2, 2, 6);

    private final String name;
    public final int width;
    public final int height;
    public final int rows;

    WardrobeShape(String name, int width, int height, int rows) {
        this.name = name;
        this.width = width;
        this.height = height;
        this.rows = rows;
    }

    public int cells() {
        return width * height;
    }

    public int slots() {
        return rows * 9;
    }

    /** The shape of a {@code width} x {@code height} rectangle, or null when none fits it. */
    public static WardrobeShape of(int width, int height) {
        for (WardrobeShape shape : values()) {
            if (shape.width == width && shape.height == height) return shape;
        }
        return null;
    }

    @Override
    public String getSerializedName() {
        return name;
    }
}
