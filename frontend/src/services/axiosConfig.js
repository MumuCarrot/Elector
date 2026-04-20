/**
 * Axios instance and response interceptor: on 401, queues requests and retries after `/auth/refresh`
 * (skips refresh loop for login/register/refresh). Maps errors to `Error` with readable messages.
 */
import axios from 'axios';

const base = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
/** Normalized API base URL including `/api/v1/` when needed. */
const API_BASE_URL = base.endsWith('/api/v1') ? `${base}/` : `${base}/api/v1/`;

/**
 * Shared Axios instance: JSON API, credentials (cookies), and API base URL.
 *
 * @type {import('axios').AxiosInstance}
 */
export const axiosInstance = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

let isRefreshing = false;
/** @type {Array<{ resolve: (value?: unknown) => void; reject: (reason?: unknown) => void }>} */
let failedQueue = [];

/**
 * Resolves or rejects all queued requests after a token refresh attempt.
 *
 * @param {Error|null} error - Error from refresh; if set, queued requests are rejected.
 * @param {string|null} [_token] - Reserved for future token replay (currently unused).
 * @returns {void}
 */
const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });

    failedQueue = [];
};

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then(() => {
                        return axiosInstance(originalRequest);
                    })
                    .catch((err) => {
                        return Promise.reject(err);
                    });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            if (
                originalRequest.url?.includes('/auth/login') ||
                originalRequest.url?.includes('/auth/register') ||
                originalRequest.url?.includes('/auth/refresh')
            ) {
                isRefreshing = false;
                const errorMessage = error.response?.data?.message ||
                                   error.response?.data?.error ||
                                   error.message ||
                                   'Authentication failed';
                return Promise.reject(new Error(errorMessage));
            }

            try {
                await axiosInstance.post('/auth/refresh');
                processQueue(null, null);
                return axiosInstance(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError, null);
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        if (error.response) {
            const data = error.response.data;
            const detail = data?.detail;
            const fromDetail =
                typeof detail === 'string'
                    ? detail
                    : Array.isArray(detail) && detail[0]?.msg
                      ? detail.map((e) => e.msg || JSON.stringify(e)).join('; ')
                      : null;
            const errorMessage =
                fromDetail ||
                data?.message ||
                data?.error ||
                `HTTP error! status: ${error.response.status}`;
            const wrapped = new Error(errorMessage);
            wrapped.response = error.response;
            return Promise.reject(wrapped);
        }

        if (error.request) {
            return Promise.reject(new Error('Network error. Please check your connection and try again.'));
        }

        return Promise.reject(error);
    }
);
