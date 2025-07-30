# Marina Active Response Module (ARM)
# Extensible multi-channel automated response system

from .core.active_response_manager import ActiveResponseManager
from .core.message_types import NormalizedMessage, MessageMetadata
from .plugins.base_plugin import BasePlugin
from .plugins.email_plugin import EmailPlugin

__version__ = "1.0.0"
__all__ = [
    "ActiveResponseManager",
    "NormalizedMessage", 
    "MessageMetadata",
    "BasePlugin",
    "EmailPlugin"
]
