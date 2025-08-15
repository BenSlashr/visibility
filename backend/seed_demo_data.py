#!/usr/bin/env python3
"""
Seed de données de démonstration pour le projet "Mon Site E-commerce".

Génère des analyses réparties sur plusieurs jours et modèles IA afin de
tester les graphiques (timeseries, comparaison modèles, heatmap, etc.).

Usage:
  python seed_demo_data.py --project "Mon Site E-commerce" --days 45 --per-day 4
"""
import argparse
import random
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.project import Project, ProjectKeyword, Competitor
from app.models.prompt import Prompt, PromptTag
from app.models.analysis import Analysis, AnalysisCompetitor
from app.models.ai_model import AIModel


def get_or_create_project(db, name: str) -> Project:
    project = db.query(Project).filter(Project.name == name).first()
    if project:
        return project
    project = Project(
        name=name,
        main_website="https://mon-site.com",
        description="Projet e-commerce de démonstration"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def ensure_keywords(db, project: Project, keywords):
    existing = db.query(ProjectKeyword).filter(ProjectKeyword.project_id == project.id).all()
    existing_set = {k.keyword for k in existing}
    for kw in keywords:
        if kw not in existing_set:
            db.add(ProjectKeyword(project_id=project.id, keyword=kw))
    db.commit()


def ensure_competitors(db, project: Project, competitors):
    existing = db.query(Competitor).filter(Competitor.project_id == project.id).all()
    existing_websites = {c.website for c in existing}
    for name, website in competitors:
        if website not in existing_websites:
            db.add(Competitor(project_id=project.id, name=name, website=website))
    db.commit()


def get_or_create_prompt(db, project: Project, name: str, template: str, tags):
    prompt = db.query(Prompt).filter(Prompt.project_id == project.id, Prompt.name == name).first()
    if prompt:
        return prompt
    prompt = Prompt(
        project_id=project.id,
        name=name,
        template=template,
        description="Prompt de démonstration",
        is_active=True,
        is_multi_agent=False,
    )
    db.add(prompt)
    db.flush()
    for t in tags:
        db.add(PromptTag(prompt_id=prompt.id, tag_name=t))
    db.commit()
    db.refresh(prompt)
    return prompt


def pick_models(db):
    # Prend quelques modèles actifs si disponibles
    models = db.query(AIModel).filter(AIModel.is_active == True).all()
    # Fallback: utiliser les identifiants connus si seed par défaut absent
    if not models:
        fallback_names = [
            'ChatGPT-4o Latest',
            'Claude 3 Haiku',
            'Gemini 2.0 Flash',
            'Mistral Small',
        ]
        models = [AIModel(name=n, provider='openai', model_identifier=n, max_tokens=4096, cost_per_1k_tokens=0.0015, is_active=True) for n in fallback_names]
        for m in models:
            db.add(m)
        db.commit()
        models = db.query(AIModel).filter(AIModel.is_active == True).all()
    return models


def random_ai_response(product_kw: str, brand_mentioned: bool, website_linked: bool) -> str:
    base = [
        f"Comparatif des meilleurs {product_kw} en 2025.",
        "Analyse des fonctionnalités, autonomie et rapport qualité/prix.",
        "Recommandations selon l'usage (gaming, pro, musique).",
    ]
    if brand_mentioned:
        base.append("Mon Site E-commerce propose une sélection intéressante.")
    if website_linked:
        base.append("Voir: https://mon-site.com")
    return "\n".join(base)


def generate_demo_analyses(db, project: Project, prompt: Prompt, models, days: int, per_day: int):
    keywords = [kw.keyword for kw in db.query(ProjectKeyword).filter(ProjectKeyword.project_id == project.id).all()] or [
        "casques gaming", "écouteurs bluetooth", "claviers mécaniques", "souris sans fil"
    ]
    competitors = [c.name for c in db.query(Competitor).filter(Competitor.project_id == project.id).all()]
    start_date = datetime.utcnow() - timedelta(days=days)

    for d in range(days):
        day = start_date + timedelta(days=d)
        for _ in range(per_day):
            model = random.choice(models)
            kw = random.choice(keywords)
            # Tirages pour la visibilité
            brand_mentioned = random.random() < 0.65
            website_linked = random.random() < 0.35
            website_mentioned = website_linked or (random.random() < 0.4)
            ranking_position = random.choice([None, 1, 2, 3, 4, 5, None, None])

            ai_text = random_ai_response(kw, brand_mentioned, website_linked)
            tokens_used = random.randint(120, 1200)
            processing_ms = random.randint(300, 4000)
            cost_estimated = round((tokens_used / 1000.0) * (model.cost_per_1k_tokens or 0.0015), 6)

            analysis = Analysis(
                prompt_id=prompt.id,
                project_id=project.id,
                ai_model_id=getattr(model, 'id', None),
                prompt_executed=prompt.template.replace('{project_name}', project.name).replace('{project_keywords}', ', '.join(keywords)),
                ai_response=ai_text,
                variables_used={"project_name": project.name, "project_keywords": ", ".join(keywords), "keyword": kw},
                brand_mentioned=brand_mentioned,
                website_mentioned=website_mentioned,
                website_linked=website_linked,
                ranking_position=ranking_position,
                ai_model_used=model.name,
                tokens_used=tokens_used,
                processing_time_ms=processing_ms,
                cost_estimated=cost_estimated,
                created_at=day + timedelta(hours=random.randint(8, 20), minutes=random.randint(0, 59))
            )
            db.add(analysis)
            db.flush()

            # Mentions concurrents aléatoires
            mentioned = random.sample(competitors, k=min(len(competitors), random.randint(0, 2))) if competitors else []
            for comp in mentioned:
                db.add(AnalysisCompetitor(
                    analysis_id=analysis.id,
                    competitor_name=comp,
                    is_mentioned=True,
                    ranking_position=None,
                    mention_context=f"Mention de {comp} dans la liste"
                ))
        db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', default='Mon Site E-commerce')
    parser.add_argument('--days', type=int, default=45)
    parser.add_argument('--per-day', type=int, default=4)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        project = get_or_create_project(db, args.project)
        ensure_keywords(db, project, [
            "casques gaming", "écouteurs bluetooth", "claviers mécaniques", "souris sans fil",
            "écrans 4k", "barres de son", "webcams full hd"
        ])
        ensure_competitors(db, project, [
            ("Amazon", "https://amazon.fr"),
            ("Cdiscount", "https://www.cdiscount.com"),
            ("Fnac", "https://www.fnac.com")
        ])
        prompt = get_or_create_prompt(
            db,
            project,
            name="Comparatif produits",
            template=(
                "Analyse les {project_keywords} et compare-les aux principaux concurrents du projet {project_name}. "
                "Indique si la marque est mentionnée et si un lien vers le site est présent."
            ),
            tags=["comparatif", "produits", "seo"]
        )
        models = pick_models(db)
        generate_demo_analyses(db, project, prompt, models, days=args.days, per_day=args.per_day)
        print(f"✅ Données de démo générées pour '{project.name}' sur {args.days} jours")
    finally:
        db.close()


if __name__ == '__main__':
    main()


