# Codigos principales:

- simple_run.py
- change_date.py
- utils.py

## Simple_run.py

Codigo para hacer una ejecucion simple del codigo

Variables importantes:

- split_df_path: path a split_df (archivo que contiene a los usuarios, departamentos, funciones, roles y lugares de aplicacion de sus roles)
- resumen_df_path: path a resumen.csv (archivo con las asignaciones)
- X_weight: Peso que tendra el atributo, 1 valor por defecto

Salida: csv con los usuarios, roles asignados (resumen.csv), roles similares (apartir de usuarios similares) y roles encontrados (roles similares == roles asignados)

## Change_date.py

Codigo para cambiar la fecha del split.csv

Variables importantes:

- cutoff: Fecha que se busca obtener formato "YYYY-MM-DD"
- split_roles_path = path a split_df (archivo que contiene a los usuarios, departamentos, funciones, roles y lugares de aplicacion de sus roles)
- resumen_path : path a resumen.csv (archivo con las asignaciones)

## *IMPORTANTE**:

- Si no tienes el split_df puedes guardarlo en el results_with_threshold.py (linea 20, agrega lineas para guardar el df y despues de eso para el codigo)

- En caso de querer hacer una fecha 2024 o mas antigua, es necesario que hagas un merge entre los df de resumentes (si quieres hacer 2024 tienes que incluir 2025). Esto aplica tanto para  simple_run.py como el change_date

- En caso de querer ver mas a detalle los roles que encuentra y no tienes que ver la funcion roles_found de utils.py (Coloca breakpoints si estas en visual o usa prints o preguntale a copilot para que te entregue mas detalles)