"""Message bus module for decoupled channel-agent communication."""

from zuberabot.bus.events import InboundMessage, OutboundMessage
from zuberabot.bus.queue import MessageBus

__all__ = ["MessageBus", "InboundMessage", "OutboundMessage"]
