from PIL import Image, ImageDraw
import math

# Créer une nouvelle image avec les dimensions pour un hero section
img = Image.new('RGB', (1600, 900), color='#E8E8F0')
d = ImageDraw.Draw(img, 'RGBA')

# Fond supérieur bleu (comme dans l'image)
d.rectangle([(0, 0), (1600, 450)], fill='#5A8FA3')

# Ajouter du contenu visuel simple représentant communauté et partage
# Mains (représentant l'entraide)
hand_color = '#FFFFFF'
for x in [100, 1500]:
    # Poignet
    d.rectangle([(x-15, 400), (x+15, 450)], fill=hand_color)
    # Paume
    d.ellipse([(x-40, 350), (x+40, 400)], fill=hand_color)

# Ajouter des cœurs
heart_color = '#CCCCDD'
for i in range(0, 1600, 300):
    for j in [200, 650]:
        d.ellipse([(i-20, j-20), (i+20, j)], fill=heart_color)
        d.ellipse([(i-20, j), (i+20, j+20)], fill=heart_color)

# Cercle avec personnes (représentant l'association)
circle_x, circle_y = 800, 650
circle_radius = 100
d.ellipse([(circle_x-circle_radius, circle_y-circle_radius), (circle_x+circle_radius, circle_y+circle_radius)], outline=heart_color, width=3)

# Petits éléments de décoration (lauriers, branches)
leaf_color = '#AAAACC'
for angle in range(0, 360, 45):
    rad = math.radians(angle)
    x = circle_x + circle_radius * 1.3 * math.cos(rad)
    y = circle_y + circle_radius * 1.3 * math.sin(rad)
    d.polygon([(x-10, y-15), (x+10, y-15), (x+5, y+15), (x-5, y+15)], fill=leaf_color)

# Logo de mains qui se serrent (haut gauche)
d.rectangle([(50, 50), (150, 150)], fill='#4A7A8F', outline=hand_color, width=2)

# Logo de mains qui se serrent (haut droit)
d.rectangle([(1450, 50), (1550, 150)], fill='#4A7A8F', outline=hand_color, width=2)

img.save('app/static/images/background-home.png')
print('✓ Image de background créée avec succès à app/static/images/background-home.png')
