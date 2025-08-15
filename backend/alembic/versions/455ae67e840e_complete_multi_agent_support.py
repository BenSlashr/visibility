"""Complete multi-agent support

Revision ID: 455ae67e840e
Revises: d9266be91414
Create Date: 2025-01-28 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '455ae67e840e'
down_revision = 'd9266be91414'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Vérifier si les modifications ont déjà été appliquées
    connection = op.get_bind()
    
    # 1. Rendre ai_model_id nullable dans prompts (si pas déjà fait)
    try:
        # SQLite ne supporte pas ALTER COLUMN directement, on doit recréer la table
        # Mais seulement si ai_model_id n'est pas déjà nullable
        
        # Vérifier si ai_model_id est nullable
        result = connection.execute(sa.text("PRAGMA table_info(prompts);")).fetchall()
        ai_model_nullable = False
        for col in result:
            if col[1] == 'ai_model_id' and col[3] == 0:  # col[3] = notnull (0 = nullable, 1 = not null)
                ai_model_nullable = True
                break
        
        if not ai_model_nullable:
            # ai_model_id est encore NOT NULL, on doit le corriger
            print("🔧 Correction: Rendre ai_model_id nullable dans prompts")
            
            # Sauvegarder les données existantes
            op.execute("""
                CREATE TABLE prompts_backup AS 
                SELECT * FROM prompts;
            """)
            
            # Supprimer la table existante
            op.drop_table('prompts')
            
            # Recréer la table avec ai_model_id nullable
            op.create_table('prompts',
                sa.Column('id', sa.String(), nullable=False),
                sa.Column('project_id', sa.String(), nullable=False),
                sa.Column('ai_model_id', sa.String(), nullable=True),  # Maintenant nullable
                sa.Column('name', sa.String(), nullable=False),
                sa.Column('template', sa.Text(), nullable=False),
                sa.Column('description', sa.Text(), nullable=True),
                sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
                sa.Column('is_multi_agent', sa.Boolean(), nullable=True, default=False),
                sa.Column('last_executed_at', sa.DateTime(), nullable=True),
                sa.Column('execution_count', sa.Integer(), nullable=True, default=0),
                sa.Column('created_at', sa.DateTime(), nullable=False),
                sa.Column('updated_at', sa.DateTime(), nullable=True),
                sa.PrimaryKeyConstraint('id'),
                sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
                sa.ForeignKeyConstraint(['ai_model_id'], ['ai_models.id'])
            )
            
            # Restaurer les données
            op.execute("""
                INSERT INTO prompts (id, project_id, ai_model_id, name, template, description, 
                                   is_active, is_multi_agent, last_executed_at, execution_count, 
                                   created_at, updated_at)
                SELECT id, project_id, ai_model_id, name, template, description, 
                       is_active, is_multi_agent, last_executed_at, execution_count, 
                       created_at, updated_at
                FROM prompts_backup;
            """)
            
            # Supprimer la sauvegarde
            op.execute("DROP TABLE prompts_backup;")
            
            # Recréer les index
            op.create_index('idx_prompts_project', 'prompts', ['project_id', 'is_active'])
            op.create_index('idx_prompts_model', 'prompts', ['ai_model_id'])
            op.create_index('idx_prompts_multi_agent', 'prompts', ['is_multi_agent'])
            op.create_index('idx_prompts_last_executed', 'prompts', ['last_executed_at'])
        else:
            print("✅ ai_model_id est déjà nullable dans prompts")
            
    except Exception as e:
        print(f"⚠️ Erreur lors de la modification de prompts: {e}")
    
    # 2. Vérifier que prompt_ai_models existe (normalement déjà créée)
    try:
        tables = connection.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_ai_models';")).fetchall()
        if not tables:
            print("🔧 Création de la table prompt_ai_models")
            op.create_table('prompt_ai_models',
                sa.Column('prompt_id', sa.String(), nullable=False),
                sa.Column('ai_model_id', sa.String(), nullable=False),
                sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
                sa.Column('created_at', sa.DateTime(), nullable=False),
                sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
                sa.ForeignKeyConstraint(['ai_model_id'], ['ai_models.id'], ondelete='CASCADE'),
                sa.PrimaryKeyConstraint('prompt_id', 'ai_model_id')
            )
            op.create_index('idx_prompt_ai_models_prompt', 'prompt_ai_models', ['prompt_id'])
            op.create_index('idx_prompt_ai_models_active', 'prompt_ai_models', ['is_active'])
        else:
            print("✅ Table prompt_ai_models existe déjà")
    except Exception as e:
        print(f"⚠️ Erreur avec prompt_ai_models: {e}")
    
    # 3. Passer variables_used de TEXT à JSON dans analyses (SQLite: recréation)
    try:
        print("🔧 Migration: variables_used TEXT -> JSON dans analyses")
        # Sauvegarde
        op.execute("""
            CREATE TABLE analyses_backup AS 
            SELECT * FROM analyses;
        """)
        # Drop
        op.drop_table('analyses')
        # Recreate avec JSON
        op.create_table('analyses',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('prompt_id', sa.String(), nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('ai_model_id', sa.String(), nullable=True),
            sa.Column('prompt_executed', sa.Text(), nullable=False),
            sa.Column('ai_response', sa.Text(), nullable=False),
            sa.Column('variables_used', sa.JSON(), nullable=True),
            sa.Column('brand_mentioned', sa.Boolean(), nullable=True, default=False),
            sa.Column('website_mentioned', sa.Boolean(), nullable=True, default=False),
            sa.Column('website_linked', sa.Boolean(), nullable=True, default=False),
            sa.Column('ranking_position', sa.Integer(), nullable=True),
            sa.Column('ai_model_used', sa.String(), nullable=False),
            sa.Column('tokens_used', sa.Integer(), nullable=True, default=0),
            sa.Column('processing_time_ms', sa.Integer(), nullable=True, default=0),
            sa.Column('cost_estimated', sa.Float(), nullable=True, default=0.0),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['ai_model_id'], ['ai_models.id'])
        )
        # Restaurer (variables_used: JSON parse best-effort)
        op.execute("""
            INSERT INTO analyses (
                id, prompt_id, project_id, ai_model_id, prompt_executed, ai_response,
                variables_used, brand_mentioned, website_mentioned, website_linked,
                ranking_position, ai_model_used, tokens_used, processing_time_ms,
                cost_estimated, created_at, updated_at
            )
            SELECT 
                id, prompt_id, project_id, ai_model_id, prompt_executed, ai_response,
                CASE 
                    WHEN variables_used IS NULL OR variables_used = '' THEN NULL 
                    ELSE variables_used 
                END as variables_used,
                brand_mentioned, website_mentioned, website_linked,
                ranking_position, ai_model_used, tokens_used, processing_time_ms,
                cost_estimated, created_at, updated_at
            FROM analyses_backup;
        """)
        op.execute("DROP TABLE analyses_backup;")
        # Index
        op.create_index('idx_analyses_project_date', 'analyses', ['project_id', 'created_at'])
        op.create_index('idx_analyses_prompt_date', 'analyses', ['prompt_id', 'created_at'])
        op.create_index('idx_analyses_ai_model', 'analyses', ['ai_model_id'])
        op.create_index('idx_analyses_brand_mentioned', 'analyses', ['brand_mentioned', 'created_at'])
        op.create_index('idx_analyses_ranking', 'analyses', ['ranking_position', 'created_at'])
    except Exception as e:
        print(f"⚠️ Erreur migration JSON variables_used: {e}")
    
    # 4. Migrer les données existantes vers prompt_ai_models (si pas déjà fait)
    try:
        # Vérifier s'il y a déjà des données dans prompt_ai_models
        count = connection.execute(sa.text("SELECT COUNT(*) FROM prompt_ai_models;")).scalar()
        if count == 0:
            print("🔧 Migration des données vers prompt_ai_models")
            # Migrer tous les prompts existants
            connection.execute(sa.text("""
                INSERT INTO prompt_ai_models (prompt_id, ai_model_id, is_active, created_at)
                SELECT id, ai_model_id, 1, created_at
                FROM prompts 
                WHERE ai_model_id IS NOT NULL
            """))
            print(f"✅ {connection.execute(sa.text('SELECT COUNT(*) FROM prompt_ai_models;')).scalar()} relations migrées")
        else:
            print(f"✅ prompt_ai_models contient déjà {count} relations")
    except Exception as e:
        print(f"⚠️ Erreur lors de la migration des données: {e}")


def downgrade() -> None:
    # Restaurer l'état précédent
    
    # 1. Supprimer la table prompt_ai_models
    op.drop_table('prompt_ai_models')
    
    # 2. Rendre ai_model_id NOT NULL dans prompts
    # (Complexe avec SQLite, on va juste supprimer les colonnes ajoutées)
    
    # 3. Supprimer les colonnes ajoutées
    # Note: SQLite ne supporte pas DROP COLUMN, donc on recrée la table
    connection = op.get_bind()
    
    # Sauvegarder les données
    op.execute("""
        CREATE TABLE prompts_backup AS 
        SELECT id, project_id, ai_model_id, name, template, description, 
               is_active, last_executed_at, execution_count, created_at, updated_at
        FROM prompts
        WHERE ai_model_id IS NOT NULL;
    """)
    
    # Supprimer la table
    op.drop_table('prompts')
    
    # Recréer sans is_multi_agent et avec ai_model_id NOT NULL
    op.create_table('prompts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('ai_model_id', sa.String(), nullable=False),  # Retour à NOT NULL
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('template', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_model_id'], ['ai_models.id'])
    )
    
    # Restaurer les données
    op.execute("""
        INSERT INTO prompts (id, project_id, ai_model_id, name, template, description, 
                           is_active, last_executed_at, execution_count, created_at, updated_at)
        SELECT id, project_id, ai_model_id, name, template, description, 
               is_active, last_executed_at, execution_count, created_at, updated_at
        FROM prompts_backup;
    """)
    
    # Supprimer la sauvegarde
    op.execute("DROP TABLE prompts_backup;") 