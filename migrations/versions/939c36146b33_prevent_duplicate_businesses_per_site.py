"""prevent duplicate businesses per site

Revision ID: 939c36146b33
Revises: 76f9e71a6602
Create Date: 2026-10-30 11:43:46.432973
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "939c36146b33"
down_revision: Union[str, Sequence[str], None] = "217e6c5990a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM business
                    GROUP BY site_id, business_name
                    HAVING COUNT(*) > 1
                ) THEN
                    RAISE EXCEPTION
                        'Duplicate business names exist within the same site. '
                        'Resolve duplicates before applying this migration.';
                END IF;
            END $$;
            """
        )
    )

    op.create_unique_constraint(
        "uq_business_site_name",
        "business",
        ["site_id", "business_name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_business_site_name",
        "business",
        type_="unique",
    )
