"""add_anonymous_voting

Revision ID: 001_anon
Revises: 90e4b7b5e523
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001_anon"
down_revision: Union[str, Sequence[str], None] = "90e4b7b5e523"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "election_settings",
        sa.Column("anonymous", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "anonymous_vote_tokens",
        sa.Column("election_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["election_id"], ["elections.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        "idx_anon_token_user_election",
        "anonymous_vote_tokens",
        ["user_id", "election_id"],
        unique=True,
    )
    op.create_index(
        "idx_anon_token_token", "anonymous_vote_tokens", ["token"], unique=True
    )
    op.create_index(
        "idx_anon_token_election", "anonymous_vote_tokens", ["election_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_anon_token_election", table_name="anonymous_vote_tokens")
    op.drop_index("idx_anon_token_token", table_name="anonymous_vote_tokens")
    op.drop_index("idx_anon_token_user_election", table_name="anonymous_vote_tokens")
    op.drop_table("anonymous_vote_tokens")
    op.drop_column("election_settings", "anonymous")
