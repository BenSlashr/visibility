"""Add SERP functionality tables

Revision ID: 6f7a8b9c0d1e
Revises: 455ae67e840e
Create Date: 2025-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '6f7a8b9c0d1e'
down_revision = '455ae67e840e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajoute les tables pour la fonctionnalité SERP"""
    
    # Table serp_imports - Tracking des imports CSV
    op.create_table(
        'serp_imports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('import_date', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('total_keywords', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        
        # Contraintes
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    
    # Index pour optimiser les requêtes
    op.create_index('idx_serp_imports_project', 'serp_imports', ['project_id'])
    op.create_index('idx_serp_imports_active', 'serp_imports', ['project_id', 'is_active'])
    op.create_index('idx_serp_imports_date', 'serp_imports', ['import_date'])
    
    # Table serp_keywords - Mots-clés SERP importés
    op.create_table(
        'serp_keywords',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('import_id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('keyword', sa.String(), nullable=False),
        sa.Column('keyword_normalized', sa.String(), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        
        # Contraintes
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['import_id'], ['serp_imports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    
    # Index pour optimiser les requêtes
    op.create_index('idx_serp_keywords_project', 'serp_keywords', ['project_id'])
    op.create_index('idx_serp_keywords_import', 'serp_keywords', ['import_id'])
    op.create_index('idx_serp_keywords_normalized', 'serp_keywords', ['keyword_normalized'])
    op.create_index('idx_serp_keywords_position', 'serp_keywords', ['position'])
    
    # Table prompt_serp_associations - Associations prompts-keywords
    op.create_table(
        'prompt_serp_associations',
        sa.Column('prompt_id', sa.String(), nullable=False),
        sa.Column('serp_keyword_id', sa.String(), nullable=False),
        sa.Column('matching_score', sa.Float(), nullable=True),
        sa.Column('association_type', sa.String(), nullable=False, default='manual'),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        
        # Contraintes
        sa.PrimaryKeyConstraint('prompt_id', 'serp_keyword_id'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['serp_keyword_id'], ['serp_keywords.id'], ondelete='CASCADE'),
        
        # Check constraint pour association_type
        sa.CheckConstraint(
            "association_type IN ('manual', 'auto', 'suggested')",
            name='check_association_type'
        )
    )
    
    # Index pour optimiser les requêtes
    op.create_index('idx_prompt_serp_prompt', 'prompt_serp_associations', ['prompt_id'])
    op.create_index('idx_prompt_serp_keyword', 'prompt_serp_associations', ['serp_keyword_id'])
    op.create_index('idx_prompt_serp_type', 'prompt_serp_associations', ['association_type'])


def downgrade() -> None:
    """Supprime les tables SERP"""
    
    # Supprimer les tables dans l'ordre inverse (FK contraintes)
    op.drop_table('prompt_serp_associations')
    op.drop_table('serp_keywords')
    op.drop_table('serp_imports')