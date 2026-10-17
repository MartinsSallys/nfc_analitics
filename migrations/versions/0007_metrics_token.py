"""Token de consulta privada por loja, armazenado apenas como hash.

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stores", sa.Column("metrics_token_hash", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_stores_metrics_token_hash", "stores", ["metrics_token_hash"])


def downgrade():
    op.drop_constraint("uq_stores_metrics_token_hash", "stores", type_="unique")
    op.drop_column("stores", "metrics_token_hash")
