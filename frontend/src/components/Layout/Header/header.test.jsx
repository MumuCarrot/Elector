import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Header from './header.jsx';

const mockUseAuth = jest.fn();
const mockUseNavigate = jest.fn();

jest.mock('../../../contexts/AuthContext', () => ({
    useAuth: () => mockUseAuth(),
}));

jest.mock('react-router-dom', () => {
    const React = require('react');
    return {
        Link: ({ children, ...props }) => <a {...props}>{children}</a>,
        useNavigate: () => mockUseNavigate,
    };
});

describe('Header', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('shows Sign In and Sign Up buttons when user is not authenticated', () => {
        mockUseAuth.mockReturnValue({
            isAuthenticated: false,
            user: null,
            logout: jest.fn(),
        });

        render(<Header />);

        expect(screen.getByText(/Sign In/i)).toBeInTheDocument();
        expect(screen.getByText(/Sign Up/i)).toBeInTheDocument();
    });

    test('shows Profile and Logout when user is authenticated', () => {
        mockUseAuth.mockReturnValue({
            isAuthenticated: true,
            user: { id: 1, email: 'test@example.com' },
            logout: jest.fn(),
        });

        render(<Header />);

        expect(screen.getByText(/Profile/i)).toBeInTheDocument();
        expect(screen.getByText(/Logout/i)).toBeInTheDocument();
    });

    test('calls logout when Logout button is clicked', () => {
        const logoutMock = jest.fn();

        mockUseAuth.mockReturnValue({
            isAuthenticated: true,
            user: { id: 1 },
            logout: logoutMock,
        });

        render(<Header />);

        fireEvent.click(screen.getByText(/Logout/i));
        expect(logoutMock).toHaveBeenCalled();
    });
});

