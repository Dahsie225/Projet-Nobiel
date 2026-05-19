from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """Modèle pour les utilisateurs (administrateurs, modérateurs)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')  # 'admin', 'moderator', 'user'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    articles = db.relationship('Article', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Member(db.Model):
    """Modèle pour les membres/adhérents de l'association"""
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(20))  # 'M', 'F', 'Other'
    birthdate = db.Column(db.Date)
    
    # Adresse
    address = db.Column(db.String(255))
    city = db.Column(db.String(80))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(80), default='Côte d\'Ivoire')
    
    # Photo d'identité
    identity_photo = db.Column(db.String(255))
    
    # Rôle dans la section régionale
    section_role = db.Column(db.String(50), default='member')  # 'president', 'vice_president', 'secretary', 'treasurer', 'member'

    # Statut d'adhésion
    membership_status = db.Column(db.String(20), default='pending')  # 'pending', 'active', 'inactive', 'resigned'
    membership_type = db.Column(db.String(50))  # 'student', 'professional', 'partner', 'donor'
    
    # Dates
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Relations
    adhesions = db.relationship('Adhesion', backref='member', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Member {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class Article(db.Model):
    """Modèle pour les actualités/articles du blog"""
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    slug = db.Column(db.String(128), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500))
    
    # Métadonnées
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50))  # 'news', 'event', 'announcement'
    is_published = db.Column(db.Boolean, default=False)
    cover_image = db.Column(db.String(255))  # chemin relatif static/
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Article {self.title}>'


class Adhesion(db.Model):
    """Modèle pour gérer les adhésions (cotisations)"""
    __tablename__ = 'adhesions'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    
    # Type et montant
    adhesion_type = db.Column(db.String(50), nullable=False)  # 'annual', 'monthly', etc.
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='XOF')  # Franc CFA
    
    # Statut de paiement
    payment_status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'cancelled'
    payment_method = db.Column(db.String(50))  # 'cash', 'bank_transfer', 'mobile_money', etc.
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Justificatif
    receipt_file = db.Column(db.String(255))  # chemin du fichier justificatif
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Adhesion {self.member_id} - {self.adhesion_type}>'
    
    @property
    def is_active(self):
        """Vérifie si l'adhésion est actuellement valide"""
        from datetime import date
        return self.payment_status == 'paid' and self.start_date <= date.today() <= self.end_date


class Media(db.Model):
    """Modèle pour la médiathèque (photos et vidéos d'événements)"""
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    # Type : 'image' ou 'video'
    media_type = db.Column(db.String(10), nullable=False, default='image')

    # Pour les images uploadées
    file_path = db.Column(db.String(255))

    # Pour les vidéos YouTube / liens externes
    video_url = db.Column(db.String(500))

    # Événement associé
    event_name = db.Column(db.String(255))
    event_date = db.Column(db.Date)

    # Visibilité
    is_published = db.Column(db.Boolean, default=True)

    # Auteur et dates
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.title}>'


class NewsletterSubscription(db.Model):
    """Abonnés à la newsletter"""
    __tablename__ = 'newsletter_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Newsletter {self.email}>'
