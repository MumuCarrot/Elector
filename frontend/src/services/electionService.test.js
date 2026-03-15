import electionService from './electionService';
import { axiosInstance } from './axiosConfig';

jest.mock('./axiosConfig', () => ({
    axiosInstance: jest.fn(),
}));

describe('electionService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('getElections calls /elections', async () => {
        axiosInstance.mockResolvedValueOnce({ data: { elections: [] } });

        const result = await electionService.getElections();

        expect(axiosInstance).toHaveBeenCalledWith({
            url: '/elections',
            method: 'GET',
            data: undefined,
        });
        expect(result).toEqual({ elections: [] });
    });

    test('getElectionResults aggregates votes per candidate', async () => {
        axiosInstance.mockResolvedValueOnce({
            data: [
                { candidate_id: 1 },
                { candidate_id: 1 },
                { candidate_id: 2 },
            ],
        });

        const result = await electionService.getElectionResults(10);

        expect(axiosInstance).toHaveBeenCalledWith({
            url: '/votes/election/10',
            method: 'GET',
            data: undefined,
        });
        expect(result).toEqual({ 1: 2, 2: 1 });
    });
});


