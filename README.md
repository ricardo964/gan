# MDGA: Programación de horarios universitarios (UTP)

Algoritmo genético multi-profundidad (MDGA) para generar horarios universitarios. Es el proyecto de
la FISC de la Universidad Tecnológica de Panamá: el Hito 2 es el diseño (`d.pdf`) y el Hito 3 es el
prototipo funcional.

## Puesta en marcha

```bash
cp .env.example .env
docker compose up -d --build
```

| Servicio | URL |
|---|---|
| Aplicación web | http://localhost:5000 |
| API REST | http://localhost:5000/api/v1/estado |
| Adminer (BD) | http://localhost:8080 (servidor `db`, usuario `mdga`) |

Flujo:
1. **Importar** `datos/ejemplo_utp.xlsx` (o los archivos de la coordinación).
2. Revisar las **Reglas**.
3. Ir a **Optimizar**.
4. Consultar **Resultados**: horario, explicación y evolución.

Si cambia `db/init.sql`, recree la base con `docker compose down -v && docker compose up -d`.
Esto borra todos los datos.

## Estructura

```
engine/      Núcleo de cómputo MDGA (NumPy, sin Flask ni BD)
  problem.py    modelo q=(t,r), e=(l,c,S); cromosoma entero (E, 2)
  rules.py      catálogo de condiciones (motor de inferencia)
  fitness.py    F = Σ wᵢVᵢ, H, S y niveles superficial/medio/profundo
  operators.py  torneo, cruce uniforme por evento, mutación, elitismo, D_t
  ga.py         pipeline evolutivo y criterios de parada
  synthetic.py  instancias sintéticas tipo UTP
explain/     Subsistema explicativo (desglose de F por regla)
ingest/      Ingesta y validación de CSV/XLSX
app/         Flask (MVC): models/ (MySQL), controllers/ (web y API), templates/
db/init.sql  Esquema y datos semilla (60 franjas, 9 reglas)
scripts/     generar_datos.py, experimento.py
tests/       Pruebas unitarias (pytest)
docs/        Informes (alpha.md)
```

## Desarrollo local

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/experimento.py --corridas 10
```

## API (resumen)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/{salones,docentes,materias,grupos,franjas}` | Datos académicos |
| GET, POST / PATCH | `/api/v1/reglas`, `/api/v1/reglas/<id>` | Reglas |
| POST | `/api/v1/corridas` | Inicia una corrida: `{t_max, k, n, tau, pc, pm, seed}` y responde 202 |
| GET | `/api/v1/corridas/<id>` | Estado, métricas y los k mejores |
| GET | `/api/v1/corridas/<id>/historial` | Mejor F, H y D_t por iteración |
| POST | `/api/v1/corridas/<id>/cancelar` | Cancela la corrida |
| GET | `/api/v1/horarios/<id>?por=grupo&valor=G001` | Asignaciones |
| GET | `/api/v1/horarios/<id>/explicacion` | Vᵢ, wᵢ, eventos y cobertura |

Estado: **Prototipo Alpha**. Ver [docs/alpha.md](docs/alpha.md).
