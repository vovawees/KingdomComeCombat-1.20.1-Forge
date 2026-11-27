package com.kingdomcomecombat.compat;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Optional, no-hard-dependency mod-compatibility layer.
 *
 * <p>Every check is null-safe, cached, and degrades to "feature absent" if the mod
 * (or FML mod list) is unavailable. No class from another mod is referenced here, so
 * Kingdom Come Combat never requires any other mod to load. Optional integrations
 * elsewhere should gate on {@link #isLoaded(String)} / the flags below.
 *
 * <p>Known mod ids (1.20.1 FreeSM pack focus). Absence is always safe.
 */
public final class KccModCompat {

    // ---- known mod ids -----------------------------------------------------
    public static final String TACZ = "tacz";                          // Timeless & Classics Zero (guns)
    public static final String TACZ_TWEAKS = "tacz_tweaks";
    public static final String CURIOS = "curios";
    public static final String GO_PRONE = "go_prone";
    public static final String NOT_ENOUGH_ANIMATIONS = "notenoughanimations";
    public static final String QUARK = "quark";
    public static final String SERENE_SEASONS = "sereneseasons";
    public static final String IMMERSIVE_VEHICLES = "mts";             // Immersive Vehicles / MTS
    public static final String KUBEJS = "kubejs";
    public static final String FIRST_PERSON = "firstperson";
    public static final String YES_STEVE_MODEL = "yes_steve_model";
    public static final String ENTITY_MODEL_FEATURES = "entity_model_features";
    public static final String GECKOLIB = "geckolib";

    /** Namespace used by TACZ ranged weapons. */
    private static final String TACZ_NAMESPACE = TACZ;

    /** Testing hook; production uses FML {@link ModList}. */
    public interface ModListAccess {
        boolean isLoaded(String modId);
    }

    private static volatile ModListAccess modListAccess = KccModCompat::defaultIsLoaded;
    private static final Map<String, Boolean> CACHE = new HashMap<>();
    private static volatile boolean cacheReady = false;

    private KccModCompat() {
    }

    // ---- core queries ------------------------------------------------------

    /** @return true if a mod with this id is present. Never throws; false if unknown. */
    public static boolean isLoaded(String modId) {
        if (modId == null || modId.isEmpty()) {
            return false;
        }
        if (!cacheReady) {
            // don't cache until FML has a mod list, to stay correct at early init
            return safeQuery(modId);
        }
        synchronized (CACHE) {
            return CACHE.computeIfAbsent(modId, KccModCompat::safeQuery);
        }
    }

    /** Build the cache once FML has finished loading mods. Safe to call any time. */
    public static void rebuildCache() {
        synchronized (CACHE) {
            CACHE.clear();
            cacheReady = true;
        }
    }

    /** Clear cache + reset access (tests / after mod list changes). */
    public static void reset() {
        synchronized (CACHE) {
            CACHE.clear();
            cacheReady = false;
        }
        modListAccess = KccModCompat::defaultIsLoaded;
    }

    /** Test hook: inject a mod-list source. Production never calls this. */
    public static void setModListForTesting(ModListAccess access) {
        modListAccess = access != null ? access : KccModCompat::defaultIsLoaded;
        synchronized (CACHE) {
            CACHE.clear();
            cacheReady = true;
        }
    }

    // ---- known integrations (all optional) --------------------------------

    public static boolean isTaczLoaded() {
        return isLoaded(TACZ);
    }

    public static boolean isCuriosLoaded() {
        return isLoaded(CURIOS);
    }

    public static boolean isGoProneLoaded() {
        return isLoaded(GO_PRONE);
    }

    public static boolean isNotEnoughAnimationsLoaded() {
        return isLoaded(NOT_ENOUGH_ANIMATIONS);
    }

    /**
     * True when a third-party animation mod should win for NON-combat animations.
     * Kingdom Come Combat keeps its combat overrides for KCC weapons regardless.
     */
    public static boolean shouldSuppressKccAnimations() {
        return isNotEnoughAnimationsLoaded() || isLoaded(YES_STEVE_MODEL);
    }

    /** True if KCC should not run its own combat on this stack (e.g. TACZ ranged guns). */
    public static boolean shouldSkipKccCombat(ItemStack stack) {
        return isRangedGun(stack);
    }

    // ---- item classification (no hard dependency on other mods' classes) ---

    /** @return true for ranged guns (TACZ namespace or gun-like registration), false for null/empty/unknown. */
    public static boolean isRangedGun(ItemStack stack) {
        if (stack == null || stack.isEmpty()) {
            return false;
        }
        Optional<ResourceLocation> key = Optional.ofNullable(ForgeRegistries.ITEMS.getKey(stack.getItem()));
        if (key.isEmpty()) {
            return false;
        }
        String namespace = key.get().getNamespace();
        String path = key.get().getPath();
        if (TACZ_NAMESPACE.equals(namespace)) {
            return true;
        }
        // soft heuristic for other gun mods; KCC melee weapons live in our own namespace
        if (!"kingdom_come_combat".equals(namespace) && !"minecraft".equals(namespace)) {
            String lower = path.toLowerCase(java.util.Locale.ROOT);
            return lower.contains("gun") || lower.contains("rifle") || lower.contains("pistol")
                    || lower.contains("shotgun") || lower.contains("sniper");
        }
        return false;
    }

    // ---- internals ---------------------------------------------------------

    private static boolean safeQuery(String modId) {
        try {
            return modListAccess.isLoaded(modId);
        } catch (Throwable t) {
            return false;
        }
    }

    private static boolean defaultIsLoaded(String modId) {
        try {
            ModList list = ModList.get();
            return list != null && list.isLoaded(modId);
        } catch (Throwable t) {
            return false;
        }
    }

    /** Immutable snapshot of currently-known loaded known-ids (diagnostics). */
    public static Map<String, Boolean> snapshot() {
        synchronized (CACHE) {
            return Collections.unmodifiableMap(new HashMap<>(CACHE));
        }
    }
}
