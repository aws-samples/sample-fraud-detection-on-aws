// Authentication module - sessionStorage token storage with httpOnly cookie backup
class Auth {
    constructor() {
        this.tokenKey = 'fraud_detection_token';
        this.refreshTokenKey = 'fraud_detection_refresh_token';
        this.userKey = 'fraud_detection_user';
        this._refreshTimer = null;
    }

    async login(username, password) {
        try {
            const response = await fetch(`${CONFIG.API_ENDPOINT}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok && data.token) {
                sessionStorage.setItem(this.tokenKey, data.token);
                sessionStorage.setItem(this.userKey, username);
                if (data.refreshToken) {
                    sessionStorage.setItem(this.refreshTokenKey, data.refreshToken);
                }
                this._scheduleRefresh();
                return { success: true };
            } else {
                return { success: false, error: data.error || 'Authentication failed' };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    _scheduleRefresh() {
        if (this._refreshTimer) clearTimeout(this._refreshTimer);
        const token = this.getToken();
        if (!token) return;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const expiresMs = payload.exp * 1000;
            // Refresh 2 minutes before expiry
            const refreshIn = expiresMs - Date.now() - 120000;
            if (refreshIn > 0) {
                this._refreshTimer = setTimeout(() => this._doRefresh(), refreshIn);
            }
        } catch (e) { /* ignore */ }
    }

    async _doRefresh() {
        const refreshToken = sessionStorage.getItem(this.refreshTokenKey);
        if (!refreshToken) return false;
        try {
            const response = await fetch(`${CONFIG.API_ENDPOINT}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ refreshToken })
            });
            const data = await response.json();
            if (response.ok && data.token) {
                sessionStorage.setItem(this.tokenKey, data.token);
                this._scheduleRefresh();
                return true;
            }
            return false;
        } catch (e) {
            return false;
        }
    }

    async tryRefresh() {
        return this._doRefresh();
    }

    getToken() {
        return sessionStorage.getItem(this.tokenKey);
    }

    getUser() {
        return sessionStorage.getItem(this.userKey);
    }

    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.exp && payload.exp * 1000 < Date.now()) {
                this.logout();
                return false;
            }
            return true;
        } catch (e) {
            return false;
        }
    }

    async logout() {
        if (this._refreshTimer) clearTimeout(this._refreshTimer);
        try {
            await fetch(`${CONFIG.API_ENDPOINT}/auth/logout`, {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
        sessionStorage.removeItem(this.tokenKey);
        sessionStorage.removeItem(this.refreshTokenKey);
        sessionStorage.removeItem(this.userKey);
        window.location.href = 'login.html';
    }
}

const auth = new Auth();
// Resume refresh timer if already logged in
auth._scheduleRefresh();
