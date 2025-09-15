# Prototipo

## Marco general


El presente proyecto se enfoca en el desarrollo de una aplicación web cuyo propósito es ofrecer un sistema que permita al equipo de gestión de accesos realizar un análisis detallado del estado actual de la empresa, con el objetivo de identificar posibles asignaciones de permisos que los trabajadores puedan necesitar. Esta tarea se llevará a cabo estimando la similitud entre los trabajadores de la empresa, con el fin de detectar qué roles le faltan a un trabajador basándose en sus compañeros más parecidos. Posteriormente, todos estos roles candidatos generados por el análisis deberán ser clasificados para determinar cuáles de ellos constituyen recomendaciones útiles, que finalmente serán presentadas a través de una interfaz web.

Un aspecto clave del proyecto es la funcionalidad de poder ajustar las recomendaciones generadas. Esto se realizará utilizando el feedback proporcionado por el equipo de gestión de accesos, para determinar qué tipo de recomendaciones resultan ser más útiles y cuáles no.

### Hitos principales del proyecto

1. Definición de la problemática: El equipo identificó un problema relacionado con la elevada cantidad de solicitudes de asignación de permisos que recibía el equipo de gestión de accesos. Esto generó un enfoque centrado en la predicción de futuras solicitudes, con el objetivo de asignar roles antes de que los trabajadores tengan la necesidad de solicitarlos.
2. Investigación y análisis de la información proporcionada: Se realizó un estudio sobre los datos proporcionados por la empresa para determinar la mejor forma de abordar la problemática encontrada. Este trabajo se llevó a cabo en conjunto con la contraparte, que nos brindó la capacitación necesaria para comprender qué representaba cada uno de los datos.
3. Procesamiento de datos: Se realizó un filtrado de la información para quedarnos únicamente con la información relevante de los trabajadores.
4. Representación vectorial de los trabajadores: Se utilizó la información relevante de los usuarios para representarlos en un vector multidimensional.
5. Cálculo de la similitud de los trabajadores: Se desarrolló una herramienta que utiliza la representación vectorial de los trabajadores para determinar la similitud entre estos.
6. Generación de posibles roles a asignar: Se utilizó la similitud entre los trabajadores para poder generar múltiples candidatos de roles a asignar, basándose en los usuarios más parecidos.
7. Validación de roles candidatos: Se utilizó datos de asignaciones realizadas por el equipo de gestión de accesos para comprobar si estas se encuentran dentro de los candidatos generados, validando así la calidad de los resultados.
8. Clasificación de roles candidatos: Se realizó una clasificación de todos los roles candidatos generados a partir de usuarios similares, con el fin de poder determinar cuáles deben ser recomendados y cuáles no.
9. Desarrollo del prototipo: Se implementó un prototipo de la aplicación web, que permite visualizar de manera interactiva los roles recomendados.

### Revisión de requerimientos

En la sección 2 del presente informe, se detallan los requisitos funcionales y no funcionales.

 A continuación, se presentará la revisión de cada uno de ellos en base a lo desarrollado por el equipo

- **RF1**: El sistema actual permite la subida de archivos con los datos extraídos de la plataforma SAP. El formato de estos puede ser *.xlsx* o *.csv*.
- **RF2**: El sistema actual permite generar una predicción amplia de distintos posibles permisos que el trabajador necesite en base a otros usuarios similares.
- **RF3**: El sistema actual permite clasificar los múltiples posibles roles a asignar para determinar cuáles de estos deben ser recomendados o no, incluyendo la funcionalidad de que, a partir del feedback proporcionado, se vaya ajustando esta clasificación para generar mejores recomendaciones.
- **RF4**: El sistema cuenta con una interfaz intuitiva que permite la visualización de las recomendaciones.
- **Requisitos no funcionales**: Para los requisitos no funcionales, el sistema fue desarrollado para cumplir cada uno de ellos, permitiendo el análisis de grandes volúmenes de datos y dando la opción de poder reentrenar el sistema, todo esto a través de una interfaz intuitiva y segura.


### Entorno de Soporte y Desarrollo

El prototipo desarrollado utiliza las distintas herramientas y tecnologías mencionadas en la sección *2.4*.


## Revisión del Prototipo

El prototipo desarrollado permite obtener de manera preliminar los posibles roles a asignar, generados a partir de la similitud entre los usuarios. Este sistema permite utilizar distintos algoritmos para el cálculo de la similitud y modificar el criterio utilizado para determinar qué usuarios se consideran similares. Adicionalmente, cuenta con la funcionalidad de comprobar la calidad de los resultados obtenidos, utilizando asignaciones realizadas por el equipo de gestión de accesos con posterioridad a la fecha en que se recibieron los datos iniciales.

### Contexto general del prototipo

El prototipo desarrollado tiene como objetivo principal reducir las solicitudes que recibe el equipo de gestión de accesos SAP de la empresa CMPC. Una de las formas de solucionar esta problemática es anticiparse a estas solicitudes. Para ello, el sistema utiliza datos extraídos directamente de la plataforma SAP de la empresa, lo que permite identificar posibles permisos a asignar que los trabajadores puedan necesitar.

El sistema proporciona al equipo de gestión de accesos la funcionalidad de poder ingresar los datos de la plataforma SAP para poder realizar un análisis exhaustivo. A través de una interfaz interactiva, los miembros del equipo pueden ver las recomendaciones generadas para los distintos trabajadores de la empresa y, adicionalmente, evaluar cada una de ellas con el fin de mejorar el funcionamiento general de la aplicación.

Esta implementación permitirá que se puedan tomar decisiones de manera ágil para asignar permisos a los usuarios, dándole al equipo la posibilidad de anticiparse a las múltiples solicitudes de los trabajadores de la empresa.

### Esquema general de Componentes del Prototipo

 A continuación, se presentan los componentes presentes dentro del prototipo desarrollado:

- Representación vectorial de los trabajadores
- Calculo de la similitud entre los trabajadores
- Obtención de potenciales roles a aplicar

### Descripción de componentes


Representación vectorial de los trabajadores:

- **General**: Permite representar a los trabajadores mediante vectores multidimensionales, utilizando sus atributos principales.
- **Implementación**: A partir de los datos de departamento, funciones y roles de los trabajadores, se realiza una codificación binaria de estos atributos para representarlos en múltiples dimensiones.

Cálculo de la similitud entre los trabajadores:

- **General**: Permite determinar qué tan parecidos son los trabajadores entre sí.
- **Implementación**: Utilizando la representación vectorial de los trabajadores, se aplican distintos algoritmos que calculan la similitud entre vectores, con el objetivo de obtener la similitud entre distintos trabajadores.

Obtención de potenciales roles a aplicar:

- **General**: Permite obtener posibles candidatos de roles a asignar, basándose en trabajadores similares.
- **Implementación**: Utilizando la similitud entre los trabajadores de la empresa, se comparan los permisos de aquellos que cumplen un criterio mínimo de similitud, con el fin de encontrar los permisos faltantes.





## Verificación y Validación

En el desarrollo de un sistema en el cual se busca realizar recomendaciones que resulten de utilidad, es fundamental garantizar la calidad de estas.

### Verificación

La verificación realizada sobre el sistema se centró principalmente en comprobar que no se perdiera ni se modificara información relevante de los trabajadores durante el proceso de codificación.

Para lograrlo, se revisaron exhaustivamente los datos después de cada proceso realizado para la codificación de estos. En la primera iteración, se buscó principalmente que se integraran correctamente los distintos archivos que contenían la información de los trabajadores y de los roles que estos tenían asignados. Posteriormente, se realizó una segunda iteración, en la que se realizó un cambio de formato sobre la información obtenida.

Los resultados mostraron que, en la primera iteración, se guardaban de manera correcta los múltiples roles que tenían los trabajadores. En la segunda, se detectaron algunos casos atípicos en los que ciertos roles no tenían especificado un lugar de aplicación. Por ello, se consultó al equipo de gestión de accesos y se llegó a la decisión de que estos no eran relevantes, por lo que no formarán parte de nuestro análisis.


### Validación


La fase de validación se centró en confirmar que el sistema desarrollado generara roles que efectivamente el trabajador necesitaba.



A continuación, se presentan los puntos relevantes que se abordaron en el proceso de validación:

- **Comparación con asignaciones reales**: Se utilizaron asignaciones de roles realizadas posteriormente a la obtención de los datos iniciales de la empresa, con la finalidad de comprobar si el sistema era capaz de identificar estos roles utilizando la similitud entre trabajadores. Este proceso ayudó a comprobar que el enfoque centrado en similitud efectivamente era capaz de encontrar potenciales roles a asignar.


### Plan de Testing

El plan de testing se centra en los siguientes puntos:

- **Pruebas internas**: En una primera etapa, se realizaron pruebas utilizando asignaciones realizadas por el propio equipo de gestión de accesos. Estas pruebas permitieron validar la metodología planteada para la resolución de la problemática.
- **Pruebas con el equipo de gestión de accesos**: Una vez clasificados los permisos, se solicitará al equipo de gestión de accesos que evalúe estas recomendaciones, con la finalidad de utilizar su feedback para así poder ajustar y mejorar el modelo.

### Análisis Critico y evaluación de riesgos

En esta sección se detallan algunos de los riesgos críticos identificados y las medidas implementadas para mitigarlos:

1. **Recomendación de roles incorrecta**:
    - **Impacto**: Si el programa genera constantemente recomendaciones incorrectas, puede hacer que el sistema pierda toda su utilidad.
    - **Medidas de mitigación:** Se implementó un sistema de recolección de feedback para que, en estos casos, se pueda reajustar el modelo y mejorar los resultados, o bien descartar el modelo actual y entrenar uno nuevo con los datos recolectados.



