from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.responses import Response

from node.dependencies import get_blockchain
from node.schemas.block import Block
from node.schemas.transaction import Transaction
from node.services.node import Node

router = APIRouter(tags=["blockchain"])

node_identifier = str(uuid4()).replace('-', '')


@router.post("/transactions/new")
async def new_transaction(data: Transaction, blockchain: Node = Depends(get_blockchain)):
    # data is already validated by Transaction schema
    blockchain.mempool.new_transaction(data)

    # gossip transactions to neighbors
    blockchain.gossip_transactions()

    return JSONResponse(
        content={'message': f'Transaction will be added to chain soon'},
        status_code=201
    )


@router.get("/transactions")
async def get_transactions(blockchain: Node = Depends(get_blockchain)):
    transactions = blockchain.mempool.get_all()
    return JSONResponse(
        content={
            'transactions': [tx.model_dump() for tx in transactions],
            'count': len(transactions)
        },
        status_code=200
    )


@router.get("/fetch")
async def fetch_transactions(blockchain: Node = Depends(get_blockchain)):
    last_block = blockchain.last_block
    last_nonce = last_block.nonce

    if not blockchain.mempool.get_block_transaction():
        return Response(status_code=204)

    return JSONResponse(
        content={
            'message': "Fetch successful",
            'index': len(blockchain.chain) + 1,
            'transactions': [tx.model_dump() for tx in blockchain.mempool.get_block_transaction()],
            'nonce': last_nonce,
            'previous_hash': blockchain.hash(last_block),
        },
        status_code=200
    )


@router.post("/mined")
async def mined_block(block: Block, blockchain: Node = Depends(get_blockchain)):
    # basic validations
    if block.index != len(blockchain.chain) + 1:
        print("Index is not valid")
        return
    if block.previous_hash != blockchain.hash(blockchain.last_block):
        print("Previous hash does not match")
        return
    if not blockchain.valid_nonce(block.index, block.transactions, blockchain.last_block.nonce, block.previous_hash, block.timestamp, block.nonce):
        print("Nonce is not valid")
        return

    # check if all transactions are in mempool
    if not blockchain.mempool.contains_all(block.transactions):
        print("Mempool does not contain all transactions")
        return

    # if chain is not valid return void
    temp = blockchain.copy_chain()
    temp.new_block(
        index=block.index,
        timestamp=block.timestamp,
        transactions=block.transactions,
        nonce=block.nonce,
        previous_hash=block.previous_hash
    )

    if not temp.valid_chain():
        print("Chain is not valid after adding the block")
        return

    # add block to chain
    blockchain.new_block(
        index=block.index,
        timestamp=block.timestamp,
        transactions=block.transactions,
        nonce=block.nonce,
        previous_hash=block.previous_hash
    )

    # remove transactions from mempool
    blockchain.mempool.remove(block.transactions)

    # gossip chain
    blockchain.gossip_chain()


@router.get("/chain")
async def chain(
    node_address: str | None = Query(None, description="Address of the requesting node (for seed node to register)"),
    blockchain: Node = Depends(get_blockchain)
):
    if node_address:
        if node_address not in blockchain.nodes:
            print(f'Registering new node: {node_address}')
            blockchain.register_node(node_address)
            # Note: gossip_neighbors() is not called here to avoid blocking and cycles
            # Neighbors will be synced when the new node calls sync_neighbors()
    
    return JSONResponse(
        content=jsonable_encoder(
            {
                'chain': [block for block in blockchain.chain],
                'length': len(blockchain.chain),
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