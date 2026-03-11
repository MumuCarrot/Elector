from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.responses import JSONResponse

from node.dependencies import get_blockchain
from node.schemas.gossip import GossipChainRequestSchema
from node.schemas.transaction import Transaction
from node.services.node import Node

router = APIRouter()

@router.post("/transactions")
async def gossip_transactions(transactions: list[Transaction],
                        blockchain: Node = Depends(get_blockchain)):
    blockchain.mempool.new_transactions(transactions)

    all_transactions = blockchain.mempool.get_all()
    return JSONResponse(
        content={
            "message": "Transactions received",
            "transactions": [tx.model_dump() for tx in all_transactions]
        },
        status_code=201
    )


@router.post("/chain")
async def gossip_chain(ctx: GossipChainRequestSchema,
                 blockchain: Node = Depends(get_blockchain)):
    if len(ctx.chain) > len(blockchain.chain) and blockchain.valid_chain(ctx.chain):
        blockchain.chain = ctx.chain
        blockchain.mempool.remove_all(ctx.tx_ids)
        return JSONResponse(
            content={"message": "Chain updated successfully"},
            status_code=200
        )
    else:
        return JSONResponse(
            content={
                "message": "Received chain is not valid or not longer",
                "chain": [block.model_dump() for block in blockchain.chain]
            },
            status_code=400
        )


@router.post("/neighbors")
async def gossip_neighbors(nodes: list[str],
                     blockchain: Node = Depends(get_blockchain)):
    for node_address in nodes:
        if not blockchain.is_registered(node_address):
            blockchain.register_node(node_address)
    return JSONResponse(
        content={
            "message": "Neighbors updated successfully",
            "nodes": list(blockchain.nodes)
        },
        status_code=201
    )