/**
 * Interactive Cytoscape.js Graph Editor
 */

document.addEventListener('DOMContentLoaded', () => {
  let cy = null;
  let activeGraph = AppStorage.getActiveGraph();
  let selectedElement = null;

  // Cytoscape Canvas Stylesheet
  const cyStyle = [
    {
      selector: 'node',
      style: {
        'background-color': '#ffffff',
        'label': 'data(label)',
        'color': '#14532d',
        'font-size': '13px',
        'font-weight': 'bold',
        'text-valign': 'center',
        'text-halign': 'center',
        'width': 38,
        'height': 38,
        'border-width': 2.5,
        'border-color': '#15803d',
        'shadow-blur': 4,
        'shadow-color': 'rgba(0,0,0,0.1)',
        'shadow-offset-y': 2
      }
    },
    {
      selector: 'node:selected',
      style: {
        'background-color': '#f97316',
        'border-color': '#c2410c',
        'color': '#ffffff',
        'border-width': 3.5,
        'shadow-blur': 8,
        'shadow-color': 'rgba(249, 115, 22, 0.4)'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2.5,
        'line-color': '#94a3b8',
        'target-arrow-color': '#94a3b8',
        'target-arrow-shape': activeGraph.directed ? 'triangle' : 'none',
        'curve-style': 'bezier',
        'label': 'data(weight)',
        'font-size': '12px',
        'font-weight': 'bold',
        'color': '#1e293b',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.9,
        'text-background-padding': 3,
        'text-border-width': 1,
        'text-border-color': '#e2e8f0',
        'text-border-style': 'solid'
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#f97316',
        'target-arrow-color': '#f97316',
        'width': 4
      }
    }
  ];

  function initCytoscape(elements, directed = true) {
    cy = cytoscape({
      container: document.getElementById('cy'),
      elements: elements,
      style: cyStyle,
      layout: { name: 'preset' },
      boxSelectionEnabled: false,
      autoungrabify: false
    });

    // Update arrow shapes based on directed mode
    cy.style()
      .selector('edge')
      .style('target-arrow-shape', directed ? 'triangle' : 'none')
      .update();

    cy.fit(null, 40);

    // Event handlers
    cy.on('select', 'node, edge', (e) => {
      selectedElement = e.target;
      updateInspector(selectedElement);
    });

    cy.on('unselect', 'node, edge', (e) => {
      if (selectedElement === e.target) {
        selectedElement = null;
        clearInspector();
      }
    });

    cy.on('dragfree', 'node', () => {
      syncAndSave();
    });

    updateSummary();
    populateEdgeSelects();
  }

  function syncAndSave() {
    if (!cy) return;
    const elements = {
      nodes: cy.nodes().map(n => ({
        data: n.data(),
        position: n.position()
      })),
      edges: cy.edges().map(e => ({
        data: e.data()
      }))
    };
    const directed = document.getElementById('directedToggle').checked;
    activeGraph = { directed, elements };
    AppStorage.setActiveGraph(activeGraph);
    updateSummary();
    populateEdgeSelects();
  }

  function updateSummary() {
    if (!cy) return;
    const nodes = cy.nodes();
    const edges = cy.edges();
    document.getElementById('inspectorVerticesCount').textContent = nodes.length;
    document.getElementById('inspectorEdgesCount').textContent = edges.length;

    let hasNegative = false;
    edges.forEach(e => {
      const w = parseFloat(e.data('weight'));
      if (w < 0) hasNegative = true;
    });

    const negBadge = document.getElementById('badgeNegativeWeights');
    if (hasNegative) {
      negBadge.textContent = 'Detected';
      negBadge.className = 'badge badge-orange';
    } else {
      negBadge.textContent = 'None';
      negBadge.className = 'badge badge-gray';
    }

    const directed = document.getElementById('directedToggle').checked;
    const dirBadge = document.getElementById('badgeGraphType');
    dirBadge.textContent = directed ? 'Directed' : 'Undirected';
    dirBadge.className = directed ? 'badge badge-green' : 'badge badge-blue';
  }

  function updateInspector(el) {
    const container = document.getElementById('elementInspector');
    if (el.isNode()) {
      container.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <strong>Vertex:</strong> <span class="badge badge-green" style="font-size: 14px;">${el.id()}</span>
        </div>
        <div style="margin-bottom: 8px;">
          <span style="color: var(--text-muted);">Outgoing Connections:</span>
          <strong>${el.outgoers('edge').length}</strong>
        </div>
        <div style="margin-bottom: 14px;">
          <span style="color: var(--text-muted);">Incoming Connections:</span>
          <strong>${el.incomers('edge').length}</strong>
        </div>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-secondary btn-sm" id="btnInspectRename" style="flex: 1;"><i class="fa-solid fa-pen"></i> Rename</button>
          <button class="btn btn-danger btn-sm" id="btnInspectDelete" style="flex: 1;"><i class="fa-solid fa-trash"></i> Delete</button>
        </div>
      `;
      document.getElementById('btnInspectRename').addEventListener('click', openEditSelected);
      document.getElementById('btnInspectDelete').addEventListener('click', deleteSelected);
    } else if (el.isEdge()) {
      container.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <strong>Edge:</strong> <span class="badge badge-purple" style="font-size: 13px;">${el.source().id()} &rarr; ${el.target().id()}</span>
        </div>
        <div style="margin-bottom: 14px;">
          <span style="color: var(--text-muted);">Weight / Cost:</span>
          <strong style="color: #15803d; font-size: 16px;">${el.data('weight')}</strong>
        </div>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-secondary btn-sm" id="btnInspectEditWeight" style="flex: 1;"><i class="fa-solid fa-pen"></i> Edit Weight</button>
          <button class="btn btn-danger btn-sm" id="btnInspectDeleteEdge" style="flex: 1;"><i class="fa-solid fa-trash"></i> Delete</button>
        </div>
      `;
      document.getElementById('btnInspectEditWeight').addEventListener('click', openEditSelected);
      document.getElementById('btnInspectDeleteEdge').addEventListener('click', deleteSelected);
    }
  }

  function clearInspector() {
    document.getElementById('elementInspector').innerHTML = `
      <p style="text-align: center; padding: 20px 0;">
        <i class="fa-solid fa-arrow-pointer" style="font-size: 20px; color: #cbd5e1; display: block; margin-bottom: 8px;"></i>
        Click any vertex or edge in the graph to inspect or modify its attributes.
      </p>
    `;
  }

  function populateEdgeSelects() {
    const srcSelect = document.getElementById('edgeSource');
    const tgtSelect = document.getElementById('edgeTarget');
    if (!srcSelect || !tgtSelect || !cy) return;

    srcSelect.innerHTML = '';
    tgtSelect.innerHTML = '';
    const nodes = cy.nodes();
    nodes.forEach((n, idx) => {
      const id = n.id();
      srcSelect.add(new Option(id, id));
      tgtSelect.add(new Option(id, id));
    });
    if (nodes.length > 1) {
      tgtSelect.selectedIndex = 1;
    }
  }

  // Initial load
  document.getElementById('directedToggle').checked = activeGraph.directed !== false;
  initCytoscape(activeGraph.elements, activeGraph.directed !== false);

  // Zoom and Fit Handlers
  document.getElementById('btnZoomIn').addEventListener('click', () => cy.zoom(cy.zoom() * 1.25));
  document.getElementById('btnZoomOut').addEventListener('click', () => cy.zoom(cy.zoom() * 0.8));
  document.getElementById('btnFit').addEventListener('click', () => cy.fit(null, 40));

  // Toggle Directed/Undirected
  document.getElementById('directedToggle').addEventListener('change', (e) => {
    const isDirected = e.target.checked;
    cy.style()
      .selector('edge')
      .style('target-arrow-shape', isDirected ? 'triangle' : 'none')
      .update();
    syncAndSave();
    showToast(`Graph switched to ${isDirected ? 'Directed' : 'Undirected'} mode.`);
  });

  // Modal open/close helpers
  function openModal(id) { document.getElementById(id).classList.add('active'); }
  function closeModal(id) { document.getElementById(id).classList.remove('active'); }

  // Add Vertex
  document.getElementById('btnAddNode').addEventListener('click', () => openModal('addVertexModal'));
  document.getElementById('closeAddVertexModal').addEventListener('click', () => closeModal('addVertexModal'));
  document.getElementById('formAddVertex').addEventListener('submit', (e) => {
    e.preventDefault();
    const label = document.getElementById('vertexLabel').value.trim();
    if (!label) return;

    if (cy.getElementById(label).length > 0) {
      alert(`Vertex with ID '${label}' already exists.`);
      return;
    }

    // Place near center with slight random offset
    const extent = cy.extent();
    const posX = (extent.x1 + extent.x2) / 2 + (Math.random() * 80 - 40);
    const posY = (extent.y1 + extent.y2) / 2 + (Math.random() * 80 - 40);

    cy.add({
      group: 'nodes',
      data: { id: label, label: label },
      position: { x: posX, y: posY }
    });

    closeModal('addVertexModal');
    document.getElementById('vertexLabel').value = '';
    syncAndSave();
    showToast(`Vertex '${label}' added.`);
  });

  // Connect Edge
  document.getElementById('btnAddEdge').addEventListener('click', () => {
    populateEdgeSelects();
    openModal('addEdgeModal');
  });
  document.getElementById('closeAddEdgeModal').addEventListener('click', () => closeModal('addEdgeModal'));
  document.getElementById('formAddEdge').addEventListener('submit', (e) => {
    e.preventDefault();
    const src = document.getElementById('edgeSource').value;
    const tgt = document.getElementById('edgeTarget').value;
    const weightVal = parseFloat(document.getElementById('edgeWeight').value);

    if (src === tgt) {
      if (!confirm("Add self-loop on vertex " + src + "?")) return;
    }

    const directed = document.getElementById('directedToggle').checked;
    const edgeId = `e_${src}_${tgt}_${Date.now()}`;

    cy.add({
      group: 'edges',
      data: {
        id: edgeId,
        source: src,
        target: tgt,
        weight: isNaN(weightVal) ? 1 : weightVal,
        directed: directed
      }
    });

    closeModal('addEdgeModal');
    syncAndSave();
    showToast(`Connected edge (${src} → ${tgt}, wt=${weightVal}).`);
  });

  // Edit Selected Element
  function openEditSelected() {
    if (!selectedElement) {
      alert("Please select a vertex or edge to edit.");
      return;
    }
    const title = document.getElementById('editModalTitle');
    const fields = document.getElementById('editElementFields');

    if (selectedElement.isNode()) {
      title.textContent = `Rename Vertex '${selectedElement.id()}'`;
      fields.innerHTML = `
        <div class="form-group">
          <label for="editVertexLabel">New Vertex Label</label>
          <input type="text" id="editVertexLabel" class="form-control" value="${selectedElement.id()}" required maxlength="12">
        </div>
      `;
    } else {
      title.textContent = `Edit Edge Weight (${selectedElement.source().id()} → ${selectedElement.target().id()})`;
      fields.innerHTML = `
        <div class="form-group">
          <label for="editEdgeWeight">Edge Weight</label>
          <input type="number" id="editEdgeWeight" class="form-control" value="${selectedElement.data('weight')}" step="any" required>
        </div>
      `;
    }
    openModal('editElementModal');
  }

  document.getElementById('btnEditSelected').addEventListener('click', openEditSelected);
  document.getElementById('closeEditModal').addEventListener('click', () => closeModal('editElementModal'));
  document.getElementById('formEditElement').addEventListener('submit', (e) => {
    e.preventDefault();
    if (!selectedElement) return;

    if (selectedElement.isNode()) {
      const newLabel = document.getElementById('editVertexLabel').value.trim();
      if (!newLabel) return;
      if (newLabel !== selectedElement.id() && cy.getElementById(newLabel).length > 0) {
        alert(`Vertex with ID '${newLabel}' already exists.`);
        return;
      }
      const oldId = selectedElement.id();
      const pos = selectedElement.position();
      const connectedEdges = selectedElement.connectedEdges().map(e => e.data());
      
      // Cytoscape IDs are immutable, recreate with new ID
      cy.remove(selectedElement);
      cy.add({ group: 'nodes', data: { id: newLabel, label: newLabel }, position: pos });
      connectedEdges.forEach(ed => {
        const s = ed.source === oldId ? newLabel : ed.source;
        const t = ed.target === oldId ? newLabel : ed.target;
        cy.add({ group: 'edges', data: { id: `e_${s}_${t}_${Date.now()}`, source: s, target: t, weight: ed.weight, directed: ed.directed } });
      });
      selectedElement = null;
      clearInspector();
      showToast(`Renamed vertex to '${newLabel}'.`);
    } else {
      const newW = parseFloat(document.getElementById('editEdgeWeight').value);
      selectedElement.data('weight', isNaN(newW) ? 1 : newW);
      updateInspector(selectedElement);
      showToast(`Updated edge weight to ${newW}.`);
    }

    closeModal('editElementModal');
    syncAndSave();
  });

  // Delete Selected Element
  function deleteSelected() {
    if (!selectedElement) {
      alert("Please select a vertex or edge to delete.");
      return;
    }
    const desc = selectedElement.isNode() ? `Vertex '${selectedElement.id()}'` : `Edge`;
    cy.remove(selectedElement);
    selectedElement = null;
    clearInspector();
    syncAndSave();
    showToast(`${desc} deleted.`);
  }

  document.getElementById('btnDeleteSelected').addEventListener('click', deleteSelected);

  // Keyboard shortcut [Delete]
  window.addEventListener('keydown', (e) => {
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedElement && document.activeElement.tagName !== 'INPUT') {
      deleteSelected();
    }
  });

  // Clear Graph
  document.getElementById('btnClearGraph').addEventListener('click', () => {
    if (confirm("Are you sure you want to clear the entire graph?")) {
      cy.elements().remove();
      selectedElement = null;
      clearInspector();
      syncAndSave();
      showToast("Graph cleared.");
    }
  });

  // Reset Graph / Layout
  document.getElementById('btnResetLayout').addEventListener('click', () => {
    const layout = cy.layout({ name: 'cose', animate: true, animationDuration: 400 });
    layout.run();
    setTimeout(syncAndSave, 450);
  });

  // Load Sample Graphs
  document.getElementById('sampleGraphSelect').addEventListener('change', async (e) => {
    const key = e.target.value;
    if (!key) return;

    try {
      const res = await fetch(`/api/samples/${key}`);
      const data = await res.json();
      if (data.success && data.graph) {
        document.getElementById('directedToggle').checked = data.graph.directed !== false;
        initCytoscape(data.graph.elements, data.graph.directed !== false);
        syncAndSave();
        showToast(`Loaded preset '${data.graph.name}'.`, 'success');
      }
    } catch (err) {
      alert("Failed to load sample graph: " + err.message);
    }
    e.target.value = '';
  });

  // Random Graph Generator
  document.getElementById('btnRandomGraph').addEventListener('click', () => openModal('randomGraphModal'));
  document.getElementById('closeRandomModal').addEventListener('click', () => closeModal('randomGraphModal'));
  document.getElementById('randomDensity').addEventListener('input', (e) => {
    document.getElementById('densityVal').textContent = e.target.value;
  });

  document.getElementById('formRandomGraph').addEventListener('submit', async (e) => {
    e.preventDefault();
    const num_nodes = parseInt(document.getElementById('randomNodesCount').value, 10);
    const density = parseFloat(document.getElementById('randomDensity').value);
    const allow_negative = document.getElementById('randomAllowNegative').checked;
    const directed = document.getElementById('directedToggle').checked;

    try {
      const res = await fetch('/api/random-graph', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num_nodes, density, directed, allow_negative })
      });
      const data = await res.json();
      if (data.success && data.graph) {
        initCytoscape(data.graph.elements, directed);
        syncAndSave();
        closeModal('randomGraphModal');
        showToast(`Generated random graph with ${num_nodes} vertices.`, 'success');
      }
    } catch (err) {
      alert("Failed to generate random graph: " + err.message);
    }
  });

  // Save Graph to SQLite Database
  document.getElementById('btnSaveGraphModal').addEventListener('click', () => openModal('saveGraphModal'));
  document.getElementById('closeSaveGraphModal').addEventListener('click', () => closeModal('saveGraphModal'));
  document.getElementById('formSaveGraph').addEventListener('submit', async (e) => {
    e.preventDefault();
    const graphName = document.getElementById('saveGraphName').value.trim();
    if (!graphName) return;

    try {
      const res = await fetch('/api/graphs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_name: graphName,
          graph_data: activeGraph
        })
      });
      const data = await res.json();
      if (data.success) {
        closeModal('saveGraphModal');
        showToast(`Graph '${graphName}' saved to your account!`, 'success');
        loadUserSavedGraphsList();
      } else {
        alert("Error: " + data.error);
      }
    } catch (err) {
      alert("Failed to save graph: " + err.message);
    }
  });

  // Load User's Saved Graphs from Database
  async function loadUserSavedGraphsList() {
    const select = document.getElementById('userSavedGraphsSelect');
    try {
      const res = await fetch('/api/graphs');
      const data = await res.json();
      if (data.success && data.graphs) {
        select.innerHTML = '<option value="">-- Load Saved Graph --</option>';
        data.graphs.forEach(g => {
          select.add(new Option(g.graph_name, g.id));
        });
      }
    } catch (e) {
      console.warn("Could not load user saved graphs list", e);
    }
  }

  loadUserSavedGraphsList();

  document.getElementById('userSavedGraphsSelect').addEventListener('change', async (e) => {
    const graphId = e.target.value;
    if (!graphId) return;

    try {
      const res = await fetch(`/api/graphs/${graphId}`);
      const data = await res.json();
      if (data.success && data.elements) {
        const loadedGraph = data.elements;
        document.getElementById('directedToggle').checked = loadedGraph.directed !== false;
        initCytoscape(loadedGraph.elements || loadedGraph, loadedGraph.directed !== false);
        syncAndSave();
        showToast(`Loaded saved graph '${data.graph.graph_name}'.`, 'success');
      }
    } catch (err) {
      alert("Failed to load saved graph: " + err.message);
    }
    e.target.value = '';
  });
});

