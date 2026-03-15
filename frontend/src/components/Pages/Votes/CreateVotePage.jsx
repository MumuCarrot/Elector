import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import electionService from '../../../services/electionService';

function CreateVotePage() {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        candidates: [{ name: '', description: '' }, { name: '', description: '' }],
        settings: {
            start_date: '',
            end_date: '',
            is_public: true,
            allow_revoting: false,
            max_votes: 1,
            require_auth: true,
        },
    });
    const [pdfFile, setPdfFile] = useState(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    React.useEffect(() => {
        if (!isAuthenticated) {
            navigate('/auth/login');
        }
    }, [isAuthenticated, navigate]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        
        if (name.startsWith('settings.')) {
            const settingKey = name.split('.')[1];
            setFormData(prev => ({
                ...prev,
                settings: {
                    ...prev.settings,
                    [settingKey]: type === 'checkbox' ? checked : value,
                },
            }));
        } else {
            setFormData(prev => ({
                ...prev,
                [name]: value,
            }));
        }
        setError('');
    };

    const handleCandidateChange = (index, field, value) => {
        setFormData(prev => {
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
        setFormData(prev => ({
            ...prev,
            candidates: [...prev.candidates, { name: '', description: '' }],
        }));
    };

    const removeCandidate = (index) => {
        if (formData.candidates.length > 2) {
            setFormData(prev => ({
                ...prev,
                candidates: prev.candidates.filter((_, i) => i !== index),
            }));
        }
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.type !== 'application/pdf') {
                setError('Please upload a PDF file');
                return;
            }
            if (file.size > 10 * 1024 * 1024) {
                setError('File size should be less than 10MB');
                return;
            }
            setPdfFile(file);
            setError('');
        }
    };

    const validateForm = () => {
        if (!formData.title.trim()) {
            setError('Title is required');
            return false;
        }
        if (formData.candidates.length < 2) {
            setError('At least 2 candidates are required');
            return false;
        }
        const validCandidates = formData.candidates.filter(cand => cand.name.trim());
        if (validCandidates.length < 2) {
            setError('At least 2 candidates must have names');
            return false;
        }
        if (formData.settings.start_date && formData.settings.end_date) {
            if (new Date(formData.settings.start_date) >= new Date(formData.settings.end_date)) {
                setError('End date must be after start date');
                return false;
            }
        }
        if (formData.settings.max_votes < 1) {
            setError('Max votes must be at least 1');
            return false;
        }
        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!validateForm()) {
            return;
        }

        setIsLoading(true);

        try {
            const electionData = {
                title: formData.title,
                description: formData.description || null,
                start_date: formData.settings.start_date || null,
                end_date: formData.settings.end_date || null,
                is_public: formData.settings.is_public,
                candidates: formData.candidates
                    .filter(cand => cand.name.trim())
                    .map(cand => ({
                        name: cand.name.trim(),
                        description: cand.description.trim() || null,
                    })),
                settings: {
                    allow_revoting: formData.settings.allow_revoting,
                    max_votes: parseInt(formData.settings.max_votes) || 1,
                    require_auth: formData.settings.require_auth,
                },
            };

            const response = await electionService.createElection(electionData, pdfFile);
            navigate(`/votes/${response.election?.id || response.id}`);
        } catch (err) {
            setError(err.message || 'Failed to create election. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 mb-8">Create New Election</h1>

                <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
                    {error && (
                        <div className="rounded-md bg-red-50 p-4">
                            <p className="text-sm font-medium text-red-800">{error}</p>
                        </div>
                    )}

                    {/* Title */}
                    <div>
                        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                            Vote Title *
                        </label>
                        <input
                            type="text"
                            id="title"
                            name="title"
                            required
                            value={formData.title}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter vote title"
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                            Description
                        </label>
                        <textarea
                            id="description"
                            name="description"
                            rows="4"
                            value={formData.description}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter vote description"
                        />
                    </div>

                    {/* Candidates */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Candidates *
                        </label>
                        {formData.candidates.map((candidate, index) => (
                            <div key={index} className="mb-4 p-4 border border-gray-200 rounded-md">
                                <div className="flex gap-2 mb-2">
                                    <input
                                        type="text"
                                        value={candidate.name}
                                        onChange={(e) => handleCandidateChange(index, 'name', e.target.value)}
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder={`Candidate ${index + 1} name *`}
                                        required
                                    />
                                    {formData.candidates.length > 2 && (
                                        <button
                                            type="button"
                                            onClick={() => removeCandidate(index)}
                                            className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                                        >
                                            Remove
                                        </button>
                                    )}
                                </div>
                                <textarea
                                    value={candidate.description}
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
                            className="mt-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                        >
                            + Add Candidate
                        </button>
                    </div>

                    {/* PDF File Upload */}
                    <div>
                        <label htmlFor="pdfFile" className="block text-sm font-medium text-gray-700 mb-2">
                            Attach PDF Document (Optional)
                        </label>
                        <input
                            type="file"
                            id="pdfFile"
                            accept="application/pdf"
                            onChange={handleFileChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        {pdfFile && (
                            <p className="mt-2 text-sm text-gray-600">
                                Selected: {pdfFile.name} ({(pdfFile.size / 1024 / 1024).toFixed(2)} MB)
                            </p>
                        )}
                    </div>

                    {/* Settings */}
                    <div className="border-t pt-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Settings</h2>

                        <div className="space-y-4">
                            {/* Start Date */}
                            <div>
                                <label htmlFor="settings.start_date" className="block text-sm font-medium text-gray-700 mb-2">
                                    Start Date (Optional)
                                </label>
                                <input
                                    type="datetime-local"
                                    id="settings.start_date"
                                    name="settings.start_date"
                                    value={formData.settings.start_date}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {/* End Date */}
                            <div>
                                <label htmlFor="settings.end_date" className="block text-sm font-medium text-gray-700 mb-2">
                                    End Date (Optional)
                                </label>
                                <input
                                    type="datetime-local"
                                    id="settings.end_date"
                                    name="settings.end_date"
                                    value={formData.settings.end_date}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {/* Max Votes */}
                            <div>
                                <label htmlFor="settings.max_votes" className="block text-sm font-medium text-gray-700 mb-2">
                                    Max Votes
                                </label>
                                <input
                                    type="number"
                                    id="settings.max_votes"
                                    name="settings.max_votes"
                                    min="1"
                                    value={formData.settings.max_votes}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {/* Checkboxes */}
                            <div className="space-y-3">
                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        name="settings.is_public"
                                        checked={formData.settings.is_public}
                                        onChange={handleChange}
                                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                    />
                                    <span className="ml-2 text-sm text-gray-700">Public election (visible to everyone)</span>
                                </label>

                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        name="settings.allow_revoting"
                                        checked={formData.settings.allow_revoting}
                                        onChange={handleChange}
                                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                    />
                                    <span className="ml-2 text-sm text-gray-700">Allow revoting</span>
                                </label>

                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        name="settings.require_auth"
                                        checked={formData.settings.require_auth}
                                        onChange={handleChange}
                                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                    />
                                    <span className="ml-2 text-sm text-gray-700">Require authentication to vote</span>
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Submit Buttons */}
                    <div className="flex gap-4 pt-4">
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? 'Creating...' : 'Create Election'}
                        </button>
                        <button
                            type="button"
                            onClick={() => navigate('/votes')}
                            className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                        >
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default CreateVotePage;

