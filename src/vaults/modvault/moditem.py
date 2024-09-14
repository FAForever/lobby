from __future__ import annotations

import os
import urllib
from typing import TYPE_CHECKING

from src import util
from src.api.models.Mod import Mod
from src.api.models.ModVersion import ModType
from src.vaults.modvault import utils
from src.vaults.vaultitem import VaultListItem

if TYPE_CHECKING:
    from src.vaults.modvault.modvault import ModVault


class ModListItem(VaultListItem):
    def __init__(self, parent: ModVault, item_info: Mod, *args, **kwargs) -> None:
        super().__init__(parent, item_info, *args, **kwargs)
        self.html = str(util.THEME.readfile("vaults/modvault/modinfo.qthtml"))
        self._preview_dler.set_target_dir(util.MOD_PREVIEW_DIR)
        self.update()

    def should_be_visible(self) -> bool:
        p = self.parent
        if p.showType == "all":
            return True
        elif p.showType == "ui":
            return self.item_version.modtype == ModType.UI
        elif p.showType == "sim":
            return self.item_version.modtype == ModType.SIM
        elif p.showType == "yours":
            return self.item_info.author == self.parent.client.login
        elif p.showType == "installed":
            return self.item_version.uid in self.parent.uids
        else:
            return True

    def update(self) -> None:
        if thumbstr := self.item_version.thumbnail_url:
            name = os.path.basename(urllib.parse.unquote(thumbstr))
            img = utils.getIcon(name)
            if img:
                self.set_item_icon(img, False)
            else:
                self._preview_dler.download(name, self._item_dl_request, thumbstr)
        else:
            self.set_item_icon("games/unknown_map.png")
        super().update()

    def update_visibility(self) -> None:
        if self.item_version.modtype == ModType.UI:
            modtype = "UI mod"
        else:
            modtype = ""

        if self.item_version.uid in self.parent.uids:
            color = "green"
        else:
            color = "white"

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
                modtype=modtype,
                author=self.item_info.author,
            ),
        )
        super().update_visibility()
