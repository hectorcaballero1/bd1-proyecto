import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta
import io
import time

fake = Faker('es_ES')

# ============================================================
# CONFIGURACIÓN
# ============================================================
CANTIDAD_USUARIOS = 100000  # Cambiar según: 1000, 10000, 100000, 1000000

SEGUIMIENTOS_POR_USUARIO = 5        
PUBLICACIONES_POR_USUARIO = 3      
MULTIMEDIA_POR_PUBLICACION = 1      
COMENTARIOS_POR_USUARIO = 5         

RANGO_LIKES = (10, 20)              
RANGO_RESPUESTAS = (0, 3)           

PORCENTAJE_IMAGENES = 0.85          
PESOS_ESTADO_USUARIO = [90, 8, 2]   # % de A, D, E

# ============================================================
# GENERACIÓN DE CONTENIDO REUTILIZABLE
# ============================================================
print("🔧 Generando contenido reutilizable...")
start_global = time.time()

# Función para limpiar texto (evitar problemas con COPY)
def clean_text(text):
    return text.replace('\n', ' ').replace('\t', ' ').replace('\\', '\\\\').replace('\r', '')

BIOGRAFIAS_POOL = [clean_text(fake.text(max_nb_chars=150)) for _ in range(100)]
TEXTOS_PUBLICACION_POOL = [clean_text(fake.text(max_nb_chars=400)) for _ in range(200)]
TEXTOS_COMENTARIO_POOL = [clean_text(fake.text(max_nb_chars=200)) for _ in range(300)]

print(f"✓ Contenido generado\n")

# ============================================================
# CONEXIÓN
# ============================================================
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="red_social",
    user="postgres",
    password="postgres123"
)
cur = conn.cursor()
print("✓ Conexión exitosa\n")

print("="*70)
print("CONFIGURACIÓN DE GENERACIÓN")
print("="*70)
print(f"Usuarios:                 {CANTIDAD_USUARIOS:,}")
print(f"Seguimientos por usuario: {SEGUIMIENTOS_POR_USUARIO}")
print(f"Publicaciones por usuario: {PUBLICACIONES_POR_USUARIO}")
print(f"Multimedia por publicación: {MULTIMEDIA_POR_PUBLICACION}")
print(f"Likes por usuario:        {RANGO_LIKES[0]}-{RANGO_LIKES[1]}")
print(f"Comentarios por usuario:  {COMENTARIOS_POR_USUARIO}")
print(f"Respuestas por usuario:   {RANGO_RESPUESTAS[0]}-{RANGO_RESPUESTAS[1]}")
print("="*70 + "\n")

# ============================================================
# OPTIMIZACIONES DE POSTGRESQL
# ============================================================
print("🔧 APLICANDO OPTIMIZACIONES DE POSTGRESQL...")
cur.execute("SET synchronous_commit = OFF;")
cur.execute("SET maintenance_work_mem = '1GB';")
cur.execute("SET work_mem = '256MB';")
cur.execute("SET effective_cache_size = '4GB';")
conn.commit()
print("✓ PostgreSQL optimizado\n")

# ============================================================
# DESACTIVAR CONSTRAINTS Y TRIGGERS
# ============================================================
print("🔧 DESACTIVANDO CONSTRAINTS Y TRIGGERS...")
cur.execute("SET session_replication_role = replica;")  # Desactiva TODAS las FKs
cur.execute("ALTER TABLE Publicacion DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Comentario DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Publicacion_MeGusta DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Seguimiento DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Comentario_Responde DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Publicacion_Contenido DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Imagen DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Video DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Audio DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Mensaje DISABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Mensaje_Contenido DISABLE TRIGGER ALL;")
conn.commit()
print("✓ Constraints y triggers desactivados\n")

# ============================================================
# CONVERTIR A UNLOGGED (MUCHO MÁS RÁPIDO)
# ============================================================
print("🔧 CONVIRTIENDO TABLAS A UNLOGGED...")
tablas = ['Usuario', 'Seguimiento', 'Publicacion', 'Publicacion_MeGusta', 
          'Comentario', 'Comentario_Responde', 'Publicacion_Contenido',
          'Imagen', 'Video', 'Audio', 'Mensaje', 'Mensaje_Contenido']

for tabla in tablas:
    try:
        cur.execute(f"ALTER TABLE {tabla} SET UNLOGGED;")
    except Exception as e:
        print(f"  ⚠ {tabla}: {e}")

conn.commit()
print("✓ Tablas convertidas a UNLOGGED\n")

# ============================================================
# 1. USUARIOS (CON COPY - ULTRA RÁPIDO)
# ============================================================
print(f"📊 [1/6] Generando {CANTIDAD_USUARIOS:,} usuarios...")
start_time = time.time()

csv_buffer = io.StringIO()
emails = []

for i in range(CANTIDAD_USUARIOS):
    email = f"user{i}@redsocial.com"
    emails.append(email)
    username = f"usuario_{i}"
    biografia = random.choice(BIOGRAFIAS_POOL) if random.random() > 0.4 else ''
    foto = f"perfil_{i}.jpg" if random.random() > 0.3 else ''
    estado = random.choices(['A', 'D', 'E'], weights=PESOS_ESTADO_USUARIO)[0]
    
    csv_buffer.write(f"{email}\t{username}\t{biografia}\t{foto}\t{estado}\n")
    
    if (i + 1) % 100000 == 0:
        print(f"  Progreso: {i + 1:,}/{CANTIDAD_USUARIOS:,} usuarios")

csv_buffer.seek(0)
cur.copy_expert("""
    COPY Usuario (email, username, biografia, foto_de_perfil, estado)
    FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '')
""", csv_buffer)
conn.commit()

elapsed = time.time() - start_time
print(f"✓ {CANTIDAD_USUARIOS:,} usuarios en {elapsed:.2f}s ({CANTIDAD_USUARIOS/elapsed:.0f} users/s)\n")

# ============================================================
# 2. SEGUIMIENTOS (ULTRA OPTIMIZADO)
# ============================================================
print(f"📊 [2/6] Generando seguimientos ({SEGUIMIENTOS_POR_USUARIO} por usuario)...")
start_time = time.time()

csv_buffer = io.StringIO()
seguimientos_count = 0
total_usuarios = len(emails)

for idx, email in enumerate(emails):
    # OPTIMIZACIÓN: Usar índices aleatorios en lugar de random.sample
    seguidos_indices = set()
    
    while len(seguidos_indices) < SEGUIMIENTOS_POR_USUARIO:
        random_idx = random.randint(0, total_usuarios - 1)
        if random_idx != idx:  # No seguirse a sí mismo
            seguidos_indices.add(random_idx)
    
    # Escribir al CSV
    for seguido_idx in seguidos_indices:
        csv_buffer.write(f"{email}\t{emails[seguido_idx]}\n")
        seguimientos_count += 1
    
    # Progreso cada 10k usuarios
    if (idx + 1) % 10000 == 0:
        elapsed = time.time() - start_time
        usuarios_por_segundo = (idx + 1) / elapsed
        restantes = (total_usuarios - idx - 1) / usuarios_por_segundo
        print(f"  Progreso: {idx + 1:,}/{total_usuarios:,} ({usuarios_por_segundo:.0f} users/s) ETA: {restantes/60:.1f}min")

csv_buffer.seek(0)
cur.copy_expert("""
    COPY Seguimiento (email_seguidor, email_seguido)
    FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
""", csv_buffer)
conn.commit()

elapsed = time.time() - start_time
print(f"✓ {seguimientos_count:,} seguimientos en {elapsed:.2f}s\n")

# ============================================================
# 3. PUBLICACIONES + MULTIMEDIA (POR LOTES - EVITA MemoryError)
# ============================================================
print(f"📊 [3/6] Generando publicaciones + multimedia...")
start_time = time.time()

fecha_inicio = datetime.now() - timedelta(days=730)  # 2 años atrás
fecha_fin = datetime.now()
rango_segundos = int((fecha_fin - fecha_inicio).total_seconds())

id_pub = 1
id_multimedia = 1
publicaciones_info = []

BATCH_SIZE = 100000  # Procesar de 100k en 100k para no saturar memoria

for batch_start in range(0, len(emails), BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE, len(emails))
    emails_batch = emails[batch_start:batch_end]
    
    pub_csv = io.StringIO()
    img_csv = io.StringIO()
    vid_csv = io.StringIO()
    pub_contenido_csv = io.StringIO()
    
    for email in emails_batch:
        for _ in range(PUBLICACIONES_POR_USUARIO):
            # Fecha aleatoria
            segundos = random.randint(0, rango_segundos)
            fecha = fecha_inicio + timedelta(seconds=segundos)
            fecha_str = fecha.strftime('%Y-%m-%d %H:%M:%S')
            
            # Texto descriptivo (90% tiene texto)
            texto = random.choice(TEXTOS_PUBLICACION_POOL) if random.random() > 0.1 else ''
            
            # Insertar publicación
            pub_csv.write(f"{id_pub}\t{texto}\t{fecha_str}\t{email}\n")
            publicaciones_info.append({'id': id_pub, 'fecha': fecha, 'autor': email})
            
            # Generar multimedia para esta publicación
            for m_idx in range(MULTIMEDIA_POR_PUBLICACION):
                if random.random() < PORCENTAJE_IMAGENES:
                    # Imagen (85% de probabilidad)
                    url = f"img_{id_pub}_{m_idx}.jpg"
                    img_csv.write(f"{id_multimedia}\t{url}\t{fecha_str}\n")
                else:
                    # Video (15% de probabilidad)
                    url = f"vid_{id_pub}_{m_idx}.mp4"
                    vid_csv.write(f"{id_multimedia}\t{url}\t{fecha_str}\n")
                
                # Relación Publicacion_Contenido
                pub_contenido_csv.write(f"{id_multimedia}\t{id_pub}\n")
                id_multimedia += 1
            
            id_pub += 1
    
    # Insertar lote de publicaciones
    pub_csv.seek(0)
    cur.copy_expert("""
        COPY Publicacion (id_publicacion, texto_descriptivo, fecha_de_creacion, email_autor)
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '')
    """, pub_csv)
    
    # Insertar lote de imágenes
    img_csv.seek(0)
    cur.copy_expert("""
        COPY Imagen (id_multimedia, ubicacion_almacenamiento, fecha_subida)
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
    """, img_csv)
    
    # Insertar lote de videos
    vid_csv.seek(0)
    cur.copy_expert("""
        COPY Video (id_multimedia, ubicacion_almacenamiento, fecha_subida)
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
    """, vid_csv)
    
    # Insertar lote de relaciones
    pub_contenido_csv.seek(0)
    cur.copy_expert("""
        COPY Publicacion_Contenido (id_multimedia, id_publicacion)
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
    """, pub_contenido_csv)
    
    conn.commit()
    
    # Progreso
    elapsed = time.time() - start_time
    usuarios_procesados = batch_end
    usuarios_por_segundo = usuarios_procesados / elapsed
    restantes = (total_usuarios - usuarios_procesados) / usuarios_por_segundo
    print(f"  Lote {batch_start//BATCH_SIZE + 1}/{(total_usuarios + BATCH_SIZE - 1)//BATCH_SIZE}: {usuarios_procesados:,}/{total_usuarios:,} ({usuarios_por_segundo:.0f} users/s) ETA: {restantes/60:.1f}min")

# Actualizar secuencia de multimedia
cur.execute(f"SELECT setval('multimedia_id_seq', {id_multimedia});")
conn.commit()

elapsed = time.time() - start_time
total_multimedia = id_multimedia - 1
print(f"✓ {len(publicaciones_info):,} publicaciones + {total_multimedia:,} multimedia en {elapsed:.2f}s\n")

# ============================================================
# 4. ME GUSTAS (POR LOTES - EVITA MemoryError)
# ============================================================
print(f"📊 [4/6] Generando me gustas ({RANGO_LIKES[0]}-{RANGO_LIKES[1]} por usuario)...")
start_time = time.time()

ids_pubs = [p['id'] for p in publicaciones_info]
total_pubs = len(ids_pubs)
likes_count = 0

BATCH_SIZE = 100000  # Procesar de 100k en 100k

for batch_start in range(0, len(emails), BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE, len(emails))
    emails_batch = emails[batch_start:batch_end]
    
    csv_buffer = io.StringIO()
    
    for email in emails_batch:
        cant_likes = random.randint(RANGO_LIKES[0], RANGO_LIKES[1])
        cant_likes = min(cant_likes, total_pubs)
        
        # OPTIMIZACIÓN: Usar índices aleatorios en lugar de random.sample
        likes_indices = set()
        while len(likes_indices) < cant_likes:
            random_idx = random.randint(0, total_pubs - 1)
            likes_indices.add(random_idx)
        
        for idx_pub in likes_indices:
            csv_buffer.write(f"{email}\t{ids_pubs[idx_pub]}\n")
            likes_count += 1
    
    # Insertar lote
    csv_buffer.seek(0)
    cur.copy_expert("""
        COPY Publicacion_MeGusta (email_usuario, id_publicacion)
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
    """, csv_buffer)
    conn.commit()
    
    # Progreso
    elapsed = time.time() - start_time
    usuarios_procesados = batch_end
    usuarios_por_segundo = usuarios_procesados / elapsed
    restantes = (total_usuarios - usuarios_procesados) / usuarios_por_segundo
    print(f"  Lote {batch_start//BATCH_SIZE + 1}/{(total_usuarios + BATCH_SIZE - 1)//BATCH_SIZE}: {usuarios_procesados:,}/{total_usuarios:,} ({usuarios_por_segundo:.0f} users/s) ETA: {restantes/60:.1f}min")

elapsed = time.time() - start_time
print(f"✓ {likes_count:,} me gustas en {elapsed:.2f}s\n")

# ============================================================
# 5. COMENTARIOS (POR LOTES - EVITA MemoryError)
# ============================================================
print(f"📊 [5/6] Generando comentarios ({COMENTARIOS_POR_USUARIO} por usuario)...")
start_time = time.time()

comentarios_por_publicacion = {}
id_comentario = 1

BATCH_SIZE = 100000  # Procesar de 100k en 100k

for batch_start in range(0, len(emails), BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE, len(emails))
    emails_batch = emails[batch_start:batch_end]
    
    csv_buffer = io.StringIO()
    
    for email in emails_batch:
        for _ in range(COMENTARIOS_POR_USUARIO):
            # Seleccionar publicación aleatoria
            pub_info = random.choice(publicaciones_info)
            id_pub = pub_info['id']
            fecha_pub = pub_info['fecha']
            
            # Fecha del comentario (después de la publicación)
            dias_desde_pub = (datetime.now() - fecha_pub).days
            if dias_desde_pub > 0:
                dias_aleatorios = random.randint(0, min(dias_desde_pub, 365))
                fecha_comentario = fecha_pub + timedelta(days=dias_aleatorios)
            else:
                fecha_comentario = fecha_pub
            
            fecha_str = fecha_comentario.strftime('%Y-%m-%d %H:%M:%S')
            texto = random.choice(TEXTOS_COMENTARIO_POOL)
            
            csv_buffer.write(f"{id_comentario}\t{texto}\t{fecha_str}\t{id_pub}\t{email}\n")
            
            # Guardar para generar respuestas después
            if id_pub not in comentarios_por_publicacion:
                comentarios_por_publicacion[id_pub] = []
            comentarios_por_publicacion[id_pub].append(id_comentario)
            
            id_comentario += 1
    
    # Insertar lote
    csv_buffer.seek(0)
    cur.copy_expert("""
        COPY Comentario (id_comentario, texto, fecha_de_creacion, id_publicacion, email_autor)
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
    """, csv_buffer)
    conn.commit()
    
    # Progreso
    elapsed = time.time() - start_time
    usuarios_procesados = batch_end
    usuarios_por_segundo = usuarios_procesados / elapsed
    restantes = (total_usuarios - usuarios_procesados) / usuarios_por_segundo
    print(f"  Lote {batch_start//BATCH_SIZE + 1}/{(total_usuarios + BATCH_SIZE - 1)//BATCH_SIZE}: {usuarios_procesados:,}/{total_usuarios:,} ({usuarios_por_segundo:.0f} users/s) ETA: {restantes/60:.1f}min")

total_comentarios = id_comentario - 1
elapsed = time.time() - start_time
print(f"✓ {total_comentarios:,} comentarios en {elapsed:.2f}s\n")

# ============================================================
# 6. RESPUESTAS (CON COPY)
# ============================================================
print(f"📊 [6/6] Generando respuestas ({RANGO_RESPUESTAS[0]}-{RANGO_RESPUESTAS[1]} por usuario)...")
start_time = time.time()

csv_buffer = io.StringIO()
publicaciones_con_multiples = [
    pub_id for pub_id, comentarios in comentarios_por_publicacion.items()
    if len(comentarios) >= 2
]

respuestas_count = 0
respuestas_insertadas = set()  # Para evitar duplicados en id_hijo

if publicaciones_con_multiples:
    for idx, email in enumerate(emails):
        cant_respuestas = random.randint(RANGO_RESPUESTAS[0], RANGO_RESPUESTAS[1])
        
        for _ in range(cant_respuestas):
            try:
                id_pub = random.choice(publicaciones_con_multiples)
                comentarios = comentarios_por_publicacion[id_pub]
                
                if len(comentarios) >= 2:
                    # Seleccionar hijo y padre diferentes
                    id_hijo, id_padre = random.sample(comentarios, 2)
                    
                    # Evitar duplicados (cada hijo solo puede tener un padre)
                    if id_hijo not in respuestas_insertadas:
                        csv_buffer.write(f"{id_hijo}\t{id_padre}\n")
                        respuestas_insertadas.add(id_hijo)
                        respuestas_count += 1
            except:
                pass
        
        if (idx + 1) % 50000 == 0:
            elapsed = time.time() - start_time
            usuarios_por_segundo = (idx + 1) / elapsed
            restantes = (total_usuarios - idx - 1) / usuarios_por_segundo
            print(f"  Progreso: {idx + 1:,}/{total_usuarios:,} ({usuarios_por_segundo:.0f} users/s) ETA: {restantes/60:.1f}min")
    
    csv_buffer.seek(0)
    cur.copy_expert("""
        COPY Comentario_Responde (id_hijo, id_padre)
        FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
    """, csv_buffer)
    conn.commit()

elapsed = time.time() - start_time
print(f"✓ {respuestas_count:,} respuestas en {elapsed:.2f}s\n")

# ============================================================
# REACTIVAR CONSTRAINTS Y TRIGGERS
# ============================================================
print("🔧 REACTIVANDO CONSTRAINTS Y TRIGGERS...")
cur.execute("SET session_replication_role = DEFAULT;")
cur.execute("ALTER TABLE Publicacion ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Comentario ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Publicacion_MeGusta ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Seguimiento ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Comentario_Responde ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Publicacion_Contenido ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Imagen ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Video ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Audio ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Mensaje ENABLE TRIGGER ALL;")
cur.execute("ALTER TABLE Mensaje_Contenido ENABLE TRIGGER ALL;")
conn.commit()
print("✓ Constraints y triggers reactivados\n")

# ============================================================
# CONVERTIR A LOGGED (PERSISTENCIA)
# ============================================================
print("🔧 CONVIRTIENDO TABLAS A LOGGED...")
for tabla in tablas:
    try:
        cur.execute(f"ALTER TABLE {tabla} SET LOGGED;")
    except Exception as e:
        print(f"  ⚠ {tabla}: {e}")

conn.commit()
print("✓ Tablas convertidas a LOGGED\n")

# ============================================================
# ACTUALIZAR ESTADÍSTICAS (IMPORTANTE PARA CONSULTAS)
# ============================================================
print("🔧 ACTUALIZANDO ESTADÍSTICAS DE TABLAS...")
cur.execute("ANALYZE;")
conn.commit()
print("✓ Estadísticas actualizadas\n")

# ============================================================
# FINALIZAR
# ============================================================
cur.close()
conn.close()

elapsed_global = time.time() - start_global

print("="*70)
print("✅ GENERACIÓN COMPLETA")
print("="*70)
print(f"Total usuarios:       {CANTIDAD_USUARIOS:,}")
print(f"Total seguimientos:   {seguimientos_count:,}")
print(f"Total publicaciones:  {len(publicaciones_info):,}")
print(f"Total multimedia:     {total_multimedia:,}")
print(f"Total me gustas:      {likes_count:,}")
print(f"Total comentarios:    {total_comentarios:,}")
print(f"Total respuestas:     {respuestas_count:,}")
print(f"\n⏱️  TIEMPO TOTAL:      {elapsed_global/60:.2f} minutos")
print("="*70)

# Cálculo de tuplas totales
total_tuplas = (CANTIDAD_USUARIOS + seguimientos_count + len(publicaciones_info) + 
                total_multimedia + likes_count + total_comentarios + respuestas_count + 
                len(publicaciones_info))  # Publicacion_Contenido

print(f"\n📊 Total de tuplas insertadas: {total_tuplas:,}")
print(f"📊 Velocidad promedio: {total_tuplas/elapsed_global:.0f} tuplas/segundo")
print(f"\n🎯 Listo para experimentación!")