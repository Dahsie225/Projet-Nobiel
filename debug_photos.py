#!/usr/bin/env python
"""Script pour déboguer les photos d'identité"""
from app import create_app, db
from app.models.models import Member

app = create_app()

with app.app_context():
    members = Member.query.all()
    print(f"Total des membres: {len(members)}\n")
    
    for member in members:
        print(f"ID: {member.id}")
        print(f"Nom: {member.full_name}")
        print(f"Photo: {member.identity_photo}")
        print(f"Existe en BD: {member.identity_photo is not None}")
        print("-" * 50)
