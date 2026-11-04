/**
 * Step-by-Step Algorithm Visualization Engine
 * Powered by backend execution trace arrays
 */

document.addEventListener('DOMContentLoaded', () => {
  let cy = null;
  const activeGraph = AppStorage.getActiveGraph();
  let traceSteps = [];
  let currentStepIdx = -1;
  let isPlaying = false;
  let timerId = null;

  // Cytoscape Canvas Stylesheet with state-based selectors
  const visStyle = [
    {
      selector: 'node',
      style: {
        'background-color': '#e2e8f0',     // Unvisited: Light grey
        'label': 'data(label)',
        'color': '#1e293b',
        'font-size': '13px',
        'font-weight': 'bold',
        'text-valign': 'center',
        'text-halign': 'center',
        'width': 36,
        'height': 36,
        'border-width': 2,
        'border-color': '#94a3b8',
        'transition-property': 'background-color, border-color, width, height',
        'transition-duration': '0.2s'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2.5,
        'line-color': '#cbd5e1',
        'target-arrow-color': '#cbd5e1',
        'target-arrow-shape': activeGraph.directed ? 'triangle' : 'none',
        'curve-style': 'bezier',
        'label': 'data(weight)',
        'font-size': '11px',
        'font-weight': '600',
        'color': '#475569',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.85,
        'text-background-padding': 2,
        'transition-property': 'line-color, target-arrow-color, width',
        'transition-duration': '0.2s'
      }
    },
    // Visual States
    {
      selector: '.node-processing',
      style: {
        'background-color': '#f97316',      // Processing: Orange
        'color': '#ffffff',
        'border-color': '#c2410c',
        'border-width': 4,
        'width': 44,
        'height': 44,
        'z-index': 99
      }
    },
    {
      selector: '.node-visited',
      style: {
        'background-color': '#2563eb',      // Visited: Blue
        'color': '#ffffff',
        'border-color': '#1d4ed8',
        'border-width': 2.5
      }
    },
    {
      selector: '.node-path',
      style: {
        'background-color': '#16a34a',      // Final Shortest Path: Green
        'color': '#ffffff',
        'border-color': '#14532d',
        'border-width': 4,
        'width': 42,
        'height': 42,
        'z-index': 100
      }
    },
    {
      selector: '.edge-explored',
      style: {
        'line-color': '#9333ea',            // Explored Edge: Purple
        'target-arrow-color': '#9333ea',
        'width': 3.5,
        'z-index': 50
      }
    },
    {
      selector: '.edge-path',
      style: {
        'line-color': '#16a34a',            // Final Path Edge: Green
        'target-arrow-color': '#16a34a',
        'width': 4.5,
        'z-index': 100
      }
    }
  ];

  function initCytoscape() {
    cy = cytoscape({
      container: document.getElementById('cy'),
      elements: activeGraph.elements,
      style: visStyle,
      layout: { name: 'preset' }
    });
    cy.fit(null, 40);

    // Populate dropdowns
    const srcSelect = document.getElementById('visSource');
    const dstSelect = document.getElementById('visDestination');
    srcSelect.innerHTML = '';
    dstSelect.innerHTML = '';

    const nodes = cy.nodes();
    nodes.forEach((n) => {
      const id = n.id();
      srcSelect.add(new Option(id, id));
      dstSelect.add(new Option(id, id));
    });
    if (nodes.length > 1) {
      dstSelect.selectedIndex = nodes.length - 1;
    }

    // Check query params
    const params = new URLSearchParams(window.location.search);
    if (params.get('algo')) {
      const algoEl = document.getElementById('visAlgorithm');
      if (algoEl) algoEl.value = params.get('algo');
    }
    if (params.get('src')) {
      srcSelect.value = params.get('src');
    }
    if (params.get('dst')) {
      dstSelect.value = params.get('dst');
    }
  }

  initCytoscape();

  // Zoom controls
  document.getElementById('btnVisZoomIn').addEventListener('click', () => cy.zoom(cy.zoom() * 1.25));
  document.getElementById('btnVisZoomOut').addEventListener('click', () => cy.zoom(cy.zoom() * 0.8));
  document.getElementById('btnVisFit').addEventListener('click', () => cy.fit(null, 40));

  // Reset Graph Visuals
  function resetGraphVisuals() {
    cy.elements().removeClass('node-processing node-visited node-path edge-explored edge-path');
  }

  // Load Execution Trace from Python backend
  async function loadExecutionTrace() {
    pausePlayback();
    resetGraphVisuals();

    const algo = document.getElementById('visAlgorithm').value;
    const src = document.getElementById('visSource').value;
    const dst = document.getElementById('visDestination').value;
    const loadBtn = document.getElementById('btnLoadTrace');

    loadBtn.disabled = true;
    loadBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating...`;

    try {
      const res = await fetch('/api/algorithm/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          algorithm: algo,
          source: src,
          destination: dst,
          graph_data: activeGraph.elements,
          directed: activeGraph.directed,
          save_to_history: false
        })
      });

      const data = await res.json();
      loadBtn.disabled = false;
      loadBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Generate Trace`;

      if (!data.success) {
        showToast(data.error || "Algorithm reported an issue.", 'error');
        document.getElementById('stepExplanationBox').innerHTML = `
          <div class="alert alert-danger" style="margin: 0;">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <div><strong>Algorithm Notice:</strong><br>${data.error}</div>
          </div>
        `;
        traceSteps = data.steps || [];
      } else {
        traceSteps = data.steps || [];
        showToast(`Loaded ${traceSteps.length} execution steps for ${data.algorithm}.`, 'success');
      }

      currentStepIdx = 0;
      updateUIForStep(currentStepIdx);
    } catch (err) {
      loadBtn.disabled = false;
      loadBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Generate Trace`;
      alert("Failed to fetch execution trace: " + err.message);
    }
  }

  // Render a specific step index
  function updateUIForStep(index) {
    if (!traceSteps || traceSteps.length === 0 || index < 0 || index >= traceSteps.length) {
      document.getElementById('stepCounterBadge').textContent = 'Step 0 / 0';
      document.getElementById('animProgressFill').style.width = '0%';
      return;
    }

    const step = traceSteps[index];

    // 1. Update Progress & Counter
    document.getElementById('stepCounterBadge').textContent = `Step ${index + 1} / ${traceSteps.length}`;
    const pct = ((index + 1) / traceSteps.length) * 100;
    document.getElementById('animProgressFill').style.width = `${pct}%`;

    // 2. Execution Status Badge
    const statusBadge = document.getElementById('execStatusBadge');
    statusBadge.textContent = step.action || 'Executing';
    statusBadge.className = step.action === 'completed' ? 'badge badge-green' : (step.action === 'negative_cycle' ? 'badge badge-orange' : 'badge badge-blue');

    // 3. Current Vertex & Edge
    document.getElementById('statusCurrentVertex').textContent = step.current_vertex || 'None';
    document.getElementById('statusCurrentEdge').textContent = step.current_edge ? `${step.current_edge[0]} → ${step.current_edge[1]}` : 'None';

    // 4. Visited and Unvisited lists
    const visitedContainer = document.getElementById('statusVisitedList');
    if (step.visited && step.visited.length > 0) {
      visitedContainer.innerHTML = step.visited.map(v => `<span class="badge badge-blue">${v}</span>`).join(' ');
    } else {
      visitedContainer.innerHTML = `<span style="color: #94a3b8; font-size: 12px;">None</span>`;
    }

    const unvisitedContainer = document.getElementById('statusUnvisitedList');
    if (step.unvisited && step.unvisited.length > 0) {
      unvisitedContainer.innerHTML = step.unvisited.map(v => `<span class="badge badge-gray">${v}</span>`).join(' ');
    } else {
      unvisitedContainer.innerHTML = `<span style="color: #94a3b8; font-size: 12px;">None</span>`;
    }

    // 5. Human Explanation Box
    document.getElementById('stepExplanationBox').innerHTML = `
      <div style="font-weight: 700; color: var(--heading-green); margin-bottom: 4px;">
        ${step.iteration ? `[${step.iteration}] ` : ''}${formatActionTitle(step.action)}
      </div>
      <div>${step.explanation || ''}</div>
    `;

    // 6. Distance Table
    const tableBody = document.getElementById('distanceTableBody');
    if (step.matrix) {
      // Floyd Warshall matrix view
      document.getElementById('dataStructureTitle').innerHTML = `<i class="fa-solid fa-table"></i> Distance Matrix`;
      let matrixHtml = `<table class="custom-table" style="font-size: 11px;"><thead><tr><th>From \\ To</th>`;
      const nodes = Object.keys(step.matrix);
      nodes.forEach(n => { matrixHtml += `<th>${n}</th>`; });
      matrixHtml += `</tr></thead><tbody>`;
      nodes.forEach(u => {
        matrixHtml += `<tr><td><strong>${u}</strong></td>`;
        nodes.forEach(v => {
          const val = step.matrix[u][v];
          const isPivot = (u === step.pivot_vertex || v === step.pivot_vertex);
          const cellStyle = isPivot ? 'background: #fef3c7; font-weight: bold;' : '';
          matrixHtml += `<td style="${cellStyle}">${val}</td>`;
        });
        matrixHtml += `</tr>`;
      });
      matrixHtml += `</tbody></table>`;
      document.getElementById('distanceTableContainer').innerHTML = matrixHtml;
    } else if (step.distances) {
      document.getElementById('dataStructureTitle').innerHTML = `<i class="fa-solid fa-table"></i> Distance Table`;
      let rows = '';
      for (const [node, dist] of Object.entries(step.distances)) {
        const pred = (step.predecessors && step.predecessors[node]) || 'None';
        const isCurrent = node === step.current_vertex;
        rows += `
          <tr style="${isCurrent ? 'background: #fff7ed; font-weight: 600;' : ''}">
            <td>${node}</td>
            <td style="color: #15803d; font-weight: 600;">${dist}</td>
            <td>${pred}</td>
          </tr>
        `;
      }
      tableBody.innerHTML = rows;
    }

    // 7. Cytoscape Graph Highlighting
    resetGraphVisuals();

    // Mark visited nodes
    if (step.visited) {
      step.visited.forEach(id => {
        const n = cy.getElementById(id);
        if (n.length) n.addClass('node-visited');
      });
    }

    // Mark current active vertex
    if (step.current_vertex) {
      const activeN = cy.getElementById(step.current_vertex);
      if (activeN.length) {
        activeN.removeClass('node-visited').addClass('node-processing');
      }
    }

    // Mark current active edge
    if (step.current_edge) {
      const [u, v] = step.current_edge;
      const edges = cy.edges().filter(e => {
        const src = e.source().id();
        const tgt = e.target().id();
        return (src === u && tgt === v) || (!activeGraph.directed && src === v && tgt === u);
      });
      edges.addClass('edge-explored');
    }

    // Highlight final path if completed
    if (step.action === 'completed' && step.highlight_path) {
      step.highlight_path.forEach(([u, v]) => {
        cy.getElementById(u).removeClass('node-processing node-visited').addClass('node-path');
        cy.getElementById(v).removeClass('node-processing node-visited').addClass('node-path');
        cy.edges().filter(e => {
          const s = e.source().id();
          const t = e.target().id();
          return (s === u && t === v) || (!activeGraph.directed && s === v && t === u);
        }).removeClass('edge-explored').addClass('edge-path');
      });
    }
  }

  function formatActionTitle(action) {
    if (!action) return 'Step Execution';
    return action.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }

  // Playback Control Functions
  function playPlayback() {
    if (!traceSteps || traceSteps.length === 0) {
      loadExecutionTrace().then(() => {
        if (traceSteps.length > 0) startTimer();
      });
      return;
    }
    if (currentStepIdx >= traceSteps.length - 1) {
      currentStepIdx = 0;
    }
    startTimer();
  }

  function startTimer() {
    isPlaying = true;
    updatePlayPauseButton();
    const speed = parseInt(document.getElementById('animSpeedSelect').value, 10) || 800;
    clearInterval(timerId);
    timerId = setInterval(() => {
      if (currentStepIdx < traceSteps.length - 1) {
        currentStepIdx++;
        updateUIForStep(currentStepIdx);
      } else {
        pausePlayback();
      }
    }, speed);
  }

  function pausePlayback() {
    isPlaying = false;
    clearInterval(timerId);
    timerId = null;
    updatePlayPauseButton();
  }

  function updatePlayPauseButton() {
    const btn = document.getElementById('btnPlayPause');
    if (isPlaying) {
      btn.innerHTML = `<i class="fa-solid fa-pause"></i> Pause`;
      btn.className = 'btn btn-warning btn-sm';
    } else {
      btn.innerHTML = `<i class="fa-solid fa-play"></i> Play`;
      btn.className = 'btn btn-primary btn-sm';
    }
  }

  // Event Listeners for Controls
  document.getElementById('btnLoadTrace').addEventListener('click', loadExecutionTrace);

  document.getElementById('btnPlayPause').addEventListener('click', () => {
    if (isPlaying) {
      pausePlayback();
    } else {
      playPlayback();
    }
  });

  document.getElementById('btnNextStep').addEventListener('click', () => {
    pausePlayback();
    if (!traceSteps || traceSteps.length === 0) {
      loadExecutionTrace();
      return;
    }
    if (currentStepIdx < traceSteps.length - 1) {
      currentStepIdx++;
      updateUIForStep(currentStepIdx);
    }
  });

  document.getElementById('btnPrevStep').addEventListener('click', () => {
    pausePlayback();
    if (currentStepIdx > 0) {
      currentStepIdx--;
      updateUIForStep(currentStepIdx);
    }
  });

  document.getElementById('btnResetAnim').addEventListener('click', () => {
    pausePlayback();
    resetGraphVisuals();
    if (traceSteps.length > 0) {
      currentStepIdx = 0;
      updateUIForStep(currentStepIdx);
    }
  });

  document.getElementById('animSpeedSelect').addEventListener('change', () => {
    if (isPlaying) {
      pausePlayback();
      startTimer();
    }
  });

  // Auto-load if navigated with query params
  const initialParams = new URLSearchParams(window.location.search);
  if (initialParams.has('src') && initialParams.has('dst')) {
    setTimeout(loadExecutionTrace, 250);
  }
});

