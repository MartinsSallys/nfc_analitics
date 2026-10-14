"""Cria os destinos das lojas.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column(
            "destination",
            sa.Enum(
                "google",
                "whatsapp",
                "instagram",
                native_enum=False,
                create_constraint=True,
                name="link_destination",
            ),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "destination", name="uq_links_store_destination"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
    )
    op.create_index("ix_links_store_id", "links", ["store_id"])


def downgrade():
    op.drop_table("links")
