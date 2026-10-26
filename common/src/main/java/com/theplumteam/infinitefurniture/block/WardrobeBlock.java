package com.theplumteam.infinitefurniture.block;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import com.theplumteam.infinitefurniture.registry.ModRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Containers;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * A wardrobe piece. Placed on its own it is a small wardrobe; used on the top, bottom or side of
 * another wardrobe it joins it into a tall, wide or big one ({@link WardrobeStructure#plan}).
 * Breaking any block of a wardrobe takes the whole wardrobe down and gives back one piece per block.
 */
public class WardrobeBlock extends BaseEntityBlock {
    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;
    public static final EnumProperty<WardrobeShape> SHAPE = EnumProperty.create("shape", WardrobeShape.class);
    public static final IntegerProperty PART = IntegerProperty.create("part", 0, 3);

    /** Set while this mod removes the rest of a wardrobe, so those removals don't recurse. */
    private static boolean dismantling;
    /** The block a creative player is breaking: it gives no pieces back (the contents still drop). */
    @Nullable
    private static BlockPos creativeBreak;

    public WardrobeBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH)
                .setValue(SHAPE, WardrobeShape.SMALL).setValue(PART, 0));
    }

    public static BlockState stateFor(Direction facing, WardrobeShape shape, int part) {
        return ModRegistry.WARDROBE.get().defaultBlockState()
                .setValue(FACING, facing).setValue(SHAPE, shape).setValue(PART, part);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, SHAPE, PART);
    }

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new WardrobeBlockEntity(pos, state);
    }

    @Nullable
    public static WardrobeBlockEntity anchorEntity(BlockGetter level, BlockPos pos, BlockState state) {
        BlockPos anchor = WardrobeStructure.of(pos, state).anchor();
        return level.getBlockEntity(anchor) instanceof WardrobeBlockEntity wardrobe ? wardrobe : null;
    }

    @SuppressWarnings("deprecation")
    @Override
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player,
                                 InteractionHand hand, BlockHitResult hit) {
        ItemStack held = player.getItemInHand(hand);
        if (held.is(ModRegistry.WARDROBE_ITEM.get())) {
            Optional<WardrobeStructure.Merge> merge = WardrobeStructure.plan(level, pos, state, hit.getDirection());
            // Nothing to join: the piece is placed on its own, as any block would be.
            if (merge.isEmpty()) return InteractionResult.PASS;
            if (!level.isClientSide) {
                build((ServerLevel) level, merge.get());
                if (!player.getAbilities().instabuild) held.shrink(1);
                level.gameEvent(player, GameEvent.BLOCK_PLACE, merge.get().added());
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        if (level.isClientSide) return InteractionResult.SUCCESS;
        WardrobeBlockEntity wardrobe = anchorEntity(level, pos, state);
        if (wardrobe != null) player.openMenu(wardrobe);
        return InteractionResult.CONSUME;
    }

    /** Joins the planned wardrobes: their contents go, in order, into the new wardrobe's anchor. */
    public static void build(ServerLevel level, WardrobeStructure.Merge merge) {
        WardrobeStructure result = merge.result();
        List<ItemStack> contents = new ArrayList<>();
        for (WardrobeStructure joined : merge.joined()) {
            if (level.getBlockEntity(joined.anchor()) instanceof WardrobeBlockEntity wardrobe) {
                wardrobe.closeViewers();
                contents.addAll(wardrobe.takeAll());
            }
        }
        for (int row = 0; row < result.shape().height; row++) {
            for (int column = 0; column < result.shape().width; column++) {
                level.setBlock(result.pos(column, row),
                        stateFor(result.facing(), result.shape(), WardrobeStructure.part(column, row)), Block.UPDATE_ALL);
            }
        }
        Vec3 center = result.center();
        if (level.getBlockEntity(result.anchor()) instanceof WardrobeBlockEntity anchor) {
            contents = anchor.insert(contents);
        }
        for (ItemStack left : contents) Containers.dropItemStack(level, center.x, center.y, center.z, left);
        level.playSound(null, merge.added(), SoundEvents.WOOD_PLACE, SoundSource.BLOCKS, 1.0f, 0.8f);
    }

    @Override
    public void playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        creativeBreak = player.getAbilities().instabuild ? pos.immutable() : null;
        super.playerWillDestroy(level, pos, state, player);
    }

    @SuppressWarnings("deprecation")
    @Override
    public void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        if (!state.is(newState.getBlock()) && !dismantling) {
            boolean creative = pos.equals(creativeBreak);
            creativeBreak = null;
            dismantle(level, pos, state, creative);
        }
        super.onRemove(state, level, pos, newState, moved);
    }

    /** Drops the contents and the pieces of the wardrobe {@code pos} belonged to, and clears its other blocks. */
    private static void dismantle(Level level, BlockPos pos, BlockState state, boolean creative) {
        WardrobeStructure structure = WardrobeStructure.of(pos, state);
        Vec3 center = structure.center();
        WardrobeBlockEntity wardrobe = anchorEntity(level, pos, state);
        if (wardrobe != null) {
            for (ItemStack stack : wardrobe.takeAll()) {
                Containers.dropItemStack(level, center.x, center.y, center.z, stack);
            }
        }
        int pieces = 1;
        dismantling = true;
        try {
            for (BlockPos cell : structure.cells()) {
                if (cell.equals(pos)) continue;
                BlockState other = level.getBlockState(cell);
                if (other.getBlock() instanceof WardrobeBlock
                        && WardrobeStructure.of(cell, other).equals(structure)) {
                    level.removeBlock(cell, false);
                    pieces++;
                }
            }
        } finally {
            dismantling = false;
        }
        if (!creative) {
            Containers.dropItemStack(level, center.x, center.y, center.z,
                    new ItemStack(ModRegistry.WARDROBE_ITEM.get(), pieces));
        }
    }

    @SuppressWarnings("deprecation")
    @Override
    public void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (level.getBlockEntity(pos) instanceof WardrobeBlockEntity wardrobe) wardrobe.recheckOpen();
    }

    @SuppressWarnings("deprecation")
    @Override
    public boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    @SuppressWarnings("deprecation")
    @Override
    public int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {
        return AbstractContainerMenu.getRedstoneSignalFromContainer(anchorEntity(level, pos, state));
    }

    @SuppressWarnings("deprecation")
    @Override
    public BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @SuppressWarnings("deprecation")
    @Override
    public BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }
}
