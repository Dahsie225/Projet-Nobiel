from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from app import db, csrf
from app.models.models import Article, Member, Media, NewsletterSubscription
import re
import uuid
import hmac
import hashlib
import requests as http_requests

main_bp = Blueprint('main', __name__)

# ── CinetPay ────────────────────────────────────────────────────────────────
_CINETPAY_CHANNELS = {
    'orange': 'CI_ORANGEMONEY',
    'mtn':    'CI_MTNCIMOBILE',
    'wave':   'CI_WAVE',
}

@main_bp.route('/donate/pay', methods=['POST'])
@csrf.exempt
def donate_pay():
    """Initie un paiement CinetPay et retourne l'URL de checkout."""
    data = request.get_json(silent=True) or {}

    try:
        amount = int(str(data.get('amount', 0)).replace(' ', ''))
    except (ValueError, TypeError):
        return jsonify({'error': 'Montant invalide'}), 400

    if amount < 100:
        return jsonify({'error': 'Le montant minimum est 100 FCFA'}), 400

    method   = data.get('method', 'orange')
    don_type = data.get('type', 'Don Unique')
    phone    = str(data.get('phone', '')).strip()

    if not phone:
        return jsonify({'error': 'Numéro de téléphone requis'}), 400

    channel        = _CINETPAY_CHANNELS.get(method, 'CI_ORANGEMONEY')
    transaction_id = uuid.uuid4().hex[:20].upper()

    payload = {
        "apikey":        current_app.config.get('CINETPAY_API_KEY', ''),
        "site_id":       current_app.config.get('CINETPAY_SITE_ID', ''),
        "transaction_id": transaction_id,
        "amount":        amount,
        "currency":      "XOF",
        "description":   f"Don NOBIEL – {don_type}",
        "return_url":    url_for('main.donate_return', _external=True),
        "notify_url":    url_for('main.donate_notify', _external=True),
        "channels":      channel,
        "customer_name":         "Donateur",
        "customer_surname":      "NOBIEL",
        "customer_email":        "contact@nobiel.org",
        "customer_phone_number": phone,
        "customer_address":      "Abidjan",
        "customer_city":         "Abidjan",
        "customer_country":      "CI",
        "customer_state":        "CI",
        "customer_zip_code":     "00225",
    }

    try:
        resp = http_requests.post(
            'https://api-checkout.cinetpay.com/v2/payment',
            json=payload,
            timeout=15,
        )
        body = resp.json()
    except Exception as exc:
        return jsonify({'error': f'Erreur réseau: {exc}'}), 502

    if str(body.get('code')) == '201':
        payment_url = body['data']['payment_url']
        return jsonify({'payment_url': payment_url})

    return jsonify({'error': body.get('message', 'Erreur CinetPay')}), 400


@main_bp.route('/donate/return')
def donate_return():
    """Page de retour après paiement CinetPay."""
    return render_template('donate_return.html')


@main_bp.route('/donate/notify', methods=['POST'])
@csrf.exempt
def donate_notify():
    """Notification serveur-à-serveur de CinetPay (webhook)."""
    # Vérification de signature CinetPay
    secret_key = current_app.config.get('CINETPAY_SECRET_KEY', '')
    if secret_key:
        data = request.form  # CinetPay envoie en form-data
        cpm_site_id   = data.get('cpm_site_id', '')
        cpm_trans_id  = data.get('cpm_trans_id', '')
        cpm_amount    = data.get('cpm_amount', '')
        signature_received = data.get('cpm_password', '')
        # Construction de la chaîne à signer (format CinetPay)
        message = f"{cpm_site_id}{cpm_trans_id}{cpm_amount}{secret_key}"
        expected = hashlib.sha256(message.encode()).hexdigest()
        if not hmac.compare_digest(expected, signature_received):
            return '', 403
    return '', 200


@main_bp.route('/')
def index():
    """Page d'accueil"""
    # Statistiques globales
    total_members = Member.query.filter_by(membership_status='active').count()
    total_articles = Article.query.filter_by(is_published=True).count()
    
    # Récupérer le dernier article publié
    recent_articles = Article.query.filter_by(is_published=True).order_by(
        Article.published_at.desc()
    ).first()
    
    # Récupérer les médias publiés (6 derniers)
    media_items = Media.query.filter_by(is_published=True).order_by(
        Media.created_at.desc()
    ).limit(6).all()

    return render_template('index.html',
                         total_members=total_members,
                         total_articles=total_articles,
                         recent_articles=recent_articles,
                         media_items=media_items)

@main_bp.route('/about')
def about():
    """Page à propos"""
    return render_template('about.html')

@main_bp.route('/biographie-president')
def biographie_president():
    """Biographie du Président"""
    return render_template('president.html')

@main_bp.route('/organisation')
def organisation():
    """Lois, règlements intérieurs et Bureau National"""
    return render_template('organisation.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Page de contact"""
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not email or not message:
            flash('Veuillez remplir tous les champs obligatoires.', 'danger')
        else:
            # TODO: intégrer un envoi d'email (Flask-Mail) ici
            flash('Votre message a bien été envoyé. Nous vous répondrons rapidement !', 'success')
            return redirect(url_for('main.contact'))
    return render_template('contact.html')

@main_bp.route('/actions')
def discover_actions():
    """Page Découvrir nos actions"""
    # Récupérer tous les articles publiés
    articles = Article.query.filter_by(is_published=True).order_by(
        Article.published_at.desc()
    ).all()
    
    return render_template('discover_actions.html', articles=articles)

@main_bp.route('/donate')
def donate():
    """Page Faire un don"""
    return render_template('donate.html')

@main_bp.route('/sections-regionales')
def sections_regionales():
    """Page des sections régionales"""
    cities = ['Abidjan', 'Sassandra', 'San-Pédro', 'Korogho', 'Bouaké', 'Man']
    sections_stats = {}
    for city in cities:
        sections_stats[city] = Member.query.filter_by(
            city=city, membership_status='active'
        ).count()
    return render_template('sections_regionales.html', sections_stats=sections_stats)


@main_bp.route('/actions/education')
def action_education():
    return render_template('actions/education.html')

@main_bp.route('/actions/solidarite')
def action_solidarite():
    return render_template('actions/solidarite.html')

@main_bp.route('/actions/developpement')
def action_developpement():
    return render_template('actions/developpement.html')

@main_bp.route('/actions/assistance')
def action_assistance():
    return render_template('actions/assistance.html')


@main_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """Page Mon Compte — profil et changement de mot de passe"""
    member = Member.query.filter_by(email=current_user.email).first()

    if request.method == 'POST':
        current_pw  = request.form.get('current_password', '')
        new_pw      = request.form.get('new_password', '')
        confirm_pw  = request.form.get('confirm_password', '')

        if not current_user.check_password(current_pw):
            flash('Mot de passe actuel incorrect.', 'danger')
        elif len(new_pw) < 8:
            flash('Le nouveau mot de passe doit comporter au moins 8 caractères.', 'danger')
        elif new_pw != confirm_pw:
            flash('Les deux mots de passe ne correspondent pas.', 'danger')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('Mot de passe mis à jour avec succès.', 'success')
        return redirect(url_for('main.account'))

    return render_template('account.html', member=member)


@main_bp.route('/newsletter/subscribe', methods=['POST'])
@csrf.exempt
def newsletter_subscribe():
    """Inscription à la newsletter"""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or request.form.get('email', '')).strip().lower()

    # Validation basique
    if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'success': False, 'message': 'Adresse email invalide.'}), 400

    # Vérifier si déjà inscrit
    if NewsletterSubscription.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Cette adresse est déjà inscrite.'}), 409

    db.session.add(NewsletterSubscription(email=email))
    db.session.commit()
    return jsonify({'success': True, 'message': 'Inscription réussie ! Merci.'})
