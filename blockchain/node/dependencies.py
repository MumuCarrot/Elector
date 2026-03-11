import os
from node.core.settings import settings
from node.services.node import Node

_blockchain_instance: Node | None = None


def get_blockchain() -> Node:
    global _blockchain_instance
    if _blockchain_instance is None:
        
        actual_host = os.environ.get("NODE_ACTUAL_HOST", settings.app.APP_HOST)
        actual_port = int(os.environ.get("NODE_ACTUAL_PORT", settings.app.APP_PORT))
        
        _blockchain_instance = Node(
            host=actual_host,
            port=actual_port
        )
    return _blockchain_instance