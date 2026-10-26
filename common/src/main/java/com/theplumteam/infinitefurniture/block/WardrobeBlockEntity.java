package com.theplumteam.infinitefurniture.block;

import java.util.ArrayList;
import java.util.List;

import com.theplumteam.infinitefurniture.registry.ModRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.ContainerOpenersCounter;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoBlockEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Every wardrobe block has one, but only the anchor's is used: it holds the contents of the
 * whole wardrobe and is what the renderer draws. Its slots are the size of the biggest wardrobe,
 * so a wardrobe that grows keeps everything; {@link #getContainerSize()} follows the shape.
 */
public class WardrobeBlockEntity extends BaseContainerBlockEntity implements GeoBlockEntity {
    private static final int MAX_SLOTS = 54;
    private static final int OPEN_EVENT = 1;
    private static final RawAnimation OPEN = RawAnimation.begin()
            .thenPlay("animation.wardrobe.open").thenLoop("animation.wardrobe.open_idle");
    private static final RawAnimation CLOSE = RawAnimation.begin().thenPlay("animation.wardrobe.close");

    private NonNullList<ItemStack> items = NonNullList.withSize(MAX_SLOTS, ItemStack.EMPTY);
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    /** Slots in use, synced to clients so the clothes inside follow how full it is. */
    private int filled;
    /** Players looking inside, as the server last reported it (client only). */
    private int viewers;
    /** Whether it has opened since it was loaded, so a closed wardrobe doesn't play "close" on load. */
    private boolean hasOpened;

    private final ContainerOpenersCounter openers = new ContainerOpenersCounter() {
        @Override
        protected void onOpen(Level level, BlockPos pos, BlockState state) {
            playSound(state, SoundEvents.BARREL_OPEN);
        }

        @Override
        protected void onClose(Level level, BlockPos pos, BlockState state) {
            playSound(state, SoundEvents.BARREL_CLOSE);
        }

        @Override
        protected void openerCountChanged(Level level, BlockPos pos, BlockState state, int before, int now) {
            level.blockEvent(pos, state.getBlock(), OPEN_EVENT, now);
        }

        @Override
        protected boolean isOwnContainer(Player player) {
            return player.containerMenu instanceof ChestMenu menu && menu.getContainer() == WardrobeBlockEntity.this;
        }
    };

    public WardrobeBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.WARDROBE_ENTITY.get(), pos, state);
    }

    public WardrobeStructure structure() {
        return WardrobeStructure.of(worldPosition, getBlockState());
    }

    public WardrobeShape shape() {
        return getBlockState().getValue(WardrobeBlock.SHAPE);
    }

    public boolean isAnchor() {
        return getBlockState().getValue(WardrobeBlock.PART) == 0;
    }

    public boolean isOpen() {
        return viewers > 0;
    }

    /** How full it is, from 0 to 1. */
    public float fullness() {
        return Math.min(1.0f, filled / (float) getContainerSize());
    }

    // ------------------------------------------------------------------ contents

    @Override
    public int getContainerSize() {
        return shape().slots();
    }

    @Override
    public boolean isEmpty() {
        for (int i = 0; i < getContainerSize(); i++) {
            if (!items.get(i).isEmpty()) return false;
        }
        return true;
    }

    @Override
    public ItemStack getItem(int slot) {
        return items.get(slot);
    }

    @Override
    public ItemStack removeItem(int slot, int amount) {
        ItemStack stack = ContainerHelper.removeItem(items, slot, amount);
        if (!stack.isEmpty()) setChanged();
        return stack;
    }

    @Override
    public ItemStack removeItemNoUpdate(int slot) {
        return ContainerHelper.takeItem(items, slot);
    }

    @Override
    public void setItem(int slot, ItemStack stack) {
        items.set(slot, stack);
        if (stack.getCount() > getMaxStackSize()) stack.setCount(getMaxStackSize());
        setChanged();
    }

    @Override
    public boolean stillValid(Player player) {
        if (level == null || level.getBlockEntity(worldPosition) != this || !isAnchor()) return false;
        return player.distanceToSqr(structure().center()) <= 64.0;
    }

    @Override
    public void clearContent() {
        items.clear();
        setChanged();
    }

    /** Empties every slot and returns what was in them, in slot order. */
    public List<ItemStack> takeAll() {
        List<ItemStack> taken = new ArrayList<>();
        for (int i = 0; i < items.size(); i++) {
            if (!items.get(i).isEmpty()) taken.add(items.set(i, ItemStack.EMPTY));
        }
        setChanged();
        return taken;
    }

    /** Fills the free slots in order with {@code stacks} and returns those that didn't fit. */
    public List<ItemStack> insert(List<ItemStack> stacks) {
        List<ItemStack> left = new ArrayList<>();
        int slot = 0;
        for (ItemStack stack : stacks) {
            while (slot < getContainerSize() && !items.get(slot).isEmpty()) slot++;
            if (slot < getContainerSize()) items.set(slot++, stack);
            else left.add(stack);
        }
        setChanged();
        return left;
    }

    /** Sends away anyone who has this wardrobe open, before it is joined into another. */
    public void closeViewers() {
        if (level == null) return;
        for (Player player : level.players()) {
            if (player instanceof ServerPlayer && player.containerMenu instanceof ChestMenu menu
                    && menu.getContainer() == this) {
                player.closeContainer();
            }
        }
    }

    @Override
    public void setChanged() {
        super.setChanged();
        int now = 0;
        for (ItemStack stack : items) {
            if (!stack.isEmpty()) now++;
        }
        if (now != filled) {
            filled = now;
            if (level != null && !level.isClientSide) {
                level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3);
            }
        }
    }

    // ------------------------------------------------------------------ menu

    @Override
    protected Component getDefaultName() {
        return Component.translatable("container.infinitefurniture.wardrobe");
    }

    @Override
    protected AbstractContainerMenu createMenu(int id, Inventory inventory) {
        return shape().rows == 3 ? ChestMenu.threeRows(id, inventory, this) : ChestMenu.sixRows(id, inventory, this);
    }

    @Override
    public void startOpen(Player player) {
        if (!remove && !player.isSpectator()) openers.incrementOpeners(player, level, worldPosition, getBlockState());
    }

    @Override
    public void stopOpen(Player player) {
        if (!remove && !player.isSpectator()) openers.decrementOpeners(player, level, worldPosition, getBlockState());
    }

    public void recheckOpen() {
        if (!remove) openers.recheckOpeners(level, worldPosition, getBlockState());
    }

    @Override
    public boolean triggerEvent(int id, int data) {
        if (id == OPEN_EVENT) {
            viewers = data;
            if (data > 0) hasOpened = true;
            return true;
        }
        return super.triggerEvent(id, data);
    }

    private void playSound(BlockState state, SoundEvent sound) {
        if (level == null) return;
        Vec3 center = structure().center();
        level.playSound(null, center.x, center.y, center.z, sound, SoundSource.BLOCKS, 0.5f,
                level.random.nextFloat() * 0.1f + 0.9f);
    }

    // ------------------------------------------------------------------ saving and sync

    @Override
    public void load(CompoundTag tag) {
        super.load(tag);
        if (tag.contains("Items")) {
            items = NonNullList.withSize(MAX_SLOTS, ItemStack.EMPTY);
            ContainerHelper.loadAllItems(tag, items);
            filled = (int) items.stream().filter(stack -> !stack.isEmpty()).count();
        }
        if (tag.contains("Filled")) filled = tag.getInt("Filled");
    }

    @Override
    protected void saveAdditional(CompoundTag tag) {
        super.saveAdditional(tag);
        ContainerHelper.saveAllItems(tag, items);
    }

    /** Clients get how full it is, never what is inside. */
    @Override
    public CompoundTag getUpdateTag() {
        CompoundTag tag = new CompoundTag();
        tag.putInt("Filled", filled);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }

    /** Forge reads this to cull the renderer; the wardrobe can be bigger than its block. */
    public AABB getRenderBoundingBox() {
        return structure().bounds().inflate(0.5);
    }

    // ------------------------------------------------------------------ animation

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "doors", 0, state -> {
            if (isOpen()) return state.setAndContinue(OPEN);
            if (hasOpened) return state.setAndContinue(CLOSE);
            return PlayState.STOP;
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
