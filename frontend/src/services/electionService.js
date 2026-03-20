import { axiosInstance } from './axiosConfig';

class ElectionService {
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

    async getElections() {
        return this.request('/elections');
    }

    async getElectionById(electionId) {
        return this.request(`/elections/${electionId}`);
    }

    async createElection(electionData, pdfFile = null) {
        if (pdfFile) {
            const formData = new FormData();
            
            Object.keys(electionData).forEach(key => {
                if (key === 'candidates' && Array.isArray(electionData[key])) {
                    formData.append('candidates', JSON.stringify(electionData[key]));
                } else if (key === 'settings' && typeof electionData[key] === 'object') {
                    formData.append('settings', JSON.stringify(electionData[key]));
                } else {
                    formData.append(key, electionData[key]);
                }
            });
            
            formData.append('pdfFile', pdfFile);
            
            try {
                const response = await axiosInstance({
                    url: '/elections',
                    method: 'POST',
                    data: formData,
                });
                return response.data;
            } catch (error) {
                throw error;
            }
        }
        
        return this.request('/elections', {
            method: 'POST',
            data: electionData,
        });
    }

    async updateElection(electionId, electionData) {
        return this.request(`/elections/${electionId}`, {
            method: 'PUT',
            data: electionData,
        });
    }

    async deleteElection(electionId) {
        return this.request(`/elections/${electionId}`, {
            method: 'DELETE',
        });
    }

    async requestAnonymousToken(electionId) {
        const response = await this.request(`/votes/election/${electionId}/request-token`, {
            method: 'POST',
        });
        return response.token;
    }

    async submitVote(electionId, candidateIds, anonymousToken = null) {
        const votes = Array.isArray(candidateIds) ? candidateIds : [candidateIds];
        const data = {
            election_id: electionId,
            candidate_ids: votes,
        };
        if (anonymousToken) {
            data.anonymous_token = anonymousToken;
        }
        const response = await this.request('/votes/batch', {
            method: 'POST',
            data,
        });
        return response.votes || [response];
    }

    async getMyVote(electionId) {
        try {
            return await this.request(`/votes/election/${electionId}/my-vote`);
        } catch (error) {
            if (error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    async getElectionResults(electionId) {
        const data = await this.request(`/votes/election/${electionId}/results`);

        if (Array.isArray(data)) {
            return data.reduce((acc, vote) => {
                const id = vote.candidate_id;
                if (id === undefined || id === null) {
                    return acc;
                }
                acc[id] = (acc[id] || 0) + 1;
                return acc;
            }, {});
        }
        return data;
    }
}

const electionService = new ElectionService();
export default electionService;

