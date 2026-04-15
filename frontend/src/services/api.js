import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

export const authAPI = {
    register: (email, password, fullName = '') =>
        api.post('/auth/register', { email, password, full_name: fullName }),

    login: (email, password) =>
        api.post('/auth/login', { email, password }),

    logout: () =>
        api.post('/auth/logout'),

    verify: () =>
        api.get('/auth/verify'),
};

export const converterAPI = {
    convert: (sourceCode, sourceLang, targetLang, includeVideo = false) =>
        api.post('/convert', {
            source_code: sourceCode,
            source_language: sourceLang,
            target_language: targetLang,
            include_video: includeVideo,
        }),

    getHistory: (limit = 10) =>
        api.get(`/history?limit=${limit}`),

    getConversionDetail: (id) =>
        api.get(`/history/${id}`),

    clearHistory: () =>
        api.delete('/history'),

    runCode: (code, language, stdin = "") =>
        api.post('/run', { code, language, stdin }),
};

export const statsAPI = {
    getStats: () =>
        api.get('/stats'),

    getVideos: (language = null) =>
        api.get(language ? `/videos?language=${language}` : '/videos'),

    getPreferences: () =>
        api.get('/preferences'),

    updatePreferences: (preferences) =>
        api.put('/preferences', preferences),

    updateVideo: (id, url) =>
        api.put(`/videos/${id}`, { video_url: url }),
};

export default api;
