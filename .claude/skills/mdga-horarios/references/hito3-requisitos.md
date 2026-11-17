# Hito 3: Prototipo funcional (Semanas 8 a 11, Módulo III)

Transcripción del enunciado (fuente: `image.jpeg`).

Durante este hito el equipo deberá transformar el diseño conceptual en un **prototipo funcional**.

## 5.1 Construcción
El sistema deberá implementar los principales componentes definidos durante el Hito 2 y demostrar la interacción entre los mecanismos de razonamiento, las fuentes de conocimiento y el entorno.

Cuando corresponda, deberá existir una conexión funcional entre el **motor de inferencia** y la **base de hechos o conocimiento**.

## 5.2 Prototipo Alpha
El prototipo Alpha corresponde a la primera versión funcional de la solución. Deberá demostrar la implementación de los componentes fundamentales y permitir identificar problemas de arquitectura, integración o razonamiento.

## 5.3 Prototipo Beta
El prototipo Beta deberá incorporar las correcciones identificadas durante las pruebas del prototipo Alpha y demostrar un comportamiento integrado y estable del sistema.

## 5.4 Evaluación
La evaluación deberá realizarse mediante métricas cuantitativas apropiadas para la técnica seleccionada.

Las métricas deberán estar justificadas a partir de la literatura científica analizada durante el Hito 1.

**Principio de evaluación:** No basta con demostrar que el programa "funciona". El equipo deberá demostrar mediante evidencia experimental que la solución cumple los objetivos definidos y explicar sus fortalezas y limitaciones.

## Correspondencia con el diseño del Hito 2
| Requisito H3 | Elemento del H2 |
|---|---|
| Motor de inferencia | Evaluador de reglas con `F(P) = Σ w_i V_i(P)` (sección 7.1), en sus niveles superficial, medio y profundo |
| Base de hechos/conocimiento | MySQL: datos académicos, reglas (nombre, tipo, condición, peso, estado) y parámetros |
| Mecanismos de razonamiento | Reglas + pipeline del AG (torneo, cruce uniforme por evento, mutación por reasignación, elitismo k) |
| Entorno | Web (HTTPS), ingesta CSV/XLSX, API REST/JSON |
| Métricas | Sección 11: H, S, F, R_f, G_f, ΔF, convergencia, D_t, tiempo, cobertura explicativa; 30 corridas |
| Literatura del Hito 1 | Refs. [1] Alkan & Özcan 2003, [2] Badoni 2023, [3] González López 2021, [4] Gozali 2020, [6] Müller 2025 (ITC 2019) |

## Sugerencias para el entregable
- **Alpha:** ingesta y datos en MySQL, generación de eventos, cromosoma, evaluador con las HC básicas, AG completo y guardado de los k mejores. Hay que documentar los problemas encontrados.
- **Beta:** reglas configurables desde la web, todas las HC/SC, subsistema explicativo, dashboard de convergencia, estabilidad y correcciones de lo visto en Alpha (con una tabla "problema → corrección").
- **Experimentos:** 30 corridas por configuración, con media, desviación estándar y mejor resultado. Incluir curvas de convergencia, la tasa de factibilidad, un análisis de sensibilidad a τ, pm, N y k, y una discusión de fortalezas y limitaciones.
