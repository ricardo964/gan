---
name: mdga-horarios
description: Contexto completo del proyecto UTP "Programación de horarios universitarios mediante un Algoritmo Genético Multi-Profundidad (MDGA)": diseño formal del Hito 2 (modelo, cromosoma, función de aptitud, arquitectura MVC + MySQL, operadores genéticos, métricas) y requisitos del Hito 3 (prototipo Alpha/Beta, evaluación con métricas). Úsala siempre que el usuario trabaje en este proyecto: implementar el motor MDGA, la base de datos, la app web, las reglas, el subsistema explicativo, los experimentos/métricas, o redactar informes/hitos del curso, aunque solo diga "el algoritmo", "el proyecto", "el hito" o "los horarios".
---

# Proyecto MDGA – Horarios universitarios UTP

**Curso:** Universidad Tecnológica de Panamá, FISC, Depto. de Computación y Simulación de Sistemas.
**Docente:** Nicolás Benjamín Beliz Osorio.
**Equipo:** Alejandro Muñoz, Liam Thompson y Ricardo Villarreal.
**Hito 2** (diseño formal) entregado el 1 de octubre de 2026. **Hito 3** (prototipo funcional) corresponde a las semanas 8 a 11 del Módulo III.

Fuentes originales: `d.pdf` (Hito 2) e `image.jpeg` (enunciado del Hito 3), ambos en la raíz del proyecto.

## Cómo usar esta skill
- Toda implementación debe ser **fiel al diseño del Hito 2**. Si algo del código se aparta de él, avísalo explícitamente.
- Si necesitas detalles (tablas, fórmulas, entradas/salidas, interfaces), lee `references/hito2-diseno.md`.
- Para los entregables y criterios del Hito 3, lee `references/hito3-requisitos.md`.
- Los informes se redactan en español formal y académico, con el mismo estilo del Hito 2 (LaTeX, tablas y figuras numeradas, referencias IEEE).

## Resumen del diseño (lo esencial)

**Modelo.** Paquete `q = (t, r)` (franja, sala); evento `e = (l, c, S)` (docente, clase, estudiantes); asignación `p = (q, e)`; horario `P = {(q, e)}`.
- Dominio de `t`: **60 franjas**, de lunes 7:00 a sábado 16:00.
- Dominio de `r`: los salones disponibles con su capacidad.
- Cada materia genera tantos eventos como **horas semanales** tenga.

**Cromosoma.** Es un vector de enteros con un gen por evento. Solo cambian `t` y `r`; `l`, `c` y `S` quedan fijos durante la búsqueda.

**Aptitud (minimizar).** `F(P) = Σ_i w_i · V_i(P)`, con `w_HC ≫ w_SC`.
- Restricciones duras (HC): conflictos de docente, conflictos de clase, capacidad de sala y disponibilidad docente.
- Restricciones blandas (SC): preferencias docentes, distribución de carga, separación entre eventos y conflictos de estudiantes.
- **Multi-profundidad:**
  - Superficial: cada evento por separado (disponibilidad, capacidad).
  - Medio: relaciones entre eventos del mismo docente, clase o sala (conflictos, carga, separación).
  - Profundo: asignación de estudiantes a secciones (conflictos de estudiantes).

**Reglas configurables** guardadas en MySQL, con los campos nombre, tipo (HC/SC), condición lógica, peso y estado (activa o inactiva). Cambiar reglas no debe requerir tocar el código del algoritmo.

**Pipeline evolutivo (es un AG, no una Evolution Strategy):**
`P0 aleatoria → Eval F → Torneo(τ) → Cruce uniforme por evento (pc) → Mutación por reasignación (pm) → Elitismo k → P_{t+1}`
- Torneo: se toman τ individuos al azar y gana el de menor `F`.
- Cruce uniforme **por evento**: por cada evento, una máscara elige de qué padre se hereda el paquete `(t, r)` completo. Nunca se mezcla la `t` de un padre con la `r` del otro.
- Mutación: con probabilidad `pm` por evento, se cambia `(t, r) → (t', r')`, `(t', r)` o `(t, r')`.
- Elitismo y reemplazo generacional: `E_t = Best_k(P_t)` y `P_{t+1} = E_t ∪ C_t`, donde `|C_t| = N − k`.
- Terminación: al llegar a `T_max` iteraciones o a un criterio de calidad.
- En cada iteración se guardan en MySQL los **k mejores**, con su iteración y su aptitud.

**Parámetros:** `T_max`, `k`, `N`, `τ`, `pc` y `pm`. Todos deben ser positivos y cumplir `k < N`.

**Arquitectura:** MVC con aplicación web (Vista + Controlador), MySQL (Modelo) y el motor de optimización. Tiene 5 componentes:
1. Repositorio de datos (MySQL).
2. Núcleo de cómputo (motor MDGA).
3. Subsistema explicativo: desglose de `F(P)` por regla, eventos que violan cada regla y comparación de los k mejores.
4. Pipelines de ingesta: CSV/XLSX de la coordinación, con validación de docentes existentes, capacidades y horas coherentes, y generación de los eventos.
5. Interfaz: vistas, dashboards y adaptadores de API REST/JSON.

**Secuencia:** usuario → web (`T_max`, k) → controlador carga datos y reglas de MySQL → motor ejecuta el bucle (evaluar, operadores, guardar k) → mejor horario → explicador (`V_i`, `w_i`) → visualización.

**Métricas (sección 11):**
- Calidad de la solución: `F`, `H(P)` (factible si `H = 0`), `S(P)`, `V_i` por regla, conflictos de estudiantes, ocupación de salas `(1/E)·Σ|S_e|/cap(r_e) ≤ 1` y desviación estándar de la carga diaria de cada docente.
- Desempeño del algoritmo: tasa de factibilidad `R_f = N_f/N_c`, `G_f` (generaciones hasta lograr factibilidad), `ΔF = (F0* − FT*)/F0*`, curva de convergencia, diversidad `D_t` (distancia de Hamming por paquete) y tiempo de ejecución.
- Calidad del sistema: cobertura explicativa cercana al 100 %, configurabilidad y trazabilidad.
- **Protocolo:** unas 30 corridas independientes por configuración, reportando media, desviación estándar y mejor resultado.

## Hito 3 (en curso)
Construir el prototipo funcional:
- Implementar los componentes del Hito 2 e integrar el razonamiento (reglas y AG), el conocimiento (MySQL y reglas) y el entorno (web/API).
- Conectar de forma funcional el motor de inferencia (evaluador de reglas) con la base de hechos (MySQL).
- **Alpha:** primera versión funcional, pensada para detectar problemas de arquitectura, integración o razonamiento.
- **Beta:** corrige lo encontrado en Alpha y debe ser integrada y estable.
- **Evaluación:** métricas cuantitativas justificadas con la literatura del Hito 1 (referencias [1] a [4] y [6], ITC 2019).

> No basta con que "funcione": hay que demostrar con evidencia experimental que se cumplen los objetivos y explicar las fortalezas y las limitaciones.
