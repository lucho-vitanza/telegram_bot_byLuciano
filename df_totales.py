import pandas as pd
import numpy as np

from textblob import TextBlob
import Levenshtein

from datetime import datetime
import datefinder

import json

def procesar_df():

    df_data = pd.read_excel('/mnt/b/Documentos/9_PORTAhnos/chatBot_telegram/src/proyecto_total_detallado_20230615110459.xlsx')
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

    #no_count = df_totales['CONSIDERAR'].value_counts()['NO']
    #print("Número de valores 'NO' en la columna CONSIDERAR:", no_count)
    


    # df_monedas ---------------------------------------------------------------------------------------->

    df_monedas = df_totales

    df_totales = df_monedas.copy()

    columnas_eliminar = ['TOTAL (U$S)', 'TOTAL ($)', 'coincidencias', 'coincidencias','indice']
    df_totales = df_monedas.drop(columns=columnas_eliminar)


    df_totales = df_totales.rename(columns={'TOTAL (U$S)_x': 'TOTAL (U$S)', 'TOTAL ($)_x': 'TOTAL ($)'})
    
    
    df_obs = df_dataC["OBSERVACIONES"]

    df_obs = df_obs.to_frame()

    df_facturas = pd.DataFrame(columns=['Mejor_Texto', 'Similitud'])
    
    frases_clave = ("A 0009-00055556","A 0009-00003407", "A 0006-00012269","C 0003-00000003","E 0002-00021191")

    def encontrar_frase_mas_parecida(df_obs, frases_clave):

        df_facturas = df_obs.copy()
        df_facturas['Mejor_Texto'] = ""
        df_facturas['Similitud'] = 0.0

        for index, row in df_facturas.iterrows():
            texto = row['OBSERVACIONES']  # Reemplaza 'columna_texto' con el nombre de la columna de texto en tu DataFrame

            mejor_similitud = 0
            mejor_texto = None

            for frase in frases_clave:
                if len(texto) >= len(frase):
                    n = len(texto) - len(frase) + 1  # Número de subcadenas posibles en 'texto'
                    for i in range(n):
                        subcadena = texto[i:i+len(frase)]
                        if subcadena[0] in ['A','C','E']:  # Verificar que la subcadena comience con 'A' o 'C'
                            similitud = Levenshtein.ratio(subcadena, frase)
                            if similitud > mejor_similitud:
                                mejor_similitud = similitud
                                mejor_texto = subcadena

            df_facturas.at[index, 'Mejor_Texto'] = mejor_texto
            df_facturas.at[index, 'Similitud'] = mejor_similitud

        
        #df_facturas.loc[df_facturas['Similitud'] <= 0.5, 'Mejor_Texto'] = ""
        return df_facturas

    df_facturas = encontrar_frase_mas_parecida(df_obs, frases_clave)

    
    


    # df_facturas_fechas ---------------------------------------

    df_obs = df_dataC["OBSERVACIONES"]
    df_obs = df_obs.to_frame()

    def extraer_fechas(df_obs):
        df_facturas_fechas = df_obs.copy()
        df_facturas_fechas['FECHAS_FACTURAS'] = ""

        for index, row in df_obs.iterrows():
            texto = row['OBSERVACIONES']

            fechas_encontradas = list(datefinder.find_dates(texto))

            if fechas_encontradas:
                fechas_sin_hora = [fecha.strftime("%d-%m-%Y") for fecha in fechas_encontradas]
                fechas_str = ", ".join([str(fecha) for fecha in fechas_encontradas])

                df_facturas_fechas.at[index, 'FECHAS_FACTURAS'] = fechas_str[0:10]

            else:
                df_facturas_fechas.at[index, 'FECHAS_FACTURAS'] = ""

        return df_facturas_fechas



    df_facturas_fechas= extraer_fechas(df_obs)



    # INDICES + MERGE -------------------------------------------------------


    # Agregar una columna de índice a df_dataC
    df_dataC['indice'] = df_dataC.index

    # Agregar una columna de indice a df_monedas
    df_totales['indice'] = df_totales.index

    # Agregar una columna de índice a df_facturas
    df_facturas['indice'] = df_facturas.index

    # Agregar una columna de índice a df_resultados_fechas
    df_facturas_fechas['indice'] = df_facturas_fechas.index

    df_merged = pd.merge(df_totales, df_dataC, on='indice')
    df_merged = pd.merge(df_merged, df_facturas, on='indice')
    df_merged = pd.merge(df_merged, df_facturas_fechas, on='indice')



    # df_final ---------------------------------------

    df_final = df_merged.copy()

    df_final = df_final.rename(columns={'Mejor_Texto': 'NUMERO_FACTURA', 'OBSERVACIONES_x' : 'OBSERVACIONES','FECHA' : 'FECHA_ASIENTO','NUMERO_OPERACION': 'NUMERO_ASIENTO'})


    columnas_filtradas = ['IMPUTACION','CANTIDAD_SOLICITADA', 'CANTIDAD_REMITO','TOTAL (U$S)', 'TOTAL ($)', 'CONSIDERAR', 'FECHAS_FACTURAS', 'NUMERO_FACTURA', 'CUENTA_CONTABLE_OC', 'DESCRIPCION_CUENTA_CONTABLE_OC', 'PROYECTO_CODIGO_OC', 'PROYECTO_OC', 'NUMERO_REMITO', 'FECHA_REMITO', 'OBSERVACIONES', 'PROVEEDOR', 'OC_FECHA', 'OC_USUARIO', 'FECHA_ASIENTO', 'OC_NUMERO', 'TIPO', 'NUMERO_ASIENTO', 'CODIGO_ARTICULO', 'ARTICULO']

    df_final = df_final[columnas_filtradas]



    # df_normalizada ------------------------------------------------------------------------->

    df_normalizada = df_final.copy()

    columnas_numericas = ['NUMERO_FACTURA', 'NUMERO_ASIENTO', 'OC_NUMERO', 'CODIGO_ARTICULO','NUMERO_REMITO','CUENTA_CONTABLE_OC','CANTIDAD_SOLICITADA', 'CANTIDAD_REMITO']
    df_normalizada[columnas_numericas] = df_normalizada[columnas_numericas].fillna(0)

    #RELLENO los registros vacios con el nombre o el codigo de proyecto segun corresponda
    df_normalizada['PROYECTO_CODIGO_OC'] = df_normalizada['PROYECTO_CODIGO_OC'].fillna(df_normalizada['PROYECTO_CODIGO_OC'].ffill())
    df_normalizada['PROYECTO_OC'] = df_normalizada['PROYECTO_OC'].fillna(df_normalizada['PROYECTO_OC'].ffill())


    # Saco los asientos que no empiecen con 16
    df_normalizada.loc[~df_normalizada["NUMERO_ASIENTO"].str.startswith("16"), "NUMERO_ASIENTO"] = "0"

    #CAMBIO DE TIPO FLOAT64 a INT
    columnas_enteros = ['OC_NUMERO', 'CODIGO_ARTICULO', 'NUMERO_REMITO', 'CUENTA_CONTABLE_OC','NUMERO_ASIENTO']
    df_normalizada[columnas_enteros] = df_normalizada[columnas_enteros].astype(int)

    #CAMBIO DE TIPO .str a FLOAT
    columnas_FLOAT = ['CANTIDAD_SOLICITADA', 'CANTIDAD_REMITO']
    df_normalizada[columnas_FLOAT] = df_normalizada[columnas_FLOAT].astype(float)


    # df-normalizadaC   ----------------------------------------------------------------------->

    df_normalizadaC=df_normalizada.copy()


    frases_condicion = ["Provision Hs de trabajo", "P/reclasf", "CONSUMOS DEPOSITO"]
    df_normalizadaC['tiene texto especial?'] = 0
    df_normalizadaC['frase'] = ""

    # Verificar si alguna de las frases condicionales se encuentra en el texto de la columna 'OBSERVACIONES'
    for index, row in df_normalizadaC.iterrows():
        texto = row['OBSERVACIONES']

        for frase in frases_condicion:
            if frase in texto:
                df_normalizadaC.loc[index, 'tiene texto especial?'] = 1
                df_normalizadaC.loc[index, 'frase'] = frase
                break

#------------------------------------------->cuenta contable y cantidad-----------------

    df_normalizadaC["CANTIDAD"] = 0

    df_normalizadaC["CUENTA_CONTABLE"] = ""

    for index, row in df_normalizadaC.iterrows():

    #cuenta contable

        if (row["IMPUTACION"] != 0.0):
            df_normalizadaC.at[index, "CUENTA_CONTABLE"] = row["IMPUTACION"]

        elif (row["IMPUTACION"] == 0.0):
            df_normalizadaC.at[index, "CUENTA_CONTABLE"] = row["DESCRIPCION_CUENTA_CONTABLE_OC"]

    #cantidades

        if (row["NUMERO_FACTURA"] == 0.0) & (row["NUMERO_REMITO"] == 0.0) & (row["OC_NUMERO"] != 0.0):  df_normalizadaC.at[index, "CANTIDAD"] = row["CANTIDAD_SOLICITADA"]
        else:  df_normalizadaC.at[index, "CANTIDAD"] = row["CANTIDAD_REMITO"]


    #print(f'columnas df_normalizadaC cuando usamos cuenta contable y cantidades {df_normalizadaC.columns}')

    # df_clasificar ---------------------------------------------------------

    #   print(df_normalizadaC.dtypes)

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

            elif (row["NUMERO_ASIENTO"] != 0) and (row["NUMERO_FACTURA_1111"] == 0) and (row["NUMERO_REMITO"] == 0) and (row["OC_NUMERO"] == 0): #and (row["tiene texto especial?"] == 0):
                df.at[index, "CLASIFICACION"] = "Otros asientos (reclasif/compes)"

            else:
                df.at[index, "CLASIFICACION"] = np.nan
        
        return df

    df_clasificada = clasificar(df_normalizadaC)


    #print(f'columnas df_normalizadaC despuus de clasificar {df_clasificada.columns}')

    columnas_filtradas = ['TOTAL (U$S)', 'TOTAL ($)', 'CONSIDERAR', 'FECHAS_FACTURAS', 'NUMERO_FACTURA', 'CUENTA_CONTABLE_OC', 'DESCRIPCION_CUENTA_CONTABLE_OC', 'PROYECTO_CODIGO_OC', 'PROYECTO_OC', 'NUMERO_REMITO', 'FECHA_REMITO', 'OBSERVACIONES', 'PROVEEDOR', 'OC_FECHA', 'CLASIFICACION', 'FECHA_ASIENTO', 'OC_NUMERO', 'TIPO', 'NUMERO_ASIENTO', 'CODIGO_ARTICULO', 'ARTICULO',"CANTIDAD", "CUENTA_CONTABLE","IMPUTACION"]

    df_clasificada = df_normalizadaC[columnas_filtradas]

    df_clasificada = df_clasificada.drop('OBSERVACIONES', axis=1)

    #print(df_clasificada)
# df_agrupado -------------------------------------------------->

    df_agrupado = df_clasificada.groupby('CLASIFICACION').agg({'TOTAL (U$S)': 'sum', 'TOTAL ($)': 'sum', 'CANTIDAD': 'sum'})

    #resultados_df = df_agrupado.to_dict(orient='index')

    #resultados_df_json = json.dumps(df_agrupado)
    
    #return resultados_df_json
    return df_agrupado.to_json(orient='records')
    #return df_clasificada.to_json(orient='records')


if __name__ == '__main__':

    resultados_json = procesar_df()


    print(resultados_json)
