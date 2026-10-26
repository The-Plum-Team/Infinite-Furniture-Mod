package com.theplumteam.infinitefurniture.client;

import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.theplumteam.infinitefurniture.InfiniteFurniture;
import com.theplumteam.infinitefurniture.block.WardrobeBlock;
import com.theplumteam.infinitefurniture.block.WardrobeBlockEntity;
import com.theplumteam.infinitefurniture.block.WardrobeShape;
import com.theplumteam.infinitefurniture.block.WardrobeStructure;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;

/**
 * Draws a wardrobe from its anchor block with the shape's {@link FurnitureModel}. The models are
 * centred on their own footprint, so a two-wide wardrobe is moved half a block along its side axis.
 * Opening plays "open" and then holds "open_idle"; closing plays "close". The clothes inside follow
 * how full the wardrobe is: an empty one is bare, and each group of clothes appears once the
 * wardrobe is fuller than its threshold. While {@link #ghost} is set it draws see-through, for
 * {@link GhostPreview}.
 */
public class WardrobeRenderer implements BlockEntityRenderer<WardrobeBlockEntity> {
    private static final float GHOST_ALPHA = 0.55f;
    private static final Map<WardrobeShape, List<Clothes>> CLOTHES = Map.of(
            WardrobeShape.SMALL, List.of(new Clothes("clothes", 0)),
            WardrobeShape.TALL, List.of(new Clothes("clothes", 0)),
            WardrobeShape.WIDE, List.of(new Clothes("clothes_l", 0), new Clothes("clothes_r", 0.5f)),
            WardrobeShape.BIG, List.of(new Clothes("hanging", 0), new Clothes("clothes", 0.5f)));
    /** Loaded on first use; a resource reload needs a restart to pick up changed models. */
    private static final Map<WardrobeShape, FurnitureModel> MODELS = new EnumMap<>(WardrobeShape.class);

    static boolean ghost;

    private static String name(WardrobeShape shape) {
        return "wardrobe_" + shape.getSerializedName();
    }

    private static FurnitureModel model(WardrobeShape shape) {
        return MODELS.computeIfAbsent(shape, s -> FurnitureModel.load(InfiniteFurniture.id("furniture/" + name(s) + ".json")));
    }

    private static ResourceLocation texture(WardrobeShape shape) {
        return InfiniteFurniture.id("textures/block/" + name(shape) + ".png");
    }

    @Override
    public void render(WardrobeBlockEntity wardrobe, float partialTick, PoseStack poseStack,
                       MultiBufferSource bufferSource, int packedLight, int packedOverlay) {
        if (!wardrobe.isAnchor()) return;
        if (!ghost && GhostPreview.hides(wardrobe.getBlockPos())) return;
        WardrobeShape shape = wardrobe.shape();
        FurnitureModel model = model(shape);
        Direction facing = wardrobe.getBlockState().getValue(WardrobeBlock.FACING);
        Direction side = WardrobeStructure.side(facing);
        double shift = (shape.width - 1) * 0.5;

        poseStack.pushPose();
        poseStack.translate(0.5 + side.getStepX() * shift, 0, 0.5 + side.getStepZ() * shift);
        // The models face north.
        poseStack.mulPose(Axis.YP.rotationDegrees(switch (facing) {
            case WEST -> 90;
            case SOUTH -> 180;
            case EAST -> 270;
            default -> 0;
        }));
        poseStack.scale(1 / 16f, 1 / 16f, 1 / 16f);
        RenderType type = ghost ? RenderType.entityTranslucent(texture(shape)) : RenderType.entityCutoutNoCull(texture(shape));
        model.render(poseStack, bufferSource.getBuffer(type), pose(wardrobe, model, partialTick), hidden(wardrobe),
                packedLight, packedOverlay, 1, 1, 1, ghost ? GHOST_ALPHA : 1);
        poseStack.popPose();
    }

    private static FurnitureModel.Pose pose(WardrobeBlockEntity wardrobe, FurnitureModel model, float partialTick) {
        if (wardrobe.getLevel() == null) return FurnitureModel.Pose.REST;
        float seconds = (wardrobe.getLevel().getGameTime() - wardrobe.changedAt() + partialTick) / 20f;
        if (wardrobe.isOpen()) {
            FurnitureModel.Animation open = model.animation("open");
            if (open != null && seconds < open.length) return open.sample(seconds);
            FurnitureModel.Animation idle = model.animation("open_idle");
            if (idle != null) return idle.sample(0);
            return open != null ? open.sample(open.length) : FurnitureModel.Pose.REST;
        }
        FurnitureModel.Animation close = model.animation("close");
        // A wardrobe that hasn't opened since it loaded is simply closed.
        if (wardrobe.hasOpened() && close != null) return close.sample(seconds);
        return FurnitureModel.Pose.REST;
    }

    private static Set<String> hidden(WardrobeBlockEntity wardrobe) {
        float fullness = wardrobe.fullness();
        Set<String> hidden = new HashSet<>();
        for (Clothes clothes : CLOTHES.get(wardrobe.shape())) {
            if (fullness <= clothes.above) hidden.add(clothes.bone);
        }
        return hidden;
    }

    @Override
    public boolean shouldRenderOffScreen(WardrobeBlockEntity wardrobe) {
        return wardrobe.shape().cells() > 1;
    }

    /** A bone of clothes, shown while the wardrobe is fuller than {@code above}. */
    private record Clothes(String bone, float above) {
    }
}
