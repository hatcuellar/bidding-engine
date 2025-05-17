"""Initial schema

Revision ID: d72ce3cc7d3f
Revises: 
Create Date: 2023-05-16 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd72ce3cc7d3f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create brand_strategies table
    op.create_table('brand_strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=False),
        sa.Column('vpi_multiplier', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('strategy_config', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_brand_active', 'brand_strategies', ['brand_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_brand_strategies_brand_id'), 'brand_strategies', ['brand_id'], unique=False)
    op.create_index(op.f('ix_brand_strategies_id'), 'brand_strategies', ['id'], unique=False)

    # Create bid_history table
    op.create_table('bid_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=False),
        sa.Column('ad_slot_id', sa.Integer(), nullable=False),
        sa.Column('bid_amount', sa.Float(), nullable=False),
        sa.Column('normalized_value', sa.Float(), nullable=False),
        sa.Column('quality_factor', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('ctr', sa.Float(), nullable=True),
        sa.Column('cvr', sa.Float(), nullable=True),
        sa.Column('bid_type', sa.String(), nullable=False),
        sa.Column('bid_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bid_type_time', 'bid_history', ['bid_type', 'bid_timestamp'], unique=False)
    op.create_index('idx_brand_slot_time', 'bid_history', ['brand_id', 'ad_slot_id', 'bid_timestamp'], unique=False)
    op.create_index(op.f('ix_bid_history_ad_slot_id'), 'bid_history', ['ad_slot_id'], unique=False)
    op.create_index(op.f('ix_bid_history_bid_timestamp'), 'bid_history', ['bid_timestamp'], unique=False)
    op.create_index(op.f('ix_bid_history_brand_id'), 'bid_history', ['brand_id'], unique=False)
    op.create_index(op.f('ix_bid_history_id'), 'bid_history', ['id'], unique=False)

    # Create feature_cache table for metadata about cached features
    op.create_table('feature_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_key', sa.String(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('ttl_seconds', sa.Integer(), nullable=False, server_default='86400'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_cache_feature_key'), 'feature_cache', ['feature_key'], unique=True)
    op.create_index(op.f('ix_feature_cache_id'), 'feature_cache', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_feature_cache_id'), table_name='feature_cache')
    op.drop_index(op.f('ix_feature_cache_feature_key'), table_name='feature_cache')
    op.drop_table('feature_cache')
    
    op.drop_index(op.f('ix_bid_history_id'), table_name='bid_history')
    op.drop_index(op.f('ix_bid_history_brand_id'), table_name='bid_history')
    op.drop_index(op.f('ix_bid_history_bid_timestamp'), table_name='bid_history')
    op.drop_index(op.f('ix_bid_history_ad_slot_id'), table_name='bid_history')
    op.drop_index('idx_brand_slot_time', table_name='bid_history')
    op.drop_index('idx_bid_type_time', table_name='bid_history')
    op.drop_table('bid_history')
    
    op.drop_index(op.f('ix_brand_strategies_id'), table_name='brand_strategies')
    op.drop_index(op.f('ix_brand_strategies_brand_id'), table_name='brand_strategies')
    op.drop_index('idx_brand_active', table_name='brand_strategies')
    op.drop_table('brand_strategies')