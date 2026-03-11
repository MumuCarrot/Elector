from node.schemas.transaction import Transaction


class Mempool:
    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def get_all(self):
        return self._transactions

    def contains(self, tx: Transaction) -> bool:
        for transaction in self._transactions:
            if tx.id == transaction.id:
                return True
        return False

    def new_transaction(self, tx) -> None:
        if not self.contains(tx):
            self._transactions.append(tx)

    def new_transactions(self, txs) -> None:
        for tx in txs:
            self.new_transaction(tx)

    def get_block_transaction(self, limit=100) -> list[Transaction]:
        return self._transactions[:limit]

    def remove(self, tx_id: list[Transaction]) -> None:
        self._transactions = [tx for tx in self._transactions if tx not in tx_id]

    def remove_all(self, tx_ids: list[str]) -> None:
        self._transactions = [tx for tx in self._transactions if tx.id not in tx_ids]

    def contains_all(self, txs: list[Transaction]) -> bool:
        for tx in txs:
            if not self.contains(tx):
                return False
        return True