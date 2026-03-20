import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import List

import requests
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from node.core.settings import settings
from node.db.database import async_session_maker
from node.models.block import Block as BlockModel
from node.models.transaction import Transaction as TransactionModel
from node.repositories.block_repository import BlockRepository
from node.repositories.transaction_repository import TransactionRepository
from node.schemas.block import Block as BlockSchema
from node.schemas.transaction import Transaction as TransactionSchema
from node.services.mempool import Mempool
from node.utils.datetime_utils import dt_to_timestamp, to_naive_dt

logger = logging.getLogger(__name__)


def _model_to_schema_block(block: BlockModel) -> BlockSchema:
    """Maps a SQLAlchemy ``Block`` row (with transactions) to API ``Block`` schema.

    Args:
        block: Loaded ORM block including ``transactions``.

    Returns:
        BlockSchema: Pydantic block with Unix ``timestamp`` for JSON compatibility.

    """
    tx_schemas = [
        TransactionSchema(
            id=t.id,
            election_id=t.election_id,
            voter_id=t.voter_id,
            candidate_id=t.candidate_id,
            created_at=t.created_at,
        )
        for t in block.transactions
    ]
    
    ts = dt_to_timestamp(block.timestamp)

    return BlockSchema(
        index=block.index,
        timestamp=ts,
        transactions=tx_schemas,
        nonce=block.nonce,
        previous_hash=block.previous_hash,
    )


class Node:
    """In-process blockchain node: peers, mempool, mining task, and optional request session.

    Attributes:
        host: Advertised bind host (may be ``0.0.0.0``).
        port: TCP port of this API server.
        nodes: Known peer addresses ``host:port``.
        mempool: Pending transactions not yet in a block.
        session: Set per-request by FastAPI dependencies when handling HTTP calls.
        _initializing: True until ``initialize`` finishes neighbor/tx sync.
        _mining_task: Background task running ``_mining_loop_forever``.
        _mining_interval_seconds: Sleep between mining attempts when idle or after errors.

    """

    def __init__(self, host: str, port: int, is_copy: bool = False):
        """Creates a node and optionally registers the configured main node as a peer.

        When ``is_copy`` is False and this instance is not the configured main port,
        the main node address is added to ``nodes``. The app lifespan typically uses
        ``is_copy=True`` to avoid duplicate registration side effects in ``__init__``.

        Args:
            host: Hostname or IP for this node.
            port: Listen port for this node.
            is_copy: If True, skips automatic main-node registration in ``__init__``.

        """
        self.host = host
        self.port = port
        self.nodes = set()
        self.mempool = Mempool()
        self._initializing = True
        self._mining_task: asyncio.Task | None = None
        self._mining_interval_seconds: float = 1.0
        if not is_copy:
            if self.port != settings.app.MAIN_NODE_PORT:
                main_address = f"{settings.app.MAIN_NODE_HOST}:{settings.app.MAIN_NODE_PORT}"
                logger.info("Connecting to main node at %s", main_address)
                self.register_node(main_address)
            else:
                logger.info("Running as main node on port %s", self.port)

    async def initialize(self) -> None:
        """Ensures genesis exists, syncs chain/transactions/peers, then starts mining.

        Should be called once from the FastAPI lifespan on the process main event loop.

        """
        # Register main node if this is not the main node (skipped when is_copy=True in __init__)
        if self.port != settings.app.MAIN_NODE_PORT:
            main_address = f"{settings.app.MAIN_NODE_HOST}:{settings.app.MAIN_NODE_PORT}"
            logger.info("Connecting to main node at %s", main_address)
            self.register_node(main_address)
        else:
            logger.info("Running as main node on port %s", self.port)

        async with async_session_maker() as init_session:
            await self._async_init(init_session)
        self._initializing = False
        self._mining_task = asyncio.create_task(self._mining_loop_forever())

    async def _mining_loop_forever(self) -> None:
        """Repeatedly runs one mining cycle in a fresh DB session until cancelled.

        Runs on the same asyncio loop as FastAPI to avoid asyncpg cross-loop issues.

        """
        while True:
            try:
                async with async_session_maker() as session:
                    await self._mining_cycle(session)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Error in mining loop: %s", exc)
            await asyncio.sleep(self._mining_interval_seconds)


    async def _async_init(self, session: AsyncSession) -> None:
        """Creates genesis if DB is empty, then pulls chain, mempool txs, and peer list.

        Args:
            session: Database session for initialization queries.

        """
        # initialize genesis block
        block_repo = BlockRepository(session)
        count = await block_repo.count()
        if count == 0:
            genesis_hash = hashlib.sha256(
                b"1[]100080c1aaa09528a4c444a59a2a37545c40"
            ).hexdigest()
            genesis = BlockModel(
                index=1,
                timestamp=datetime.fromtimestamp(0),
                nonce=100,
                previous_hash="080c1aaa09528a4c444a59a2a37545c4",
                hash=genesis_hash,
            )
            await block_repo.create(genesis)

        # sync from network
        await self.resolve_conflicts(session)
        
        # sync transactions
        await self._sync_transactions_async(session)
        
        # sync neighbors
        await self._sync_neighbors_async()


    async def _get_chain(self, session: AsyncSession) -> list[BlockModel]:
        """Loads all blocks from storage ordered by ``index`` ascending.

        Args:
            session: Active async session.

        Returns:
            list[BlockModel]: Full chain as ORM objects.

        """
        block_repo = BlockRepository(session)
        return await block_repo.get_chain_ordered()


    async def _get_confirmed_tx_ids(
        self, session: AsyncSession, tx_ids: list[str]
    ) -> set[str]:
        """Returns which transaction ids already appear in any mined block.

        Args:
            session: Database session.
            tx_ids: Candidate ids (typically mempool batch).

        Returns:
            set[str]: Subset of ``tx_ids`` that are confirmed on-chain.

        """
        if not tx_ids:
            return set()
            
        return await BlockRepository(session).get_transaction_ids_in_chain(tx_ids)


    async def add_to_mempool(
        self, session: AsyncSession, transactions: list[TransactionSchema]
    ) -> None:
        """Queues new votes in the mempool, ignoring ids already present in blocks.

        Args:
            session: Database session for confirmation lookup.
            transactions: Incoming vote payloads.

        """
        if not transactions:
            return
            
        tx_ids = [tx.id for tx in transactions]
        confirmed = await self._get_confirmed_tx_ids(session, tx_ids)
        to_add = [tx for tx in transactions if tx.id not in confirmed]
        self.mempool.new_transactions(to_add)


    async def _get_chain_schemas(self, session: AsyncSession) -> list[BlockSchema]:
        """Returns the chain as Pydantic models for JSON and validation.

        Args:
            session: Database session.

        Returns:
            list[BlockSchema]: Serializable chain.

        """
        blocks = await self._get_chain(session)
        return [_model_to_schema_block(b) for b in blocks]


    async def last_block(self, session: AsyncSession) -> BlockModel | None:
        """Get last block from DB."""

        block_repo = BlockRepository(session)
        return await block_repo.get_last_block()


    async def get_chain(self, session: AsyncSession) -> list[BlockSchema]:
        """Public accessor for the chain as ``BlockSchema`` list (HTTP handlers).

        Args:
            session: Database session.

        Returns:
            list[BlockSchema]: Full chain.

        """
        return await self._get_chain_schemas(session)


    @staticmethod
    def valid_nonce(index, transactions, last_nonce, previous_hash, timestamp, nonce):
        """Checks proof-of-work: SHA256 digest must start with ``PROOF_OF_WORK_DIFFICULTY``.

        The preimage includes block index, serialized transactions, parent's nonce,
        previous hash, timestamp, and this block's nonce.

        Args:
            index: Block height.
            transactions: List of tx objects or dicts.
            last_nonce: Previous block's nonce.
            previous_hash: Parent hash string.
            timestamp: Block time (numeric or stringifiable).
            nonce: Candidate nonce.

        Returns:
            bool: True if the hash prefix matches the configured difficulty.

        """
        if not transactions:
            transactions_dict = []
        else:
            transactions_dict = [
                tx.model_dump(mode="json")
                if hasattr(tx, "model_dump")
                else (tx.dict() if hasattr(tx, "dict") else tx)
                for tx in transactions
            ]
        transactions_json = json.dumps(transactions_dict, sort_keys=True, default=str)
        guess = f"{index}{transactions_json}{last_nonce}{previous_hash}{timestamp}{nonce}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == settings.app.PROOF_OF_WORK_DIFFICULTY


    @staticmethod
    def _tx_to_dict(tx) -> dict:
        """Normalizes a transaction-like object to a JSON-friendly dict.

        Args:
            tx: Pydantic model, dict-like, or ORM object with vote fields.

        Returns:
            dict: Transaction fields suitable for hashing.

        """
        if hasattr(tx, "model_dump"):
            return tx.model_dump(mode="json")
        if hasattr(tx, "dict"):
            return tx.dict()
        return {
            "id": getattr(tx, "id", None),
            "election_id": getattr(tx, "election_id", None),
            "voter_id": getattr(tx, "voter_id", None),
            "candidate_id": getattr(tx, "candidate_id", None),
            "created_at": getattr(tx, "created_at", None),
        }


    @classmethod
    def _block_hash(
        cls,
        index: int,
        timestamp,
        transactions: list,
        nonce: int,
        previous_hash: str,
    ) -> str:
        """Computes SHA256 hex digest over canonical JSON of block fields.

        Args:
            index: Block index.
            timestamp: ``datetime`` or epoch-like value.
            transactions: Transactions to include in the preimage.
            nonce: Block nonce.
            previous_hash: Parent block hash.

        Returns:
            str: 64-character hex digest.

        """
        txs = [cls._tx_to_dict(tx) for tx in transactions]
        ts_str = (
            timestamp.isoformat()
            if hasattr(timestamp, "isoformat")
            else str(timestamp)
        )
        block_dict = {
            "index": index,
            "timestamp": ts_str,
            "transactions": txs,
            "nonce": nonce,
            "previous_hash": previous_hash,
        }
        block_string = json.dumps(block_dict, sort_keys=True, default=str).encode()
        return hashlib.sha256(block_string).hexdigest()

    @classmethod
    def hash(cls, block) -> str:
        txs = getattr(block, "transactions", [])
        return cls._block_hash(
            block.index, block.timestamp, txs, block.nonce, block.previous_hash
        )


    async def new_block(
        self,
        session: AsyncSession,
        index: int,
        timestamp: float,
        transactions: list[TransactionSchema],
        nonce: int,
        previous_hash: str | None = None,
    ) -> BlockModel:
        """Persists a new block and its transactions, linking rows in the database.

        Args:
            session: Database session.
            index: New block height.
            timestamp: Unix time or ``datetime``.
            transactions: Votes to store under this block.
            nonce: Proof-of-work nonce.
            previous_hash: Explicit parent hash, or computed from current tip.

        Returns:
            BlockModel: Saved block ORM instance.

        """
        block_repo = BlockRepository(session)
        transaction_repo = TransactionRepository(session)
        last = await self.last_block(session)
        prev_hash = previous_hash or (self.hash(last) if last else "080c1aaa09528a4c444a59a2a37545c4")
        block_hash = self._block_hash(index, timestamp, transactions, nonce, prev_hash)

        # DB expects datetime; convert Unix timestamp (float/int) if needed
        if isinstance(timestamp, datetime):
            ts = timestamp
        else:
            ts = datetime.fromtimestamp(float(timestamp))

        block = BlockModel(
            index=index,
            timestamp=ts,
            nonce=nonce,
            previous_hash=prev_hash,
            hash=block_hash,
        )
        await block_repo.create(block)
        for tx in transactions:
            t = TransactionModel(
                id=tx.id,
                block_id=block.id,
                election_id=tx.election_id,
                voter_id=tx.voter_id,
                candidate_id=tx.candidate_id,
                created_at=to_naive_dt(tx.created_at),
            )
            await transaction_repo.create(t)
        return block


    def register_node(self, address: str) -> None:
        """Adds a peer ``host:port`` string to the in-memory peer set.

        Args:
            address: Peer URL fragment without scheme (e.g. ``127.0.0.1:5001``).

        """
        self.nodes.add(address)


    def is_registered(self, address: str) -> bool:
        """Returns whether ``address`` is in the local peer set.

        Args:
            address: Peer ``host:port`` string.

        Returns:
            bool: True if registered.

        """

        return address in self.nodes


    async def valid_chain(self, session: AsyncSession | None = None, chain: list | None = None) -> bool:
        """Validates hash linkage and proof-of-work for each block after the first.

        Args:
            session: Required when ``chain`` is None (loads from DB).
            chain: In-memory chain as schemas, dicts, or ORM objects.

        Returns:
            bool: False if empty or any check fails.

        Raises:
            ValueError: If ``chain`` is None and ``session`` is None.

        """
        if chain is None:
            if session is None:
                raise ValueError("Session is required if chain is not provided")
            chain = await self._get_chain(session)

        if not chain:
            return False
        
        if chain and isinstance(chain[0], dict):
            chain = TypeAdapter(List[BlockSchema]).validate_python(chain)
        
        for i in range(1, len(chain)):
            last_block = chain[i - 1]
            block = chain[i]
            if block.previous_hash != self.hash(last_block):
                return False
            txs = block.transactions if hasattr(block, "transactions") else []
            if not self.valid_nonce(
                block.index,
                txs,
                last_block.nonce,
                block.previous_hash,
                block.timestamp,
                block.nonce,
            ):
                return False
        return True


    async def resolve_conflicts(self, session: AsyncSession) -> bool:
        """Replaces the local chain if a peer exposes a longer valid chain.

        Args:
            session: Database session for rewrite and commits.

        Returns:
            bool: True if the stored chain was replaced.

        """
        connection_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        own_address = f"{connection_host}:{self.port}"
        block_repo = BlockRepository(session)
        transaction_repo = TransactionRepository(session)
        max_length = await block_repo.count()
        new_chain = None

        # fetch chains from other nodes
        for node in self.nodes:
            try:
                response = await asyncio.to_thread(
                    requests.get,
                    f"http://{node}/blockchain/chain",
                    params={"node_address": own_address},
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                length = data["length"]
                chain_data = data["chain"]
                
                if length <= max_length:
                    continue

                if await self.valid_chain(session, chain_data):
                    max_length = length
                    new_chain = chain_data

            except Exception as e:
                logger.warning("Failed to fetch chain from %s: %s", node, e)

        # replace chain if new chain is valid
        if new_chain:
            chain_schemas = TypeAdapter(List[BlockSchema]).validate_python(new_chain)

            # delete existing blocks (cascade deletes transactions)
            existing = await block_repo.get_chain_ordered()
            for b in existing:
                await block_repo.delete(BlockModel.id == b.id)

            # create blocks and their transactions
            for block_schema in chain_schemas:
                block_hash = self.hash(block_schema)
                ts = block_schema.timestamp
                if isinstance(ts, (int, float)):
                    ts = datetime.fromtimestamp(ts)

                block = BlockModel(
                    index=block_schema.index,
                    timestamp=ts,
                    nonce=block_schema.nonce,
                    previous_hash=block_schema.previous_hash,
                    hash=block_hash,
                )
                await block_repo.create(block)
                
                for tx in block_schema.transactions:
                    t = TransactionModel(
                        id=tx.id,
                        block_id=block.id,
                        election_id=tx.election_id,
                        voter_id=tx.voter_id,
                        candidate_id=tx.candidate_id,
                        created_at=to_naive_dt(tx.created_at),
                    )
                    await transaction_repo.create(t)

            tx_ids = [tx.id for b in chain_schemas for tx in b.transactions]
            self.mempool.remove_all(tx_ids)

        return new_chain is not None


    async def replace_chain_with(
        self, session: AsyncSession, chain_schemas: list[BlockSchema], tx_ids: list[str]
    ) -> None:
        """Deletes local blocks and persists ``chain_schemas``; prunes mempool by ``tx_ids``.

        Args:
            session: Database session.
            chain_schemas: Validated peer chain.
            tx_ids: All transaction ids contained in that chain.

        """
        block_repo = BlockRepository(session)
        transaction_repo = TransactionRepository(session)
        existing = await block_repo.get_chain_ordered()
        for b in existing:
            await block_repo.delete(BlockModel.id == b.id)
        for block_schema in chain_schemas:
                block_hash = self.hash(block_schema)
                ts = block_schema.timestamp
                if isinstance(ts, (int, float)):
                    ts = datetime.fromtimestamp(ts)
                block = BlockModel(
                    index=block_schema.index,
                    timestamp=ts,
                    nonce=block_schema.nonce,
                    previous_hash=block_schema.previous_hash,
                    hash=block_hash,
                )
                await block_repo.create(block)
                for tx in block_schema.transactions:
                    t = TransactionModel(
                        id=tx.id,
                        block_id=block.id,
                        election_id=tx.election_id,
                        voter_id=tx.voter_id,
                        candidate_id=tx.candidate_id,
                        created_at=to_naive_dt(tx.created_at),
                    )
                    await transaction_repo.create(t)
        self.mempool.remove_all(tx_ids)


    async def _mining_cycle(self, session: AsyncSession) -> None:
        """Mining cycle."""
        
        transactions = self.mempool.get_block_transaction()

        if not transactions:
            await asyncio.sleep(self._mining_interval_seconds)
            return
        
        logger.info("Mining cycle: %d transactions in mempool", len(transactions))
        
        last_block = await self.last_block(session)
        if not last_block:
            logger.warning("Mining cycle: no last block, skipping")
            return
        
        index = last_block.index + 1
        previous_hash = self.hash(last_block)
        timestamp = time.time()
        nonce = 0
        last_nonce = last_block.nonce
        
        while not self.valid_nonce(
            index=index,
            transactions=transactions,
            last_nonce=last_nonce,
            previous_hash=previous_hash,
            timestamp=timestamp,
            nonce=nonce,
        ):
            nonce += 1
        
        if not self.mempool.contains_all(transactions):
            logger.warning("Mining cycle: mempool changed, aborting")
            return

        # Sync with network before creating block - another node may have mined same tx
        await self.resolve_conflicts(session)
        if not self.mempool.contains_all(transactions):
            logger.warning("Mining cycle: tx already mined by another node, aborting")
            return

        # Final check: abort if any tx already in chain (prevents duplicate blocks)
        tx_ids = [tx.id for tx in transactions]
        confirmed = await self._get_confirmed_tx_ids(session, tx_ids)
        already_mined = [tx for tx in transactions if tx.id in confirmed]
        if already_mined:
            logger.warning(
                "Mining cycle: aborting - %d tx already in chain (mined elsewhere)",
                len(already_mined),
            )
            self.mempool.remove(already_mined)
            return

        logger.info("Mining cycle: creating block index=%d nonce=%d", index, nonce)
        await self.new_block(
            session=session,
            index=index,
            timestamp=timestamp,
            transactions=transactions,
            nonce=nonce,
            previous_hash=previous_hash,
        )

        self.mempool.remove(transactions)
        logger.info("Mining cycle: block %d created successfully", index)
        await self._gossip_chain_async(session)


    async def _gossip_chain_async(self, session: AsyncSession) -> None:
        """POSTs the full chain to each peer; on 400, may trigger conflict resolution.

        Args:
            session: Session used if a longer remote chain must be applied.

        """
        chain = await self._get_chain_schemas(session)
        tx_ids = [tx.id for b in chain for tx in b.transactions]
        
        for node in self.nodes:
            try:
                response = await asyncio.to_thread(
                    requests.post,
                    f"http://{node}/gossip/chain",
                    json={"chain": [b.model_dump(mode="json") for b in chain], "tx_ids": tx_ids},
                )

                if response.status_code == 200:
                    continue

                if response.status_code == 400:
                    remote = response.json().get("chain", [])

                    if await self.valid_chain(chain=remote) and len(remote) > len(chain):
                        await self.resolve_conflicts(session)

            except Exception as e:
                logger.warning("Failed to gossip chain to %s: %s", node, e)


    async def gossip_transactions(self, session: AsyncSession) -> None:
        """Pushes the current mempool to peers and merges any returned superset.

        Args:
            session: Database session for merging received txs into mempool.

        """
        for node in self.nodes:
            try:
                transactions = self.mempool.get_all()
                response = await asyncio.to_thread(
                    requests.post,
                    f"http://{node}/gossip/transactions",
                    json=[tx.model_dump(mode="json") for tx in transactions],
                )

                if response.status_code == 201:
                    data = response.json().get("transactions", [])
                    received = TypeAdapter(List[TransactionSchema]).validate_python(data)
                    await self.add_to_mempool(session, received)

            except Exception as e:
                logger.warning("Failed to gossip transaction to %s: %s", node, e)


    async def gossip_chain(self, session: AsyncSession) -> None:
        """Public wrapper that gossips the current chain to all peers."""

        await self._gossip_chain_async(session)


    async def gossip_neighbors(self, ignore_nodes: List[str] | None = None) -> None:
        """Exchanges full peer lists with neighbors to discover new addresses.

        Args:
            ignore_nodes: Addresses not to re-add (plus self is always ignored).

        """
        if self._initializing:
            return

        connection_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        own_address = f"{connection_host}:{self.port}"
        
        if ignore_nodes is None:
            ignore_nodes = []
        ignore_nodes.append(own_address)
        
        for node in self.nodes:
            try:
                response = await asyncio.to_thread(
                    requests.post,
                    f"http://{node}/gossip/neighbors",
                    json=list(self.nodes),
                )

                if response.status_code == 201:
                    nodes_list = response.json().get("nodes", [])
                    new_nodes = [
                        addr
                        for addr in nodes_list
                        if addr not in self.nodes and addr not in ignore_nodes
                    ]
                    self.nodes.update(new_nodes)

            except Exception as e:
                logger.warning("Failed to gossip neighbors to %s: %s", node, e)


    async def sync_chain(self, session: AsyncSession) -> None:
        """Runs longest-chain resolution against peers (see ``resolve_conflicts``)."""

        await self.resolve_conflicts(session)


    async def _sync_transactions_async(self, session: AsyncSession) -> None:
        """Pulls each peer's mempool via HTTP and merges into the local mempool."""

        for node in self.nodes:
            try:
                response = await asyncio.to_thread(
                    requests.get, f"http://{node}/blockchain/transactions"
                )
                if response.status_code == 200:
                    data = response.json().get("transactions", [])
                    if data:
                        received = TypeAdapter(List[TransactionSchema]).validate_python(data)
                        await self.add_to_mempool(session, received)
            except Exception as e:
                logger.warning("Failed to sync transactions from %s: %s", node, e)


    async def _sync_neighbors_async(self) -> None:
        """Fetches ``/blockchain/nodes`` from peers to expand the local peer set."""

        connection_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        own_address = f"{connection_host}:{self.port}"
        for node in self.nodes:
            try:
                response = await asyncio.to_thread(
                    requests.get, f"http://{node}/blockchain/nodes"
                )
                if response.status_code == 200:
                    for addr in response.json().get("nodes", []):
                        if addr != own_address:
                            self.register_node(addr)
            except Exception as e:
                logger.warning("Failed to sync neighbors from %s: %s", node, e)


    def sync_neighbors(self) -> None:
        """Blocking helper: runs ``_sync_neighbors_async`` in a new event loop.

        Prefer the async API from FastAPI contexts; this exists for synchronous callers.

        """
        asyncio.run(self._sync_neighbors_async())


    async def undo_block(self, session: AsyncSession) -> BlockModel | None:
        """Removes the chain tip and re-queues its transactions in the mempool.

        Args:
            session: Database session.

        Returns:
            BlockModel | None: The removed block, or None if chain was empty.

        """
        last = await self.last_block(session)
        if not last:
            return None

        tx_repo = TransactionRepository(session)
        block_repo = BlockRepository(session)
        await tx_repo.delete_many(TransactionModel.block_id == last.id)
        await block_repo.delete(BlockModel.id == last.id)
        for t in last.transactions:
            self.mempool.new_transaction(
                TransactionSchema(
                    id=t.id,
                    election_id=t.election_id,
                    voter_id=t.voter_id,
                    candidate_id=t.candidate_id,
                    created_at=t.created_at,
                )
            )
        return last


    def copy_chain(self) -> "Node":
        """Factory for a lightweight sibling node sharing host/port without main-node hooks.

        Returns:
            Node: New instance with ``is_copy=True``.

        """
        new_node = Node(self.host, self.port, is_copy=True)
        return new_node