#!/bin/bash

for numPresupuesto in {1..14}
do
    echo "Ejecutando df_totales.py con el valor $numPresupuesto"
    python df_totales.py $numPresupuesto
done

