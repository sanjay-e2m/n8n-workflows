// Enhanced Workflow App with Full Functionality
class WorkflowApp {
  constructor() {
    this.state = {
      workflows: [],
      currentPage: 1,
      totalPages: 1,
      totalCount: 0,
      perPage: 20,
      isLoading: false,
      searchQuery: '',
      filters: {
        trigger: 'all',
        complexity: 'all',
        category: 'all',
        activeOnly: false
      },
      categories: [],
      categoryMap: new Map()
    };

    this.elements = {
      searchInput: document.getElementById('searchInput'),
      triggerFilter: document.getElementById('triggerFilter'),
      complexityFilter: document.getElementById('complexityFilter'),
      categoryFilter: document.getElementById('categoryFilter'),
      activeOnlyFilter: document.getElementById('activeOnly'),
      themeToggle: document.getElementById('themeToggle'),
      resultsCount: document.getElementById('resultsCount'),
      workflowGrid: document.getElementById('workflowGrid'),
      loadMoreContainer: document.getElementById('loadMoreContainer'),
      loadMoreBtn: document.getElementById('loadMoreBtn'),
      loadingState: document.getElementById('loadingState'),
      errorState: document.getElementById('errorState'),
      noResultsState: document.getElementById('noResultsState'),
      errorMessage: document.getElementById('errorMessage'),
      retryBtn: document.getElementById('retryBtn'),
      totalCount: document.getElementById('totalCount'),
      activeCount: document.getElementById('activeCount'),
      nodeCount: document.getElementById('nodeCount'),
      integrationCount: document.getElementById('integrationCount'),
      backToTop: document.getElementById('backToTop'),
      // Modal elements
      workflowModal: document.getElementById('workflowModal'),
      modalTitle: document.getElementById('modalTitle'),
      modalClose: document.getElementById('modalClose'),
      modalDescription: document.getElementById('modalDescription'),
      modalStats: document.getElementById('modalStats'),
      modalIntegrations: document.getElementById('modalIntegrations'),
      downloadBtn: document.getElementById('downloadBtn'),
      viewJsonBtn: document.getElementById('viewJsonBtn'),
      viewDiagramBtn: document.getElementById('viewDiagramBtn'),
      jsonSection: document.getElementById('jsonSection'),
      jsonViewer: document.getElementById('jsonViewer'),
      diagramSection: document.getElementById('diagramSection'),
      diagramViewer: document.getElementById('diagramViewer'),
      copyJsonBtn: document.getElementById('copyJsonBtn'),
      copyDiagramBtn: document.getElementById('copyDiagramBtn')
    };

    this.searchDebounceTimer = null;
    this.currentWorkflow = null;
    this.currentJsonData = null;
    this.currentDiagramData = null;
    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.setupTheme();
    this.initMermaid();
    this.setupBackToTop();
    await this.loadInitialData();
  }

  initMermaid() {
    // Initialize Mermaid with proper configuration
    if (typeof mermaid !== 'undefined') {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'base',
        themeVariables: {
          primaryColor: '#3b82f6',
          primaryTextColor: '#1e293b',
          primaryBorderColor: '#2563eb',
          lineColor: '#64748b',
          secondaryColor: '#f1f5f9',
          tertiaryColor: '#f8fafc'
        }
      });
    }
  }

  setupEventListeners() {
    // Search and filters
    this.elements.searchInput.addEventListener('input', (e) => {
      this.state.searchQuery = e.target.value;
      this.debounceSearch();
    });

    this.elements.triggerFilter.addEventListener('change', (e) => {
      this.state.filters.trigger = e.target.value;
      this.state.currentPage = 1;
      this.resetAndSearch();
    });

    this.elements.complexityFilter.addEventListener('change', (e) => {
      this.state.filters.complexity = e.target.value;
      this.state.currentPage = 1;
      this.resetAndSearch();
    });

    this.elements.categoryFilter.addEventListener('change', (e) => {
      const selectedCategory = e.target.value;
      this.state.filters.category = selectedCategory;
      this.state.currentPage = 1;
      this.resetAndSearch();
    });

    this.elements.activeOnlyFilter.addEventListener('change', (e) => {
      this.state.filters.activeOnly = e.target.checked;
      this.state.currentPage = 1;
      this.resetAndSearch();
    });

    // Load more
    this.elements.loadMoreBtn.addEventListener('click', () => {
      this.loadMoreWorkflows();
    });

    // Retry
    this.elements.retryBtn.addEventListener('click', () => {
      this.loadInitialData();
    });

    // Theme toggle
    this.elements.themeToggle.addEventListener('click', () => {
      this.toggleTheme();
    });

    // Modal events
    this.elements.modalClose.addEventListener('click', () => {
      this.closeModal();
    });

    this.elements.workflowModal.addEventListener('click', (e) => {
      if (e.target === this.elements.workflowModal) {
        this.closeModal();
      }
    });

    this.elements.viewJsonBtn.addEventListener('click', () => {
      this.toggleJsonView();
    });

    this.elements.viewDiagramBtn.addEventListener('click', () => {
      this.toggleDiagramView();
    });

    // Copy button events
    this.elements.copyJsonBtn.addEventListener('click', () => {
      this.copyToClipboard(this.currentJsonData, 'copyJsonBtn');
    });

    this.elements.copyDiagramBtn.addEventListener('click', () => {
      this.copyToClipboard(this.currentDiagramData, 'copyDiagramBtn');
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeModal();
      }
    });
  }

  setupBackToTop() {
    window.addEventListener('scroll', () => {
      if (window.pageYOffset > 300) {
        this.elements.backToTop.classList.add('visible');
      } else {
        this.elements.backToTop.classList.remove('visible');
      }
    });

    this.elements.backToTop.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  setupTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.updateThemeToggle(savedTheme);
  }

  toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    this.updateThemeToggle(newTheme);
  }

  updateThemeToggle(theme) {
    this.elements.themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
  }

  debounceSearch() {
    clearTimeout(this.searchDebounceTimer);
    this.searchDebounceTimer = setTimeout(() => {
      this.state.currentPage = 1;
      this.resetAndSearch();
    }, 300);
  }

  async apiCall(endpoint, options = {}) {
    const response = await fetch(`/api${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async loadInitialData() {
    this.showState('loading');

    try {
      await this.loadCategories();
      this.populateCategoryFilter();

      const [stats] = await Promise.all([
        this.apiCall('/stats'),
        this.loadWorkflows(true)
      ]);

      this.updateStatsDisplay(stats);
    } catch (error) {
      console.error('Error during initial data loading:', error);
      this.showError('Failed to load data: ' + error.message);
    }
  }

  async loadCategories() {
    try {
      const [categoriesResponse, mappingsResponse] = await Promise.all([
        this.apiCall('/categories'),
        this.apiCall('/category-mappings')
      ]);

      this.state.categories = categoriesResponse.categories || ['Uncategorized'];

      const categoryMap = new Map();
      const mappings = mappingsResponse.mappings || {};

      Object.entries(mappings).forEach(([filename, category]) => {
        categoryMap.set(filename, category || 'Uncategorized');
      });

      this.state.categoryMap = categoryMap;
      return { categories: this.state.categories, mappings: mappings };
    } catch (error) {
      console.error('Failed to load categories from API:', error);
      this.state.categories = ['Uncategorized'];
      this.state.categoryMap = new Map();
      return { categories: this.state.categories, mappings: {} };
    }
  }

  populateCategoryFilter() {
    const select = this.elements.categoryFilter;
    if (!select) return;

    while (select.children.length > 1) {
      select.removeChild(select.lastChild);
    }

    this.state.categories.forEach(category => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      select.appendChild(option);
    });
  }

  async loadWorkflows(reset = false) {
    if (reset) {
      this.state.currentPage = 1;
      this.state.workflows = [];
    }

    this.state.isLoading = true;

    try {
      const needsAllWorkflows = this.state.filters.category !== 'all' && reset;
      let allWorkflows = [];
      let totalCount = 0;
      let totalPages = 1;

      if (needsAllWorkflows) {
        allWorkflows = await this.loadAllWorkflowsForCategoryFiltering();

        const filteredWorkflows = allWorkflows.filter(workflow => {
          const workflowCategory = this.getWorkflowCategory(workflow.filename);
          return workflowCategory === this.state.filters.category;
        });

        allWorkflows = filteredWorkflows;
        totalCount = filteredWorkflows.length;
        totalPages = 1;
      } else {
        const params = new URLSearchParams({
          q: this.state.searchQuery,
          trigger: this.state.filters.trigger,
          complexity: this.state.filters.complexity,
          active_only: this.state.filters.activeOnly,
          page: this.state.currentPage,
          per_page: this.state.perPage
        });

        const response = await this.apiCall(`/workflows?${params}`);
        allWorkflows = response.workflows;
        totalCount = response.total;
        totalPages = response.pages;
      }

      if (reset) {
        this.state.workflows = allWorkflows;
        this.state.totalCount = totalCount;
        this.state.totalPages = totalPages;
      } else {
        this.state.workflows.push(...allWorkflows);
      }

      this.updateUI();
    } catch (error) {
      this.showError('Failed to load workflows: ' + error.message);
    } finally {
      this.state.isLoading = false;
    }
  }

  async loadAllWorkflowsForCategoryFiltering() {
    const allWorkflows = [];
    let currentPage = 1;
    const maxPerPage = 100;

    while (true) {
      const params = new URLSearchParams({
        q: this.state.searchQuery,
        trigger: this.state.filters.trigger,
        complexity: this.state.filters.complexity,
        active_only: this.state.filters.activeOnly,
        page: currentPage,
        per_page: maxPerPage
      });

      const response = await this.apiCall(`/workflows?${params}`);
      allWorkflows.push(...response.workflows);

      if (currentPage >= response.pages) break;
      currentPage++;
    }

    return allWorkflows;
  }

  getWorkflowCategory(filename) {
    const category = this.state.categoryMap.get(filename);
    return category && category.trim() ? category : 'Uncategorized';
  }

  async loadMoreWorkflows() {
    if (this.state.currentPage >= this.state.totalPages) return;
    this.state.currentPage++;
    await this.loadWorkflows(false);
  }

  resetAndSearch() {
    this.loadWorkflows(true);
  }

  updateUI() {
    this.updateResultsCount();
    this.renderWorkflows();
    this.updateLoadMoreButton();

    if (this.state.workflows.length === 0) {
      this.showState('no-results');
    } else {
      this.showState('content');
    }
  }

  updateStatsDisplay(stats) {
    this.elements.totalCount.textContent = stats.total.toLocaleString();
    this.elements.activeCount.textContent = stats.active.toLocaleString();
    this.elements.nodeCount.textContent = stats.total_nodes.toLocaleString();
    this.elements.integrationCount.textContent = stats.unique_integrations.toLocaleString();
  }

  updateResultsCount() {
    const start = (this.state.currentPage - 1) * this.state.perPage + 1;
    const end = Math.min(this.state.currentPage * this.state.perPage, this.state.totalCount);
    this.elements.resultsCount.textContent = 
      `Showing ${start}-${end} of ${this.state.totalCount.toLocaleString()} workflows`;
  }

  renderWorkflows() {
    if (!this.elements.workflowGrid) return;

    this.elements.workflowGrid.innerHTML = '';

    this.state.workflows.forEach(workflow => {
      const card = this.createWorkflowCard(workflow);
      this.elements.workflowGrid.appendChild(card);
    });
  }

  createWorkflowCard(workflow) {
    const card = document.createElement('div');
    card.className = 'workflow-card';
    card.addEventListener('click', () => this.openWorkflowModal(workflow));

    const statusClass = workflow.active ? 'status-active' : 'status-inactive';
    const complexityClass = `complexity-${workflow.complexity}`;
    const category = this.getWorkflowCategory(workflow.filename);

    card.innerHTML = `
      <div class="workflow-header">
        <div class="workflow-meta">
          <div class="status-dot ${statusClass}"></div>
          <span>${workflow.active ? 'Active' : 'Inactive'}</span>
          <div class="complexity-dot ${complexityClass}"></div>
          <span>${workflow.complexity}</span>
          <span>${workflow.node_count} nodes</span>
        </div>
        <div class="trigger-badge">${workflow.trigger_type}</div>
      </div>
      
      <h3 class="workflow-title">${this.escapeHtml(workflow.name)}</h3>
      <p class="workflow-description">${this.escapeHtml(workflow.description)}</p>
      
      ${category !== 'Uncategorized' ? `<div class="category-badge">${category}</div>` : ''}
      
      <div class="workflow-integrations">
        <div class="integrations-title">Integrations</div>
        <div class="integrations-list">
          ${workflow.integrations.slice(0, 5).map(integration => 
            `<span class="integration-tag">${this.escapeHtml(integration)}</span>`
          ).join('')}
          ${workflow.integrations.length > 5 ? 
            `<span class="integration-tag">+${workflow.integrations.length - 5} more</span>` : ''}
        </div>
      </div>
      
      <div class="workflow-actions">
        <button class="action-btn primary" onclick="event.stopPropagation(); window.open('/api/workflows/${workflow.filename}/download', '_blank')">
          <i class="fas fa-download"></i> Download
        </button>
        <button class="action-btn" onclick="event.stopPropagation(); this.closest('.workflow-card').click()">
          <i class="fas fa-eye"></i> View Details
        </button>
      </div>
    `;

    return card;
  }

  updateLoadMoreButton() {
    if (!this.elements.loadMoreContainer) return;

    if (this.state.currentPage >= this.state.totalPages) {
      this.elements.loadMoreContainer.classList.add('hidden');
    } else {
      this.elements.loadMoreContainer.classList.remove('hidden');
    }
  }

  async openWorkflowModal(workflow) {
    this.currentWorkflow = workflow;
    this.elements.modalTitle.textContent = workflow.name;
    this.elements.modalDescription.textContent = workflow.description;

    const category = this.getWorkflowCategory(workflow.filename);
    this.elements.modalStats.innerHTML = `
      <div class="stat-item">
        <strong>Status:</strong> ${workflow.active ? 'Active' : 'Inactive'}
      </div>
      <div class="stat-item">
        <strong>Trigger:</strong> ${workflow.trigger_type}
      </div>
      <div class="stat-item">
        <strong>Complexity:</strong> ${workflow.complexity}
      </div>
      <div class="stat-item">
        <strong>Nodes:</strong> ${workflow.node_count}
      </div>
      <div class="stat-item">
        <strong>Category:</strong> ${category}
      </div>
    `;

    this.elements.modalIntegrations.innerHTML = workflow.integrations
      .map(integration => `<span class="integration-tag">${this.escapeHtml(integration)}</span>`)
      .join('');

    this.elements.downloadBtn.onclick = () => {
      window.open(`/api/workflows/${workflow.filename}/download`, '_blank');
    };

    this.elements.workflowModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  closeModal() {
    this.elements.workflowModal.classList.add('hidden');
    document.body.style.overflow = '';
    this.elements.jsonSection.classList.add('hidden');
    this.elements.diagramSection.classList.add('hidden');
    this.resetCopyButton('copyJsonBtn');
    this.resetCopyButton('copyDiagramBtn');
  }

  async toggleJsonView() {
    if (this.elements.jsonSection.classList.contains('hidden')) {
      if (!this.currentJsonData) {
        try {
          const response = await this.apiCall(`/workflows/${this.currentWorkflow.filename}`);
          this.currentJsonData = JSON.stringify(response.raw_json, null, 2);
          this.elements.jsonViewer.textContent = this.currentJsonData;
        } catch (error) {
          this.elements.jsonViewer.textContent = 'Error loading JSON: ' + error.message;
        }
      }
      this.elements.jsonSection.classList.remove('hidden');
      this.elements.viewJsonBtn.textContent = 'Hide JSON';
    } else {
      this.elements.jsonSection.classList.add('hidden');
      this.elements.viewJsonBtn.textContent = 'View JSON';
    }
  }

  async toggleDiagramView() {
    if (this.elements.diagramSection.classList.contains('hidden')) {
      if (!this.currentDiagramData) {
        try {
          this.elements.diagramViewer.innerHTML = 'Loading diagram...';
          const response = await this.apiCall(`/workflows/${this.currentWorkflow.filename}/diagram`);
          this.currentDiagramData = response.diagram;
          
          if (typeof mermaid !== 'undefined') {
            const graphDiv = document.createElement('div');
            graphDiv.id = 'mermaid-graph-' + Date.now();
            this.elements.diagramViewer.innerHTML = '';
            this.elements.diagramViewer.appendChild(graphDiv);
            
            try {
              await mermaid.render('graph', this.currentDiagramData, graphDiv);
            } catch (error) {
              this.elements.diagramViewer.innerHTML = `
                <pre style="background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-md); overflow: auto; font-size: 0.875rem;">${this.escapeHtml(this.currentDiagramData)}</pre>
              `;
            }
          } else {
            this.elements.diagramViewer.innerHTML = `
              <pre style="background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-md); overflow: auto; font-size: 0.875rem;">${this.escapeHtml(this.currentDiagramData)}</pre>
            `;
          }
        } catch (error) {
          this.elements.diagramViewer.textContent = 'Error loading diagram: ' + error.message;
        }
      }
      this.elements.diagramSection.classList.remove('hidden');
      this.elements.viewDiagramBtn.textContent = 'Hide Diagram';
    } else {
      this.elements.diagramSection.classList.add('hidden');
      this.elements.viewDiagramBtn.textContent = 'View Diagram';
    }
  }

  showState(state) {
    const states = ['loading', 'error', 'no-results', 'content'];
    states.forEach(s => {
      const element = document.getElementById(`${s}State`.replace('-', ''));
      if (element) {
        element.classList.toggle('hidden', s !== state);
      }
    });

    switch (state) {
      case 'content':
        this.elements.workflowGrid.classList.remove('hidden');
        break;
    }
  }

  showError(message) {
    this.elements.errorMessage.textContent = message;
    this.showState('error');
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  async copyToClipboard(text, buttonId) {
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      this.showCopySuccess(buttonId);
    } catch (error) {
      this.fallbackCopyToClipboard(text, buttonId);
    }
  }

  fallbackCopyToClipboard(text, buttonId) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      document.execCommand('copy');
      this.showCopySuccess(buttonId);
    } catch (error) {
      console.error('Failed to copy text: ', error);
    } finally {
      document.body.removeChild(textArea);
    }
  }

  showCopySuccess(buttonId) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    const originalText = button.innerHTML;
    button.innerHTML = '✅ Copied!';
    button.classList.add('copied');

    setTimeout(() => {
      button.innerHTML = originalText;
      button.classList.remove('copied');
    }, 2000);
  }

  resetCopyButton(buttonId) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    button.innerHTML = '📋 Copy';
    button.classList.remove('copied');
  }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
  window.workflowApp = new WorkflowApp();
});