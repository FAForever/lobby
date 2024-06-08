from __future__ import annotations

from typing import TYPE_CHECKING

import util
from api.models.Map import Map
from fa import maps
from mapGenerator import mapgenUtils
from vaults.vaultitem import VaultListItem

if TYPE_CHECKING:
    from vaults.mapvault.mapvault import MapVault


class MapListItem(VaultListItem):
    def __init__(self, parent: MapVault, item_info: Map, *args, **kwargs) -> None:
        super().__init__(parent, item_info, *args, **kwargs)
        self.html = str(util.THEME.readfile("vaults/mapvault/mapinfo.qthtml"))
        self._preview_dler.set_target_dir(util.MAP_PREVIEW_SMALL_DIR)
        self.update()

    def update(self) -> None:
        if thumbnail := maps.preview(self.item_version.folder_name):
            self.setIcon(thumbnail)
        else:
            if self.item_version.thumbnail_url_small == "":
                if mapgenUtils.isGeneratedMap(self.item_version.folder_name):
                    self.setItemIcon("games/generated_map.png")
                else:
                    self.setItemIcon("games/unknown_map.png")
            else:
                self._preview_dler.download(
                    f"{self.item_version.folder_name}.png",
                    self._item_dl_request,
                    self.item_version.thumbnail_url_small,
                )
        VaultListItem.update(self)

    def should_be_visible(self) -> bool:
        p = self.parent
        if p.showType == "all":
            return True
        elif p.showType == "unranked":
            return not self.item_version.ranked
        elif p.showType == "ranked":
            return self.item_version.ranked
        elif p.showType == "installed":
            return maps.isMapAvailable(self.item_version.folder_name)
        else:
            return True

    def update_visibility(self):
        if maps.isMapAvailable(self.item_version.folder_name):
            color = "green"
        else:
            color = "white"

        maptype = "" if self.item_version.ranked else "Unranked map"
        if self.item_info.reviews_summary is None:
            score = reviews = "-"
        else:
            score = round(self.item_info.reviews_summary.average_score, 1)
            reviews = self.item_info.reviews_summary.num_reviews

        self.setText(
            self.html.format(
                color=color,
                version=self.item_version.version,
                title=self.item_info.display_name,
                description=self.item_version.description,
                rating=score,
                reviews=reviews,
                date=util.utctolocal(self.item_version.create_time),
                modtype=maptype,
                height=self.item_version.size.height_km,
                width=self.item_version.size.width_km,
            ),
        )
        super().update_visibility()

    def __lt__(self, other: MapListItem) -> bool:
        if self.parent.sortType == "size":
            return self._lt_size(other)
        return super().__lt__(other)

    def _lt_size(self, other: MapListItem) -> bool:
        if self.item_version.size == other.item_version.size:
            return self._lt_alphabetical(other)
        return self.item_version.size < other.item_version.size
