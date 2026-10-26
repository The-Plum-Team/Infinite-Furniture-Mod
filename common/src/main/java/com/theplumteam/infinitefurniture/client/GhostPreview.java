package com.theplumteam.infinitefurniture.client;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

import com.mojang.blaze3d.vertex.PoseStack;
import com.theplumteam.infinitefurniture.block.WardrobeBlock;
import com.theplumteam.infinitefurniture.block.WardrobeBlockEntity;
import com.theplumteam.infinitefurniture.block.WardrobeStructure;
import com.theplumteam.infinitefurniture.registry.ModRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * While the player holds a wardrobe and looks at a wardrobe it would join, shows the wardrobe the
 * click would build, see-through, in place of the wardrobes it would replace. Each loader calls
 * {@link #render} once a frame, after the translucent blocks.
 */
public final class GhostPreview {
    private static final Set<BlockPos> HIDDEN = new HashSet<>();
    @Nullable
    private static WardrobeBlockEntity ghost;

    private GhostPreview() {
    }

    /** Whether the wardrobe anchored at {@code anchor} is being replaced by the preview this frame. */
    static boolean hides(BlockPos anchor) {
        return HIDDEN.contains(anchor);
    }

    public static void render(PoseStack poseStack, MultiBufferSource.BufferSource buffers, Vec3 camera, float partialTick) {
        HIDDEN.clear();
        Optional<WardrobeStructure.Merge> merge = plan();
        if (merge.isEmpty()) {
            ghost = null;
            return;
        }
        Minecraft minecraft = Minecraft.getInstance();
        ClientLevel level = minecraft.level;
        WardrobeStructure result = merge.get().result();
        for (WardrobeStructure joined : merge.get().joined()) HIDDEN.add(joined.anchor());

        BlockState state = WardrobeBlock.stateFor(result.facing(), result.shape(), 0);
        if (ghost == null || !ghost.getBlockPos().equals(result.anchor()) || ghost.getBlockState() != state) {
            ghost = new WardrobeBlockEntity(result.anchor(), state);
            ghost.setLevel(level);
        }
        BlockEntityRenderer<WardrobeBlockEntity> renderer = minecraft.getBlockEntityRenderDispatcher().getRenderer(ghost);
        if (renderer == null) return;

        BlockPos anchor = result.anchor();
        poseStack.pushPose();
        poseStack.translate(anchor.getX() - camera.x, anchor.getY() - camera.y, anchor.getZ() - camera.z);
        WardrobeRenderer.ghost = true;
        try {
            int light = LevelRenderer.getLightColor(level, merge.get().added());
            renderer.render(ghost, partialTick, poseStack, buffers, light, OverlayTexture.NO_OVERLAY);
        } finally {
            WardrobeRenderer.ghost = false;
            poseStack.popPose();
        }
        buffers.endBatch();
    }

    private static Optional<WardrobeStructure.Merge> plan() {
        Minecraft minecraft = Minecraft.getInstance();
        LocalPlayer player = minecraft.player;
        ClientLevel level = minecraft.level;
        if (player == null || level == null || player.isSecondaryUseActive()) return Optional.empty();
        // Only the main hand joins: with anything else there, a click opens the wardrobe.
        if (!player.getMainHandItem().is(ModRegistry.WARDROBE_ITEM.get())) return Optional.empty();
        if (!(minecraft.hitResult instanceof BlockHitResult hit) || hit.getType() != HitResult.Type.BLOCK) {
            return Optional.empty();
        }
        BlockState state = level.getBlockState(hit.getBlockPos());
        return WardrobeStructure.plan(level, hit.getBlockPos(), state, hit.getDirection());
    }
}
