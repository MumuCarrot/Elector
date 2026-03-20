from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from node.dependencies import get_blockchain, get_session
from node.schemas.gossip import GossipChainRequestSchema
from node.schemas.transaction import Transaction
from node.services.node import Node

router = APIRouter()


@router.post("/transactions")
async def gossip_transactions(
    transactions: list[Transaction],
    blockchain: Node = Depends(get_blockchain),
    session: AsyncSession = Depends(get_session),
):
    """Merges received transactions into the mempool and echoes the full mempool.

    Args:
        transactions: Incoming vote transactions from a peer.
        blockchain: Injected node.
        session: Request DB session.

    Returns:
        JSONResponse: 201 with all mempool transactions.

    """
    await blockchain.add_to_mempool(session, transactions)

    all_transactions = blockchain.mempool.get_all()
    return JSONResponse(
        content={
            "message": "Transactions received",
            "transactions": [tx.model_dump(mode="json") for tx in all_transactions],
        },
        status_code=201,
    )


@router.post("/chain")
async def gossip_chain(
    ctx: GossipChainRequestSchema,
    blockchain: Node = Depends(get_blockchain),
):
    """Replaces the local chain if the peer sends a longer valid chain.

    Args:
        ctx: Chain and transaction ids from peer.
        blockchain: Injected node (uses ``blockchain.session``).

    Returns:
        JSONResponse: 200 on replace, 400 with current chain if rejected.

    """
    session = blockchain.session
    current_chain = await blockchain.get_chain(session)
    if len(ctx.chain) > len(current_chain) and await blockchain.valid_chain(chain=ctx.chain):
        await blockchain.replace_chain_with(session, ctx.chain, ctx.tx_ids)
        return JSONResponse(
            content={"message": "Chain updated successfully"},
            status_code=200,
        )
    return JSONResponse(
        content={
            "message": "Received chain is not valid or not longer",
            "chain": [b.model_dump(mode="json") for b in current_chain],
        },
        status_code=400,
    )


@router.post("/neighbors")
async def gossip_neighbors(
    nodes: list[str],
    blockchain: Node = Depends(get_blockchain),
):
    """Merges peer-reported neighbor addresses into the local peer set.

    Args:
        nodes: Known peers from the sender.
        blockchain: Injected node.

    Returns:
        JSONResponse: 201 with updated ``nodes`` list.

    """
    for node_address in nodes:
        if not blockchain.is_registered(node_address):
            blockchain.register_node(node_address)
    return JSONResponse(
        content={
            "message": "Neighbors updated successfully",
            "nodes": list(blockchain.nodes),
        },
        status_code=201,
    )
