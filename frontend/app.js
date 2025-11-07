const analyzeBtn = document.getElementById('analyze-btn');
const repoInput = document.getElementById('repo-url');
const errorBox = document.getElementById('error');
const spinner = document.getElementById('spinner');
const resultsSection = document.getElementById('results');
const metadataBox = document.getElementById('metadata');
const summaryBox = document.getElementById('summary');
const c4Diagram = document.getElementById('c4-diagram');
const dependenciesDiagram = document.getElementById('dependencies-diagram');
const routesDiagram = document.getElementById('routes-diagram');
const dbDiagram = document.getElementById('db-diagram');
const rawBox = document.getElementById('raw');
const tabs = document.querySelectorAll('.tabs button');
const zoomSelect = document.getElementById('zoom-select');

let originalDiagrams = {
  c4: '',
  dependencies: '',
  routes: '',
  db: ''
};
let moduleStructure = {};

mermaid.initialize({ startOnLoad: false });

function setActiveTab(targetId) {
  document.querySelectorAll('.tab-content').forEach((el) => {
    if (el.id === targetId) {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  });
  tabs.forEach((button) => {
    if (button.dataset.target === targetId) {
      button.classList.add('active');
    } else {
      button.classList.remove('active');
    }
  });
}

tabs.forEach((button) => {
  button.addEventListener('click', () => {
    setActiveTab(button.dataset.target);
    if (button.dataset.target !== 'raw') {
      mermaid.run();
    }
  });
});

async function analyzeRepo() {
  const url = repoInput.value.trim();
  if (!url) {
    errorBox.textContent = 'Please enter a GitHub URL.';
    return;
  }
  errorBox.textContent = '';
  spinner.classList.remove('hidden');
  resultsSection.classList.add('hidden');

  try {
    const response = await fetch('http://127.0.0.1:8000/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: url })
    });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail || 'Analysis failed');
    }
    const data = await response.json();
    renderResults(data);
  } catch (err) {
    console.error(err);
    errorBox.textContent = err.message;
  } finally {
    spinner.classList.add('hidden');
  }
}

function renderResults(data) {
  resultsSection.classList.remove('hidden');
  metadataBox.innerHTML = `
    <h2>${data.repo.name}</h2>
    <p>Default branch: ${data.repo.default_branch}</p>
    <p>SHA: ${data.repo.sha}</p>
    <p>Languages: ${Object.entries(data.repo.languages)
      .map(([lang, pct]) => `${lang}: ${pct}%`)
      .join(', ')}</p>
  `;

  summaryBox.innerHTML = `
    <h3>Explain Like I'm New</h3>
    <ul>${data.summaries.high_level.map((item) => `<li>${item}</li>`).join('')}</ul>
    <h3>Focus Modules</h3>
    <ul>
      ${data.summaries.focus_modules
        .map((mod) => `<li><strong>${mod.module}</strong> (${mod.why}) - ${mod.notes}</li>`)
        .join('')}
    </ul>
    <p><strong>Limits:</strong> Files scanned ${data.limits.file_count_scanned}, nodes capped at ${data.limits.max_nodes}</p>
  `;

  c4Diagram.textContent = data.diagrams.c4_modules_mermaid;
  dependenciesDiagram.textContent = data.diagrams.dependencies_mermaid;
  routesDiagram.textContent = data.diagrams.routes_mermaid;
  dbDiagram.textContent = data.diagrams.db_mermaid;
  rawBox.textContent = JSON.stringify(data, null, 2);

  originalDiagrams = {
    c4: data.diagrams.c4_modules_mermaid,
    dependencies: data.diagrams.dependencies_mermaid,
    routes: data.diagrams.routes_mermaid,
    db: data.diagrams.db_mermaid
  };
  moduleStructure = data.modules || {};

  populateZoomOptions();
  applyZoom('');

  setActiveTab('summary');
  mermaid.run();
}

analyzeBtn.addEventListener('click', analyzeRepo);
repoInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    analyzeRepo();
  }
});

zoomSelect.addEventListener('change', (event) => {
  applyZoom(event.target.value);
});

function populateZoomOptions() {
  zoomSelect.innerHTML = '';
  const defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = 'All modules';
  zoomSelect.appendChild(defaultOption);
  zoomSelect.value = '';

  Object.keys(moduleStructure)
    .sort()
    .forEach((module) => {
      if (!module || module === '.') {
        return;
      }
      const option = document.createElement('option');
      option.value = module;
      option.textContent = module;
      zoomSelect.appendChild(option);
    });
}

function applyZoom(module) {
  if (!module) {
    c4Diagram.textContent = originalDiagrams.c4;
    dependenciesDiagram.textContent = originalDiagrams.dependencies;
    routesDiagram.textContent = originalDiagrams.routes;
    dbDiagram.textContent = originalDiagrams.db;
  } else {
    c4Diagram.textContent = buildC4ForModule(module);
    dependenciesDiagram.textContent = filterDependencies(module);
    routesDiagram.textContent = filterMermaidLines(originalDiagrams.routes, module);
    dbDiagram.textContent = originalDiagrams.db;
  }
  mermaid.run();
}

function buildC4ForModule(module) {
  const files = moduleStructure[module] || [];
  const safeId = module.replace(/[\/.]/g, '_') || 'root';
  const lines = ['graph TD'];
  lines.push(`    ${safeId}[${module || '.'}]`);
  files.forEach((file) => {
    const fileId = `${safeId}_${file.replace(/[\/.]/g, '_')}`;
    lines.push(`    ${safeId} --> ${fileId}[${file}]`);
  });
  if (files.length === 0) {
    lines.push('    Empty[No files in module]');
  }
  return lines.join('\n');
}

function filterDependencies(module) {
  const lines = originalDiagrams.dependencies.split('\n');
  const header = lines.shift();
  const modulePrefix = module === '.' ? '' : `${module}/`;
  const filtered = lines.filter((line) => {
    if (!line.trim()) return false;
    if (module === '.') {
      return !line.includes('/');
    }
    return line.includes(modulePrefix);
  });
  if (filtered.length === 0) {
    filtered.push('    Empty[No dependencies in module]');
  }
  return [header, ...filtered].join('\n');
}

function filterMermaidLines(mermaidSource, module) {
  const lines = mermaidSource.split('\n');
  const header = lines.shift();
  const filtered = lines.filter((line) => line.includes(module));
  if (filtered.length === 0) {
    filtered.push('    NoRoutes[No routes for module]');
  }
  return [header, ...filtered].join('\n');
}
