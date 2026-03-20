import React, { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

/**
 * @typedef {object} AuthContextValue
 * @property {object|null} user - Current user or null.
 * @property {boolean} isAuthenticated - Whether a user session is active.
 * @property {boolean} isLoading - Initial auth check in progress.
 * @property {(userData: object) => void} login - Stores user and sets authenticated.
 * @property {() => Promise<void>} logout - Clears server and local session.
 * @property {(userData: object) => void} updateUser - Merges fields into `user`.
 */

/** @type {React.Context<AuthContextValue|null>} */
const AuthContext = createContext(null);

/**
 * Provides authentication state and actions to the component tree.
 * On mount, attempts session refresh and loads the current user.
 *
 * @param {{ children: React.ReactNode }} props - React children to wrap.
 * @returns {JSX.Element} Provider element.
 */
export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        /**
         * Restores session via refresh cookie and loads `/auth/me`.
         *
         * @returns {Promise<void>}
         */
        const checkAuth = async () => {
            try {
                try {
                    await authService.refreshToken();
                } catch (error) {
                    localStorage.removeItem('user');
                    setUser(null);
                    setIsAuthenticated(false);
                    setIsLoading(false);
                    return;
                }

                try {
                    const response = await authService.getCurrentUser();
                    const userData = response.user || response;
                    setUser(userData);
                    setIsAuthenticated(true);
                    localStorage.setItem('user', JSON.stringify(userData));
                } catch (error) {
                    localStorage.removeItem('user');
                    setUser(null);
                    setIsAuthenticated(false);
                }
            } catch (error) {
                console.error('Error checking authentication:', error);
                localStorage.removeItem('user');
                setUser(null);
                setIsAuthenticated(false);
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, []);

    /**
     * Persists user in localStorage and marks the session as authenticated.
     *
     * @param {Record<string, unknown>} userData - User object from login/register.
     * @returns {void}
     */
    const login = (userData) => {
        try {
            localStorage.setItem('user', JSON.stringify(userData));
            setUser(userData);
            setIsAuthenticated(true);
        } catch (error) {
            console.error('Error saving authentication:', error);
            throw error;
        }
    };

    /**
     * Calls logout API, clears local user state and storage.
     *
     * @returns {Promise<void>}
     */
    const logout = async () => {
        try {
            try {
                await authService.logout();
            } catch (error) {
                console.error('Error calling logout API:', error);
            }

            localStorage.removeItem('user');
            setUser(null);
            setIsAuthenticated(false);
        } catch (error) {
            console.error('Error during logout:', error);
            localStorage.removeItem('user');
            setUser(null);
            setIsAuthenticated(false);
        }
    };

    /**
     * Shallow-merges updates into the current user and persists to localStorage.
     *
     * @param {Record<string, unknown>} userData - Partial user fields to merge.
     * @returns {void}
     */
    const updateUser = (userData) => {
        try {
            const updatedUser = { ...user, ...userData };
            localStorage.setItem('user', JSON.stringify(updatedUser));
            setUser(updatedUser);
        } catch (error) {
            console.error('Error updating user:', error);
            throw error;
        }
    };

    const value = {
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        updateUser,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

/**
 * Hook to read auth state and actions. Must be used under {@link AuthProvider}.
 *
 * @returns {AuthContextValue} Context value.
 * @throws {Error} If used outside `AuthProvider`.
 */
export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
