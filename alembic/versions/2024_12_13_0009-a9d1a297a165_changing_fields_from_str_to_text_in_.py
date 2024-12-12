"""Changing fields from str to text in text and test

Revision ID: a9d1a297a165
Revises: 2feff3b78537
Create Date: 2024-12-13 00:09:39.325996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9d1a297a165'
down_revision: Union[str, None] = '2feff3b78537'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tests', 'description',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=False)
    op.alter_column('texts', 'body',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('texts', 'body',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('tests', 'description',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    # ### end Alembic commands ###