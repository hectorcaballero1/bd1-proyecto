import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('es_ES')

# ============================================================
# CONFIGURACIÓN HÍBRIDA (OPTIMIZADA PARA ÍNDICES)
# ============================================================
CANTIDAD_USUARIOS = 1000  # Cambiar según: 1000, 10000, 100000, 1000000

# VALORES FIJOS (rapidez sin sacrificar funcionalidad)
SEGUIMIENTOS_POR_USUARIO = 9        # Cada usuario sigue a 9 personas
PUBLICACIONES_POR_USUARIO = 5       # Cada usuario hace 5 publicaciones
MULTIMEDIA_POR_PUBLICACION = 2      # Cada publicación tiene 2 multimedia
COMENTARIOS_POR_USUARIO = 6         # Cada usuario hace 6 comentarios

# VALORES ALEATORIOS (necesarios para variabilidad en índices)
RANGO_LIKES = (10, 40)              # Entre 10-40 likes por usuario
RANGO_RESPUESTAS = (0, 5)           # Entre 0-5 respuestas por usuario

# Constantes
PORCENTAJE_IMAGENES = 0.85          # 85% imágenes, 15% videos
PESOS_ESTADO_USUARIO = [90, 8, 2]   # 90% activo, 8% desactivado, 2% eliminado

# ============================================================

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
print("\n" + "="*60)
print("CONFIGURACIÓN")
print("="*60)
print(f"Usuarios: {CANTIDAD_USUARIOS:,}")
print(f"Seguimientos por usuario: {SEGUIMIENTOS_POR_USUARIO} (fijo)")
print(f"Publicaciones por usuario: {PUBLICACIONES_POR_USUARIO} (fijo)")
print(f"Multimedia por publicación: {MULTIMEDIA_POR_PUBLICACION} (fijo)")
print(f"Likes por usuario: {RANGO_LIKES[0]}-{RANGO_LIKES[1]} (aleatorio)")
print(f"Comentarios por usuario: {COMENTARIOS_POR_USUARIO} (fijo)")
print(f"Respuestas por usuario: {RANGO_RESPUESTAS[0]}-{RANGO_RESPUESTAS[1]} (aleatorio)")
print("="*60 + "\n")

# ==================== 1. USUARIOS ====================
print(f"Generando {CANTIDAD_USUARIOS} usuarios...")
usuarios = []
emails = []

for i in range(CANTIDAD_USUARIOS):
    email = f"user{i}@redsocial.com"
    emails.append(email)
    username = f"usuario_{i}"
    biografia = fake.text(max_nb_chars=150) if random.random() > 0.4 else None
    foto = f"perfil_{i}.jpg" if random.random() > 0.3 else None
    estado = random.choices(['A', 'D', 'E'], weights=PESOS_ESTADO_USUARIO)[0]
    
    usuarios.append((email, username, biografia, foto, estado))

cur.executemany("""
    INSERT INTO Usuario (email, username, biografia, foto_de_perfil, estado)
    VALUES (%s, %s, %s, %s, %s)
""", usuarios)
conn.commit()
print(f"✓ {CANTIDAD_USUARIOS} usuarios insertados")

# ==================== 2. SEGUIMIENTOS ====================
print(f"Generando seguimientos ({SEGUIMIENTOS_POR_USUARIO} por usuario)...")
seguimientos = set()

for email in emails:
    seguidos = 0
    intentos = 0
    max_intentos = SEGUIMIENTOS_POR_USUARIO * 3
    
    while seguidos < SEGUIMIENTOS_POR_USUARIO and intentos < max_intentos:
        intentos += 1
        seguido = random.choice(emails)
        if seguido != email and (email, seguido) not in seguimientos:
            seguimientos.add((email, seguido))
            seguidos += 1

print(f"  Total: {len(seguimientos)} seguimientos")

cur.executemany("""
    INSERT INTO Seguimiento (email_seguidor, email_seguido)
    VALUES (%s, %s)
""", list(seguimientos))
conn.commit()
print(f"✓ {len(seguimientos)} seguimientos insertados")

# ==================== 3. PUBLICACIONES CON MULTIMEDIA ====================
print(f"Generando publicaciones ({PUBLICACIONES_POR_USUARIO} por usuario)...")

publicaciones_exitosas = 0
publicaciones_fallidas = 0
publicaciones_info = []

for idx, email in enumerate(emails):
    for _ in range(PUBLICACIONES_POR_USUARIO):
        try:
            cur.execute("BEGIN")
            
            # 1. Insertar publicación
            texto = fake.text(max_nb_chars=400) if random.random() > 0.1 else None
            fecha = fake.date_time_between(start_date='-2y', end_date='now')
            
            cur.execute("""
                INSERT INTO Publicacion (texto_descriptivo, fecha_de_creacion, email_autor)
                VALUES (%s, %s, %s) RETURNING id_publicacion
            """, (texto, fecha, email))
            id_pub = cur.fetchone()[0]
            
            # 2. Insertar multimedia (URLs SIMPLES)
            for idx_media in range(MULTIMEDIA_POR_PUBLICACION):
                if random.random() < PORCENTAJE_IMAGENES:
                    if idx_media == 0:
                        url = f"img_{id_pub}.jpg"
                    else:
                        url = f"img_{id_pub}_{idx_media}.jpg"
                    
                    cur.execute("""
                        INSERT INTO Imagen (ubicacion_almacenamiento, fecha_subida)
                        VALUES (%s, %s) RETURNING id_multimedia
                    """, (url, fecha))
                else:
                    if idx_media == 0:
                        url = f"vid_{id_pub}.mp4"
                    else:
                        url = f"vid_{id_pub}_{idx_media}.mp4"
                    
                    cur.execute("""
                        INSERT INTO Video (ubicacion_almacenamiento, fecha_subida)
                        VALUES (%s, %s) RETURNING id_multimedia
                    """, (url, fecha))
                
                id_multimedia = cur.fetchone()[0]
                
                # 3. Vincular multimedia con publicación
                cur.execute("""
                    INSERT INTO Publicacion_Contenido (id_multimedia, id_publicacion)
                    VALUES (%s, %s)
                """, (id_multimedia, id_pub))
            
            cur.execute("COMMIT")
            publicaciones_exitosas += 1
            
            publicaciones_info.append({
                'id': id_pub,
                'fecha': fecha,
                'autor': email
            })
            
        except Exception as e:
            cur.execute("ROLLBACK")
            publicaciones_fallidas += 1
            if publicaciones_fallidas < 5:
                print(f"  Error en publicación: {e}")
    
    # Progreso cada 100 usuarios
    if (idx + 1) % 100 == 0:
        print(f"  Progreso: {idx + 1}/{CANTIDAD_USUARIOS} usuarios procesados")

print(f"✓ {publicaciones_exitosas} publicaciones insertadas")
if publicaciones_fallidas > 0:
    print(f"⚠ {publicaciones_fallidas} publicaciones fallaron")

# ==================== 4. ME GUSTAS (ALEATORIO) ====================
print(f"Generando me gustas ({RANGO_LIKES[0]}-{RANGO_LIKES[1]} por usuario)...")

if publicaciones_info:
    ids_pubs = [p['id'] for p in publicaciones_info]
    likes = set()
    
    for idx, email in enumerate(emails):
        cant_likes = random.randint(RANGO_LIKES[0], RANGO_LIKES[1])
        likes_dados = 0
        
        cant_likes = min(cant_likes, len(ids_pubs))
        
        intentos = 0
        max_intentos = cant_likes * 2
        
        while likes_dados < cant_likes and intentos < max_intentos:
            intentos += 1
            id_pub = random.choice(ids_pubs)
            if (email, id_pub) not in likes:
                likes.add((email, id_pub))
                likes_dados += 1
        
        if (idx + 1) % 100 == 0:
            print(f"  Progreso: {idx + 1}/{CANTIDAD_USUARIOS} usuarios procesados")
    
    print(f"  Total: {len(likes)} me gustas")
    
    cur.executemany("""
        INSERT INTO Publicacion_MeGusta (email_usuario, id_publicacion)
        VALUES (%s, %s)
    """, list(likes))
    conn.commit()
    print(f"✓ {len(likes)} me gustas insertados")
else:
    print("⚠ No hay publicaciones, saltando me gustas")

# ==================== 5. COMENTARIOS ====================
print(f"Generando comentarios ({COMENTARIOS_POR_USUARIO} por usuario)...")

if publicaciones_info:
    comentarios_por_publicacion = {}
    total_comentarios = 0
    
    for idx, email in enumerate(emails):
        for _ in range(COMENTARIOS_POR_USUARIO):
            pub_info = random.choice(publicaciones_info)
            id_pub = pub_info['id']
            fecha_pub = pub_info['fecha']
            
            # Comentario DESPUÉS de la publicación
            if fecha_pub < datetime.now():
                dias_desde_pub = (datetime.now() - fecha_pub).days
                if dias_desde_pub > 0:
                    dias_aleatorios = random.randint(0, min(dias_desde_pub, 365))
                    fecha_comentario = fecha_pub + timedelta(days=dias_aleatorios)
                else:
                    fecha_comentario = fecha_pub
            else:
                fecha_comentario = fecha_pub
            
            texto = fake.text(max_nb_chars=200)
            
            cur.execute("""
                INSERT INTO Comentario (texto, fecha_de_creacion, id_publicacion, email_autor)
                VALUES (%s, %s, %s, %s) RETURNING id_comentario
            """, (texto, fecha_comentario, id_pub, email))
            
            id_comentario = cur.fetchone()[0]
            total_comentarios += 1
            
            if id_pub not in comentarios_por_publicacion:
                comentarios_por_publicacion[id_pub] = []
            comentarios_por_publicacion[id_pub].append(id_comentario)
        
        if (idx + 1) % 100 == 0:
            conn.commit()
            print(f"  Progreso: {idx + 1}/{CANTIDAD_USUARIOS} usuarios procesados")
    
    conn.commit()
    print(f"✓ {total_comentarios} comentarios insertados")
else:
    print("⚠ No hay publicaciones, saltando comentarios")
    comentarios_por_publicacion = {}

# ==================== 6. RESPUESTAS A COMENTARIOS (ALEATORIO) ====================
print(f"Generando respuestas ({RANGO_RESPUESTAS[0]}-{RANGO_RESPUESTAS[1]} por usuario)...")

if comentarios_por_publicacion:
    publicaciones_con_multiples = [
        pub_id for pub_id, comentarios in comentarios_por_publicacion.items()
        if len(comentarios) >= 2
    ]
    
    if publicaciones_con_multiples:
        respuestas = []
        
        for idx, email in enumerate(emails):
            cant_respuestas = random.randint(RANGO_RESPUESTAS[0], RANGO_RESPUESTAS[1])
            respuestas_hechas = 0
            
            intentos = 0
            max_intentos = cant_respuestas * 3 if cant_respuestas > 0 else 0
            
            while respuestas_hechas < cant_respuestas and intentos < max_intentos:
                intentos += 1
                
                try:
                    id_pub = random.choice(publicaciones_con_multiples)
                    comentarios = comentarios_por_publicacion[id_pub]
                    
                    if len(comentarios) >= 2:
                        id_hijo = random.choice(comentarios)
                        id_padre = random.choice([c for c in comentarios if c != id_hijo])
                        
                        respuestas.append((id_hijo, id_padre))
                        respuestas_hechas += 1
                except:
                    pass
            
            if (idx + 1) % 100 == 0:
                print(f"  Progreso: {idx + 1}/{CANTIDAD_USUARIOS} usuarios procesados")
        
        print(f"  Total intentos: {len(respuestas)} respuestas")
        
        cur.executemany("""
            INSERT INTO Comentario_Responde (id_hijo, id_padre)
            VALUES (%s, %s)
            ON CONFLICT (id_hijo) DO NOTHING
        """, respuestas)
        conn.commit()
        
        cur.execute("SELECT COUNT(*) FROM Comentario_Responde")
        total_respuestas = cur.fetchone()[0]
        print(f"✓ {total_respuestas} respuestas insertadas")
    else:
        print("⚠ No hay publicaciones con múltiples comentarios")
else:
    print("⚠ No hay comentarios")

# ==================== FINALIZAR ====================
cur.close()
conn.close()

print("\n" + "="*60)
print("✅ GENERACIÓN COMPLETA")
print("="*60)
print(f"Total usuarios:      {CANTIDAD_USUARIOS:,}")
print(f"Total seguimientos:  {len(seguimientos):,} (~{len(seguimientos)//CANTIDAD_USUARIOS} por usuario)")
print(f"Total publicaciones: {publicaciones_exitosas:,} (~{publicaciones_exitosas//CANTIDAD_USUARIOS} por usuario)")

if publicaciones_info:
    print(f"Total me gustas:     {len(likes):,} (~{len(likes)//CANTIDAD_USUARIOS} por usuario)")
    print(f"Total comentarios:   {total_comentarios:,} (~{total_comentarios//CANTIDAD_USUARIOS} por usuario)")
    if 'total_respuestas' in locals():
        print(f"Total respuestas:    {total_respuestas:,}")

print(f"\n⚠ Nota: Tabla Mensaje vacía (no utilizada en las consultas de experimentación)")
print("="*60)