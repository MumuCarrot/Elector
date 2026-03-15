import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import authService from '../../../services/authService';
import userProfileService from '../../../services/userProfileService';
import electionService from '../../../services/electionService';

function UserProfilePage() {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [userData, setUserData] = useState(null);
    const [profile, setProfile] = useState(null);
    const [votes, setVotes] = useState([]);
    const [votesWithDetails, setVotesWithDetails] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [profileForm, setProfileForm] = useState({
        birth_date: '',
        avatar_url: '',
        address: '',
    });

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/auth/login');
            return;
        }
        fetchUserData();
    }, [isAuthenticated, navigate]);

    const fetchUserData = async () => {
        try {
            setIsLoading(true);
            setError('');

            const userResponse = await authService.getCurrentUser();
            const userInfo = userResponse.user || userResponse;
            setUserData(userInfo);

            const profileData = await userProfileService.getMyProfile();
            setProfile(profileData);
            
            if (profileData) {
                setProfileForm({
                    birth_date: profileData.birth_date || '',
                    avatar_url: profileData.avatar_url || '',
                    address: profileData.address || '',
                });
            }

            if (userInfo.id || userInfo._id) {
                try {
                    const votesData = await userProfileService.getUserVotes(userInfo.id || userInfo._id);
                    const votesArray = Array.isArray(votesData) ? votesData : [];
                    setVotes(votesArray);
                    
                    const votesDetails = await Promise.all(
                        votesArray.map(async (vote) => {
                            try {
                                const election = await electionService.getElectionById(vote.election_id);
                                const electionData = election.election || election;
                                const candidate = electionData.candidates?.find(
                                    c => (c.id || c._id) === vote.candidate_id
                                );
                                return {
                                    ...vote,
                                    election: electionData,
                                    candidate: candidate,
                                };
                            } catch (err) {
                                console.error('Failed to load election details:', err);
                                return vote;
                            }
                        })
                    );
                    setVotesWithDetails(votesDetails);
                } catch (err) {
                    console.error('Failed to load votes:', err);
                    setVotes([]);
                    setVotesWithDetails([]);
                }
            }
        } catch (err) {
            setError(err.message || 'Failed to load user data');
        } finally {
            setIsLoading(false);
        }
    };

    const handleProfileChange = (field, value) => {
        setProfileForm(prev => ({
            ...prev,
            [field]: value,
        }));
    };

    const handleSaveProfile = async () => {
        setIsSaving(true);
        setError('');

        try {
            let updatedProfile;
            if (profile) {
                updatedProfile = await userProfileService.updateProfile(profileForm);
            } else {
                updatedProfile = await userProfileService.createProfile({
                    user_id: userData.id || userData._id,
                    ...profileForm,
                });
            }
            
            setProfile(updatedProfile);
            setIsEditing(false);
        } catch (err) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to save profile';
            setError(errorMessage);
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancelEdit = () => {
        if (profile) {
            setProfileForm({
                birth_date: profile.birth_date || '',
                avatar_url: profile.avatar_url || '',
                address: profile.address || '',
            });
        } else {
            setProfileForm({
                birth_date: '',
                avatar_url: '',
                address: '',
            });
        }
        setIsEditing(false);
        setError('');
    };

    const handleVoteClick = (electionId) => {
        navigate(`/votes/${electionId}`);
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-gray-600">Loading profile...</div>
            </div>
        );
    }

    if (!userData) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="text-red-600 mb-4">Failed to load user data</div>
                    <button
                        onClick={() => navigate('/')}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Go Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div className="flex items-center justify-between mb-6">
                        <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
                        {!isEditing && (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Edit Profile
                            </button>
                        )}
                    </div>

                    {error && (
                        <div className="rounded-md bg-red-50 p-4 mb-4">
                            <p className="text-sm font-medium text-red-800">{error}</p>
                        </div>
                    )}

                    {/* User Information */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Email
                            </label>
                            <p className="text-gray-900">{userData.email}</p>
                        </div>

                        {userData.phone && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Phone
                                </label>
                                <p className="text-gray-900">{userData.phone}</p>
                            </div>
                        )}

                        {userData.first_name && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    First Name
                                </label>
                                <p className="text-gray-900">{userData.first_name}</p>
                            </div>
                        )}

                        {userData.last_name && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Last Name
                                </label>
                                <p className="text-gray-900">{userData.last_name}</p>
                            </div>
                        )}

                        {userData.created_at && (
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Member Since
                                </label>
                                <p className="text-gray-900">
                                    {new Date(userData.created_at).toLocaleDateString()}
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Profile Section */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Profile Information</h2>

                    {isEditing ? (
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="birth_date" className="block text-sm font-medium text-gray-700 mb-2">
                                    Birth Date
                                </label>
                                <input
                                    type="date"
                                    id="birth_date"
                                    value={profileForm.birth_date}
                                    onChange={(e) => handleProfileChange('birth_date', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label htmlFor="avatar_url" className="block text-sm font-medium text-gray-700 mb-2">
                                    Avatar URL
                                </label>
                                <input
                                    type="url"
                                    id="avatar_url"
                                    value={profileForm.avatar_url}
                                    onChange={(e) => handleProfileChange('avatar_url', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="https://example.com/avatar.jpg"
                                />
                                {profileForm.avatar_url && (
                                    <div className="mt-2">
                                        <img
                                            src={profileForm.avatar_url}
                                            alt="Avatar preview"
                                            className="w-24 h-24 rounded-full object-cover border-2 border-gray-200"
                                            onError={(e) => {
                                                e.target.style.display = 'none';
                                            }}
                                        />
                                    </div>
                                )}
                            </div>

                            <div>
                                <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                                    Address
                                </label>
                                <textarea
                                    id="address"
                                    value={profileForm.address}
                                    onChange={(e) => handleProfileChange('address', e.target.value)}
                                    rows="3"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Enter your address"
                                />
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button
                                    onClick={handleSaveProfile}
                                    disabled={isSaving}
                                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                >
                                    {isSaving ? 'Saving...' : 'Save Changes'}
                                </button>
                                <button
                                    onClick={handleCancelEdit}
                                    disabled={isSaving}
                                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 transition-colors"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {profile ? (
                                <>
                                    {profile.avatar_url && (
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                                Avatar
                                            </label>
                                            <img
                                                src={profile.avatar_url}
                                                alt="Avatar"
                                                className="w-32 h-32 rounded-full object-cover border-2 border-gray-200"
                                                onError={(e) => {
                                                    e.target.style.display = 'none';
                                                }}
                                            />
                                        </div>
                                    )}

                                    {profile.birth_date && (
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Birth Date
                                            </label>
                                            <p className="text-gray-900">
                                                {new Date(profile.birth_date).toLocaleDateString()}
                                            </p>
                                        </div>
                                    )}

                                    {profile.address && (
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Address
                                            </label>
                                            <p className="text-gray-900">{profile.address}</p>
                                        </div>
                                    )}

                                    {!profile.avatar_url && !profile.birth_date && !profile.address && (
                                        <p className="text-gray-500 italic">No profile information available. Click "Edit Profile" to add information.</p>
                                    )}
                                </>
                            ) : (
                                <p className="text-gray-500 italic">No profile created yet. Click "Edit Profile" to create one.</p>
                            )}
                        </div>
                    )}
                </div>

                {/* Voting History */}
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Voting History</h2>
                    
                    {votes.length === 0 ? (
                        <p className="text-gray-500 italic">You haven't voted in any elections yet.</p>
                    ) : (
                        <div className="space-y-3">
                            {votesWithDetails.length > 0 ? (
                                votesWithDetails.map((vote) => (
                                    <div
                                        key={vote.id || vote._id}
                                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                                        onClick={() => handleVoteClick(vote.election_id)}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                                <h3 className="font-semibold text-gray-900 mb-2">
                                                    {vote.election?.title || vote.election?.name || 'Unknown Election'}
                                                </h3>
                                                <p className="text-sm text-gray-600 mb-1">
                                                    <span className="font-medium">Voted for:</span>{' '}
                                                    {vote.candidate?.name || 'Unknown Candidate'}
                                                </p>
                                                {vote.candidate?.description && (
                                                    <p className="text-sm text-gray-500 mb-2 line-clamp-2">
                                                        {vote.candidate.description}
                                                    </p>
                                                )}
                                                <p className="text-xs text-gray-400">
                                                    {new Date(vote.created_at).toLocaleString()}
                                                </p>
                                            </div>
                                            <svg
                                                className="w-5 h-5 text-gray-400 flex-shrink-0 ml-4"
                                                fill="none"
                                                stroke="currentColor"
                                                viewBox="0 0 24 24"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth={2}
                                                    d="M9 5l7 7-7 7"
                                                />
                                            </svg>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                votes.map((vote) => (
                                    <div
                                        key={vote.id || vote._id}
                                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                                        onClick={() => handleVoteClick(vote.election_id)}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                                <p className="text-sm text-gray-500 mb-1">
                                                    Voted on {new Date(vote.created_at).toLocaleDateString()}
                                                </p>
                                                <p className="text-gray-600 text-sm">
                                                    Election ID: {vote.election_id}
                                                </p>
                                                <p className="text-gray-600 text-sm">
                                                    Candidate ID: {vote.candidate_id}
                                                </p>
                                            </div>
                                            <svg
                                                className="w-5 h-5 text-gray-400"
                                                fill="none"
                                                stroke="currentColor"
                                                viewBox="0 0 24 24"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth={2}
                                                    d="M9 5l7 7-7 7"
                                                />
                                            </svg>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default UserProfilePage;

