import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext.jsx';

jest.mock('../services/authService', () => ({
    refreshToken: jest.fn().mockResolvedValue({}),
    getCurrentUser: jest.fn().mockRejectedValue(new Error('No user')),
    logout: jest.fn().mockResolvedValue({}),
}));

async function setupHook() {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const hookResult = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
        expect(hookResult.result.current.isLoading).toBe(false);
    });

    return hookResult;
}

describe('AuthContext', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
    });

    test('login saves user and sets isAuthenticated', async () => {
        const userData = { id: 1, email: 'test@example.com' };
        const { result } = await setupHook();

        act(() => {
            result.current.login(userData);
        });

        expect(result.current.user).toEqual(userData);
        expect(result.current.isAuthenticated).toBe(true);
        expect(JSON.parse(localStorage.getItem('user'))).toEqual(userData);
    });

    test('logout clears user and isAuthenticated', async () => {
        const userData = { id: 1, email: 'test@example.com' };
        const { result } = await setupHook();

        act(() => {
            result.current.login(userData);
        });

        await act(async () => {
            await result.current.logout();
        });

        expect(result.current.user).toBeNull();
        expect(result.current.isAuthenticated).toBe(false);
        expect(localStorage.getItem('user')).toBeNull();
    });

    test('updateUser merges and persists user data', async () => {
        const userData = { id: 1, email: 'test@example.com', name: 'Old' };
        const updated = { name: 'New' };

        const { result } = await setupHook();

        act(() => {
            result.current.login(userData);
        });

        act(() => {
            result.current.updateUser(updated);
        });

        expect(result.current.user).toEqual({ ...userData, ...updated });
        expect(JSON.parse(localStorage.getItem('user'))).toEqual({
            ...userData,
            ...updated,
        });
    });
});


