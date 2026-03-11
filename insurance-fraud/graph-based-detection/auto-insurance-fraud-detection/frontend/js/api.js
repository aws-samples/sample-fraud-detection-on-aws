// API Client
class APIClient {
    constructor() {
        this.baseURL = CONFIG.API_ENDPOINT;
    }

    async request(endpoint, method = 'GET', body = null) {
        if (!auth.isAuthenticated()) {
            const refreshed = await auth.tryRefresh();
            if (!refreshed) {
                auth.logout();
                throw new Error('Not authenticated');
            }
        }
        const token = auth.getToken();

        const options = {
            method,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            credentials: 'include' // Include httpOnly cookies
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, options);
            
            if (response.status === 401) {
                const refreshed = await auth.tryRefresh();
                if (refreshed) {
                    // Retry the request with new token
                    options.headers['Authorization'] = `Bearer ${auth.getToken()}`;
                    const retry = await fetch(`${this.baseURL}${endpoint}`, options);
                    if (retry.ok) return await retry.json();
                }
                auth.logout();
                return;
            }

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // List endpoints
    async listClaimants() {
        return this.request('/claimants');
    }

    async listClaims() {
        return this.request('/claims');
    }

    async listRepairShops() {
        return this.request('/repair-shops');
    }

    async listVehicles() {
        return this.request('/vehicles');
    }

    async listMedicalProviders() {
        return this.request('/medical-providers');
    }

    // Claims Management
    async submitClaim(claimData) {
        return this.request('/claims', 'POST', claimData);
    }

    async getClaim(claimId) {
        return this.request(`/claims/${claimId}`);
    }

    async getClaimantClaims(claimantId) {
        return this.request(`/claimants/${claimantId}/claims`);
    }

    async getClaimantRiskScore(claimantId) {
        return this.request(`/claimants/${claimantId}/risk-score`);
    }

    async getClaimantVelocity(claimantId) {
        return this.request(`/claimants/${claimantId}/claim-velocity`);
    }

    async getClaimantFraudAnalysis(claimantId) {
        return this.request(`/claimants/${claimantId}/fraud-analysis`);
    }

    // Fraud Patterns
    async getCollisionRings() {
        return this.request('/fraud-patterns/collision-rings');
    }

    async getProfessionalWitnesses() {
        return this.request('/fraud-patterns/professional-witnesses');
    }

    async getCollusionIndicators() {
        return this.request('/fraud-patterns/collusion-indicators');
    }

    async getCrossClaimPatterns(claimantId) {
        return this.request(`/fraud-patterns/cross-claim-patterns/${claimantId}`);
    }

    // Fraud Networks
    async getInfluentialClaimants() {
        return this.request('/fraud-networks/influential-claimants');
    }

    async getOrganizedRings() {
        return this.request('/fraud-networks/organized-rings');
    }

    async getConnections() {
        return this.request('/fraud-networks/connections');
    }

    async getIsolatedRings() {
        return this.request('/fraud-networks/isolated-rings');
    }

    // Analytics
    async getFraudTrends() {
        return this.request('/analytics/fraud-trends');
    }

    async getGeographicHotspots() {
        return this.request('/analytics/geographic-hotspots');
    }

    async getClaimAmountAnomalies() {
        return this.request('/analytics/claim-amount-anomalies');
    }

    async getTemporalPatterns() {
        return this.request('/analytics/temporal-patterns');
    }

    // Entity Analysis
    async getRepairShopStatistics(shopId) {
        return this.request(`/repair-shops/${shopId}/statistics`);
    }

    async getRepairShopNetwork(shopId) {
        return this.request(`/repair-shops/${shopId}`);
    }

    async getFraudHubs() {
        return this.request('/repair-shops/fraud-hubs');
    }

    async getVehicleFraudHistory(vehicleId) {
        return this.request(`/vehicles/${vehicleId}/fraud-history`);
    }

    async getMedicalProviderFraudAnalysis(providerId) {
        return this.request(`/medical-providers/${providerId}/fraud-analysis`);
    }

    async getMedicalProviderNetwork(providerId) {
        return this.request(`/medical-providers/${providerId}`);
    }

    async listAttorneys() {
        return this.request('/attorneys');
    }

    async listWitnesses() {
        return this.request('/witnesses');
    }

    async listPassengers() {
        return this.request('/passengers');
    }

    async listTowCompanies() {
        return this.request('/tow-companies');
    }

    async getIsolatedRing(entityId, entityType) {
        return this.request(`/fraud-networks/isolated-rings?id=${entityId}&type=${entityType}`);
    }
}

const api = new APIClient();
