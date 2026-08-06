import pandas as pd
import unicodedata
import us

# ----------------------------
# CARGA
# ----------------------------
df = pd.read_csv('data/ecommerce_orders_feb2026.csv')

# ----------------------------
# LIMPIEZA BÁSICA
# ----------------------------
df['order_date'] = pd.to_datetime(df['order_date'])
df['updated_date'] = pd.to_datetime(df['updated_date'])

df['discount'] = df['discount'].fillna(0)
df['tax'] = df['tax'].fillna(0)
df['shipping_cost'] = df['shipping_cost'].fillna(0)

df['payment_method'] = df['payment_method'].fillna('NO ESPECIFICADO').str.upper()

# ----------------------------
# NORMALIZACIÓN TEXTO
# ----------------------------
def normalizar_texto(texto):
    if pd.isna(texto):
        return "NO ESPECIFICADO"
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', str(texto))
        if unicodedata.category(c) != 'Mn'
    )
    return texto.strip().upper()

df['city'] = df['city'].apply(normalizar_texto)
df['state'] = df['state'].apply(normalizar_texto)
df['country'] = df['country'].apply(normalizar_texto)

# ----------------------------
# NORMALIZACIÓN ESTADOS
# ----------------------------
mapeo_unificado = {
    'COAHUILA DE ZARAGOZA': 'COAHUILA',
    'DISTRITO FEDERAL': 'CDMX',
    'CIUDAD DE MEXICO': 'CDMX',
    'DF': 'CDMX',
    'MEXICO': 'EDOMEX',
    'ESTADO DE MEXICO': 'EDOMEX',
    'MICHOACAN': 'MICHOACÁN',
    'YUCATAN': 'YUCATÁN',
    'NUEVO LEON': 'NUEVO LEÓN',
    'QUERETARO': 'QUERÉTARO',
    'VERACRUZ DE IGNACIO DE LA LLAVE': 'VERACRUZ'
}

df['state'] = df['state'].replace(mapeo_unificado)

def expandir_estado_us(valor):
    estado = us.states.lookup(valor)
    return estado.name.upper() if estado else valor

df['state'] = df['state'].apply(expandir_estado_us)

# ----------------------------
# 🔥 LIMPIEZA + IMPUTACIÓN DE MONEDA
# ----------------------------
df['currency'] = df['currency'].str.upper().str.strip()

def asignar_moneda(row):
    # Si la moneda está vacía, decidimos por el tipo de mercado
    if pd.isna(row['currency']) or row['currency'] == '':
        if row['country'] != 'MX': # Todo lo que no es MX (Global o Internacional)
            return 'USD'
        else:
            return 'MXN'
    return row['currency']

df['currency'] = df.apply(asignar_moneda, axis=1)

# ----------------------------
# 🔥 RELLENO DE UNIT_PRICE
# ----------------------------
mapa_estado_precio = df[df['unit_price'] > 0] \
    .groupby(['product_id', 'state'])['unit_price'] \
    .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.mean()) \
    .to_dict()

mapa_nacional_precio = df[df['unit_price'] > 0] \
    .groupby('product_id')['unit_price'] \
    .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.mean()) \
    .to_dict()

def rellenar_precio(row):
    # Si el precio original es nulo o cero...
    if pd.isna(row['unit_price']) or row['unit_price'] == 0:
        # 1. Buscamos por Estado
        precio_estado = mapa_estado_precio.get((row['product_id'], row['state']))
        
        if pd.notna(precio_estado):
            return precio_estado
        
        # 2. Si no hay por estado, buscamos Nacional. 
        # Agregamos ', 0' al final del .get() para que sea el valor por defecto
        return mapa_nacional_precio.get(row['product_id'], 0) 
    
    return row['unit_price']

# Aplicamos la función y aseguramos que no queden nulos "colados"
df['unit_price'] = df.apply(rellenar_precio, axis=1).fillna(0)

# ----------------------------
# 💱 CONVERSIÓN A MXN
# ----------------------------
cambio = 17.25

df['unit_price_mxn'] = df.apply(
    lambda x: x['unit_price'] * cambio if x['currency'] == 'USD' else x['unit_price'],
    axis=1
)

df['discount_mxn'] = df.apply(
    lambda x: x['discount'] * cambio if x['currency'] == 'USD' else x['discount'],
    axis=1
).fillna(0)

# ----------------------------
# 💥 REVENUE FINAL
# ----------------------------
def calcular_revenue(row):
    # 1. Regla de Cancelación
    if str(row['status']).strip().upper() == 'CANCELLED':
        return 0
    
    # 2. Regla de Precio Vacío
    if row['unit_price_mxn'] < 0.01:
        return 0
    
    # 3. MATEMÁTICA EN PESOS (Usando las nuevas columnas _mxn)
    # Sumamos impuestos y restamos descuentos y envíos
    return row['unit_price_mxn'] + row['tax'] - row['discount_mxn'] - row['shipping_cost']

# Aplicamos la función usando las columnas convertidas
df['revenue_mxn'] = df.apply(calcular_revenue, axis=1)

# ----------------------------
# FEATURES
# ----------------------------
def segmentar_mercado(pais):
    if pais == 'MX':
        return 'Nacional'
    elif pais == 'US':
        return 'Internacional'
    else:
        return 'Global'

df['market_type'] = df['country'].apply(segmentar_mercado)

df['lead_time_days'] = (df['updated_date'] - df['order_date']).dt.days
df['lead_time_days'] = df['lead_time_days'].apply(lambda x: x if x >= 0 else 0)

df['order_hour'] = df['order_date'].dt.hour
df['time_of_day'] = pd.cut(
    df['order_hour'],
    bins=[0, 12, 18, 24],
    labels=['Mañana', 'Tarde', 'Noche'],
    include_lowest=True
)

promedio_ventas = df['revenue_mxn'].mean()
df['order_value_segment'] = df['revenue_mxn'].apply(
    lambda x: 'Alto Valor' if x > promedio_ventas else 'Estándar'
)

#Nombre del nuevo archivo
final_file_name = 'data/ecommerce_orders_cleaned.xlsx'

# Selecciona solo las columnas que vas a usar para tus tablas dinámicas en Excel
columnas_finales = [
    'order_id', 'order_date', 'updated_date', 'time_of_day', 'status', 'channel', 'fulfillment', 
    'payment_method', 'shipping_tier', 'product_id', 'category', 'quantity', 'revenue_mxn', 'city', 
    'state', 'country', 'market_type', 'lead_time_days', 'order_value_segment'
]

df[columnas_finales].to_excel(final_file_name, index=False)
print(f"Archivo guardado como: {final_file_name}")



"""df_prod09 = df[df['product_id'] == 'PROD-45']

print(df_prod09[[
    'product_id',
    'state',
    'country',
    'currency',
    'unit_price',
    'unit_price_mxn',
    'quantity',
    'discount_mxn',
    'shipping_cost',
    'tax',
    'revenue_mxn'
]])"""