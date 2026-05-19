from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app import db
from app.models.models import Article, User
from app.utils import generate_slug
from app.email_utils import send_newsletter_notification
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from datetime import datetime

articles_bp = Blueprint('articles', __name__, url_prefix='/articles')

# === FORMULAIRES ===
class ArticleForm(FlaskForm):
    title = StringField('Titre', validators=[
        DataRequired(),
        Length(min=5, max=255, message='Titre entre 5 et 255 caractères')
    ])
    excerpt = TextAreaField('Résumé', validators=[
        Length(max=500, message='Résumé max 500 caractères')
    ])
    content = TextAreaField('Contenu', validators=[DataRequired()])
    category = SelectField('Catégorie', choices=[
        ('news', 'Actualité'),
        ('event', 'Événement'),
        ('announcement', 'Annonce')
    ])
    is_published = BooleanField('Publier maintenant')
    submit = SubmitField('Sauvegarder')

# === ROUTES ===
@articles_bp.route('/')
def list_articles():
    """Liste des actualités publiées avec recherche"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    query = Article.query.options(joinedload(Article.author)).filter_by(is_published=True)

    if search:
        like = f'%{search}%'
        query = query.filter(
            (Article.title.ilike(like)) |
            (Article.excerpt.ilike(like)) |
            (Article.content.ilike(like))
        )

    if category:
        query = query.filter_by(category=category)

    articles = query.order_by(Article.published_at.desc()).paginate(page=page, per_page=10)

    return render_template('articles/list.html', articles=articles, search=search, category=category)

@articles_bp.route('/<slug>')
def view_article(slug):
    """Visualiser un article"""
    article = Article.query.filter_by(slug=slug).first_or_404()
    
    # Apenas articles published
    if not article.is_published and (not current_user.is_authenticated or current_user.id != article.author_id):
        return redirect(url_for('articles.list_articles'))
    
    return render_template('articles/view.html', article=article)

@articles_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_article():
    """Créer un nouvel article"""
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            slug=generate_slug(form.title.data),
            content=form.content.data,
            excerpt=form.excerpt.data or '',
            category=form.category.data,
            author_id=current_user.id,
            is_published=form.is_published.data,
            published_at=datetime.utcnow() if form.is_published.data else None
        )
        
        db.session.add(article)
        db.session.commit()

        if article.is_published:
            send_newsletter_notification(article)

        flash(f'Article "{article.title}" créé avec succès !', 'success')
        return redirect(url_for('articles.view_article', slug=article.slug))
    
    return render_template('articles/edit.html', form=form, title='Nouvel Article')

@articles_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    """Modifier un article"""
    article = Article.query.get_or_404(article_id)
    
    # Vérification de permission
    if article.author_id != current_user.id and current_user.role != 'admin':
        flash('Vous n\'avez pas la permission de modifier cet article.', 'danger')
        return redirect(url_for('articles.view_article', slug=article.slug))
    
    form = ArticleForm()
    if form.validate_on_submit():
        was_published = article.is_published
        article.title = form.title.data
        article.slug = generate_slug(form.title.data)
        article.content = form.content.data
        article.excerpt = form.excerpt.data
        article.category = form.category.data
        article.is_published = form.is_published.data
        if form.is_published.data and not article.published_at:
            article.published_at = datetime.utcnow()
        elif not form.is_published.data:
            article.published_at = None
        
        db.session.commit()

        # Notifier uniquement lors de la transition brouillon → publié
        if not was_published and article.is_published:
            send_newsletter_notification(article)

        flash(f'Article "{article.title}" modifié avec succès !', 'success')
        return redirect(url_for('articles.view_article', slug=article.slug))
    
    elif request.method == 'GET':
        form.title.data = article.title
        form.excerpt.data = article.excerpt
        form.content.data = article.content
        form.category.data = article.category
        form.is_published.data = article.is_published
    
    return render_template('articles/edit.html', form=form, article=article, title='Modifier Article')

@articles_bp.route('/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    """Supprimer un article"""
    article = Article.query.get_or_404(article_id)
    
    # Vérification de permission
    if article.author_id != current_user.id and current_user.role != 'admin':
        flash('Vous n\'avez pas la permission de supprimer cet article.', 'danger')
        return redirect(url_for('articles.list_articles'))
    
    title = article.title
    db.session.delete(article)
    db.session.commit()
    
    flash(f'Article "{title}" supprimé avec succès !', 'success')
    return redirect(url_for('articles.list_articles'))

@articles_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Tableau de bord admin pour la gestion des articles"""
    if current_user.role not in ['admin', 'moderator']:
        flash('Accès réservé aux administrateurs.', 'danger')
        return redirect(url_for('main.index'))
    
    articles = Article.query.options(joinedload(Article.author)).order_by(Article.created_at.desc()).all()
    return render_template('articles/admin_dashboard.html', articles=articles)

