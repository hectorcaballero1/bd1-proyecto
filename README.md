# Instrucciones de uso

## Setup inicial

Crear el virtual enviroment

```sh
python -m venv venv

# Windows (PowerShell):

venv\Scripts\activate

# Mac/Linux:

source venv/bin/activate

# Instalar dependencias

pip install -r requirements.txt
```

Levantar la base de datos con docker

```sh
docker-compose up -d
```

Borrar la base de datos

```sh
docker-compose down -v
```

## Guía para generar y verificar dumps

Pasos para generar dump (1k, 10k, 100k, 1M)

Nota: El proceso es idéntico para todos los volúmenes, solo cambia CANTIDAD_USUARIOS en el script Python y el nombre del dump.

1. Limpiar y levantar base de datos

Windows:

```sh
docker-compose down -v
docker-compose up -d
```

Linux/Mac:


```sh
docker-compose down -v
docker-compose up -d
```
2. Verificar el entorno virtual de Python

Windows:

```sh
venv\Scripts\activate
```

Linux/Mac:

```sh
source venv/bin/activate
```

3. Configurar cantidad de usuarios

Editar scripts/generar_datos.py y cambiar la línea:

```python
CANTIDAD_USUARIOS = 1000  # Cambiar según: 1000, 10000, 100000, 1000000
```

4. Ejecutar script

Windows:

```sh
python scripts\generar_datos.py
```

Linux/Mac:

```sh
python scripts/generar_datos.py
```

5. Crear dump

Windows:

```sh
docker exec red-social-db pg_dump -U postgres --data-only red_social > dumps\dump_1k.sql
```

Linux/Mac:

```sh
docker exec red-social-db pg_dump -U postgres --data-only red_social > dumps/dump_1k.sql
```

Cambiar el nombre del dump según corresponda:

- dump_1k.sql para 1,000 usuarios
- dump_10k.sql para 10,000 usuarios
- dump_100k.sql para 100,000 usuarios
- dump_1M.sql para 1,000,000 usuarios

6. Verificar dump

Borrar base de datos y volver a levantar

```sh
docker-compose down -v
docker-compose up -d
```

Restaurar la base de datos

Windows: 

```sh
Get-Content dumps\dump_1k.sql | docker exec -i red-social-db psql -U postgres -d red_social
```

Linux/Mac:

```sh
docker exec -i red-social-db psql -U postgres -d red_social < dumps/dump_1k.sql
```

Cambiar dump_1k.sql por el dump que se quiere restaurar.

7. Verificacion final

```sh
docker exec -it red-social-db psql -U postgres -d red_social -c "SELECT COUNT(*) FROM Usuario;"
```

**Resultado esperado:**

```sh
 count 
-------
  1000
(1 row)
```

El número debe coincidir con CANTIDAD_USUARIOS del script.