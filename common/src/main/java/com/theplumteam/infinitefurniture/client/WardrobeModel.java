package com.theplumteam.infinitefurniture.client;

import java.util.List;
import java.util.Map;

import com.theplumteam.infinitefurniture.InfiniteFurniture;
import com.theplumteam.infinitefurniture.block.WardrobeBlockEntity;
import com.theplumteam.infinitefurniture.block.WardrobeShape;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.GeoModel;

/**
 * One model per shape, from the assets tools/convert_models.py builds. The clothes inside follow
 * how full the wardrobe is: an empty one is bare, and each group of clothes appears once the
 * wardrobe is fuller than its threshold.
 */
public class WardrobeModel extends GeoModel<WardrobeBlockEntity> {
    private static final Map<WardrobeShape, List<Clothes>> CLOTHES = Map.of(
            WardrobeShape.SMALL, List.of(new Clothes("clothes", 0)),
            WardrobeShape.TALL, List.of(new Clothes("clothes", 0)),
            WardrobeShape.WIDE, List.of(new Clothes("clothes_l", 0), new Clothes("clothes_r", 0.5f)),
            WardrobeShape.BIG, List.of(new Clothes("hanging", 0), new Clothes("clothes", 0.5f)));

    private static ResourceLocation asset(String folder, WardrobeShape shape, String suffix) {
        return InfiniteFurniture.id(folder + "/wardrobe_" + shape.getSerializedName() + suffix);
    }

    @Override
    public ResourceLocation getModelResource(WardrobeBlockEntity wardrobe) {
        return asset("geo", wardrobe.shape(), ".geo.json");
    }

    @Override
    public ResourceLocation getTextureResource(WardrobeBlockEntity wardrobe) {
        return asset("textures/block", wardrobe.shape(), ".png");
    }

    @Override
    public ResourceLocation getAnimationResource(WardrobeBlockEntity wardrobe) {
        return asset("animations", wardrobe.shape(), ".animation.json");
    }

    @Override
    public void setCustomAnimations(WardrobeBlockEntity wardrobe, long instanceId,
                                    AnimationState<WardrobeBlockEntity> state) {
        float fullness = wardrobe.fullness();
        for (Clothes clothes : CLOTHES.get(wardrobe.shape())) {
            getBone(clothes.bone).ifPresent(bone -> bone.setHidden(fullness <= clothes.above));
        }
    }

    /** A bone of clothes, shown while the wardrobe is fuller than {@code above}. */
    private record Clothes(String bone, float above) {
    }
}
