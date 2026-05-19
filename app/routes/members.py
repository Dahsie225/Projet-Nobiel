from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.models import Member, Adhesion, User
from app.email_utils import send_member_welcome
from wtforms import StringField, SelectField, TextAreaField, DateField, FloatField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os

members_bp = Blueprint('members', __name__, url_prefix='/members')

# === FORMULAIRES ===
class JoinForm(FlaskForm):
    first_name = StringField('Prénom', validators=[DataRequired()])
    last_name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Téléphone', validators=[Optional()])
    gender = SelectField('Genre', choices=[
        ('', 'Sélectionner...'),
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('Other', 'Autre')
    ])
    birthdate = DateField('Date de naissance', validators=[Optional()])
    regional_section = SelectField('Section Régionale', choices=[
        ('', 'Sélectionner votre section...'),
        ('Abidjan', '🏛️ Abidjan (Siège National)'),
        ('Sassandra', '🏙️ Sassandra'),
        ('San-Pédro', '🏙️ San-Pédro'),
        ('Korogho', '🏙️ Korogho'),
        ('Bouaké', '🏙️ Bouaké'),
        ('Man', '🏙️ Man')
    ], validators=[DataRequired()])
    membership_type = SelectField('Type d\'adhésion', choices=[
        ('student', 'Étudiant'),
        ('professional', 'Professionnel'),
        ('partner', 'Partenaire Institutionnel'),
        ('donor', 'Donateur')
    ], validators=[DataRequired()])
    identity_photo = FileField('Photo d\'Identité', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images seulement (JPG, PNG)!')
    ])
    submit = SubmitField('S\'Inscrire')
    
    def validate_email(self, email):
        member = Member.query.filter_by(email=email.data).first()
        if member:
            raise ValidationError('Cet email est déjà utilisé.')

class AdhesionForm(FlaskForm):
    adhesion_type = SelectField('Type d\'adhésion', choices=[
        ('annual', 'Annuelle'),
        ('monthly', 'Mensuelle'),
        ('lifetime', 'À vie')
    ], validators=[DataRequired()])
    amount = FloatField('Montant (XOF)', validators=[DataRequired()])
    payment_method = SelectField('Méthode de paiement', choices=[
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('orange_money', 'Orange Money'),
        ('wave', 'Wave'),
        ('mtn', 'MTN Mobile Money')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes (optionnel)', validators=[Optional()])
    receipt_file = FileField('Justificatif de paiement', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images ou PDF uniquement !')
    ])
    submit = SubmitField('Enregistrer l\'Adhésion')

# === ROUTES ===
SECTION_INFO = {
    'Abidjan':   {'label': 'Siège National', 'icon': '🌍', 'badge': '🏛️ SIÈGE NATIONAL', 'is_national': True},
    'Sassandra': {'label': 'Section Régionale', 'icon': '🏙️', 'badge': None, 'is_national': False},
    'San-Pédro': {'label': 'Section Régionale', 'icon': '🏙️', 'badge': None, 'is_national': False},
    'Korogho':   {'label': 'Section Régionale', 'icon': '🏙️', 'badge': None, 'is_national': False},
    'Bouaké':    {'label': 'Section Régionale', 'icon': '🏙️', 'badge': None, 'is_national': False},
    'Man':       {'label': 'Section Régionale', 'icon': '🏙️', 'badge': None, 'is_national': False},
}

SECTION_ROLE_LABELS = {
    'president':      'Président',
    'vice_president': 'Vice-Président',
    'secretary':      'Secrétaire',
    'treasurer':      'Trésorier',
    'member':         'Membre',
}

@members_bp.route('/section/<city>')
def section_detail(city):
    """Page de détail d'une section régionale"""
    info = SECTION_INFO.get(city)
    if not info:
        flash('Section introuvable.', 'danger')
        return redirect(url_for('main.index'))

    # Responsables de la section (tous sauf rôle 'member')
    leaders = Member.query.filter_by(city=city, membership_status='active').filter(
        Member.section_role.in_(['president', 'vice_president', 'secretary', 'treasurer'])
    ).all()

    # Membres ordinaires
    members_count = Member.query.filter_by(city=city, membership_status='active').count()

    return render_template(
        'members/section.html',
        city=city,
        info=info,
        leaders=leaders,
        members_count=members_count,
        role_labels=SECTION_ROLE_LABELS
    )

@members_bp.route('/')
def list_members():
    """Liste des membres (annuaire)"""
    if not current_user.is_authenticated:
        flash('Vous devez être connecté pour accéder à l\'annuaire.', 'warning')
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    city = request.args.get('city', '')
    
    query = Member.query.filter_by(membership_status='active')
    
    if search:
        query = query.filter(
            (Member.first_name.ilike(f'%{search}%')) |
            (Member.last_name.ilike(f'%{search}%')) |
            (Member.email.ilike(f'%{search}%'))
        )
    
    if city:
        query = query.filter_by(city=city)
    
    members = query.order_by(Member.first_name).paginate(page=page, per_page=20)
    
    # Get list of cities for filter
    cities = db.session.query(Member.city).distinct().all()
    cities = [c[0] for c in cities if c[0]]
    
    return render_template('members/list.html', members=members, cities=cities, search=search, city=city)

@members_bp.route('/<int:member_id>')
def view_member(member_id):
    """Visualiser le profil d'un membre"""
    member = Member.query.get_or_404(member_id)
    
    if not current_user.is_authenticated:
        flash('Vous devez être connecté pour voir les détails d\'un membre.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Check member status
    if member.membership_status not in ['active', 'pending']:
        if current_user.id != member.id and current_user.role != 'admin':
            return redirect(url_for('members.list_members'))
    
    return render_template('members/view.html', member=member)

@members_bp.route('/join', methods=['GET', 'POST'])
def join():
    """Formulaire d'adhésion"""
    form = JoinForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing = Member.query.filter_by(email=form.email.data).first()
        if existing:
            flash('Cet email est déjà enregistré.', 'danger')
            return redirect(url_for('members.join'))
        
        # Traiter la photo d'identité
        identity_photo_path = None
        if form.identity_photo.data:
            try:
                file = form.identity_photo.data
                filename = secure_filename(file.filename)
                # Ajouter un timestamp pour éviter les collisions
                filename = f"{datetime.utcnow().timestamp()}_{filename}"
                
                # Créer le dossier uploads s'il n'existe pas
                upload_folder = current_app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                identity_photo_path = f"uploads/{filename}"
            except Exception as e:
                flash(f'Erreur lors de l\'upload de la photo: {str(e)}', 'warning')
                identity_photo_path = None
        
        member = Member(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            gender=form.gender.data if form.gender.data else None,
            birthdate=form.birthdate.data,
            city=form.regional_section.data,
            membership_type=form.membership_type.data,
            identity_photo=identity_photo_path,
            membership_status='pending'
        )
        
        db.session.add(member)
        db.session.commit()

        send_member_welcome(member)

        flash('Merci de votre adhésion ! Veuillez attendre la confirmation.', 'success')
        return redirect(url_for('main.index'))
    
    total_members = Member.query.count()
    return render_template('members/join.html', form=form, total_members=total_members)

@members_bp.route('/<int:member_id>/adhesions', methods=['GET', 'POST'])
@login_required
def view_adhesions(member_id):
    """Gestion des adhésions d'un membre"""
    member = Member.query.get_or_404(member_id)
    
    # Check permissions
    if current_user.id != member.id and current_user.role != 'admin':
        flash('Vous n\'avez pas accès à ces informations.', 'danger')
        return redirect(url_for('members.list_members'))
    
    form = AdhesionForm()
    if form.validate_on_submit():
        # Calculate dates
        start_date = datetime.now().date()
        if form.adhesion_type.data == 'annual':
            end_date = start_date + timedelta(days=365)
        elif form.adhesion_type.data == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:  # lifetime
            end_date = start_date + timedelta(days=36500)  # 100 years
        
        adhesion = Adhesion(
            member_id=member.id,
            adhesion_type=form.adhesion_type.data,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            start_date=start_date,
            end_date=end_date,
            payment_status='pending',
            notes=form.notes.data
        )

        # Gérer l'upload du justificatif
        if form.receipt_file.data and form.receipt_file.data.filename:
            try:
                rf = form.receipt_file.data
                rf_filename = secure_filename(rf.filename)
                rf_filename = f"receipt_{member.id}_{int(datetime.utcnow().timestamp())}_{rf_filename}"
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'receipts')
                os.makedirs(upload_dir, exist_ok=True)
                rf.save(os.path.join(upload_dir, rf_filename))
                adhesion.receipt_file = f'uploads/receipts/{rf_filename}'
            except Exception as e:
                flash(f'Erreur upload justificatif : {str(e)}', 'warning')
        
        db.session.add(adhesion)
        member.membership_status = 'active'
        db.session.commit()
        
        flash('Adhésion enregistrée avec succès !', 'success')
        return redirect(url_for('members.view_adhesions', member_id=member.id))
    
    adhesions = Adhesion.query.filter_by(member_id=member.id).order_by(
        Adhesion.created_at.desc()
    ).all()
    
    return render_template('members/adhesions.html', member=member, form=form, adhesions=adhesions)

@members_bp.route('/<int:adhesion_id>/validate-payment', methods=['POST'])
@login_required
def validate_payment(adhesion_id):
    """Valider le paiement d'une adhésion (Admin only)"""
    adhesion = Adhesion.query.get_or_404(adhesion_id)
    
    if current_user.role != 'admin':
        flash('Accès réservé aux administrateurs.', 'danger')
        return redirect(url_for('main.index'))
    
    adhesion.payment_status = 'paid'
    adhesion.paid_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Paiement de l\'adhésion validé pour {adhesion.member.full_name}.', 'success')
    return redirect(url_for('members.view_adhesions', member_id=adhesion.member_id))

