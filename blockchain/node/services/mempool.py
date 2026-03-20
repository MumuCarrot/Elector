from node.schemas.transaction import Transaction


class Mempool:
    """Stores unconfirmed vote transactions until a block is mined.

    Attributes:
        _transactions: Ordered list of pending ``Transaction`` schemas.

    """

    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def get_all(self) -> list[Transaction]:
        """Returns the live list of pending transactions (mutable reference)."""

        return self._transactions

    def contains(self, tx: Transaction) -> bool:
        """Returns whether a transaction with the same ``id`` is already queued."""

        for t in self._transactions:
            if t.id == tx.id:
                return True
        return False

    def new_transaction(self, tx: Transaction) -> None:
        """Appends ``tx`` if its ``id`` is not already present."""

        if not self.contains(tx):
            self._transactions.append(tx)

    def new_transactions(self, txs: list[Transaction]) -> None:
        """Appends each transaction, skipping duplicates by ``id``."""

        for tx in txs:
            self.new_transaction(tx)

    def get_block_transaction(self, limit: int = 100) -> list[Transaction]:
        """Returns up to ``limit`` transactions from the front of the queue."""

        return self._transactions[:limit]

    def remove(self, txs: list[Transaction]) -> None:
        """Removes transactions whose ``id`` matches any in ``txs``."""

        tx_ids = {tx.id for tx in txs}
        self._transactions = [t for t in self._transactions if t.id not in tx_ids]

    def remove_all(self, tx_ids: list[str]) -> None:
        """Removes all transactions whose ``id`` is in ``tx_ids``."""

        self._transactions = [t for t in self._transactions if t.id not in tx_ids]

    def contains_all(self, txs: list[Transaction]) -> bool:
        """Returns True if every transaction in ``txs`` is present in the mempool."""

        return all(self.contains(tx) for tx in txs)
