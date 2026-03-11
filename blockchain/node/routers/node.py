from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from node.dependencies import get_blockchain
from node.schemas.node import RegisterNodeRequest
from node.services.node import Node

router = APIRouter(tags=["node"])


@router.post("/register")
async def register_node(
    data: RegisterNodeRequest,
    blockchain: Node = Depends(get_blockchain)
):
    for node_address in data.nodes:
        blockchain.register_node(node_address)

    # gossip neighbors
    blockchain.gossip_neighbors(ignore_nodes=data.nodes)

    return JSONResponse(
        content={
            'message': f'New nodes have been added',
            'total_nodes': list(blockchain.nodes)
        },
        status_code=201
    )


@router.post("/resolve")
async def resolve_conflicts(blockchain: Node = Depends(get_blockchain)):
    replaced = blockchain.resolve_conflicts()
    
    if replaced:
        return JSONResponse(
            content={
                'message': 'Our chain was replaced',
                'new_chain': [block.model_dump() for block in blockchain.chain]
            },
            status_code=200
        )
    else:
        return JSONResponse(
            content={
                'message': 'Our chain is authoritative',
                'chain': [block.model_dump() for block in blockchain.chain]
            },
            status_code=200
        )