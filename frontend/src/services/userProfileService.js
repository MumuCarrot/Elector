import { axiosInstance } from './axiosConfig';

class UserProfileService {
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

    async createProfile(profileData) {
        return this.request('/user-profiles', {
            method: 'POST',
            data: profileData,
        });
    }

    async updateProfile(profileData) {
        return this.request('/user-profiles/me/profile', {
            method: 'PUT',
            data: profileData,
        });
    }

    async getUserVotes(userId) {
        return this.request(`/votes/user/${userId}`);
    }
}

const userProfileService = new UserProfileService();
export default userProfileService;

