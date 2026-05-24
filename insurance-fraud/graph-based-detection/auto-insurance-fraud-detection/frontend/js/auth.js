// Authentication module — cookie-only mode.
//
// Security model:
//   • The actual JWT lives in an httpOnly, Secure, SameSite=None cookie
//     named `__Host-fraud_detection_token` set by the backend /auth/login handler.
//     The `__Host-` prefix is browser-enforced: the cookie is only accepted
//     when Secure + Path=/ + no Domain attribute are all set, which guards
//     against accidental relaxation of those security attributes.
//   • JavaScript cannot read that cookie (that's the whole point — XSS
//     protection against token theft).
//   • The browser auto-forwards the cookie on every `fetch()` that uses
//     `credentials: 'include'`.
//   • We keep only non-sensitive metadata in sessionStorage — specifically
//     the username and the token expiry timestamp — so the UI can show the
//     logged-in user and proactively refresh before the cookie goes stale.
//   • The refresh token is still returned in the JSON body on login and is
//     kept in sessionStorage; it's a lower-value credential (usable only
//     via the /auth/refresh endpoint) and we need JS access to it to drive
//     the refresh timer. A future hardening pass could move this to a
//     second httpOnly cookie with Path=/auth/refresh.
class Auth {
    constructor() {
        this.userKey = 'fraud_detection_user';
        this.expiryKey = 'fraud_detection_token_expiry';
        this.refreshTokenKey = 'fraud_detection_refresh_token';
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
                // Do NOT persist data.token anywhere JS-accessible — the
                // httpOnly cookie does the work. Persist only the expiry
                // (epoch seconds) so we can proactively refresh, and the
                // refresh token so we can actually do it.
                sessionStorage.setItem(this.userKey, username);
                const expiresAt = Math.floor(Date.now() / 1000) + (data.expiresIn || 3600);
                sessionStorage.setItem(this.expiryKey, String(expiresAt));
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
        const expiresAt = parseInt(sessionStorage.getItem(this.expiryKey) || '0', 10);
        if (!expiresAt) return;
        const refreshIn = (expiresAt * 1000) - Date.now() - 120000;  // 2 min before
        if (refreshIn > 0) {
            this._refreshTimer = setTimeout(() => this._doRefresh(), refreshIn);
        }
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
                // The new token is sent by the backend as a fresh Set-Cookie
                // header. We only track the new expiry.
                const expiresAt = Math.floor(Date.now() / 1000) + (data.expiresIn || 3600);
                sessionStorage.setItem(this.expiryKey, String(expiresAt));
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

    getUser() {
        return sessionStorage.getItem(this.userKey);
    }

    isAuthenticated() {
        // With cookie-based auth we can't directly inspect the cookie from
        // JS. We rely on the expiry timestamp we recorded at login/refresh
        // time. If the timer says we're still inside the window, assume yes;
        // if not, the next API call will return 401 and the flow will
        // trigger a refresh.
        const expiresAt = parseInt(sessionStorage.getItem(this.expiryKey) || '0', 10);
        if (!expiresAt) return false;
        if (Date.now() >= expiresAt * 1000) {
            return false;
        }
        return true;
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
        sessionStorage.removeItem(this.userKey);
        sessionStorage.removeItem(this.expiryKey);
        sessionStorage.removeItem(this.refreshTokenKey);
        window.location.href = 'login.html';
    }
}

const auth = new Auth();
// Resume refresh timer if already logged in
auth._scheduleRefresh();
