"""
Base plugin class for ARM plugins
Each plugin should handle specific channel tasks
"""

from abc import ABC, abstractmethod
from typing import Any
from ..core.message_types import NormalizedMessage, ResponseMessage

class BasePlugin(ABC):
    """
    Abstract base class for ARM channel plugins
    Each plugin must implement these methods
    """

    @abstractmethod
    def normalize(self, raw_data: Any) -> NormalizedMessage:
        """
        Convert raw incoming data to a standardized NormalizedMessage
        :param raw_data: The raw input from the channel
        :return: NormalizedMessage
        """
        pass

    @abstractmethod
    def respond(self, message: NormalizedMessage, response: ResponseMessage):
        """
        Send a response back through the channel
        :param message: The original normalized message
        :param response: The response to send
        """
        pass
