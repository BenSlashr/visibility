"""
Configuration des dictionnaires de mots-clés pour la classification NLP
Utilisé par AdvancedTopicsClassifier pour analyser l'intention SEO et les business topics
"""

# =============================================================================
# SEO INTENT CLASSIFICATION
# =============================================================================

SEO_INTENT_KEYWORDS = {
    'commercial': {
        # Comparaisons et choix
        'comparaison': ['vs', 'versus', 'contre', 'comparaison', 'différence', 'compare', 'comparer', 'face à face', 'côte à côte'],
        'choix': ['meilleur', 'meilleure', 'meilleures', 'top', 'classement', 'ranking', 'choisir', 'sélectionner', 'recommandé'],
        'alternatives': ['alternative', 'concurrent', 'remplacer', 'substitut', 'équivalent', 'similaire', 'plutôt que'],
        'achat': ['acheter', 'achat', 'commander', 'commande', 'boutique', 'magasin', 'vendeur', 'distributeur', 'fournisseur'],
        'prix': ['prix', 'coût', 'coûte', 'tarif', 'budget', 'gratuit', 'payant', 'abonnement', 'licence', 'investissement'],
        'evaluation': ['avis', 'test', 'review', 'évaluation', 'note', 'recommandation', 'opinion', 'retour', 'expérience'],
        'decision': ['conseillé', 'suggéré', 'propose', 'recommande', 'convient', 'adapté', 'idéal', 'parfait'],
        'qualite_prix': ['rapport qualité prix', 'vaut le coup', 'bon plan', 'rentable', 'pas donné', 'abordable'],
        
        # Pondération : intention très commerciale
        'weight': 2.0
    },
    
    'informational': {
        # Questions et définitions
        'questions': ['comment', 'pourquoi', 'qu\'est-ce', 'que', 'quoi', 'qui', 'où', 'quand', 'combien'],
        'definitions': ['définition', 'signifie', 'veut dire', 'c\'est quoi', 'qu\'est-ce que', 'définir'],
        'explanations': ['explication', 'explique', 'principe', 'fonctionnement', 'marche', 'fonctionne'],
        'guides': ['guide', 'tutoriel', 'tuto', 'manuel', 'documentation', 'aide', 'mode d\'emploi'],
        'learning': ['apprendre', 'comprendre', 'savoir', 'connaître', 'découvrir', 'étudier'],
        'types': ['types', 'sortes', 'catégories', 'genres', 'variétés', 'modèles', 'versions'],
        'history': ['histoire', 'origine', 'évolution', 'développement', 'création', 'invention'],
        'general_info': ['information', 'renseigner', 'informer', 'détails', 'précisions'],
        
        # Pondération : neutre
        'weight': 1.0
    },
    
    'transactional': {
        # Actions et utilisation
        'installation': ['installer', 'installation', 'configurer', 'configuration', 'paramétrer', 'setup', 'mise en place'],
        'utilisation': ['utiliser', 'utilisation', 'démarrer', 'lancer', 'activer', 'mettre en marche', 'démarrage'],
        'maintenance': ['réparer', 'dépanner', 'maintenance', 'entretien', 'nettoyer', 'vérifier', 'réparation'],
        'programmation': ['programmer', 'paramétrer', 'régler', 'ajuster', 'personnaliser', 'customiser'],
        'download': ['télécharger', 'download', 'installer', 'application', 'app', 'logiciel'],
        'etapes': ['étapes', 'procédure', 'méthode', 'processus', 'marche à suivre', 'instruction'],
        'troubleshooting': ['problème', 'erreur', 'bug', 'panne', 'dysfonctionnement', 'ne marche pas', 'résoudre'],
        'actions': ['créer', 'faire', 'réaliser', 'effectuer', 'exécuter', 'accomplir'],
        
        # Pondération : action oriented
        'weight': 1.5
    },
    
    'navigational': {
        # Recherche d'entreprises/sites
        'contact': ['contact', 'contacter', 'joindre', 'téléphone', 'email', 'adresse', 'coordonnées'],
        'site': ['site officiel', 'site web', 'website', 'page', 'url', 'lien', 'site internet'],
        'support': ['support', 'assistance', 'aide', 'service client', 'helpdesk', 'support technique'],
        'account': ['compte', 'connexion', 'login', 'inscription', 'profil', 'enregistrement'],
        'company': ['entreprise', 'société', 'compagnie', 'marque', 'fabricant', 'constructeur'],
        'location': ['où trouver', 'magasin', 'revendeur', 'distributeur', 'proche', 'près de chez'],
        'download_official': ['télécharger depuis', 'version officielle', 'authentique', 'original'],
        'access': ['accéder', 'aller sur', 'se rendre', 'visiter', 'consulter'],
        
        # Pondération : peu commercial
        'weight': 0.5
    }
}

# =============================================================================
# BUSINESS TOPICS PAR SECTEUR
# =============================================================================

BUSINESS_TOPICS = {
    'domotique': {
        'pricing': {
            'keywords': [
                'prix', 'coût', 'tarif', 'budget', 'investissement', 'rentabilité', 'économie', 
                'pas cher', 'abordable', 'onéreux', 'gratuit', 'payant', 'subscription', 'abonnement',
                'rapport qualité prix', 'amortissement', 'retour sur investissement', 'ROI'
            ],
            'weight': 1.0
        },
        'features': {
            'keywords': [
                'fonction', 'fonctionnalité', 'option', 'caractéristique', 'capacité', 
                'possibilité', 'performance', 'qualité', 'avantage', 'bénéfice', 'atout',
                'innovation', 'nouveauté', 'évolution', 'amélioration'
            ],
            'weight': 1.0
        },
        'installation': {
            'keywords': [
                'installation', 'installer', 'montage', 'pose', 'configuration', 'setup',
                'câblage', 'branchement', 'connexion', 'raccordement', 'mise en service',
                'facilité installation', 'plug and play', 'prêt à l\'emploi'
            ],
            'weight': 1.2
        },
        'compatibility': {
            'keywords': [
                'compatible', 'compatibilité', 'intégration', 'fonctionne avec', 'support',
                'protocole', 'standard', 'norme', 'interopérabilité', 'ouvert',
                'écosystème', 'connectivité', 'liaison'
            ],
            'weight': 1.1
        },
        'security': {
            'keywords': [
                'sécurité', 'sécurisé', 'protection', 'chiffrement', 'cryptage', 'piratage',
                'vulnérabilité', 'authentification', 'mot de passe', 'confidentialité',
                'privacy', 'données personnelles', 'RGPD'
            ],
            'weight': 1.3
        },
        'automation': {
            'keywords': [
                'automatisation', 'automatique', 'programmable', 'scénario', 'routine',
                'intelligence', 'smart', 'intelligent', 'adaptatif', 'apprentissage',
                'IA', 'machine learning', 'algorithme'
            ],
            'weight': 1.2
        },
        'control': {
            'keywords': [
                'contrôle', 'commande', 'pilotage', 'gestion', 'supervision', 'monitoring',
                'surveillance', 'télécommande', 'application mobile', 'app',
                'interface', 'dashboard', 'tableau de bord'
            ],
            'weight': 1.0
        },
        'energy': {
            'keywords': [
                'énergie', 'énergétique', 'consommation', 'économie', 'efficacité',
                'optimisation', 'chauffage', 'climatisation', 'éclairage', 'électricité',
                'isolation', 'thermique', 'température'
            ],
            'weight': 1.4
        }
    },
    
    'tech_general': {
        'performance': {
            'keywords': [
                'performance', 'vitesse', 'rapidité', 'lenteur', 'optimisation', 'benchmark',
                'temps de réponse', 'latence', 'débit', 'bande passante', 'fluidité',
                'réactivité', 'efficacité'
            ],
            'weight': 1.2
        },
        'usability': {
            'keywords': [
                'facilité', 'simple', 'complexe', 'ergonomie', 'interface', 'UX', 'convivial',
                'intuitive', 'apprentissage', 'prise en main', 'user friendly',
                'accessibilité', 'navigation'
            ],
            'weight': 1.0
        },
        'reliability': {
            'keywords': [
                'fiabilité', 'fiable', 'stable', 'robuste', 'panne', 'dysfonctionnement',
                'bug', 'erreur', 'disponibilité', 'uptime', 'continuité',
                'résistance', 'durabilité'
            ],
            'weight': 1.3
        },
        'scalability': {
            'keywords': [
                'évolutif', 'extensible', 'modulaire', 'croissance', 'adaptation',
                'mise à niveau', 'upgrade', 'extension', 'expansion',
                'flexible', 'personnalisable'
            ],
            'weight': 1.1
        },
        'support': {
            'keywords': [
                'support', 'assistance', 'aide', 'documentation', 'formation',
                'communauté', 'forum', 'tutoriel', 'guide', 'FAQ',
                'service client', 'helpdesk'
            ],
            'weight': 0.9
        }
    },
    
    'saas_software': {
        'subscription': {
            'keywords': [
                'abonnement', 'mensuel', 'annuel', 'licence', 'plan', 'freemium',
                'essai gratuit', 'trial', 'premium', 'pro', 'enterprise',
                'tarification', 'pricing'
            ],
            'weight': 1.4
        },
        'integration': {
            'keywords': [
                'intégration', 'API', 'webhook', 'connecteur', 'plugin', 'extension',
                'synchronisation', 'import', 'export', 'connexion',
                'liaison', 'passerelle'
            ],
            'weight': 1.2
        },
        'collaboration': {
            'keywords': [
                'collaboration', 'équipe', 'partage', 'workflow', 'gestion de projet',
                'permissions', 'rôles', 'utilisateurs', 'teamwork',
                'coopération', 'travail collaboratif'
            ],
            'weight': 1.0
        },
        'analytics': {
            'keywords': [
                'analytics', 'analyse', 'rapport', 'statistiques', 'métriques',
                'dashboard', 'KPI', 'insight', 'données', 'reporting',
                'business intelligence', 'data'
            ],
            'weight': 1.1
        }
    }
}

# =============================================================================
# MOTS-CLÉS SECTORIELS SPÉCIALISÉS
# =============================================================================

SECTOR_SPECIFIC_KEYWORDS = {
    'domotique': {
        'brands': [
            'Somfy', 'Legrand', 'Schneider Electric', 'Honeywell', 'Control4', 'Fibaro', 
            'Devolo', 'Zipato', 'Vera', 'SmartThings', 'Hubitat', 'Jeedom', 'Home Assistant',
            'Netatmo', 'Philips Hue', 'IKEA Tradfri', 'Xiaomi', 'Aqara', 'Shelly'
        ],
        'products': [
            'TaHoma', 'Connexoon', 'Home + Control', 'Wiser', 'Céliane', 'Mosaic',
            'Dexxo', 'Oximo', 'Yslo', 'Evolvia', 'Smoove', 'Situo', 'Nina'
        ],
        'technologies': [
            'Z-Wave', 'Zigbee', 'KNX', 'WiFi', 'Thread', 'Matter', 'EnOcean',
            'Bluetooth', 'LoRa', 'RF433', 'Infrarouge', 'Mesh', 'X10'
        ],
        'devices': [
            'volet roulant', 'store', 'portail', 'garage', 'éclairage', 'prise connectée',
            'interrupteur', 'détecteur', 'capteur', 'caméra', 'thermostat', 'radiateur',
            'serrure connectée', 'sonnette', 'alarme', 'sirène'
        ],
        'functions': [
            'programmation', 'scénario', 'automatisation', 'géolocalisation', 'planning',
            'minuterie', 'temporisation', 'condition', 'trigger', 'action', 'routine',
            'simulation présence', 'mode absence'
        ]
    },
    
    'marketing_digital': {
        'channels': [
            'SEO', 'SEA', 'social media', 'email marketing', 'content marketing',
            'influencer marketing', 'affiliate marketing', 'display', 'retargeting',
            'programmatic', 'native advertising'
        ],
        'metrics': [
            'CTR', 'CPC', 'CPM', 'ROAS', 'ROI', 'conversion', 'lead', 'impression',
            'reach', 'engagement', 'bounce rate', 'time on site', 'pages par session'
        ],
        'tools': [
            'Google Analytics', 'Google Ads', 'Facebook Ads', 'LinkedIn Ads', 'Mailchimp',
            'HubSpot', 'Salesforce', 'SEMrush', 'Ahrefs', 'Moz', 'Hotjar'
        ],
        'strategies': [
            'inbound', 'outbound', 'funnel', 'nurturing', 'segmentation', 'personalization',
            'automation', 'A/B testing', 'attribution', 'remarketing'
        ]
    },
    
    'ecommerce': {
        'platforms': [
            'Shopify', 'WooCommerce', 'Magento', 'PrestaShop', 'BigCommerce',
            'Salesforce Commerce', 'Amazon', 'eBay', 'Etsy', 'Cdiscount'
        ],
        'payment': [
            'PayPal', 'Stripe', 'Klarna', 'Apple Pay', 'Google Pay', 'carte bancaire',
            'virement', 'chèque', 'espèces', '3x sans frais', 'paiement sécurisé'
        ],
        'logistics': [
            'livraison', 'expédition', 'transport', 'stock', 'entrepôt', 'dropshipping',
            'fulfillment', 'retour', 'échange', 'garantie', 'SAV'
        ],
        'optimization': [
            'conversion', 'panier abandonné', 'upselling', 'cross-selling',
            'recommandation', 'personnalisation', 'checkout', 'landing page',
            'CRO', 'UX ecommerce'
        ]
    }
}

# =============================================================================
# EXPRESSIONS ET LOCUTIONS FRANÇAISES
# =============================================================================

FRENCH_EXPRESSIONS = {
    'commercial_expressions': [
        'rapport qualité prix', 'vaut le coup', 'bon plan', 'meilleur choix',
        'investissement rentable', 'pas donné', 'haut de gamme', 'entrée de gamme',
        'milieu de gamme', 'sur mesure', 'clé en main', 'tout compris',
        'sans engagement', 'satisfait ou remboursé', 'essai gratuit',
        'money back guarantee', 'retour sur investissement'
    ],
    
    'comparison_expressions': [
        'face à face', 'côte à côte', 'en comparaison', 'par rapport à',
        'contrairement à', 'à la différence de', 'tandis que', 'alors que',
        'en revanche', 'au contraire', 'plutôt que', 'à la place de',
        'en opposition', 'versus'
    ],
    
    'recommendation_expressions': [
        'je recommande', 'je conseille', 'je suggère', 'à privilégier',
        'à éviter', 'excellent choix', 'parfait pour', 'idéal si',
        'convient bien', 'adapté aux', 'destiné aux', 'pensé pour',
        'fait pour', 'conçu pour'
    ],
    
    'technical_expressions': [
        'facile à utiliser', 'prise en main', 'courbe d\'apprentissage',
        'plug and play', 'prêt à l\'emploi', 'paramétrage avancé',
        'mode expert', 'interface intuitive', 'ergonomie soignée',
        'user friendly', 'clé en main'
    ]
}

# =============================================================================
# CONFIGURATION DE SCORING
# =============================================================================

SCORING_CONFIG = {
    'confidence_thresholds': {
        'high': 0.7,
        'medium': 0.4,
        'low': 0.0
    },
    
    'topic_relevance_thresholds': {
        'high': 5.0,
        'medium': 2.0,
        'low': 0.0
    },
    
    'minimum_keyword_length': 3,
    'context_window_size': 10,
    'max_topics_returned': 5
}