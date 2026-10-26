package com.theplumteam.infinitefurniture;

import com.theplumteam.infinitefurniture.registry.ModRegistry;
import net.minecraft.resources.ResourceLocation;

public final class InfiniteFurniture {
    public static final String MOD_ID = "infinitefurniture";

    private InfiniteFurniture() {
    }

    public static void init() {
        ModRegistry.register();
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MOD_ID, path);
    }
}
