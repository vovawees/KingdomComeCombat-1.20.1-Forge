package com.kingdomcomecombat.mixin;

import com.kingdomcomecombat.injury.ModStatusEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.item.MilkBucketItem;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

import java.util.List;

/** 1.21-1.21.4 variant, before milk clearing moved to a consume-effect component. */
@Mixin(MilkBucketItem.class)
public class LegacyMilkBucketInjuryMixin {
    @Redirect(
            method = "finishUsing",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/LivingEntity;removeAllEffects()Z"), require = 0
    )
    private boolean kingdomcomecombat$milkKeepsInjuriesAndBleeding(LivingEntity entity) {
        boolean removedAny = false;
        for (StatusEffectInstance instance : List.copyOf(entity.getActiveEffects())) {
            if (!ModStatusEffects.isInjuryOrBleeding(instance.getEffect())) {
                removedAny |= entity.removeEffect(instance.getEffect());
            }
        }
        return removedAny;
    }
}
