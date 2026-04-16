import React, { useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import './Auth.css';

const Auth = ({ onLogin }) => {
    const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
    const [isLogin, setIsLogin] = useState(true);
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        fullName: '',
        remember: false,
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            if (isLogin) {
                const { data } = await authAPI.login(formData.email, formData.password);
                if (data.success) {
                    const storage = formData.remember ? localStorage : sessionStorage;
                    storage.setItem('token', data.token);
                    storage.setItem('user', JSON.stringify(data.user));
                    onLogin(data.token, data.user);
                } else {
                    setError(data.detail || 'Login failed');
                }
            } else {
                const { data } = await authAPI.register(
                    formData.email,
                    formData.password,
                    formData.fullName
                );
                if (data.success) {
                    setSuccess('Registration successful! Please login.');
                    setTimeout(() => {
                        setIsLogin(true);
                        setSuccess('');
                    }, 500);
                } else {
                    setError(data.detail || 'Registration failed');
                }
            }
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Network error. Make sure backend is running on http://localhost:8000'
            );
        }

        setLoading(false);
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const toggleMode = () => {
        setIsLogin(!isLogin);
        setError('');
        setSuccess('');
        setShowPassword(false);
        setFormData({ email: '', password: '', fullName: '', remember: false });
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <button 
                    className="theme-toggle-btn" 
                    onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                    title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
                >
                    {theme === 'light' ? '🌙' : '☀️'}
                </button>

                <div className="auth-header">
                    <div className="logo-container">
                        <div className="logo-icon">&lt;/&gt;</div>
                        <div className="logo-text">
                            <div className="logo-title gradient-text">AI-Powered</div>
                            <div className="logo-subtitle gradient-text">Multi-Code Converter</div>
                        </div>
                    </div>
                    <h2 className="auth-title">{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
                    <p className="auth-description">
                        {isLogin ? 'Log in to continue your journey' : 'Join us to start converting code'}
                    </p>
                </div>

                {error && <div className="message error-message">{error}</div>}
                {success && <div className="message success-message">{success}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    {!isLogin && (
                        <div className="form-group">
                            <label className="form-label">Full Name (Optional)</label>
                            <input
                                type="text"
                                name="fullName"
                                className="form-input"
                                placeholder="Enter your full name"
                                value={formData.fullName}
                                onChange={handleChange}
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input
                            type="email"
                            name="email"
                            className="form-input"
                            placeholder="Enter your email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showPassword ? "text" : "password"}
                                name="password"
                                className="form-input"
                                placeholder="Enter your password"
                                value={formData.password}
                                onChange={handleChange}
                                required
                            />
                            <button
                                type="button"
                                className="password-toggle-btn"
                                onClick={() => setShowPassword(!showPassword)}
                                aria-label={showPassword ? "Hide password" : "Show password"}
                            >
                                {showPassword ? (
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                                        <line x1="1" y1="1" x2="23" y2="23"></line>
                                    </svg>
                                ) : (
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                        <circle cx="12" cy="12" r="3"></circle>
                                    </svg>
                                )}
                            </button>
                        </div>
                    </div>

                    {isLogin && (
                        <div className="form-extras">
                            <label className="checkbox-label">
                                <input
                                    type="checkbox"
                                    name="remember"
                                    checked={formData.remember}
                                    onChange={handleChange}
                                />
                                <span>Remember me</span>
                            </label>
                            <a href="#" className="forgot-link">
                                Forgot password?
                            </a>
                        </div>
                    )}

                    <button type="submit" className="auth-button" disabled={loading}>
                        <span className="button-text">
                            {loading ? 'Processing...' : isLogin ? 'Log In' : 'Sign Up'}
                        </span>
                    </button>
                </form>

                <div className="auth-divider">
                    <span>or {isLogin ? 'sign up' : 'log in'}</span>
                </div>

                <div className="auth-switch">
                    {isLogin ? "Don't have an account? " : 'Already have an account? '}
                    <button type="button" onClick={toggleMode} className="switch-link">
                        {isLogin ? 'Sign Up' : 'Log In'}
                    </button>
                </div>
            </div>

            {/* Floating particles effect */}
            <div className="particles">
                <div className="particle"></div>
                <div className="particle"></div>
                <div className="particle"></div>
                <div className="particle"></div>
                <div className="particle"></div>
            </div>
        </div>
    );
};

export default Auth;
