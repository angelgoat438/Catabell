"""
Inyector de suciedad CONTROLADA sobre el dataset limpio (ground truth).
Cada anomalia queda registrada en dirty/audit_log.csv para poder
validar despues el proceso de limpieza en Silver.
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime

random.seed(7)
np.random.seed(7)

CLEAN = "/home/claude/clean"
DIRTY = "/home/claude/dirty"

audit_log = []  # (tabla, columna, tipo_problema, n_filas_afectadas, detalle)

def log(tabla, columna, tipo, n, detalle=""):
    audit_log.append({"tabla": tabla, "columna": columna, "tipo_problema": tipo,
                       "filas_afectadas": n, "detalle": detalle})

# =================================================================
# DIM_EMPLEADO: nulos en fecha_contratacion, texto con espacios/mayus
# =================================================================
df = pd.read_csv(f"{CLEAN}/dim_empleado.csv")

# nulos en salario (dato sensible que a veces no se registra)
idx = df.sample(frac=0.03, random_state=1).index
df.loc[idx, "salario"] = np.nan
log("dim_empleado", "salario", "nulos", len(idx))

# inconsistencia de texto en puesto: mayus/minus/espacios random
idx = df.sample(frac=0.15, random_state=2).index
def ensuciar_texto(v):
    opciones = [v.upper(), v.lower(), f" {v} ", v.replace("e", "e ")]
    return random.choice(opciones)
df.loc[idx, "puesto"] = df.loc[idx, "puesto"].apply(ensuciar_texto)
log("dim_empleado", "puesto", "inconsistencia_texto", len(idx))

# formatos de fecha mezclados en fecha_contratacion
idx = df.sample(frac=0.2, random_state=3).index
def fecha_a_formato_raro(v):
    d = datetime.strptime(str(v), "%Y-%m-%d")
    formato = random.choice(["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"])
    return d.strftime(formato)
df.loc[idx, "fecha_contratacion"] = df.loc[idx, "fecha_contratacion"].apply(fecha_a_formato_raro)
log("dim_empleado", "fecha_contratacion", "formato_fecha_inconsistente", len(idx))

df.to_csv(f"{DIRTY}/dim_empleado.csv", index=False)

# =================================================================
# DIM_CLIENTE: nulos en email, ciudad con inconsistencias de texto
# =================================================================
df = pd.read_csv(f"{CLEAN}/dim_cliente.csv")

idx = df[df["cliente_id"] != 0].sample(frac=0.1, random_state=4).index
df.loc[idx, "email"] = np.nan
log("dim_cliente", "email", "nulos", len(idx))

idx = df.sample(frac=0.12, random_state=5).index
df.loc[idx, "ciudad"] = df.loc[idx, "ciudad"].apply(
    lambda v: random.choice([str(v).upper(), str(v).lower(), f"{v} "]) if pd.notna(v) else v
)
log("dim_cliente", "ciudad", "inconsistencia_texto", len(idx))

df.to_csv(f"{DIRTY}/dim_cliente.csv", index=False)

# =================================================================
# DIM_PRODUCTO / DIM_TIENDA / DIM_PROVEEDOR: se copian igual (control)
# =================================================================
for t in ["dim_producto", "dim_tienda", "dim_proveedor"]:
    pd.read_csv(f"{CLEAN}/{t}.csv").to_csv(f"{DIRTY}/{t}.csv", index=False)

# =================================================================
# FACT_VENTA: duplicados exactos, formato fecha, claves huerfanas (empleado)
# =================================================================
df = pd.read_csv(f"{CLEAN}/fact_venta.csv")

# 1) duplicados exactos: repetir un 1% de filas tal cual
dup_rows = df.sample(frac=0.01, random_state=6)
df = pd.concat([df, dup_rows], ignore_index=True)
log("fact_venta", "(fila completa)", "duplicados_exactos", len(dup_rows))

# 2) claves huerfanas: empleado_id que no existe (fuera de rango)
idx = df.sample(frac=0.005, random_state=7).index
df.loc[idx, "empleado_id"] = df.loc[idx, "empleado_id"] + 9000  # id inexistente
log("fact_venta", "empleado_id", "clave_huerfana", len(idx))

# 3) formato de fecha mezclado
idx = df.sample(frac=0.25, random_state=8).index
def fecha_venta_raro(v):
    d = datetime.strptime(str(v), "%Y-%m-%d")
    formato = random.choice(["%d/%m/%Y", "%d-%m-%Y"])
    return d.strftime(formato)
df.loc[idx, "fecha"] = df.loc[idx, "fecha"].apply(fecha_venta_raro)
log("fact_venta", "fecha", "formato_fecha_inconsistente", len(idx))

# 4) metodo_pago con inconsistencia de texto
idx = df.sample(frac=0.1, random_state=9).index
df.loc[idx, "metodo_pago"] = df.loc[idx, "metodo_pago"].apply(
    lambda v: random.choice([str(v).upper(), str(v).lower()])
)
log("fact_venta", "metodo_pago", "inconsistencia_texto", len(idx))

df.to_csv(f"{DIRTY}/fact_venta.csv", index=False)

# =================================================================
# FACT_LINEA_VENTA: outliers, clave huerfana (producto), tipos mezclados
# =================================================================
df = pd.read_csv(f"{CLEAN}/fact_linea_venta.csv")

# 1) outliers de cantidad (imposible en un ticket real)
idx = df.sample(n=25, random_state=10).index
df.loc[idx, "cantidad"] = np.random.choice([50000, 99999, 200000], size=len(idx))
log("fact_linea_venta", "cantidad", "outlier_numerico", len(idx))

# 2) precio_unitario negativo (error de sistema)
idx = df.sample(n=15, random_state=11).index
df.loc[idx, "precio_unitario"] = -df.loc[idx, "precio_unitario"]
log("fact_linea_venta", "precio_unitario", "outlier_numerico_negativo", len(idx))

# 3) claves huerfanas: producto_id que no existe
idx = df.sample(frac=0.004, random_state=12).index
df.loc[idx, "producto_id"] = df.loc[idx, "producto_id"] + 500  # fuera de rango (1-90)
log("fact_linea_venta", "producto_id", "clave_huerfana", len(idx))

# 4) cantidad como texto en vez de numero (tipos mezclados)
idx = df.sample(frac=0.02, random_state=13).index
df["cantidad"] = df["cantidad"].astype(object)
df.loc[idx, "cantidad"] = df.loc[idx, "cantidad"].apply(lambda v: str(v))
log("fact_linea_venta", "cantidad", "tipo_mezclado_texto", len(idx))

# 5) duplicados casi-exactos: mismo venta_id+producto pero cantidad distinta
dup_idx = df.sample(frac=0.005, random_state=14).index
casi_dup = df.loc[dup_idx].copy()
casi_dup["cantidad"] = casi_dup["cantidad"].apply(
    lambda v: (int(v) if str(v).isdigit() else 1) + random.randint(1, 3)
)
df = pd.concat([df, casi_dup], ignore_index=True)
log("fact_linea_venta", "(fila completa)", "casi_duplicados", len(casi_dup))

df.to_csv(f"{DIRTY}/fact_linea_venta.csv", index=False)

# =================================================================
# FACT_COMPRA / FACT_LINEA_COMPRA: clave huerfana + nulos en coste
# =================================================================
df_c = pd.read_csv(f"{CLEAN}/fact_compra.csv")
idx = df_c.sample(frac=0.005, random_state=15).index
df_c.loc[idx, "proveedor_id"] = df_c.loc[idx, "proveedor_id"] + 100
log("fact_compra", "proveedor_id", "clave_huerfana", len(idx))
df_c.to_csv(f"{DIRTY}/fact_compra.csv", index=False)

df_lc = pd.read_csv(f"{CLEAN}/fact_linea_compra.csv")
idx = df_lc.sample(frac=0.02, random_state=16).index
df_lc.loc[idx, "coste_unitario"] = np.nan
log("fact_linea_compra", "coste_unitario", "nulos", len(idx))
df_lc.to_csv(f"{DIRTY}/fact_linea_compra.csv", index=False)

# =================================================================
# GUARDAR LOG DE AUDITORIA
# =================================================================
df_log = pd.DataFrame(audit_log)
df_log.to_csv(f"{DIRTY}/audit_log.csv", index=False)
print(df_log.to_string(index=False))
print(f"\nTotal anomalias registradas: {len(df_log)} tipos distintos")
