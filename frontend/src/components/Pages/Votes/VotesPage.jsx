import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import electionService from '../../../services/electionService';

function VotesPage() {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [votes, setVotes] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchVotes();
    }, []);

    const fetchVotes = async () => {
        try {
            setIsLoading(true);
            setError('');
            const response = await electionService.getElections();
            setVotes(response.elections || response || []);
        } catch (err) {
            setError(err.message || 'Failed to load votes');
            setVotes([]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleParticipate = (voteId) => {
        if (!isAuthenticated) {
            navigate('/auth/login');
            return;
        }
        navigate(`/votes/${voteId}`);
    };

    const truncateDescription = (text, maxLines = 3) => {
        if (!text) return '';
        const lines = text.split('\n');
        if (lines.length <= maxLines) return text;
        return lines.slice(0, maxLines).join('\n') + '...';
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-gray-600">Loading votes...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-red-600">Error: {error}</div>
            </div>
        );
    }

    if (votes.length === 0) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
                <div className="max-w-md w-full text-center">
                    <div className="mb-6">
                        <svg
                            className="mx-auto h-16 w-16 text-gray-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                        No votes available
                    </h2>
                    <p className="text-gray-600 mb-6">
                        There are no active votes at the moment. Be the first to create one!
                    </p>
                    {isAuthenticated ? (
                        <button
                            onClick={() => navigate('/votes/create')}
                            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                        >
                            Create Your Vote
                        </button>
                    ) : (
                        <div className="space-y-3">
                            <p className="text-sm text-gray-500 mb-4">
                                Sign in to create a vote
                            </p>
                            <button
                                onClick={() => navigate('/auth/login')}
                                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                            >
                                Sign In
                            </button>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 mb-8">Active Votes</h1>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {votes.map((vote) => (
                        <div
                            key={vote.id || vote._id}
                            className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow overflow-hidden"
                        >
                            <div className="h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
                            
                            <div className="p-6">
                                <h2 className="text-xl font-semibold text-gray-900 mb-3 line-clamp-2">
                                    {vote.title || vote.name}
                                </h2>
                                
                                <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                                    {truncateDescription(vote.description || vote.desc || 'No description available')}
                                </p>
                                
                                <button
                                    onClick={() => handleParticipate(vote.id || vote._id)}
                                    className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                                >
                                    Participate
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default VotesPage;

