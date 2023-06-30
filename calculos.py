import pandas as pd
import sys
import json

# Llamar a la función para ejecutar df_totales.py
numPresupuesto = sys.argv[1]  # Obtener el valor del primer argumento de línea de comandos
numArnumPresupuesto = int(numPresupuesto)


df_clasificada = pd.read_excel(f'/mnt/b/Documentos/9_PORTAhnos/chatBot_telegram/df_clasificada_{numPresupuesto}.xlsx')

def estadisticas(df):

    # df_agrupado -------------------------------------------------->

    df_clasificacion = df.groupby('CLASIFICACION').agg({'TOTAL (U$S)': 'sum', 'TOTAL ($)': 'sum', 'CANTIDAD': 'sum'})
    df_tipo = df.groupby('TIPO').agg({'TOTAL (U$S)': 'sum', 'TOTAL ($)': 'sum', 'CANTIDAD': 'sum'})
    

    # Obtener la suma de la columna "TOTAL (U$S)"
    suma_total_usd = df["TOTAL (U$S)"].sum()

    # Obtener la cantidad de valores únicos de la columna "OC_NUMERO"
    cantidad_oc_numero = df["OC_NUMERO"].nunique()

    # Obtener la cantidad de valores únicos de las columnas "NUMERO_FACTURA" y "NUMERO_REMITO"
    cantidad_numero_factura = df["NUMERO_FACTURA"].nunique()
    cantidad_numero_remito = df["NUMERO_REMITO"].nunique()

    # sumatoria de cada valor único en df_clasificacion
    df_clasificacion["SUMA"] = df_clasificacion["TOTAL (U$S)"]
    
    # Porcentaje de cada valor único en df_tipo
    df_tipo["PORCENTAJE"] = df_tipo["TOTAL (U$S)"] / suma_total_usd * 100

    
    sumatoria_clasificacion = pd.Series(df_clasificacion["SUMA"].round(2), name="Sumatoria Clasificacion")
    porcentaje_tipo = pd.Series(df_tipo["PORCENTAJE"].round(2), name="Porcentaje Tipo")


    df_cuenta_contable = df.groupby("CUENTA_CONTABLE").agg({"TOTAL (U$S)": "sum"})
    df_cuenta_contable["SUMA"] = df_cuenta_contable["TOTAL (U$S)"]
    #df_cuenta_contable["PORCENTAJE"] = df_cuenta_contable["TOTAL (U$S)"] / suma_total_usd * 100

    sumatoria_cuenta_contable = pd.Series(df_cuenta_contable["SUMA"].round(2), name="Sumatoria Cuenta Contable")
    #porcentaje_cuenta_contable = pd.Series(df_cuenta_contable["PORCENTAJE"].round(2), name="Porcentaje Cuenta Contable")

    resultados = {
        "Total en el proyecto" : round(suma_total_usd,2),
        "Sumatoria Clasificacion": sumatoria_clasificacion.to_dict(),
        "Porcentaje Tipo": porcentaje_tipo.to_dict(),
        "Por cuenta Contable": sumatoria_cuenta_contable.to_dict(),
        "Cantidad de facturas" : cantidad_numero_factura,
        "Cantidad de remitos" : cantidad_numero_remito,
        "Cantidad de Ordenes de compra" : cantidad_oc_numero

    }

    resultados_json = json.dumps(resultados)

    return resultados_json


# Llamar a la función estadisticas con el DataFrame df_clasificada
resultados_json = estadisticas(df_clasificada)

print(resultados_json)