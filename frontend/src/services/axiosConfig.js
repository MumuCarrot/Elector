import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1/';

export const axiosInstance = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

let isRefreshing = false;
let failedQueue = [];

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
            const errorMessage = error.response.data?.message || 
                               error.response.data?.error || 
                               `HTTP error! status: ${error.response.status}`;
            return Promise.reject(new Error(errorMessage));
        }

        if (error.request) {
            return Promise.reject(new Error('Network error. Please check your connection and try again.'));
        }

        return Promise.reject(error);
    }
);

