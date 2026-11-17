# Hito 2: Especificación y Diseño Formal (MDGA). Texto completo extraído de d.pdf

              Universidad Tecnológica de Panamá

    FACULTAD DE INGENIERÍA DE SISTEMAS COMPUTACIONALES

        Departamento de Computación y Simulación de Sistemas




   Especificación y Diseño Formal de una Solución
     Inteligente para la Programación de Horarios
    Universitarios mediante un Algoritmo Genético
                Multi-Profundidad (MDGA)


Hito 2: Especificación y Diseño Formal de la Solución Inteligente




                              Integrantes

                   Alejandro Muñoz      8-993-2342
                   Liam Thompson        8-1015-2421
                   Ricardo Villarreal   8-1016-1180
Hito 2: Especificación y Diseño Formal – MDGA       Universidad Tecnológica de Panamá



                  Docente: BELIZ OSORIO, NICOLAS BENJAMIN




                             Fecha: 1 de octubre de 2026

                                                2
Hito 2: Especificación y Diseño Formal – MDGA                Universidad Tecnológica de Panamá




Índice

1. Introducción                                                                                 1

2. Metodología Formal Aplicada                                                                  2
   2.1. Descripción de la metodología . . . . . . . . . . . . . . . . . . . . . . . . .         2
   2.2. Justificación de la metodología . . . . . . . . . . . . . . . . . . . . . . . . .       4

3. Modelo Conceptual del Sistema                                                                4
   3.1. Modelo formal del problema . . . . . . . . . . . . . . . . . . . . . . . . . . .        5
   3.2. Representación de la solución . . . . . . . . . . . . . . . . . . . . . . . . .         5
   3.3. Función de aptitud . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      6

4. Arquitectura Propuesta                                                                       9
   4.1. Gestión de reglas . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    10
   4.2. Flujo de ejecución . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .     11

5. Componentes del Sistema                                                                     12

6. Flujo de Información                                                                        14

7. Mecanismos de Razonamiento                                                                  14
   7.1. Razonamiento basado en reglas . . . . . . . . . . . . . . . . . . . . . . . .          14
   7.2. Estrategia evolutiva . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .     16
   7.3. Selección por torneo . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .     17
   7.4. Cruce uniforme por evento . . . . . . . . . . . . . . . . . . . . . . . . . . .        17
   7.5. Mutación por reasignación . . . . . . . . . . . . . . . . . . . . . . . . . . . .      17
   7.6. Elitismo, reemplazo y terminación . . . . . . . . . . . . . . . . . . . . . . .        18

8. Fuentes de Conocimiento                                                                     18

9. Entradas y Salidas del Sistema                                                              19
   9.1. Especificación de entradas . . . . . . . . . . . . . . . . . . . . . . . . . . .       20
   9.2. Especificación de salidas . . . . . . . . . . . . . . . . . . . . . . . . . . . .      20

10. Interfaces con el Entorno                                                                  21

11. Métricas de Evaluación y Calidad                                                           22
    11.1. Calidad de la solución . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .   22
    11.2. Desempeño del algoritmo . . . . . . . . . . . . . . . . . . . . . . . . . . . .      23
    11.3. Calidad del sistema y de la explicación . . . . . . . . . . . . . . . . . . . . .    23

Referencias                                                                                    24




                                                i
Hito 2: Especificación y Diseño Formal – MDGA            Universidad Tecnológica de Panamá




1 Introducción

La generación de horarios universitarios consiste en asignar cursos, docentes, estudian-
tes, franjas horarias y espacios físicos de manera coordinada, procurando satisfacer las
restricciones propias de la institución. En términos prácticos, no basta con producir un ho-
rario completo: cada asignación debe ser compatible con la disponibilidad de los docentes,
la capacidad y disponibilidad de los salones, la estructura de los grupos y la posible coin-
cidencia de actividades para un mismo estudiante. Por esta razón, el problema se formula
como una tarea de optimización combinatoria en la que se distinguen restricciones du-
ras, cuyo incumplimiento produce soluciones no factibles, y restricciones blandas, cuyo
cumplimiento permite mejorar la calidad y conveniencia del horario.

En la Universidad Tecnológica de Panamá (UTP), la cantidad de cursos, estudiantes, do-
centes, aulas y franjas horarias involucradas incrementa significativamente el número de
combinaciones posibles. La dificultad aumenta todavía más cuando se consideran simultá-
neamente las relaciones entre cursos, secciones y estudiantes. Un procedimiento manual
o basado únicamente en reglas aisladas puede generar resultados válidos para una parte
del problema, pero resulta difícil de mantener cuando cambian los datos institucionales o
cuando se desea comparar muchas alternativas. En consecuencia, se requiere una estra-
tegia que permita explorar sistemáticamente diferentes configuraciones y medir de forma
uniforme sus ventajas y conflictos.

Los trabajos sobre programación de horarios han empleado algoritmos genéticos y otras
metaheurísticas para explorar este espacio de búsqueda y reducir progresivamente las
violaciones de restricciones. También se han estudiado estrategias híbridas y mecanis-
mos destinados a equilibrar la exploración de nuevas soluciones con la explotación de las
configuraciones que presentan mejores resultados [1, 2, 3, 4]. Estos antecedentes respal-
dan la utilización de una estrategia evolutiva como núcleo de optimización, siempre que la
representación del horario y la función de aptitud reflejen adecuadamente las característi-
cas del problema institucional.

Ante esta problemática, se plantea el uso de un algoritmo genético multi-profundidad (MD-
GA) para generar y evaluar diferentes configuraciones de horarios. El enfoque propuesto
separa la representación de las soluciones, la evaluación de las restricciones y los me-
canismos de evolución. De esta manera, el sistema puede priorizar la obtención de ho-
rarios factibles y, una vez reducidos los conflictos obligatorios, mejorar progresivamente
las condiciones blandas que determinan la calidad de la solución. Además, la arquitectura
contempla reglas configurables y un mecanismo de explicación que permite identificar las
causas de las penalizaciones obtenidas por cada horario.




                                                1
Hito 2: Especificación y Diseño Formal – MDGA             Universidad Tecnológica de Panamá




2 Metodología Formal Aplicada

2.1 Descripción de la metodología

El desarrollo del sistema se plantea mediante una metodología iterativa basada en el mo-
delo en espiral, adaptada a un problema de optimización mediante algoritmos genéticos.
Este enfoque permite construir y evaluar progresivamente el sistema, utilizando los resul-
tados de cada iteración para ajustar la representación de las soluciones, las funciones de
evaluación y los operadores evolutivos.

Los datos institucionales de la UTP constituyen la base del proceso de generación de
horarios. A partir de ellos se construye una población inicial de soluciones candidatas,
donde cada individuo representa una posible asignación de cursos, estudiantes, docentes,
aulas y franjas horarias. Las soluciones se evalúan mediante una función de aptitud que
considera el cumplimiento de las restricciones duras y la satisfacción de las restricciones
blandas.

El proceso evolutivo aplica mecanismos de selección, cruce y mutación para generar nue-
vas soluciones. La evaluación permite identificar conflictos y medir la calidad de los hora-
rios, mientras que los resultados obtenidos orientan el refinamiento de los parámetros y
componentes del algoritmo en las iteraciones siguientes.

                       Tabla 1: Fases de la metodología de desarrollo

 Fase                      Descripción

 Definición y modelado     Se identifican los datos, variables y restricciones necesarias
                           para representar el problema de generación de horarios.
 Inicialización            Se construye la población inicial de horarios candidatos a
                           partir de la información institucional disponible.
 Evaluación                Cada solución se evalúa mediante una función de aptitud
                           que determina el cumplimiento de las restricciones duras y la
                           calidad respecto a las restricciones blandas.
 Evolución                 Se aplican los operadores genéticos de selección, cruce y
                           mutación para generar nuevas soluciones y explorar el
                           espacio de búsqueda.
 Análisis y                Se analizan los resultados obtenidos y se ajustan los
 refinamiento              componentes del sistema para mejorar progresivamente la
                           calidad de las soluciones.


El proceso se repite hasta alcanzar un criterio de terminación establecido. De esta forma,
la metodología no considera la generación del horario como un proceso estrictamente se-
cuencial, sino como un ciclo de construcción, evaluación y mejora de soluciones (Figura 1).


                                                2
Hito 2: Especificación y Diseño Formal – MDGA                              Universidad Tecnológica de Panamá




                                      Datos institucionales
                                 grupos, docentes, salones, reglas


                                    Modelado del problema
                               eventos, paquetes (t, r), restricciones



                                       Población inicial P0
          Ciclo evolutivo


                                  Evaluación de aptitud F (X)



                   Selección                   Cruce                     Mutación


                                     Nueva población Pt+1

                                                                                        No: t ← t + 1


                                   ¿Criterio de terminación?


                                                  Sí

                                       Mejores k horarios

Figura 1: Ciclo de desarrollo del sistema basado en algoritmos genéticos. La flecha de retorno
representa el carácter iterativo del algoritmo.




                                                         3
Hito 2: Especificación y Diseño Formal – MDGA                         Universidad Tecnológica de Panamá




2.2 Justificación de la metodología

La elección de una metodología basada en el modelo en espiral resulta adecuada debido
a la naturaleza combinatoria del problema de generación de horarios universitarios. El
número de posibles asignaciones aumenta considerablemente a medida que se incorporan
cursos, estudiantes, docentes, aulas, períodos y restricciones, lo que hace inviable explorar
exhaustivamente todo el espacio de soluciones.

Los algoritmos genéticos abordan este problema mediante una búsqueda heurística basa-
da en una población de soluciones. En lugar de buscar directamente una solución óptima
por enumeración, el algoritmo evoluciona progresivamente las soluciones candidatas y
favorece aquellas con mejor desempeño según la función de aptitud.

El carácter iterativo del modelo en espiral permite, además, evaluar el comportamiento del
algoritmo y realizar ajustes durante el desarrollo. Esto es particularmente importante en
este sistema, ya que la definición de la función de aptitud, la representación de los horarios
y los operadores genéticos influyen significativamente en la capacidad del algoritmo para
encontrar soluciones factibles y de buena calidad.

Por tanto, la metodología seleccionada integra el proceso iterativo de desarrollo con el
proceso evolutivo propio de los algoritmos genéticos, permitiendo refinar el sistema pro-
gresivamente a partir de los resultados obtenidos durante su evaluación (Figura 2).


         Iteración                  Evaluación                Refinamiento                 Nueva iteración

                                                                        Nivel de desarrollo (modelo en espiral)


                                          cada iteración ejecuta y ajusta el algoritmo


                                                                                 Nivel del algoritmo genético

                                                                                                Nueva
         Población        Aptitud        Selección          Cruce            Mutación          población



Figura 2: Relación entre el modelo de desarrollo y el algoritmo genético: cada iteración del desarrollo
permite evaluar y ajustar el algoritmo.




3 Modelo Conceptual del Sistema

El modelo conceptual define los principales elementos que representan el problema de
generación de horarios y las relaciones entre ellos, independientemente de la implemen-
tación del sistema. Debido a que la solución emplea técnicas de computación evolutiva,
el modelo se centra en la representación del horario, la codificación de las soluciones y la


                                                     4
Hito 2: Especificación y Diseño Formal – MDGA           Universidad Tecnológica de Panamá



función utilizada para evaluar su calidad.


3.1 Modelo formal del problema

El problema se representa mediante la asignación de eventos académicos a paquetes
conformados por una franja horaria y una sala. Un paquete q se define como el par (t, r),
donde t representa el período de tiempo y r la sala asignada. Por su parte, un evento e
está compuesto por un docente l, una clase c y el conjunto S de estudiantes asociados.


                                         q = (t, r)                                   (1)



                                        e = (l, c, S)                                 (2)

La relación entre un evento y el paquete al que se asigna se representa mediante:


                                         p = (q, e)                                   (3)

De esta forma, un horario P está constituido por el conjunto de asignaciones que rela-
cionan cada evento académico con un paquete disponible. Esta representación permite
expresar el problema como una búsqueda de asignaciones que minimicen los conflictos y,
simultáneamente, mejoren la calidad general del horario.


3.2 Representación de la solución

Cada horario candidato se representa mediante un cromosoma compuesto por valores
enteros discretos. La estructura del cromosoma mantiene una correspondencia directa
con los eventos académicos, de manera que cada evento posee la información necesaria
para determinar su asignación (Figura 3).




                                                5
Hito 2: Especificación y Diseño Formal – MDGA                     Universidad Tecnológica de Panamá



                 Tabla 2: Estructura conceptual de la representación del horario

   Elemento              Tipo                 Descripción

   Tiempo                Entero               Identifica una de las franjas horarias
                                              disponibles durante la semana.
   Sala                  Entero               Identifica el espacio físico asignado al
                                              evento.
   Docente               Identificador        Docente responsable del evento;
                                              permanece fijo durante la búsqueda.
   Clase                 Identificador        Clase o curso asociado al evento;
                                              permanece fijo durante la búsqueda.
   Estudiantes           Conjunto             Estudiantes asociados al evento;
                                              permanece fijo durante la búsqueda.


La búsqueda evolutiva modifica únicamente los elementos relacionados con la asignación
del evento, principalmente el tiempo y la sala. Esto reduce el espacio de búsqueda y con-
serva la información académica que define cada evento.




Figura 3: Estructura del individuo (cromosoma): cada evento contiene un paquete variable q = (t, r)
y los campos fijos l, c y S.



3.3 Función de aptitud

La calidad de cada horario se determina mediante una función de aptitud formulada como
un problema de minimización. Esta función asigna una penalización a las soluciones en
función de las restricciones que incumplen:

                                                 ∑
                                      F (P ) =       wi Vi (P )                                 (4)
                                                 i


                                                 6
Hito 2: Especificación y Diseño Formal – MDGA                Universidad Tecnológica de Panamá



donde Vi (P ) representa el número de violaciones de la restricción i y wi corresponde al
peso asignado a dicha restricción. Una solución de mayor calidad presenta un menor valor
de F (P ).

Las restricciones se dividen en dos grupos. Las restricciones duras (HC) representan con-
diciones necesarias para obtener un horario factible, mientras que las restricciones blandas
(SC) permiten medir y mejorar la calidad de una solución que ya satisface las condiciones
fundamentales.
                     Tabla 3: Clasificación de las restricciones del sistema

   Tipo             Propósito                        Ejemplos

   Duras (HC)       Garantizar la factibilidad       Conflictos de docentes, conflictos de
                    del horario.                     clases, capacidad de las salas y
                                                     disponibilidad docente.
   Blandas (SC)     Mejorar la calidad y             Preferencias docentes, distribución
                    conveniencia del horario.        de carga, separación entre eventos y
                                                     conflictos de estudiantes.


Las restricciones duras reciben una penalización considerablemente mayor que las res-
tricciones blandas (wHC ≫ wSC ). De esta manera, el proceso de optimización prioriza
inicialmente la eliminación de conflictos que impiden obtener un horario factible y poste-
riormente busca mejorar las condiciones de calidad.

Evaluación multi-profundidad. En coherencia con el enfoque MDGA, las restricciones se
organizan en tres niveles de profundidad según la información que requieren para eva-
luarse. La penalización total es la suma de las contribuciones de los tres niveles (Tabla 4
y Figura 4).

                   Tabla 4: Niveles de profundidad de la función de aptitud

 Nivel              Información evaluada                     Restricciones típicas

 Superficial        Asignación individual de cada            Disponibilidad docente,
                    evento (t, r).                           capacidad de sala.
 Medio              Relaciones entre eventos de un           Conflictos de docentes y
                    mismo docente, clase o sala.             clases, distribución de carga,
                                                             separación entre eventos.
 Profundo           Asignación de estudiantes a las          Conflictos de estudiantes.
                    secciones.




                                                 7
Hito 2: Especificación y Diseño Formal – MDGA                                 Universidad Tecnológica de Panamá




                                                Datos académicos



                   Docentes                             Clases                             Estudiantes



                                        Eventos académicos         e = (l, c, S)


                                    Horario candidato   P = {(q, e)}, q = (t, r)


                                      Representación cromosómica (enteros)


                                                                       ∑
                                     Función de aptitud     F (P ) =       i wi Vi (P )




                Nivel superficial                   Nivel medio                           Nivel profundo



                                                 Penalización total


                                      Calidad del horario       (menor F = mejor)

Figura 4: Modelo conceptual del sistema de generación de horarios: los datos académicos son la
entrada y la función de aptitud transforma las violaciones de restricciones en una medida cuantita-
tiva de calidad.




                                                            8
Hito 2: Especificación y Diseño Formal – MDGA              Universidad Tecnológica de Panamá




4 Arquitectura Propuesta

El sistema se desarrolla bajo el patrón arquitectónico Modelo–Vista–Controlador (MVC),
debido a que permite separar la gestión de los datos, la lógica del sistema y la interac-
ción con el usuario. Esta separación facilita el mantenimiento y la evolución del sistema,
permitiendo modificar sus componentes sin generar un acoplamiento innecesario entre la
interfaz, la lógica de optimización y la persistencia de los datos.

La arquitectura está orientada a una aplicación web mediante la cual el usuario puede re-
gistrar y administrar la información necesaria para la generación de horarios. Entre estos
datos se incluyen docentes, salones, bloques horarios, grupos y las reglas lógicas que de-
terminan las condiciones que debe cumplir un horario. Toda esta información se almacena
en una base de datos MySQL.

Una característica importante de la arquitectura es que las restricciones pueden ser defi-
nidas y almacenadas como información del sistema. De esta manera, las reglas utilizadas
durante la evaluación de los horarios pueden configurarse sin modificar directamente el
código fuente del algoritmo. Estas reglas pueden representar condiciones duras o blandas
y estar asociadas a una determinada penalización, lo que permite adaptar el sistema a
diferentes necesidades de planificación.

Una vez cargada la información y configuradas las reglas, el usuario puede iniciar el proce-
so de generación de horarios y establecer parámetros como el número máximo de iteracio-
nes y el valor de k. Durante cada iteración, las soluciones se evalúan utilizando las reglas
almacenadas y se seleccionan los k individuos con mejor desempeño. Estos resultados
se almacenan en la base de datos junto con la información correspondiente a la iteración.




                                                9
Hito 2: Especificación y Diseño Formal – MDGA                               Universidad Tecnológica de Panamá



                               Tabla 5: Componentes de la arquitectura MVC

   Componente               Responsabilidad                        Funciones principales

   Modelo                   Gestionar los datos y las              Acceso a MySQL, gestión de
                            operaciones asociadas al               docentes, salones, bloques
                            dominio.                               horarios, grupos, reglas, horarios y
                                                                   resultados.
   Vista                    Proporcionar la interfaz de            Registro y consulta de información,
                            interacción con el usuario.            definición de reglas, configuración
                                                                   de parámetros y visualización de
                                                                   resultados.
   Controlador              Coordinar las solicitudes y            Validar entradas, gestionar las
                            la lógica del sistema.                 operaciones del modelo e iniciar el
                                                                   proceso de optimización.
   Motor de                 Generar y evaluar                      Crear horarios candidatos, aplicar
   optimización             soluciones.                            operadores evolutivos, evaluar las
                                                                   reglas y seleccionar las mejores
                                                                   soluciones.



           Usuario



     Aplicación web            datos y reglas                                 carga
                                                       MySQL                            Motor de optimización
  (Vista + Controlador)
                                                 datos académicos,                       generación y evaluación
      registro de datos,                          reglas, horarios,                       por reglas, operadores
    reglas y parámetros;
                                                     mejores k                          evolutivos, selección de k
   consulta de resultados       resultados                                  mejores k




                                       iniciar optimización (iteraciones máx., k)

Figura 5: Arquitectura general: los datos académicos y las reglas forman parte de la configuración
persistente y son utilizados posteriormente por el motor de optimización.



4.1 Gestión de reglas

Las restricciones del problema se representan mediante reglas lógicas que determinan si
una condición es violada por un horario. Cada regla puede almacenar información como
su nombre, tipo, condición lógica, peso o penalización y estado de activación.




                                                          10
Hito 2: Especificación y Diseño Formal – MDGA             Universidad Tecnológica de Panamá



                          Tabla 6: Información asociada a una regla

   Campo                Descripción

   Nombre               Identificador descriptivo de la regla.
   Tipo                 Indica si corresponde a una restricción dura o blanda.
   Condición            Expresión lógica utilizada para determinar si la regla es
                        violada.
   Peso                 Penalización asignada a la violación de la regla.
   Estado               Permite activar o desactivar la regla durante la generación del
                        horario.


Esta representación permite que el sistema sea configurable y adaptable. Por ejemplo,
una institución podría establecer como regla que un docente no puede tener dos clases
simultáneas, mientras que otra regla podría penalizar que un docente sea asignado fuera
de su horario preferido. Ambas condiciones pueden formar parte de la configuración del
problema y ser utilizadas por la función de aptitud durante la evaluación de los individuos.

Es importante distinguir entre los datos del problema y las reglas que determinan cómo se
evalúan esos datos. Los docentes, grupos, salones y horarios constituyen la información
sobre la cual se construyen las soluciones, mientras que las reglas determinan qué tan
adecuada es cada solución.


4.2 Flujo de ejecución

El funcionamiento general comienza con la carga de la información académica y la confi-
guración de las reglas mediante la aplicación web. Una vez almacenados estos elementos,
el usuario establece los parámetros de ejecución e inicia el proceso de optimización.

Durante cada iteración, el sistema genera y evalúa soluciones utilizando las reglas confi-
guradas. Las soluciones se ordenan de acuerdo con su función de aptitud y se conservan
los k mejores individuos. Estos individuos se almacenan en la base de datos junto con su
iteración y valor de aptitud, permitiendo mantener un historial de la evolución del proceso.




                                             11
Hito 2: Especificación y Diseño Formal – MDGA                   Universidad Tecnológica de Panamá



                                   Tabla 7: Flujo general del sistema

   Etapa                   Descripción

   Configuración           El usuario registra docentes, salones, bloques, grupos y
                           reglas lógicas.
   Almacenamiento          La información se valida y se almacena en MySQL.
   Parámetros              Se establece el número máximo de iteraciones y el valor de k.
   Generación              Se construye y evoluciona una población de horarios
                           candidatos.
   Evaluación              Cada individuo se evalúa mediante las reglas almacenadas y
                           la función de aptitud.
   Selección               Se identifican los k individuos con mejor desempeño.
   Persistencia            Los mejores individuos se almacenan asociados a su iteración
                           y valor de aptitud.
   Finalización            Al alcanzar el número máximo de iteraciones, los resultados
                           quedan disponibles para su consulta.



5 Componentes del Sistema

El sistema se organiza en cinco componentes que se corresponden con la arquitectura
descrita en la sección anterior y se relacionan según se muestra en la Figura 6.

                             Interfaz de usuario y módulos de comunicación

                                            Dashboards de
               Vistas gráficas                                          Adaptadores de API
                                             visualización




                  Núcleo de cómputo            resultados       Subsistema explicativo
                      motor MDGA                               justificación de los horarios




                  Repositorio de datos                           Pipelines de ingesta
                        MySQL                                archivos de la coordinación UTP

Figura 6: Diagrama de componentes del sistema: muestra la relación entre el núcleo de cómputo,
el subsistema explicativo, el repositorio MySQL y los procesos de ingesta que suministran los datos
al sistema.




                                                  12
Hito 2: Especificación y Diseño Formal – MDGA            Universidad Tecnológica de Panamá




                             Tabla 8: Componentes del sistema

  Componente                Descripción

  Repositorio de datos      Base de datos MySQL que almacena los datos
                            académicos (grupos, docentes, materias, salones y
                            bloques horarios), las reglas lógicas, los parámetros de
                            ejecución y los mejores horarios con su iteración y valor de
                            aptitud.
  Núcleo de cómputo         Motor de optimización basado en el MDGA: genera la
                            población inicial, evalúa la aptitud mediante las reglas
                            almacenadas, aplica los operadores evolutivos y
                            selecciona los k mejores individuos.
  Subsistema                Módulo que justifica cada horario generado: desglosa
  explicativo               F (P ) por regla, identifica los eventos que incumplen
                            restricciones y permite comparar los k mejores horarios.
  Pipelines de ingesta      Procesos que importan la información entregada por la
  automática de datos       coordinación de la UTP, la validan (existencia de docentes,
                            capacidad de salones, horas semanales coherentes) y la
                            cargan en el repositorio, generando los eventos del
                            problema.
  Interfaz de usuario y     Vistas gráficas para registrar datos y reglas, dashboards
  módulos de                de visualización del horario y de la evolución del algoritmo,
  comunicación              y adaptadores de API para comunicar el sistema con otras
                            aplicaciones.




                                            13
Hito 2: Especificación y Diseño Formal – MDGA                Universidad Tecnológica de Panamá




6 Flujo de Información

El flujo de información describe dinámicamente cómo los datos de entrada se transforman
paso a paso en conocimiento procesable y salidas operativas. La Tabla 9 resume las trans-
formaciones principales y la Figura 7 presenta el diagrama de secuencia temporal de una
solicitud de generación de horarios, desde que ingresa por la interfaz hasta que el motor
genera la conclusión (el mejor horario) y su explicación.

                 Tabla 9: Transformación de la información a lo largo del sistema

   Etapa                    Entrada                             Salida

   Ingesta                  Archivos de la coordinación.        Datos validados en
                                                                MySQL.
   Modelado                 Grupos, docentes, materias,         Conjunto de eventos
                            horas semanales.                    e = (l, c, S).
   Optimización             Eventos, reglas, parámetros.        Poblaciones de horarios y
                                                                sus aptitudes F (P ).
   Selección                Población evaluada.                 Mejores k horarios por
                                                                iteración.
   Explicación              Horario y reglas evaluadas.         Desglose de violaciones
                                                                Vi y pesos wi .
   Presentación             Horario y explicación.              Vistas, dashboards y
                                                                exportaciones.




7 Mecanismos de Razonamiento

El razonamiento del sistema combina dos mecanismos complementarios: la evaluación
basada en reglas, que determina qué tan adecuada es una solución, y un proceso evolu-
tivo, que utiliza esa evaluación para explorar el espacio de búsqueda y construir mejores
soluciones.


7.1 Razonamiento basado en reglas

Cada regla almacenada en el sistema (Tabla 6) es una condición lógica evaluada sobre
un horario candidato. Si la condición se cumple, la regla es violada y se acumula su pe-
                                   ∑
nalización wi . La aptitud F (P ) = i wi Vi (P ) constituye así la conclusión cuantitativa del
razonamiento, y el desglose por regla Vi (P ) constituye su explicación.




                                               14
Hito 2: Especificación y Diseño Formal – MDGA                                     Universidad Tecnológica de Panamá




                                                                                                                     Subsistema
     Usuario            Interfaz web           Controlador             MySQL                Motor MDGA
                                                                                                                     explicativo

        1: solicitar generación

                          2: enviar parámetros (Tmáx , k)

                                                    3: cargar datos y reglas

                                                    4: datos y reglas activas

                                                                5: iniciar optimización


                                                                        loop [mientras t < Tmáx ]
                                                                                   6: evaluar po-
                                                                                      blación (F )

                                                                            7: selección, cruce,
                                                                            mutación y elitismo


                                                                            8: guardar mejores k


                                                              9: mejor horario y aptitud

                                                                          10: solicitar explicación

                                                                                                      11: desglosar F (P )

                                                                                                     12: Vi y wi por regla

                                                                                13: explicación

                              14: horario + explicación

          15: visualización

Figura 7: Diagrama de secuencia de una solicitud de generación de horarios: la interfaz envía
los datos y parámetros al sistema, el motor ejecuta la optimización, se almacenan los mejores
resultados y finalmente se devuelve el horario junto con su explicación.




                                                              15
Hito 2: Especificación y Diseño Formal – MDGA                            Universidad Tecnológica de Panamá




7.2 Estrategia evolutiva

Se define una única estrategia evolutiva, con un pipeline claro y consistente con la re-
presentación discreta del horario y con la función de penalización. La estrategia combina
selección por torneo, cruce uniforme por evento, mutación por reasignación y elitismo de
los mejores k (Figura 8):



 P0 → Eval → Selecttorneo → Crossoveruniforme → Mutationreasignación → Elitismk → Pt+1


   Población                                                                           Mejores horarios
   inicial P0
                                                                                               Sí


                      No: t ← t + 1, Pt+1 es la nueva población actual                    ¿Criterio
                                                                                         de parada?




                                                                                           Nueva
   Evaluación       Selección          Cruce            Mutación            Elitismo
                                                                                          población
     F (X)          por torneo        uniforme        reasignación         mejores k
                                                                                            Pt+1

Figura 8: Pipeline evolutivo para la optimización del horario académico: cada generación pasa por
evaluación, selección, cruce, mutación y elitismo hasta formar la siguiente población, o detenerse
cuando se cumple el criterio establecido.


                           Tabla 10: Operadores de la estrategia evolutiva

   Etapa                Operador                         Función

   Inicialización       Población aleatoria             Generar soluciones candidatas.
   Evaluación           Función de aptitud              Penalizar las restricciones violadas.
   Selección            Torneo                           Elegir progenitores controlando la
                                                         presión selectiva.
   Cruce                Uniforme por evento             Combinar las asignaciones de los
                                                        progenitores.
   Mutación             Reasignación de                  Cambiar horario y/o salón de un evento.
                        evento
   Elitismo             Mejores k individuos            Preservar las mejores soluciones
                                                        encontradas.
   Reemplazo            Generacional                     Construir Pt+1 .
   Terminación          Iteraciones máximas              Detener la evolución.
                        o criterio de calidad




                                                      16
Hito 2: Especificación y Diseño Formal – MDGA                                  Universidad Tecnológica de Panamá



Nota terminológica. Esta estrategia no debe confundirse con las Evolution Strategies (ES),
familia específica de algoritmos asociada a esquemas (µ, λ) y (µ + λ) con mutaciones pa-
rametrizadas. Formalmente, se trata de un pipeline evolutivo basado en algoritmo genético
para la generación de horarios académicos.


7.3 Selección por torneo
                                              ∑
Dado que en la función F (X) =                    i wi Vi (X) un menor valor indica una mejor solución, la
selección por torneo resulta natural: se toma al azar un subconjunto T de τ individuos y se
elige el de menor aptitud,
                                              X ∗ = arg mín F (X).                                           (5)
                                                              X∈T

Este operador evita transformar la aptitud en probabilidades, como exigiría la ruleta, y
permite controlar la presión selectiva mediante el tamaño τ del torneo.


7.4 Cruce uniforme por evento

El cruce uniforme combina dos horarios padres para construir un nuevo horario, pero se
aplica a cada evento académico como una unidad completa. Cada evento contiene la asig-
nación que puede modificarse, formada por su bloque horario y su salón; por esta razón,
el operador debe transferir el evento completo desde uno de los padres al descendiente.

El procedimiento es sencillo. Para cada evento, el algoritmo elige aleatoriamente cuál de
los dos progenitores aportará su asignación. Así, algunos eventos del descendiente pue-
den provenir del primer horario y los restantes del segundo. Por ejemplo, si existen cuatro
eventos y el operador selecciona los eventos 1 y 3 del primer progenitor, mientras que
toma los eventos 2 y 4 del segundo, el nuevo horario conservará esas cuatro asignaciones
exactamente como fueron heredadas.

Esta forma de combinar las soluciones permite reunir partes favorables de horarios dife-
rentes sin separar los elementos que pertenecen a una misma asignación. En particular, se
evita producir una combinación artificial en la que el bloque horario de un progenitor quede
asociado al salón de otro. El resultado es una mezcla de las características de ambos pa-
dres que posteriormente será evaluada por la función de aptitud y, cuando corresponda,
modificada mediante la mutación (Figura 9).


7.5 Mutación por reasignación

Cada evento se muta con probabilidad pm reasignando su paquete, ya sea completo o de
forma parcial:

                 (ti , ri ) → (t′i , ri′ ),        (ti , ri ) → (t′i , ri ),    (ti , ri ) → (ti , ri′ ).    (6)


                                                             17
Hito 2: Especificación y Diseño Formal – MDGA                      Universidad Tecnológica de Panamá



De este modo se exploran directamente nuevas combinaciones de horario y salón, sin
alterar los campos fijos l, c y S.

                    Progenitor X      X1           X2             X3            X4

                    Progenitor Y       Y1           Y2            Y3             Y4

                        Máscara      m1 = 1       m2 = 0       m3 = 1          m4 = 0


                       Cruce: Z       X1            Y2            X3             Y4
                                                             evento 3 mutado

                    Mutación: Z ′     X1            Y2         (t′3 , r3 )       Y4

Figura 9: Ejemplo de cruce uniforme por evento y de mutación por reasignación parcial (se modifica
solo el tiempo del evento 3).



7.6 Elitismo, reemplazo y terminación

El elitismo conserva explícitamente los k mejores individuos de cada generación, en co-
herencia con el almacenamiento de los mejores k horarios definido en la arquitectura:

                              Et = Bestk (Pt ),          Pt+1 = Et ∪ Ct ,                        (7)

donde Ct es el conjunto de N − k descendientes, evaluados tras el cruce y la mutación,
y N es el tamaño de la población. Esto garantiza que las mejores soluciones encontradas
no se pierdan por efecto del cruce o la mutación. La evolución se detiene al alcanzar el
número máximo de iteraciones o un criterio de calidad previamente establecido.



8 Fuentes de Conocimiento

La fuente de conocimiento principal es la información suministrada por la coordinación de
la UTP, a partir de la cual se construyen los eventos y el espacio de búsqueda del algo-
ritmo. Adicionalmente, el sistema incorpora conocimiento normativo y de configuración,
expresado mediante reglas lógicas y parámetros.




                                                  18
Hito 2: Especificación y Diseño Formal – MDGA               Universidad Tecnológica de Panamá



                         Tabla 11: Fuentes de conocimiento del sistema

   Fuente                   Información                        Uso en el modelo

   Coordinación de la       Cantidad de grupos,                Define los eventos
   UTP                      profesores y materias.             e = (l, c, S).
   Coordinación de la       Cantidad de horas semanales        Determina cuántos
   UTP                      por materia.                       eventos genera cada
                                                               materia.
   Coordinación de la       Discretización del espacio         Define el dominio de t (60
   UTP                      temporal.                          franjas, de lunes 7:00 a
                                                               sábado 16:00).
   Coordinación de la       Lista de salones disponibles.      Define el dominio de r y
   UTP                                                         las capacidades.
   Usuario del sistema      Reglas lógicas: tipo,              Definen la función de
                            condición, peso y estado.          aptitud.
   Usuario del sistema      Parámetros de ejecución.           Controlan el algoritmo
                                                               (iteraciones máximas, k,
                                                               etc.).



9 Entradas y Salidas del Sistema

Esta sección especifica la interfaz de entrada y salida (I/O) de la aplicación.




                                              19
Hito 2: Especificación y Diseño Formal – MDGA               Universidad Tecnológica de Panamá




9.1 Especificación de entradas

                                Tabla 12: Entradas del sistema

   Entrada               Contenido                                Medio / validación

   Grupos                Identificador, materia asociada y        Archivo o formulario; el
                         conjunto de estudiantes.                 identificador debe ser
                                                                  único.
   Docentes              Identificador y disponibilidad.          Archivo o formulario.
   Materias              Código y horas semanales.                Horas enteras mayores
                                                                  que cero.
   Franjas horarias      Discretización del tiempo (60            Configuración del
                         franjas).                                sistema.
   Salones               Identificador y capacidad.               Capacidad entera
                                                                  positiva.
   Reglas lógicas        Nombre, tipo (HC/SC), condición,         Formulario web.
                         peso y estado.
   Parámetros de         Iteraciones máximas, k, tamaño de        Formulario web; valores
   ejecución             población N , tamaño de torneo τ ,       positivos y k < N .
                         probabilidad de cruce pc y de
                         mutación pm .


9.2 Especificación de salidas

                                 Tabla 13: Salidas del sistema

   Salida                    Contenido                              Medio

   Mejores k horarios        Asignación (t, r) de cada evento,      MySQL y vista web.
                             con su iteración y aptitud F (P ).
   Horario por entidad       Vista del horario por grupo,           Vista web,
                             docente o salón.                       exportación.
   Desglose de               Valores Vi (P ) y penalización por     Subsistema
   violaciones               regla.                                 explicativo.
   Historial de evolución    Mejor aptitud por iteración.           Dashboard.
   Reportes exportables      Horarios y resultados en formato       Archivos y API.
                             de intercambio.




                                              20
Hito 2: Especificación y Diseño Formal – MDGA                              Universidad Tecnológica de Panamá




10 Interfaces con el Entorno

Se definen los mecanismos de integración del sistema inteligente con el mundo exterior,
incluyendo sistemas legados, redes y usuarios humanos (Figura 10 y Tabla 14).


     Coordinación UTP                                                                           Usuarios humanos
                                impor                                                            coordinación, do-
       archivos de da-               tación                                       S
                                                                             HTTP
       tos académicos                                                                           centes y estudiantes
                                                Sistema inteligente
                                                   aplicación web,
                                                    motor MDGA
                                                      y MySQL
     Sistemas legados                                                      API /
                                        EST                                        expor        Sistemas externos
     sistemas institucio-        API R                                                  t.
                                                                                               consumidores de la API
       nales existentes

                                              Red institucional (TCP/IP)

Figura 10: Interfaces del sistema con el entorno: se muestran las entradas procedentes de la coor-
dinación y los sistemas legados, la interacción de los usuarios mediante la aplicación web y las
salidas destinadas a sistemas externos.


                            Tabla 14: Mecanismos de integración con el entorno

   Elemento                   Mecanismo de integración                                     Protocolo / formato

   Coordinación de            Importación de los archivos de datos                         Archivos tabulares
   la UTP                     académicos mediante los pipelines de                         (CSV, XLSX).
                              ingesta.
   Sistemas legados           Adaptadores de API para intercambiar                         API REST, JSON.
                              datos académicos y horarios sin
                              modificar los sistemas existentes.
   Usuarios                   Aplicación web con vistas gráficas y                         HTTPS desde
   humanos                    dashboards para registrar datos,                             navegador.
                              configurar reglas, ejecutar el proceso
                              y consultar resultados.
   Red e                      El sistema se despliega sobre la red                         TCP/IP, conexión
   infraestructura            institucional; la aplicación accede al                       MySQL.
                              repositorio de datos.


Al tratarse de un sistema de software, no se requiere interacción directa con dispositivos
físicos; las redes físicas intervienen únicamente como medio de comunicación entre los
usuarios, el servidor de aplicación y el repositorio de datos.




                                                        21
Hito 2: Especificación y Diseño Formal – MDGA              Universidad Tecnológica de Panamá




11 Métricas de Evaluación y Calidad

Las métricas de evaluación se derivan del modelo del sistema: la función de aptitud F (P ) =
∑
  i wi Vi (P ), la clasificación de restricciones en duras (HC) y blandas (SC) y el proceso
evolutivo. Se agrupan en tres categorías.


11.1 Calidad de la solución

                           Tabla 15: Métricas de calidad del horario

   Métrica                     Definición                               Objetivo
                                        ∑
   Aptitud total               F (P ) = i wi Vi (P )                    Minimizar.
                                         ∑
   Violaciones duras           H(P ) = i∈HC Vi (P ). El horario es      H(P ) = 0.
                               factible si H(P ) = 0.
                                        ∑
   Penalización blanda         S(P ) = j∈SC wj Vj (P )                  Minimizar.
   Violaciones por regla       Vi (P ) para cada regla activa.          Identificar
                                                                        conflictos.
   Conflictos de               Número de estudiantes con                Minimizar.
   estudiantes                 eventos simultáneos.
                                1 ∑     |Se |
   Ocupación de salas                         , con |Se | estudiantes   Menor o igual a 1.
                               E e cap(re )
                               del evento y cap(re ) capacidad de
                               su sala.
   Equilibrio de carga         Desviación estándar de las horas         Minimizar.
   docente                     diarias asignadas a cada docente.




                                              22
Hito 2: Especificación y Diseño Formal – MDGA                Universidad Tecnológica de Panamá




11.2 Desempeño del algoritmo

                     Tabla 16: Métricas de desempeño del algoritmo evolutivo

   Métrica                      Definición                               Objetivo

   Tasa de factibilidad         Rf = Nf /Nc , con Nf corridas que        Maximizar.
                                obtienen H(P ) = 0 de Nc corridas
                                independientes.
   Generaciones hasta           Gf = mín{t : H(mejort ) = 0}             Minimizar.
   factibilidad
   Mejora relativa              ∆F = (F0∗ − FT∗ )/F0∗ , con F0∗ y FT∗    Maximizar.
                                la mejor aptitud inicial y final.
   Curva de convergencia        Mejor aptitud por iteración t.           Descenso
                                                                         estable.
                                           2     ∑
   Diversidad poblacional       Dt =                     d(Xa , Xb ),    Evitar
                                       N (N − 1) a<b
                                                                         convergencia
                                con d la fracción de eventos con
                                                                         prematura.
                                distinto paquete (t, r).
   Tiempo de ejecución          Tiempo total hasta la finalización.      Minimizar.


11.3 Calidad del sistema y de la explicación

                            Tabla 17: Métricas de calidad del sistema

   Métrica                      Definición                               Objetivo

   Cobertura explicativa        Proporción de violaciones de P que       Cercana al
                                el subsistema explicativo asocia a       100 %.
                                una regla y a los eventos
                                involucrados.
   Configurabilidad             Cambio de reglas, pesos y estado         Cumplida.
                                sin modificar el código del
                                algoritmo.
   Trazabilidad                 Los mejores k individuos se              Cumplida.
                                conservan con su iteración y
                                aptitud.


Protocolo de evaluación. Debido al carácter estocástico del algoritmo, cada configuración
se ejecuta en varias corridas independientes (por ejemplo, 30) y se reportan la media,
la desviación estándar y el mejor resultado de cada métrica. Los valores obtenidos se
emplean en el ciclo de refinamiento descrito en la metodología para ajustar parámetros y
pesos.

                                               23
Hito 2: Especificación y Diseño Formal – MDGA             Universidad Tecnológica de Panamá




Referencias

 [1] A. Alkan and E. Özcan, “Memetic algorithms for timetabling,” in Proc. 2003 Con-
     gress on Evolutionary Computation (CEC 2003), vol. 3, pp. 1796–1802, 2003, doi:
     10.1109/CEC.2003.1299890.

 [2] R. P. Badoni et al., “An exploration and exploitation-based metaheuristic approach for
     university course timetabling problems,” Axioms, vol. 12, no. 8, Art. no. 720, 2023, doi:
     10.3390/axioms12080720.

 [3] B. S. González López, R. A. García Hernández, and Y. Ledeneva, “Personal course
     timetabling for university students based on genetic algorithm,” International Journal
     of Combinatorial Optimization Problems and Informatics, vol. 12, no. 3, pp. 32–49,
     2021, doi: 10.61467/2007.1558.2021.v12i3.237.

 [4] A. A. Gozali, B. Kurniawan, W. Weng, and S. Fujimura, “Solving university course
     timetabling problem using localized island model genetic algorithm with dual dynamic
     migration policy,” IEEJ Transactions on Electrical and Electronic Engineering, vol. 15,
     no. 3, pp. 389–400, 2020, doi: 10.1002/tee.23067.

 [5] B. Kitchenham and S. Charters, Guidelines for Performing Systematic Literature
     Reviews in Software Engineering, EBSE Technical Report EBSE-2007-01, ver-
     sion 2.3, Keele University and Durham University, 2007. [Online]. Available: https:
     //homepages.dcc.ufmg.br/~figueiredo/disciplinas/papers/guidelines-kitchenham.pdf.
     Accessed: Sep. 8, 2026.

 [6] T. Müller, H. Rudová, and Z. Müllerová, “Real-world university course timetabling at
     the International Timetabling Competition 2019,” Journal of Scheduling, vol. 28, pp.
     247–267, 2025, doi: 10.1007/s10951-023-00801-w.

 [7] IJCOPI, “Indexing/abstracting,” [Online]. Available: https://ijcopi.org/ojs/indexing. Ac-
     cessed: Sep. 8, 2026.

 [8] ITC 2019, “Data format,” [Online]. Available: https://www.itc2019.org/format. Acces-
     sed: Sep. 8, 2026.




                                             24
