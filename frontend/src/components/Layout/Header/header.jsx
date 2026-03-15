import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';

function Header() {
    const navigate = useNavigate();
    const { isAuthenticated, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/');
        setIsMenuOpen(false);
    };

    const handleNavClick = (path) => {
        navigate(path);
        setIsMenuOpen(false);
    };

    return (
        <header className="w-full bg-white border-b border-gray-200 shadow-sm">
            <div className="max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-6 lg:px-8 py-3 gap-4">
                {/* Logo */}
                <div className="flex items-center flex-shrink-0">
                    <Link
                        to="/"
                        className="text-gray-800 font-bold text-2xl transition-colors hover:text-blue-600 no-underline"
                        onClick={() => setIsMenuOpen(false)}
                    >
                        <span>Elector</span>
                    </Link>
                </div>

                {/* Desktop navigation */}
                <nav className="hidden md:flex gap-6 items-center flex-1 justify-center">
                    <Link
                        to="/"
                        className="text-gray-800 font-medium py-2 px-4 rounded transition-all hover:bg-gray-100 hover:text-blue-600 no-underline"
                    >
                        Home
                    </Link>
                    <Link
                        to="/votes"
                        className="text-gray-800 font-medium py-2 px-4 rounded transition-all hover:bg-gray-100 hover:text-blue-600 no-underline"
                    >
                        Votes
                    </Link>
                    <Link
                        to="/votes/create"
                        className="text-gray-800 font-medium py-2 px-4 rounded transition-all hover:bg-gray-100 hover:text-blue-600 no-underline"
                    >
                        Create
                    </Link>
                </nav>

                {/* Desktop auth controls */}
                <div className="hidden md:flex items-center gap-3 flex-shrink-0 ml-auto">
                    {isAuthenticated ? (
                        <>
                            <Link
                                to="/profile"
                                className="text-gray-800 font-medium py-2 px-4 rounded transition-all hover:bg-gray-100 hover:text-blue-600 no-underline inline-block"
                            >
                                Profile
                            </Link>
                            <button
                                className="py-2 px-4 rounded cursor-pointer font-medium text-sm transition-all bg-transparent text-red-600 border border-red-600 hover:bg-red-600 hover:text-white"
                                onClick={handleLogout}
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                className="py-2 px-4 rounded cursor-pointer font-medium text-sm transition-all bg-transparent text-gray-800 border border-gray-200 hover:bg-gray-100 hover:border-blue-600 hover:text-blue-600"
                                onClick={() => navigate('/auth/login')}
                            >
                                Sign In
                            </button>
                            <button
                                className="py-2 px-4 rounded cursor-pointer font-medium text-sm transition-all bg-blue-600 text-white hover:bg-blue-700 border-none"
                                onClick={() => navigate('/auth/register')}
                            >
                                Sign Up
                            </button>
                        </>
                    )}
                </div>

                {/* Mobile menu button */}
                <button
                    className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                    onClick={() => setIsMenuOpen((prev) => !prev)}
                    aria-label="Toggle navigation menu"
                >
                    <span className="sr-only">Open main menu</span>
                    {isMenuOpen ? (
                        <svg
                            className="h-6 w-6"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    ) : (
                        <svg
                            className="h-6 w-6"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    )}
                </button>
            </div>

            {/* Mobile dropdown menu */}
            {isMenuOpen && (
                <div className="md:hidden border-t border-gray-200 bg-white">
                    <nav className="px-4 py-3 space-y-1">
                        <button
                            className="w-full text-left text-gray-800 font-medium py-2 px-2 rounded transition-all hover:bg-gray-100 hover:text-blue-600"
                            onClick={() => handleNavClick('/')}
                        >
                            Home
                        </button>
                        <button
                            className="w-full text-left text-gray-800 font-medium py-2 px-2 rounded transition-all hover:bg-gray-100 hover:text-blue-600"
                            onClick={() => handleNavClick('/votes')}
                        >
                            Votes
                        </button>
                        <button
                            className="w-full text-left text-gray-800 font-medium py-2 px-2 rounded transition-all hover:bg-gray-100 hover:text-blue-600"
                            onClick={() => handleNavClick('/votes/create')}
                        >
                            Create
                        </button>

                        <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
                            {isAuthenticated ? (
                                <>
                                    <button
                                        className="w-full text-left text-gray-800 font-medium py-2 px-2 rounded transition-all hover:bg-gray-100 hover:text-blue-600"
                                        onClick={() => handleNavClick('/profile')}
                                    >
                                        Profile
                                    </button>
                                    <button
                                        className="w-full text-left py-2 px-2 rounded cursor-pointer font-medium text-sm transition-all bg-transparent text-red-600 border border-red-600 hover:bg-red-600 hover:text-white"
                                        onClick={handleLogout}
                                    >
                                        Logout
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button
                                        className="w-full text-left py-2 px-2 rounded cursor-pointer font-medium text-sm transition-all bg-transparent text-gray-800 border border-gray-200 hover:bg-gray-100 hover:border-blue-600 hover:text-blue-600"
                                        onClick={() => handleNavClick('/auth/login')}
                                    >
                                        Sign In
                                    </button>
                                    <button
                                        className="w-full text-left py-2 px-2 rounded cursor-pointer font-medium text-sm transition-all bg-blue-600 text-white hover:bg-blue-700 border-none"
                                        onClick={() => handleNavClick('/auth/register')}
                                    >
                                        Sign Up
                                    </button>
                                </>
                            )}
                        </div>
                    </nav>
                </div>
            )}
        </header>
    );
}

export default Header;

