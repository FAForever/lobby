import util
from fa import maps
from mapGenerator import mapgenUtils
from vaults.vaultitem import VaultItem


class MapItem(VaultItem):
    def __init__(self, parent, folderName, *args, **kwargs):
        VaultItem.__init__(self, parent, *args, **kwargs)

        self.formatterItem = str(
            util.THEME.readfile("vaults/mapvault/mapinfo.qthtml"),
        )

        self.height = 0
        self.width = 0
        self.maxPlayers = 0
        self.thumbnail = None
        self.unranked = False
        self.folderName = folderName
        self.thumbstrSmall = ""
        self.thumbnailLarge = ""
        self._preview_dler.set_target_dir(util.MAP_PREVIEW_SMALL_DIR)

    def update(self, item_dict):
        self.name = maps.getDisplayName(item_dict["folderName"])
        self.description = item_dict["description"]
        self.version = item_dict["version"]
        self.rating = item_dict["rating"]
        self.reviews = item_dict["reviews"]

        self.maxPlayers = item_dict["maxPlayers"]
        self.height = int(item_dict["height"] / 51.2)
        self.width = int(item_dict["width"] / 51.2)

        self.folderName = item_dict["folderName"]
        self.date = item_dict['date'][:10]
        self.unranked = not item_dict["ranked"]
        self.link = item_dict["link"]
        self.thumbstrSmall = item_dict["thumbnailSmall"]
        self.thumbnailLarge = item_dict["thumbnailLarge"]

        self.thumbnail = maps.preview(self.folderName)
        if self.thumbnail:
            self.setIcon(self.thumbnail)
        else:
            if self.thumbstrSmall == "":
                if mapgenUtils.isGeneratedMap(self.folderName):
                    self.setItemIcon("games/generated_map.png")
                else:
                    self.setItemIcon("games/unknown_map.png")
            else:
                self._preview_dler.download(
                    f"{self.folderName}.png",
                    self._item_dl_request,
                    self.thumbstrSmall,
                )
        VaultItem.update(self)

    def shouldBeVisible(self):
        p = self.parent
        if p.showType == "all":
            return True
        elif p.showType == "unranked":
            return self.unranked
        elif p.showType == "ranked":
            return not self.unranked
        elif p.showType == "installed":
            return maps.isMapAvailable(self.folderName)
        else:
            return True

    def updateVisibility(self):
        if self.unranked:
            self.itemType_ = "Unranked map"
        if maps.isMapAvailable(self.folderName):
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
                height=self.height,
                width=self.width,
            ),
        )

        VaultItem.updateVisibility(self)
