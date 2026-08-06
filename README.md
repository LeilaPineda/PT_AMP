# 🛒 Pipeline Integral de Limpieza, Automatización y Enriquecimiento de Datos con Python y Pandas

Repositorio enfocado en demostrar habilidades prácticas de **Ciencia de Datos, Ingeniería de Datos y Automatización** utilizando Python y Pandas, resolviendo tanto la limpieza fundamental de bases de datos como retos complejos de transformación en el comercio electrónico.

---

## 🎯 Objetivo Principal
El objetivo de este proyecto es transformar conjuntos de datos crudos, ruidosos y desestructurados en insumos limpios, confiables y de alto valor comercial, aplicando buenas prácticas de procesamiento en Python.

Los principales retos resueltos en este pipeline incluyen:
1. **Deduplicación de registros:** Identificación y eliminación de filas duplicadas idénticas.
2. **Normalización de textos y geografía:** Estandarización de mayúsculas, eliminación de acentos mediante `unicodedata` y unificación de estados (México y EE. UU.).
3. **Manejo de valores nulos:** Imputación inteligente y asignación de etiquetas de respaldo (*fallback*) para registros vacíos.
4. **Tratamiento de fechas heterogéneas:** Normalización y conversión de formatos de fecha mixtos o irregulares.
5. **Limpieza de variables numéricas y monetarias:** Transformación de campos con texto erróneo o formato inválido a valores numéricos estándar.
6. **Imputación jerárquica de precios:** Recuperación de precios faltantes usando la **moda** (`x.mode()`) para reflejar el precio de lista real frente al promedio.
7. **Unificación financiera y conversión de divisas:** Homologación de monedas internacionales (USD a MXN) con un tipo de cambio fijo y cálculo de ingresos netos (*Revenue*).
8. **Ingeniería de Características (Feature Engineering):** Creación de nuevas columnas y métricas estratégicas para análisis de negocio.

---

## 🛠️ Tecnologías y Librerías Utilizadas
* **Python**: Lenguaje principal de programación.
* **Pandas**: Manipulación, limpieza, filtrado, agrupación y transformación de estructuras tabulares.
* **Unicodedata**: Normalización de caracteres y eliminación de diacríticos.
* **US (Biblioteca de Python)**: Estandarización y validación de nombres de estados de EE. UU.
* **OpenPyXL**: Lectura y exportación de archivos en formato Excel (`.xlsx`).

---

## 🔄 Proceso de Elaboración y Pasos Técnicos

### 1. Carga e Inspección Inicial
Se realiza la lectura de las fuentes de datos mediante Pandas (`pd.read_excel` / `pd.read_csv`), seguida de una revisión exploratoria para detectar anomalías, tipos de datos incorrectos, filas duplicadas y valores nulos críticos distribuidos en el dataset.

### 2. Deduplicación y Limpieza de Filas
Se detectan y eliminan registros duplicados exactos para evitar sesgos o distorsiones en futuras métricas y análisis estadísticos.

### 3. Normalización de Textos, Nombres y Datos Geográficos
* Se eliminan espacios en blanco sobrantes (`.strip()`), se estandarizan mayúsculas/minúsculas y se aplica formato de nombre propio o unificación de textos con `unicodedata`.
* Se unifican variantes geográficas (por ejemplo, mapeando "DISTRITO FEDERAL" o "DF" a "CDMX") y se validan estados de EE. UU. con la librería `us`.
* Se asignan etiquetas por defecto (ej. *"Sin Nombre"*) a aquellos registros críticos que carecen de información.

### 4. Tratamiento de Fechas Heterogéneas
Se procesan columnas de fecha que presentan múltiples formatos de entrada, unificándolas bajo un estándar temporal coherente (`pd.to_datetime`).

### 5. Limpieza de Campos Numéricos y Monetarios
Se tratan los valores erróneos, cadenas de texto inválidas (como *"no disponible"*) o errores de captura, transformándolos a tipos de datos numéricos limpios (`float` / `int`).

### 6. Imputación Inteligente de Precios (`unit_price`)
* **Asignación de Divisa:** Se implementó un algoritmo condicional para detectar registros con moneda vacía, asignando `USD` a transacciones internacionales y `MXN` a las locales.
* **Recuperación con Moda vs. Promedio:** 
  > *Decisión técnica:* Se priorizó el uso de la **moda** (`x.mode()`) en lugar del promedio. En e-commerce, el promedio puede distorsionarse por centavos o variaciones menores, mientras que la moda refleja con exactitud el **precio de lista real** del producto. La búsqueda se estructuró de forma jerárquica: primero por `product_id` y `state`, y como respaldo, la moda nacional del producto.

---

## 💡 Columnas Agregadas y Lógica de Negocio (Feature Engineering)

Para dotar al dataset de inteligencia comercial y facilitar la creación de tableros (en Power BI o Excel), se calcularon y agregaron las siguientes columnas clave:

* **`currency` (Imputada):** Se rellenaron los vacíos detectando automáticamente el mercado de origen para evitar errores al calcular ingresos.
* **`unit_price_mxn` y `discount_mxn`:** 
  * *¿Por qué se agregaron?* Para poder sumar y analizar ingresos de forma global, era obligatorio estandarizar todas las divisas a una sola moneda. Se aplicó un factor de conversión de tipo de cambio fijo (`17.25`) exclusivamente a los registros en Dólares (`USD`), manteniendo los pesos intactos.
* **`revenue_mxn` (Ingreso Neto):**
  * *¿Por qué se creó?* Representa la ganancia real de la transacción aplicando reglas de negocio estrictas:
    1. Si el pedido tiene un estatus de `CANCELLED`, el ingreso se anula automáticamente (`0`).
    2. Se filtran precios inválidos o menores a 0.01.
    3. Se calcula matemáticamente sumando el precio en MXN más los impuestos, restando los descuentos ya convertidos y restando los costos de envío.
* **`market_type`:** Segmentación del mercado en *Nacional*, *Internacional* o *Global* basándose en el país de origen.
* **`lead_time_days`:** Mide los días transcurridos entre la creación de la orden (`order_date`) y su actualización/cierre (`updated_date`) para evaluar eficiencia logística.
* **`time_of_day`:** Categorización horaria de la compra (*Mañana*, *Tarde*, *Noche*) mediante intervalos (`pd.cut`).
* **`order_value_segment`:** Clasificación automática de cada pedido en *"Alto Valor"* o *"Estándar"* al compararlo contra la media general de ingresos.

---

## 📊 Resultados y Exportación
El script procesa toda la lógica anterior y genera archivos finales optimizados, limpios y enriquecidos listos para ser conectados a herramientas de Business Intelligence, bases de datos o dashboards analíticos.

```python


# Ejemplo de transformación y limpieza aplicada con Pandas
import pandas as pd

# Carga de datos sucios
df = pd.read_csv('data/ecommerce_orders_feb2026.csv')

# Eliminación de duplicados y limpieza básica de espacios
df = df.drop_duplicates()
df['Nombre'] = df['Nombre'].str.strip().str.title().fillna('Sin Nombre')

# Fragmento clave: Conversión de moneda y cálculo de Revenue neto
df['unit_price_mxn'] = df.apply(
    lambda x: x['unit_price'] * cambio if x['currency'] == 'USD' else x['unit_price'],
    axis=1
)

print("Datos limpios y listos para exportar.")

