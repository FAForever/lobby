from enum import Enum
from typing import NamedTuple

from api.models.PlayerEvent import PlayerEvent
from fa.factions import Factions


class PlayerEvents(Enum):
    EVENT_LOST_ACUS = "d6a699b7-99bc-4a7f-b128-15e1e289a7b3"
    EVENT_BUILT_AIR_UNITS = "3ebb0c4d-5e92-4446-bf52-d17ba9c5cd3c"
    EVENT_LOST_AIR_UNITS = "225e9b2e-ae09-4ae1-a198-eca8780b0fcd"
    EVENT_BUILT_LAND_UNITS = "ea123d7f-bb2e-4a71-bd31-88859f0c3c00"
    EVENT_LOST_LAND_UNITS = "a1a3fd33-abe2-4e56-800a-b72f4c925825"
    EVENT_BUILT_NAVAL_UNITS = "b5265b42-1747-4ba1-936c-292202637ce6"
    EVENT_LOST_NAVAL_UNITS = "3a7b3667-0f79-4ac7-be63-ba841fd5ef05"
    EVENT_BUILT_TECH_1_UNITS = "a8ee4f40-1e30-447b-bc2c-b03065219795"
    EVENT_LOST_TECH_1_UNITS = "3dd3ed78-ce78-4006-81fd-10926738fbf3"
    EVENT_BUILT_TECH_2_UNITS = "89d4f391-ed2d-4beb-a1ca-6b93db623c04"
    EVENT_LOST_TECH_2_UNITS = "aebd750b-770b-4869-8e37-4d4cfdc480d0"
    EVENT_BUILT_TECH_3_UNITS = "92617974-8c1f-494d-ab86-65c2a95d1486"
    EVENT_LOST_TECH_3_UNITS = "7f15c2be-80b7-4573-8f41-135f84773e0f"
    EVENT_BUILT_EXPERIMENTALS = "ed9fd79d-5ec7-4243-9ccf-f18c4f5baef1"
    EVENT_LOST_EXPERIMENTALS = "701ca426-0943-4931-85af-6a08d36d9aaa"
    EVENT_BUILT_ENGINEERS = "60bb1fc0-601b-45cd-bd26-83b1a1ac979b"
    EVENT_LOST_ENGINEERS = "e8e99a68-de1b-4676-860d-056ad2207119"
    EVENT_AEON_PLAYS = "96ccc66a-c5a0-4f48-acaa-888b00778b57"
    EVENT_AEON_WINS = "a6b51c26-64e6-4e7a-bda7-ea1cfe771ebb"
    EVENT_CYBRAN_PLAYS = "ad193982-e7ca-465c-80b0-5493f9739559"
    EVENT_CYBRAN_WINS = "56b06197-1890-42d0-8b59-25e1add8dc9a"
    EVENT_UEF_PLAYS = "1b900d26-90d2-43d0-a64e-ed90b74c3704"
    EVENT_UEF_WINS = "7be6fdc5-7867-4467-98ce-f7244a66625a"
    EVENT_SERAPHIM_PLAYS = "fefcb392-848f-4836-9683-300b283bc308"
    EVENT_SERAPHIM_WINS = "15b6c19a-6084-4e82-ada9-6c30e282191f"


class PlayerEventMetric(NamedTuple):
    name: str
    total: Enum
    subcategory: Enum

    def get_components_values(self, events_map: dict[str, PlayerEvent]) -> tuple[int, int]:
        total_ev = events_map.get(self.total.value)
        subcat_ev = events_map.get(self.subcategory.value)
        total = total_ev.current_count if total_ev else 0
        sub = subcat_ev.current_count if subcat_ev else 0
        return max(0, sub), max(0, total - sub)


FACTION_PLAYS_METRICS = (
    PlayerEventMetric(
        Factions.AEON.to_name().capitalize(),
        PlayerEvents.EVENT_AEON_PLAYS,
        PlayerEvents.EVENT_AEON_WINS,
    ),
    PlayerEventMetric(
        Factions.CYBRAN.to_name().capitalize(),
        PlayerEvents.EVENT_CYBRAN_PLAYS,
        PlayerEvents.EVENT_CYBRAN_WINS,
    ),
    PlayerEventMetric(
        Factions.UEF.to_name().capitalize(),
        PlayerEvents.EVENT_UEF_PLAYS,
        PlayerEvents.EVENT_UEF_WINS,
    ),
    PlayerEventMetric(
        Factions.SERAPHIM.to_name().capitalize(),
        PlayerEvents.EVENT_SERAPHIM_PLAYS,
        PlayerEvents.EVENT_SERAPHIM_WINS,
    ),
)

BUILT_LOST_METRICS = (
    PlayerEventMetric(
        "Air",
        PlayerEvents.EVENT_BUILT_AIR_UNITS,
        PlayerEvents.EVENT_LOST_AIR_UNITS,
    ),
    PlayerEventMetric(
        "Land",
        PlayerEvents.EVENT_BUILT_LAND_UNITS,
        PlayerEvents.EVENT_LOST_LAND_UNITS,
    ),
    PlayerEventMetric(
        "Naval",
        PlayerEvents.EVENT_BUILT_NAVAL_UNITS,
        PlayerEvents.EVENT_LOST_NAVAL_UNITS,
    ),
    PlayerEventMetric(
        "Tech 1",
        PlayerEvents.EVENT_BUILT_TECH_1_UNITS,
        PlayerEvents.EVENT_LOST_TECH_1_UNITS,
    ),
    PlayerEventMetric(
        "Tech 2",
        PlayerEvents.EVENT_BUILT_TECH_2_UNITS,
        PlayerEvents.EVENT_LOST_TECH_2_UNITS,
    ),
    PlayerEventMetric(
        "Tech 3",
        PlayerEvents.EVENT_BUILT_TECH_3_UNITS,
        PlayerEvents.EVENT_LOST_TECH_3_UNITS,
    ),
    PlayerEventMetric(
        "Engineers",
        PlayerEvents.EVENT_BUILT_ENGINEERS,
        PlayerEvents.EVENT_LOST_ENGINEERS,
    ),
)

EXPERIMENTALS_BUILT_LOST_METRICS = (
    PlayerEventMetric(
        "Experimentals",
        PlayerEvents.EVENT_BUILT_EXPERIMENTALS,
        PlayerEvents.EVENT_LOST_EXPERIMENTALS,
    ),
)
