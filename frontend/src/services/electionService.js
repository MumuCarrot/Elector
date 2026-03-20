import { axiosInstance } from './axiosConfig';

/**
 * HTTP client for elections and voting API endpoints.
 */
class ElectionService {
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
     * Lists all elections.
     *
     * @returns {Promise<unknown>} List payload (e.g. `{ elections: [...] }` or array).
     */
    async getElections() {
        return this.request('/elections');
    }

    /**
     * Fetches a single election by id.
     *
     * @param {string} electionId - Election identifier.
     * @returns {Promise<unknown>} Election detail payload.
     */
    async getElectionById(electionId) {
        return this.request(`/elections/${electionId}`);
    }

    /**
     * Creates an election; optionally uploads a PDF as multipart form data.
     *
     * @param {Record<string, unknown>} electionData - Title, description, candidates, settings, dates, etc.
     * @param {File|null} [pdfFile=null] - Optional PDF attachment.
     * @returns {Promise<unknown>} Created election response.
     */
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

    /**
     * Updates an existing election.
     *
     * @param {string} electionId - Election identifier.
     * @param {Record<string, unknown>} electionData - Fields to update.
     * @returns {Promise<unknown>} Update response.
     */
    async updateElection(electionId, electionData) {
        return this.request(`/elections/${electionId}`, {
            method: 'PUT',
            data: electionData,
        });
    }

    /**
     * Deletes an election.
     *
     * @param {string} electionId - Election identifier.
     * @returns {Promise<unknown>} Delete response.
     */
    async deleteElection(electionId) {
        return this.request(`/elections/${electionId}`, {
            method: 'DELETE',
        });
    }

    /**
     * Requests an anonymous voting token for an election.
     *
     * @param {string} electionId - Election identifier.
     * @returns {Promise<string>} Anonymous token string.
     */
    async requestAnonymousToken(electionId) {
        const response = await this.request(`/votes/election/${electionId}/request-token`, {
            method: 'POST',
        });
        return response.token;
    }

    /**
     * Submits one or more votes for candidates in an election.
     *
     * @param {string} electionId - Election identifier.
     * @param {string|string[]} candidateIds - Single id or list of candidate ids.
     * @param {string|null} [anonymousToken=null] - Token when anonymous voting is enabled.
     * @returns {Promise<unknown>} Vote submission response (votes array or wrapped).
     */
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

    /**
     * Returns the current user's vote for an election, or null if none (404).
     *
     * @param {string} electionId - Election identifier.
     * @returns {Promise<unknown|null>} Vote record or null.
     */
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

    /**
     * Fetches aggregated results; normalizes array tallies into a candidate-id → count map.
     *
     * @param {string} electionId - Election identifier.
     * @returns {Promise<Record<string, number>|unknown>} Counts per candidate or raw API shape.
     */
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

/** Singleton {@link ElectionService} for the app. */
const electionService = new ElectionService();
export default electionService;
