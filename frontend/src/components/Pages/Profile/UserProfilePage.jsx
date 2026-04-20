import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import authService from '../../../services/authService';
import userProfileService from '../../../services/userProfileService';
import electionService from '../../../services/electionService';

/** @returns {string} Local today's date as YYYY-MM-DD for `<input type="date" max>`. */
function todayISODate() {
    const t = new Date();
    const y = t.getFullYear();
    const m = String(t.getMonth() + 1).padStart(2, '0');
    const d = String(t.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

/**
 * Client-side avatar check: valid http(s) URL and `<img>` load success.
 *
 * @param {string} url - Trimmed URL or empty.
 * @returns {Promise<{ ok: boolean, message?: string }>}
 */
function validateAvatarUrlClient(url) {
    const trimmed = url.trim();
    if (!trimmed) {
        return Promise.resolve({ ok: true });
    }
    try {
        const u = new URL(trimmed);
        if (u.protocol !== 'http:' && u.protocol !== 'https:') {
            return Promise.resolve({ ok: false, message: 'Avatar URL must use http or https' });
        }
    } catch {
        return Promise.resolve({ ok: false, message: 'Avatar URL is not valid' });
    }
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => resolve({ ok: true });
        img.onerror = () =>
            resolve({ ok: false, message: 'Avatar URL does not load as an image' });
        img.src = trimmed;
    });
}

/**
 * @param {object|null|undefined} u - User object from API.
 * @returns {{ email: string, phone: string, first_name: string, last_name: string }}
 */
function buildAccountForm(u) {
    return {
        email: u?.email ?? '',
        phone: u?.phone ?? '',
        first_name: u?.first_name ?? '',
        last_name: u?.last_name ?? '',
    };
}

/**
 * Authenticated profile: editable account + extended profile, voting history.
 *
 * @returns {JSX.Element} Profile page.
 */
function UserProfilePage() {
    const navigate = useNavigate();
    const { isAuthenticated, updateUser } = useAuth();
    const [userData, setUserData] = useState(null);
    const [profile, setProfile] = useState(null);
    const [votes, setVotes] = useState([]);
    const [votesWithDetails, setVotesWithDetails] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [accountForm, setAccountForm] = useState(buildAccountForm(null));
    const [profileForm, setProfileForm] = useState({
        birth_date: '',
        avatar_url: '',
        address: '',
    });

    const fetchUserData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError('');

            const userResponse = await authService.getCurrentUser();
            const userInfo = userResponse.user || userResponse;
            setUserData(userInfo);
            setAccountForm(buildAccountForm(userInfo));

            const profileData = await userProfileService.getMyProfile();
            setProfile(profileData);

            if (profileData) {
                setProfileForm({
                    birth_date: profileData.birth_date || '',
                    avatar_url: profileData.avatar_url || '',
                    address: profileData.address || '',
                });
            } else {
                setProfileForm({
                    birth_date: '',
                    avatar_url: '',
                    address: '',
                });
            }

            if (userInfo.id || userInfo._id) {
                try {
                    const uid = userInfo.id || userInfo._id;
                    const votesData = await userProfileService.getUserVotes(uid);
                    const votesArray = Array.isArray(votesData) ? votesData : votesData?.votes || [];
                    setVotes(votesArray);

                    const votesDetails = await Promise.all(
                        votesArray.map(async (vote) => {
                            try {
                                const election = await electionService.getElectionById(vote.election_id);
                                const electionData = election.election || election;
                                const candidate = electionData.candidates?.find(
                                    (c) => (c.id || c._id) === vote.candidate_id
                                );
                                return {
                                    ...vote,
                                    election: electionData,
                                    candidate,
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
    }, []);

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/auth/login');
            return;
        }
        fetchUserData();
    }, [isAuthenticated, navigate, fetchUserData]);

    /**
     * @param {string} field - Account form key.
     * @param {string} value - New value.
     */
    const handleAccountChange = (field, value) => {
        setAccountForm((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    /**
     * @param {string} field - Profile form key.
     * @param {string} value - New value.
     */
    const handleProfileChange = (field, value) => {
        setProfileForm((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    /**
     * Validates and persists account + profile.
     *
     * @returns {Promise<void>}
     */
    const handleSaveAll = async () => {
        setError('');
        const emailTrim = accountForm.email.trim();
        if (!emailTrim) {
            setError('Email is required');
            return;
        }

        if (profileForm.birth_date && profileForm.birth_date > todayISODate()) {
            setError('Birth date cannot be later than today');
            return;
        }

        const avatarCheck = await validateAvatarUrlClient(profileForm.avatar_url || '');
        if (!avatarCheck.ok) {
            setError(avatarCheck.message || 'Invalid avatar URL');
            return;
        }

        setIsSaving(true);
        try {
            const accountPayload = {
                email: emailTrim,
                phone: accountForm.phone.trim() || null,
                first_name: accountForm.first_name.trim() || null,
                last_name: accountForm.last_name.trim() || null,
            };

            const accountRes = await authService.updateCurrentUser(accountPayload);
            const updatedUser = accountRes.user || accountRes;
            setUserData(updatedUser);
            setAccountForm(buildAccountForm(updatedUser));
            updateUser(updatedUser);

            const profilePayload = {
                birth_date: profileForm.birth_date || null,
                avatar_url: profileForm.avatar_url.trim() || null,
                address: profileForm.address.trim() || null,
            };

            let updatedProfile;
            if (profile) {
                updatedProfile = await userProfileService.updateProfile(profilePayload);
            } else {
                updatedProfile = await userProfileService.createProfile({
                    user_id: updatedUser.id || updatedUser._id,
                    ...profilePayload,
                });
            }

            setProfile(updatedProfile);
            setProfileForm({
                birth_date: updatedProfile.birth_date || '',
                avatar_url: updatedProfile.avatar_url || '',
                address: updatedProfile.address || '',
            });
            setIsEditing(false);
        } catch (err) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to save profile';
            const msg =
                typeof errorMessage === 'string'
                    ? errorMessage
                    : Array.isArray(errorMessage)
                      ? errorMessage.map((e) => e.msg || JSON.stringify(e)).join('; ')
                      : 'Failed to save profile';
            setError(msg);
        } finally {
            setIsSaving(false);
        }
    };

    /** Restores forms from saved state and exits edit mode. */
    const handleCancelEdit = () => {
        if (userData) {
            setAccountForm(buildAccountForm(userData));
        }
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

    /**
     * @param {string} electionId - Election to open.
     */
    const handleVoteClick = (electionId) => {
        navigate(`/votes/${electionId}`);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-16">
                <div className="text-gray-600">Loading profile...</div>
            </div>
        );
    }

    if (!userData) {
        return (
            <div className="flex items-center justify-center py-16 px-4">
                <div className="text-center">
                    <div className="text-red-600 mb-4">Failed to load user data</div>
                    <button
                        type="button"
                        onClick={() => navigate('/')}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Go Home
                    </button>
                </div>
            </div>
        );
    }

    const todayMax = todayISODate();

    return (
        <div className="bg-gray-50 py-8 px-4">
            <div className="max-w-4xl mx-auto">
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div className="flex items-center justify-between mb-6">
                        <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
                        {!isEditing && (
                            <button
                                type="button"
                                onClick={() => setIsEditing(true)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Edit profile
                            </button>
                        )}
                    </div>

                    {error && (
                        <div className="rounded-md bg-red-50 p-4 mb-4">
                            <p className="text-sm font-medium text-red-800">{error}</p>
                        </div>
                    )}

                    <h2 className="text-lg font-semibold text-gray-800 mb-4 border-b border-gray-100 pb-2">
                        Account
                    </h2>

                    {isEditing ? (
                        <div className="space-y-4 mb-8">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                                    Email
                                </label>
                                <input
                                    id="email"
                                    type="email"
                                    autoComplete="email"
                                    value={accountForm.email}
                                    onChange={(e) => handleAccountChange('email', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                                    Phone
                                </label>
                                <input
                                    id="phone"
                                    type="tel"
                                    autoComplete="tel"
                                    value={accountForm.phone}
                                    onChange={(e) => handleAccountChange('phone', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="+1 234 567 8900"
                                />
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label
                                        htmlFor="first_name"
                                        className="block text-sm font-medium text-gray-700 mb-1"
                                    >
                                        First name
                                    </label>
                                    <input
                                        id="first_name"
                                        type="text"
                                        autoComplete="given-name"
                                        value={accountForm.first_name}
                                        onChange={(e) => handleAccountChange('first_name', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label
                                        htmlFor="last_name"
                                        className="block text-sm font-medium text-gray-700 mb-1"
                                    >
                                        Last name
                                    </label>
                                    <input
                                        id="last_name"
                                        type="text"
                                        autoComplete="family-name"
                                        value={accountForm.last_name}
                                        onChange={(e) => handleAccountChange('last_name', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-3 mb-8">
                            <div>
                                <span className="block text-sm font-medium text-gray-700 mb-1">Email</span>
                                <p className="text-gray-900">{userData.email}</p>
                            </div>
                            <div>
                                <span className="block text-sm font-medium text-gray-700 mb-1">Phone</span>
                                <p className="text-gray-900">{userData.phone || '—'}</p>
                            </div>
                            <div>
                                <span className="block text-sm font-medium text-gray-700 mb-1">First name</span>
                                <p className="text-gray-900">{userData.first_name || '—'}</p>
                            </div>
                            <div>
                                <span className="block text-sm font-medium text-gray-700 mb-1">Last name</span>
                                <p className="text-gray-900">{userData.last_name || '—'}</p>
                            </div>
                            {userData.created_at && (
                                <div>
                                    <span className="block text-sm font-medium text-gray-700 mb-1">
                                        Member since
                                    </span>
                                    <p className="text-gray-900">
                                        {new Date(userData.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    <h2 className="text-lg font-semibold text-gray-800 mb-4 border-b border-gray-100 pb-2">
                        Profile details
                    </h2>

                    {isEditing ? (
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="birth_date" className="block text-sm font-medium text-gray-700 mb-2">
                                    Birth date
                                </label>
                                <input
                                    type="date"
                                    id="birth_date"
                                    max={todayMax}
                                    value={profileForm.birth_date}
                                    onChange={(e) => handleProfileChange('birth_date', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="mt-1 text-xs text-gray-500">Cannot be later than today.</p>
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
                                {profileForm.avatar_url.trim() ? (
                                    <div className="mt-2">
                                        <img
                                            src={profileForm.avatar_url.trim()}
                                            alt="Avatar preview"
                                            className="w-24 h-24 rounded-full object-cover border-2 border-gray-200"
                                            onError={(e) => {
                                                e.target.style.display = 'none';
                                            }}
                                        />
                                    </div>
                                ) : null}
                            </div>

                            <div>
                                <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                                    Address
                                </label>
                                <textarea
                                    id="address"
                                    value={profileForm.address}
                                    onChange={(e) => handleProfileChange('address', e.target.value)}
                                    rows={3}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Enter your address"
                                />
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button
                                    type="button"
                                    onClick={handleSaveAll}
                                    disabled={isSaving}
                                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                >
                                    {isSaving ? 'Saving...' : 'Save changes'}
                                </button>
                                <button
                                    type="button"
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
                            {profile?.avatar_url ? (
                                <div>
                                    <span className="block text-sm font-medium text-gray-700 mb-2">Avatar</span>
                                    <img
                                        src={profile.avatar_url}
                                        alt="Avatar"
                                        className="w-32 h-32 rounded-full object-cover border-2 border-gray-200"
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                        }}
                                    />
                                </div>
                            ) : null}

                            <div>
                                <span className="block text-sm font-medium text-gray-700 mb-1">Birth date</span>
                                <p className="text-gray-900">
                                    {profile?.birth_date
                                        ? new Date(profile.birth_date).toLocaleDateString()
                                        : '—'}
                                </p>
                            </div>

                            <div>
                                <span className="block text-sm font-medium text-gray-700 mb-1">Address</span>
                                <p className="text-gray-900">{profile?.address || '—'}</p>
                            </div>

                            {!profile && (
                                <p className="text-gray-500 italic text-sm">
                                    Extended profile will be created when you save for the first time.
                                </p>
                            )}
                        </div>
                    )}
                </div>

                <div className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Voting history</h2>

                    {votes.length === 0 ? (
                        <p className="text-gray-500 italic">You haven&apos;t voted in any elections yet.</p>
                    ) : (
                        <div className="space-y-3">
                            {votesWithDetails.length > 0
                                ? votesWithDetails.map((vote) => (
                                      <div
                                          key={vote.id || vote._id}
                                          className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                                          onClick={() => handleVoteClick(vote.election_id)}
                                          onKeyDown={(e) => {
                                              if (e.key === 'Enter' || e.key === ' ') {
                                                  e.preventDefault();
                                                  handleVoteClick(vote.election_id);
                                              }
                                          }}
                                          role="button"
                                          tabIndex={0}
                                      >
                                          <div className="flex justify-between items-start">
                                              <div className="flex-1">
                                                  <h3 className="font-semibold text-gray-900 mb-2">
                                                      {vote.election?.title ||
                                                          vote.election?.name ||
                                                          'Unknown election'}
                                                  </h3>
                                                  <p className="text-sm text-gray-600 mb-1">
                                                      <span className="font-medium">Voted for:</span>{' '}
                                                      {vote.candidate?.name || 'Unknown candidate'}
                                                  </p>
                                                  {vote.candidate?.description ? (
                                                      <p className="text-sm text-gray-500 mb-2 line-clamp-2">
                                                          {vote.candidate.description}
                                                      </p>
                                                  ) : null}
                                                  <p className="text-xs text-gray-400">
                                                      {new Date(vote.created_at).toLocaleString()}
                                                  </p>
                                              </div>
                                              <svg
                                                  className="w-5 h-5 text-gray-400 flex-shrink-0 ml-4"
                                                  fill="none"
                                                  stroke="currentColor"
                                                  viewBox="0 0 24 24"
                                                  aria-hidden
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
                                : votes.map((vote) => (
                                      <div
                                          key={vote.id || vote._id}
                                          className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                                          onClick={() => handleVoteClick(vote.election_id)}
                                          onKeyDown={(e) => {
                                              if (e.key === 'Enter' || e.key === ' ') {
                                                  e.preventDefault();
                                                  handleVoteClick(vote.election_id);
                                              }
                                          }}
                                          role="button"
                                          tabIndex={0}
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
                                                  aria-hidden
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
                                  ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default UserProfilePage;
