#!/usr/bin/env python3
"""
Script pour appliquer la migration NLP manuellement
Utilisé lorsque Alembic n'est pas disponible
"""

import sqlite3
import os
import sys
from pathlib import Path

# Déterminer le chemin de la base de données
DB_PATH = Path(__file__).parent / "data" / "visibility.db"

def apply_nlp_migration():
    """Applique la migration pour créer la table analysis_topics"""
    
    if not DB_PATH.exists():
        print(f"❌ Base de données non trouvée: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Vérifier si la table existe déjà
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='analysis_topics'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Table analysis_topics existe déjà")
            conn.close()
            return True
        
        print("🔧 Création de la table analysis_topics...")
        
        # Créer la table analysis_topics
        cursor.execute("""
            CREATE TABLE analysis_topics (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL UNIQUE,
                seo_intent TEXT NOT NULL,
                seo_confidence REAL NOT NULL DEFAULT 0.0,
                seo_detailed_scores TEXT,  -- JSON en TEXT pour SQLite
                business_topics TEXT,      -- JSON en TEXT pour SQLite
                content_type TEXT,
                content_confidence REAL DEFAULT 0.0,
                sector_entities TEXT,      -- JSON en TEXT pour SQLite
                semantic_keywords TEXT,    -- JSON en TEXT pour SQLite
                global_confidence REAL NOT NULL DEFAULT 0.0,
                sector_context TEXT,
                processing_version TEXT DEFAULT '1.0',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
            )
        """)
        
        # Créer les index
        print("🔧 Création des index...")
        
        cursor.execute("""
            CREATE INDEX idx_analysis_topics_intent 
            ON analysis_topics (seo_intent, seo_confidence)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_analysis_topics_content_type 
            ON analysis_topics (content_type)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_analysis_topics_confidence 
            ON analysis_topics (global_confidence)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_analysis_topics_sector 
            ON analysis_topics (sector_context)
        """)
        
        # Trigger pour mettre à jour updated_at
        cursor.execute("""
            CREATE TRIGGER update_analysis_topics_updated_at
            AFTER UPDATE ON analysis_topics
            FOR EACH ROW
            BEGIN
                UPDATE analysis_topics 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
        
        # Fonction pour générer des UUIDs (simulée avec random)
        cursor.execute("""
            CREATE TRIGGER set_analysis_topics_id
            BEFORE INSERT ON analysis_topics
            FOR EACH ROW
            WHEN NEW.id IS NULL
            BEGIN
                UPDATE analysis_topics 
                SET id = (
                    lower(hex(randomblob(4))) || '-' || 
                    lower(hex(randomblob(2))) || '-' || 
                    '4' || substr(lower(hex(randomblob(2))), 2) || '-' || 
                    substr('ab89', 1 + (abs(random()) % 4), 1) || 
                    substr(lower(hex(randomblob(2))), 2) || '-' || 
                    lower(hex(randomblob(6)))
                )
                WHERE rowid = NEW.rowid;
            END
        """)
        
        conn.commit()
        
        # Vérifier que la table a été créée
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='analysis_topics'
        """)
        
        if cursor.fetchone():
            print("✅ Table analysis_topics créée avec succès")
            
            # Afficher les colonnes créées
            cursor.execute("PRAGMA table_info(analysis_topics)")
            columns = cursor.fetchall()
            print(f"📊 Colonnes créées: {len(columns)}")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            conn.close()
            return True
        else:
            print("❌ Erreur: Table non créée")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def check_nlp_migration():
    """Vérifie si la migration NLP est appliquée"""
    
    if not DB_PATH.exists():
        print(f"❌ Base de données non trouvée: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Vérifier la table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='analysis_topics'
        """)
        
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Compter les entrées
            cursor.execute("SELECT COUNT(*) FROM analysis_topics")
            count = cursor.fetchone()[0]
            print(f"✅ Table analysis_topics existe avec {count} entrées")
        else:
            print("❌ Table analysis_topics n'existe pas")
        
        conn.close()
        return table_exists
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Migration NLP pour Visibility-V2")
    print(f"📍 Base de données: {DB_PATH}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_nlp_migration()
    else:
        if apply_nlp_migration():
            print("\n🎉 Migration appliquée avec succès!")
            print("Vous pouvez maintenant utiliser les fonctionnalités NLP.")
        else:
            print("\n💥 Échec de la migration")
            sys.exit(1)