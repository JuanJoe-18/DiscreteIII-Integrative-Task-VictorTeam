export type Example = { id: string; title: string; mode: 'resume' | 'tokens'; content: string }

export const EXAMPLES: Example[] = [
  {
    id: 'fs-ok',
    title: 'Valid Full Stack',
    mode: 'resume',
    content: `Name: Laura Gómez
Description: Web developer with 3 years of experience building e-commerce applications.

Skills
- Frontend: JavaScript, TypeScript, React, HTML and CSS
- Backend: Node.js with Express, REST API
- Databases: PostgreSQL
- Tools: Git, Docker`,
  },
  {
    id: 'fs-nogit',
    title: 'Full Stack without Git',
    mode: 'resume',
    content: `Description: Web developer focused on interfaces and services.

Skills
- JavaScript, React, Vue
- Node.js, Express, GraphQL
- MongoDB and MySQL
- Deployment on Vercel`,
  },
  {
    id: 'ml-ok',
    title: 'Valid ML',
    mode: 'resume',
    content: `Name: Andrés Patiño
Description: Machine learning engineer working on computer vision.

Technical experience
- Python for modelling and pipelines
- Data processing with Pandas and NumPy
- Model training with TensorFlow and Keras
- Storage in PostgreSQL
- Version control with Git`,
  },
  {
    id: 'ml-ds',
    title: 'Satisfies ML and Data Scientist',
    mode: 'resume',
    content: `Name: Camila Rojas
Description: Data scientist focused on predictive models.

Skills
- Python and SQL
- Pandas, NumPy and inferential statistics
- Visualization with Matplotlib and Tableau
- Scikit-learn and PyTorch
- MySQL
- Git`,
  },
  {
    id: 'ml-es',
    title: 'Spanish résumé (ML)',
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
    id: 'direct-bad',
    title: 'Direct sequence out of order',
    mode: 'tokens',
    content: 'GIT, JAVASCRIPT, REACT, NODE_JS, POSTGRESQL',
  },
]
