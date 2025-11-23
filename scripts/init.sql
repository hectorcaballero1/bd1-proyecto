-- ============================================================
-- 1. CREACIÓN DE TABLAS
-- ============================================================

CREATE TABLE Usuario (
    email VARCHAR(255) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    biografia VARCHAR(255),
    foto_de_perfil VARCHAR(255),
    fecha_de_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado CHAR(1) NOT NULL CHECK (estado IN ('A', 'D', 'E')) 
);

CREATE TABLE Seguimiento (
    email_seguidor VARCHAR(255) NOT NULL,
    email_seguido VARCHAR(255) NOT NULL,
    PRIMARY KEY (email_seguidor, email_seguido),
    FOREIGN KEY (email_seguidor) REFERENCES Usuario(email),
    FOREIGN KEY (email_seguido) REFERENCES Usuario(email),
    CONSTRAINT check_no_self_follow CHECK (email_seguidor<>email_seguido)
);

CREATE TABLE Publicacion (
    id_publicacion BIGSERIAL PRIMARY KEY,
    texto_descriptivo VARCHAR(2200),
    fecha_de_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_autor VARCHAR(255) NOT NULL,
    FOREIGN KEY (email_autor) REFERENCES Usuario(email)
);

CREATE TABLE Publicacion_MeGusta (
    email_usuario VARCHAR(255) NOT NULL,
    id_publicacion BIGINT NOT NULL,
    PRIMARY KEY (email_usuario, id_publicacion),
    FOREIGN KEY (email_usuario) REFERENCES Usuario(email),
    FOREIGN KEY (id_publicacion) REFERENCES Publicacion(id_publicacion)
);

CREATE TABLE Comentario (
    id_comentario BIGSERIAL PRIMARY KEY,
    texto VARCHAR(2200) NOT NULL,
    fecha_de_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_publicacion BIGINT NOT NULL,
    email_autor VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_publicacion) REFERENCES Publicacion(id_publicacion),
    FOREIGN KEY (email_autor) REFERENCES Usuario(email)
);

CREATE TABLE Comentario_Responde (
    id_hijo BIGINT PRIMARY KEY,
    id_padre BIGINT NOT NULL,
    FOREIGN KEY (id_hijo) REFERENCES Comentario(id_comentario),
    FOREIGN KEY (id_padre) REFERENCES Comentario(id_comentario),
    CONSTRAINT check_no_self_reply CHECK (id_hijo <> id_padre)
);

CREATE TABLE Mensaje (
    id_mensaje BIGSERIAL PRIMARY KEY,
    texto VARCHAR(1000),
    fecha_de_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado CHAR(1) NOT NULL CHECK (estado IN ('E', 'R', 'L')), 
    email_remitente VARCHAR(255) NOT NULL,
    email_destinatario VARCHAR(255) NOT NULL,
    FOREIGN KEY (email_remitente) REFERENCES Usuario(email),
    FOREIGN KEY (email_destinatario) REFERENCES Usuario(email),
    CONSTRAINT check_no_self_message CHECK (email_remitente <> email_destinatario)
);

CREATE SEQUENCE multimedia_id_seq START 1;

CREATE TABLE Imagen (
    id_multimedia BIGINT PRIMARY KEY DEFAULT nextval('multimedia_id_seq'),
    ubicacion_almacenamiento VARCHAR(255) NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Video (
    id_multimedia BIGINT PRIMARY KEY DEFAULT nextval('multimedia_id_seq'),
    ubicacion_almacenamiento VARCHAR(255) NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Audio (
    id_multimedia BIGINT PRIMARY KEY DEFAULT nextval('multimedia_id_seq'),
    ubicacion_almacenamiento VARCHAR(255) NOT NULL,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Publicacion_Contenido (
    id_multimedia BIGINT PRIMARY KEY,
    id_publicacion BIGINT NOT NULL,
    FOREIGN KEY (id_publicacion) REFERENCES Publicacion(id_publicacion)
);

CREATE TABLE Mensaje_Contenido (
    id_multimedia BIGINT PRIMARY KEY,
    id_mensaje BIGINT NOT NULL,
    FOREIGN KEY (id_mensaje) REFERENCES Mensaje(id_mensaje)
);

-- ============================================================
-- 2. TRIGGERS - RESTRICCIÓN DE MULTIMEDIA OBLIGATORIO
-- ============================================================

-- Función: Validar que una publicación tenga multimedia
CREATE OR REPLACE FUNCTION check_publicacion_tiene_multimedia()
RETURNS TRIGGER AS $$
BEGIN
    -- Verificar si la publicación tiene al menos un multimedia
    IF NOT EXISTS (
        SELECT 1 
        FROM Publicacion_Contenido 
        WHERE id_publicacion = NEW.id_publicacion
    ) THEN
        RAISE EXCEPTION 'La publicacion % debe tener al menos un elemento multimedia', 
                        NEW.id_publicacion;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger diferido: Se ejecuta al COMMIT
CREATE CONSTRAINT TRIGGER enforce_multimedia_required
AFTER INSERT ON Publicacion
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION check_publicacion_tiene_multimedia();

-- ============================================================
-- 3. TRIGGERS - PREVENIR ELIMINACIÓN DEL ÚLTIMO MULTIMEDIA
-- ============================================================

-- Función: Prevenir que se elimine el último multimedia de una publicación
CREATE OR REPLACE FUNCTION prevent_last_multimedia_deletion()
RETURNS TRIGGER AS $$
BEGIN
    -- Contar cuántos multimedia quedan para esta publicación
    IF (SELECT COUNT(*) 
        FROM Publicacion_Contenido 
        WHERE id_publicacion = OLD.id_publicacion) <= 1 THEN
        RAISE EXCEPTION 'No se puede eliminar el ultimo multimedia de la publicacion %', 
                        OLD.id_publicacion;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Ejecutar antes de DELETE
CREATE TRIGGER trigger_prevent_last_multimedia_delete
BEFORE DELETE ON Publicacion_Contenido
FOR EACH ROW
EXECUTE FUNCTION prevent_last_multimedia_deletion();