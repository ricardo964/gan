# Prototipo Alpha: MDGA para horarios UTP

**Hito 3, secciones 5.1 (Construcción) y 5.2 (Prototipo Alpha)**. Fecha: 16 de noviembre de 2026.

El Alpha es la primera versión funcional de la solución. Implementa los componentes definidos en el
Hito 2 y sirve para **identificar problemas de arquitectura, integración y razonamiento**, que la
Beta (5.3) deberá corregir.

---

## 1. Construcción (5.1)

### 1.1 Componentes implementados

| Componente del Hito 2 (Tabla 8) | Implementación | Estado |
|---|---|---|
| Repositorio de datos (MySQL) | `db/init.sql`, `app/models/repo.py` | ✅ |
| Núcleo de cómputo (motor MDGA) | `engine/` (`problem`, `rules`, `fitness`, `operators`, `ga`) | ✅ |
| Subsistema explicativo | `explain/explainer.py` + vista y API de explicación | ✅ |
| Pipelines de ingesta | `ingest/pipeline.py` (CSV/XLSX con validación) | ✅ |
| Interfaz y módulos de comunicación | `app/controllers/*`, `app/templates/*`, API `/api/v1` | ✅ |

### 1.2 Interacción entre razonamiento, conocimiento y entorno

```
 Entorno                         Conocimiento                    Razonamiento
 ───────                         ────────────                    ────────────
 Coordinación UTP ─ XLSX/CSV ─▶ ingest (valida) ─▶ MySQL ◀──┐
 Usuario ─ HTTPS ─▶ Flask (Vista+Controlador) ─ reglas ─▶   │
                                     │                      │
                     parámetros ─────┤                      │
                                     ▼                      │
                     services/optimizer (hilo)              │
                       repo.load_problem() ── hechos ──▶ engine.Problem
                       repo.load_rules()   ── reglas ──▶ engine.Evaluator (motor de inferencia)
                                                         engine.run_ga  (pipeline evolutivo)
                       ◀── on_iteration: mejores k ───── │
                       explain() ◀── mejores k ──────────┘
                       repo.save_* ─────────────────────────┘ (historial, k mejores, violaciones)
 Sistemas externos ◀─ REST/JSON ─ /api/v1
```

**Conexión entre el motor de inferencia y la base de hechos**, que el Hito 3 pide de forma explícita:
- `repo.load_problem()` transforma las tablas de MySQL (franjas, salones, disponibilidad,
  inscripciones y eventos) en los arreglos NumPy del `Problem`.
- `repo.load_rules()` convierte las reglas almacenadas (nombre, tipo, nivel, condición, peso y estado)
  en objetos `engine.Rule`. El `Evaluator` resuelve la `condicion` de cada regla contra el catálogo
  `engine/rules.py`.
- Los resultados del razonamiento regresan a la base: `historial`, `horarios`, `asignaciones` y
  `violaciones`.
- Si se cambia una regla en la web o por la API, cambia la evaluación de la siguiente corrida sin tocar
  el código (configurabilidad, métrica 11.3).

### 1.3 Fidelidad al diseño del Hito 2

| Elemento del diseño | Implementación |
|---|---|
| q = (t, r), e = (l, c, S), P = {(q, e)} | `Problem`; cromosoma entero (E, 2) |
| Solo t y r son variables | Los operadores no tocan `event_teacher`, `event_class` ni `class_students` |
| F = Σ wᵢVᵢ, H, S, con w_HC ≫ w_SC | `Evaluator`; reglas semilla con 1000 frente a 2–10 |
| Niveles superficial, medio y profundo | Campo `nivel` en cada regla y desglose `by_level` |
| Torneo τ, cruce uniforme por evento, mutación por reasignación (3 variantes) y elitismo k | `engine/operators.py` |
| P_{t+1} = Best_k(P_t) ∪ C_t, con \|C_t\| = N − k | `engine/ga.py` |
| Terminación por T_max o por criterio de calidad | `GAParams.t_max` / `target_f`, más cancelación |
| Persistencia de los k mejores con iteración y aptitud | Tabla `horarios`, una fila por (iteración, rango) |
| 60 franjas, de lunes 7:00 a sábado 16:00 | Semilla de `franjas` (bloques de 1 h; el tamaño del bloque es un supuesto) |

**Desviación consciente:** las *asignaciones* (t, r) completas solo se guardan para los k mejores de la
**iteración final**. En el resto de las iteraciones se guardan su F, H y S. Guardar E × k filas en
cada iteración generaría cientos de miles de filas por corrida (ver el hallazgo A5).

### 1.4 Verificación

- **35 pruebas unitarias** (`pytest`) del evaluador (cada condición calculada a mano), los operadores,
  el pipeline (factibilidad, monotonía por elitismo, reproducibilidad, criterios de parada), el
  subsistema explicativo y la ingesta.
- **Prueba de integración manual** sobre Docker (web + MySQL):
  1. Importar `datos/ejemplo_utp.xlsx`.
  2. Rechazar una regla inválida y parámetros inválidos (respuesta 400).
  3. Ejecutar una corrida y ver el horario por grupo, docente y salón.
  4. Ver la explicación (cobertura del 100 %) y exportar el CSV.
  5. Probar la API: CRUD de reglas (400 y 409), corridas (202), historial y horarios.
  6. Cancelar una corrida en curso.

---

## 2. Resultados experimentales del Alpha

Experimento hecho con `scripts/experimento.py`:
- Parámetros por defecto: T_max = 300, N = 60, k = 5, τ = 3, p_c = 0.9, p_m = 0.01.
- Se usan las reglas semilla.
- Cada corrida usa una semilla distinta.

### 2.1 Instancia base: 98 eventos, 12 salas, 15 docentes, 30 grupos, 190 estudiantes. 10 corridas

| Métrica | Media ± desv. | [mín, máx] |
|---|---|---|
| Tasa de factibilidad R_f | **1.00** | |
| F* | 534.3 ± 48.2 | [416.7, 622.5] |
| H* | 0 | |
| G_f (generaciones hasta H = 0) | 47.1 ± 6.9 | [32, 55] |
| ΔF | 0.989 ± 0.001 | |
| Diversidad final D_T | 0.060 ± 0.014 | [0.035, 0.090] |
| Horarios distintos entre los k = 5 mejores | 3.9 ± 0.9 | [3, 5] |
| Tiempo | 7.4 ± 0.1 s | |

Violaciones blandas medias que quedan (Vᵢ): conflictos de estudiantes 47.3 (× w = 10), carga docente 10.8
(× 3), preferencias 5.6 (× 5) y separación 0.4 (× 2).

### 2.2 Instancia mayor: 280 eventos, 18 salas, 40 docentes, 90 grupos, 529 estudiantes. 5 corridas

| Métrica | Media ± desv. | [mín, máx] |
|---|---|---|
| R_f | **1.00** | |
| F* | 5024.4 ± 252.6 | [4682.3, 5346.7] |
| G_f | 168.4 ± 40.3 | [96, 215] |
| ΔF | 0.965 ± 0.002 | |
| D_T | 0.076 ± 0.011 | |
| Tiempo | **48.6 ± 0.7 s** | |
| Conflictos de estudiantes restantes | 468.2 | |

### 2.3 Perfil de costo por regla (instancia mayor, ms por individuo)

| Regla | Nivel | ms |
|---|---|---|
| conflicto_estudiantes | profundo | **2.94** |
| distribucion_carga | medio | 0.048 |
| resto (7 reglas) | superficial/medio | 0.006–0.019 cada una |
| Diversidad D_t (por iteración, N = 60) | | 6.4 |

El nivel profundo consume ≈ 95 % del tiempo de evaluación.

---

## 3. Problemas identificados (para la Beta)

### Razonamiento

| # | Problema | Evidencia | Propuesta para la Beta |
|---|---|---|---|
| R1 | **Convergencia prematura.** La población colapsa (D_T ≈ 0.06), y después de alcanzar H = 0 casi no mejora la parte blanda. | D_T de 0.035 a 0.09; la curva de F se estanca tras G_f. | Mutación adaptativa (subir p_m cuando D_t cae), inmigrantes aleatorios o reinicio parcial; estudiar τ. |
| R2 | **Clones entre los k mejores.** El elitismo conserva copias idénticas, así que "los k mejores horarios" no son k alternativas distintas. | 3.9 de 5 distintos en promedio; en la primera corrida web los 3 mejores tenían exactamente la misma F (666.26). | Elitismo sin duplicados: Best_k sobre individuos únicos. |
| R3 | **El nivel profundo domina el costo** (≈ 95 %) y no escala bien: la instancia mayor tarda 6.5 veces más con 2.9 veces más eventos. | Perfil §2.3. | (a) Multiplicación de matrices en `float32` (con BLAS) o dispersa; (b) evaluación multi-profundidad escalonada: calcular el nivel profundo solo cuando los niveles superficial y medio son prometedores (por ejemplo H = 0 o candidatos a élite). |
| R4 | **Calibración de pesos.** `conflicto_estudiantes` domina S(P), así que la búsqueda ignora la carga docente y las preferencias. | §2.1 y §2.2. | Análisis de sensibilidad de los pesos y normalización por cantidad de estudiantes. |
| R5 | La inicialización aleatoria ignora la capacidad y la disponibilidad, por lo que F₀ es muy alto (≈ 5·10⁴). | `f_inicial` de las corridas. | Comparar experimentalmente con una inicialización heurística (salas con capacidad suficiente), manteniendo la aleatoria como línea base del Hito 2. |

### Integración y persistencia

| # | Problema | Evidencia | Propuesta para la Beta |
|---|---|---|---|
| I1 | **`violaciones.conteo` es INT** y trunca Vᵢ reales (la carga diaria es una desviación estándar). La explicación muestra 12 cuando V = 12.107. | Consulta a la BD (penalización 36.32 / w 3). | Cambiar la columna a `DOUBLE`. |
| I2 | **Editar los datos después de una corrida rompe la trazabilidad.** Al regenerar eventos se borran en cascada las asignaciones históricas, y la importación elimina todas las corridas. | Diseño de `sync_eventos` y `replace_academic_data`. | Versionar el conjunto de datos (copia inmutable por corrida) o bloquear ediciones con corridas asociadas. |
| I3 | Las corridas viven en hilos del proceso web. Un reinicio las interrumpe (quedan marcadas como `error`). | `mark_interrupted()`. | Cola de trabajos (proceso *worker* aparte) y reanudación. |
| I4 | La validación de la ingesta va en dos fases: los errores de tipo ocultan los de rango hasta que se corrigen. | Prueba con `salones.csv` (capacidad −3 y "x"). | Reportar todos los errores en una sola pasada. |

### Arquitectura y calidad

| # | Problema | Propuesta para la Beta |
|---|---|---|
| A1 | No hay pruebas automáticas de integración web/API contra MySQL (solo pruebas manuales). | Base `mdga_test` en Docker y pruebas con `app.test_client()`. |
| A2 | Los estudiantes e inscripciones solo se cargan por ingesta, no desde formularios. | Formularios de inscripción o carga parcial por entidad. |
| A3 | La API no tiene autenticación. | Token de API y roles (coordinación, consulta). |
| A4 | Datos solo sintéticos. | Validar con datos reales de la coordinación UTP. |
| A5 | Las asignaciones solo se guardan en la iteración final (desviación §1.3). | Parámetro "guardar cada m iteraciones" si se necesita reconstruir horarios intermedios. |

---

## 4. Cómo reproducir

```bash
docker compose up -d                       # web :5000, MySQL :3306, Adminer :8080
# Importar datos/ejemplo_utp.xlsx en http://localhost:5000/ingesta/
.venv/bin/python -m pytest -q              # pruebas unitarias
.venv/bin/python scripts/experimento.py --corridas 10 --tmax 300
.venv/bin/python scripts/experimento.py --corridas 5 --tmax 300 \
    --grupos 90 --estudiantes 1500 --salones 18 --docentes 40 --materias 45
```

Nota: el protocolo del Hito 2 (§11) pide 30 corridas por configuración. Las 10 y 5 de este informe
son exploratorias, para detectar problemas. La evaluación formal (5.4) debe usar 30.
