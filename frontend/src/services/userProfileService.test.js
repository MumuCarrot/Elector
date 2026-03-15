import userProfileService from './userProfileService';
import { axiosInstance } from './axiosConfig';

jest.mock('./axiosConfig', () => ({
    axiosInstance: jest.fn(),
}));

describe('userProfileService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('getMyProfile returns null on 404', async () => {
        const error = new Error('Not found');
        error.response = { status: 404 };
        axiosInstance.mockRejectedValueOnce(error);

        const result = await userProfileService.getMyProfile();

        expect(result).toBeNull();
    });

    test('createProfile sends POST to /user-profiles', async () => {
        axiosInstance.mockResolvedValueOnce({ data: { id: 1 } });

        const profileData = { first_name: 'John' };
        const result = await userProfileService.createProfile(profileData);

        expect(axiosInstance).toHaveBeenCalledWith({
            url: '/user-profiles',
            method: 'POST',
            data: profileData,
        });
        expect(result).toEqual({ id: 1 });
    });
});


