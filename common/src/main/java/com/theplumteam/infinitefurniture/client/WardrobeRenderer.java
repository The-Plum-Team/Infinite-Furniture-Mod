package com.theplumteam.infinitefurniture.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.theplumteam.infinitefurniture.block.WardrobeBlockEntity;
import com.theplumteam.infinitefurniture.block.WardrobeStructure;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.core.object.Color;
import software.bernie.geckolib.renderer.GeoBlockRenderer;

/**
 * Draws a wardrobe from its anchor block. The models are centred on their own footprint, so a
 * two-wide wardrobe is moved half a block along its side axis. While {@link #ghost} is set it draws
 * see-through, for {@link GhostPreview}.
 */
public class WardrobeRenderer extends GeoBlockRenderer<WardrobeBlockEntity> {
    private static final Color GHOST = Color.ofRGBA(1.0f, 1.0f, 1.0f, 0.55f);

    static boolean ghost;

    public WardrobeRenderer() {
        super(new WardrobeModel());
    }

    @Override
    public void defaultRender(PoseStack poseStack, WardrobeBlockEntity wardrobe, MultiBufferSource bufferSource,
                              @Nullable RenderType renderType, @Nullable VertexConsumer buffer, float yaw,
                              float partialTick, int packedLight) {
        if (!wardrobe.isAnchor()) return;
        if (!ghost && GhostPreview.hides(wardrobe.getBlockPos())) return;
        super.defaultRender(poseStack, wardrobe, bufferSource, renderType, buffer, yaw, partialTick,
                packedLight);
    }

    @Override
    public void preRender(PoseStack poseStack, WardrobeBlockEntity wardrobe, BakedGeoModel model,
                          MultiBufferSource bufferSource, VertexConsumer buffer, boolean isReRender, float partialTick,
                          int packedLight, int packedOverlay, float red, float green, float blue, float alpha) {
        super.preRender(poseStack, wardrobe, model, bufferSource, buffer, isReRender, partialTick, packedLight,
                packedOverlay, red, green, blue, alpha);
        if (!isReRender) {
            Direction side = WardrobeStructure.side(getFacing(wardrobe));
            double shift = (wardrobe.shape().width - 1) * 0.5;
            poseStack.translate(side.getStepX() * shift, 0, side.getStepZ() * shift);
        }
    }

    @Override
    public RenderType getRenderType(WardrobeBlockEntity wardrobe, ResourceLocation texture,
                                    @Nullable MultiBufferSource bufferSource, float partialTick) {
        return ghost ? RenderType.entityTranslucent(texture) : super.getRenderType(wardrobe, texture, bufferSource, partialTick);
    }

    @Override
    public Color getRenderColor(WardrobeBlockEntity wardrobe, float partialTick, int packedLight) {
        return ghost ? GHOST : Color.WHITE;
    }

    @Override
    public boolean shouldRenderOffScreen(WardrobeBlockEntity wardrobe) {
        return wardrobe.shape().cells() > 1;
    }
}
