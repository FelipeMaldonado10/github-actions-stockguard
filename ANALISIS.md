# Análisis — Introducción práctica a GitHub Actions

Taller autónomo sobre el caso StockGuard. Todas las respuestas usan datos de las
ejecuciones reales de este repositorio, no definiciones copiadas.

## Evidencias de las ejecuciones

| # | Evento | Commit | Ejecución | Resultado |
| --- | --- | --- | --- | --- |
| 1 | `push` | `971c9fd` estructura inicial | [40730295320](https://github.com/FelipeMaldonado10/github-actions-stockguard/actions/runs/40730295320) | success |
| 2 | `push` | `97f2912` fallo intencional | [40730927193](https://github.com/FelipeMaldonado10/github-actions-stockguard/actions/runs/40730927193) | failure |
| 3 | `push` | `eaa12ef` prueba restaurada | [40731161082](https://github.com/FelipeMaldonado10/github-actions-stockguard/actions/runs/40731161082) | success |
| 4 | `pull_request` | `0b89d64` regla de sobrestock — [PR #1](https://github.com/FelipeMaldonado10/github-actions-stockguard/pull/1) | [40731372782](https://github.com/FelipeMaldonado10/github-actions-stockguard/actions/runs/40731372782) | success |
| 5 | `workflow_dispatch` | `eaa12ef` sobre `main` | [40731494610](https://github.com/FelipeMaldonado10/github-actions-stockguard/actions/runs/40731494610) | success |

La ejecución manual figura como `CI ejecutado por FelipeMaldonado10`, tanto en
`run-name` como en el actor registrado por GitHub.

## 1. Una ejecución exitosa y una fallida: qué las produjo y qué step decidió

La exitosa (`40730295320`) la produjo el commit inicial `971c9fd`, que subió la regla
`clasificar_stock` con sus 5 pruebas y el workflow. La fallida (`40730927193`) la
produjo `97f2912`, un commit de una sola línea que cambió la expectativa de
`test_stock_critico` de `"CRITICO"` a `"NORMAL"`.

En las dos, el step que decidió el resultado fue el **6, "Ejecutar pruebas"**. Los
steps 2 a 5 (descarga, Python, dependencias, `compileall`) terminaron en `success`
también en la ejecución fallida: la sintaxis era correcta y las dependencias estaban
bien. Lo único que distinguió a las dos ejecuciones fue el resultado de `pytest -v`.

## 2. Por qué pytest local no reemplaza pytest en GitHub Actions

Porque no prueban el mismo entorno, y en este taller la diferencia no es teórica.

Mi entorno local corrió las pruebas con **Python 3.14**, que es el intérprete del
`venv` que tenía a mano; el workflow fija **Python 3.12** en un `ubuntu-latest`. Un
comportamiento que cambió entre versiones pasaría en un lado y no en el otro.

Además, la ejecución local arranca con un directorio de trabajo donde ya están
instaladas las dependencias, existen archivos sin commitear y hay cachés de
`__pycache__` y `.pytest_cache`. El runner arranca de un clon limpio: si una prueba
depende de un archivo que nunca se commiteó, localmente pasa y en Actions falla. Es
el mismo motivo por el que el `pytest.ini` de este repositorio tuvo que estar en el
commit inicial y no después.

Local responde "funciona en mi máquina". Actions responde "funciona en el repositorio".

## 3. Qué riesgo tiene mergear sin esperar los checks del PR

El riesgo es que una regla de negocio rota llegue a `main` con apariencia de código
revisado.

En este taller el commit `97f2912` no rompía nada visible: la aplicación seguía
importando, `compileall` pasaba y solo una prueba fallaba. Si eso hubiera entrado a
`main` por merge directo, `clasificar_stock(7, 20)` habría devuelto `NORMAL` para un
producto con 7 unidades y mínimo 20, es decir **un producto en nivel crítico no habría
disparado la alerta de reposición**. Nadie se entera hasta que falta el producto en la
góndola.

Un check en el PR convierte ese error en un merge bloqueado, y el costo de arreglarlo
es un commit en la rama, no un incidente en producción.

## 4. La línea esencial del error

```
E       assert 'CRITICO' == 'NORMAL'
```

Lo que permitió diagnosticar fue el orden de la comparación. La función devolvió
`'CRITICO'`, que es lo correcto según la regla: el error no estaba en
`src/inventario.py`, estaba en la expectativa de la prueba. Sin esa línea uno tiende a
sospechar de la lógica de negocio; con esa línea el diagnóstico es inmediato y el
arreglo también.

El encabezado del fallo confirma dónde buscar:
`tests/test_inventario.py::test_stock_critico FAILED` — módulo y prueba exactos, sin
tener que leer el log completo.

## 5. Diferencia entre un step con `uses:` y uno con `run:`

Un step con `uses:` delega en una **action publicada**: no ejecuta comandos propios,
invoca un paquete versionado que GitHub descarga y corre. Un step con `run:` ejecuta
**comandos de shell** en el runner, con lo que ya está instalado.

En este workflow, los steps 2 y 3 son `uses:` (`actions/checkout@v6` y
`actions/setup-python@v5`): traen el repositorio y un intérprete de Python que el
runner no tiene en la versión pedida. Los steps 4, 5 y 6 son `run:`: `pip install`,
`python -m compileall`, `pytest -v`. Son comandos que escribiría a mano en mi máquina.

La consecuencia práctica: los `uses:` se actualizan subiendo la versión de la action y
leyendo su changelog; los `run:` se actualizan cambiando el comando, y su
comportamiento depende del shell y del sistema operativo del runner.

## 6. Qué aporta `${{ github.actor }}` en `run-name`

`github.actor` es el login de quien disparó la ejecución. Ponerlo en `run-name` hace
que la lista de ejecuciones diga **quién** hizo cada una, sin abrir el run.

En este repositorio el nombre de las cinco ejecuciones es `CI ejecutado por
FelipeMaldonado10`. En un equipo eso sirve para dos cosas concretas: ubicar rápido al
autor de un cambio cuando algo falla, y dejar registro de participación individual en
una ejecución manual.

Un detalle que conviene saber: el actor no siempre es quien escribió el código. En un
`pull_request` es el autor del PR, pero en un `workflow_dispatch` es quien apretó "Run
workflow". Para atribuir código hay que mirar el commit; para atribuir la ejecución,
el actor.

## 7. Si el workflow pasa pero la aplicación falla con Docker, ¿Actions no sirve?

No. Significa que el workflow verifica **otra cosa**, y hay que leer qué declara.

Este CI verifica tres cosas: que las dependencias se instalan desde `requirements.txt`,
que el código compila (`compileall src tests`) y que las 8 pruebas unitarias pasan. Eso
es todo. No verifica que Kafka levante, que `docker compose up` funcione, que las
imágenes se construyan ni que el pipeline procese datos reales.

De hecho, mi CI está en verde con un `docker-compose.yml` inexistente en este
repositorio: nunca lo mira. Un check verde es una afirmación acotada, y el error es leer
"CI verde" como "la aplicación funciona". Lo que corresponde es que el workflow pruebe
lo que se pueda probar en segundos, y que el resto tenga sus propias validaciones
(fuera de CI, o en un job manual que no corra en cada push).

## 8. Tres checks para mi variante de RapidGo 360

| Check | Error concreto que evita |
| --- | --- |
| `python -m compileall producer spark scripts` | Que un archivo con error de sintaxis entre a `main` y reviente recién cuando alguien levanta el job. Ya pasó en este proyecto con un script de creación de topics. |
| `pytest` sobre las reglas de alerta y el contrato del evento | Que un umbral de A1 o A2 se cambie sin querer y la alerta deje de dispararse, o que un evento que no cumple el contrato se cuele hasta el lake. |
| `docker compose config --quiet` | Un `docker-compose.yml` inválido (servicio mal indentado, variable sin definir, volumen mal apuntado) que impide levantar Kafka y Spark. Valida en un segundo, sin levantar nada. |

## 9. Cuál de esos checks va primero y por qué

El de `pytest` sobre las reglas de negocio, porque es el único de los tres que detecta
un error **silencioso**.

`compileall` y `docker compose config` detectan cosas que no arrancan, y eso se nota
solo: si el archivo no compila o el compose es inválido, nadie llega lejos. Un umbral
de alerta mal puesto, en cambio, no rompe nada: el pipeline corre, los datos se
escriben, y la alerta simplemente nunca dispara. Ese es el error caro, y es el que solo
una prueba de la regla puede atrapar.

El de `compileall` va segundo porque es el más barato y corta el workflow antes de
gastar tiempo instalando dependencias o corriendo la suite.

## 10. Qué prueba sería demasiado costosa o frágil en cada push

Levantar el stack completo —Kafka, Spark y Airflow en contenedores— en cada push. Es
costoso (minutos de runner y de arranque por cada commit), frágil (depende de imágenes,
puertos libres, memoria del runner y tiempos de espera que varían) y, sobre todo,
**redundante**: el 80% de lo que rompe un commit se detecta con `pytest` en segundos.

Tampoco corresponde ejecutar el producer durante minutos para generar datos reales en
cada push: un test que espera datos que llegan por red no es determinista.

Cómo lo validaría en su lugar, en tres niveles:

1. **En cada push**, la regla aislada: pruebas que reciben eventos congelados (un
   archivo de ejemplo versionado) y comprueban el resultado sin broker.
2. **Antes del merge de cambios grandes**, una corrida manual con `workflow_dispatch`
   que levante el compose y ejecute un humo de extremo a extremo. La decisión de
   correrla es humana, y queda registrada con el actor y el commit.
3. **Localmente**, el pipeline completo con datos reales, como evidencia del equipo.
   Eso no reemplaza al CI: lo complementa.

## Hallazgo: la guía, ejecutada al pie de la letra, falla en el primer push

Con el layout que la propia guía propone (`src/` y `tests/` en la raíz, con
`src/__init__.py`) y el step `pytest -v` tal cual, la suite **no importa `src`**:

```
tests\test_inventario.py:3: in <module>
    from src.inventario import clasificar_stock
E   ModuleNotFoundError: No module named 'src'
```

El paso 19 de la guía atribuye ese error a que falte `src/__init__.py` o a no ejecutar
pytest desde la raíz. En mi caso el `__init__.py` existía y pytest corría desde la raíz,
así que ese diagnóstico no alcanza. La causa real es otra: el script `pytest`, en su
modo de importación por defecto, agrega a `sys.path` el directorio de cada módulo de
prueba —`tests/`— y **no** la raíz del repositorio. Por eso `python -m pytest` sí
funciona: el `-m` agrega el directorio actual a `sys.path`.

Lo resolví sin tocar el `ci.yml` de la guía, agregando un `pytest.ini` en la raíz:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Queda como defecto real de la guía: el workflow que propone no funciona con la
estructura que propone, y el troubleshooting apunta a otro lado. Con `python -m pytest`
en el step, o con ese `pytest.ini`, se corrige.
