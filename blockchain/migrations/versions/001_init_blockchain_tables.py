"""init blockchain tables

Revision ID: 001
Revises:
Create Date: 2025-03-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blockchain_blocks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("nonce", sa.Integer(), nullable=False),
        sa.Column("previous_hash", sa.String(), nullable=False),
        sa.Column("hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "idx_blockchain_block_index",
        "blockchain_blocks",
        ["index"],
        unique=True,
    )
    op.create_index(
        "idx_blockchain_block_hash",
        "blockchain_blocks",
        ["hash"],
        unique=True,
    )
    op.create_index(
        "idx_blockchain_block_created_at",
        "blockchain_blocks",
        ["created_at"],
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "block_id",
            sa.String(36),
            sa.ForeignKey("blockchain_blocks.id"),
            nullable=False,
        ),
        sa.Column("election_id", sa.String(), nullable=False),
        sa.Column("voter_id", sa.String(), nullable=False),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "idx_bc_tx_block_id",
        "transactions",
        ["block_id"],
    )
    op.create_index(
        "idx_bc_tx_election_id",
        "transactions",
        ["election_id"],
    )
    op.create_index(
        "idx_bc_tx_voter_id",
        "transactions",
        ["voter_id"],
    )
    op.create_index(
        "idx_bc_tx_candidate_id",
        "transactions",
        ["candidate_id"],
    )
    op.create_index(
        "idx_bc_tx_created_at",
        "transactions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("blockchain_blocks")
