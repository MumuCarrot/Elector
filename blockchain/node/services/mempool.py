from node.schemas.transaction import Transaction


class Mempool:
    """In-memory pool for unconfirmed transactions."""

    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def get_all(self) -> list[Transaction]:
        return self._transactions

    def contains(self, tx: Transaction) -> bool:
        for t in self._transactions:
            if t.id == tx.id:
                return True
        return False

    def new_transaction(self, tx: Transaction) -> None:
        if not self.contains(tx):
            self._transactions.append(tx)

    def new_transactions(self, txs: list[Transaction]) -> None:
        for tx in txs:
            self.new_transaction(tx)

    def get_block_transaction(self, limit: int = 100) -> list[Transaction]:
        return self._transactions[:limit]

    def remove(self, txs: list[Transaction]) -> None:
        tx_ids = {tx.id for tx in txs}
        self._transactions = [t for t in self._transactions if t.id not in tx_ids]

    def remove_all(self, tx_ids: list[str]) -> None:
        self._transactions = [t for t in self._transactions if t.id not in tx_ids]

    def contains_all(self, txs: list[Transaction]) -> bool:
        return all(self.contains(tx) for tx in txs)
