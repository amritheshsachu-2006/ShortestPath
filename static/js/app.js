/**
 * Shortest Path Finder - Shared App Utility Module
 */

const AppStorage = {
  STORAGE_KEY: 'aga_active_graph_data',

  DEFAULT_GRAPH: {
    directed: true,
    elements: {
      nodes: [
        { data: { id: "A", label: "A" }, position: { x: 100, y: 200 } },
        { data: { id: "B", label: "B" }, position: { x: 250, y: 100 } },
        { data: { id: "C", label: "C" }, position: { x: 250, y: 300 } },
        { data: { id: "D", label: "D" }, position: { x: 420, y: 100 } },
        { data: { id: "E", label: "E" }, position: { x: 420, y: 300 } },
        { data: { id: "F", label: "F" }, position: { x: 580, y: 200 } }
      ],
      edges: [
        { data: { id: "e_A_B", source: "A", target: "B", weight: 4, directed: true } },
        { data: { id: "e_A_C", source: "A", target: "C", weight: 2, directed: true } },
        { data: { id: "e_B_C", source: "B", target: "C", weight: 1, directed: true } },
        { data: { id: "e_B_D", source: "B", target: "D", weight: 5, directed: true } },
        { data: { id: "e_C_D", source: "C", target: "D", weight: 8, directed: true } },
        { data: { id: "e_C_E", source: "C", target: "E", weight: 10, directed: true } },
        { data: { id: "e_D_E", source: "D", target: "E", weight: 2, directed: true } },
        { data: { id: "e_D_F", source: "D", target: "F", weight: 6, directed: true } },
        { data: { id: "e_E_F", source: "E", target: "F", weight: 3, directed: true } }
      ]
    }
  },

  getActiveGraph() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        const parsed = JSON.parse(data);
        if (parsed && parsed.elements) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn("Could not read graph from storage, using default", e);
    }
    return JSON.parse(JSON.stringify(this.DEFAULT_GRAPH));
  },

  setActiveGraph(graphData) {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(graphData));
    } catch (e) {
      console.error("Could not write graph to storage", e);
    }
  },

  resetToDefault() {
    this.setActiveGraph(this.DEFAULT_GRAPH);
    return JSON.parse(JSON.stringify(this.DEFAULT_GRAPH));
  }
};

// UI Toast Notification Helper
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toastContainer';
    toastContainer.style.position = 'fixed';
    toastContainer.style.bottom = '20px';
    toastContainer.style.right = '20px';
    toastContainer.style.zIndex = '9999';
    toastContainer.style.display = 'flex';
    toastContainer.style.flexDirection = 'column';
    toastContainer.style.gap = '10px';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bg = type === 'success' ? '#15803d' : type === 'error' ? '#dc2626' : '#2563eb';
  toast.style.background = bg;
  toast.style.color = '#ffffff';
  toast.style.padding = '12px 20px';
  toast.style.borderRadius = '8px';
  toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
  toast.style.fontSize = '13px';
  toast.style.fontWeight = '500';
  toast.style.display = 'flex';
  toast.style.alignItems = 'center';
  toast.style.gap = '8px';
  toast.style.opacity = '0';
  toast.style.transform = 'translateY(10px)';
  toast.style.transition = 'all 0.3s ease';

  const iconClass = type === 'success' ? 'fa-check' : type === 'error' ? 'fa-triangle-exclamation' : 'fa-info-circle';
  toast.innerHTML = `<i class="fa-solid ${iconClass}"></i> <span>${message}</span>`;
  toastContainer.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

