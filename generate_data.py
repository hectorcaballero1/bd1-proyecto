import psycopg2
from faker import Faker
import random

fake = Faker('es_ES')

# Conectar (usa las mismas credenciales del .env)
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="red_social",      # DB_NAME del .env
    user="postgres",             # DB_USER del .env
    password="postgres123"       # DB_PASSWORD del .env
)
cur = conn.cursor()

print("✓ Conectado a PostgreSQL")

# Generar 1000 usuarios
print("Insertando usuarios...")
for i in range(1000):
    email = f"user{i}@test.com"
    username = f"usuario_{i}"
    biografia = fake.text(max_nb_chars=150)
    foto = f"foto_{i}.jpg"
    estado = 'A'
    
    cur.execute(
        """INSERT INTO Usuario (email, username, biografia, foto_de_perfil, estado)
           VALUES (%s, %s, %s, %s, %s)""",
        (email, username, biografia, foto, estado)
    )
    
    if (i + 1) % 100 == 0:
        print(f"  {i + 1} usuarios insertados...")
        conn.commit()

conn.commit()
print("✓ 1000 usuarios creados!")

cur.close()
conn.close()