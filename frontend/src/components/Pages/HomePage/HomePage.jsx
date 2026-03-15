import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';

function HomePage() {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    return (
        <div className="min-h-screen">
            {/* Hero Section */}
            <section className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white py-20 px-4">
                <div className="max-w-6xl mx-auto text-center">
                    <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
                        Your Voice Matters
                    </h1>
                    <p className="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
                        Make your opinion count. Participate in democratic decisions and shape the future through secure, transparent voting.
                    </p>
                    {!isAuthenticated ? (
                        <div className="flex gap-4 justify-center flex-wrap">
                            <button
                                onClick={() => navigate('/auth/register')}
                                className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                            >
                                Get Started
                            </button>
                            <button
                                onClick={() => navigate('/auth/login')}
                                className="bg-transparent border-2 border-white text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-white hover:text-blue-600 transition-all"
                            >
                                Sign In
                            </button>
                        </div>
                    ) : (
                        <div className="flex gap-4 justify-center">
                            <button
                                onClick={() => navigate('/votes')}
                                className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                            >
                                View Active Votes
                            </button>
                        </div>
                    )}
                </div>
            </section>

            {/* Why Voting Matters Section */}
            <section className="py-16 px-4 bg-gray-50">
                <div className="max-w-6xl mx-auto">
                    <h2 className="text-4xl font-bold text-center mb-12 text-gray-800">
                        Why Your Vote Matters
                    </h2>
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow">
                            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-6">
                                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h3 className="text-2xl font-semibold mb-4 text-gray-800">Democracy in Action</h3>
                            <p className="text-gray-600 leading-relaxed">
                                Every vote contributes to collective decision-making. Your participation ensures that diverse perspectives shape the outcomes.
                            </p>
                        </div>

                        <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
                                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                            </div>
                            <h3 className="text-2xl font-semibold mb-4 text-gray-800">Secure & Transparent</h3>
                            <p className="text-gray-600 leading-relaxed">
                                Our platform uses advanced encryption and blockchain technology to ensure your vote is secure and verifiable.
                            </p>
                        </div>

                        <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow">
                            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-6">
                                <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <h3 className="text-2xl font-semibold mb-4 text-gray-800">Quick & Easy</h3>
                            <p className="text-gray-600 leading-relaxed">
                                Vote from anywhere, anytime. Our intuitive interface makes participating in important decisions simple and accessible.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-16 px-4 bg-white">
                <div className="max-w-6xl mx-auto">
                    <h2 className="text-4xl font-bold text-center mb-12 text-gray-800">
                        How It Works
                    </h2>
                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div className="space-y-6">
                            <div className="flex gap-4">
                                <div className="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-xl">
                                    1
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-2 text-gray-800">Create an Account</h3>
                                    <p className="text-gray-600">Sign up in seconds with a simple registration process. Your identity is protected and verified.</p>
                                </div>
                            </div>
                            <div className="flex gap-4">
                                <div className="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-xl">
                                    2
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-2 text-gray-800">Browse Active Votes</h3>
                                    <p className="text-gray-600">Explore ongoing polls and elections. See what matters to your community.</p>
                                </div>
                            </div>
                            <div className="flex gap-4">
                                <div className="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-xl">
                                    3
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-2 text-gray-800">Cast Your Vote</h3>
                                    <p className="text-gray-600">Make your choice with confidence. Your vote is encrypted and recorded securely.</p>
                                </div>
                            </div>
                            <div className="flex gap-4">
                                <div className="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-xl">
                                    4
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-2 text-gray-800">See Results</h3>
                                    <p className="text-gray-600">Track real-time results and see how your vote contributed to the final outcome.</p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-12 rounded-2xl">
                            <div className="text-center">
                                <div className="text-6xl font-bold text-blue-600 mb-4">100%</div>
                                <p className="text-xl text-gray-700 font-semibold mb-2">Secure</p>
                                <p className="text-gray-600">Your vote is protected by industry-leading security measures</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Call to Action Section */}
            <section className="py-16 px-4 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-4xl font-bold mb-6">
                        Ready to Make Your Voice Heard?
                    </h2>
                    <p className="text-xl mb-8 text-blue-100">
                        Join thousands of users who are already participating in democratic decisions. Every vote counts.
                    </p>
                    {!isAuthenticated ? (
                        <div className="flex gap-4 justify-center flex-wrap">
                            <button
                                onClick={() => navigate('/auth/register')}
                                className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                            >
                                Start Voting Now
                            </button>
                        </div>
                    ) : (
                        <div className="flex gap-4 justify-center">
                            <button
                                onClick={() => navigate('/votes')}
                                className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                            >
                                Explore Votes
                            </button>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}

export default HomePage;

