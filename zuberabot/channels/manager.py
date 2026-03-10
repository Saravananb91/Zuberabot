"""Channel manager for coordinating chat channels."""

import asyncio
from typing import Any

from loguru import logger

from zuberabot.bus.events import OutboundMessage
from zuberabot.bus.queue import MessageBus
from zuberabot.channels.base import BaseChannel
from zuberabot.config.schema import Config


class ChannelManager:
    """
    Manages WhatsApp channel and coordinates message routing.
    
    Responsibilities:
    - Initialize WhatsApp channel
    - Start/stop channel
    - Route outbound messages
    """
    
    def __init__(self, config: Config, bus: MessageBus):
        self.config = config
        self.bus = bus
        self.whatsapp_channel: BaseChannel | None = None
        self._dispatch_task: asyncio.Task | None = None
        
        self._init_channel()
    
    def _init_channel(self) -> None:
        """Initialize WhatsApp channel based on config."""
        
        if self.config.channels.whatsapp.enabled:
            try:
                from zuberabot.channels.whatsapp import WhatsAppChannel
                self.whatsapp_channel = WhatsAppChannel(
                    self.config.channels.whatsapp, self.bus
                )
                logger.info("WhatsApp channel enabled")
            except ImportError as e:
                logger.warning(f"WhatsApp channel not available: {e}")
                logger.error("Install WhatsApp bridge dependencies to use WhatsApp channel")
    
    async def start_all(self) -> None:
        """Start WhatsApp channel and the outbound dispatcher."""
        if not self.whatsapp_channel:
            logger.warning("WhatsApp channel not enabled")
            return
        
        # Start outbound dispatcher
        self._dispatch_task = asyncio.create_task(self._dispatch_outbound())
        
        # Start WhatsApp channel
        logger.info("Starting WhatsApp channel...")
        await self.whatsapp_channel.start()
    
    async def stop_all(self) -> None:
        """Stop WhatsApp channel and the dispatcher."""
        logger.info("Stopping WhatsApp channel...")
        
        # Stop dispatcher
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        
        # Stop WhatsApp channel
        if self.whatsapp_channel:
            try:
                await self.whatsapp_channel.stop()
                logger.info("Stopped WhatsApp channel")
            except Exception as e:
                logger.error(f"Error stopping WhatsApp channel: {e}")
    
    async def _dispatch_outbound(self) -> None:
        """Dispatch outbound messages to WhatsApp channel."""
        logger.info("Outbound dispatcher started")
        
        while True:
            try:
                msg = await asyncio.wait_for(
                    self.bus.consume_outbound(),
                    timeout=1.0
                )
                
                # Send to WhatsApp (msg.channel should be "whatsapp")
                if self.whatsapp_channel:
                    try:
                        await self.whatsapp_channel.send(msg)
                    except Exception as e:
                        logger.error(f"Error sending to WhatsApp: {e}")
                else:
                    logger.error("WhatsApp channel not available")
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    def get_status(self) -> dict[str, Any]:
        """Get WhatsApp channel status."""
        if self.whatsapp_channel:
            return {
                "whatsapp": {
                    "enabled": True,
                    "running": self.whatsapp_channel.is_running
                }
            }
        return {"whatsapp": {"enabled": False, "running": False}}
    
    @property
    def is_running(self) -> bool:
        """Check if WhatsApp channel is running."""
        return self.whatsapp_channel.is_running if self.whatsapp_channel else False
