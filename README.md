# StockGuard — práctica de GitHub Actions

Taller autónomo de la guía *Introducción práctica a GitHub Actions* (Big Data,
Ingeniería de Sistemas y Computación), actividad preparatoria del proyecto final
RapidGo 360.

Este repositorio **no es RapidGo**: es un caso de juguete para aprender el mecanismo
de Actions, provocar una falla a propósito y corregirla.

## Regla de negocio

`clasificar_stock(stock_actual, stock_minimo)` devuelve el nivel de riesgo del
inventario de un producto:

| Condición | Resultado |
| --- | --- |
| `stock_actual == 0` | `AGOTADO` |
| `stock_actual <= stock_minimo * 0.5` | `CRITICO` |
| `stock_actual <= stock_minimo` | `BAJO` |
| cualquier otro caso | `NORMAL` |

`stock_actual` negativo o `stock_minimo <= 0` son entradas inválidas y lanzan
`ValueError`.

### Regla de sobrestock

`detectar_sobrestock(stock_actual, stock_minimo)` devuelve `True` cuando el stock
supera tres veces el mínimo requerido, es decir cuando el capital inmovilizado en
inventario es excesivo. El límite es estricto: con mínimo 20, un stock de 60 todavía
es normal y 61 ya es sobrestock.

Ejemplo: con mínimo 20 y 7 unidades, el resultado es `CRITICO`, porque 7 es menor o
igual a la mitad de 20 (10).

## Cómo correrlo

```bash
python -m pip install -r requirements.txt
pytest -v
```

## Qué automatiza el workflow

`.github/workflows/ci.yml` se dispara con `push` a `main`, con un Pull Request hacia
`main` y de forma manual con `workflow_dispatch`. En un runner `ubuntu-latest`:

1. descarga el repositorio,
2. instala Python 3.12,
3. instala las dependencias,
4. valida sintaxis con `python -m compileall src tests`,
5. ejecuta las pruebas con `pytest -v`.

## Evidencias

Las ejecuciones y el análisis están en [`ANALISIS.md`](ANALISIS.md).
