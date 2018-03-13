import time
import html
from PyQt5.QtCore import QObject, pyqtSignal

from chat.channel_widget import ChannelWidget
from chat.chatter_model import ChatterModel, ChatterEventFilter, \
    ChatterItemDelegate, ChatterSortFilterModel
from chat.chatter_menu import ChatterMenu
from model.chat.channel import ChannelType
from model.chat.chatline import ChatLineType
from util.magic_dict import MagicDict
from downloadManager import DownloadRequest


class ChannelView(QObject):
    privmsg_requested = pyqtSignal(str)

    def __init__(self, channel, controller, widget, chatter_list_view,
                 lines_view):
        QObject.__init__(self)
        self._channel = channel
        self._controller = controller
        self._chatter_list_view = chatter_list_view
        self._lines_view = lines_view
        self.widget = widget

        self.widget.line_typed.connect(self._at_line_typed)
        self._chatter_list_view.double_clicked.connect(
            self._at_chatter_double_clicked)
        if self._channel.id_key.type == ChannelType.PRIVATE:
            self.widget.show_chatter_list(False)

        self._channel.added_chatter.connect(self._update_chatter_count)
        self._channel.removed_chatter.connect(self._update_chatter_count)
        self._update_chatter_count()

    def _update_chatter_count(self):
        text = "{} users (type to filter)".format(len(self._channel.chatters))
        self.widget.set_nick_edit_label(text)

    @classmethod
    def build(cls, channel, controller, **kwargs):
        widget = ChannelWidget.build(channel, **kwargs)
        lines_view = ChatAreaView.build(channel, widget, **kwargs)
        chatter_list_view = ChattersView.build(channel, widget, **kwargs)
        return cls(channel, controller, widget, chatter_list_view, lines_view)

    @classmethod
    def builder(cls, controller, **kwargs):
        def make(channel):
            return cls.build(channel, controller, **kwargs)
        return make

    def _at_line_typed(self, line):
        self._controller.send_message(self._channel.id_key, line)

    def _at_chatter_double_clicked(self, data):
        self.privmsg_requested.emit(data.chatter.name)


class ChatAreaView:
    def __init__(self, channel, widget, metadata_builder, avatar_adder,
                 formatter):
        self._channel = channel
        self._widget = widget
        self._metadata_builder = metadata_builder
        self._channel.lines.added.connect(self._add_line)
        self._meta_lines = []
        self._avatar_adder = avatar_adder
        self._formatter = formatter

    @classmethod
    def build(cls, channel, widget, **kwargs):
        metadata_builder = ChatLineMetadata.builder(**kwargs)
        avatar_adder = ChatAvatarPixAdder.build(widget, **kwargs)
        formatter = ChatLineFormatter.build(**kwargs)
        return cls(channel, widget, metadata_builder, avatar_adder, formatter)

    def _add_line(self, number):
        for line in self._channel.lines[-number:]:
            data = self._metadata_builder(line, self._channel)
            if data.meta.player.avatar.url:
                self._avatar_adder.add_avatar(data.meta.player.avatar.url())
            self._meta_lines.append(data)
            text = self._formatter.format(data)
            self._widget.append_line(text)


class ChatAvatarPixAdder:
    def __init__(self, widget, avatar_dler):
        self._avatar_dler = avatar_dler
        self._widget = widget
        self._requests = {}

    @classmethod
    def build(cls, widget, avatar_dler, **kwargs):
        return cls(widget, avatar_dler)

    def add_avatar(self, url):
        avatar_pix = self._avatar_dler.avatars.get(url, None)
        if avatar_pix is not None:
            self._add_avatar_resource(url, avatar_pix)
        elif url not in self._requests:
            req = DownloadRequest()
            req.done.connect(self._add_avatar_resource)
            self._requests[url] = req
            self._avatar_dler.download_avatar(url, req)

    def _add_avatar_resource(self, url, pix):
        if url in self._requests:
            del self._requests[url]
        self._widget.add_avatar_resource(url, pix)


class ChatLineMetadata:
    def __init__(self, line, channel, channelchatterset, me, user_relations):
        self.line = line
        self._make_metadata(channel, channelchatterset, me, user_relations)

    @classmethod
    def builder(cls, channelchatterset, me, user_relations, **kwargs):
        def make(line, channel):
            return cls(line, channel, channelchatterset, me,
                       user_relations.model)
        return make

    def _make_metadata(self, channel, channelchatterset, me, user_relations):
        self.meta = MagicDict()
        cc = channelchatterset.get((channel.id_key, self.line.sender), None)
        chatter = None
        player = None
        if cc is not None:
            chatter = cc.chatter
            player = chatter.player

        self._chatter_metadata(cc, chatter)
        self._player_metadata(player)
        self._relation_metadata(chatter, player, me, user_relations)
        self._mention_metadata(me)

    def _chatter_metadata(self, cc, chatter):
        if cc is None:
            return
        cmeta = self.meta.put("chatter")
        cmeta.is_mod = cc.is_mod()

    def _player_metadata(self, player):
        if player is None:
            return
        self.meta.put("player")
        self._avatar_metadata(player.avatar)

    def _relation_metadata(self, chatter, player, me, user_relations):
        name = None if chatter is None else chatter.name
        id_ = None if player is None else player.id
        self.meta.is_friend = user_relations.is_friend(id_, name)
        self.meta.is_foe = user_relations.is_foe(id_, name)
        self.meta.is_me = me.player is not None and me.player.login == name
        self.meta.is_clannie = me.is_clannie(id_)

    def _mention_metadata(self, me):
        self.meta.mentions_me = (me.login is not None and
                                 me.login in self.line.text)

    def _avatar_metadata(self, ava):
        if ava is None:
            return
        tip = ava.get("tooltip", "")
        url = ava.get("url", None)

        self.meta.player.put("avatar")
        self.meta.player.avatar.tip = tip
        if url is not None:
            self.meta.player.avatar.url = url


class ChatLineFormatter:
    def __init__(self, theme):
        self._set_theme(theme)
        self._last_timestamp = None

    @classmethod
    def build(cls, theme, **kwargs):
        return cls(theme)

    def _set_theme(self, theme):
        self._chatline_template = theme.readfile("chat/chatline.qhtml")
        self._avatar_template = theme.readfile("chat/chatline_avatar.qhtml")

    def _line_tags(self, data):
        line = data.line
        meta = data.meta
        if line.type == ChatLineType.NOTICE:
            yield "notice"
        if not self._check_timestamp(line.time):
            yield "notimestamp"
        if meta.chatter:
            yield "chatter"
        if meta.player:
            yield "player"
        if meta.is_friend and meta.is_friend():
            yield "friend"
        if meta.is_foe and meta.is_foe():
            yield "foe"
        if meta.is_me and meta.is_me():
            yield "me"
        if meta.is_clannie and meta.is_clannie():
            yield "clannie"
        if meta.is_mod and meta.is_mod():
            yield "mod"
        if meta.mentions_me and meta.mentions_me():
            yield "mentions_me"
        if meta.player.avatar and meta.player.avatar():
            yield "avatar"

    def format(self, data):
        tags = " ".join(self._line_tags(data))
        if data.meta.player.avatar.url:
            ava_meta = data.meta.player.avatar
            avatar_url = ava_meta.url()
            avatar_tip = ava_meta.tip() if ava_meta.tip else ""
            avatar = self._avatar_template.format(
                url=avatar_url,
                tip=avatar_tip)
        else:
            avatar = ""

        return self._chatline_template.format(
            time=time.strftime('%H:%M', time.localtime(data.line.time)),
            sender=html.escape(data.line.sender),
            text=html.escape(data.line.text),
            avatar=avatar,
            tags=tags)

    def _check_timestamp(self, stamp):
        local = time.localtime(stamp)
        new_stamp = (self._last_timestamp is None or
                     local.tm_hour != self._last_timestamp.tm_hour or
                     local.tm_min != self._last_timestamp.tm_min)
        if new_stamp:
            self._last_timestamp = local
        return new_stamp


class ChattersView:
    def __init__(self, widget, delegate, model, event_filter):
        self.delegate = delegate
        self.model = model
        self.event_filter = event_filter
        self.widget = widget

        widget.set_chatter_delegate(self.delegate)
        widget.set_chatter_model(self.model)
        widget.set_chatter_event_filter(self.event_filter)
        widget.chatter_list_resized.connect(self.at_chatter_list_resized)

    def at_chatter_list_resized(self, size):
        self.delegate.update_width(size)

    @classmethod
    def build(cls, channel, widget, user_relations, **kwargs):
        model = ChatterModel.build(
            channel, relation_trackers=user_relations.trackers, **kwargs)
        sort_filter_model = ChatterSortFilterModel.build(
            model, user_relations=user_relations.model, **kwargs)

        chatter_menu = ChatterMenu.build(**kwargs)
        delegate = ChatterItemDelegate.build(**kwargs)
        event_filter = ChatterEventFilter.build(delegate, chatter_menu,
                                                **kwargs)

        return cls(widget, delegate, sort_filter_model, event_filter)

    @property
    def double_clicked(self):
        return self.event_filter.double_clicked