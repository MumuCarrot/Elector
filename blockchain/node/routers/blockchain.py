import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from node.dependencies import get_blockchain, get_session
from node.schemas.block import Block
from node.schemas.transaction import Transaction
from node.services.node import Node

logger = logging.getLogger(__name__)
router = APIRouter(tags=["blockchain"])

node_identifier = str(uuid4()).replace('-', '')


@router.post("/transactions/new")
async def new_transaction(
    data: Transaction,
    blockchain: Node = Depends(get_blockchain),
    session: AsyncSession = Depends(get_session),
):
    await blockchain.add_to_mempool(session, [data])

    # gossip transactions to neighbors
    await blockchain.gossip_transactions(session)

    return JSONResponse(
        content={'message': f'Transaction will be added to chain soon'},
        status_code=201
    )


@router.get("/transactions")
async def get_transactions(blockchain: Node = Depends(get_blockchain)):
    transactions = blockchain.mempool.get_all()
    return JSONResponse(
        content={
            'transactions': [tx.model_dump(mode="json") for tx in transactions],
            'count': len(transactions)
        },
        status_code=200
    )


@router.post("/mined")
async def mined_block(block: Block, blockchain: Node = Depends(get_blockchain)):
    session = blockchain.session
    chain_schemas = await blockchain.get_chain(session)
    last_block = await blockchain.last_block(session)
    if not last_block:
        logger.warning("Mined block rejected: no last block")
        return
    if block.index != len(chain_schemas) + 1:
        logger.warning("Mined block rejected: index not valid (got %s, expected %s)", block.index, len(chain_schemas) + 1)
        return
    if block.previous_hash != blockchain.hash(last_block):
        logger.warning("Mined block rejected: previous hash does not match")
        return
    if not blockchain.valid_nonce(
        block.index, block.transactions, last_block.nonce,
        block.previous_hash, block.timestamp, block.nonce
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
        previous_hash=block.previous_hash
    )
    blockchain.mempool.remove(block.transactions)
    await blockchain.gossip_chain(session)


@router.get("/chain")
async def chain(
    node_address: str | None = Query(None, description="Address of the requesting node (for seed node to register)"),
    blockchain: Node = Depends(get_blockchain)
):
    if node_address:
        if node_address not in blockchain.nodes:
            logger.info("Registering new node: %s", node_address)
            blockchain.register_node(node_address)
    chain_schemas = await blockchain.get_chain(blockchain.session)
    return JSONResponse(
        content=jsonable_encoder(
            {
                'chain': [b.model_dump(mode="json") for b in chain_schemas],
                'length': len(chain_schemas),
            }
        ),
        status_code=200
    )


@router.get("/nodes")
async def get_nodes(blockchain: Node = Depends(get_blockchain)):
    return JSONResponse(
        content={
            'nodes': list(blockchain.nodes),
            'count': len(blockchain.nodes)
        },
        status_code=200
    )