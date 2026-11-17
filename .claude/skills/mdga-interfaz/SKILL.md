---
name: mdga-interfaz
description: Diseño de la interfaz y de los módulos de comunicación del proyecto MDGA (horarios UTP) según las figuras 5, 6, 7 y 10 del Hito 2: aplicación web Flask (Vista + Controlador), vistas gráficas, dashboards de visualización, adaptadores de API REST/JSON, ingesta CSV/XLSX y su conexión con el motor MDGA, el subsistema explicativo y MySQL. Úsala siempre que el usuario pida crear o modificar pantallas, rutas Flask, plantillas, formularios, dashboards, endpoints de la API, importación/exportación de datos o la visualización de horarios del proyecto, aunque solo diga "la interfaz", "la web", "el front" o "la API".
---

# Interfaz del sistema MDGA (Flask)

Esta skill complementa a `mdga-horarios`, que contiene el modelo, el AG y las métricas; cárgala también cuando haga falta. Las figuras originales están en `assets/`:
- `fig5-arquitectura-13.png`: aplicación web ↔ MySQL ↔ motor.
- `fig6-componentes-15.png`: interfaz de usuario y módulos de comunicación.
- `fig7-secuencia-17.png` y `fig7-secuencia-18.png`: secuencia de una solicitud.
- `fig10-entorno-24.png`: interfaces con el entorno.

Ábrelas con Read si necesitas verlas.

**Entorno:** se usa `docker compose up -d` con tres servicios:
- `web`: Flask en :5000, con el código montado y recarga automática.
- `db`: MySQL 8.4 en :3306, con el esquema en `db/init.sql`.
- `adminer`: interfaz para la BD en :8080.

Las dependencias están en `requirements.txt`: Flask, Flask-SQLAlchemy, PyMySQL, numpy, openpyxl y gunicorn. Las credenciales están en `.env`, y la app recibe la conexión en `DATABASE_URL`. La app se crea con `app:create_app()` y tiene `/health`. Hay una alternativa local en `.venv`.

## Lo que dicen las figuras

**Fig. 6. Interfaz de usuario y módulos de comunicación.** Es un bloque con tres partes:
1. **Vistas gráficas**: registrar datos y reglas. Se conectan con el **Núcleo de cómputo (motor MDGA)**.
2. **Dashboards de visualización**: el horario y la evolución del algoritmo.
3. **Adaptadores de API**: comunicación con otras aplicaciones. Se conectan con el **Subsistema explicativo**.

Las demás relaciones de la figura: el núcleo envía "resultados" al subsistema explicativo; el núcleo se comunica con el **repositorio MySQL**; y los **pipelines de ingesta** (archivos de la coordinación UTP) cargan datos en MySQL.

**Fig. 5. Arquitectura.**
- La aplicación web (Vista + Controlador) se encarga del registro de datos, reglas y parámetros, y de la consulta de resultados.
- Envía "datos y reglas" a MySQL y recibe "resultados".
- MySQL hace la "carga" al motor y recibe del motor los "mejores k".
- La web inicia la optimización enviando las iteraciones máximas y k.

**Fig. 7. Secuencia.**
1. Usuario → Interfaz: solicitar generación.
2. Interfaz → Controlador: enviar parámetros (`T_max`, k).
3. Controlador → MySQL: cargar datos y reglas.
4. MySQL → Controlador: datos y reglas activas.
5. Controlador → Motor: iniciar optimización.
6. a 8. Bucle `t < T_max`: evaluar `F`, aplicar selección, cruce, mutación y elitismo, y guardar los k mejores.
9. Motor → Controlador: mejor horario y su aptitud.
10. a 13. Controlador → Explicativo: desglosar `F(P)`; devuelve `V_i` y `w_i` por regla.
14. Controlador → Interfaz: horario + explicación.
15. Interfaz → Usuario: visualización.

**Fig. 10 / Tabla 14. Entorno (red institucional TCP/IP).**
| Actor | Canal | Formato |
|---|---|---|
| Coordinación UTP | importación por los pipelines de ingesta | CSV, XLSX |
| Sistemas legados | adaptadores API REST | JSON |
| Usuarios (coordinación, docentes, estudiantes) | aplicación web | HTTPS desde el navegador |
| Sistemas externos | API / exportación | JSON, archivos |

## Mapa a Flask (estructura recomendada)

```
app/
  __init__.py          # create_app(), registro de blueprints
  models/              # Modelo: acceso a MySQL (docentes, salones, franjas, grupos, materias, reglas, corridas, resultados)
  controllers/         # Blueprints = Controlador (validan entradas e invocan modelo/motor)
    datos.py           #   CRUD de grupos, docentes, materias, salones
    reglas.py          #   CRUD de reglas
    optimizacion.py    #   parámetros + lanzar corrida
    resultados.py      #   horarios, explicación, dashboards
    ingesta.py         #   subir CSV/XLSX
    api.py             #   /api/v1/* (adaptadores REST/JSON)
  templates/           # Vista (Jinja2)
  static/
engine/                # Núcleo de cómputo MDGA (NumPy, sin Flask)
  evaluator.py         # reglas → F(P), V_i (superficial/medio/profundo)
  ga.py                # torneo, cruce uniforme por evento, mutación, elitismo k
explain/               # Subsistema explicativo
ingest/                # Pipelines de ingesta y validación
```

**Regla de diseño:** `engine/` no importa Flask. El controlador le pasa arrays de NumPy y reglas, y recibe los resultados. Así se mantienen la separación MVC y la "configurabilidad" de la métrica 11.3.

## Pantallas (Vistas gráficas y Dashboards)

| Vista | Ruta | Contenido (según las Tablas 12 y 13) |
|---|---|---|
| Inicio / panel | `/` | Estado de los datos cargados, última corrida y accesos rápidos |
| Grupos | `/grupos` | id único, materia y estudiantes |
| Docentes | `/docentes` | id y disponibilidad (cuadrícula de las 60 franjas) |
| Materias | `/materias` | código y horas semanales (entero > 0) |
| Salones | `/salones` | id y capacidad (entero > 0) |
| Franjas | `/franjas` | 60 franjas, de lunes 7:00 a sábado 16:00 (configuración) |
| Reglas | `/reglas` | nombre, tipo HC/SC, condición, peso y estado (activa o inactiva) |
| Importar | `/ingesta` | subir CSV/XLSX, ver el reporte de validación y confirmar la carga |
| Optimizar | `/optimizar` | `T_max`, k, N, τ, pc, pm (positivos y `k < N`); botón "Generar" |
| Resultados | `/corridas/<id>` | los mejores k con su iteración y `F(P)`, `H(P)` y `S(P)`, y la comparación entre ellos |
| Horario | `/corridas/<id>/horario/<n>?por=grupo\|docente\|salon` | cuadrícula día × franja, que se puede exportar |
| Explicación | `/corridas/<id>/horario/<n>/explicacion` | tabla de `V_i`, `w_i` y `w_i·V_i` por regla, con los eventos que la violan |
| Evolución | `/corridas/<id>/evolucion` | curva de la mejor aptitud por iteración y la diversidad `D_t` |

## Adaptadores de API (REST/JSON)
- `GET/POST /api/v1/{grupos,docentes,materias,salones,reglas}`
- `POST /api/v1/corridas`: recibe `{T_max, k, N, tau, pc, pm}` y responde `{id}`.
- `GET /api/v1/corridas/<id>`: estado y los mejores k.
- `GET /api/v1/corridas/<id>/historial`: mejor `F` en cada iteración.
- `GET /api/v1/horarios/<id>?por=grupo|docente|salon`
- `GET /api/v1/horarios/<id>/explicacion`
- `GET /api/v1/horarios/<id>/export?formato=csv|json`

Los errores se devuelven en JSON, con la forma `{"error": "...", "campo": "..."}` y el código 400 o 404.

## Criterios
- Validar en el controlador: identificadores únicos, horas y capacidades enteras positivas, `k < N`, y probabilidades en [0, 1].
- Una corrida larga no debe bloquear la petición: lánzala en un hilo o en segundo plano y consulta su estado por la API. El historial de los k mejores queda en la BD (trazabilidad).
- El dashboard de evolución y la vista de explicación sirven como evidencia para el Hito 3 (cobertura explicativa y curvas de convergencia).
- Para el estilo visual, si el usuario no indica otro, puede usarse la skill `mono-bento-ui`.
