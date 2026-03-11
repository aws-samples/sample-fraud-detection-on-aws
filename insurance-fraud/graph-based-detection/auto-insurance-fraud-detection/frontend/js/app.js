// Main application logic
class App {
    constructor() {
        this.graph = null;
        this.currentView = null;
        this.init();
        // Close graph popups when any modal closes
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close') || 
                (e.target.classList.contains('modal-overlay') && e.target === e.currentTarget)) {
                d3.selectAll('.graph-popup').remove();
            }
        });
    }

    legendHTML(showRingMember = false) {
        return `<div class="legend">
                                <span class="legend-item"><span class="color-box green"></span> ${i18n.t('lowRisk')}</span>
                                <span class="legend-item"><span class="color-box yellow"></span> ${i18n.t('mediumRisk')}</span>
                                <span class="legend-item"><span class="color-box red"></span> ${i18n.t('highRisk')}</span>
                                <span class="legend-item"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;border:3px solid #ef4444;background:#ef4444;box-shadow:0 0 8px rgba(239,68,68,0.6);margin-right:5px;vertical-align:middle;"></span> ${i18n.t('corruptEntity')}</span>
                                ${showRingMember ? `<span class="legend-item"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;border:3px solid #2563eb;margin-right:5px;vertical-align:middle;"></span> ${i18n.t('ringMember')}</span>` : ''}
                            </div>
                            <p class="corrupt-entity-note">${i18n.t('corruptEntityTooltip')}</p>`;
    }

    getFraudDescription(entityType) {
        const keyMap = {
            'repair-shop': 'descRepairShop',
            'medical-provider': 'descMedicalProvider',
            'vehicle': 'descVehicle',
            'claim': 'descClaim'
        };
        const key = keyMap[entityType];
        return key ? `<p class="fraud-description" data-i18n="${key}">${i18n.t(key)}</p>` : '';
    }

    getViewDescription(descKey, rationaleKey) {
        let html = descKey ? `<p class="fraud-description" data-i18n="${descKey}">${i18n.t(descKey)}</p>` : '';
        if (rationaleKey && rationaleKey !== descKey) {
            html += `<p class="fraud-description" data-i18n="${rationaleKey}">${i18n.t(rationaleKey)}</p>`;
        }
        return html;
    }

    init() {
        // Check authentication
        if (!auth.isAuthenticated()) {
            window.location.href = 'login.html';
            return;
        }

        // Initialize language
        const languageSelector = document.getElementById('languageSelector');
        languageSelector.value = i18n.currentLang;
        i18n.updateUI();
        
        languageSelector.addEventListener('change', (e) => {
            i18n.setLanguage(e.target.value);
            // Re-render current view if one is loaded
            if (this.currentView) {
                this.loadView(this.currentView);
            }
        });

        // Display current user
        document.getElementById('currentUser').textContent = auth.getUser();

        // Setup logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            auth.logout();
        });

        // Setup menu navigation
        document.querySelectorAll('.menu a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = e.target.getAttribute('data-view');
                this.loadView(view);
            });
        });
    }

    async loadView(viewName) {
        this.currentView = viewName;
        d3.selectAll('.graph-popup').remove();
        const container = document.getElementById('viewContainer');
        
        // Show loading
        container.innerHTML = DOMPurify.sanitize(`<div class=\"loading\">${i18n.t('loading')}</div>`);

        try {
            switch(viewName) {
                // Fraud Patterns (no parameters)
                case 'collision-rings':
                    await this.showCollisionRings();
                    break;
                case 'professional-witnesses':
                    await this.showProfessionalWitnesses();
                    break;
                case 'collusion-indicators':
                    await this.showCollusionIndicators();
                    break;
                case 'cross-claim-patterns':
                    await this.showCrossClaimPatterns();
                    break;

                // Fraud Networks (no parameters)
                case 'influential-claimants':
                    await this.showInfluentialClaimants();
                    break;
                case 'organized-rings':
                    await this.showOrganizedRings();
                    break;
                case 'connections':
                    await this.showConnections();
                    break;
                case 'isolated-rings':
                    await this.showIsolatedRings();
                    break;

                // Analytics (no parameters)
                case 'fraud-trends':
                    await this.showFraudTrends();
                    break;
                case 'geographic-hotspots':
                    await this.showGeographicHotspots();
                    break;
                case 'claim-anomalies':
                    await this.showClaimAnomalies();
                    break;
                case 'temporal-patterns':
                    await this.showTemporalPatterns();
                    break;
                case 'fraud-hubs':
                    await this.showFraudHubs();
                    break;

                // Views with parameters
                case 'claims-detail':
                    this.showClaimDetailForm();
                    break;
                case 'claimants-claims':
                    this.showClaimantClaimsForm();
                    break;
                case 'claimants-risk-score':
                    this.showClaimantRiskScoreForm();
                    break;
                case 'claimants-velocity':
                    this.showClaimantVelocityForm();
                    break;
                case 'claimants-fraud-analysis':
                    this.showClaimantFraudAnalysisForm();
                    break;
                case 'repair-shop-stats':
                    this.showRepairShopStatsForm();
                    break;
                case 'vehicle-fraud-history':
                    this.showVehicleFraudHistoryForm();
                    break;
                case 'medical-provider-fraud':
                    this.showMedicalProviderFraudForm();
                    break;

                case 'claims-submit':
                    this.showSubmitClaimForm();
                    break;
            }
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error: ${error.message}</div>`);
        }
    }

    // Fraud Pattern views
    async showCollisionRings() {
        const data = await api.getCollisionRings();
        this.renderGraphView('collisionRings', data);
    }

    async showProfessionalWitnesses() {
        const data = await api.getProfessionalWitnesses();
        this.renderGraphView('professionalWitnesses', data);
    }

    async showCollusionIndicators() {
        const data = await api.getCollusionIndicators();
        this.renderGraphView('collusionIndicators', data);
    }

    async showCrossClaimPatterns() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class=\"loading\">${i18n.t('loading')}</div>`);
        
        try {
            const data = await api.listClaimants();
            const claimantIds = data.claimants;
            
            if (claimantIds.length === 0) {
                container.innerHTML = DOMPurify.sanitize(`<div class=\"error\">${i18n.t('noClaimantsFound')}</div>`);
                return;
            }
            
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2 data-i18n="crossClaimPatterns">${i18n.t('crossClaimPatterns')}</h2>
                    <p class="fraud-description" data-i18n="descCrossClaimPatterns">${i18n.t('descCrossClaimPatterns')}</p>
                </div>
                <div class="form-container">
                    <div class="form-group">
                        <label for="entitySelect">Select Claimant:</label>
                        <select id="entitySelect">
                            <option value="" data-i18n="selectClaimant">${i18n.t('selectClaimant')}</option>
                            ${claimantIds.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <button id="viewBtn" class="btn-primary" disabled>View</button>
                </div>
                
                <div id="modalOverlay" class="modal-overlay">
                  <div class="modal-dialog">
                    <div class="modal-header">
                        <h2 class="modal-title">Cross-Claim Patterns</h2>
                        <button id="modalClose" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-content">
                        <div class="view-header">
                            ${this.legendHTML()}
                        </div>
                        <div id="graphContainer" class="graph-container"></div>
                    </div>
                  </div>
                </div>
            `);
            
            const selectEl = document.getElementById('entitySelect');
            const viewBtn = document.getElementById('viewBtn');
            const modalOverlay = document.getElementById('modalOverlay');
            const modalClose = document.getElementById('modalClose');
            
            selectEl.addEventListener('change', () => {
                viewBtn.disabled = !selectEl.value;
            });
            
            modalClose.addEventListener('click', () => {
                            modalOverlay.classList.remove('active');
                        });
            
                        modalOverlay.addEventListener('click', (e) => {
                            if (e.target === modalOverlay) modalOverlay.classList.remove('active');
                        });
            
            viewBtn.addEventListener('click', async () => {
                const id = selectEl.value;
                if (id) {
                    viewBtn.disabled = true;
                    viewBtn.textContent = i18n.t('loading');
                    try {
                        const networkData = await api.getCrossClaimPatterns(id);
                        
                        const graphContainer = document.getElementById('graphContainer');
                        graphContainer.innerHTML = '';
                        
                        modalOverlay.classList.add('active');
                        
                        this.graph = new GraphVisualizer('graphContainer');
                        const graphData = this.transformToGraphData(networkData);
                        this.graph.renderGraph(graphData);
                    } catch (error) {
                        alert(`Error: ${error.message}`);
                    } finally {
                        viewBtn.disabled = false;
                        viewBtn.textContent = i18n.t('view');
                    }
                }
            });
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error loading claimants: ${error.message}</div>`);
        }
    }

    // Fraud Network views
    async showInfluentialClaimants() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class="loading">${i18n.t('loading')}</div>`);
        
        try {
            // Get claimant IDs
            const data = await api.listClaimants();
            const claimantIds = data.claimants;
            
            if (claimantIds.length === 0) {
                container.innerHTML = DOMPurify.sanitize(`<div class="error">${i18n.t('noClaimantsFound')}</div>`);
                return;
            }
            
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2 data-i18n="influentialClaimants">${i18n.t('influentialClaimants')}</h2>
                    <p class="fraud-description" data-i18n="descInfluentialClaimants">${i18n.t('descInfluentialClaimants')}</p>
                </div>
                <div class="form-container">
                    <div class="form-group">
                        <label for="claimantIdInput" data-i18n="enterClaimantId">${i18n.t('enterClaimantId')}</label>
                        <input type="text" id="claimantIdInput" placeholder="${i18n.t('enterClaimantId')}">
                    </div>
                    <div class="form-group">
                        <label for="entitySelect" data-i18n="orSelectClaimant">${i18n.t('orSelectClaimant')}</label>
                        <select id="entitySelect">
                            <option value="" data-i18n="selectClaimant">${i18n.t('selectClaimant')}</option>
                            ${claimantIds.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <button id="viewBtn" class="btn-primary" data-i18n="viewNetwork">${i18n.t('viewNetwork')}</button>
                </div>
                <div id="resultContainer"></div>
            `);
            
            const inputEl = document.getElementById('claimantIdInput');
            const selectEl = document.getElementById('entitySelect');
            const viewBtn = document.getElementById('viewBtn');
            
            inputEl.addEventListener('input', () => {
                if (inputEl.value) selectEl.value = '';
            });
            
            selectEl.addEventListener('change', () => {
                if (selectEl.value) inputEl.value = '';
            });
            
            viewBtn.addEventListener('click', async () => {
                const id = inputEl.value || selectEl.value;
                if (id) {
                    viewBtn.disabled = true;
                    viewBtn.textContent = i18n.t('loading');
                    try {
                        // Use cross-claim patterns endpoint to show claimant's network
                        const networkData = await api.getCrossClaimPatterns(id);
                        
                        // Render graph in resultContainer instead of replacing whole view
                        const resultContainer = document.getElementById('resultContainer');
                        resultContainer.innerHTML = DOMPurify.sanitize(`
                            <div class="view-header">
                                ${this.legendHTML()}
                            </div>
                            <div id="graphContainer" class="graph-container"></div>
                        `);
                        
                        // Initialize graph
                        this.graph = new GraphVisualizer('graphContainer');
                        const graphData = this.transformToGraphData(networkData);
                        this.graph.renderGraph(graphData);
                    } catch (error) {
                        document.getElementById('resultContainer').innerHTML = DOMPurify.sanitize(
                            `<div class="error">${i18n.t('error')}: ${error.message}</div>`);
                    } finally {
                        viewBtn.disabled = false;
                        viewBtn.textContent = i18n.t('viewNetwork');
                    }
                }
            });
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">${i18n.t('error')}: ${error.message}</div>`);
        }
    }

    async showOrganizedRings() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class="loading">${i18n.t('loading')}</div>`);
        
        try {
            const data = await api.getOrganizedRings();
            
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2 data-i18n="organizedRings">${i18n.t('organizedRings')}</h2>
                    <p class="fraud-description" data-i18n="descOrganizedRings">${i18n.t('descOrganizedRings')}</p>
                    <p class="fraud-description" data-i18n="rationaleOrganizedRings">${i18n.t('rationaleOrganizedRings')}</p>
                </div>
            `);
            
            if (!data.rings || data.rings.length === 0) {
                container.innerHTML = DOMPurify.sanitize(container.innerHTML + '<div class="info">No organized fraud rings detected.</div>');
                return;
            }
            
            // Display each ring in its own modal-style dialog
            data.rings.forEach((ring, index) => {
                const ringDiv = document.createElement('div');
                ringDiv.className = 'modal-dialog';
                ringDiv.style.cssText = 'position:relative;margin:20px auto;max-height:none;';
                ringDiv.innerHTML = DOMPurify.sanitize(`
                    <div class="modal-header">
                        <h2 class="modal-title">Ring ${index + 1} — ${ring.members?.length || 0} member(s), ${(ring.averageFraudScore * 100).toFixed(1)}% avg fraud, Risk: ${ring.riskLevel}</h2>
                    </div>
                    <div class="modal-content">
                        <div class="view-header">
                            ${this.legendHTML(true)}
                        </div>
                        <div id="ring-graph-${index}" class="graph-container" style="min-height:500px;"></div>
                    </div>
                `);
                container.appendChild(ringDiv);

                if (ring.graph) {
                    // Mark member nodes
                    const memberSet = new Set(ring.members || []);
                    ring.graph.nodes.forEach(n => { n.isMember = memberSet.has(n.id); });
                    const graph = new GraphVisualizer(`ring-graph-${index}`);
                    graph.renderGraph(ring.graph);
                }
            });
            
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error loading organized rings: ${error.message}</div>`);
        }
    }

    async showConnections() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class=\"loading\">${i18n.t('loading')}</div>`);
        
        try {
            // Get claimant IDs
            const data = await api.listClaimants();
            const claimantIds = data.claimants;
            
            if (claimantIds.length === 0) {
                container.innerHTML = DOMPurify.sanitize(`<div class=\"error\">${i18n.t('noClaimantsFound')}</div>`);
                return;
            }
            
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2 data-i18n="connections">${i18n.t('connections')}</h2>
                    <p class="fraud-description" data-i18n="descConnections">${i18n.t('descConnections')}</p>
                </div>
                <div class="form-container">
                    <div class="form-group">
                        <label for="sourceSelect">Source Claimant:</label>
                        <select id="sourceSelect">
                            <option value="">-- Select Source --</option>
                            ${claimantIds.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="targetSelect">Target Claimant:</label>
                        <select id="targetSelect">
                            <option value="">-- Select Target --</option>
                            ${claimantIds.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <button id="viewBtn" class="btn-primary" disabled>Find Connection</button>
                </div>
                <div id="resultContainer"></div>
            `);
            
            const sourceSelect = document.getElementById('sourceSelect');
            const targetSelect = document.getElementById('targetSelect');
            const viewBtn = document.getElementById('viewBtn');
            
            const updateButton = () => {
                viewBtn.disabled = !sourceSelect.value || !targetSelect.value;
            };
            
            sourceSelect.addEventListener('change', updateButton);
            targetSelect.addEventListener('change', updateButton);
            
            viewBtn.addEventListener('click', async () => {
                const sourceId = sourceSelect.value;
                const targetId = targetSelect.value;
                
                if (sourceId && targetId) {
                    viewBtn.disabled = true;
                    viewBtn.textContent = i18n.t('loading');
                    try {
                        // Get both networks and merge them
                        const [sourceNetwork, targetNetwork] = await Promise.all([
                            api.getCrossClaimPatterns(sourceId),
                            api.getCrossClaimPatterns(targetId)
                        ]);
                        
                        // Merge the networks
                        const mergedNetwork = {
                            nodes: [...sourceNetwork.nodes, ...targetNetwork.nodes],
                            edges: [...sourceNetwork.edges, ...targetNetwork.edges]
                        };
                        
                        // Remove duplicate nodes
                        const nodeMap = new Map();
                        mergedNetwork.nodes.forEach(n => nodeMap.set(n.id, n));
                        mergedNetwork.nodes = Array.from(nodeMap.values());
                        
                        // Render graph in resultContainer
                        const resultContainer = document.getElementById('resultContainer');
                        resultContainer.innerHTML = DOMPurify.sanitize(`
                            <div class="view-header">
                                ${this.legendHTML()}
                            </div>
                            <div id="graphContainer" class="graph-container"></div>
                        `);
                        
                        this.graph = new GraphVisualizer('graphContainer');
                        const graphData = this.transformToGraphData(mergedNetwork);
                        this.graph.renderGraph(graphData);
                    } catch (error) {
                        document.getElementById('resultContainer').innerHTML = DOMPurify.sanitize(
                            `<div class="error">Error: ${error.message}</div>`);
                    } finally {
                        viewBtn.disabled = false;
                        viewBtn.textContent = i18n.t('view');
                    }
                }
            });
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error loading claimants: ${error.message}</div>`);
        }
    }

    async showIsolatedRings() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class=\"loading\">${i18n.t('loading')}</div>`);
        
        try {
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2 data-i18n="isolatedRings">${i18n.t('isolatedRings')}</h2>
                    <p class="fraud-description" data-i18n="descIsolatedRings">${i18n.t('descIsolatedRings')}</p>
                    <p class="fraud-description" data-i18n="rationaleIsolatedRings">${i18n.t('rationaleIsolatedRings')}</p>
                </div>
                <div class="form-container">
                    <div class="form-group">
                        <label for="entityTypeSelect">Select Entity Type:</label>
                        <select id="entityTypeSelect">
                            <option value="">-- Select Type --</option>
                            <option value="claimant">Claimant</option>
                            <option value="claim">Claim</option>
                            <option value="repair-shop">Repair Shop</option>
                            <option value="vehicle">Vehicle</option>
                            <option value="medical-provider">Medical Provider</option>
                            <option value="attorney">Attorney</option>
                            <option value="witness">Witness</option>
                            <option value="passenger">Passenger</option>
                            <option value="tow-company">Tow Company</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="entitySelect">Select Entity:</label>
                        <select id="entitySelect" disabled>
                            <option value="">-- Select type first --</option>
                        </select>
                    </div>
                    <button id="viewBtn" class="btn-primary" disabled>View Ring</button>
                </div>
                
                <div id="modalOverlay" class="modal-overlay">
                  <div class="modal-dialog">
                    <div class="modal-header">
                        <h2 class="modal-title">Isolated Ring</h2>
                        <button id="modalClose" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-content">
                        <div class="view-header">
                            ${this.legendHTML()}
                        </div>
                        <div id="graphContainer" class="graph-container"></div>
                    </div>
                  </div>
                </div>
            `);
            
            const entityTypeSelect = document.getElementById('entityTypeSelect');
            const entitySelect = document.getElementById('entitySelect');
            const viewBtn = document.getElementById('viewBtn');
            const modalOverlay = document.getElementById('modalOverlay');
            const modalClose = document.getElementById('modalClose');
            
            // Handle entity type change
            entityTypeSelect.addEventListener('change', async () => {
                const entityType = entityTypeSelect.value;
                
                if (!entityType) {
                    entitySelect.disabled = true;
                    entitySelect.innerHTML = DOMPurify.sanitize(`<option value="">${i18n.t('loading')}</option>`);
                    viewBtn.disabled = true;
                    return;
                }
                
                entitySelect.disabled = true;
                entitySelect.innerHTML = DOMPurify.sanitize(`<option value="">${i18n.t('loading')}</option>`);
                viewBtn.disabled = true;
                
                try {
                    let data, items, placeholder;
                    switch(entityType) {
                        case 'claimant':
                            data = await api.listClaimants();
                            items = data.claimants; placeholder = '-- Select claimant --';
                            break;
                        case 'repair-shop':
                            data = await api.listRepairShops();
                            items = data.repairShops; placeholder = '-- Select repair shop --';
                            break;
                        case 'medical-provider':
                            data = await api.listMedicalProviders();
                            items = data.medicalProviders; placeholder = '-- Select medical provider --';
                            break;
                        case 'attorney':
                            data = await api.listAttorneys();
                            items = data.attorneys; placeholder = '-- Select attorney --';
                            break;
                        case 'witness':
                            data = await api.listWitnesses();
                            items = data.witnesses; placeholder = '-- Select witness --';
                            break;
                        case 'passenger':
                            data = await api.listPassengers();
                            items = data.passengers; placeholder = '-- Select passenger --';
                            break;
                        case 'tow-company':
                            data = await api.listTowCompanies();
                            items = data.towCompanies; placeholder = '-- Select tow company --';
                            break;
                        case 'claim':
                            data = await api.listClaims();
                            items = data.claims.map(c => ({id: c.id, name: `$${c.amount}${c.date ? ' - ' + new Date(c.date * 1000).toLocaleDateString() : ''} (${c.id.substring(0,8)}...)`}));
                            placeholder = '-- Select claim --';
                            break;
                        case 'vehicle':
                            data = await api.listVehicles();
                            items = data.vehicles.map(v => ({id: v.id, name: `${v.year} ${v.make} · ${v.plate}`}));
                            placeholder = '-- Select vehicle --';
                            break;
                    }
                    entitySelect.innerHTML = '';
                    const defaultOpt = document.createElement('option');
                    defaultOpt.value = '';
                    defaultOpt.textContent = placeholder;
                    entitySelect.appendChild(defaultOpt);
                    items.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = item.name;
                        entitySelect.appendChild(opt);
                    });
                    entitySelect.disabled = false;
                } catch (error) {
                    entitySelect.innerHTML = DOMPurify.sanitize(`<option value="">${i18n.t('error')}</option>`);
                }
            });
            
            // Handle entity selection
            entitySelect.addEventListener('change', () => {
                viewBtn.disabled = !entitySelect.value;
            });
            
            // Handle view button
            viewBtn.addEventListener('click', async () => {
                const entityId = entitySelect.value;
                const entityType = entityTypeSelect.value;
                if (!entityId) return;
                
                viewBtn.disabled = true;
                viewBtn.textContent = i18n.t('loading');
                
                try {
                    const graphData = await api.getIsolatedRing(entityId, entityType);
                    
                    if (this.graph && this.graph.simulation) {
                        this.graph.simulation.stop();
                        this.graph = null;
                    }
                    
                    // Recreate the graph container to ensure clean state
                    const oldContainer = document.getElementById('graphContainer');
                    const newContainer = document.createElement('div');
                    newContainer.id = 'graphContainer';
                    newContainer.className = 'graph-container';
                    oldContainer.parentNode.replaceChild(newContainer, oldContainer);
                    
                    // Update modal title with selected entity
                    const modalTitle = document.querySelector('.modal-title');
                    if (modalTitle) {
                        const selectedText = entitySelect.options[entitySelect.selectedIndex].text;
                        modalTitle.textContent = `Isolated Ring: ${selectedText}`;
                    }
                    
                    modalOverlay.classList.add('active');
                    
                    this.graph = new GraphVisualizer('graphContainer');
                    this.graph.renderGraph(graphData);
                    
                    viewBtn.disabled = false;
                    viewBtn.textContent = i18n.t('view');
                } catch (error) {
                    alert('Error loading ring: ' + error.message);
                    viewBtn.disabled = false;
                    viewBtn.textContent = i18n.t('view');
                }
            });
            
            // Handle modal close
            modalClose.addEventListener('click', () => {
                modalOverlay.classList.remove('active');
                const graphContainer = document.getElementById('graphContainer');
                if (graphContainer) graphContainer.innerHTML = '';
                if (this.graph && this.graph.simulation) {
                    this.graph.simulation.stop();
                    this.graph = null;
                }
            });
            
                        modalOverlay.addEventListener('click', (e) => {
                            if (e.target === modalOverlay) {
                                modalOverlay.classList.remove('active');
                                const gc = document.getElementById('graphContainer');
                                if (gc) gc.innerHTML = '';
                                if (this.graph && this.graph.simulation) {
                                    this.graph.simulation.stop();
                                    this.graph = null;
                                }
                            }
                        });
            
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error loading view: ${error.message}</div>`);
        }
    }

    // Analytics views
    async showFraudTrends() {
        const data = await api.getFraudTrends();
        this.renderDataView('fraudTrends', data);
    }

    async showGeographicHotspots() {
        const data = await api.getGeographicHotspots();
        this.renderGraphView('geographicHotspots', data);
    }

    async showClaimAnomalies() {
        const data = await api.getClaimAmountAnomalies();
        this.renderDataView('claimAnomalies', data);
    }

    async showTemporalPatterns() {
        const data = await api.getTemporalPatterns();
        
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`
            <div class="view-header">
                <h2 data-i18n="temporalPatterns">${i18n.t('temporalPatterns')}</h2>
                <p class="fraud-description" data-i18n="descTemporalPatterns">${i18n.t('descTemporalPatterns')}</p>
            </div>
            <div class="data-container">
                <h3>Rapid Filers (High Claim Velocity)</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Claimant ID</th>
                            <th>Claim Count</th>
                            <th>Suspicion Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.rapidFilers.map(r => `
                            <tr>
                                <td>${r.claimantId}</td>
                                <td>${r.claimCount}</td>
                                <td><span class="badge badge-${r.suspicionLevel}">${r.suspicionLevel}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                
                ${data.suspiciousHours && data.suspiciousHours.length > 0 ? `
                    <h3>Suspicious Hours</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Hour</th>
                                <th>Claim Count</th>
                                <th>Fraud Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.suspiciousHours.map(h => `
                                <tr>
                                    <td>${h.hour}:00</td>
                                    <td>${h.claimCount}</td>
                                    <td>${(h.fraudRate * 100).toFixed(1)}%</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                ` : ''}
            </div>
        `);
    }

    async showFraudHubs() {
        const data = await api.getFraudHubs();
        this.renderGraphView('fraudHubs', data);
    }

    // Forms for parameterized endpoints
    async showClaimantClaimsForm() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class=\"loading\">${i18n.t('loading')}</div>`);
        
        try {
            const data = await api.listClaimants();
            const claimantIds = data.claimants;
            
            if (claimantIds.length === 0) {
                container.innerHTML = DOMPurify.sanitize(`<div class=\"error\">${i18n.t('noClaimantsFound')}</div>`);
                return;
            }
            
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2 data-i18n="claimantClaims">${i18n.t('claimantClaims')}</h2>
                    <p class="fraud-description" data-i18n="descClaimantClaims">${i18n.t('descClaimantClaims')}</p>
                </div>
                <div class="form-container">
                    <div class="form-group">
                        <label for="claimantIdInput" data-i18n="enterClaimantId">${i18n.t('enterClaimantId')}</label>
                        <input type="text" id="claimantIdInput" placeholder="Enter claimant ID">
                    </div>
                    <div class="form-group">
                        <label for="entitySelect" data-i18n="orSelectClaimant">${i18n.t('orSelectClaimant')}</label>
                        <select id="entitySelect">
                            <option value="" data-i18n="selectClaimant">${i18n.t('selectClaimant')}</option>
                            ${claimantIds.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <button id="viewBtn" class="btn-primary">View Claims</button>
                </div>
                
                <div id="modalOverlay" class="modal-overlay">
                  <div class="modal-dialog">
                    <div class="modal-header">
                        <h2 class="modal-title">Claimant Claims</h2>
                        <button id="modalClose" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-content">
                        <div class="view-header">
                            ${this.legendHTML()}
                        </div>
                        <div id="graphContainer" class="graph-container"></div>
                    </div>
                  </div>
                </div>
            `);
            
            const inputEl = document.getElementById('claimantIdInput');
            const selectEl = document.getElementById('entitySelect');
            const viewBtn = document.getElementById('viewBtn');
            const modalOverlay = document.getElementById('modalOverlay');
            const modalClose = document.getElementById('modalClose');
            
            inputEl.addEventListener('input', () => {
                if (inputEl.value) selectEl.value = '';
            });
            
            selectEl.addEventListener('change', () => {
                if (selectEl.value) inputEl.value = '';
            });
            
            modalClose.addEventListener('click', () => {
                            modalOverlay.classList.remove('active');
                        });
            
                        modalOverlay.addEventListener('click', (e) => {
                            if (e.target === modalOverlay) modalOverlay.classList.remove('active');
                        });
            
            viewBtn.addEventListener('click', async () => {
                const id = inputEl.value || selectEl.value;
                if (id) {
                    viewBtn.disabled = true;
                    viewBtn.textContent = i18n.t('loading');
                    try {
                        const claimData = await api.getClaimantClaims(id);
                        
                        const graphContainer = document.getElementById('graphContainer');
                        graphContainer.innerHTML = '';
                        
                        modalOverlay.classList.add('active');
                        
                        this.graph = new GraphVisualizer('graphContainer');
                        const graphData = this.transformToGraphData(claimData);
                        this.graph.renderGraph(graphData);
                    } catch (error) {
                        alert(`Error: ${error.message}`);
                    } finally {
                        viewBtn.disabled = false;
                        viewBtn.textContent = i18n.t('view');
                    }
                }
            });
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error loading claimants: ${error.message}</div>`);
        }
    }

    showClaimantRiskScoreForm() {
        this.showModalSelectForm(i18n.t('riskScore'), 'riskScore', 'claimant', async (id) => {
            const data = await api.getClaimantRiskScore(id);
            return { type: 'data', data };
        });
    }

    showClaimantVelocityForm() {
        this.showModalSelectForm(i18n.t('claimVelocity'), 'claimVelocity', 'claimant', async (id) => {
            const data = await api.getClaimantVelocity(id);
            return { type: 'data', data };
        });
    }

    async showClaimantFraudAnalysisForm() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class=\"loading\">${i18n.t('loading')}</div>`);
        
        try {
            const data = await api.listClaimants();
            const claimantIds = data.claimants;
            
            if (claimantIds.length === 0) {
                container.innerHTML = DOMPurify.sanitize(`<div class=\"error\">${i18n.t('noClaimantsFound')}</div>`);
                return;
            }
            
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2 data-i18n="fraudAnalysis">${i18n.t('fraudAnalysis')}</h2>
                    <p class="fraud-description" data-i18n="descFraudAnalysis">${i18n.t('descFraudAnalysis')}</p>
                </div>
                <div class="form-container">
                    <div class="form-group">
                        <label for="entitySelect">${i18n.t('selectClaimant').replace(/^--\s*|\s*--$/g,'')}:</label>
                        <select id="entitySelect">
                            <option value="" data-i18n="selectClaimant">${i18n.t('selectClaimant')}</option>
                            ${claimantIds.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                        </select>
                    </div>
                    <button id="viewBtn" class="btn-primary" disabled>${i18n.t('analyze')}</button>
                </div>
                
                <div id="modalOverlay" class="modal-overlay">
                  <div class="modal-dialog">
                    <div class="modal-header">
                        <h2 class="modal-title">${i18n.t('fraudAnalysis')}</h2>
                        <button id="modalClose" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-content">
                        <div class="view-header">
                            ${this.legendHTML()}
                        </div>
                        <div id="graphContainer" class="graph-container"></div>
                    </div>
                  </div>
                </div>
            `);
            
            const selectEl = document.getElementById('entitySelect');
            const viewBtn = document.getElementById('viewBtn');
            const modalOverlay = document.getElementById('modalOverlay');
            const modalClose = document.getElementById('modalClose');
            
            selectEl.addEventListener('change', () => {
                viewBtn.disabled = !selectEl.value;
            });
            
            modalClose.addEventListener('click', () => {
                            modalOverlay.classList.remove('active');
                        });
            
                        modalOverlay.addEventListener('click', (e) => {
                            if (e.target === modalOverlay) modalOverlay.classList.remove('active');
                        });
            
            viewBtn.addEventListener('click', async () => {
                const id = selectEl.value;
                if (id) {
                    viewBtn.disabled = true;
                    viewBtn.textContent = i18n.t('loading');
                    try {
                        const analysisData = await api.getClaimantFraudAnalysis(id);
                        
                        // Clear previous graph
                        const graphContainer = document.getElementById('graphContainer');
                        graphContainer.innerHTML = '';
                        
                        modalOverlay.classList.add('active');
                        
                        this.graph = new GraphVisualizer('graphContainer');
                        const graphData = this.transformToGraphData(analysisData);
                        this.graph.renderGraph(graphData);
                    } catch (error) {
                        alert(`Error: ${error.message}`);
                    } finally {
                        viewBtn.disabled = false;
                        viewBtn.textContent = i18n.t('analyze');
                    }
                }
            });
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error loading claimants: ${error.message}</div>`);
        }
    }

    showClaimDetailForm() {
        this.showModalSelectForm(i18n.t('claimDetails'), 'claimDetails', 'claim', async (id) => {
            const data = await api.getClaim(id);
            return { type: 'data', data };
        });
    }

    showRepairShopStatsForm() {
        this.showModalSelectForm(i18n.t('repairShopStats'), 'repairShopStats', 'repair-shop', async (id) => {
            const graph = await api.getRepairShopNetwork(id);
            return { type: 'graph', data: graph };
        });
    }

    showVehicleFraudHistoryForm() {
        this.showModalSelectForm(i18n.t('vehicleFraudHistory'), 'vehicleFraudHistory', 'vehicle', async (id) => {
            const data = await api.getVehicleFraudHistory(id);
            return { type: 'data', data };
        });
    }

    showMedicalProviderFraudForm() {
        this.showModalSelectForm(i18n.t('medicalProviderFraud'), 'medicalProviderFraud', 'medical-provider', async (id) => {
            const graph = await api.getMedicalProviderNetwork(id);
            return { type: 'graph', data: graph };
        });
    }

    async showModalSelectForm(title, titleKey, entityType, callback) {
        const _descMap = {
        collisionRings:    ['descCollisionRings',    'rationaleCollisionRings'],
        professionalWitnesses: ['descProfessionalWitnesses', 'rationaleProfessionalWitnesses'],
        collusionIndicators:   ['descCollusionIndicators',   'rationaleCollusionIndicators'],
        fraudTrends:       ['descFraudTrends',       'rationaleFraudTrends'],
        geographicHotspots:['descGeographicHotspots','rationaleGeographicHotspots'],
        claimAnomalies:    ['descClaimAnomalies',    'rationaleClaimAnomalies'],
        fraudHubs:         ['descFraudHubs',         'rationaleFraudHubs'],
        claimDetails:      ['descClaimDetails',      null],
        riskScore:         ['descRiskScore',         null],
        claimVelocity:     ['descClaimVelocity',     null],
        repairShopStats:   ['descRepairShopStats',   null],
        vehicleFraudHistory:['descVehicleFraudHistory',null],
        medicalProviderFraud:['descMedicalProviderFraud',null],
        crossClaimPatterns:['descCrossClaimPatterns','rationaleCrossClaimPatterns'],
        temporalPatterns:  ['descTemporalPatterns',  'rationaleTemporalPatterns'],
        connections:       ['descConnections',       'rationaleConnections'],
        isolatedRings:     ['descIsolatedRings',     'rationaleIsolatedRings'],
        organizedRings:    ['descOrganizedRings',    'rationaleOrganizedRings'],
        influentialClaimants:['descInfluentialClaimants',null],
    };
        const [_dk, _rk] = _descMap[titleKey] || [null, null];
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`<div class=\"loading\">${i18n.t('loading')}</div>`);
        
        try {
            let data;
            let entityList;
            
            switch(entityType) {
                case 'claimant':
                    data = await api.listClaimants();
                    entityList = data.claimants;
                    break;
                case 'claim':
                    data = await api.listClaims();
                    entityList = data.claims;
                    break;
                case 'repair-shop':
                    data = await api.listRepairShops();
                    entityList = data.repairShops;
                    break;
                case 'vehicle':
                    data = await api.listVehicles();
                    entityList = data.vehicles;
                    break;
                case 'medical-provider':
                    data = await api.listMedicalProviders();
                    entityList = data.medicalProviders;
                    break;
            }
            
            if (!entityList || entityList.length === 0) {
                container.innerHTML = DOMPurify.sanitize(`<div class="error">${i18n.t('noData')}</div>`);
                return;
            }
            
            const getOptionLabel = (item) => {
                if (entityType === 'claim') return `$${item.amount} - ${item.date}`;
                if (entityType === 'vehicle') return `${item.year} ${item.make} · ${item.plate}`;
                return item.name;
            };

            const selectLabels = {
                'claimant':        i18n.t('selectClaimant'),
                'claim':           i18n.t('selectClaim'),
                'vehicle':         i18n.t('selectVehicle'),
                'repair-shop':     i18n.t('selectShop'),
                'medical-provider':i18n.t('selectProvider'),
            };
            const selectLabel = selectLabels[entityType] || `-- Select ${entityType} --`;
            
            container.innerHTML = DOMPurify.sanitize(`
                <div class="view-header">
                    <h2>${title}</h2>
                    ${this.getViewDescription(_dk, _rk) || this.getFraudDescription(entityType)}
                </div>
                <div class="form-container">
                    <div class="form-group">
                        <label for="entitySelect">${selectLabel.replace(/^--\s*/, '').replace(/\s*--$/, '')}:</label>
                        <select id="entitySelect">
                            <option value="">${selectLabel}</option>
                            ${entityList.map(item => `<option value="${item.id}">${getOptionLabel(item)}</option>`).join('')}
                        </select>
                    </div>
                    <button id="viewBtn" class="btn-primary" disabled>${i18n.t('view')}</button>
                </div>
                
                <div id="modalOverlay" class="modal-overlay">
                  <div class="modal-dialog">
                    <div class="modal-header">
                        <h2 class="modal-title">${title}</h2>
                        <button id="modalClose" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-content">
                        <div id="modalContentArea"></div>
                    </div>
                  </div>
                </div>
            `);
            
            const selectEl = document.getElementById('entitySelect');
            const viewBtn = document.getElementById('viewBtn');
            const modalOverlay = document.getElementById('modalOverlay');
            const modalClose = document.getElementById('modalClose');
            const modalContentArea = document.getElementById('modalContentArea');
            
            selectEl.addEventListener('change', () => {
                viewBtn.disabled = !selectEl.value;
            });
            
            modalClose.addEventListener('click', () => {
                            modalOverlay.classList.remove('active');
                        });
            
                        modalOverlay.addEventListener('click', (e) => {
                            if (e.target === modalOverlay) modalOverlay.classList.remove('active');
                        });
            
            viewBtn.addEventListener('click', async () => {
                const id = selectEl.value;
                if (id) {
                    viewBtn.disabled = true;
                    viewBtn.textContent = i18n.t('loading');
                    try {
                        const result = await callback(id);
                        
                        modalContentArea.innerHTML = '';
                        
                        if (result.type === 'graph') {
                            modalContentArea.innerHTML = DOMPurify.sanitize(`
                                <div class="view-header">
                                    ${this.legendHTML()}
                                </div>
                                <div id="graphContainer" class="graph-container"></div>
                            `);
                            
                            modalOverlay.classList.add('active');
                            
                            this.graph = new GraphVisualizer('graphContainer');
                            const graphData = this.transformToGraphData(result.data);
                            this.graph.renderGraph(graphData);
                        } else {
                            const scoreKeys = ['riskScore','fraudScore','averageFraudScore','mlRiskScore','mlVelocityScore','mlAnomalyScore','rejectionRate','highFraudRate','fraudRate','shopDiversity','witnessDiversity'];
                            const riskMap = { high: 'riskHigh', medium: 'riskMedium', low: 'riskLow', unknown: 'riskUnknown' };
                            const fmtVal = v => {
                                if (typeof v === 'boolean') return i18n.t(v ? 'boolTrue' : 'boolFalse');
                                if (typeof v === 'string' && riskMap[v]) return i18n.t(riskMap[v]);
                                return v;
                            };
                            const html = Object.entries(result.data)
                                .filter(([k,v]) => v !== null && v !== undefined)
                                .map(([k,v]) => {
                                    const label = k.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase()).trim();
                                    let val;
                                    if (scoreKeys.includes(k)) val = `${(v * 100).toFixed(1)}%`;
                                    else if (v !== null && typeof v === 'object' && !Array.isArray(v)) val = Object.entries(v).map(([ek,ev]) => `${ek.replace(/([A-Z])/g,' $1').toLowerCase().trim()}: ${fmtVal(ev)}`).join(', ');
                                    else val = fmtVal(v);
                                    return `<p><strong>${label}:</strong> ${val}</p>`;
                                }).join('');
                            modalContentArea.innerHTML = DOMPurify.sanitize(html);
                            modalOverlay.classList.add('active');
                        }
                    } catch (error) {
                        alert(`Error: ${error.message}`);
                    } finally {
                        viewBtn.disabled = false;
                        viewBtn.textContent = i18n.t('view');
                    }
                }
            });
        } catch (error) {
            container.innerHTML = DOMPurify.sanitize(`<div class="error">Error loading list: ${error.message}</div>`);
        }
    }

    async showEntitySelectForm(titleKey, entityType, callback) {
        const _descMap = {
        collisionRings:    ['descCollisionRings',    'rationaleCollisionRings'],
        professionalWitnesses: ['descProfessionalWitnesses', 'rationaleProfessionalWitnesses'],
        collusionIndicators:   ['descCollusionIndicators',   'rationaleCollusionIndicators'],
        fraudTrends:       ['descFraudTrends',       'rationaleFraudTrends'],
        geographicHotspots:['descGeographicHotspots','rationaleGeographicHotspots'],
        claimAnomalies:    ['descClaimAnomalies',    'rationaleClaimAnomalies'],
        fraudHubs:         ['descFraudHubs',         'rationaleFraudHubs'],
        claimDetails:      ['descClaimDetails',      null],
        riskScore:         ['descRiskScore',         null],
        claimVelocity:     ['descClaimVelocity',     null],
        repairShopStats:   ['descRepairShopStats',   null],
        vehicleFraudHistory:['descVehicleFraudHistory',null],
        medicalProviderFraud:['descMedicalProviderFraud',null],
        crossClaimPatterns:['descCrossClaimPatterns','rationaleCrossClaimPatterns'],
        temporalPatterns:  ['descTemporalPatterns',  'rationaleTemporalPatterns'],
        connections:       ['descConnections',       'rationaleConnections'],
        isolatedRings:     ['descIsolatedRings',     'rationaleIsolatedRings'],
        organizedRings:    ['descOrganizedRings',    'rationaleOrganizedRings'],
        influentialClaimants:['descInfluentialClaimants',null],
    };
        const title = i18n.t(titleKey);
        const [dk, rk] = _descMap[titleKey] || [null, null];
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`
            <div class="view-header">
                <h2>${title}</h2>
                ${this.getViewDescription(dk, rk)}
            </div>
            <div class="form-container">
                <div class="form-group">
                    <label for="entitySelect">${i18n.t('select' + entityType.charAt(0).toUpperCase() + entityType.slice(1).replace('-','').replace('provider','Provider')).replace(/^--|--$/g,'')}:</label>
                    <select id="entitySelect">
                        <option value="">${i18n.t('loading')}</option>
                    </select>
                </div>
                <button id="viewBtn" class="btn-primary" disabled>${i18n.t('view')}</button>
            </div>
            <div id="resultContainer"></div>
        `);

        // Load entities from API
        const selectEl = document.getElementById('entitySelect');
        selectEl.innerHTML = DOMPurify.sanitize(`<option value="">${i18n.t('loading')}</option>`);
        
        // Load list based on entity type
        try {
            let data;
            switch(entityType) {
                case 'claimant':
                    data = await api.listClaimants();
                    selectEl.innerHTML = DOMPurify.sanitize(`<option value="" data-i18n="selectClaimant">${i18n.t('selectClaimant')}</option>`);
                    data.claimants.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = `${item.name} (${item.id.substring(0,8)}...)`;
                        selectEl.appendChild(opt);
                    });
                    break;
                case 'claim':
                    data = await api.listClaims();
                    selectEl.innerHTML = DOMPurify.sanitize(`<option value="" data-i18n="selectClaim">${i18n.t('selectClaim')}</option>`);
                    data.claims.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = `$${item.amount} - ${item.date} (${item.id.substring(0,8)}...)`;
                        selectEl.appendChild(opt);
                    });
                    break;
                case 'repair-shop':
                    data = await api.listRepairShops();
                    selectEl.innerHTML = DOMPurify.sanitize(`<option value="">${i18n.t('selectShop')}</option>`);
                    data.repairShops.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = item.name;
                        selectEl.appendChild(opt);
                    });
                    break;
                case 'vehicle':
                    data = await api.listVehicles();
                    selectEl.innerHTML = DOMPurify.sanitize(`<option value="" data-i18n="selectVehicle">${i18n.t('selectVehicle')}</option>`);
                    data.vehicles.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = `${item.year} ${item.make} · ${item.plate}`;
                        selectEl.appendChild(opt);
                    });
                    break;
                case 'medical-provider':
                    data = await api.listMedicalProviders();
                    selectEl.innerHTML = DOMPurify.sanitize(`<option value="">${i18n.t('selectProvider')}</option>`);
                    data.medicalProviders.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = item.name;
                        selectEl.appendChild(opt);
                    });
                    break;
            }
        } catch (error) {
            selectEl.innerHTML = DOMPurify.sanitize(`<option value="">${i18n.t('error')}</option>`);
            console.error('Error loading entities:', error);
        }

        const viewBtn = document.getElementById('viewBtn');
        
        selectEl.addEventListener('change', () => {
            viewBtn.disabled = !selectEl.value;
        });

        viewBtn.addEventListener('click', async () => {
            const id = selectEl.value;
            if (id) {
                viewBtn.disabled = true;
                viewBtn.textContent = i18n.t('loading');
                try {
                    await callback(id);
                } catch (error) {
                    document.getElementById('resultContainer').innerHTML = DOMPurify.sanitize(
                        `<div class="error">Error: ${error.message}</div>`);
                } finally {
                    viewBtn.disabled = false;
                    viewBtn.textContent = i18n.t('view');
                }
            }
        });
    }

    async showSubmitClaimForm() {
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`
            <div class="view-header"><h2>${i18n.t('submitClaim')}</h2></div>
            <div class="form-container">
                <div class="form-group">
                    <label>Claimant</label>
                    <select id="sc-claimant"><option value="">${i18n.t('loading')}</option></select>
                </div>
                <div class="form-group">
                    <label>Vehicle</label>
                    <select id="sc-vehicle"><option value="">${i18n.t('loading')}</option></select>
                </div>
                <div class="form-group">
                    <label>Repair Shop</label>
                    <select id="sc-shop"><option value="">${i18n.t('loading')}</option></select>
                </div>
                <div class="form-group">
                    <label>Claim Amount ($)</label>
                    <input type="number" id="sc-amount" min="1" max="1000000" step="0.01" placeholder="e.g. 5000.00" />
                </div>
                <button id="sc-submit" class="btn-primary" disabled>${i18n.t('submitClaim')}</button>
                <div id="sc-error" class="error-message"></div>
            </div>
        `);

        // Load dropdowns in parallel
        const [claimants, vehicles, shops] = await Promise.all([
            api.listClaimants().catch(() => ({})),
            api.listVehicles().catch(() => ({})),
            api.listRepairShops().catch(() => ({}))
        ]);

        const fill = (id, items, labelFn) => {
            const sel = document.getElementById(id);
            sel.innerHTML = DOMPurify.sanitize(
                `<option value="">-- Select --</option>` +
                items.map(it => `<option value="${it.id}">${labelFn(it)}</option>`).join('')
            );
        };

        fill('sc-claimant', claimants.claimants  || [], c => c.name || c.id);
        fill('sc-vehicle',  vehicles.vehicles    || [], v => [v.year, v.make, v.model].filter(x => x && x !== 'Unknown').join(' ') || v.id);
        fill('sc-shop',     shops.repairShops    || [], s => s.name || s.id);

        const btn = document.getElementById('sc-submit');
        const enableBtn = () => {
            const ok = document.getElementById('sc-claimant').value &&
                       document.getElementById('sc-vehicle').value &&
                       document.getElementById('sc-shop').value &&
                       parseFloat(document.getElementById('sc-amount').value) > 0;
            btn.disabled = !ok;
        };
        ['sc-claimant','sc-vehicle','sc-shop','sc-amount'].forEach(id =>
            document.getElementById(id).addEventListener('change', enableBtn)
        );
        document.getElementById('sc-amount').addEventListener('input', enableBtn);

        btn.addEventListener('click', async () => {
            const errEl = document.getElementById('sc-error');
            errEl.textContent = '';
            btn.disabled = true;
            btn.textContent = i18n.t('loading');

            const body = {
                claimantId:  document.getElementById('sc-claimant').value,
                vehicleId:   document.getElementById('sc-vehicle').value,
                repairShopId: document.getElementById('sc-shop').value,
                claimAmount: parseFloat(document.getElementById('sc-amount').value)
            };

            try {
                const timestamp = String(Math.floor(Date.now() / 1000));
                const rawBody = JSON.stringify(body);
                const message = `${timestamp}:${rawBody}`;
                const key = await crypto.subtle.importKey(
                    'raw', new TextEncoder().encode('default-key-change-in-production'),
                    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
                );
                const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(message));
                const signature = Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2,'0')).join('');

                const token = auth.getToken();
                const res = await fetch(`${CONFIG.API_ENDPOINT}/claims`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                        'X-Request-Timestamp': timestamp,
                        'X-Request-Signature': signature
                    },
                    credentials: 'include',
                    body: rawBody
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

                // Show result popup
                d3.selectAll('.graph-popup').remove();
                const score = data.fraudScore ?? 0;
                const color = score >= 0.7 ? '#ef4444' : score >= 0.4 ? '#f59e0b' : '#10b981';
                const popup = d3.select('body').append('div').attr('class', 'graph-popup')
                    .style('left', '50%').style('top', '50%')
                    .style('transform', 'translate(-50%, -50%)')
                    .style('position', 'fixed').style('min-width', '280px');
                popup.append('span').attr('class', 'graph-popup-close').text('×')
                    .on('click', () => d3.selectAll('.graph-popup').remove());
                popup.append('h4').text('Claim Submitted');
                popup.append('p').html(`<strong>Claim ID:</strong> <code style="font-size:0.85em;user-select:all">${data.claimId}</code>`);
                popup.append('p').html(`<strong>Status:</strong> ${data.status}`);
                popup.append('p').html(`<strong>Fraud Score:</strong> <span style="color:${color};font-weight:600">${(score * 100).toFixed(1)}%</span>`);
                popup.append('p').html(`<strong>Message:</strong> ${data.message}`);

                // Reset form
                document.getElementById('sc-claimant').value = '';
                document.getElementById('sc-vehicle').value = '';
                document.getElementById('sc-shop').value = '';
                document.getElementById('sc-amount').value = '';
                btn.disabled = true;
                btn.textContent = i18n.t('submitClaim');
            } catch (e) {
                errEl.textContent = e.message;
                btn.disabled = false;
                btn.textContent = i18n.t('submitClaim');
            }
        });
    }

    renderGraphView(titleKey, data) {
        const _descMap = {
        collisionRings:    ['descCollisionRings',    'rationaleCollisionRings'],
        professionalWitnesses: ['descProfessionalWitnesses', 'rationaleProfessionalWitnesses'],
        collusionIndicators:   ['descCollusionIndicators',   'rationaleCollusionIndicators'],
        fraudTrends:       ['descFraudTrends',       'rationaleFraudTrends'],
        geographicHotspots:['descGeographicHotspots','rationaleGeographicHotspots'],
        claimAnomalies:    ['descClaimAnomalies',    'rationaleClaimAnomalies'],
        fraudHubs:         ['descFraudHubs',         'rationaleFraudHubs'],
        claimDetails:      ['descClaimDetails',      null],
        riskScore:         ['descRiskScore',         null],
        claimVelocity:     ['descClaimVelocity',     null],
        repairShopStats:   ['descRepairShopStats',   null],
        vehicleFraudHistory:['descVehicleFraudHistory',null],
        medicalProviderFraud:['descMedicalProviderFraud',null],
        crossClaimPatterns:['descCrossClaimPatterns','rationaleCrossClaimPatterns'],
        temporalPatterns:  ['descTemporalPatterns',  'rationaleTemporalPatterns'],
        connections:       ['descConnections',       'rationaleConnections'],
        isolatedRings:     ['descIsolatedRings',     'rationaleIsolatedRings'],
        organizedRings:    ['descOrganizedRings',    'rationaleOrganizedRings'],
        influentialClaimants:['descInfluentialClaimants',null],
    };
        const title = i18n.t(titleKey);
        const [dk, rk] = _descMap[titleKey] || [null, null];
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`
            <div class="view-header">
                <h2>${title}</h2>
                ${this.getViewDescription(dk, rk)}
            </div>
            <div class="modal-dialog" style="position:relative;margin:20px auto;max-height:none;">
                <div class="modal-header">
                    <h2 class="modal-title">${title}</h2>
                </div>
                <div class="modal-content">
                    <div class="view-header">
                        ${this.legendHTML()}
                    </div>
                    <div id="graphContainer" class="graph-container" style="min-height:500px;"></div>
                </div>
            </div>
        `);

        this.graph = new GraphVisualizer('graphContainer');
        const graphData = this.transformToGraphData(data);
        this.graph.renderGraph(graphData);
    }

    renderDataView(titleKey, data) {
        const _descMap = {
        collisionRings:    ['descCollisionRings',    'rationaleCollisionRings'],
        professionalWitnesses: ['descProfessionalWitnesses', 'rationaleProfessionalWitnesses'],
        collusionIndicators:   ['descCollusionIndicators',   'rationaleCollusionIndicators'],
        fraudTrends:       ['descFraudTrends',       'rationaleFraudTrends'],
        geographicHotspots:['descGeographicHotspots','rationaleGeographicHotspots'],
        claimAnomalies:    ['descClaimAnomalies',    'rationaleClaimAnomalies'],
        fraudHubs:         ['descFraudHubs',         'rationaleFraudHubs'],
        claimDetails:      ['descClaimDetails',      null],
        riskScore:         ['descRiskScore',         null],
        claimVelocity:     ['descClaimVelocity',     null],
        repairShopStats:   ['descRepairShopStats',   null],
        vehicleFraudHistory:['descVehicleFraudHistory',null],
        medicalProviderFraud:['descMedicalProviderFraud',null],
        crossClaimPatterns:['descCrossClaimPatterns','rationaleCrossClaimPatterns'],
        temporalPatterns:  ['descTemporalPatterns',  'rationaleTemporalPatterns'],
        connections:       ['descConnections',       'rationaleConnections'],
        isolatedRings:     ['descIsolatedRings',     'rationaleIsolatedRings'],
        organizedRings:    ['descOrganizedRings',    'rationaleOrganizedRings'],
        influentialClaimants:['descInfluentialClaimants',null],
    };
        const title = i18n.t(titleKey);
        const [dk, rk] = _descMap[titleKey] || [null, null];
        const container = document.getElementById('viewContainer');
        container.innerHTML = DOMPurify.sanitize(`
            <div class="view-header">
                <h2>${title}</h2>
                ${this.getViewDescription(dk, rk)}
            </div>
            <div class="data-container">
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        `);
    }

    transformToGraphData(data) {
        // If data already has nodes/edges format, return as is
        if (data.nodes && data.edges) {
            return data;
        }

        // Otherwise, create a simple visualization from the data
        // This is a placeholder - actual transformation depends on API response format
        return {
            nodes: data.nodes || [],
            edges: data.edges || data.relationships || []
        };
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new App();
});
