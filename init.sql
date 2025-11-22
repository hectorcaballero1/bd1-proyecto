-- init.sql
-- Este script se ejecuta automáticamente cuando se crea el contenedor

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
    CONSTRAINT check_no_self_follow CHECK (email_seguidor <> email_seguido)
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