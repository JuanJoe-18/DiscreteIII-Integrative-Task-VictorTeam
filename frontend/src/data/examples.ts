export type Example = { id: string; title: string; mode: 'resume' | 'tokens'; content: string }

export const EXAMPLES: Example[] = [
  {
    id: 'fs-ok',
    title: 'Full Stack válido',
    mode: 'resume',
    content: `Nombre: Laura Gómez
Descripción: Desarrolladora web con 3 años de experiencia en aplicaciones de comercio electrónico.

Habilidades
- Frontend: JavaScript, TypeScript, React, HTML y CSS
- Backend: Node.js con Express, API REST
- Bases de datos: PostgreSQL
- Herramientas: Git, Docker`,
  },
  {
    id: 'fs-nogit',
    title: 'Full Stack sin Git',
    mode: 'resume',
    content: `Descripción: Desarrollador web enfocado en interfaces y servicios.

Habilidades
- JavaScript, React, Vue
- Node.js, Express, GraphQL
- MongoDB y MySQL
- Despliegue en Vercel`,
  },
  {
    id: 'ml-ok',
    title: 'ML válido',
    mode: 'resume',
    content: `Nombre: Andrés Patiño
Descripción: Ingeniero de aprendizaje automático en visión por computador.

Experiencia técnica
- Python para modelado y pipelines
- Procesamiento de datos con Pandas y NumPy
- Entrenamiento de modelos con TensorFlow y Keras
- Almacenamiento en PostgreSQL
- Control de versiones con Git`,
  },
  {
    id: 'ml-ds',
    title: 'Cumple ML y Data Scientist',
    mode: 'resume',
    content: `Nombre: Camila Rojas
Descripción: Científica de datos con enfoque en modelos predictivos.

Habilidades
- Python y SQL
- Pandas, NumPy y estadística inferencial
- Visualización con Matplotlib y Tableau
- Scikit-learn y PyTorch
- MySQL
- Git`,
  },
  {
    id: 'direct-bad',
    title: 'Secuencia directa fuera de orden',
    mode: 'tokens',
    content: 'GIT, JAVASCRIPT, REACT, NODE_JS, POSTGRESQL',
  },
]
