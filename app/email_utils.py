"""
Utilitaires email NOBIEL — envois transactionnels.
Les emails ne sont envoyés que si MAIL_USERNAME est configuré dans .env.
"""
from flask import current_app
from flask_mail import Message
from app import mail


def _send(subject: str, recipients: list[str], html: str, bcc: list[str] | None = None) -> None:
    """Envoie un email en gérant silencieusement les erreurs de configuration."""
    if not recipients or not any(recipients):
        return
    try:
        msg = Message(subject=subject, recipients=recipients, bcc=bcc or [], html=html)
        mail.send(msg)
    except Exception as exc:
        current_app.logger.warning(f"[email] Échec envoi à {recipients}: {exc}")


# ── Templates HTML ──────────────────────────────────────────────────────────

_BASE = """
<div style="font-family:sans-serif;max-width:600px;margin:0 auto;background:#0f1629;
            color:#e2e8f0;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#1d4ed8,#ca8a04);padding:28px 32px;">
    <h1 style="margin:0;font-size:22px;color:#fff;">🌟 NOBIEL</h1>
    <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.7);">
      Association des Élèves et Étudiants du Bounkani
    </p>
  </div>
  <div style="padding:32px;">
    {body}
  </div>
  <div style="padding:18px 32px;border-top:1px solid rgba(255,255,255,0.08);
              font-size:12px;color:rgba(255,255,255,0.35);text-align:center;">
    © NOBIEL — Abidjan, Côte d'Ivoire · <a href="mailto:contact@nobiel.ci"
    style="color:#f59e0b;">contact@nobiel.ci</a>
  </div>
</div>
"""


def _wrap(body: str) -> str:
    return _BASE.format(body=body)


# ── Emails publics ───────────────────────────────────────────────────────────

def send_member_welcome(member) -> None:
    """Email de bienvenue envoyé après inscription (statut pending)."""
    body = f"""
    <h2 style="margin:0 0 12px;color:#fff;">Bonjour {member.first_name} 👋</h2>
    <p>Merci de votre demande d'adhésion à l'association <strong>NOBIEL</strong> !</p>
    <p>Votre dossier est actuellement <span style="color:#fbbf24;font-weight:700;">en cours d'examen</span>
    par notre équipe. Vous recevrez une notification dès que votre adhésion sera validée.</p>
    <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:16px;margin:20px 0;">
      <p style="margin:0 0 6px;font-size:13px;color:rgba(255,255,255,0.5);">VOTRE DOSSIER</p>
      <p style="margin:0;"><strong>Nom :</strong> {member.full_name}</p>
      <p style="margin:4px 0 0;"><strong>Section :</strong> {member.city or '—'}</p>
      <p style="margin:4px 0 0;"><strong>Type d'adhésion :</strong> {member.membership_type or '—'}</p>
    </div>
    <p style="color:rgba(255,255,255,0.6);font-size:14px;">
      En attendant, n'hésitez pas à nous contacter à
      <a href="mailto:contact@nobiel.ci" style="color:#f59e0b;">contact@nobiel.ci</a>.
    </p>
    """
    _send(
        subject="✅ Votre demande d'adhésion NOBIEL a bien été reçue",
        recipients=[member.email],
        html=_wrap(body),
    )


def send_member_activated(member) -> None:
    """Email de confirmation d'activation du compte membre."""
    body = f"""
    <h2 style="margin:0 0 12px;color:#fff;">Félicitations {member.first_name} 🎉</h2>
    <p>Votre adhésion à l'association <strong>NOBIEL</strong> vient d'être
    <span style="color:#34d399;font-weight:700;">validée</span> par notre équipe !</p>
    <p>Vous êtes désormais membre actif. Bienvenue dans la communauté Bounkani.</p>
    <div style="margin:24px 0;">
      <a href="https://nobiel.ci/account"
         style="background:linear-gradient(135deg,#1d4ed8,#ca8a04);color:#fff;
                padding:12px 28px;border-radius:8px;text-decoration:none;
                font-weight:700;font-size:15px;">
        Accéder à Mon Compte →
      </a>
    </div>
    """
    _send(
        subject="🎉 Votre adhésion NOBIEL est validée !",
        recipients=[member.email],
        html=_wrap(body),
    )


def send_adhesion_approved(adhesion) -> None:
    """Email de confirmation de paiement d'adhésion."""
    member = adhesion.member
    if not member:
        return
    body = f"""
    <h2 style="margin:0 0 12px;color:#fff;">Bonjour {member.first_name} 👋</h2>
    <p>Votre paiement d'adhésion a été
    <span style="color:#34d399;font-weight:700;">enregistré et approuvé</span>.</p>
    <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:16px;margin:20px 0;">
      <p style="margin:0 0 6px;font-size:13px;color:rgba(255,255,255,0.5);">DÉTAILS</p>
      <p style="margin:0;"><strong>Type :</strong> {adhesion.adhesion_type}</p>
      <p style="margin:4px 0 0;"><strong>Montant :</strong> {int(adhesion.amount)} XOF</p>
      <p style="margin:4px 0 0;"><strong>Valide jusqu'au :</strong>
        {adhesion.end_date.strftime('%d/%m/%Y') if adhesion.end_date else '—'}</p>
    </div>
    <p style="color:rgba(255,255,255,0.6);font-size:14px;">
      Merci pour votre soutien à l'association NOBIEL.
    </p>
    """
    _send(
        subject="💳 Paiement d'adhésion NOBIEL confirmé",
        recipients=[member.email],
        html=_wrap(body),
    )


def send_newsletter_notification(article) -> None:
    """Notifie tous les abonnés newsletter d'un nouvel article publié.

    Envoie par lots de 50 via BCC pour limiter les appels SMTP.
    N'est déclenché que lors de la première publication (draft → publié).
    """
    from app.models.models import NewsletterSubscription
    from flask import url_for

    subscribers = (NewsletterSubscription.query
                   .with_entities(NewsletterSubscription.email)
                   .all())
    emails = [s.email for s in subscribers]
    if not emails:
        return

    cat_map = {
        'news':         'Actualité',
        'event':        'Événement',
        'announcement': 'Annonce',
        'opinion':      'Opinion',
    }
    cat_label = cat_map.get(article.category, 'Actualité')

    try:
        article_url = url_for('articles.view_article', slug=article.slug, _external=True)
    except Exception:
        article_url = '#'

    excerpt_html = (
        f'<p style="color:rgba(255,255,255,0.75);font-size:15px;line-height:1.7;">'
        f'{article.excerpt}</p>'
        if article.excerpt else ''
    )

    body = f"""
    <div style="display:inline-block;background:rgba(249,115,22,0.15);border:1px solid #f97316;
                color:#f97316;padding:4px 12px;border-radius:20px;font-size:12px;
                font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:16px;">
      {cat_label}
    </div>
    <h2 style="margin:0 0 16px;color:#fff;font-size:20px;line-height:1.4;">{article.title}</h2>
    {excerpt_html}
    <div style="margin:28px 0;">
      <a href="{article_url}"
         style="background:linear-gradient(135deg,#1d4ed8,#ca8a04);color:#fff;
                padding:13px 30px;border-radius:8px;text-decoration:none;
                font-weight:700;font-size:15px;">
        Lire l'article →
      </a>
    </div>
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:24px 0;">
    <p style="color:rgba(255,255,255,0.35);font-size:12px;margin:0;">
      Vous recevez cet email car vous êtes inscrit à la newsletter NOBIEL.<br>
      Pour vous désinscrire, contactez-nous à
      <a href="mailto:contact@nobiel.ci" style="color:#f59e0b;">contact@nobiel.ci</a>.
    </p>
    """
    html = _wrap(body)
    subject = f"🔔 NOBIEL — {cat_label} : {article.title}"

    # Envoi par lots de 50 (premier = recipient, reste en BCC)
    chunk_size = 50
    for i in range(0, len(emails), chunk_size):
        chunk = emails[i:i + chunk_size]
        _send(subject=subject, recipients=[chunk[0]], bcc=chunk[1:], html=html)
