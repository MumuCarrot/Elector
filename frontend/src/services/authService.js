import { axiosInstance } from './axiosConfig';

class AuthService {
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

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            data: { email, password },
        });
    }

    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            data: userData,
        });
    }

    async logout() {
        return this.request('/auth/logout', {
            method: 'POST',
        });
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async refreshToken() {
        return this.request('/auth/refresh', {
            method: 'POST',
        });
    }
}

const authService = new AuthService();
export default authService;

