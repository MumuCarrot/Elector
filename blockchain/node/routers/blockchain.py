import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from node.dependencies import get_blockchain, get_session
from node.schemas.block import Block
from node.schemas.transaction import Transaction
from node.services.node import Node

logger = logging.getLogger(__name__)
router = APIRouter(tags=["blockchain"])

node_identifier = str(uuid4()).replace("-", "")


@router.post("/transactions/new")
async def new_transaction(
    data: Transaction,
    blockchain: Node = Depends(get_blockchain),
    session: AsyncSession = Depends(get_session),
):
    """Accepts a new vote, adds it to the mempool, and gossips to peers.

    Args:
        data: Vote transaction payload.
        blockchain: Injected node.
        session: Request-scoped DB session.

    Returns:
        JSONResponse: 201 with transaction metadata.

    """
    await blockchain.add_to_mempool(session, [data])

    await blockchain.gossip_transactions(session)

    return JSONResponse(
        content={
            "message": "Transaction will be added to chain soon",
            "transaction_id": data.id,
            "election_id": data.election_id,
            "voter_id": data.voter_id,
            "candidate_id": data.candidate_id,
            "created_at": data.created_at.isoformat() if data.created_at else None,
        },
        status_code=201,
    )


@router.get("/transactions")
async def get_transactions(blockchain: Node = Depends(get_blockchain)):
    """Returns all transactions currently in the local mempool.

    Returns:
        JSONResponse: Mempool list and count.

    """
    transactions = blockchain.mempool.get_all()
    return JSONResponse(
        content={
            "transactions": [tx.model_dump(mode="json") for tx in transactions],
            "count": len(transactions),
        },
        status_code=200,
    )


@router.post("/mined")
async def mined_block(block: Block, blockchain: Node = Depends(get_blockchain)):
    """Validates an externally mined block and appends it if rules pass.

    Silently returns when validation fails (logs warnings). On success, persists
    the block, removes its txs from the mempool, and gossips the chain.

    Args:
        block: Proposed block from a miner.
        blockchain: Injected node (uses ``blockchain.session``).

    Returns:
        None: Early return on validation failure; otherwise JSON is not returned
        explicitly (implicit None).

    """
    session = blockchain.session
    await blockchain.rollback_chain_to_valid_prefix(session)
    chain_schemas = await blockchain.get_chain(session)
    last_block = await blockchain.last_block(session)

    if not last_block:
        logger.warning("Mined block rejected: no last block")
        return

    if block.index != len(chain_schemas) + 1:
        logger.warning(
            "Mined block rejected: index not valid (got %s, expected %s)",
            block.index,
            len(chain_schemas) + 1,
        )
        return

    if block.previous_hash != blockchain.hash(last_block):
        logger.warning("Mined block rejected: previous hash does not match")
        return

    if not blockchain.valid_nonce(
        block.index,
        block.transactions,
        last_block.nonce,
        block.previous_hash,
        block.timestamp,
        block.nonce,
    ):
        logger.warning("Mined block rejected: nonce is not valid")
        return

    if not blockchain.mempool.contains_all(block.transactions):
        logger.warning("Mined block rejected: mempool does not contain all transactions")
        return

    if not await blockchain.valid_chain(chain=chain_schemas + [block]):
        logger.warning("Mined block rejected: chain not valid after adding block")
        return

    await blockchain.new_block(
        session,
        index=block.index,
        timestamp=block.timestamp,
        transactions=block.transactions,
        nonce=block.nonce,
        previous_hash=block.previous_hash,
    )
    blockchain.mempool.remove(block.transactions)
    await blockchain.gossip_chain(session)


@router.get("/chain")
async def chain(
    node_address: str | None = Query(
        None, description="Address of the requesting node (for seed node to register)"
    ),
    blockchain: Node = Depends(get_blockchain),
):
    """Returns the full chain and optionally registers the caller as a peer.

    Args:
        node_address: If provided, added to ``blockchain.nodes`` when new.
        blockchain: Injected node.

    Returns:
        JSONResponse: ``chain`` and ``length``.

    """
    if node_address:
        if node_address not in blockchain.nodes:
            logger.info("Registering new node: %s", node_address)
            blockchain.register_node(node_address)
    chain_schemas = await blockchain.get_chain(blockchain.session)
    return JSONResponse(
        content=jsonable_encoder(
            {
                "chain": [b.model_dump(mode="json") for b in chain_schemas],
                "length": len(chain_schemas),
            }
        ),
        status_code=200,
    )


@router.get("/nodes")
async def get_nodes(blockchain: Node = Depends(get_blockchain)):
    """Returns known peer node addresses.

    Returns:
        JSONResponse: ``nodes`` list and ``count``.

    """
    return JSONResponse(
        content={
            "nodes": list(blockchain.nodes),
            "count": len(blockchain.nodes),
        },
        status_code=200,
    )
