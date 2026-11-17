-- MDGA schema (Milestone 2: Tables 6, 11, 12 and 13)
SET NAMES utf8mb4;

-- Time slots: 60, from Monday 7:00 to Saturday 16:00
CREATE TABLE franjas (
  id INT PRIMARY KEY,                 -- t = 1..60
  dia TINYINT NOT NULL,               -- 1=Monday .. 6=Saturday
  hora_inicio TIME NOT NULL,
  hora_fin TIME NOT NULL
);

CREATE TABLE salones (
  id INT AUTO_INCREMENT PRIMARY KEY,  -- r
  codigo VARCHAR(30) NOT NULL UNIQUE,
  capacidad INT NOT NULL CHECK (capacidad > 0)
);

CREATE TABLE docentes (
  id INT AUTO_INCREMENT PRIMARY KEY,  -- l
  codigo VARCHAR(30) NOT NULL UNIQUE,
  nombre VARCHAR(120)
);

-- Teacher availability / preference per time slot
CREATE TABLE disponibilidad_docente (
  docente_id INT NOT NULL,
  franja_id INT NOT NULL,
  disponible BOOLEAN NOT NULL DEFAULT TRUE,
  preferida BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (docente_id, franja_id),
  FOREIGN KEY (docente_id) REFERENCES docentes(id) ON DELETE CASCADE,
  FOREIGN KEY (franja_id) REFERENCES franjas(id)
);

CREATE TABLE materias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(30) NOT NULL UNIQUE,
  nombre VARCHAR(120),
  horas_semanales INT NOT NULL CHECK (horas_semanales > 0)
);

CREATE TABLE estudiantes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(30) NOT NULL UNIQUE
);

-- Group = class c (section of a subject) with its teacher
CREATE TABLE grupos (
  id INT AUTO_INCREMENT PRIMARY KEY,  -- c
  codigo VARCHAR(30) NOT NULL UNIQUE,
  materia_id INT NOT NULL,
  docente_id INT NOT NULL,
  FOREIGN KEY (materia_id) REFERENCES materias(id),
  FOREIGN KEY (docente_id) REFERENCES docentes(id)
);

-- Set S of students in the group
CREATE TABLE grupo_estudiante (
  grupo_id INT NOT NULL,
  estudiante_id INT NOT NULL,
  PRIMARY KEY (grupo_id, estudiante_id),
  FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
  FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
);

-- Events e = (l, c, S): one per weekly hour of the group's subject
CREATE TABLE eventos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  grupo_id INT NOT NULL,
  indice INT NOT NULL,                -- 1..horas_semanales
  UNIQUE (grupo_id, indice),
  FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
);

-- Logical rules (Table 6)
CREATE TABLE reglas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL UNIQUE,
  tipo ENUM('HC','SC') NOT NULL,
  nivel ENUM('superficial','medio','profundo') NOT NULL,
  condicion VARCHAR(255) NOT NULL,     -- identifier/expression evaluated by the engine
  peso DOUBLE NOT NULL CHECK (peso >= 0),
  activa BOOLEAN NOT NULL DEFAULT TRUE,
  descripcion VARCHAR(255)
);

-- Run = execution with its parameters (Table 12)
CREATE TABLE corridas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  creada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado ENUM('pendiente','ejecutando','cancelando','cancelada','terminada','error')
         NOT NULL DEFAULT 'pendiente',
  t_max INT NOT NULL CHECK (t_max > 0),
  k INT NOT NULL CHECK (k > 0),
  n INT NOT NULL CHECK (n > 0),
  tau INT NOT NULL CHECK (tau > 0),
  pc DOUBLE NOT NULL CHECK (pc BETWEEN 0 AND 1),
  pm DOUBLE NOT NULL CHECK (pm BETWEEN 0 AND 1),
  semilla INT,
  -- Summary results (filled in when finished)
  n_eventos INT,
  generaciones INT,
  g_factible INT,                     -- G_f: generations until H = 0
  mejor_f DOUBLE,
  mejor_h DOUBLE,
  f_inicial DOUBLE,                   -- F0* for Delta F
  evaluaciones INT,
  detenida_por VARCHAR(20),           -- t_max | calidad | cancelada
  tiempo_s DOUBLE,
  mensaje TEXT,                       -- error detail
  CHECK (k < n)
);

-- Evolution history: best fitness and diversity per iteration
CREATE TABLE historial (
  corrida_id INT NOT NULL,
  iteracion INT NOT NULL,
  mejor_f DOUBLE NOT NULL,
  mejor_h DOUBLE,
  media_f DOUBLE,
  diversidad DOUBLE,
  PRIMARY KEY (corrida_id, iteracion),
  FOREIGN KEY (corrida_id) REFERENCES corridas(id) ON DELETE CASCADE
);

-- k best schedules per iteration (traceability)
CREATE TABLE horarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  corrida_id INT NOT NULL,
  iteracion INT NOT NULL,
  rango INT NOT NULL,                 -- 1..k
  aptitud DOUBLE NOT NULL,            -- F(P)
  h DOUBLE NOT NULL,                  -- H(P)
  s DOUBLE NOT NULL,                  -- S(P)
  UNIQUE (corrida_id, iteracion, rango),
  FOREIGN KEY (corrida_id) REFERENCES corridas(id) ON DELETE CASCADE
);

-- Genes: (t, r) package assigned to each event
CREATE TABLE asignaciones (
  horario_id INT NOT NULL,
  evento_id INT NOT NULL,
  franja_id INT NOT NULL,
  salon_id INT NOT NULL,
  PRIMARY KEY (horario_id, evento_id),
  FOREIGN KEY (horario_id) REFERENCES horarios(id) ON DELETE CASCADE,
  -- If groups/subjects change, events are regenerated and the
  -- historical assignments of those events are deleted with them.
  FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE,
  FOREIGN KEY (franja_id) REFERENCES franjas(id),
  FOREIGN KEY (salon_id) REFERENCES salones(id)
);

-- Breakdown of violations V_i(P) by rule (explanation subsystem)
CREATE TABLE violaciones (
  horario_id INT NOT NULL,
  regla_id INT NOT NULL,
  conteo INT NOT NULL,                -- V_i(P)
  penalizacion DOUBLE NOT NULL,       -- w_i * V_i(P)
  eventos_json JSON,                  -- events involved
  PRIMARY KEY (horario_id, regla_id),
  FOREIGN KEY (horario_id) REFERENCES horarios(id) ON DELETE CASCADE,
  FOREIGN KEY (regla_id) REFERENCES reglas(id) ON DELETE CASCADE
);

-- Seed data: 60 time slots (10 per day, Monday to Saturday, 7:00 to 17:00; the last one starts at 16:00)
INSERT INTO franjas (id, dia, hora_inicio, hora_fin)
WITH RECURSIVE seq(n) AS (SELECT 0 UNION ALL SELECT n + 1 FROM seq WHERE n < 59)
SELECT n + 1, FLOOR(n / 10) + 1,
       SEC_TO_TIME((7 + MOD(n, 10)) * 3600),
       SEC_TO_TIME((8 + MOD(n, 10)) * 3600)
FROM seq;

-- Base rules (Table 3 / Table 4)
INSERT INTO reglas (nombre, tipo, nivel, condicion, peso, descripcion) VALUES
 ('disponibilidad_docente','HC','superficial','docente_no_disponible',1000,'Evento en franja no disponible del docente'),
 ('capacidad_sala','HC','superficial','estudiantes_excede_capacidad',1000,'|S| mayor que la capacidad de la sala'),
 ('conflicto_docente','HC','medio','docente_dos_eventos_misma_franja',1000,'Docente con dos eventos simultáneos'),
 ('conflicto_clase','HC','medio','clase_dos_eventos_misma_franja',1000,'Clase con dos eventos simultáneos'),
 ('conflicto_sala','HC','medio','sala_dos_eventos_misma_franja',1000,'Sala con dos eventos simultáneos'),
 ('preferencia_docente','SC','superficial','fuera_de_franja_preferida',5,'Evento fuera de la franja preferida del docente'),
 ('distribucion_carga','SC','medio','carga_diaria_desbalanceada',3,'Desbalance de horas diarias del docente'),
 ('separacion_eventos','SC','medio','eventos_clase_mismo_dia',2,'Eventos de una misma clase en el mismo día'),
 ('conflicto_estudiantes','SC','profundo','estudiante_dos_eventos_misma_franja',10,'Estudiante con eventos simultáneos');
