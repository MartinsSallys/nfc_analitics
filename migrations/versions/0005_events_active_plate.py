"""Registro mínimo de eventos com bloqueio de placas inativas.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plate_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "page_view",
                "google_click",
                "whatsapp_click",
                "instagram_click",
                native_enum=False,
                create_constraint=True,
                name="event_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["plate_id"], ["plates.id"]),
    )
    op.create_index("ix_events_plate_id", "events", ["plate_id"])
    op.execute("""
        CREATE FUNCTION enforce_active_event_plate() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE plate_active boolean;
        BEGIN
            SELECT is_active INTO plate_active FROM plates
            WHERE id = NEW.plate_id FOR SHARE;
            IF plate_active IS FALSE THEN
                RAISE EXCEPTION 'Inactive plate cannot receive new events'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER events_require_active_plate
        BEFORE INSERT OR UPDATE OF plate_id ON events
        FOR EACH ROW EXECUTE FUNCTION enforce_active_event_plate()
    """)


def downgrade():
    op.drop_table("events")
    op.execute("DROP FUNCTION enforce_active_event_plate()")
