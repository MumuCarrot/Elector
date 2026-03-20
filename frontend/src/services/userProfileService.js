import { axiosInstance } from './axiosConfig';

/**
 * HTTP client for extended user profile and per-user vote listing.
 */
class UserProfileService {
    /**
     * Performs an API request via the shared axios instance.
     *
     * @param {string} endpoint - Relative path under the API base.
     * @param {import('axios').AxiosRequestConfig} [options={}] - Axios options; `method` defaults to GET.
     * @returns {Promise<unknown>} Parsed response body (`response.data`).
     */
    async request(endpoint, options = {}) {
        try {
            const response = await axiosInstance({
                url: endpoint,
                method: options.method || 'GET',
                data: options.data,
                ...options,
            });
            return response.data;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Fetches the authenticated user's profile, or null if not found (404).
     *
     * @returns {Promise<unknown|null>} Profile object or null.
     */
    async getMyProfile() {
        try {
            return await this.request('/user-profiles/me/profile');
        } catch (error) {
            if (error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    /**
     * Creates a profile for the current or specified user (per API contract).
     *
     * @param {Record<string, unknown>} profileData - Profile fields (e.g. birth_date, avatar_url, address).
     * @returns {Promise<unknown>} Created profile.
     */
    async createProfile(profileData) {
        return this.request('/user-profiles', {
            method: 'POST',
            data: profileData,
        });
    }

    /**
     * Updates the authenticated user's profile.
     *
     * @param {Record<string, unknown>} profileData - Fields to update.
     * @returns {Promise<unknown>} Updated profile.
     */
    async updateProfile(profileData) {
        return this.request('/user-profiles/me/profile', {
            method: 'PUT',
            data: profileData,
        });
    }

    /**
     * Lists votes cast by a user.
     *
     * @param {string} userId - User identifier.
     * @returns {Promise<unknown>} Votes list or wrapped payload.
     */
    async getUserVotes(userId) {
        return this.request(`/votes/user/${userId}`);
    }
}

/** Singleton {@link UserProfileService} for the app. */
const userProfileService = new UserProfileService();
export default userProfileService;
