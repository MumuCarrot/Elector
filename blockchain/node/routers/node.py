from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from node.dependencies import get_blockchain
from node.schemas.node import RegisterNodeRequest
from node.services.node import Node

router = APIRouter(tags=["node"])


@router.post("/register")
async def register_node(
    data: RegisterNodeRequest,
    blockchain: Node = Depends(get_blockchain),
):
    """Registers one or more ``host:port`` peers and merges neighbor gossip.

    Args:
        data: List of node addresses to add.
        blockchain: Injected node.

    Returns:
        JSONResponse: 201 with updated peer list.

    """
    for node_address in data.nodes:
        blockchain.register_node(node_address)

    await blockchain.gossip_neighbors(ignore_nodes=data.nodes)

    return JSONResponse(
        content={
            "message": "New nodes have been added",
            "total_nodes": list(blockchain.nodes),
        },
        status_code=201,
    )


@router.post("/resolve")
async def resolve_conflicts(blockchain: Node = Depends(get_blockchain)):
    """Fetches longer valid chains from peers and replaces local DB if needed.

    Returns:
        JSONResponse: Message plus either the new or current chain.

    """
    replaced = await blockchain.resolve_conflicts(blockchain.session)
    chain = await blockchain.get_chain(blockchain.session)
    if replaced:
        return JSONResponse(
            content={
                "message": "Our chain was replaced",
                "new_chain": [b.model_dump(mode="json") for b in chain],
            },
            status_code=200,
        )
    return JSONResponse(
        content={
            "message": "Our chain is authoritative",
            "chain": [b.model_dump(mode="json") for b in chain],
        },
        status_code=200,
    )
