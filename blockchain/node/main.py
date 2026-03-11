from fastapi import FastAPI

from node.routers.health import router as health_router
from node.routers.blockchain import router as blockchain_router
from node.routers.node import router as node_router
from node.routers.gossip import router as gossip_router

app = FastAPI()


app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(blockchain_router, prefix="/blockchain", tags=["blockchain"])
app.include_router(node_router, prefix="/nodes", tags=["nodes"])
app.include_router(gossip_router, prefix="/gossip", tags=["gossip"])