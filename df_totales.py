import pandas as pd
import numpy as np

from textblob import TextBlob
import Levenshtein

from datetime import datetime
import datefinder

import sys
import json


#1: Presupuesto_Mejoras_PA_Prote_CCP23
#2: Presupuesto_Mnto_Planta_Prote_CCP23
#3: 

def procesar_df():

    df_data = pd.read_excel(f'/mnt/b/Documentos/9_PORTAhnos/chatBot_telegram/src/{numPresupuesto}.xlsx')
    df_dataC = df_data.copy()

    def setearTotal(df_dataC):

        columnas_totales = ['TOTAL (U$S)','TOTAL ($)']
        df_totales = df_dataC[columnas_totales]
        df_totales = pd.DataFrame()

        df_totales["TOTAL (U$S)"] = df_dataC['TOTAL (U$S)'].astype(float)
        df_totales['TOTAL ($)'] = df_dataC['TOTAL ($)'].astype(float)

        df_totales["CONSIDERAR"] = ""
        df_totales["coincidencias"] = ""
        df_totales['indice'] = df_totales.index 

        return df_totales

    df_totales = setearTotal(df_dataC)

    
    #---------------------------------------------------

    def asignar_valores_no(df, columna):

        df['indice'] = df.index

        for valor in df[columna][df[columna] <= 0].unique(): #recorre el df filtrado, menores a 0 y unicos

            ocurrencias = df[df[columna].abs() == abs(valor)].shape[0] #cuenta las ocurrencias de cada valor de ese df filtrado

            #print(f'valor = {valor}, ocurrencia = {ocurrencias}' )

            #si la cantidad de ocurrencias es divisible por dos quiere decir que todos van con "NO"
            if ocurrencias % 2 == 0 :

                value_counts_negative = len(df[df[columna] == valor])
                value_counts_positive = len(df[df[columna] == -valor])

                #print(f'ocurrencia PAR = {ocurrencias}, valor = {valor}')

                if value_counts_negative == value_counts_positive:
                    df.loc[df[columna].abs() == abs(valor) , 'CONSIDERAR'] = 'NO'
                    df.loc[df[columna].abs() == abs(valor) , 'coincidencias'] = ocurrencias

                elif value_counts_positive > value_counts_negative:

                    filas = df[df[columna] == valor].index[:]
                    df.loc[filas, 'CONSIDERAR'] = 'NO'
                    df.loc[filas, 'coincidencias'] = ocurrencias

                    filas = df[df[columna] == -valor].index[:value_counts_negative]
                    df.loc[filas, 'CONSIDERAR'] = 'NO'
                    df.loc[filas, 'coincidencias'] = ocurrencias

                elif value_counts_negative > value_counts_positive:

                    filas = df[df[columna] == -valor].index[:]
                    df.loc[filas, 'CONSIDERAR'] = 'NO'
                    df.loc[filas, 'coincidencias'] = ocurrencias

                filas = df[df[columna] == valor].index[:value_counts_positive]
                df.loc[filas, 'CONSIDERAR'] = 'NO'
                df.loc[filas, 'coincidencias'] = ocurrencias


            #si el valor es 0 le asigna NO a todas las filas
            elif valor == 0:

                df.loc[df[columna].abs() == abs(valor) , 'CONSIDERAR'] = 'NO'
                df.loc[df[columna].abs() == abs(valor) , 'coincidencias'] = ocurrencias

            #si la cantidad de ocurrencias es mayor a 1 y no divisble por dos entonces evalua que el valor no sea 0 y
            #cuenta la cantidad de valores positivos y negativos que hay, si hay mas positivos que negativos entonces
            #asigna NO en considerar a todos los valores positivos menos al ultimo y a todos los negativos
            #En caso contrario funciona igual

            elif ocurrencias > 1:

                if valor != 0:

                    value_counts_negative = len(df[df[columna] == valor])
                    value_counts_positive = len(df[df[columna] == -valor])

                    #chequeador
                    #print(f' ocurrencias IMPAR= {ocurrencias} la cantidad negativa son: {value_counts_negative}, las cantidad positiva son: {value_counts_positive}, para una variable valor = {valor} ')


                    if value_counts_positive > value_counts_negative:

                        filas = df[df[columna] == -valor].index[:value_counts_negative]
                        df.loc[filas, 'CONSIDERAR'] = 'NO'
                        df.loc[filas, 'coincidencias'] = ocurrencias

                        filas = df[df[columna] == valor].index[:]
                        df.loc[filas, 'CONSIDERAR'] = 'NO'
                        df.loc[filas, 'coincidencias'] = ocurrencias

                    else:

                        filas = df[df[columna] == valor].index[:value_counts_positive]
                        df.loc[filas, 'CONSIDERAR'] = 'NO'
                        df.loc[filas, 'coincidencias'] = ocurrencias

                        filas = df[df[columna] == -valor].index[:]
                        df.loc[filas, 'CONSIDERAR'] = 'NO'
                        df.loc[filas, 'coincidencias'] = ocurrencias

                elif ocurrencias == 1:

                    df.loc[df[columna].abs() == abs(valor) , 'CONSIDERAR'] = ''
                    df.loc[df[columna].abs() == abs(valor) , 'coincidencias'] = ocurrencias


        return df

    df_totales = asignar_valores_no(df_totales, 'TOTAL (U$S)')
    df_totales = asignar_valores_no(df_totales, 'TOTAL ($)')

    columnas_eliminar = ['TOTAL (U$S)', 'TOTAL ($)', 'coincidencias', 'coincidencias','indice']
    df_totales = df_totales.drop(columns=columnas_eliminar)

    df_totales = df_totales.rename(columns={'TOTAL (U$S)_x': 'TOTAL (U$S)', 'TOTAL ($)_x': 'TOTAL ($)'})

    
    # df_facturas ---------------------------------------------------------------------------------->

    df_obs = df_dataC["OBSERVACIONES"]
    df_obs = df_obs.to_frame()

    df_facturas = pd.DataFrame(columns=['Mejor_Texto', 'Similitud'])
    
    frases_clave = ("A 0009-00055556","A 0009-00003407", "A 0006-00012269","C 0003-00000003",
                    "E 0002-00021191","M 0007-00000011")

    def encontrar_frase_mas_parecida(df, frases_clave):

        df_facturas = df.copy()
        df_facturas['Mejor_Texto'] = ""
        df_facturas['Similitud'] = 0.0

        for index, row in df.iterrows():
            texto = row['OBSERVACIONES']  # Reemplaza 'columna_texto' con el nombre de la columna de texto en tu DataFrame

            mejor_similitud = 0
            mejor_texto = None

            for frase in frases_clave:
                if len(texto) >= len(frase):
                    n = len(texto) - len(frase) + 1  # Número de subcadenas posibles en 'texto'
                    for i in range(n):
                        subcadena = texto[i:i+len(frase)]
                        if subcadena[0] in ['A','C','E','M']:  # Verificar que la subcadena comience con 'A' o 'C'
                            similitud = Levenshtein.ratio(subcadena, frase)
                            if similitud > mejor_similitud:
                                mejor_similitud = similitud
                                mejor_texto = subcadena

            df_facturas.at[index, 'Mejor_Texto'] = mejor_texto
            df_facturas.at[index, 'Similitud'] = mejor_similitud

        
        df_facturas.loc[df_facturas['Similitud'] <= 0.5, 'Mejor_Texto'] = ""
        return df_facturas

    df_facturas = encontrar_frase_mas_parecida(df_obs, frases_clave)

    #df_facturas.to_excel('df_facturas.xlsx',index=False)


    # df_facturas_fechas ---------------------------------------------------------------------------->

    df_obs = df_dataC["OBSERVACIONES"]
    df_obs = df_obs.to_frame()

    def extraer_fechas(df):
        df_facturas_fechas = df.copy()
        df_facturas_fechas['FECHAS_FACTURAS'] = ""

        for index, row in df.iterrows():
            texto = row['OBSERVACIONES']

            fechas_encontradas = list(datefinder.find_dates(texto))

            if fechas_encontradas:
                fechas_sin_hora = [fecha.strftime("%d-%m-%Y") for fecha in fechas_encontradas]
                fechas_str = ", ".join([str(fecha) for fecha in fechas_encontradas])

                df_facturas_fechas.at[index, 'FECHAS_FACTURAS'] = fechas_str[0:10]

            else:
                df_facturas_fechas.at[index, 'FECHAS_FACTURAS'] = ""

        df_facturas_fechas = df_facturas_fechas.drop(['OBSERVACIONES'],axis=1)

        return df_facturas_fechas

    df_facturas_fechas= extraer_fechas(df_obs)

    #df_facturas_fechas.to_excel('df_facturas_fechas.xlsx',index=False)

    # df_considerar ---------------------------------------------------------------------->

    df_obs = df_dataC["OBSERVACIONES"]
    df_obs = df_obs.to_frame()

    df_considerar = pd.DataFrame(columns=['Mejor_Texto_obs', 'Similitud_obs'])

    df_considerar['CONSIDERAR_OBS'] = ''


    frases_clave = ["Asiento Mensual Por Acreedores", "Provision Remitos sin Factura", "Reverso prov IVA",
                        "Provision Manual Facturas a Recibir"]


    def encontrar_frase_mas_parecida(df, frases_clave):
        df_considerar['Mejor_Texto_obs'] = ""
        df_considerar['Similitud_obs'] = 0.0

        for index, row in df.iterrows():
            texto = row['OBSERVACIONES']  # Reemplaza 'columna_texto' con el nombre de la columna de texto en tu DataFrame

            mejor_similitud = 0
            Mejor_Texto = None

            for frase in frases_clave:
                if len(texto) >= len(frase):
                    n = len(texto) - len(frase) + 1  # Número de subcadenas posibles en 'texto'
                    for i in range(n):
                        subcadena = texto[i:i+len(frase)]
                        similitud = Levenshtein.ratio(subcadena, frase)
                        if similitud > mejor_similitud:
                                mejor_similitud = similitud
                                Mejor_Texto = subcadena

            df_considerar.at[index, 'Mejor_Texto_obs'] = frase
            df_considerar.at[index, 'Similitud_obs'] = mejor_similitud

        #CRITERIO PARA DEFINIR QUE SI Y QUE NO DENTRO DEL RANGO DE Levenshtein

        df_considerar.loc[df_considerar['Similitud_obs'] >= 0.8, 'CONSIDERAR_OBS'] = "NO"

        
        return df_considerar

    df_considerar = encontrar_frase_mas_parecida(df_obs, frases_clave)

    #df_considerar.to_excel('df_considerar.xlsx',index=False)

    # INDICES + MERGE -------------------------------------------------------

    # Agregar una columna de índice a df_dataC
    df_dataC['indice'] = df_dataC.index

    # Agregar una columna de indice a df_monedas
    df_totales['indice'] = df_totales.index

    # Agregar una columna de índice a df_facturas
    df_facturas['indice'] = df_facturas.index

    # Agregar una columna de índice a df_resultados_fechas
    df_facturas_fechas['indice'] = df_facturas_fechas.index

    # Agregar una columna de índice a df_considerar segun OBS
    df_considerar['indice'] = df_considerar.index

    df_merged = pd.merge(df_totales, df_dataC, on='indice')
    df_merged = pd.merge(df_merged, df_facturas, on='indice')
    df_merged = pd.merge(df_merged, df_facturas_fechas, on='indice')
    df_merged = df_merged.merge(df_considerar[['indice', 'CONSIDERAR_OBS']], on='indice', how='left')
    df_merged['CONSIDERAR'] = df_merged['CONSIDERAR'].astype(str) + df_merged['CONSIDERAR_OBS'].astype(str)
    df_merged = df_merged.drop(columns=['CONSIDERAR_OBS'])
    df_merged['CONSIDERAR'] = df_merged['CONSIDERAR'].apply(lambda x: 'NO' if x != 'nan' else 'SI')

    # df_final -------------------------------------------------------------------------->

    df_final = df_merged.copy()

    df_final = df_final.rename(columns={'Mejor_Texto': 'NUMERO_FACTURA', 
                                        'OBSERVACIONES_x' : 'OBSERVACIONES',
                                        'FECHA' : 'FECHA_ASIENTO',
                                        'NUMERO_OPERACION': 'NUMERO_ASIENTO'})

    columnas_filtradas = ['IMPUTACION','CANTIDAD_SOLICITADA', 'CANTIDAD_REMITO','TOTAL (U$S)', 'TOTAL ($)', 
                          'CONSIDERAR', 'FECHAS_FACTURAS', 'NUMERO_FACTURA', 'CUENTA_CONTABLE_OC', 
                          'DESCRIPCION_CUENTA_CONTABLE_OC', 'PROYECTO_CODIGO_OC', 'PROYECTO_OC',
                            'NUMERO_REMITO', 'FECHA_REMITO', 'OBSERVACIONES', 'PROVEEDOR', 'OC_FECHA',
                            'OC_USUARIO', 'FECHA_ASIENTO', 'OC_NUMERO', 'TIPO', 'NUMERO_ASIENTO',
                            'CODIGO_ARTICULO', 'ARTICULO','CODIGO_IMPUTACION']

    df_final = df_final[columnas_filtradas]

    #df_final.to_excel('df_final.xlsx',index=False)


    # df_normalizada ------------------------------------------------------------------------->

    df_normalizada = df_final.copy()

    columnas_numericas = ['NUMERO_FACTURA', 'NUMERO_ASIENTO', 'OC_NUMERO', 'CODIGO_ARTICULO',
                          'NUMERO_REMITO','CUENTA_CONTABLE_OC','CANTIDAD_SOLICITADA',
                           'CANTIDAD_REMITO','CODIGO_IMPUTACION']
    df_normalizada[columnas_numericas] = df_normalizada[columnas_numericas].fillna(0)

    #RELLENO los registros vacios con el nombre o el codigo de proyecto segun corresponda
    df_normalizada['PROYECTO_CODIGO_OC'] = df_normalizada['PROYECTO_CODIGO_OC'].fillna(df_normalizada['PROYECTO_CODIGO_OC'].ffill())
    df_normalizada['PROYECTO_OC'] = df_normalizada['PROYECTO_OC'].fillna(df_normalizada['PROYECTO_OC'].ffill())


    #Saco los asientos que no empiecen con 16
    df_normalizada.loc[~(df_normalizada["NUMERO_ASIENTO"].str.startswith(("16","17"))), "NUMERO_ASIENTO"] = "0"

    #saco los "-" de la columna codigo_imputacion
    df_normalizada.loc[df_normalizada["CODIGO_IMPUTACION"] == "-", "CODIGO_IMPUTACION"] = 0

    #CAMBIO DE TIPO FLOAT64 a INT
    columnas_enteros = ['OC_NUMERO', 'CODIGO_ARTICULO', 'NUMERO_REMITO', 'CUENTA_CONTABLE_OC',
                        'NUMERO_ASIENTO','CODIGO_IMPUTACION']
    df_normalizada[columnas_enteros] = df_normalizada[columnas_enteros].astype(int)

    #CAMBIO DE TIPO .str a FLOAT
    columnas_FLOAT = ['CANTIDAD_SOLICITADA', 'CANTIDAD_REMITO']
    df_normalizada[columnas_FLOAT] = df_normalizada[columnas_FLOAT].astype(float)

    #df_normalizada.to_excel('df_normalizada.xlsx',index=False)

    # df_clasificacionOtros --------------------------------------------------------------------------------->
    df_obs = df_dataC["OBSERVACIONES"]
    df_obs = df_obs.to_frame()
    
    df_clasificacionOtros = pd.DataFrame(columns=['Mejor_Texto', 'Similitud'])

    frases_clave = ["Provision Hs de trabajo", "P/reclasf", "CONSUMOS DEPOSITO",
                    "AJUSTE STOCK PAÑOL","REVERSO Hs de trabajo",]

    def encontrar_frase_mas_parecida(df, frases_clave):

        df_clasificacionOtros = df.copy()
        df_clasificacionOtros['Mejor_Texto'] = ""
        df_clasificacionOtros['Similitud'] = 0.0

        for index, row in df.iterrows():
            texto = row['OBSERVACIONES']  # Reemplaza 'columna_texto' con el nombre de la columna de texto en tu DataFrame

            mejor_similitud = 0
            mejor_texto = None

            for frase in frases_clave:
                if len(texto) >= len(frase):
                    n = len(texto) - len(frase) + 1  # Número de subcadenas posibles en 'texto'
                    for i in range(n):
                        subcadena = texto[i:i+len(frase)]
                        similitud = Levenshtein.ratio(subcadena, frase)
                        if similitud > mejor_similitud:
                                mejor_similitud = similitud
                                mejor_texto = frase

            df_clasificacionOtros.at[index, 'Mejor_Texto'] = mejor_texto
            df_clasificacionOtros.at[index, 'Similitud'] = mejor_similitud

        df_clasificacionOtros.loc[df_clasificacionOtros['Similitud'] <= 0.7, 'Mejor_Texto'] = ""
        df_clasificacionOtros['texto_especial'] = df_clasificacionOtros['Mejor_Texto'].apply(lambda x: 1 if x in ["Provision Hs de trabajo","REVERSO Hs de trabajo"] else (2 if x == "P/reclasf" else (3 if x in ["CONSUMOS DEPOSITO", "AJUSTE STOCK PAÑOL"] else 0)))

        return df_clasificacionOtros

    df_clasificacionOtros = encontrar_frase_mas_parecida(df_obs, frases_clave)

    #df_clasificacionOtros.to_excel('df_clasificacionOtros.xlsx',index=False)

    # df_normalizadaC---------------------------------------------------------->

    df_normalizadaC = df_normalizada.copy()
    df_normalizadaC["CANTIDAD"] = 0
    df_normalizadaC["CUENTA_CONTABLE"] = ""

    for index, row in df_normalizadaC.iterrows():

    #cuenta contable
        if (row["IMPUTACION"] != "-"):
            df_normalizadaC.at[index, "CUENTA_CONTABLE"] = row["IMPUTACION"]

        elif (row["IMPUTACION"]):
            df_normalizadaC.at[index, "CUENTA_CONTABLE"] = row["DESCRIPCION_CUENTA_CONTABLE_OC"]

    #cantidades

        if (row["NUMERO_FACTURA"] == 0.0) & (row["NUMERO_REMITO"] == 0.0) & (row["OC_NUMERO"] != 0.0):  df_normalizadaC.at[index, "CANTIDAD"] = row["CANTIDAD_SOLICITADA"]
        else:  df_normalizadaC.at[index, "CANTIDAD"] = row["CANTIDAD_REMITO"]


    #df_normalizadaC.to_excel('df_normalizadaC.xlsx',index=False)

    # df_clasificar --------------------------------------------------------------------->
    
    df_clasificacionOtros["indice"] = df_clasificacionOtros.index
    df_normalizadaC["indice"] = df_normalizadaC.index
    df_normalizadaC = df_normalizadaC.merge(df_clasificacionOtros[['indice', 'texto_especial']], on='indice', how='left')
    
    def clasificar(df):

        def es_digito(cadena):
            if isinstance(cadena, str) and cadena.isdigit():
                return 1
            else:
                return 0
            
        df["NUMERO_FACTURA_1111"] = df["NUMERO_FACTURA"].astype(str).str[-2:].apply(es_digito)

        df["CLASIFICACION"] = ""

        for index, row in df.iterrows():
            if (row["NUMERO_ASIENTO"] == 0) and (row["NUMERO_FACTURA_1111"] == 0) and (row["NUMERO_REMITO"] == 0) and (row["OC_NUMERO"] != 0):
                df.at[index, "CLASIFICACION"] = "Oc Sin remito y sin factura"
            elif (row["NUMERO_ASIENTO"] != 0) and (row["NUMERO_FACTURA_1111"] != 0) and (row["NUMERO_REMITO"] != 0) and (row["OC_NUMERO"] != 0):
                df.at[index, "CLASIFICACION"] = "Oc Con remito y con factura"
            elif (row["NUMERO_ASIENTO"] == 0) and (row["NUMERO_FACTURA_1111"] == 0) and (row["NUMERO_REMITO"] != 0) and (row["OC_NUMERO"] != 0):
                df.at[index, "CLASIFICACION"] = "Oc Con remito y sin factura"
            elif (row["NUMERO_ASIENTO"] != 0) and (row["NUMERO_FACTURA_1111"] != 0) and (row["NUMERO_REMITO"] == 0) and (row["OC_NUMERO"] == 0):
                df.at[index, "CLASIFICACION"] = "Factura de servicios"
            elif (row["NUMERO_ASIENTO"] != 0) and (row["NUMERO_FACTURA_1111"] == 0) and (row["NUMERO_REMITO"] == 0) and (row["OC_NUMERO"] == 0) and (row["texto_especial"] == 0):
                df.at[index, "CLASIFICACION"] = "Otros asientos (reclasif/compes)"
            elif (row["NUMERO_ASIENTO"] != 0) and (row["NUMERO_FACTURA_1111"] == 0) and (row["NUMERO_REMITO"] == 0) and (row["OC_NUMERO"] == 0) and (row["texto_especial"] == 1):
                df.at[index, "CLASIFICACION"] = "Asiento de sueldos"
            elif (row["NUMERO_ASIENTO"] != 0) and (row["NUMERO_FACTURA_1111"] == 0) and (row["NUMERO_REMITO"] == 0) and (row["OC_NUMERO"] == 0) and (row["texto_especial"] == 2):
                df.at[index, "CLASIFICACION"] = "Otros asientos (reclasif/compes)"
            elif (row["NUMERO_ASIENTO"] != 0) and (row["NUMERO_FACTURA_1111"] == 0) and (row["NUMERO_REMITO"] == 0) and (row["OC_NUMERO"] == 0) and (row["texto_especial"] == 3):
                df.at[index, "CLASIFICACION"] = "Asientos Pannol"
            else:
                df.at[index, "CLASIFICACION"] = np.nan
        return df

    df_clasificada = clasificar(df_normalizadaC)

    columnas_filtradas = ['TOTAL (U$S)', 'TOTAL ($)', 'CONSIDERAR', 'FECHAS_FACTURAS',
                          'NUMERO_FACTURA', 'CUENTA_CONTABLE_OC',
                          'PROYECTO_CODIGO_OC', 'PROYECTO_OC', 'NUMERO_REMITO',
                          'FECHA_REMITO', 'OBSERVACIONES', 'PROVEEDOR', 'OC_FECHA',
                          'CLASIFICACION', 'FECHA_ASIENTO', 'OC_NUMERO',
                          'TIPO', 'NUMERO_ASIENTO', 'CODIGO_ARTICULO', 'ARTICULO',
                          "CANTIDAD", "CUENTA_CONTABLE",'CODIGO_IMPUTACION']

    df_clasificada = df_normalizadaC[columnas_filtradas]

    df_clasificada.to_excel('df_clasificada.xlsx',index=False)

    
    # df_agrupado -------------------------------------------------->

    df_agrupado = df_clasificada.groupby('CLASIFICACION').agg({'TOTAL (U$S)': 'sum', 'TOTAL ($)': 'sum', 'CANTIDAD': 'sum'})

    df_agrupado.to_excel('df_agrupado.xlsx',index=False)
    
    return df_clasificada

if __name__ == '__main__':

    numPresupuesto = sys.argv[1]  # Obtener el valor del primer argumento de línea de comandos
    numPresupuesto = int(numPresupuesto)

    resultados_json = procesar_df()
    print(resultados_json)
