package com.theplumteam.infinitefurniture.registry;

import com.theplumteam.infinitefurniture.InfiniteFurniture;
import com.theplumteam.infinitefurniture.block.WardrobeBlock;
import com.theplumteam.infinitefurniture.block.WardrobeBlockEntity;
import dev.architectury.registry.registries.DeferredRegister;
import dev.architectury.registry.registries.RegistrySupplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

public final class ModRegistry {
    private static final DeferredRegister<net.minecraft.world.level.block.Block> BLOCKS =
            DeferredRegister.create(InfiniteFurniture.MOD_ID, Registries.BLOCK);
    private static final DeferredRegister<Item> ITEMS = DeferredRegister.create(InfiniteFurniture.MOD_ID, Registries.ITEM);
    private static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(InfiniteFurniture.MOD_ID, Registries.BLOCK_ENTITY_TYPE);

    public static final RegistrySupplier<WardrobeBlock> WARDROBE = BLOCKS.register("wardrobe", () ->
            new WardrobeBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.WOOD)
                    .instrument(NoteBlockInstrument.BASS)
                    .strength(2.5f)
                    .sound(SoundType.WOOD)
                    .ignitedByLava()
                    .noOcclusion()
                    .pushReaction(PushReaction.BLOCK)));

    public static final RegistrySupplier<BlockItem> WARDROBE_ITEM = ITEMS.register("wardrobe", () ->
            new BlockItem(WARDROBE.get(), new Item.Properties().arch$tab(CreativeModeTabs.FUNCTIONAL_BLOCKS)));

    @SuppressWarnings("DataFlowIssue")
    public static final RegistrySupplier<BlockEntityType<WardrobeBlockEntity>> WARDROBE_ENTITY =
            BLOCK_ENTITIES.register("wardrobe", () ->
                    BlockEntityType.Builder.of(WardrobeBlockEntity::new, WARDROBE.get()).build(null));

    private ModRegistry() {
    }

    public static void register() {
        BLOCKS.register();
        ITEMS.register();
        BLOCK_ENTITIES.register();
    }
}
