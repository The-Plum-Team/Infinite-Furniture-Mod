package com.theplumteam.infinitefurniture.client;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

import com.theplumteam.infinitefurniture.block.WardrobeBlock;
import com.theplumteam.infinitefurniture.block.WardrobeBlockEntity;
import com.theplumteam.infinitefurniture.block.WardrobeShape;
import com.theplumteam.infinitefurniture.block.WardrobeStructure;
import com.theplumteam.infinitefurniture.registry.ModRegistry;
import dev.architectury.event.events.client.ClientTickEvent;
import dev.architectury.platform.Platform;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.AccessibilityOnboardingScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Development only, with {@code -Dinfinitefurniture.showcase=true}: makes a flat creative world,
 * builds every wardrobe with the same planning and joining a click uses, checks what they hold and
 * drop, then photographs them closed, open, from behind and with the ghost preview, writes
 * {@code showcase/report.txt} next to the screenshots and quits. Exits with the failures counted.
 */
public final class Showcase {
    private static final String WORLD = "infinitefurniture-showcase-" + System.currentTimeMillis();
    private static final List<Consumer<Minecraft>> STEPS = new ArrayList<>();
    private static final List<String> REPORT = new ArrayList<>();
    private static int failures;
    private static int wait;
    private static boolean started;
    private static BlockPos base;

    private Showcase() {
    }

    public static void initIfEnabled() {
        if (!Platform.isDevelopmentEnvironment() || !Boolean.getBoolean("infinitefurniture.showcase")) return;
        ClientTickEvent.CLIENT_POST.register(Showcase::tick);
    }

    private static void tick(Minecraft minecraft) {
        if (!started) {
            minecraft.options.pauseOnLostFocus = false;
            // A fresh game directory opens on the accessibility welcome first.
            if (minecraft.screen instanceof AccessibilityOnboardingScreen) {
                minecraft.options.onboardAccessibility = false;
                minecraft.setScreen(new TitleScreen());
            }
            if (minecraft.screen instanceof TitleScreen) {
                started = true;
                createWorld(minecraft);
            }
            return;
        }
        if (minecraft.player == null || minecraft.level == null || minecraft.getSingleplayerServer() == null) return;
        if (STEPS.isEmpty() && base == null) {
            base = minecraft.player.blockPosition();
            plan();
            wait = 100;
        }
        if (wait > 0) {
            wait--;
            return;
        }
        if (!STEPS.isEmpty()) STEPS.remove(0).accept(minecraft);
    }

    private static void createWorld(Minecraft minecraft) {
        LevelSettings settings = new LevelSettings(WORLD, GameType.CREATIVE, false, Difficulty.PEACEFUL, true,
                new GameRules(), WorldDataConfiguration.DEFAULT);
        GameRules rules = settings.gameRules();
        rules.getRule(GameRules.RULE_DAYLIGHT).set(false, null);
        rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, null);
        minecraft.createWorldOpenFlows().createFreshLevel(WORLD, settings, new WorldOptions(1L, false, false),
                registries -> registries.registryOrThrow(Registries.WORLD_PRESET)
                        .getHolderOrThrow(WorldPresets.FLAT).value().createWorldDimensions());
    }

    // ------------------------------------------------------------------ the scenario

    private static void plan() {
        // The wardrobes stand in a row 6 blocks south of the player, fronts facing north (towards the player).
        BlockPos row = base.south(6);
        BlockPos small = row.west(6), tall = row.west(4), wide = row.west(1), big = row.east(3);
        BlockPos breakTest = row.east(9), almostBig = row.west(10);

        onServer(level -> {
            level.setDayTime(6000);
            put(level, small);
            fill(level, small, 5);

            put(level, tall);
            fill(level, tall, 4);
            join(level, tall, Direction.UP, WardrobeShape.TALL);
            check("tall keeps what the small one held", count(level, tall) == 4);

            put(level, wide);
            join(level, wide, Direction.EAST, WardrobeShape.WIDE);
            fill(level, wide, 40);

            // A big one: a wide one, a small one on its left end, then the last piece on the right end.
            put(level, big);
            fill(level, big, 3);
            join(level, big, Direction.EAST, WardrobeShape.WIDE);
            put(level, big.above());
            fill(level, big.above(), 2);
            check("a small one on a wide one doesn't join by itself",
                    level.getBlockState(big.above()).getValue(WardrobeBlock.SHAPE) == WardrobeShape.SMALL);
            join(level, big.east(), Direction.UP, WardrobeShape.BIG);
            check("big keeps the contents of both", count(level, big) == 5);
            check("big is intact", WardrobeStructure.of(big, level.getBlockState(big)).isIntact(level));
            fill(level, big, 40);

            // One piece short of a big one, for the ghost.
            put(level, almostBig);
            join(level, almostBig, Direction.EAST, WardrobeShape.WIDE);
            put(level, almostBig.above());

            // Front and back never join.
            put(level, row.west(12));
            check("the front doesn't join", WardrobeStructure.plan(level, row.west(12),
                    level.getBlockState(row.west(12)), Direction.NORTH).isEmpty());

            // Breaking one block of a big wardrobe takes it all down and gives back four pieces.
            put(level, breakTest);
            join(level, breakTest, Direction.UP, WardrobeShape.TALL);
            put(level, breakTest.east());
            join(level, breakTest.east(), Direction.UP, WardrobeShape.BIG);
            fill(level, breakTest, 7);
            level.destroyBlock(breakTest.east().above(), true);
            boolean gone = true;
            for (int dx = 0; dx < 2; dx++) {
                for (int dy = 0; dy < 2; dy++) {
                    gone &= level.getBlockState(breakTest.east(dx).above(dy)).isAir();
                }
            }
            check("breaking one block removes the whole big wardrobe", gone);
        });
        waitTicks(5);
        onServer(level -> {
            AABB area = new AABB(breakTest).inflate(4);
            int pieces = 0, stuff = 0;
            for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, area)) {
                if (item.getItem().is(ModRegistry.WARDROBE_ITEM.get())) pieces += item.getItem().getCount();
                else stuff += item.getItem().getCount();
                item.discard();
            }
            check("four pieces drop (got " + pieces + ")", pieces == 4);
            check("the contents drop (got " + stuff + " items)", stuff == 7 * 16);
        });

        // Photographs: the camera stands 6.5 blocks north of the row, at eye height, looking south.
        command("gamemode spectator");
        Vec3 front = Vec3.atBottomCenterOf(base).add(-1.0, 1.6, -2.0);
        look(front, 0, 8);
        shot("1-front-closed");
        open(small, tall, wide, big);
        waitTicks(30);
        shot("2-front-open");
        look(Vec3.atBottomCenterOf(base).add(-7.5, 1.0, 3.2), -50, 22);
        shot("3-small-and-tall-open");
        look(Vec3.atBottomCenterOf(base).add(3.6, 1.4, 3.0), 10, 25);
        shot("4-big-open");
        look(Vec3.atBottomCenterOf(big).add(0.5, 5.0, 0.0), 0, 90);
        shot("4b-big-open-from-above");
        look(Vec3.atBottomCenterOf(tall).add(0.0, 5.0, 0.0), 0, 90);
        shot("4c-tall-open-from-above");
        close(small, tall, wide, big);
        waitTicks(30);
        look(Vec3.atBottomCenterOf(base).add(-1.5, 1.6, 12.5), 180, 10);
        shot("5-back");
        look(Vec3.atBottomCenterOf(base).add(-10.5, 1.0, 9.5), -130, 12);
        shot("6-side");

        // The ghost: holding a piece, looking at the top of the small wardrobe, in creative.
        command("gamemode creative");
        STEPS.add(minecraft -> {
            minecraft.player.getAbilities().flying = true;
            minecraft.player.onUpdateAbilities();
            minecraft.player.getInventory().selected = 0;
            minecraft.player.getInventory().setItem(0, new ItemStack(ModRegistry.WARDROBE_ITEM.get()));
        });
        look(Vec3.atBottomCenterOf(small).add(0.0, 2.2, -2.6), 0, 25);
        STEPS.add(minecraft -> check("the ghost has a target",
                minecraft.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(small)));
        shot("7-ghost-tall");
        look(Vec3.atBottomCenterOf(almostBig.east()).add(0.0, 2.2, -2.6), 0, 25);
        shot("8-ghost-big", true);

        // The menu of the big wardrobe: a double chest's worth of slots.
        look(Vec3.atBottomCenterOf(big).add(0.5, 1.6, -3.0), 0, 15);
        onServer(level -> {
            var player = level.players().get(0);
            WardrobeBlockEntity wardrobe = WardrobeBlock.anchorEntity(level, big, level.getBlockState(big));
            player.openMenu(wardrobe);
        });
        waitTicks(10);
        shot("9-menu", true);
        STEPS.add(minecraft -> check("the big wardrobe opens a 54-slot menu",
                minecraft.player.containerMenu.slots.size() == 54 + 36));
        STEPS.add(minecraft -> finish(minecraft));
    }

    // ------------------------------------------------------------------ helpers run on the server

    private static void put(ServerLevel level, BlockPos pos) {
        level.setBlock(pos, WardrobeBlock.stateFor(Direction.NORTH, WardrobeShape.SMALL, 0), 3);
    }

    /** Plans and builds exactly as a click with a piece on {@code face} of {@code pos} does. */
    private static void join(ServerLevel level, BlockPos pos, Direction face, WardrobeShape expected) {
        var merge = WardrobeStructure.plan(level, pos, level.getBlockState(pos), face);
        check(expected.getSerializedName() + " plan from " + face, merge.isPresent()
                && merge.get().result().shape() == expected);
        merge.ifPresent(m -> WardrobeBlock.build(level, m));
    }

    private static void fill(ServerLevel level, BlockPos pos, int stacks) {
        WardrobeBlockEntity wardrobe = WardrobeBlock.anchorEntity(level, pos, level.getBlockState(pos));
        if (wardrobe == null) {
            check("a wardrobe at " + pos, false);
            return;
        }
        List<ItemStack> items = new ArrayList<>();
        for (int i = 0; i < stacks; i++) items.add(new ItemStack(i % 2 == 0 ? Items.WHITE_WOOL : Items.LEATHER, 16));
        wardrobe.insert(items);
    }

    private static int count(ServerLevel level, BlockPos pos) {
        WardrobeBlockEntity wardrobe = WardrobeBlock.anchorEntity(level, pos, level.getBlockState(pos));
        if (wardrobe == null) return -1;
        int stacks = 0;
        for (int i = 0; i < wardrobe.getContainerSize(); i++) {
            if (!wardrobe.getItem(i).isEmpty()) stacks++;
        }
        return stacks;
    }

    private static void open(BlockPos... wardrobes) {
        viewers(1, wardrobes);
    }

    private static void close(BlockPos... wardrobes) {
        viewers(0, wardrobes);
    }

    /** Tells clients the wardrobe has {@code count} viewers, as opening its menu would. */
    private static void viewers(int count, BlockPos... wardrobes) {
        onServer(level -> {
            for (BlockPos pos : wardrobes) {
                BlockPos anchor = WardrobeStructure.of(pos, level.getBlockState(pos)).anchor();
                level.blockEvent(anchor, ModRegistry.WARDROBE.get(), 1, count);
            }
        });
    }

    private static void onServer(Consumer<ServerLevel> action) {
        STEPS.add(minecraft -> {
            var server = minecraft.getSingleplayerServer();
            CompletableFuture<Void> done = server.submit(() -> action.accept(server.overworld()));
            done.join();
        });
    }

    // ------------------------------------------------------------------ helpers run on the client

    private static void command(String command) {
        STEPS.add(minecraft -> minecraft.player.connection.sendCommand(command));
        waitTicks(5);
    }

    private static void look(Vec3 eye, float yaw, float pitch) {
        STEPS.add(minecraft -> minecraft.player.connection.sendCommand(String.format(java.util.Locale.ROOT,
                "tp @s %.2f %.2f %.2f %.1f %.1f", eye.x, eye.y - minecraft.player.getEyeHeight(), eye.z, yaw, pitch)));
        waitTicks(25);
    }

    private static void shot(String name) {
        shot(name, false);
    }

    private static void shot(String name, boolean gui) {
        STEPS.add(minecraft -> {
            minecraft.options.hideGui = !gui;
            wait = 3;
        });
        STEPS.add(minecraft -> {
            Screenshot.grab(minecraft.gameDirectory, "showcase-" + name + ".png", minecraft.getMainRenderTarget(),
                    message -> { });
            minecraft.options.hideGui = false;
            REPORT.add("shot " + name);
        });
    }

    private static void waitTicks(int ticks) {
        STEPS.add(minecraft -> wait = ticks);
    }

    private static void check(String what, boolean ok) {
        REPORT.add((ok ? "PASS " : "FAIL ") + what);
        if (!ok) failures++;
    }

    private static void finish(Minecraft minecraft) {
        REPORT.add(failures == 0 ? "ALL PASSED" : failures + " FAILED");
        try {
            File out = new File(minecraft.gameDirectory, "screenshots/showcase-report.txt");
            Files.write(out.toPath(), REPORT, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        minecraft.stop();
    }
}
