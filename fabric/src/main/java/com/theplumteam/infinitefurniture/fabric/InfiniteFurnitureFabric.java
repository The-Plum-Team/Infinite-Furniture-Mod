package com.theplumteam.infinitefurniture.fabric;

import com.theplumteam.infinitefurniture.InfiniteFurniture;
import net.fabricmc.api.ModInitializer;

public final class InfiniteFurnitureFabric implements ModInitializer {
    @Override
    public void onInitialize() {
        InfiniteFurniture.init();
    }
}
