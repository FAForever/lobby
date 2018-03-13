from chat.chat_widget import ChatWidget
from chat.channel_view import ChannelView
from model.chat.channel import ChannelID, ChannelType


class ChatView:
    def __init__(self, target_viewed_channel, model, controller, widget,
                 channel_view_builder):
        self._target_viewed_channel = None
        self._model = model
        self._controller = controller
        self.widget = widget
        self._channel_view_builder = channel_view_builder
        self._channels = {}
        self._model.channels.added.connect(self._add_channel)
        self._model.channels.removed.connect(self._remove_channel)
        self._model.new_server_message.connect(self._new_server_message)
        self.widget.channel_quit_request.connect(self._at_channel_quit_request)
        self._add_channels()

        self.target_viewed_channel = target_viewed_channel

    @classmethod
    def build(cls, target_viewed_channel, model, controller, **kwargs):
        chat_widget = ChatWidget.build(**kwargs)
        channel_view_builder = ChannelView.builder(
            controller, channelchatterset=model.channelchatters, **kwargs)
        return cls(target_viewed_channel, model, controller, chat_widget,
                   channel_view_builder)

    def _add_channels(self):
        for channel in self._model.channels.values():
            self._add_channel(channel)

    def _add_channel(self, channel):
        if channel.id_key in self._channels:
            return
        view = self._channel_view_builder(channel)
        view.privmsg_requested.connect(self._request_privmsg)
        self._channels[channel.id_key] = view
        self.widget.add_channel(view.widget, channel.id_key.name)
        self._try_to_join_target_channel()

    def _remove_channel(self, channel):
        if channel.id_key not in self._channels:
            return
        view = self._channels[channel.id_key]
        view.privmsg_requested.disconnect(self._request_privmsg)
        self.widget.remove_channel(view.widget)
        del self._channels[channel.id_key]

    def _new_server_message(self, msg):
        self.widget.write_server_message(msg)

    def _at_channel_quit_request(self, cid):
        self._controller.leave_channel(cid, "tab closed")

    def _request_privmsg(self, name):
        cid = ChannelID(ChannelType.PRIVATE, name)
        self._controller.join_channel(cid)
        self.target_viewed_channel = cid

    @property
    def target_viewed_channel(self):
        return self._target_viewed_channel

    @target_viewed_channel.setter
    def target_viewed_channel(self, value):
        self._target_viewed_channel = value
        self._try_to_join_target_channel()

    def _try_to_join_target_channel(self):
        if self._target_viewed_channel is None:
            return
        view = self._channels.get(self._target_viewed_channel, None)
        if view is None:
            return
        self.widget.switch_to_channel(view.widget)
        self._target_viewed_channel = None