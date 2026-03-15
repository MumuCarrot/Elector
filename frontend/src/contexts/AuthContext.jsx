import React, { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
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

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

