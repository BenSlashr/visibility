"""Add AnalysisTopics table for NLP support

Revision ID: abc123def456
Revises: 455ae67e840e
Create Date: 2025-01-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = '455ae67e840e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Créer la table analysis_topics pour le support NLP"""
    
    # Vérifier si la table existe déjà
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'analysis_topics' not in inspector.get_table_names():
        # Créer la table analysis_topics
        op.create_table('analysis_topics',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('analysis_id', sa.String(), nullable=False),
            sa.Column('seo_intent', sa.String(), nullable=False),
            sa.Column('seo_confidence', sa.Float(), nullable=False, default=0.0),
            sa.Column('seo_detailed_scores', sa.JSON(), nullable=True),
            sa.Column('business_topics', sa.JSON(), nullable=True),
            sa.Column('content_type', sa.String(), nullable=True),
            sa.Column('content_confidence', sa.Float(), nullable=True, default=0.0),
            sa.Column('sector_entities', sa.JSON(), nullable=True),
            sa.Column('semantic_keywords', sa.JSON(), nullable=True),
            sa.Column('global_confidence', sa.Float(), nullable=False, default=0.0),
            sa.Column('sector_context', sa.String(), nullable=True),
            sa.Column('processing_version', sa.String(), nullable=True, default='1.0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('analysis_id', name='uq_analysis_topics_analysis_id')
        )
        
        # Créer les index pour optimiser les performances
        op.create_index('idx_analysis_topics_intent', 'analysis_topics', ['seo_intent', 'seo_confidence'])
        op.create_index('idx_analysis_topics_content_type', 'analysis_topics', ['content_type'])
        op.create_index('idx_analysis_topics_confidence', 'analysis_topics', ['global_confidence'])
        op.create_index('idx_analysis_topics_sector', 'analysis_topics', ['sector_context'])
        
        print("✅ Table analysis_topics créée avec succès")
    else:
        print("ℹ️  Table analysis_topics existe déjà, pas de modification nécessaire")


def downgrade() -> None:
    """Supprimer la table analysis_topics"""
    
    # Vérifier si la table existe
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'analysis_topics' in inspector.get_table_names():
        # Supprimer les index d'abord
        try:
            op.drop_index('idx_analysis_topics_sector', table_name='analysis_topics')
            op.drop_index('idx_analysis_topics_confidence', table_name='analysis_topics')
            op.drop_index('idx_analysis_topics_content_type', table_name='analysis_topics')
            op.drop_index('idx_analysis_topics_intent', table_name='analysis_topics')
        except Exception as e:
            print(f"Avertissement: Erreur lors de la suppression des index: {e}")
        
        # Supprimer la table
        op.drop_table('analysis_topics')
        print("✅ Table analysis_topics supprimée")
    else:
        print("ℹ️  Table analysis_topics n'existe pas, pas de suppression nécessaire")