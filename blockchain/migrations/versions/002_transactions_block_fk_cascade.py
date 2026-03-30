"""transactions.block_id ON DELETE CASCADE

Revision ID: 002
Revises: 001
Create Date: 2026-03-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _find_table_schema(conn, table_name: str) -> str | None:
    """Returns schema name for a physical table (pg_catalog), or None."""
    row = conn.execute(
        text(
            """
            SELECT n.nspname
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE c.relkind = 'r'
              AND c.relname = :name
              AND n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY (n.nspname = 'public') DESC
            LIMIT 1
            """
        ),
        {"name": table_name},
    ).fetchone()
    return row[0] if row else None


def _create_transactions_table_if_missing(blocks_schema: str) -> None:
    """Creates ``transactions`` when the DB was stamped at 001 but the table is absent."""
    table_kw: dict = {}
    idx_kw: dict = {}
    if blocks_schema != "public":
        table_kw["schema"] = blocks_schema
        idx_kw["schema"] = blocks_schema
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "block_id",
            sa.String(36),
            sa.ForeignKey("blockchain_blocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("election_id", sa.String(), nullable=False),
        sa.Column("voter_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        **table_kw,
    )
    op.create_index("idx_bc_tx_block_id", "transactions", ["block_id"], **idx_kw)
    op.create_index("idx_bc_tx_election_id", "transactions", ["election_id"], **idx_kw)
    op.create_index("idx_bc_tx_voter_id", "transactions", ["voter_id"], **idx_kw)
    op.create_index("idx_bc_tx_candidate_id", "transactions", ["candidate_id"], **idx_kw)
    op.create_index("idx_bc_tx_created_at", "transactions", ["created_at"], **idx_kw)


def upgrade() -> None:
    conn = op.get_bind()
    tx_schema = _find_table_schema(conn, "transactions")
    blk_schema = _find_table_schema(conn, "blockchain_blocks")

    if tx_schema is None:
        if blk_schema is None:
            raise RuntimeError(
                "Tables blockchain_blocks and transactions are missing. "
                "Run `alembic upgrade 001` on an empty database, or fix alembic_version."
            )
        _create_transactions_table_if_missing(blk_schema)
        return

    if blk_schema is None:
        raise RuntimeError(
            "Table transactions exists but blockchain_blocks is missing; database is inconsistent."
        )

    if tx_schema != blk_schema:
        raise RuntimeError(
            f"transactions is in schema {tx_schema!r} but blockchain_blocks is in {blk_schema!r}; "
            "move both to the same schema or recreate the database."
        )

    rows = conn.execute(
        text(
            """
            SELECT c.conname
            FROM pg_constraint c
            JOIN pg_class rel ON c.conrelid = rel.oid
            JOIN pg_namespace nsp ON rel.relnamespace = nsp.oid
            WHERE nsp.nspname = :schema
              AND rel.relname = 'transactions'
              AND c.contype = 'f'
            """
        ),
        {"schema": tx_schema},
    ).fetchall()
    for (conname,) in rows:
        conn.execute(
            text(
                f'ALTER TABLE "{tx_schema}".transactions DROP CONSTRAINT "{conname}"'
            )
        )

    op.create_foreign_key(
        "transactions_block_id_fkey",
        "transactions",
        "blockchain_blocks",
        ["block_id"],
        ["id"],
        source_schema=tx_schema,
        referent_schema=blk_schema,
        ondelete="CASCADE",
    )


def downgrade() -> None:
    conn = op.get_bind()
    tx_schema = _find_table_schema(conn, "transactions")
    blk_schema = _find_table_schema(conn, "blockchain_blocks")
    if tx_schema is None or blk_schema is None:
        return

    conn.execute(
        text(
            f'ALTER TABLE "{tx_schema}".transactions '
            'DROP CONSTRAINT IF EXISTS "transactions_block_id_fkey"'
        )
    )
    op.create_foreign_key(
        "transactions_block_id_fkey",
        "transactions",
        "blockchain_blocks",
        ["block_id"],
        ["id"],
        source_schema=tx_schema,
        referent_schema=blk_schema,
    )
