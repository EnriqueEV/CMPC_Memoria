Primera iteracion toma encuenta estos atributos para la similitud los siguientes datos:
- departamento
- funcion 
- roles sin sucursal y con para la similitud (se le da mayor pesos para el caso de que sea en la misma sucursal)



Codificacion:


- Departamento y funcion codificados via one hot
- Roles codificados via multi hot. Implementacion en especifico se hace de forma que se codifica solo roles y roles+lugares por separado, para mantener los casos de usuarios que compartan el mismo rol pero aplicado a otro lugar (aunque usen el rol en distintos lugares sigue siendo el mismo rol por lo que existe algun parecido entre los usuarios, utilizando solo multi hot para roles+lugares estos usarios no tienen ningun match, por lo que se tiene que aplicar un multi hot a solo los roles)

Consideraciones:

- Para agregar pesos a una caracteristica en especifico se tiene que multiplicar la codificacion de esta por un valor a seleccionar. Por ejemplo si es que el departamento es la caracteristica mas importante se multiplica esta por 10, las funciones por 5 y roles se quedan en 1. Lo que hace que la importancia siga esta orden: Departamento>funciones>roles\
