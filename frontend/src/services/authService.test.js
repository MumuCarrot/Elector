import authService from './authService';
import { axiosInstance } from './axiosConfig';

jest.mock('./axiosConfig', () => ({
    axiosInstance: jest.fn(),
}));

describe('authService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('login sends POST to /auth/login with email and password', async () => {
        axiosInstance.mockResolvedValueOnce({ data: { token: '123' } });

        const email = 'test@example.com';
        const password = 'password';

        const result = await authService.login(email, password);

        expect(axiosInstance).toHaveBeenCalledWith({
            url: '/auth/login',
            method: 'POST',
            data: { email, password },
        });
        expect(result).toEqual({ token: '123' });
    });

    test('register sends POST to /auth/register with user data', async () => {
        axiosInstance.mockResolvedValueOnce({ data: { user: { id: 1 } } });

        const userData = { email: 'test@example.com', password: '123456' };
        const result = await authService.register(userData);

        expect(axiosInstance).toHaveBeenCalledWith({
            url: '/auth/register',
            method: 'POST',
            data: userData,
        });
        expect(result).toEqual({ user: { id: 1 } });
    });

    test('getCurrentUser calls /auth/me', async () => {
        axiosInstance.mockResolvedValueOnce({ data: { id: 1 } });

        const result = await authService.getCurrentUser();

        expect(axiosInstance).toHaveBeenCalledWith({
            url: '/auth/me',
            method: 'GET',
            data: undefined,
        });
        expect(result).toEqual({ id: 1 });
    });
});


