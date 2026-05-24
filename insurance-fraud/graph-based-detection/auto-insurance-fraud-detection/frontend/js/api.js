// API Client
class APIClient {
    constructor() {
        this.baseURL = CONFIG.API_ENDPOINT;
    }

    async request(endpoint, method = 'GET', body = null) {
        // Authentication is now carried by an httpOnly cookie (set by the
        // login Lambda) that the browser auto-forwards because we use
        // `credentials: 'include'`. We keep a client-side session-expiry
        // check as a UX hint: if the expiry flag in sessionStorage says the
        // cookie is past its TTL, proactively refresh before calling the API.
        if (!auth.isAuthenticated()) {
            const refreshed = await auth.tryRefresh();
            if (!refreshed) {
                auth.logout();
                throw new Error('Not authenticated');
            }
        }

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, options);

            if (response.status === 401) {
                const refreshed = await auth.tryRefresh();
                if (refreshed) {
                    // Retry with the fresh cookie (browser forwards automatically)
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

    // --- List endpoints (dropdown helpers) ---
    async listClaimants()        { return this.request('/claimants'); }
    async listClaims()           { return this.request('/claims'); }
    async listRepairShops()      { return this.request('/repair-shops'); }
    async listVehicles()         { return this.request('/vehicles'); }
    async listMedicalProviders() { return this.request('/medical-providers'); }
    async listAttorneys()        { return this.request('/attorneys'); }
    async listWitnesses()        { return this.request('/witnesses'); }
    async listPassengers()       { return this.request('/passengers'); }
    async listTowCompanies()     { return this.request('/tow-companies'); }

    // --- Claims ---
    async submitClaim(claimData)          { return this.request('/claims', 'POST', claimData); }
    async getClaim(claimId)               { return this.request(`/claims/${claimId}`); }
    async getClaimGraph(claimId)          { return this.request(`/claims/${claimId}/graph`); }
    async getClaimantClaims(claimantId)   { return this.request(`/claimants/${claimantId}/claims`); }
    async getClaimantRiskScore(claimantId){ return this.request(`/claimants/${claimantId}/risk-score`); }
    async getClaimantVelocity(claimantId) { return this.request(`/claimants/${claimantId}/claim-velocity`); }
    async getClaimantFraudAnalysis(claimantId) { return this.request(`/claimants/${claimantId}/fraud-analysis`); }

    // --- Collision Rings (6 sub-patterns, each its own endpoint) ---
    async getStagedAccidents()     { return this.request('/collision-rings/staged-accidents'); }
    async getSwoopAndSquat()       { return this.request('/collision-rings/swoop-and-squat'); }
    async getStuffedPassengers()   { return this.request('/collision-rings/stuffed-passengers'); }
    async getPaperCollisions()     { return this.request('/collision-rings/paper-collisions'); }
    async getCorruptAttorneys()    { return this.request('/collision-rings/corrupt-attorneys'); }
    async getCorruptTowCompanies() { return this.request('/collision-rings/corrupt-tow-companies'); }

    // --- Network Fraud ---
    async getProfessionalWitnesses() { return this.request('/network-fraud/professional-witnesses'); }
    async getOrganizedRings()        { return this.request('/network-fraud/organized-rings'); }
    async getFraudHubs()             { return this.request('/network-fraud/fraud-hubs'); }
    async getCollusionIndicators()   { return this.request('/network-fraud/collusion-indicators'); }
    async getIsolatedRings()         { return this.request('/network-fraud/isolated-rings'); }
    async getIsolatedRing(entityId, entityType) {
        return this.request(`/network-fraud/isolated-rings?id=${entityId}&type=${entityType}`);
    }
    async getCrossClaimPatterns(claimantId) {
        return this.request(`/network-fraud/cross-claim-patterns/${claimantId}`);
    }
    async getMedicalProviderFraudAnalysis(providerId) {
        return this.request(`/network-fraud/medical-providers/${providerId}/fraud-analysis`);
    }
    async getMedicalProviderNetwork(providerId) {
        return this.request(`/network-fraud/medical-providers/${providerId}`);
    }

    // --- Advanced Analysis ---
    async getInfluentialClaimants() { return this.request('/advanced-analysis/influential-claimants'); }
    async getConnections(sourceId, targetId) {
        if (sourceId && targetId) {
            return this.request(`/advanced-analysis/connections?source=${sourceId}&target=${targetId}`);
        }
        return this.request('/advanced-analysis/connections');
    }

    // --- Entity Lookup ---
    async getRepairShopStatistics(shopId) { return this.request(`/entity-lookup/repair-shops/${shopId}/statistics`); }
    async getRepairShopNetwork(shopId)    { return this.request(`/entity-lookup/repair-shops/${shopId}`); }
    async getVehicleFraudHistory(vehicleId){ return this.request(`/entity-lookup/vehicles/${vehicleId}/fraud-history`); }
    async getVehicleNetwork(vehicleId)    { return this.request(`/entity-lookup/vehicles/${vehicleId}`); }

    // --- Analytics ---
    async getFraudTrends()          { return this.request('/analytics/fraud-trends'); }
    async getGeographicHotspots()   { return this.request('/analytics/geographic-hotspots'); }
    async getClaimAmountAnomalies() { return this.request('/analytics/claim-amount-anomalies'); }
    async getTemporalPatterns()     { return this.request('/analytics/temporal-patterns'); }
}

const api = new APIClient();
