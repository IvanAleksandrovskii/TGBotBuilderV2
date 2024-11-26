"""added ai tests transcription model

Revision ID: 2feff3b78537
Revises: cbbad9c67fe2
Create Date: 2024-11-26 16:44:55.214310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2feff3b78537'
down_revision: Union[str, None] = 'cbbad9c67fe2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('psyco_tests_ai_transcriptions',
    sa.Column('sender_chat_id', sa.BigInteger(), nullable=False),
    sa.Column('reciver_chat_id', sa.BigInteger(), nullable=False),
    sa.Column('tests_ids', sa.String(), nullable=False),
    sa.Column('transcription', sa.String(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_psyco_tests_ai_transcriptions'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('psyco_tests_ai_transcriptions')
    # ### end Alembic commands ###
