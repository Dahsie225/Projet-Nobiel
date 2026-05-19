from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models.models import User
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from flask_wtf import FlaskForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# === FORMULAIRES ===
class LoginForm(FlaskForm):
    username = StringField('Identifiant', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se Connecter')

class RegisterForm(FlaskForm):
    username = StringField('Identifiant', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Identifiant entre 3 et 80 caractères')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Nom Complet', validators=[Length(max=120)])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=8, message='Au moins 8 caractères')
    ])
    password_confirm = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe ne correspondent pas')
    ])
    submit = SubmitField('S\'Inscrire')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Cet identifiant est déjà utilisé.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')

# === ROUTES ===
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'], error_message='Trop de tentatives de connexion. Réessayez dans une minute.')
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Identifiant ou mot de passe incorrect.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Ce compte est désactivé.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=True)
        flash(f'Bienvenue, {user.username} !', 'success')
        
        next_page = request.args.get('next')
        if not next_page or not url_has_allowed_host_and_scheme(next_page):
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=['POST'], error_message='Trop de tentatives. Réessayez dans une minute.')
def register():
    """Page d'inscription"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data or '',
            role='user'
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie ! Vous pouvez vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('main.index'))

def url_has_allowed_host_and_scheme(url, allowed_hosts=None, require_https=False):
    """Valide une URL de redirection"""
    from urllib.parse import urlparse
    if allowed_hosts is None:
        allowed_hosts = ['localhost', '127.0.0.1']
    
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return False
    if parsed.netloc and parsed.netloc not in allowed_hosts:
        return False
    return True
