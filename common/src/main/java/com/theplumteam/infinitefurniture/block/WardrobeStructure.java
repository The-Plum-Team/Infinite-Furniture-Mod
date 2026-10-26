package com.theplumteam.infinitefurniture.block;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/**
 * One wardrobe in the world: the blocks from {@code anchor} going {@code shape.width} blocks along
 * {@link #side()} and {@code shape.height} blocks up, all facing {@code facing}. Every block stores
 * its place in the rectangle as {@code part = column + 2 * row}; the anchor (part 0) holds the
 * contents and draws the model.
 */
public record WardrobeStructure(BlockPos anchor, Direction facing, WardrobeShape shape) {

    /** The largest shapes are tried first, so a piece completes a 2x2 whenever it can. */
    private static final WardrobeShape[] BY_SIZE = {WardrobeShape.BIG, WardrobeShape.TALL, WardrobeShape.WIDE};

    public static WardrobeStructure of(BlockPos pos, BlockState state) {
        Direction facing = state.getValue(WardrobeBlock.FACING);
        int part = state.getValue(WardrobeBlock.PART);
        BlockPos anchor = pos.relative(side(facing), -(part % 2)).below(part / 2);
        return new WardrobeStructure(anchor, facing, state.getValue(WardrobeBlock.SHAPE));
    }

    /** The axis the wide shapes grow along: the viewer's left when facing the front. */
    public static Direction side(Direction facing) {
        return facing.getClockWise();
    }

    public Direction side() {
        return side(facing);
    }

    public BlockPos pos(int column, int row) {
        return anchor.relative(side(), column).above(row);
    }

    public List<BlockPos> cells() {
        List<BlockPos> cells = new ArrayList<>(shape.cells());
        for (int row = 0; row < shape.height; row++) {
            for (int column = 0; column < shape.width; column++) {
                cells.add(pos(column, row));
            }
        }
        return cells;
    }

    public static int part(int column, int row) {
        return column + 2 * row;
    }

    /** Whether every block of the rectangle is in place, with this facing, shape and part. */
    public boolean isIntact(Level level) {
        for (int row = 0; row < shape.height; row++) {
            for (int column = 0; column < shape.width; column++) {
                BlockState state = level.getBlockState(pos(column, row));
                if (!(state.getBlock() instanceof WardrobeBlock)
                        || state.getValue(WardrobeBlock.FACING) != facing
                        || state.getValue(WardrobeBlock.SHAPE) != shape
                        || state.getValue(WardrobeBlock.PART) != part(column, row)) {
                    return false;
                }
            }
        }
        return true;
    }

    public AABB bounds() {
        BlockPos far = pos(shape.width - 1, shape.height - 1);
        return new AABB(anchor).minmax(new AABB(far));
    }

    public Vec3 center() {
        return bounds().getCenter();
    }

    /** Column of {@code pos} counted along this wardrobe's side axis from the anchor. */
    private int column(BlockPos pos) {
        Direction side = side();
        return (pos.getX() - anchor.getX()) * side.getStepX() + (pos.getZ() - anchor.getZ()) * side.getStepZ();
    }

    /**
     * What placing a wardrobe against {@code face} of the clicked one would build: the wardrobes it
     * joins and the shape they make, or empty when the piece would just be placed on its own.
     * The front and the back never join; the new block must be free, and the cells of the result
     * that are neither the clicked wardrobe nor the new piece must be whole wardrobes facing the
     * same way. The same answer drives the ghost preview on the client and the merge on the server.
     */
    public static Optional<Merge> plan(Level level, BlockPos clicked, BlockState clickedState, Direction face) {
        if (!(clickedState.getBlock() instanceof WardrobeBlock)) return Optional.empty();
        WardrobeStructure origin = of(clicked, clickedState);
        if (face.getAxis() == origin.facing.getAxis() || !origin.isIntact(level)) return Optional.empty();

        BlockPos added = clicked.relative(face);
        BlockState addedState = level.getBlockState(added);
        BlockState newState = WardrobeBlock.stateFor(origin.facing, WardrobeShape.SMALL, 0);
        if (!addedState.canBeReplaced() || !level.isUnobstructed(newState, added, CollisionContext.empty())) {
            return Optional.empty();
        }

        int addedColumn = origin.column(added);
        int addedRow = added.getY() - origin.anchor.getY();
        int minColumn = Math.min(0, addedColumn), maxColumn = Math.max(origin.shape.width - 1, addedColumn);
        int minRow = Math.min(0, addedRow), maxRow = Math.max(origin.shape.height - 1, addedRow);

        for (WardrobeShape shape : BY_SIZE) {
            for (int c0 = maxColumn - shape.width + 1; c0 <= minColumn; c0++) {
                for (int r0 = maxRow - shape.height + 1; r0 <= minRow; r0++) {
                    WardrobeStructure result = new WardrobeStructure(origin.pos(c0, r0), origin.facing, shape);
                    List<WardrobeStructure> joined = joinedInto(level, result, origin, added);
                    if (joined != null) return Optional.of(new Merge(result, added, joined));
                }
            }
        }
        return Optional.empty();
    }

    /** The wardrobes that fill {@code result} together with the new block, or null if they don't. */
    private static List<WardrobeStructure> joinedInto(Level level, WardrobeStructure result,
                                                      WardrobeStructure origin, BlockPos added) {
        AABB area = result.bounds();
        List<WardrobeStructure> joined = new ArrayList<>();
        joined.add(origin);
        for (BlockPos cell : result.cells()) {
            if (cell.equals(added) || contains(origin.bounds(), cell)) continue;
            BlockState state = level.getBlockState(cell);
            if (!(state.getBlock() instanceof WardrobeBlock) || state.getValue(WardrobeBlock.FACING) != result.facing) {
                return null;
            }
            WardrobeStructure other = of(cell, state);
            if (joined.contains(other)) continue;
            AABB bounds = other.bounds();
            if (!contains(area, BlockPos.containing(bounds.minX, bounds.minY, bounds.minZ))
                    || !contains(area, BlockPos.containing(bounds.maxX - 1, bounds.maxY - 1, bounds.maxZ - 1))
                    || !other.isIntact(level)) {
                return null;
            }
            joined.add(other);
        }
        return joined;
    }

    private static boolean contains(AABB box, BlockPos pos) {
        return box.contains(Vec3.atCenterOf(pos));
    }

    /** A planned merge: {@code result} built from the {@code joined} wardrobes plus a block at {@code added}. */
    public record Merge(WardrobeStructure result, BlockPos added, List<WardrobeStructure> joined) {
    }
}
