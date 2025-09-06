# Modulos relaciones de usuarios

## Pasos para la implementacion (sujeto a cambios)

1. [x] Creacion de vectores de usuario 04/09
2. [ ] Similitud entre vectores inicial (forma manual)
3. [ ] Entrenandiento de GNN utilizando la similitud de vectores precalculada
3. [ ] Comparacion de resultados con roles asignados entre el periodo de Junio - Septiembre

## Concideraciones

### Paso 1

Primera iteracion toma encuenta el departamento para la similitud los siguientes datos:
- departamento
- funcion 
- roles sin sucursal y con para la similitud (se le da mayor pesos para el caso de que sea en la misma sucursal)

Para el caso de roles tambien se puede analizar los siguientes mas factores como el historial de uso (tenemos acceso a eso recientemente), nivel de privilegios (03/09 es una teoria, se tiene que preguntar) y los otros 2 digitos que todavia no se sabe que son (ver roles_teoria.md). Probar funcionamiento con la primera iteracion, en caso querer mejorar los resultado tambien conciderar las otras metricas mencionadas.


- Departamento y funcion codificados via one hot
- Roles codificados via multi hot. Implementacion en especifico se hace de forma que se codifica solo roles y roles+lugares por separado, para mantener los casos de usuarios que compartan el mismo rol pero aplicado a otro lugar (aunque usen el rol en distintos lugares sigue siendo el mismo rol por lo que existe algun parecido entre los usuarios, utilizando solo multi hot para roles+lugares estos usarios no tienen ningun match, por lo que se tiene que aplicar un multi hot a solo los roles)
- Para agregar pesos a una caracteristica en especifico se tiene que multiplicar la codificacion de esta por un valor a seleccionar. Por ejemplo si es que el departamento es la caracteristica mas importante se multiplica esta por 10, las funciones por 5 y roles se quedan en 1. Lo que hace que la importancia siga esta orden: Departamento>funciones>roles\


