/**
 * Algorithm Performance Comparison Dashboard
 * Benchmarking Dijkstra, Bellman-Ford, Floyd-Warshall, BFS, and DFS with Chart.js
 */

document.addEventListener('DOMContentLoaded', () => {
  const activeGraph = AppStorage.getActiveGraph();
  let chartTimeInstance = null;
  let chartOpsInstance = null;

  // Populate source and destination dropdowns from active graph
  function populateNodes() {
    const srcSelect = document.getElementById('compSource');
    const dstSelect = document.getElementById('compDestination');
    srcSelect.innerHTML = '';
    dstSelect.innerHTML = '';

    const nodes = (activeGraph.elements && activeGraph.elements.nodes) || [];
    nodes.forEach(n => {
      const id = n.data ? n.data.id : n.id;
      srcSelect.add(new Option(id, id));
      dstSelect.add(new Option(id, id));
    });

    if (nodes.length > 1) {
      dstSelect.selectedIndex = nodes.length - 1;
    }
  }

  populateNodes();

  // Run Comparison across all 5 algorithms
  async function runComparison() {
    const source = document.getElementById('compSource').value;
    const destination = document.getElementById('compDestination').value;
    const runBtn = document.getElementById('btnRunComparison');

    if (!source || !destination) {
      alert("Please select both source and destination vertices.");
      return;
    }

    runBtn.disabled = true;
    runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Benchmarking...`;

    try {
      const res = await fetch('/api/algorithm/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: source,
          destination: destination,
          graph_data: activeGraph.elements,
          directed: activeGraph.directed
        })
      });

      const data = await res.json();
      runBtn.disabled = false;
      runBtn.innerHTML = `<i class="fa-solid fa-play"></i> Run All 5 Algorithms`;

      if (!data.success) {
        alert("Comparison failed: " + data.error);
        return;
      }

      renderComparisonResults(data.results, source, destination);
      showToast("Completed benchmarking across all 5 algorithms.", "success");
    } catch (err) {
      runBtn.disabled = false;
      runBtn.innerHTML = `<i class="fa-solid fa-play"></i> Run All 5 Algorithms`;
      alert("Network error: " + err.message);
    }
  }

  function renderComparisonResults(results, source, destination) {
    const tableBody = document.getElementById('comparisonTableBody');
    tableBody.innerHTML = '';

    const labels = [];
    const execTimes = [];
    const operations = [];

    const order = ['dijkstra', 'bellman_ford', 'floyd_warshall', 'bfs', 'dfs'];

    order.forEach(key => {
      const item = results[key];
      if (!item) return;

      labels.push(item.name.replace(" Algorithm", ""));
      execTimes.push(item.execution_time_ms || 0);
      operations.push(item.relaxations_count || 0);

      const pathText = item.path && item.path.length > 0
        ? item.path.join(' → ')
        : (item.error ? `<span class="badge badge-orange">${item.error.substring(0, 35)}...</span>` : '<span class="badge badge-gray">No Path</span>');

      const costText = item.total_distance !== null && item.total_distance !== undefined
        ? `<strong style="color: #15803d;">${item.total_distance}</strong>`
        : '<span style="color: #94a3b8;">N/A</span>';

      let statusBadge = '<span class="badge badge-green"><i class="fa-solid fa-check"></i> Optimal</span>';
      if (!item.success) {
        statusBadge = '<span class="badge badge-orange"><i class="fa-solid fa-triangle-exclamation"></i> Incompatible</span>';
      } else if (key === 'bfs') {
        statusBadge = '<span class="badge badge-blue"><i class="fa-solid fa-info"></i> Min Hops (Unweighted)</span>';
      } else if (key === 'dfs') {
        statusBadge = '<span class="badge badge-gray"><i class="fa-solid fa-xmark"></i> Traversal Only</span>';
      }

      const row = document.createElement('tr');
      row.innerHTML = `
        <td><strong>${item.name}</strong><br><span style="font-size: 11px; color: var(--text-muted);">${item.type}</span></td>
        <td style="font-family: monospace; font-size: 12px;">${pathText}</td>
        <td>${costText}</td>
        <td><strong style="color: #2563eb;">${item.execution_time_ms} ms</strong></td>
        <td>${item.visited_count}</td>
        <td>${item.relaxations_count}</td>
        <td><code>${item.time_complexity}</code></td>
        <td><code>${item.space_complexity}</code></td>
        <td>${statusBadge}</td>
      `;
      tableBody.appendChild(row);
    });

    renderCharts(labels, execTimes, operations);
  }

  function renderCharts(labels, times, ops) {
    // Chart 1: Execution Times
    const ctxTime = document.getElementById('chartExecTime').getContext('2d');
    if (chartTimeInstance) chartTimeInstance.destroy();

    chartTimeInstance = new Chart(ctxTime, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Execution Time (ms)',
          data: times,
          backgroundColor: [
            'rgba(34, 197, 94, 0.75)',
            'rgba(59, 130, 246, 0.75)',
            'rgba(168, 85, 247, 0.75)',
            'rgba(249, 115, 22, 0.75)',
            'rgba(100, 116, 139, 0.75)'
          ],
          borderColor: [
            '#16a34a',
            '#2563eb',
            '#9333ea',
            '#ea580c',
            '#475569'
          ],
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.parsed.y} ms (CPU Time)`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Milliseconds (ms)' }
          }
        }
      }
    });

    // Chart 2: Operations / Relaxations
    const ctxOps = document.getElementById('chartOperations').getContext('2d');
    if (chartOpsInstance) chartOpsInstance.destroy();

    chartOpsInstance = new Chart(ctxOps, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Edge Relaxations / Neighbor Checks',
          data: ops,
          backgroundColor: 'rgba(147, 51, 234, 0.75)',
          borderColor: '#7e22ce',
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Operations Count' }
          }
        }
      }
    });
  }

  document.getElementById('btnRunComparison').addEventListener('click', runComparison);

  // Auto-run on initial visit
  setTimeout(runComparison, 300);
});

