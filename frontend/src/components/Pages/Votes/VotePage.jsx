import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import electionService from '../../../services/electionService';

function VotePage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user, isAuthenticated } = useAuth();
    const [election, setElection] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedCandidates, setSelectedCandidates] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [hasVoted, setHasVoted] = useState(false);
    const [results, setResults] = useState(null);
    const [showSettings, setShowSettings] = useState(false);
    const [settingsForm, setSettingsForm] = useState({
        title: '',
        description: '',
        start_date: '',
        end_date: '',
        candidates: [],
    });

    const fetchResults = useCallback(async () => {
        try {
            const resultsData = await electionService.getElectionResults(id);
            setResults(resultsData);
        } catch (err) {
            console.error('Failed to load results:', err);
        }
    }, [id]);

    const fetchElection = useCallback(async () => {
        try {
            setIsLoading(true);
            setError('');
            const response = await electionService.getElectionById(id);
            const electionData = response.election || response;
            setElection(electionData);
            
            setSettingsForm({
                title: electionData.title || '',
                description: electionData.description || '',
                start_date: electionData.start_date ? new Date(electionData.start_date).toISOString().slice(0, 16) : '',
                end_date: electionData.end_date ? new Date(electionData.end_date).toISOString().slice(0, 16) : '',
                candidates: electionData.candidates || [],
            });

            if (isAuthenticated) {
                try {
                    const myVote = await electionService.getMyVote(id);
                    if (myVote) {
                        setHasVoted(true);
                        fetchResults();
                    }
                } catch (err) {
                    console.log('User has not voted yet');
                }
            }

            if (isElectionEnded(electionData)) {
                fetchResults();
            }
        } catch (err) {
            setError(err.message || 'Failed to load election');
        } finally {
            setIsLoading(false);
        }
    }, [id, isAuthenticated, fetchResults]);

    useEffect(() => {
        fetchElection();
    }, [fetchElection]);

    const isElectionStarted = (electionData) => {
        if (!electionData.start_date) return true;
        return new Date() >= new Date(electionData.start_date);
    };

    const isElectionEnded = (electionData) => {
        if (!electionData.end_date) return false;
        return new Date() >= new Date(electionData.end_date);
    };

    const isOwner = () => {
        if (!user || !election) return false;
        return user.id === election.owner_id;
    };

    const canEditSettings = () => {
        return isOwner() && !isElectionStarted(election);
    };

    const handleCandidateToggle = (candidateId) => {
        if (hasVoted || !isElectionStarted(election)) return;

        const maxVotes = election.settings?.max_votes || 1;
        setSelectedCandidates(prev => {
            if (prev.includes(candidateId)) {
                return prev.filter(id => id !== candidateId);
            } else if (prev.length < maxVotes) {
                return [...prev, candidateId];
            } else if (maxVotes === 1) {
                return [candidateId];
            }
            return prev;
        });
    };

    const handleSubmitVote = async () => {
        if (selectedCandidates.length === 0) {
            setError('Please select at least one candidate');
            return;
        }

        if (!isAuthenticated) {
            navigate('/auth/login');
            return;
        }

        setIsSubmitting(true);
        setError('');

        try {
            await electionService.submitVote(id, selectedCandidates);
            setHasVoted(true);
            setSelectedCandidates([]);
            await fetchElection();
            await fetchResults();
        } catch (err) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to submit vote';
            setError(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSettingsChange = (field, value) => {
        setSettingsForm(prev => ({
            ...prev,
            [field]: value,
        }));
    };

    const handleCandidateChange = (index, field, value) => {
        setSettingsForm(prev => {
            const newCandidates = [...prev.candidates];
            newCandidates[index] = {
                ...newCandidates[index],
                [field]: value,
            };
            return {
                ...prev,
                candidates: newCandidates,
            };
        });
    };

    const addCandidate = () => {
        setSettingsForm(prev => ({
            ...prev,
            candidates: [...prev.candidates, { name: '', description: '' }],
        }));
    };

    const removeCandidate = (index) => {
        if (settingsForm.candidates.length > 2) {
            setSettingsForm(prev => ({
                ...prev,
                candidates: prev.candidates.filter((_, i) => i !== index),
            }));
        }
    };

    const handleDeleteElection = async () => {
        if (!isOwner() || !election) return;

        if (isElectionStarted(election)) {
            setError('You can delete the election only before it starts');
            return;
        }

        const confirmed = window.confirm('Are you sure you want to delete this election? This action cannot be undone.');
        if (!confirmed) return;

        setIsSubmitting(true);
        setError('');

        try {
            await electionService.deleteElection(id);
            navigate('/votes');
        } catch (err) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete election';
            setError(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleUpdateSettings = async () => {
        const trimmedTitle = (settingsForm.title || '').trim();

        if (!trimmedTitle) {
            setError('Title is required');
            return;
        }

        const candidatesWithNames = settingsForm.candidates.filter(
            (c) => (c.name || '').trim()
        );

        if (candidatesWithNames.length < 2) {
            setError('At least 2 candidates are required');
            return;
        }

        setIsSubmitting(true);
        setError('');

        try {
            const updateData = {
                title: trimmedTitle,
                description: settingsForm.description || null,
                start_date: settingsForm.start_date || null,
                end_date: settingsForm.end_date || null,
                candidates: candidatesWithNames.map((c) => ({
                    name: (c.name || '').trim(),
                    description: (c.description || '').trim() || null,
                })),
            };

            await electionService.updateElection(id, updateData);
            setShowSettings(false);
            await fetchElection();
        } catch (err) {
            setError(err.message || 'Failed to update election');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-gray-600">Loading election...</div>
            </div>
        );
    }

    if (error && !election) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="text-red-600 mb-4">Error: {error}</div>
                    <button
                        onClick={() => navigate('/votes')}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Back to Votes
                    </button>
                </div>
            </div>
        );
    }

    if (!election) {
        return null;
    }

    const started = isElectionStarted(election);
    const ended = isElectionEnded(election);
    const owner = isOwner();
    const canEdit = canEditSettings();

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                            <h1 className="text-3xl font-bold text-gray-900 mb-2">
                                {election.title || election.name}
                            </h1>
                            {election.description && (
                                <p className="text-gray-600 whitespace-pre-line">
                                    {election.description}
                                </p>
                            )}
                        </div>
                        {owner && (
                            <div className="ml-4 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                                Owner
                            </div>
                        )}
                    </div>

                    {/* Status Badge */}
                    <div className="flex items-center gap-4 mt-4">
                        {!started && (
                            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                                Not Started
                            </span>
                        )}
                        {started && !ended && (
                            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                                Active
                            </span>
                        )}
                        {ended && (
                            <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                                Ended
                            </span>
                        )}
                        {election.start_date && (
                            <span className="text-sm text-gray-600">
                                Start: {new Date(election.start_date).toLocaleString()}
                            </span>
                        )}
                        {election.end_date && (
                            <span className="text-sm text-gray-600">
                                End: {new Date(election.end_date).toLocaleString()}
                            </span>
                        )}
                    </div>

                    {/* Owner Actions */}
                    {owner && canEdit && (
                        <div className="mt-4 pt-4 border-t flex flex-wrap gap-3">
                            <button
                                onClick={() => setShowSettings(!showSettings)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                {showSettings ? 'Hide Settings' : 'Edit Election Settings'}
                            </button>
                            <button
                                type="button"
                                onClick={handleDeleteElection}
                                disabled={isSubmitting}
                                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {isSubmitting ? 'Deleting...' : 'Delete Election'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Settings Form */}
                {showSettings && canEdit && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">Edit Election Settings</h2>
                        
                        {error && (
                            <div className="rounded-md bg-red-50 p-4 mb-4">
                                <p className="text-sm font-medium text-red-800">{error}</p>
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Title *
                                </label>
                                <input
                                    type="text"
                                    value={settingsForm.title}
                                    onChange={(e) => handleSettingsChange('title', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Description
                                </label>
                                <textarea
                                    value={settingsForm.description}
                                    onChange={(e) => handleSettingsChange('description', e.target.value)}
                                    rows="4"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Start Date
                                    </label>
                                    <input
                                        type="datetime-local"
                                        value={settingsForm.start_date}
                                        onChange={(e) => handleSettingsChange('start_date', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        End Date
                                    </label>
                                    <input
                                        type="datetime-local"
                                        value={settingsForm.end_date}
                                        onChange={(e) => handleSettingsChange('end_date', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Candidates *
                                </label>
                                {settingsForm.candidates.map((candidate, index) => (
                                    <div key={index} className="mb-4 p-4 border border-gray-200 rounded-md">
                                        <div className="flex gap-2 mb-2">
                                            <input
                                                type="text"
                                                value={candidate.name}
                                                onChange={(e) => handleCandidateChange(index, 'name', e.target.value)}
                                                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                placeholder={`Candidate ${index + 1} name *`}
                                            />
                                            {settingsForm.candidates.length > 2 && (
                                                <button
                                                    type="button"
                                                    onClick={() => removeCandidate(index)}
                                                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                                                >
                                                    Remove
                                                </button>
                                            )}
                                        </div>
                                        <textarea
                                            value={candidate.description || ''}
                                            onChange={(e) => handleCandidateChange(index, 'description', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder={`Candidate ${index + 1} description (optional)`}
                                            rows="2"
                                        />
                                    </div>
                                ))}
                                <button
                                    type="button"
                                    onClick={addCandidate}
                                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                                >
                                    + Add Candidate
                                </button>
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button
                                    onClick={handleUpdateSettings}
                                    disabled={isSubmitting}
                                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {isSubmitting ? 'Saving...' : 'Save Changes'}
                                </button>
                                <button
                                    onClick={() => setShowSettings(false)}
                                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Voting Section */}
                {started && !hasVoted && isAuthenticated && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">Cast Your Vote</h2>
                        
                        {error && (
                            <div className="rounded-md bg-red-50 p-4 mb-4">
                                <p className="text-sm font-medium text-red-800">{error}</p>
                            </div>
                        )}

                        <p className="text-gray-600 mb-4">
                            Select up to {election.settings?.max_votes || 1} candidate(s):
                        </p>

                        <div className="space-y-3 mb-6">
                            {election.candidates?.map((candidate) => {
                                const candidateId = candidate.id || candidate._id;
                                const isSelected = selectedCandidates.includes(candidateId);
                                return (
                                    <div
                                        key={candidateId}
                                        onClick={() => handleCandidateToggle(candidateId)}
                                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                                            isSelected
                                                ? 'border-blue-600 bg-blue-50'
                                                : 'border-gray-200 hover:border-gray-300'
                                        }`}
                                    >
                                        <div className="flex items-start">
                                            <div className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center mr-3 mt-1 ${
                                                isSelected
                                                    ? 'border-blue-600 bg-blue-600'
                                                    : 'border-gray-300'
                                            }`}>
                                                {isSelected && (
                                                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                    </svg>
                                                )}
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="font-semibold text-gray-900 mb-1">
                                                    {candidate.name}
                                                </h3>
                                                {candidate.description && (
                                                    <p className="text-sm text-gray-600">
                                                        {candidate.description}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        <button
                            onClick={handleSubmitVote}
                            disabled={isSubmitting || selectedCandidates.length === 0}
                            className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? 'Submitting...' : 'Submit Vote'}
                        </button>
                    </div>
                )}

                {/* Not Authenticated Message */}
                {started && !isAuthenticated && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6 text-center">
                        <p className="text-gray-600 mb-4">Please sign in to vote</p>
                        <button
                            onClick={() => navigate('/auth/login')}
                            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700"
                        >
                            Sign In
                        </button>
                    </div>
                )}

                {/* Already Voted Message */}
                {hasVoted && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                        <p className="text-green-800 font-medium">You have already voted in this election.</p>
                    </div>
                )}

                {/* Results Section */}
                {(ended || hasVoted || results) && (
                    <div className="bg-white rounded-lg shadow-md p-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">Results</h2>
                        {results ? (
                            <div className="space-y-4">
                                {election.candidates?.map((candidate) => {
                                    const candidateId = candidate.id || candidate._id;
                                    const voteCount = results[candidateId] || results[candidate.id] || results[candidate._id] || 0;
                                    const totalVotes = Object.values(results).reduce((sum, count) => sum + (count || 0), 0);
                                    const percentage = totalVotes > 0 ? ((voteCount / totalVotes) * 100).toFixed(1) : 0;
                                    
                                    return (
                                        <div key={candidateId} className="border border-gray-200 rounded-lg p-4">
                                            <div className="flex justify-between items-center mb-2">
                                                <h3 className="font-semibold text-gray-900">{candidate.name}</h3>
                                                <span className="text-gray-600">{voteCount} votes ({percentage}%)</span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-4">
                                                <div
                                                    className="bg-blue-600 h-4 rounded-full transition-all"
                                                    style={{ width: `${percentage}%` }}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <p className="text-gray-600">Results will be available after the election ends.</p>
                        )}
                    </div>
                )}

                {/* Back Button */}
                <div className="mt-6">
                    <button
                        onClick={() => navigate('/votes')}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                    >
                        ← Back to Votes
                    </button>
                </div>
            </div>
        </div>
    );
}

export default VotePage;

