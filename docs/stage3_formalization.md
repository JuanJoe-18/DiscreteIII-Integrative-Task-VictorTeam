# ResumeLens — Etapa 3: Reconocimiento de Patrones de Cualificación con Autómatas Finitos

## 1. Introducción y Objetivo de la Etapa 3

En el flujo de **ResumeLens**, la Etapa 3 constituye el **Motor de Clasificación y Lógica Formal**. Su objetivo es recibir la secuencia de competencias técnicas normalizadas y ordenadas canónicamente (generadas por la Etapa 2 de Transductores Finitos) y determinar formalmente si el candidato cumple con el patrón de cualificación requerido para uno o más perfiles profesionales.

La clasificación no es un ranking heurístico ni un juicio subjetivo de contratación: **es un reconocimiento estricto de pertenencia a un lenguaje regular formal** definido sobre el alfabeto de cualificaciones de cada perfil.

---

## 2. Definición de los Cuatro Perfiles Profesionales

El sistema soporta cuatro perfiles de la industria tecnológica (dos de Ingeniería de Software y dos de Inteligencia Artificial / Datos):

| # | Perfil Profesional | Área de Dominio | Orden Canónico de Categorías |
|---|---|---|---|
| **1** | **Full Stack Developer** *(Predefinido)* | Software Engineering | $\text{Frontend} \to \text{Backend} \to \text{Database} \to \text{Version Control}$ |
| **2** | **Machine Learning Engineer** *(Predefinido)* | AI / Data | $\text{Language} \to \text{Data Processing} \to \text{ML Framework} \to \text{Database} \to \text{Version Control}$ |
| **3** | **Cloud & DevOps Engineer** *(Propuesto)* | Software Engineering | $\text{Scripting/OS} \to \text{CI/CD} \to \text{Containers} \to \text{Cloud/IaC} \to \text{Version Control}$ |
| **4** | **Data Scientist** *(Propuesto)* | AI / Data | $\text{Language} \to \text{Data Analysis/Stats} \to \text{Data Visualization} \to \text{Machine Learning} \to \text{Version Control}$ |

---

## 3. Justificación del Modelo Computacional: Autómatas Finitos Deterministas (DFA)

Para modelar el reconocimiento de cada perfil se utiliza un **Autómata Finito Determinista (DFA)**:
$$\mathcal{M} = (Q, \Sigma, \delta, q_0, F)$$

### Razones Teóricas y de Diseño:
1. **Garantía del Orden Canónico:** La Etapa 2 clasifica y agrupa los tokens normalizados en un orden canónico específico por categoría. Por lo tanto, el lenguaje aceptado por el autómata debe satisfacer una estructura secuencial estricta:
   $$L(\mathcal{M}) = C_1^+ \cdot C_2^+ \cdots C_k^+$$
   donde cada $C_j$ representa el conjunto de tokens de la categoría $j$, y $C_j^+$ denota que el candidato debe poseer **al menos una habilidad obligatoria** de dicha categoría, permitiendo múltiples habilidades de la misma mediante bucles sobre sí mismo (*self-loops*).
2. **Determinismo y Complejidad Óptima:** Dado que cada símbolo de entrada produce exactamente una transición definida hacia un único estado siguiente, el autómata no requiere retroceso (*backtracking*) ni cálculo de clausuras $\epsilon$. La evaluación se ejecuta en tiempo $O(n)$, donde $n$ es la cantidad de competencias extraídas.
3. **Manejo Estricto de Errores con Estado Trampa ($q_{trap}$):** Cualquier violación de orden (por ejemplo, presentar control de versiones antes de base de datos) o la aparición de símbolos incompatibles conduce deterministamente a un estado trampa/muerto (*dead state*) no aceptor, del cual no es posible salir.

---

## 4. Formalización Matemática de los Cuatro Autómatas (5-Tuplas)

---

### 4.1. Perfil 1: Full Stack Developer ($\mathcal{M}_{FS}$)

#### 5-Tupla:
$$\mathcal{M}_{FS} = (Q_{FS}, \Sigma_{FS}, \delta_{FS}, q_0, F_{FS})$$

#### 1. Conjunto de Estados $Q_{FS}$:
- $q_0$: Estado inicial. Ninguna competencia validada.
- $q_{fe}$: Competencia de **Frontend** validada ($\ge 1$ tecnología frontend).
- $q_{be}$: Competencia de **Backend** validada ($\ge 1$ tecnología backend posterior a frontend).
- $q_{db}$: Competencia de **Base de Datos** validada ($\ge 1$ tecnología de base de datos posterior a backend).
- $q_{acc}$: **Aceptado.** Competencia de **Control de Versiones** validada ($\ge 1$ tecnología VCS posterior a base de datos).
- $q_{trap}$: Estado de rechazo / trampa (orden inválido o token no perteneciente).

$$Q_{FS} = \{q_0, q_{fe}, q_{be}, q_{db}, q_{acc}, q_{trap}\}$$

#### 2. Alfabeto de Entrada $\Sigma_{FS}$:
El alfabeto está particionado en 4 categorías disjuntas:
- $C_{FE} = \{\text{JAVASCRIPT}, \text{TYPESCRIPT}, \text{REACT}, \text{ANGULAR}, \text{VUE}\}$
- $C_{BE} = \{\text{NODE\_JS}, \text{DJANGO}, \text{SPRING\_BOOT}, \text{EXPRESS}, \text{FASTAPI}\}$
- $C_{DB} = \{\text{POSTGRESQL}, \text{MONGODB}, \text{MYSQL}, \text{REDIS}, \text{SQL}\}$
- $C_{VCS} = \{\text{GIT}, \text{GITHUB}, \text{GITLAB}\}$

$$\Sigma_{FS} = C_{FE} \cup C_{BE} \cup C_{DB} \cup C_{VCS}$$

#### 3. Estado Inicial:
$$q_0$$

#### 4. Conjunto de Estados de Aceptación:
$$F_{FS} = \{q_{acc}\}$$

#### 5. Función de Transición $\delta_{FS} : Q_{FS} \times \Sigma_{FS} \to Q_{FS}$:

| Estado Actual ($q$) | Entrada $s \in C_{FE}$ | Entrada $s \in C_{BE}$ | Entrada $s \in C_{DB}$ | Entrada $s \in C_{VCS}$ |
|---|---|---|---|---|
| **$q_0$** | $q_{fe}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{fe}$** | $q_{fe}$ *(self-loop)* | $q_{be}$ *(avance)* | $q_{trap}$ | $q_{trap}$ |
| **$q_{be}$** | $q_{trap}$ | $q_{be}$ *(self-loop)* | $q_{db}$ *(avance)* | $q_{trap}$ |
| **$q_{db}$** | $q_{trap}$ | $q_{trap}$ | $q_{db}$ *(self-loop)* | $q_{acc}$ *(avance)* |
| **$q_{acc}$ (Aceptador)** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{acc}$ *(self-loop)* |
| **$q_{trap}$** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |

#### Diagrama de Transición ($\mathcal{M}_{FS}$):
*(Diagrama de transición a incorporar mediante Excalidraw o elaboración manual).*

---

### 4.2. Perfil 2: Machine Learning Engineer ($\mathcal{M}_{ML}$)

#### 5-Tupla:
$$\mathcal{M}_{ML} = (Q_{ML}, \Sigma_{ML}, \delta_{ML}, q_0, F_{ML})$$

#### 1. Conjunto de Estados $Q_{ML}$:
- $q_0$: Estado inicial.
- $q_{lang}$: Lenguaje base validado ($\ge 1$ lenguaje de programación).
- $q_{data}$: Procesamiento y manipulación de datos validado.
- $q_{ml}$: Frameworks de Machine Learning y Deep Learning validados.
- $q_{db}$: Consultas y almacenamiento de datos validados.
- $q_{acc}$: **Aceptado.** Control de versiones validado.
- $q_{trap}$: Estado de rechazo.

$$Q_{ML} = \{q_0, q_{lang}, q_{data}, q_{ml}, q_{db}, q_{acc}, q_{trap}\}$$

#### 2. Alfabeto de Entrada $\Sigma_{ML}$:
- $C_{LANG} = \{\text{PYTHON}, \text{R}, \text{JULIA}\}$
- $C_{DATA} = \{\text{PANDAS}, \text{NUMPY}, \text{SCIPY}\}$
- $C_{ML} = \{\text{SCIKIT\_LEARN}, \text{TENSORFLOW}, \text{PYTORCH}, \text{KERAS}, \text{XGBOOST}\}$
- $C_{DB} = \{\text{SQL}, \text{POSTGRESQL}, \text{MYSQL}\}$
- $C_{VCS} = \{\text{GIT}, \text{GITHUB}, \text{GITLAB}\}$

$$\Sigma_{ML} = C_{LANG} \cup C_{DATA} \cup C_{ML} \cup C_{DB} \cup C_{VCS}$$

#### 3. Estado Inicial:
$$q_0$$

#### 4. Conjunto de Estados de Aceptación:
$$F_{ML} = \{q_{acc}\}$$

#### 5. Función de Transición $\delta_{ML} : Q_{ML} \times \Sigma_{ML} \to Q_{ML}$:

| Estado Actual ($q$) | Entrada $s \in C_{LANG}$ | Entrada $s \in C_{DATA}$ | Entrada $s \in C_{ML}$ | Entrada $s \in C_{DB}$ | Entrada $s \in C_{VCS}$ |
|---|---|---|---|---|---|
| **$q_0$** | $q_{lang}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{lang}$** | $q_{lang}$ | $q_{data}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{data}$** | $q_{trap}$ | $q_{data}$ | $q_{ml}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{ml}$** | $q_{trap}$ | $q_{trap}$ | $q_{ml}$ | $q_{db}$ | $q_{trap}$ |
| **$q_{db}$** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{db}$ | $q_{acc}$ |
| **$q_{acc}$ (Aceptador)** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{acc}$ |
| **$q_{trap}$** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |

#### Diagrama de Transición ($\mathcal{M}_{ML}$):
*(Diagrama de transición a incorporar mediante Excalidraw o elaboración manual).*

---

### 4.3. Perfil 3: Cloud & DevOps Engineer ($\mathcal{M}_{DEVOPS}$)

#### 5-Tupla:
$$\mathcal{M}_{DEVOPS} = (Q_{DEVOPS}, \Sigma_{DEVOPS}, \delta_{DEVOPS}, q_0, F_{DEVOPS})$$

#### 1. Conjunto de Estados $Q_{DEVOPS}$:
- $q_0$: Estado inicial.
- $q_{script}$: Scripting y administración de sistemas validado.
- $q_{cicd}$: Integración y entrega continua validada.
- $q_{cont}$: Contenedores y orquestación validados.
- $q_{cloud}$: Plataforma Cloud e Infraestructura como Código (IaC) validadas.
- $q_{acc}$: **Aceptado.** Control de versiones validado.
- $q_{trap}$: Estado de rechazo.

$$Q_{DEVOPS} = \{q_0, q_{script}, q_{cicd}, q_{cont}, q_{cloud}, q_{acc}, q_{trap}\}$$

#### 2. Alfabeto de Entrada $\Sigma_{DEVOPS}$:
- $C_{SCRIPT} = \{\text{BASH}, \text{LINUX}, \text{PYTHON}, \text{POWERSHELL}\}$
- $C_{CICD} = \{\text{GITHUB\_ACTIONS}, \text{JENKINS}, \text{GITLAB\_CI}, \text{ARGO\_CD}\}$
- $C_{CONT} = \{\text{DOCKER}, \text{KUBERNETES}, \text{PODMAN}, \text{HELM}\}$
- $C_{CLOUD} = \{\text{AWS}, \text{AZURE}, \text{GCP}, \text{TERRAFORM}, \text{ANSIBLE}\}$
- $C_{VCS} = \{\text{GIT}, \text{GITHUB}, \text{GITLAB}\}$

$$\Sigma_{DEVOPS} = C_{SCRIPT} \cup C_{CICD} \cup C_{CONT} \cup C_{CLOUD} \cup C_{VCS}$$

#### 3. Estado Inicial:
$$q_0$$

#### 4. Conjunto de Estados de Aceptación:
$$F_{DEVOPS} = \{q_{acc}\}$$

#### 5. Función de Transición $\delta_{DEVOPS} : Q_{DEVOPS} \times \Sigma_{DEVOPS} \to Q_{DEVOPS}$:

| Estado Actual ($q$) | Entrada $s \in C_{SCRIPT}$ | Entrada $s \in C_{CICD}$ | Entrada $s \in C_{CONT}$ | Entrada $s \in C_{CLOUD}$ | Entrada $s \in C_{VCS}$ |
|---|---|---|---|---|---|
| **$q_0$** | $q_{script}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{script}$** | $q_{script}$ | $q_{cicd}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{cicd}$** | $q_{trap}$ | $q_{cicd}$ | $q_{cont}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{cont}$** | $q_{trap}$ | $q_{trap}$ | $q_{cont}$ | $q_{cloud}$ | $q_{trap}$ |
| **$q_{cloud}$** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{cloud}$ | $q_{acc}$ |
| **$q_{acc}$ (Aceptador)** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{acc}$ |
| **$q_{trap}$** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |

#### Diagrama de Transición ($\mathcal{M}_{DEVOPS}$):
*(Diagrama de transición a incorporar mediante Excalidraw o elaboración manual).*

---

### 4.4. Perfil 4: Data Scientist ($\mathcal{M}_{DS}$)

#### 5-Tupla:
$$\mathcal{M}_{DS} = (Q_{DS}, \Sigma_{DS}, \delta_{DS}, q_0, F_{DS})$$

#### 1. Conjunto de Estados $Q_{DS}$:
- $q_0$: Estado inicial.
- $q_{lang}$: Lenguaje analítico validado ($\ge 1$ lenguaje de programación o consulta analítica).
- $q_{stats}$: Análisis exploratorio y estadística aplicada validado.
- $q_{viz}$: Visualización de datos y storytelling validado.
- $q_{ml}$: Modelado predictivo y algoritmos de Machine Learning validado.
- $q_{acc}$: **Aceptado.** Control de versiones validado.
- $q_{trap}$: Estado de rechazo.

$$Q_{DS} = \{q_0, q_{lang}, q_{stats}, q_{viz}, q_{ml}, q_{acc}, q_{trap}\}$$

#### 2. Alfabeto de Entrada $\Sigma_{DS}$:
- $C_{LANG} = \{\text{PYTHON}, \text{R}, \text{SQL}, \text{JULIA}\}$
- $C_{STATS} = \{\text{PANDAS}, \text{NUMPY}, \text{SCIPY}, \text{STATSMODELS}\}$
- $C_{VIZ} = \{\text{MATPLOTLIB}, \text{SEABORN}, \text{PLOTLY}, \text{TABLEAU}, \text{POWER\_BI}\}$
- $C_{ML} = \{\text{SCIKIT\_LEARN}, \text{XGBOOST}, \text{LIGHTGBM}, \text{CATBOOST}\}$
- $C_{VCS} = \{\text{GIT}, \text{GITHUB}, \text{GITLAB}\}$

$$\Sigma_{DS} = C_{LANG} \cup C_{STATS} \cup C_{VIZ} \cup C_{ML} \cup C_{VCS}$$

#### 3. Estado Inicial:
$$q_0$$

#### 4. Conjunto de Estados de Aceptación:
$$F_{DS} = \{q_{acc}\}$$

#### 5. Función de Transición $\delta_{DS} : Q_{DS} \times \Sigma_{DS} \to Q_{DS}$:

| Estado Actual ($q$) | Entrada $s \in C_{LANG}$ | Entrada $s \in C_{STATS}$ | Entrada $s \in C_{VIZ}$ | Entrada $s \in C_{ML}$ | Entrada $s \in C_{VCS}$ |
|---|---|---|---|---|---|
| **$q_0$** | $q_{lang}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{lang}$** | $q_{lang}$ | $q_{stats}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{stats}$** | $q_{trap}$ | $q_{stats}$ | $q_{viz}$ | $q_{trap}$ | $q_{trap}$ |
| **$q_{viz}$** | $q_{trap}$ | $q_{trap}$ | $q_{viz}$ | $q_{ml}$ | $q_{trap}$ |
| **$q_{ml}$** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{ml}$ | $q_{acc}$ |
| **$q_{acc}$ (Aceptador)** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{acc}$ |
| **$q_{trap}$** | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ | $q_{trap}$ |

#### Diagrama de Transición ($\mathcal{M}_{DS}$):
*(Diagrama de transición a incorporar mediante Excalidraw o elaboración manual).*

---

## 5. Casos de Prueba Diseñados

Para cada perfil se contemplan 3 tipos de escenarios en la suite de pruebas automatizadas:

1. **Caso Válido Mínimo:** 1 tecnología por cada categoría canónica obligatoria en el orden exacto.
2. **Caso Válido Extendido:** Múltiples tecnologías por categoría (activando los *self-loops*).
3. **Casos de Rechazo:**
   - **Falta de requisito:** Omitir una categoría obligatoria (ejemplo: sabe Frontend, Backend y Database, pero no VCS).
   - **Orden violado:** Tokens presentados en orden invertido o mezclado (ejemplo: Git antes de Frontend).
   - **Tokens extraños:** Tokens no pertenecientes al alfabeto del perfil.
   - **Cadena vacía:** Entrada sin calificaciones.
