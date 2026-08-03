"""
Generador de dataset LIMPIO (ground truth) para proyecto de portfolio
Cadena de supermercados - 20 tiendas, 200 empleados, 90 productos
Periodo: 3 años

Orden de generacion respeta integridad referencial:
dim_tienda -> dim_proveedor -> dim_producto -> dim_empleado -> dim_cliente
-> fact_compra -> fact_linea_compra -> fact_venta -> fact_linea_venta
"""
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker("es_ES")
Faker.seed(42)
random.seed(42)
np.random.seed(42)

FECHA_INICIO = datetime(2023, 1, 1)
FECHA_FIN = datetime(2026, 1, 1)  # 3 anios de historico

N_TIENDAS = 20
N_PROVEEDORES = 15
N_PRODUCTOS = 90
N_EMPLEADOS = 200
N_CLIENTES = 3000
N_COMPRAS = 4000          # cabeceras -> ~5 lineas cada una = 20k lineas_compra
N_VENTAS = 77000          # cabeceras -> ~6.5 lineas cada una = ~500k lineas_venta

# ---------------------------------------------------------------
# 1. DIM_TIENDA
# ---------------------------------------------------------------
ciudades_es = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Zaragoza",
               "Malaga", "Murcia", "Bilbao", "Alicante", "Cordoba",
               "Valladolid", "Vigo", "Gijon", "Granada", "Vitoria",
               "La Coruna", "Elche", "Oviedo", "Badajoz", "Cartagena"]

dim_tienda = []
for i in range(1, N_TIENDAS + 1):
    ciudad = ciudades_es[i - 1]
    dim_tienda.append({
        "tienda_id": i,
        "nombre": f"Super {ciudad} {i}",
        "ciudad": ciudad,
        "region": fake.state(),
        "fecha_apertura": fake.date_between(datetime(2005, 1, 1), datetime(2022, 12, 31)),
        "m2": random.randint(300, 2500)
    })
df_tienda = pd.DataFrame(dim_tienda)

# ---------------------------------------------------------------
# 2. DIM_PROVEEDOR
# ---------------------------------------------------------------
paises = ["Espana", "Francia", "Italia", "Alemania", "Marruecos", "Portugal"]
sectores = ["Tecnologia", "Electronica", "Textil", "Alimentacion", "Papeleria",
            "Bebidas", "Limpieza", "Congelados"]

dim_proveedor = []
for i in range(1, N_PROVEEDORES + 1):
    dim_proveedor.append({
        "proveedor_id": i,
        "empresa": fake.company(),
        "contacto": fake.name(),
        "email": fake.company_email(),
        "telefono": fake.phone_number(),
        "pais": random.choice(paises),
        "fecha_alta": fake.date_between(datetime(2010, 1, 1), datetime(2023, 1, 1)),
        "sector": random.choice(sectores)
    })
df_proveedor = pd.DataFrame(dim_proveedor)

# ---------------------------------------------------------------
# 3. DIM_PRODUCTO
# ---------------------------------------------------------------
categorias = {
    "Alimentacion": ["Lacteos", "Panaderia", "Conservas", "Snacks", "Cereales"],
    "Bebidas": ["Refrescos", "Zumos", "Agua", "Alcohol"],
    "Congelados": ["Verduras", "Pescado", "Precocinados"],
    "Limpieza": ["Hogar", "Lavanderia", "Higiene"],
    "Frescos": ["Carniceria", "Fruteria", "Charcuteria"],
    "Bazar": ["Papeleria", "Electronica", "Textil"]
}
nombres_producto = [fake.unique.word().capitalize() for _ in range(N_PRODUCTOS)]

dim_producto = []
for i in range(1, N_PRODUCTOS + 1):
    categoria = random.choice(list(categorias.keys()))
    subcategoria = random.choice(categorias[categoria])
    dim_producto.append({
        "producto_id": i,
        "nombre": f"{nombres_producto[i-1]} {subcategoria}",
        "categoria": categoria,
        "subcategoria": subcategoria,
        "proveedor_id": random.randint(1, N_PROVEEDORES),
        "unidad_medida": random.choice(["ud", "kg", "l", "pack"])
    })
df_producto = pd.DataFrame(dim_producto)

# ---------------------------------------------------------------
# 4. DIM_EMPLEADO
# ---------------------------------------------------------------
puestos = ["Cajero", "Reponedor", "Encargado", "Carnicero", "Panadero", "Seguridad"]

dim_empleado = []
for i in range(1, N_EMPLEADOS + 1):
    dim_empleado.append({
        "empleado_id": i,
        "nombre": fake.first_name(),
        "apellido": fake.last_name(),
        "tienda_id": random.randint(1, N_TIENDAS),
        "puesto": random.choice(puestos),
        "fecha_contratacion": fake.date_between(datetime(2015, 1, 1), datetime(2025, 12, 31)),
        "salario": round(random.uniform(1200, 2800), 2)
    })
df_empleado = pd.DataFrame(dim_empleado)

# ---------------------------------------------------------------
# 5. DIM_CLIENTE  (id 0 = cliente no identificado / "unknown member")
# ---------------------------------------------------------------
dim_cliente = [{
    "cliente_id": 0,
    "nombre": "NO IDENTIFICADO",
    "email": None,
    "fecha_alta": None,
    "ciudad": None
}]
for i in range(1, N_CLIENTES + 1):
    dim_cliente.append({
        "cliente_id": i,
        "nombre": fake.name(),
        "email": fake.email(),
        "fecha_alta": fake.date_between(FECHA_INICIO, FECHA_FIN),
        "ciudad": random.choice(ciudades_es)
    })
df_cliente = pd.DataFrame(dim_cliente)

# ---------------------------------------------------------------
# helper: fecha aleatoria en rango
# ---------------------------------------------------------------
def fecha_random(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

# ---------------------------------------------------------------
# 6-7. FACT_COMPRA + FACT_LINEA_COMPRA
# ---------------------------------------------------------------
fact_compra = []
fact_linea_compra = []
linea_compra_id = 1

for compra_id in range(1, N_COMPRAS + 1):
    tienda_id = random.randint(1, N_TIENDAS)
    proveedor_id = random.randint(1, N_PROVEEDORES)
    fecha = fecha_random(FECHA_INICIO, FECHA_FIN)

    n_lineas = random.randint(3, 8)
    total_compra = 0.0
    for _ in range(n_lineas):
        producto_id = random.randint(1, N_PRODUCTOS)
        cantidad = random.randint(10, 200)
        coste_unitario = round(random.uniform(0.5, 40), 2)
        total_linea = round(cantidad * coste_unitario, 2)
        total_compra += total_linea

        fact_linea_compra.append({
            "linea_compra_id": linea_compra_id,
            "compra_id": compra_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "coste_unitario": coste_unitario
        })
        linea_compra_id += 1

    fact_compra.append({
        "compra_id": compra_id,
        "fecha": fecha,
        "tienda_id": tienda_id,
        "proveedor_id": proveedor_id,
        "total": round(total_compra, 2)
    })

df_compra = pd.DataFrame(fact_compra)
df_linea_compra = pd.DataFrame(fact_linea_compra)

# ---------------------------------------------------------------
# 8-9. FACT_VENTA + FACT_LINEA_VENTA
# ---------------------------------------------------------------
metodos_pago = ["Tarjeta", "Efectivo", "Bizum", "Otros"]

fact_venta = []
fact_linea_venta = []
linea_venta_id = 1

for venta_id in range(1, N_VENTAS + 1):
    tienda_id = random.randint(1, N_TIENDAS)
    empleado_id = random.randint(1, N_EMPLEADOS)
    # 70% de ventas con cliente identificado, 30% sin identificar (id 0)
    cliente_id = random.randint(1, N_CLIENTES) if random.random() < 0.7 else 0
    fecha = fecha_random(FECHA_INICIO, FECHA_FIN)
    metodo_pago = random.choice(metodos_pago)

    n_lineas = random.randint(1, 12)
    total_venta = 0.0
    for _ in range(n_lineas):
        producto_id = random.randint(1, N_PRODUCTOS)
        cantidad = random.randint(1, 10)
        precio_unitario = round(random.uniform(0.5, 60), 2)
        descuento = round(random.choice([0, 0, 0, 0.1, 0.2]) * precio_unitario * cantidad, 2)
        total_linea = round(precio_unitario * cantidad - descuento, 2)
        total_venta += total_linea

        fact_linea_venta.append({
            "linea_venta_id": linea_venta_id,
            "venta_id": venta_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "descuento": descuento
        })
        linea_venta_id += 1

    fact_venta.append({
        "venta_id": venta_id,
        "fecha": fecha,
        "tienda_id": tienda_id,
        "empleado_id": empleado_id,
        "cliente_id": cliente_id,
        "metodo_pago": metodo_pago,
        "total": round(total_venta, 2)
    })

df_venta = pd.DataFrame(fact_venta)
df_linea_venta = pd.DataFrame(fact_linea_venta)

# ---------------------------------------------------------------
# GUARDAR TODO
# ---------------------------------------------------------------
OUT = "/home/claude/clean"
df_tienda.to_csv(f"{OUT}/dim_tienda.csv", index=False)
df_proveedor.to_csv(f"{OUT}/dim_proveedor.csv", index=False)
df_producto.to_csv(f"{OUT}/dim_producto.csv", index=False)
df_empleado.to_csv(f"{OUT}/dim_empleado.csv", index=False)
df_cliente.to_csv(f"{OUT}/dim_cliente.csv", index=False)
df_compra.to_csv(f"{OUT}/fact_compra.csv", index=False)
df_linea_compra.to_csv(f"{OUT}/fact_linea_compra.csv", index=False)
df_venta.to_csv(f"{OUT}/fact_venta.csv", index=False)
df_linea_venta.to_csv(f"{OUT}/fact_linea_venta.csv", index=False)

print("Filas generadas:")
print(f"  dim_tienda:        {len(df_tienda)}")
print(f"  dim_proveedor:     {len(df_proveedor)}")
print(f"  dim_producto:      {len(df_producto)}")
print(f"  dim_empleado:      {len(df_empleado)}")
print(f"  dim_cliente:       {len(df_cliente)}")
print(f"  fact_compra:       {len(df_compra)}")
print(f"  fact_linea_compra: {len(df_linea_compra)}")
print(f"  fact_venta:        {len(df_venta)}")
print(f"  fact_linea_venta:  {len(df_linea_venta)}")
