import psycopg2
from faker import Faker
import random
from datetime import datetime

fake = Faker('es_ES')
CANTIDAD_USUARIOS = 1000  # Cambia según necesites: 1k, 10k, 100k, 1M

# Conexión
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="red_social",
    user="postgres",
    password="postgres123"
)
cur = conn.cursor()

print("✓ Conexión exitosa")

# ==================== 1. USUARIOS ====================
print(f"Generando {CANTIDAD_USUARIOS} usuarios...")
usuarios = []
emails = []

for i in range(CANTIDAD_USUARIOS):
    email = f"user{i}@redsocial.com"
    emails.append(email)
    username = f"usuario_{i}"
    biografia = fake.text(max_nb_chars=150) if random.random() > 0.3 else None
    foto = f"foto_{i}.jpg" if random.random() > 0.7 else None
    estado = random.choices(['A', 'D', 'E'], weights=[90, 8, 2])[0]
    
    usuarios.append((email, username, biografia, foto, estado))

cur.executemany("""
    INSERT INTO Usuario (email, username, biografia, foto_de_perfil, estado)
    VALUES (%s, %s, %s, %s, %s)
""", usuarios)
conn.commit()
print(f"✓ {CANTIDAD_USUARIOS} usuarios insertados")

# ==================== 2. SEGUIMIENTOS ====================
cant_seguimientos = int(CANTIDAD_USUARIOS * 2.5)
print(f"Generando {cant_seguimientos} seguimientos...")
seguimientos = set()

while len(seguimientos) < cant_seguimientos:
    seguidor = random.choice(emails)
    seguido = random.choice(emails)
    if seguidor != seguido:
        seguimientos.add((seguidor, seguido))
    
    if len(seguimientos) % 10000 == 0:
        print(f"  Progreso: {len(seguimientos)}/{cant_seguimientos}")

cur.executemany("""
    INSERT INTO Seguimiento (email_seguidor, email_seguido)
    VALUES (%s, %s)
""", list(seguimientos))
conn.commit()
print(f"✓ {cant_seguimientos} seguimientos insertados")

# ==================== 3. PUBLICACIONES CON MULTIMEDIA (CON TRANSACCIONES) ====================
cant_publicaciones = CANTIDAD_USUARIOS * 3
print(f"Generando {cant_publicaciones} publicaciones con multimedia...")

publicaciones_exitosas = 0
publicaciones_fallidas = 0

for i in range(cant_publicaciones):
    try:
        # ← INICIO DE TRANSACCIÓN
        cur.execute("BEGIN")
        
        # 1. Insertar publicación
        texto = fake.text(max_nb_chars=400) if random.random() > 0.05 else None
        fecha = fake.date_time_between(start_date='-2y', end_date='now')
        autor = random.choice(emails)
        
        cur.execute("""
            INSERT INTO Publicacion (texto_descriptivo, fecha_de_creacion, email_autor)
            VALUES (%s, %s, %s) RETURNING id_publicacion
        """, (texto, fecha, autor))
        id_pub = cur.fetchone()[0]
        
        # 2. Insertar imagen o video aleatoriamente
        if random.random() < 0.8:  # 80% imágenes
            cur.execute("""
                INSERT INTO Imagen (ubicacion_almacenamiento)
                VALUES (%s) RETURNING id_multimedia
            """, (f"imagenes/img_{id_pub}.jpg",))
        else:  # 20% videos
            cur.execute("""
                INSERT INTO Video (ubicacion_almacenamiento)
                VALUES (%s) RETURNING id_multimedia
            """, (f"videos/vid_{id_pub}.mp4",))
        
        id_multimedia = cur.fetchone()[0]
        
        # 3. Vincular publicación con multimedia
        cur.execute("""
            INSERT INTO Publicacion_Contenido (id_multimedia, id_publicacion)
            VALUES (%s, %s)
        """, (id_multimedia, id_pub))
        
        # ← COMMIT (aquí se valida el trigger)
        cur.execute("COMMIT")
        publicaciones_exitosas += 1
        
    except Exception as e:
        cur.execute("ROLLBACK")
        publicaciones_fallidas += 1
        if publicaciones_fallidas < 5:  # Solo mostrar primeros 5 errores
            print(f"  Error en publicación {i}: {e}")
    
    if (i + 1) % 5000 == 0:
        print(f"  Progreso: {i + 1}/{cant_publicaciones} (exitosas: {publicaciones_exitosas}, fallidas: {publicaciones_fallidas})")

print(f"✓ {publicaciones_exitosas} publicaciones con multimedia insertadas")
if publicaciones_fallidas > 0:
    print(f"⚠ {publicaciones_fallidas} publicaciones fallaron")

# ==================== 4. ME GUSTAS ====================
print("Generando me gustas...")
cur.execute("SELECT id_publicacion FROM Publicacion")
ids_pubs = [row[0] for row in cur.fetchall()]

cant_likes = CANTIDAD_USUARIOS * 10
likes = set()

while len(likes) < cant_likes:
    email = random.choice(emails)
    id_pub = random.choice(ids_pubs)
    likes.add((email, id_pub))
    
    if len(likes) % 50000 == 0:
        print(f"  Progreso: {len(likes)}/{cant_likes}")

cur.executemany("""
    INSERT INTO Publicacion_MeGusta (email_usuario, id_publicacion)
    VALUES (%s, %s)
""", list(likes))
conn.commit()
print(f"✓ {cant_likes} me gustas insertados")

# ==================== 5. COMENTARIOS ====================
cant_comentarios = CANTIDAD_USUARIOS * 5
print(f"Generando {cant_comentarios} comentarios...")

for i in range(cant_comentarios):
    texto = fake.text(max_nb_chars=200)
    fecha = fake.date_time_between(start_date='-1y', end_date='now')
    id_pub = random.choice(ids_pubs)
    autor = random.choice(emails)
    
    cur.execute("""
        INSERT INTO Comentario (texto, fecha_de_creacion, id_publicacion, email_autor)
        VALUES (%s, %s, %s, %s)
    """, (texto, fecha, id_pub, autor))
    
    if (i + 1) % 10000 == 0:
        conn.commit()
        print(f"  Progreso: {i + 1}/{cant_comentarios}")

conn.commit()
print(f"✓ {cant_comentarios} comentarios insertados")

# ==================== 6. RESPUESTAS A COMENTARIOS ====================
print("Generando respuestas a comentarios...")
cur.execute("SELECT id_comentario FROM Comentario")
ids_comentarios = [row[0] for row in cur.fetchall()]

cant_respuestas = int(CANTIDAD_USUARIOS * 0.5)
respuestas_insertadas = 0

for _ in range(cant_respuestas):
    try:
        id_hijo = random.choice(ids_comentarios)
        id_padre = random.choice(ids_comentarios)
        
        if id_hijo != id_padre:
            cur.execute("""
                INSERT INTO Comentario_Responde (id_hijo, id_padre)
                VALUES (%s, %s)
            """, (id_hijo, id_padre))
            respuestas_insertadas += 1
    except:
        pass  # Ignorar duplicados o violaciones

conn.commit()
print(f"✓ {respuestas_insertadas} respuestas insertadas")

# ==================== 7. MENSAJES ====================
cant_mensajes = CANTIDAD_USUARIOS * 4
print(f"Generando {cant_mensajes} mensajes...")

for i in range(cant_mensajes):
    texto = fake.text(max_nb_chars=150) if random.random() > 0.05 else None
    fecha = fake.date_time_between(start_date='-6M', end_date='now')
    estado = random.choices(['E', 'R', 'L'], weights=[5, 15, 80])[0]
    
    while True:
        remitente = random.choice(emails)
        destinatario = random.choice(emails)
        if remitente != destinatario:
            break
    
    cur.execute("""
        INSERT INTO Mensaje (texto, fecha_de_envio, estado, email_remitente, email_destinatario)
        VALUES (%s, %s, %s, %s, %s)
    """, (texto, fecha, estado, remitente, destinatario))
    
    if (i + 1) % 10000 == 0:
        conn.commit()
        print(f"  Progreso: {i + 1}/{cant_mensajes}")

conn.commit()
print(f"✓ {cant_mensajes} mensajes insertados")

# ==================== FINALIZAR ====================
cur.close()
conn.close()

print("\n" + "="*50)
print("✅ GENERACIÓN COMPLETA")
print("="*50)
print(f"Total usuarios: {CANTIDAD_USUARIOS}")
print(f"Total publicaciones: {publicaciones_exitosas}")
print(f"Total seguimientos: {cant_seguimientos}")
print(f"Total me gustas: {cant_likes}")
print(f"Total comentarios: {cant_comentarios}")
print(f"Total mensajes: {cant_mensajes}")