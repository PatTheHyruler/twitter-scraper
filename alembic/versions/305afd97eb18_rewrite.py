"""Rewrite

Revision ID: 305afd97eb18
Revises: 
Create Date: 2023-02-04 22:47:22.819688

"""
from alembic import op
import sqlalchemy as sa

from model.types.int_list import IntList

# revision identifiers, used by Alembic.
revision = '305afd97eb18'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('media',
    sa.Column('db_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('media_key', sa.String(length=32), nullable=True),
    sa.Column('type', sa.Enum('ANIMATED_GIF', 'PHOTO', 'VIDEO', name='emediatype'), nullable=False),
    sa.Column('url', sa.String(length=1024), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('width', sa.Integer(), nullable=True),
    sa.Column('height', sa.Integer(), nullable=True),
    sa.Column('view_count', sa.Integer(), nullable=True),
    sa.Column('alt_text', sa.String(length=1024), nullable=True),
    sa.Column('tweet_id', sa.BigInteger(), nullable=False),
    sa.Column('downloaded', sa.Boolean(), nullable=False),
    sa.Column('file_path', sa.String(length=512), nullable=True),
    sa.PrimaryKeyConstraint('db_id')
    )
    op.create_index(op.f('ix_media_downloaded'), 'media', ['downloaded'], unique=False)
    op.create_index(op.f('ix_media_media_key'), 'media', ['media_key'], unique=False)
    op.create_index(op.f('ix_media_tweet_id'), 'media', ['tweet_id'], unique=False)
    op.create_table('queued_tweet',
    sa.Column('db_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tweet_id', sa.BigInteger(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('db_id')
    )
    op.create_index(op.f('ix_queued_tweet_priority'), 'queued_tweet', ['priority'], unique=False)
    op.create_index(op.f('ix_queued_tweet_tweet_id'), 'queued_tweet', ['tweet_id'], unique=False)
    op.create_index('queued_tweet_tweet_id_priority_index', 'queued_tweet', ['tweet_id', 'priority'], unique=False)
    op.create_table('saved_tweet',
    sa.Column('db_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('saved_type', sa.Enum('BOOKMARK', 'LIKE', 'PIN', name='esavedtweettype'), nullable=False),
    sa.Column('tweet_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('db_id')
    )
    op.create_index(op.f('ix_saved_tweet_saved_type'), 'saved_tweet', ['saved_type'], unique=False)
    op.create_index(op.f('ix_saved_tweet_tweet_id'), 'saved_tweet', ['tweet_id'], unique=False)
    op.create_index(op.f('ix_saved_tweet_user_id'), 'saved_tweet', ['user_id'], unique=False)
    op.create_index('saved_tweet_tweet_user_index', 'saved_tweet', ['tweet_id', 'user_id'], unique=False)
    op.create_table('tweet',
    sa.Column('db_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id', sa.BigInteger(), nullable=True),
    sa.Column('text', sa.String(length=512), nullable=False),
    sa.Column('edit_history_tweet_ids', IntList(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('entities', sa.String(length=4096), nullable=False),
    sa.Column('retweet_count', sa.Integer(), nullable=False),
    sa.Column('reply_count', sa.Integer(), nullable=False),
    sa.Column('like_count', sa.Integer(), nullable=False),
    sa.Column('quote_count', sa.Integer(), nullable=False),
    sa.Column('added_directly', sa.Boolean(), nullable=False),
    sa.Column('last_fetched', sa.DateTime(), nullable=False),
    sa.Column('author_id', sa.BigInteger(), nullable=False),
    sa.Column('conversation_id', sa.BigInteger(), nullable=False),
    sa.Column('replied_tweet_id', sa.BigInteger(), nullable=True),
    sa.Column('quoted_tweet_id', sa.BigInteger(), nullable=True),
    sa.Column('retweeted_tweet_id', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('db_id')
    )
    op.create_index(op.f('ix_tweet_author_id'), 'tweet', ['author_id'], unique=False)
    op.create_index(op.f('ix_tweet_conversation_id'), 'tweet', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_tweet_id'), 'tweet', ['id'], unique=False)
    op.create_index(op.f('ix_tweet_quoted_tweet_id'), 'tweet', ['quoted_tweet_id'], unique=False)
    op.create_index(op.f('ix_tweet_replied_tweet_id'), 'tweet', ['replied_tweet_id'], unique=False)
    op.create_index(op.f('ix_tweet_retweeted_tweet_id'), 'tweet', ['retweeted_tweet_id'], unique=False)
    op.create_table('user',
    sa.Column('db_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id', sa.BigInteger(), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('description', sa.String(length=512), nullable=True),
    sa.Column('entities', sa.String(length=4096), nullable=False),
    sa.Column('location', sa.String(length=128), nullable=True),
    sa.Column('profile_image_url', sa.String(length=1024), nullable=False),
    sa.Column('profile_image_downloaded', sa.Boolean(), nullable=False),
    sa.Column('profile_image_file_path', sa.String(length=512), nullable=True),
    sa.Column('followers_count', sa.Integer(), nullable=False),
    sa.Column('following_count', sa.Integer(), nullable=False),
    sa.Column('tweet_count', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=1024), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('db_id')
    )
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_name'), 'user', ['name'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
    op.create_table('video_version',
    sa.Column('db_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('url', sa.String(length=1024), nullable=False),
    sa.Column('content_type', sa.String(length=64), nullable=False),
    sa.Column('bit_rate', sa.Integer(), nullable=True),
    sa.Column('video_key', sa.String(length=32), nullable=False),
    sa.Column('downloaded', sa.Boolean(), nullable=False),
    sa.Column('file_path', sa.String(length=512), nullable=True),
    sa.PrimaryKeyConstraint('db_id')
    )
    op.create_index(op.f('ix_video_version_video_key'), 'video_version', ['video_key'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_video_version_video_key'), table_name='video_version')
    op.drop_table('video_version')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_name'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_tweet_retweeted_tweet_id'), table_name='tweet')
    op.drop_index(op.f('ix_tweet_replied_tweet_id'), table_name='tweet')
    op.drop_index(op.f('ix_tweet_quoted_tweet_id'), table_name='tweet')
    op.drop_index(op.f('ix_tweet_id'), table_name='tweet')
    op.drop_index(op.f('ix_tweet_conversation_id'), table_name='tweet')
    op.drop_index(op.f('ix_tweet_author_id'), table_name='tweet')
    op.drop_table('tweet')
    op.drop_index('saved_tweet_tweet_user_index', table_name='saved_tweet')
    op.drop_index(op.f('ix_saved_tweet_user_id'), table_name='saved_tweet')
    op.drop_index(op.f('ix_saved_tweet_tweet_id'), table_name='saved_tweet')
    op.drop_index(op.f('ix_saved_tweet_saved_type'), table_name='saved_tweet')
    op.drop_table('saved_tweet')
    op.drop_index('queued_tweet_tweet_id_priority_index', table_name='queued_tweet')
    op.drop_index(op.f('ix_queued_tweet_tweet_id'), table_name='queued_tweet')
    op.drop_index(op.f('ix_queued_tweet_priority'), table_name='queued_tweet')
    op.drop_table('queued_tweet')
    op.drop_index(op.f('ix_media_tweet_id'), table_name='media')
    op.drop_index(op.f('ix_media_media_key'), table_name='media')
    op.drop_index(op.f('ix_media_downloaded'), table_name='media')
    op.drop_table('media')
    # ### end Alembic commands ###
