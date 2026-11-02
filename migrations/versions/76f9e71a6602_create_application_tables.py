"""Keep the existing migration chain without recreating initial tables.

Revision ID: 76f9e71a6602
Revises: e23588f3a510
"""

from typing import Sequence, Union

revision: str = "76f9e71a6602"
down_revision: Union[str, Sequence[str], None] = "e23588f3a510"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
