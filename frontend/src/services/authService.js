import { axiosInstance } from './axiosConfig';

/**
 * HTTP client for authentication-related API endpoints.
 */
class AuthService {
    /**
     * Performs an authenticated API request via the shared axios instance.
     *
     * @param {string} endpoint - Relative path (e.g. `/auth/login`).
     * @param {import('axios').AxiosRequestConfig} [options={}] - Axios options; `method` defaults to GET.
     * @returns {Promise<unknown>} Parsed response body (`response.data`).
     */
    async request(endpoint, options = {}) {
        try {
            const response = await axiosInstance({
                url: endpoint,
                method: options.method || 'GET',
                data: options.data,
                ...options,
            });
            return response.data;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Signs in with email and password.
     *
     * @param {string} email - User email.
     * @param {string} password - User password.
     * @returns {Promise<unknown>} Login response (typically includes `user`).
     */
    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            data: { email, password },
        });
    }

    /**
     * Registers a new user.
     *
     * @param {Record<string, unknown>} userData - Registration payload (e.g. email, password, names).
     * @returns {Promise<unknown>} Registration response (typically includes `user`).
     */
    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            data: userData,
        });
    }

    /**
     * Ends the server session (logout).
     *
     * @returns {Promise<unknown>} API response body.
     */
    async logout() {
        return this.request('/auth/logout', {
            method: 'POST',
        });
    }

    /**
     * Fetches the currently authenticated user.
     *
     * @returns {Promise<unknown>} Current user payload.
     */
    async getCurrentUser() {
        return this.request('/auth/me');
    }

    /**
     * Refreshes the session token using HTTP-only cookies.
     *
     * @returns {Promise<unknown>} Refresh response body.
     */
    async refreshToken() {
        return this.request('/auth/refresh', {
            method: 'POST',
        });
    }
}

/** Singleton {@link AuthService} for the app. */
const authService = new AuthService();
export default authService;
