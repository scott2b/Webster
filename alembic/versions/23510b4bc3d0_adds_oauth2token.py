"""Adds OAuth2Token

Revision ID: 23510b4bc3d0
Revises: 49403f9c4712
Create Date: 2020-10-24 19:40:44.537538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23510b4bc3d0'
down_revision = '49403f9c4712'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('oauth2_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=True),
    sa.Column('token_type', sa.String(length=40), nullable=True),
    sa.Column('access_token', sa.String(length=48), nullable=False),
    sa.Column('refresh_token', sa.String(length=96), nullable=True),
    sa.Column('scope', sa.Text(), nullable=True),
    sa.Column('revoked', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('refreshed_at', sa.DateTime(), nullable=False),
    sa.Column('access_token_expires_at', sa.DateTime(), nullable=False),
    sa.Column('refresh_token_expires_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['oauth2_clients.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth2_tokens_access_token'), 'oauth2_tokens', ['access_token'], unique=True)
    op.create_index(op.f('ix_oauth2_tokens_refresh_token'), 'oauth2_tokens', ['refresh_token'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_oauth2_tokens_refresh_token'), table_name='oauth2_tokens')
    op.drop_index(op.f('ix_oauth2_tokens_access_token'), table_name='oauth2_tokens')
    op.drop_table('oauth2_tokens')
    # ### end Alembic commands ###
