package com.theplumteam.infinitefurniture.client;

import com.theplumteam.infinitefurniture.registry.ModRegistry;
import dev.architectury.registry.client.rendering.BlockEntityRendererRegistry;

public final class InfiniteFurnitureClient {
    private InfiniteFurnitureClient() {
    }

    /** Call once the registries are filled: on Fabric from the client initializer, on Forge from client setup. */
    public static void init() {
        BlockEntityRendererRegistry.register(ModRegistry.WARDROBE_ENTITY.get(), context -> new WardrobeRenderer());
        Showcase.initIfEnabled();
    }
}
