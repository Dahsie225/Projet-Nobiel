import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, Response
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from app import db
from app.models.models import User, Member, Article, Adhesion, Media
from app.email_utils import send_member_activated, send_adhesion_approved, send_newsletter_notification
from app.utils import generate_slug
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Décorateur pour vérifier que l'utilisateur est admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'moderator']:
            flash('Accès refusé. Seuls les administrateurs peuvent accéder à cette page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

SECTIONS_CONFIG = [
    {'city': 'Abidjan',   'icon': '🌍', 'is_national': True},
    {'city': 'Sassandra', 'icon': '🏙️', 'is_national': False},
    {'city': 'San-Pédro', 'icon': '🏙️', 'is_national': False},
    {'city': 'Korogho',   'icon': '🏙️', 'is_national': False},
    {'city': 'Bouaké',    'icon': '🏙️', 'is_national': False},
    {'city': 'Man',       'icon': '🏙️', 'is_national': False},
]

SECTION_ROLE_LABELS = {
    'president':      'Président',
    'vice_president': 'Vice-Président',
    'secretary':      'Secrétaire',
    'treasurer':      'Trésorier',
    'member':         'Membre',
}

# ===== DASHBOARD =====
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Page principale du tableau de bord admin"""
    stats = {
        'total_members': Member.query.count(),
        'active_members': Member.query.filter_by(membership_status='active').count(),
        'pending_members': Member.query.filter_by(membership_status='pending').count(),
        'total_articles': Article.query.count(),
        'total_adhesions': Adhesion.query.count(),
        'pending_adhesions': Adhesion.query.filter_by(payment_status='pending').count(),
        'paid_adhesions': Adhesion.query.filter_by(payment_status='paid').count(),
    }

    # Articles récents
    recent_articles = Article.query.options(joinedload(Article.author)).order_by(Article.published_at.desc()).limit(5).all()

    # Adhésions récentes
    recent_adhesions = Adhesion.query.order_by(Adhesion.created_at.desc()).limit(5).all()

    # Revenus du mois
    first_day_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    adhesions_month = Adhesion.query.filter(
        Adhesion.paid_at >= first_day_month,
        Adhesion.payment_status == 'paid'
    ).all()
    revenue_month = sum(a.amount for a in adhesions_month if a.amount)
    stats['revenue_month'] = revenue_month

    return render_template('admin/dashboard.html', stats=stats,
                           recent_articles=recent_articles,
                           recent_adhesions=recent_adhesions)


@admin_bp.route('/sections')
@login_required
@admin_required
def manage_sections():
    """Page de gestion des responsables de sections régionales"""
    sections_data = []
    for s in SECTIONS_CONFIG:
        city = s['city']
        city_members = (Member.query
                        .filter_by(city=city, membership_status='active')
                        .order_by(Member.first_name)
                        .all())
        leaders = {m.section_role: m for m in city_members
                   if m.section_role and m.section_role != 'member'}
        sections_data.append({
            'city': city,
            'icon': s['icon'],
            'is_national': s['is_national'],
            'members': city_members,
            'leaders': leaders,
        })
    return render_template('admin/sections.html',
                           sections_data=sections_data,
                           role_labels=SECTION_ROLE_LABELS)


@admin_bp.route('/sections/assign-role', methods=['POST'])
@login_required
@admin_required
def assign_section_role():
    """Assigner un rôle à un membre dans une section"""
    city = request.form.get('city', '').strip()
    member_id = request.form.get('member_id', type=int)
    role = request.form.get('role', '').strip()

    valid_roles = ['president', 'vice_president', 'secretary', 'treasurer', 'member']
    valid_cities = [s['city'] for s in SECTIONS_CONFIG]

    if city not in valid_cities or role not in valid_roles:
        flash('Données invalides.', 'danger')
        return redirect(url_for('admin.manage_sections'))

    if role != 'member':
        current_holders = Member.query.filter_by(city=city, section_role=role).all()
        for m in current_holders:
            m.section_role = 'member'

    member = Member.query.get_or_404(member_id)
    if member.city != city:
        flash('Ce membre n\'appartient pas à cette section.', 'danger')
        return redirect(url_for('admin.manage_sections'))

    member.section_role = role
    db.session.commit()

    flash(f'✅ {member.full_name} est maintenant {SECTION_ROLE_LABELS[role]} de la section {city}.', 'success')
    return redirect(url_for('admin.manage_sections'))

# ===== GESTION DES ADHÉSIONS =====
@admin_bp.route('/adhesions')
@login_required
@admin_required
def manage_adhesions():
    """Liste toutes les adhésions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = Adhesion.query
    
    if status_filter:
        query = query.filter_by(payment_status=status_filter)
    
    adhesions = query.order_by(Adhesion.created_at.desc()).paginate(page=page, per_page=20)
    
    stats = {
        'total': Adhesion.query.count(),
        'pending': Adhesion.query.filter_by(payment_status='pending').count(),
        'paid': Adhesion.query.filter_by(payment_status='paid').count(),
        'cancelled': Adhesion.query.filter_by(payment_status='cancelled').count(),
    }
    
    return render_template('admin/adhesions.html', adhesions=adhesions, stats=stats, 
                         current_status=status_filter)

@admin_bp.route('/adhesions/<int:adhesion_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_adhesion(adhesion_id):
    """Approuver une adhésion"""
    adhesion = Adhesion.query.get_or_404(adhesion_id)
    adhesion.payment_status = 'paid'
    adhesion.paid_at = datetime.utcnow()
    db.session.commit()
    send_adhesion_approved(adhesion)
    flash(f'Adhésion approuvée.', 'success')
    return redirect(url_for('admin.manage_adhesions'))

@admin_bp.route('/adhesions/<int:adhesion_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_adhesion(adhesion_id):
    """Rejeter une adhésion"""
    adhesion = Adhesion.query.get_or_404(adhesion_id)
    adhesion.payment_status = 'cancelled'
    db.session.commit()
    flash(f'Adhésion rejetée.', 'success')
    return redirect(url_for('admin.manage_adhesions'))

@admin_bp.route('/adhesions/<int:adhesion_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_adhesion(adhesion_id):
    """Modifier une adhésion"""
    adhesion = Adhesion.query.get_or_404(adhesion_id)
    
    if request.method == 'POST':
        adhesion.adhesion_type = request.form.get('adhesion_type')
        adhesion.amount = float(request.form.get('amount', 0))
        adhesion.payment_status = request.form.get('payment_status')
        adhesion.payment_method = request.form.get('payment_method')
        adhesion.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Adhésion mise à jour avec succès.', 'success')
        return redirect(url_for('admin.manage_adhesions'))
    
    return render_template('admin/edit_adhesion.html', adhesion=adhesion)

@admin_bp.route('/adhesions/export')
@login_required
@admin_required
def export_adhesions():
    """Exporter les adhésions en CSV (streaming, sans charger toute la table)"""
    import csv
    from io import StringIO

    def generate():
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(['ID', 'Membre', 'Type', 'Montant', 'Statut', 'Méthode', 'Date'])
        yield buf.getvalue()

        q = Adhesion.query.options(joinedload(Adhesion.member)).order_by(Adhesion.id).yield_per(200)
        for adhesion in q:
            buf = StringIO()
            writer = csv.writer(buf)
            writer.writerow([
                adhesion.id,
                adhesion.member.full_name if adhesion.member else '',
                adhesion.adhesion_type,
                adhesion.amount,
                adhesion.payment_status,
                adhesion.payment_method,
                adhesion.created_at.strftime('%Y-%m-%d')
            ])
            yield buf.getvalue()

    return Response(
        generate(),
        status=200,
        headers={
            'Content-Disposition': 'attachment; filename=adhesions.csv',
            'Content-Type': 'text/csv; charset=utf-8',
        }
    )

# ===== GESTION DES ARTICLES =====
@admin_bp.route('/articles')
@login_required
@admin_required
def manage_articles():
    """Liste tous les articles"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    
    query = Article.query.options(joinedload(Article.author))
    
    if status == 'published':
        query = query.filter(Article.published_at.isnot(None))
    elif status == 'draft':
        query = query.filter(Article.published_at.is_(None))
    
    articles = query.order_by(Article.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/articles.html', articles=articles, current_status=status)

@admin_bp.route('/articles/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_article_admin():
    """Créer un nouvel article"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'News')
        publish = request.form.get('publish') == 'on'
        
        if not title or not content:
            flash('Le titre et le contenu sont obligatoires.', 'danger')
            return redirect(url_for('admin.create_article_admin'))
        
        article = Article(
            title=title,
            slug=generate_slug(title),
            excerpt=excerpt,
            content=content,
            category=category,
            author_id=current_user.id,
            is_published=publish,
            published_at=datetime.utcnow() if publish else None
        )
        
        db.session.add(article)
        db.session.commit()

        if publish:
            send_newsletter_notification(article)

        flash('Article créé avec succès.', 'success')
        return redirect(url_for('admin.manage_articles'))
    
    return render_template('admin/create_article.html')

@admin_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_article_admin(article_id):
    """Modifier un article"""
    article = Article.query.get_or_404(article_id)
    
    if article.author_id != current_user.id and current_user.role != 'admin':
        flash('Vous ne pouvez modifier que vos propres articles.', 'danger')
        return redirect(url_for('admin.manage_articles'))
    
    if request.method == 'POST':
        was_published = article.is_published
        article.title = request.form.get('title', '').strip()
        article.slug = generate_slug(article.title)
        article.excerpt = request.form.get('excerpt', '').strip()
        article.content = request.form.get('content', '').strip()
        article.category = request.form.get('category', 'News')
        
        publish = request.form.get('publish') == 'on'
        article.is_published = publish
        if publish and not article.published_at:
            article.published_at = datetime.utcnow()
        elif not publish:
            article.published_at = None
        
        db.session.commit()

        if not was_published and publish:
            send_newsletter_notification(article)

        flash('Article mis à jour avec succès.', 'success')
        return redirect(url_for('admin.manage_articles'))
    
    return render_template('admin/edit_article_admin.html', article=article)

@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_article_admin(article_id):
    """Supprimer un article"""
    article = Article.query.get_or_404(article_id)
    
    if article.author_id != current_user.id and current_user.role != 'admin':
        flash('Vous ne pouvez supprimer que vos propres articles.', 'danger')
        return redirect(url_for('admin.manage_articles'))
    
    db.session.delete(article)
    db.session.commit()
    flash('Article supprimé avec succès.', 'success')
    return redirect(url_for('admin.manage_articles'))

# ===== GESTION DES MEMBRES (ANNUAIRE) =====
@admin_bp.route('/members')
@login_required
@admin_required
def manage_members():
    """Liste tous les membres"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    search = request.args.get('search', '', type=str)
    
    query = Member.query
    
    if status:
        query = query.filter_by(membership_status=status)
    
    if search:
        query = query.filter(
            (Member.first_name.ilike(f'%{search}%')) |
            (Member.last_name.ilike(f'%{search}%')) |
            (Member.email.ilike(f'%{search}%')) |
            (Member.city.ilike(f'%{search}%'))
        )
    
    members = query.order_by(Member.last_name).paginate(page=page, per_page=25)
    
    stats = {
        'total': Member.query.count(),
        'active': Member.query.filter_by(membership_status='active').count(),
        'pending': Member.query.filter_by(membership_status='pending').count(),
        'inactive': Member.query.filter_by(membership_status='inactive').count(),
    }
    
    return render_template('admin/members.html', members=members, stats=stats, 
                         current_status=status, search=search)

@admin_bp.route('/members/<int:member_id>')
@login_required
@admin_required
def view_member_admin(member_id):
    """Voir les détails d'un membre"""
    member = Member.query.get_or_404(member_id)
    return render_template('admin/view_member.html', member=member)

@admin_bp.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_member_admin(member_id):
    """Modifier un membre"""
    member = Member.query.get_or_404(member_id)
    
    if request.method == 'POST':
        member.first_name = request.form.get('first_name', '').strip()
        member.last_name = request.form.get('last_name', '').strip()
        member.email = request.form.get('email', '').strip()
        member.phone = request.form.get('phone', '').strip()
        member.gender = request.form.get('gender', '')
        member.address = request.form.get('address', '').strip()
        member.city = request.form.get('city', '').strip()
        member.postal_code = request.form.get('postal_code', '').strip()
        member.membership_type = request.form.get('membership_type')
        member.membership_status = request.form.get('membership_status')
        member.section_role = request.form.get('section_role', 'member')
        member.notes = request.form.get('notes', '').strip()
        
        db.session.commit()
        flash('Membre mis à jour avec succès.', 'success')
        return redirect(url_for('admin.manage_members'))
    
    return render_template('admin/edit_member.html', member=member)

@admin_bp.route('/members/<int:member_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_member(member_id):
    """Activer un membre"""
    member = Member.query.get_or_404(member_id)
    member.membership_status = 'active'
    db.session.commit()
    send_member_activated(member)
    flash(f'Membre {member.full_name} activé.', 'success')
    return redirect(url_for('admin.manage_members'))

@admin_bp.route('/members/<int:member_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_member(member_id):
    """Désactiver un membre"""
    member = Member.query.get_or_404(member_id)
    member.membership_status = 'inactive'
    db.session.commit()
    flash(f'Membre {member.full_name} désactivé.', 'success')
    return redirect(url_for('admin.manage_members'))

@admin_bp.route('/members/<int:member_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_member(member_id):
    """Supprimer définitivement un membre"""
    member = Member.query.get_or_404(member_id)
    full_name = member.full_name
    
    # Supprimer les adhésions associées
    Adhesion.query.filter_by(member_id=member_id).delete()
    
    # Supprimer le membre
    db.session.delete(member)
    db.session.commit()
    
    flash(f'Membre {full_name} supprimé définitivement.', 'success')
    return redirect(url_for('admin.manage_members'))

# ===== GESTION DES PAIEMENTS =====
@admin_bp.route('/payments')
@login_required
@admin_required
def manage_payments():
    """Gérer les paiements"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    method = request.args.get('method', '', type=str)
    
    query = Adhesion.query
    
    if status:
        query = query.filter_by(payment_status=status)
    
    if method:
        query = query.filter_by(payment_method=method)
    
    payments = query.order_by(Adhesion.created_at.desc()).paginate(page=page, per_page=20)
    
    # Statistiques
    stats = {
        'total': Adhesion.query.count(),
        'pending': Adhesion.query.filter_by(payment_status='pending').count(),
        'paid': Adhesion.query.filter_by(payment_status='paid').count(),
        'cancelled': Adhesion.query.filter_by(payment_status='cancelled').count(),
    }
    
    # Revenus
    paid_adhesions = Adhesion.query.filter_by(payment_status='paid').all()
    stats['total_revenue'] = sum(a.amount for a in paid_adhesions if a.amount)
    
    return render_template('admin/payments.html', payments=payments, stats=stats, 
                         current_status=status, current_method=method)

@admin_bp.route('/payments/<int:adhesion_id>/mark-paid', methods=['POST'])
@login_required
@admin_required
def mark_payment_paid(adhesion_id):
    """Marquer un paiement comme payé"""
    adhesion = Adhesion.query.get_or_404(adhesion_id)
    adhesion.payment_status = 'paid'
    adhesion.paid_at = datetime.utcnow()
    db.session.commit()
    flash('Paiement marqué comme payé.', 'success')
    return redirect(url_for('admin.manage_payments'))

@admin_bp.route('/payments/<int:adhesion_id>/mark-pending', methods=['POST'])
@login_required
@admin_required
def mark_payment_pending(adhesion_id):
    """Marquer un paiement comme en attente"""
    adhesion = Adhesion.query.get_or_404(adhesion_id)
    adhesion.payment_status = 'pending'
    db.session.commit()
    flash('Paiement marqué comme en attente.', 'success')
    return redirect(url_for('admin.manage_payments'))

@admin_bp.route('/payments/report')
@login_required
@admin_required
def payment_report():
    """Rapport détaillé des paiements"""
    period = request.args.get('period', 'month', type=str)
    
    if period == 'month':
        start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'year':
        start_date = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    payments = Adhesion.query.filter(Adhesion.paid_at >= start_date).all()
    
    report = {
        'period': period,
        'start_date': start_date,
        'total_payments': len(payments),
        'total_amount': sum(p.amount for p in payments if p.amount),
        'by_method': {},
        'by_type': {}
    }
    
    for payment in payments:
        # Par méthode
        method = payment.payment_method or 'Unknown'
        if method not in report['by_method']:
            report['by_method'][method] = {'count': 0, 'amount': 0}
        report['by_method'][method]['count'] += 1
        report['by_method'][method]['amount'] += payment.amount or 0
        
        # Par type
        ptype = payment.adhesion_type or 'Unknown'
        if ptype not in report['by_type']:
            report['by_type'][ptype] = {'count': 0, 'amount': 0}
        report['by_type'][ptype]['count'] += 1
        report['by_type'][ptype]['amount'] += payment.amount or 0
    
    return render_template('admin/payment_report.html', report=report, payments=payments)

# ===== ROUTES API POUR STATISTIQUES =====
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API pour récupérer les statistiques en JSON"""
    stats = {
        'members': {
            'total': Member.query.count(),
            'active': Member.query.filter_by(membership_status='active').count(),
            'pending': Member.query.filter_by(membership_status='pending').count(),
        },
        'articles': {
            'total': Article.query.count(),
            'published': Article.query.filter(Article.published_at.isnot(None)).count(),
        },
        'adhesions': {
            'total': Adhesion.query.count(),
            'paid': Adhesion.query.filter_by(payment_status='paid').count(),
            'pending': Adhesion.query.filter_by(payment_status='pending').count(),
        }
    }
    return jsonify(stats)


# ===== MÉDIAHÈQUE =====

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXT = {'mp4', 'mov', 'avi', 'webm', 'mkv'}

def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXT

def _allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXT


@admin_bp.route('/media')
@login_required
@admin_required
def media_list():
    """Lister tous les médias"""
    media_items = Media.query.order_by(Media.created_at.desc()).all()
    return render_template('admin/media.html', media_items=media_items)


@admin_bp.route('/media/upload', methods=['POST'])
@login_required
@admin_required
def media_upload():
    """Uploader un nouveau média (image ou vidéo)"""
    media_type = request.form.get('media_type', 'image')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    event_name = request.form.get('event_name', '').strip()
    event_date_str = request.form.get('event_date', '').strip()
    video_url = request.form.get('video_url', '').strip()

    if not title:
        flash('Le titre est obligatoire.', 'danger')
        return redirect(url_for('admin.media_list'))

    event_date = None
    if event_date_str:
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    file_path = None
    if media_type == 'image':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Veuillez sélectionner une image.', 'danger')
            return redirect(url_for('admin.media_list'))
        if not _allowed_image(file.filename):
            flash('Format d’image non autorisé. Utilisez PNG, JPG, GIF ou WEBP.', 'danger')
            return redirect(url_for('admin.media_list'))
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'media')
        os.makedirs(upload_dir, exist_ok=True)
        # Nom unique pour éviter les collisions
        base, ext = os.path.splitext(filename)
        unique_name = f"{base}_{int(datetime.utcnow().timestamp())}{ext}"
        file.save(os.path.join(upload_dir, unique_name))
        file_path = f'uploads/media/{unique_name}'

    elif media_type == 'video':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Veuillez sélectionner un fichier vidéo.', 'danger')
            return redirect(url_for('admin.media_list'))
        if not _allowed_video(file.filename):
            flash('Format vidéo non autorisé. Utilisez MP4, MOV, AVI ou WEBM.', 'danger')
            return redirect(url_for('admin.media_list'))
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'media')
        os.makedirs(upload_dir, exist_ok=True)
        base, ext = os.path.splitext(filename)
        unique_name = f"{base}_{int(datetime.utcnow().timestamp())}{ext}"
        file.save(os.path.join(upload_dir, unique_name))
        file_path = f'uploads/media/{unique_name}'

    media = Media(
        title=title,
        description=description or None,
        media_type=media_type,
        file_path=file_path,
        video_url=video_url or None,
        event_name=event_name or None,
        event_date=event_date,
        is_published=True,
        created_by=current_user.id,
    )
    db.session.add(media)
    db.session.commit()
    flash('Média ajouté avec succès.', 'success')
    return redirect(url_for('admin.media_list'))


@admin_bp.route('/media/upload/batch', methods=['POST'])
@login_required
@admin_required
def media_upload_batch():
    """Uploader plusieurs images en une seule fois"""
    event_name = request.form.get('event_name', '').strip()
    event_date_str = request.form.get('event_date', '').strip()

    event_date = None
    if event_date_str:
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        flash('Veuillez sélectionner au moins un fichier.', 'danger')
        return redirect(url_for('admin.media_list'))

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'media')
    os.makedirs(upload_dir, exist_ok=True)

    added = 0
    errors = []
    titles = request.form.getlist('titles')

    for idx, file in enumerate(files):
        if file.filename == '':
            continue

        # Détecter le type par l'extension
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext in ALLOWED_IMAGE_EXT:
            media_type = 'image'
        elif ext in ALLOWED_VIDEO_EXT:
            media_type = 'video'
        else:
            errors.append(f'Format non supporté : {file.filename}')
            continue

        # Titre : champ personnalisé ou nom du fichier sans extension
        title = (titles[idx].strip() if idx < len(titles) and titles[idx].strip()
                 else file.filename.rsplit('.', 1)[0])

        filename = secure_filename(file.filename)
        base, fext = os.path.splitext(filename)
        unique_name = f"{base}_{int(datetime.utcnow().timestamp())}_{idx}{fext}"
        file.save(os.path.join(upload_dir, unique_name))

        media = Media(
            title=title,
            media_type=media_type,
            file_path=f'uploads/media/{unique_name}',
            event_name=event_name or None,
            event_date=event_date,
            is_published=True,
            created_by=current_user.id,
        )
        db.session.add(media)
        added += 1

    if added:
        db.session.commit()
        flash(f'✅ {added} fichier(s) ajouté(s) avec succès.', 'success')
    if errors:
        flash('⚠️ Ignorés : ' + ', '.join(errors), 'warning')

    return redirect(url_for('admin.media_list'))


@admin_bp.route('/media/<int:media_id>/toggle', methods=['POST'])
@login_required
@admin_required
def media_toggle(media_id):
    """Publier / dépublier un média"""
    media = db.session.get(Media, media_id)
    if not media:
        flash('Média introuvable.', 'danger')
        return redirect(url_for('admin.media_list'))
    media.is_published = not media.is_published
    db.session.commit()
    state = 'publié' if media.is_published else 'dépublié'
    flash(f'Média "{media.title}" {state}.', 'success')
    return redirect(url_for('admin.media_list'))


@admin_bp.route('/media/<int:media_id>/delete', methods=['POST'])
@login_required
@admin_required
def media_delete(media_id):
    """Supprimer un média"""
    media = db.session.get(Media, media_id)
    if not media:
        flash('Média introuvable.', 'danger')
        return redirect(url_for('admin.media_list'))
    # Supprimer le fichier image si présent
    if media.file_path:
        full_path = os.path.join(current_app.root_path, 'static', media.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    db.session.delete(media)
    db.session.commit()
    flash(f'Média "{media.title}" supprimé.', 'success')
    return redirect(url_for('admin.media_list'))
