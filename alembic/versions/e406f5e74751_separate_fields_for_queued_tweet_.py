"""Separate fields for queued tweet failures

Revision ID: e406f5e74751
Revises: e8487242e5bb
Create Date: 2023-02-06 19:50:38.156993

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e406f5e74751'
down_revision = 'e8487242e5bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('queued_tweet', sa.Column('tweet_failed', sa.Boolean(), nullable=False))
    op.add_column('queued_tweet', sa.Column('replies_failed', sa.Boolean(), nullable=False))
    op.create_index(op.f('ix_queued_tweet_replies_failed'), 'queued_tweet', ['replies_failed'], unique=False)
    op.create_index(op.f('ix_queued_tweet_tweet_failed'), 'queued_tweet', ['tweet_failed'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_queued_tweet_tweet_failed'), table_name='queued_tweet')
    op.drop_index(op.f('ix_queued_tweet_replies_failed'), table_name='queued_tweet')
    op.drop_column('queued_tweet', 'replies_failed')
    op.drop_column('queued_tweet', 'tweet_failed')
    # ### end Alembic commands ###
