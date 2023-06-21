import pandas as pd
import numpy as np
import sys
import json


if __name__ == '__main__':
    
    numArticulo = sys.argv[1]  # Obtener el valor del primer argumento de línea de comandos
    numArticulo = int(numArticulo)

    #df_data y df_dataC

    df_data = pd.read_excel('/mnt/b/Documentos/9_PORTAhnos/chatBot_telegram/src/proyecto_total_detallado_20230615110459.xlsx')
    df_dataC = df_data.copy()

    #df_cantidades

    df_cantidades = pd.DataFrame()
    columnas_cantidades = ['CANTIDAD_SOLICITADA', 'CANTIDAD_RECIBIDA', 'CANTIDAD_PENDIENTE', 'CANTIDAD_REMITO', 'OC_NUMERO', 'CODIGO_ARTICULO']

    # RELLENO DE 0 todo aquello vacio
    df_cantidades[columnas_cantidades] = df_dataC[columnas_cantidades].fillna(0)
    # CAMBIO DE TIPO DE DATO
    df_cantidades[columnas_cantidades] = df_cantidades[columnas_cantidades].astype(int)
    df_cantidades['OC_FECHA_COMPROMISO_ENTREGA'] = df_dataC['OC_FECHA_COMPROMISO_ENTREGA']

    


def llamarCantidades(df_cantidades, numArticulo):
# Filtrar el DataFrame por el código de artículo

    filtro = df_cantidades['CODIGO_ARTICULO'] == numArticulo
    df_filtrado = df_cantidades[filtro]
    
    if len(df_filtrado) > 0:
        fecha_compromiso_entrega = df_filtrado['OC_FECHA_COMPROMISO_ENTREGA'].iloc[0]
    else:
        fecha_compromiso_entrega = None  # O asigna cualquier otro valor predeterminado que desees

# Calcular las sumas de las columnas requeridas
    cantidad_solicitada = df_filtrado['CANTIDAD_SOLICITADA'].sum()
    cantidad_recibida = df_filtrado['CANTIDAD_RECIBIDA'].sum()
    cantidad_pendiente = df_filtrado['CANTIDAD_PENDIENTE'].sum()
    #fecha_compromiso_entrega = df_filtrado['OC_FECHA_COMPROMISO_ENTREGA'].iloc[0]  # Tomar el primer valor de la columna

    cantidad_solicitada = int(cantidad_solicitada)
    cantidad_recibida = int(cantidad_recibida)
    cantidad_pendiente = int(cantidad_pendiente)



    # Retornar los resultados como un diccionario
    resultados = {
        'cantidad_solicitada': cantidad_solicitada,
        'cantidad_recibida': cantidad_recibida,
        'cantidad_pendiente': cantidad_pendiente,
        'fecha_compromiso_entrega': fecha_compromiso_entrega
    }
    resultados_json = json.dumps(resultados)

    return resultados_json


resultados_json = llamarCantidades(df_cantidades, numArticulo)
print(resultados_json)





#print("Resultados:")
#print(f"Cantidad solicitada: {resultados['cantidad_solicitada']}")
#print(f"Cantidad recibida: {resultados['cantidad_recibida']}")
#print(f"Cantidad pendiente: {resultados['cantidad_pendiente']}")
#print(f"Fecha compromiso entrega: {resultados['fecha_compromiso_entrega']}")
#print(df_cantidades["CODIGO_ARTICULO"])


