"""add analysis_sources table

Revision ID: 7890abcd1234
Revises: 455ae67e840e
Create Date: 2025-08-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7890abcd1234'
down_revision = '455ae67e840e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'analysis_sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('analysis_id', sa.String(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('citation_label', sa.String(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.Column('fetch_error', sa.String(), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE')
    )

    op.create_index('idx_analysis_sources_analysis', 'analysis_sources', ['analysis_id'])
    op.create_index('idx_analysis_sources_domain', 'analysis_sources', ['domain'])
    # Ajout colonne web_search_used sur analyses si absente
    try:
        op.add_column('analyses', sa.Column('web_search_used', sa.Boolean(), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('idx_analysis_sources_domain', table_name='analysis_sources')
    op.drop_index('idx_analysis_sources_analysis', table_name='analysis_sources')
    op.drop_table('analysis_sources')
    try:
        op.drop_column('analyses', 'web_search_used')
    except Exception:
        pass


