import hashlib
import json
import threading
import time
import requests
from typing import List

from pydantic import TypeAdapter

from node.core.settings import settings
from node.schemas.block import Block
from node.schemas.transaction import Transaction
from node.services.mempool import Mempool


class Node:
    def __init__(self, host: str, port: int, is_copy: bool = False):
        self.host = host
        self.port = port
        self.chain = []
        self.nodes = set()
        self.mempool = Mempool()
        self._initializing = True
        self._mining_thread: threading.Thread | None = None
        self._mining_interval_seconds: float = 1.0

        # genesis block
        self.new_block(
            index=1,
            timestamp=0.0,
            transactions=[],
            nonce=100,
            previous_hash='080c1aaa09528a4c444a59a2a37545c4'
        )

        if not is_copy:
            if self.port != settings.app.MAIN_NODE_PORT:
                main_address = f'{settings.app.MAIN_NODE_HOST}:{settings.app.MAIN_NODE_PORT}'
                print(f'Connecting to main node at {main_address}')

                # register self
                self.register_node(main_address)

                # sync chain
                self.sync_chain()

                # sync transactions
                self.sync_transactions()

                # sync neighbors
                self.sync_neighbors()

                # mark initialization as complete
                self._initializing = False
            else:
                print(f'Running as main node on port {self.port}')
                self._initializing = False

            # start background mining worker for real nodes
            self._start_mining_worker()


    @property
    def last_block(self):
        return self.chain[-1]


    @staticmethod
    def valid_nonce(index, transactions, last_nonce, previous_hash, timestamp, nonce):
        if not transactions:
            transactions_dict = []
        else:
            transactions_dict = [
                tx.model_dump(mode="json") if hasattr(tx, "model_dump")
                else (tx.dict() if hasattr(tx, "dict") else tx)
                for tx in transactions
            ]
        transactions_json = json.dumps(transactions_dict, sort_keys=True, default=str)
        
        guess = f'{index}{transactions_json}{last_nonce}{previous_hash}{timestamp}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == settings.app.PROOF_OF_WORK_DIFFICULTY


    @staticmethod
    def hash(block):
        block_dict = {
            'index': block.index,
            'timestamp': block.timestamp.isoformat() if hasattr(block.timestamp, 'isoformat') else str(block.timestamp),
            'transactions': [
                tx.model_dump(mode="json") if hasattr(tx, "model_dump")
                else (tx.dict() if hasattr(tx, "dict") else {'data': getattr(tx, 'data', None)})
                for tx in block.transactions
            ],
            'nonce': block.nonce,
            'previous_hash': block.previous_hash
        }
        block_string = json.dumps(block_dict, sort_keys=True, default=str).encode()
        return hashlib.sha256(block_string).hexdigest()


    def new_block(self, index, timestamp, transactions, nonce, previous_hash=None):
        block = Block(
            index = index,
            timestamp = timestamp,
            transactions = transactions,
            nonce = nonce,
            previous_hash = previous_hash or self.hash(self.chain[-1])
        )

        self.chain.append(block)
        return block


    def register_node(self, address):
        self.nodes.add(address)


    def is_registered(self, address):
        return address in self.nodes


    def valid_chain(self, chain = None):
        if chain is None:
            chain = self.chain

        if not chain or len(chain) == 0:
            return False

        if chain and isinstance(chain[0], dict):
            chain_adapter = TypeAdapter(List[Block])
            chain = chain_adapter.validate_python(chain)

        for i in range(1, len(chain)):
            last_block = chain[i - 1]
            block = chain[i]

            if block.previous_hash != self.hash(last_block):
                return False

            if not self.valid_nonce(block.index, block.transactions, last_block.nonce, block.previous_hash, block.timestamp, block.nonce):
                return False

        return True


    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)
        
        connection_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        own_address = f'{connection_host}:{self.port}'

        for node in neighbours:
            response = requests.get(f'http://{node}/blockchain/chain', params={'node_address': own_address})

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            chain_adapter = TypeAdapter(List[Block])
            self.chain = chain_adapter.validate_python(new_chain)
        
        return new_chain is not None


    def _start_mining_worker(self) -> None:
        if self._mining_thread is not None:
            return

        def _worker() -> None:
            while True:
                try:
                    # skip while node is still syncing initial state
                    if self._initializing:
                        time.sleep(self._mining_interval_seconds)
                        continue

                    transactions = self.mempool.get_block_transaction()
                    if not transactions:
                        time.sleep(self._mining_interval_seconds)
                        continue

                    last_block = self.last_block
                    index = len(self.chain) + 1
                    previous_hash = self.hash(last_block)
                    timestamp = time.time()
                    nonce = 0

                    while not self.valid_nonce(
                        index=index,
                        transactions=transactions,
                        last_nonce=last_block.nonce,
                        previous_hash=previous_hash,
                        timestamp=timestamp,
                        nonce=nonce,
                    ):
                        nonce += 1

                    # ensure transactions are still in mempool
                    if not self.mempool.contains_all(transactions):
                        continue

                    # simulate adding block to verify chain validity
                    temp = self.copy_chain()
                    temp.new_block(
                        index=index,
                        timestamp=timestamp,
                        transactions=transactions,
                        nonce=nonce,
                        previous_hash=previous_hash,
                    )

                    if not temp.valid_chain():
                        print("Background miner: candidate block would make chain invalid")
                        continue

                    # commit block to main chain
                    self.new_block(
                        index=index,
                        timestamp=timestamp,
                        transactions=transactions,
                        nonce=nonce,
                        previous_hash=previous_hash,
                    )

                    # remove included transactions from mempool
                    self.mempool.remove(transactions)

                    # share updated chain with neighbors
                    self.gossip_chain()
                except Exception as exc:
                    print(f"Error in mining worker: {exc}")
                    time.sleep(self._mining_interval_seconds)

        self._mining_thread = threading.Thread(target=_worker, daemon=True)
        self._mining_thread.start()


    def gossip_transactions(self):
        for node in self.nodes:
            try:
                transactions = self.mempool.get_all()
                response = requests.post(f'http://{node}/gossip/transactions', json=[tx.model_dump() for tx in transactions])
                if response.status_code == 201:
                    transactions_data = response.json()["transactions"]
                    transaction_adapter = TypeAdapter(List[Transaction])
                    received_transactions = transaction_adapter.validate_python(transactions_data)
                    self.mempool.new_transactions(received_transactions)
            except Exception as e:
                print(f'Failed to gossip transaction to {node}: {e}')


    def gossip_chain(self):
        for node in self.nodes:
            try:
                tx_ids = [tx.id for block in self.chain for tx in block.transactions]
                response = requests.post(
                    f'http://{node}/gossip/chain',
                    json={
                        'chain': [block.model_dump() for block in self.chain],
                        'tx_ids': tx_ids
                    }
                )

                if response.status_code == 200:
                    continue
                elif response.status_code == 400:
                    remote_chain = response.json().get('chain', [])
                    chain_adapter = TypeAdapter(List[Block])
                    remote_chain_blocks = chain_adapter.validate_python(remote_chain)
                    if len(remote_chain_blocks) > len(self.chain) and self.valid_chain(remote_chain_blocks):
                        self.chain = remote_chain_blocks
                        self.mempool.remove_all([tx.id for block in remote_chain_blocks for tx in block.transactions])
            except Exception as e:
                print(f'Failed to gossip chain to {node}: {e}')


    def gossip_neighbors(self, ignore_nodes: List[str] = None):
        # don't gossip during initialization to avoid cycles
        if self._initializing:
            return
            
        connection_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        own_address = f'{connection_host}:{self.port}'
        
        if ignore_nodes is None:
            ignore_nodes = []
        ignore_nodes.append(own_address)

        for node in self.nodes:
            try:
                response = requests.post(f'http://{node}/gossip/neighbors', json=list(self.nodes))
                if response.status_code == 201:
                    nodes: list = response.json().get('nodes', [])
                    new_nodes = [
                        node_address 
                        for node_address in nodes 
                        if node_address not in self.nodes
                        and node_address not in ignore_nodes
                    ]
                    self.nodes.update(new_nodes)
            except Exception as e:
                print(f'Failed to gossip neighbors to {node}: {e}')


    def sync_chain(self):
        self.resolve_conflicts()

    def sync_transactions(self):
        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/blockchain/transactions')
                if response.status_code == 200:
                    transactions_data = response.json().get('transactions', [])
                    if transactions_data:
                        transaction_adapter = TypeAdapter(List[Transaction])
                        received_transactions = transaction_adapter.validate_python(transactions_data)
                        self.mempool.new_transactions(received_transactions)
            except Exception as e:
                print(f'Failed to sync transactions from {node}: {e}')

    def sync_neighbors(self):
        connection_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        own_address = f'{connection_host}:{self.port}'
        
        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/blockchain/nodes')
                if response.status_code == 200:
                    nodes_data = response.json().get('nodes', [])
                    for node_address in nodes_data:
                        if node_address != own_address:
                            self.register_node(node_address)
            except Exception as e:
                print(f'Failed to sync neighbors from {node}: {e}')


    def undo_block(self):
        if len(self.chain) > 1:
            removed_block = self.chain.pop()
            self.mempool.new_transactions(removed_block.transactions)
            return removed_block
        return None


    def copy_chain(self):
        new_node = Node(self.host, self.port, is_copy=True)
        new_node.chain = self.chain.copy()
        return new_node