"""create initial tables

Revision ID: e23588f3a510
Revises:
Create Date: 2026-10-26
"""

from typing import Sequence, Union


revision: str = "e23588f3a510"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial database tables."""
    pass


def downgrade() -> None:
    """Remove the initial database tables."""
    pass
