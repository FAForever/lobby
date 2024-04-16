import os
import urllib

import util
from vaults.modvault import utils
from vaults.vaultitem import VaultItem


class ModItem(VaultItem):
    def __init__(self, parent, uid, *args, **kwargs):
        VaultItem.__init__(self, parent, *args, **kwargs)

        self.formatterItem = str(
            util.THEME.readfile("vaults/modvault/modinfo.qthtml"),
        )

        self.uid = uid
        self.author = ""
        self.thumbstr = ""
        self.isuidmod = False
        self.uploadedbyuser = False
        self._preview_dler.set_target_dir(util.MOD_PREVIEW_DIR)

    def shouldBeVisible(self):
        p = self.parent
        if p.showType == "all":
            return True
        elif p.showType == "ui":
            return self.isuimod
        elif p.showType == "sim":
            return not self.isuimod
        elif p.showType == "yours":
            return self.uploadedbyuser
        elif p.showType == "installed":
            return self.uid in self.parent.uids
        else:
            return True

    def update(self, item_dict):
        self.name = item_dict["name"]
        self.description = item_dict["description"]
        self.version = item_dict["version"]
        self.author = item_dict["author"]
        self.rating = item_dict["rating"]
        self.reviews = item_dict["reviews"]
        self.date = item_dict['date'][:10]
        self.isuimod = item_dict["ui"]
        self.link = item_dict["link"]
        self.thumbstr = item_dict["thumbnail"]
        self.uploadedbyuser = (self.author == self.parent.client.login)

        if self.thumbstr == "":
            self.setItemIcon("games/unknown_map.png")
        else:
            name = os.path.basename(urllib.parse.unquote(self.thumbstr))
            img = utils.getIcon(name)
            if img:
                self.setItemIcon(img, False)
            else:
                self._preview_dler.download(name, self._item_dl_request, self.thumbstr)

        VaultItem.update(self)

    def updateVisibility(self):
        if self.isuimod:
            self.itemType_ = "UI mod"
        if self.uid in self.parent.uids:
            self.color = "green"
        else:
            self.color = "white"

        self.setText(
            self.formatterItem.format(
                color=self.color,
                version=self.version,
                title=self.name,
                description=self.trimmedDescription,
                rating=self.rating,
                reviews=self.reviews,
                date=self.date,
                modtype=self.itemType_,
                author=self.author,
            ),
        )

        VaultItem.updateVisibility(self)
