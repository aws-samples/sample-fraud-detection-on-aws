// Graph visualization module using D3.js

class GraphVisualizer {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.width = Math.max(this.container.node().clientWidth || 1000, 800);
        this.height = Math.max(this.container.node().clientHeight || 700, 600);
        this.svg = null;
        this.simulation = null;
        this.filterId = `corrupt-glow-${containerId}`;
    }

    clear() {
        if (this.svg) {
            this.svg.remove();
        }
    }

    getFraudColor(fraudScore) {
        if (fraudScore >= 0.7) return '#ef4444'; // Red - likely fraud
        if (fraudScore >= 0.4) return '#f59e0b'; // Yellow - caution
        return '#10b981'; // Green - unlikely fraud
    }

    getTypeLabel(type) {
        if (!type) return 'Unknown';
        
        // Strip ::fraudEntity suffix if present
        const cleanType = type.split('::')[0];
        
        const typeMap = {
            'claimant': i18n.t('entityClaimant'),
            'claim': i18n.t('entityClaim'),
            'vehicle': i18n.t('entityVehicle'),
            'repairShop': i18n.t('entityRepairShop'),
            'witness': i18n.t('entityWitness'),
            'accident': i18n.t('entityAccident'),
            'medicalProvider': i18n.t('entityMedicalProvider'),
            'attorney': i18n.t('entityAttorney'),
            'towCompany': i18n.t('entityTowCompany'),
            'passenger': i18n.t('entityPassenger'),
            'fraudEntity': 'Entity'
        };
        
        return typeMap[cleanType] || cleanType.charAt(0).toUpperCase() + cleanType.slice(1);
    }

    renderGraph(data) {
        this.clear();

        // Create SVG - responsive to container
        this.svg = this.container.append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .attr('preserveAspectRatio', 'xMidYMid meet');

        const g = this.svg.append('g');

        // Arrow marker for directed edges
        const defs = this.svg.append('defs');
        defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#999');

        // Glow filter for corrupt nodes
        const filter = defs.append('filter').attr('id', this.filterId).attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
        const blur = filter.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur');
        const merge = filter.append('feMerge');
        merge.append('feMergeNode').attr('in', 'blur');
        merge.append('feMergeNode').attr('in', 'SourceGraphic');

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Create force simulation
        this.simulation = d3.forceSimulation(data.nodes)
            .force('link', d3.forceLink(data.edges).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2));

        // Draw edges
        const link = g.append('g')
            .selectAll('line')
            .data(data.edges)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrowhead)')
            .style('cursor', 'pointer')
            .on('click', (event, d) => this.showEdgePopup(event, d));

        const corruptTypes = new Set(['repairShop', 'witness', 'attorney', 'towCompany', 'medicalProvider', 'passenger']);

        // Draw nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(data.nodes)
            .enter().append('circle')
            .attr('r', d => d.size || 10)
            .attr('fill', d => this.getFraudColor(d.fraudScore || 0))
            .attr('stroke', d => {
                if (d.isMember) return '#2563eb';
                const score = d.fraudScore || 0;
                if (corruptTypes.has(d.type) && score >= 0.7) return '#ef4444';
                return '#fff';
            })
            .attr('stroke-width', d => {
                if (d.isMember) return 4;
                const score = d.fraudScore || 0;
                if (corruptTypes.has(d.type) && score >= 0.7) return 3;
                return 2;
            })
            .attr('class', d => {
                const score = d.fraudScore || 0;
                const classes = [];
                if (d.isMember) classes.push('node-ring-member');
                if (corruptTypes.has(d.type) && score >= 0.7) classes.push('node-corrupt');
                return classes.join(' ');
            })
            .attr('filter', d => (corruptTypes.has(d.type) && (d.fraudScore || 0) >= 0.7) ? `url(#${this.filterId})` : null)
            .style('cursor', 'pointer')
            .on('click', (event, d) => this.showNodePopup(event, d))
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d)));

        // Add label backgrounds for readability
        const labelBg = g.append('g')
            .selectAll('text')
            .data(data.nodes)
            .enter().append('text')
            .text(d => d.name ? `${d.label}: ${d.name}` : d.label || d.id)
            .attr('font-size', 10)
            .attr('dx', 12)
            .attr('dy', 4)
            .attr('stroke', 'white')
            .attr('stroke-width', 3)
            .attr('stroke-linejoin', 'round')
            .attr('paint-order', 'stroke')
            .style('pointer-events', 'none');

        // Add labels
        const label = g.append('g')
            .selectAll('text')
            .data(data.nodes)
            .enter().append('text')
            .text(d => d.name ? `${d.label}: ${d.name}` : d.label || d.id)
            .attr('font-size', 10)
            .attr('dx', 12)
            .attr('dy', 4)
            .style('pointer-events', 'none');

        // Update positions on tick
        this.simulation.on('tick', () => {
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            labelBg
                .attr('x', d => d.x)
                .attr('y', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

        // Pulse glow animation for corrupt nodes
        let pulseUp = true;
        const pulseInterval = setInterval(() => {
            if (!this.svg || this.svg.node() === null || !document.body.contains(this.svg.node())) {
                clearInterval(pulseInterval);
                return;
            }
            const sd = pulseUp ? 8 : 3;
            blur.attr('stdDeviation', sd);
            pulseUp = !pulseUp;
        }, 750);
    }

    formatPropertyValue(key, value) {
        // Detect timestamps: numeric values in date-related fields, or large numbers that look like epoch ms/s
        const dateKeys = ['date', 'time', 'created', 'updated', 'timestamp', 'claimdate', 'accidentdate', 'fileddate'];
        const isDateKey = dateKeys.some(dk => key.toLowerCase().includes(dk));
        if (isDateKey && typeof value === 'number') {
            const ms = value > 1e12 ? value : value * 1000; // handle seconds or milliseconds
            const d = new Date(ms);
            if (!isNaN(d.getTime())) return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        }
        if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
            return Object.entries(value).map(([k, v]) => `${k}: ${v}`).join(', ');
        }
        return value;
    }

    formatPropertyLabel(key) {
        const labels = {
            'isFraud': 'Is Fraud?',
            'fraudScore': 'Fraud Score',
            'claimDate': 'Claim Date',
            'claimAmount': 'Claim Amount',
            'amount': 'Amount',
            'status': 'Status',
            'name': 'Name',
            'specialty': 'Specialty',
            'rating': 'Rating',
            'suspicious': 'Suspicious',
            'licenseNumber': 'License Number',
            'make': 'Make',
            'model': 'Model',
            'year': 'Year',
            'vin': 'VIN',
            'plate': 'Plate',
            'policyNumber': 'Policy Number',
            'repairCost': 'Repair Cost',
            'injuryType': 'Injury Type',
            'witnessCount': 'Witness Count',
            'passengerCount': 'Passenger Count',
            'accidentDate': 'Accident Date',
            'accidentType': 'Accident Type',
            'location': 'Location',
            'description': 'Description',
            'riskLevel': 'Risk Level',
            'riskScore': 'Risk Score',
            'mlRiskScore': 'ML Risk Score',
            'totalClaims': 'Total Claims',
            'highFraudClaims': 'High Fraud Claims',
            'averageFraudScore': 'Avg Fraud Score',
            'componentId': 'Component ID',
            'isolationLevel': 'Isolation Level'
        };
        if (labels[key]) return labels[key];
        // camelCase to Title Case: "someProperty" -> "Some Property"
        return key.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase()).trim();
    }

    showNodePopup(event, node) {
        // Remove existing popup
        d3.selectAll('.graph-popup').remove();

        const popup = d3.select('body')
            .append('div')
            .attr('class', 'graph-popup')
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY + 10) + 'px');

        popup.append('span').attr('class', 'graph-popup-close').text('×')
            .on('click', () => d3.selectAll('.graph-popup').remove());

        popup.append('h4').text(node.label || node.id);
        if (node.name) {
            popup.append('p').html(`<strong>Name:</strong> ${node.name}`);
        }
        popup.append('p').html(`<strong>ID:</strong> <code style="font-size:0.85em;user-select:all">${node.id}</code>`);
        if (node.type) {
            popup.append('p').html(`<strong>Type:</strong> ${this.getTypeLabel(node.type)}`);
        }
        
        if (node.fraudScore !== undefined) {
            popup.append('p').html(`<strong>Fraud Score:</strong> ${(node.fraudScore * 100).toFixed(1)}%`);
        }

        // Add all properties
        Object.keys(node).forEach(key => {
            if (!['id', 'label', 'name', 'type', 'fraudScore', 'x', 'y', 'vx', 'vy', 'fx', 'fy', 'index', 'size'].includes(key) && node[key] != null) {
                popup.append('p').html(`<strong>${this.formatPropertyLabel(key)}:</strong> ${this.formatPropertyValue(key, node[key])}`);
            }
        });

        event.stopPropagation();
    }

    showEdgePopup(event, edge) {
        // Remove existing popup
        d3.selectAll('.graph-popup').remove();

        const popup = d3.select('body')
            .append('div')
            .attr('class', 'graph-popup')
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY + 10) + 'px');

        popup.append('span').attr('class', 'graph-popup-close').text('×')
            .on('click', () => d3.selectAll('.graph-popup').remove());

        popup.append('h4').text(edge.label ? edge.label.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : 'Relationship');
        popup.append('p').html(`<strong>From:</strong> ${edge.source.label || edge.source.id}`);
        popup.append('p').html(`<strong>To:</strong> ${edge.target.label || edge.target.id}`);

        // Add all properties
        Object.keys(edge).forEach(key => {
            if (!['source', 'target', 'label', 'index'].includes(key) && edge[key] != null) {
                popup.append('p').html(`<strong>${this.formatPropertyLabel(key)}:</strong> ${this.formatPropertyValue(key, edge[key])}`);
            }
        });

        event.stopPropagation();
    }

    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}
