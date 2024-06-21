from bot.core.entities import Upgrade, SleepReason
from bot.core.tapper import Tapper
from bot.utils import logger
from bot.config.config import Settings


async def get_daily_combo(bot: Tapper, most_profit_upgrade: Upgrade) -> bool:
    if await check_daily_combo_is_possible(bot):
        combo = await bot.web_client.fetch_daily_combo()
        combo_significance = await get_daily_combo_significance(bot, combo)

        if combo_significance < most_profit_upgrade.calculate_significance(bot.profile):
            if not buy_daily_combo(bot, combo):
                return False
    return True


async def get_daily_combo_significance(bot: Tapper, combo: list[str]) -> float:
    if len(combo) == 0:
        logger.info(f"{bot.session_name} | Daily combo not published")
        return float('inf')

    total_price = 0
    total_earn = 0
    welcome_coins = 0

    for upgrade in bot.upgrades:
        if upgrade.id in combo:
            total_price += upgrade.price
            total_earn += upgrade.earn_per_hour
            welcome_coins += upgrade.welcome_coins

    return (total_price - 5_000_000 - welcome_coins) / total_earn \
        + max((total_price - bot.profile.get_spending_balance()) / bot.profile.earn_per_hour, 0)


async def check_daily_combo_is_possible(bot: Tapper):
    if bot.daily_combo.is_claimed:
        return False

    reward_claimed = await try_claim_daily_combo(bot)
    if reward_claimed:
        return False

    combo = await bot.web_client.fetch_daily_combo()
    if len(combo) == 0:
        logger.info(f"{bot.session_name} | Daily combo not published")
        return False

    combo_upgrades: list[Upgrade] = list(
        filter(lambda u: u.id in combo, bot.upgrades))

    for upgrade in combo_upgrades:
        if upgrade.is_expired:
            logger.info(f"{bot.session_name} "
                        f"| Can't upgrade <e>{upgrade.name}</e> for daily combo "
                        f"| It's expired")
            return False
        if not upgrade.is_available:
            logger.info(f"{bot.session_name} "
                        f"| Can't upgrade <e>{upgrade.name}</e> for daily combo "
                        f"| Required condition: <e>{upgrade.condition}</e>")
            return False
        if upgrade.level > upgrade.max_level or upgrade.level > Settings.MAX_UPGRADE_LEVEL:
            logger.info(f"{bot.session_name} "
                        f"| Can't upgrade <e>{upgrade.name}</e> for daily combo "
                        f"| Because max level reached")
            return False
    return True


async def buy_daily_combo(bot: Tapper, combo: list[str]) -> bool:
    if len(combo) == 0:
        logger.info(f"{bot.session_name} | Daily combo not published")
        return False
    for upgrade in bot.upgrades:
        if upgrade in combo:
            if upgrade.price <= bot.profile.get_spending_balance():
                await bot.do_upgrade(upgrade=upgrade)
            else:
                logger.info(f"{bot.session_name} | Not enough money for upgrade <e>{upgrade.name}</e>")
                bot.update_preferred_sleep(
                    delay=int((upgrade.price - bot.profile.get_spending_balance()) / bot.profile.earn_per_sec),
                    sleep_reason=SleepReason.WAIT_UPGRADE_MONEY
                )
                return False

    await try_claim_daily_combo(bot)
    return True


async def try_claim_daily_combo(bot: Tapper) -> bool:
    if len(bot.daily_combo.upgrade_ids) != 3:
        return False
    bot.profile = await bot.web_client.claim_daily_combo()
    logger.success(f"{bot.session_name} | Successfully get daily combo reward | "
                   f"Reward coins: <g>+{bot.daily_combo.bonus_coins}</g>")
    await bot.sleep(delay=5)
    return True
