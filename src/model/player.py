from PyQt6.QtCore import pyqtSignal

from src.model.modelitem import ModelItem
from src.model.rating import Rating
from src.model.rating import RatingType
from src.model.transaction import transactional


class Player(ModelItem):
    newCurrentGame = pyqtSignal(object, object, object)

    """
    Represents a player the client knows about.
    """

    def __init__(
        self,
        id_,
        login,
        ratings={},
        avatar=None,
        country=None,
        clan=None,
        league=None,
        **kwargs
    ):
        ModelItem.__init__(self)
        """
        Initialize a Player
        """
        # Required fields
        # Login should be mutable, but we look up things by login right now
        self.id = int(id_)
        self.login = login

        self.add_field("avatar", avatar)
        self.add_field("country", country)
        self.add_field("clan", clan)
        self.add_field("league", league)
        self.add_field("ratings", ratings)

        # The game the player is currently playing
        self._currentGame = None

    @property
    def id_key(self):
        return self.id

    def copy(self):
        p = Player(self.id, self.login, **self.field_dict)
        p.currentGame = self.currentGame
        return p

    @transactional
    def update(self, **kwargs):
        _transaction = kwargs.pop("_transaction")

        old_data = self.copy()
        ModelItem.update(self, **kwargs)
        self.emit_update(old_data, _transaction)

    def __index__(self):
        return self.id

    @property
    def global_estimate(self):
        return self.rating_estimate()

    @property
    def ladder_estimate(self):
        return self.rating_estimate(RatingType.LADDER.value)

    @property
    def global_rating_mean(self):
        return self.rating_mean()

    @property
    def global_rating_deviation(self):
        return self.rating_deviation()

    @property
    def ladder_rating_mean(self):
        return self.rating_mean(RatingType.LADDER.value)

    @property
    def ladder_rating_deviation(self):
        return self.rating_deviation(RatingType.LADDER.value)

    @property
    def number_of_games(self):
        count = 0
        for rating_type in self.ratings:
            count += self.ratings[rating_type].get("number_of_games", 0)
        return count

    def rating_estimate(self, rating_type=RatingType.GLOBAL.value):
        """
        Get the conservative estimate of the player's trueskill rating
        """
        try:
            mean = self.ratings[rating_type]["rating"][0]
            deviation = self.ratings[rating_type]["rating"][1]
            rating = Rating(mean, deviation)
            return int(max(0, rating.displayed()))
        except (KeyError, IndexError):
            return 0

    def rating_mean(self, rating_type=RatingType.GLOBAL.value):
        try:
            return round(self.ratings[rating_type]["rating"][0])
        except (KeyError, IndexError):
            return 1500

    def rating_deviation(self, rating_type=RatingType.GLOBAL.value):
        try:
            return round(self.ratings[rating_type]["rating"][1])
        except (KeyError, IndexError):
            return 500

    def game_count(self, rating_type=RatingType.GLOBAL.value):
        try:
            return int(self.ratings[rating_type]["number_of_games"])
        except KeyError:
            return 0

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return (
            "Player(id={}, login={}, global_rating={}, ladder_rating={})"
        ).format(
            self.id,
            self.login,
            (self.global_rating_mean, self.global_rating_deviation),
            (self.ladder_rating_mean, self.ladder_rating_deviation),
        )

    @property
    def currentGame(self):
        return self._currentGame

    @transactional
    def set_currentGame(self, game, _transaction=None):
        if self.currentGame == game:
            return
        old = self._currentGame
        self._currentGame = game
        _transaction.emit(self.newCurrentGame, self, game, old)

    @currentGame.setter
    def currentGame(self, val):
        # CAVEAT: this will emit signals immediately!
        self.set_currentGame(val)
