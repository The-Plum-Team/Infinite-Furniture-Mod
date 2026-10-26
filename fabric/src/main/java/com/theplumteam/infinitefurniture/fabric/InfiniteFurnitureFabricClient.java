package com.theplumteam.infinitefurniture.fabric;

import com.theplumteam.infinitefurniture.client.GhostPreview;
import com.theplumteam.infinitefurniture.client.InfiniteFurnitureClient;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.Minecraft;

public final class InfiniteFurnitureFabricClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        InfiniteFurnitureClient.init();
        WorldRenderEvents.AFTER_TRANSLUCENT.register(context -> GhostPreview.render(context.matrixStack(),
                Minecraft.getInstance().renderBuffers().bufferSource(), context.camera().getPosition(),
                context.tickDelta()));
    }
}
