package com.theplumteam.infinitefurniture.forge;

import com.theplumteam.infinitefurniture.InfiniteFurniture;
import com.theplumteam.infinitefurniture.client.GhostPreview;
import com.theplumteam.infinitefurniture.client.InfiniteFurnitureClient;
import dev.architectury.platform.forge.EventBuses;
import net.minecraft.client.Minecraft;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

@Mod(InfiniteFurniture.MOD_ID)
public final class InfiniteFurnitureForge {
    public InfiniteFurnitureForge(FMLJavaModLoadingContext context) {
        IEventBus modBus = context.getModEventBus();
        EventBuses.registerModEventBus(InfiniteFurniture.MOD_ID, modBus);
        InfiniteFurniture.init();
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> Client.init(modBus));
    }

    private static final class Client {
        static void init(IEventBus modBus) {
            modBus.addListener((FMLClientSetupEvent event) ->
                    event.enqueueWork(InfiniteFurnitureClient::init));
            MinecraftForge.EVENT_BUS.addListener((RenderLevelStageEvent event) -> {
                if (event.getStage() == RenderLevelStageEvent.Stage.AFTER_TRANSLUCENT_BLOCKS) {
                    GhostPreview.render(event.getPoseStack(), Minecraft.getInstance().renderBuffers().bufferSource(),
                            event.getCamera().getPosition(), event.getPartialTick());
                }
            });
        }
    }
}
