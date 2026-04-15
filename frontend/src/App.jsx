import React, { useState, useEffect } from 'react';
import Auth from './components/Auth';
import Dashboard from './components/Dashboard';
import Footer from './components/Footer';
import './index.css';

function App() {
    const [token, setToken] = useState(null);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for saved auth on mount
        const savedToken = localStorage.getItem('token') || sessionStorage.getItem('token');
        const savedUser = localStorage.getItem('user') || sessionStorage.getItem('user');

        if (savedToken && savedUser) {
            try {
                setToken(savedToken);
                setUser(JSON.parse(savedUser));
            } catch (err) {
                console.error('Failed to parse saved user:', err);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('user');
            }
        }

        setLoading(false);
    }, []);

    const handleLogin = (newToken, newUser) => {
        setToken(newToken);
        setUser(newUser);
    };

    const handleLogout = () => {
        setToken(null);
        setUser(null);
    };

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                color: 'var(--text-primary)'
            }}>
                <div>Loading...</div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                {token && user ? (
                    <Dashboard token={token} user={user} onLogout={handleLogout} />
                ) : (
                    <Auth onLogin={handleLogin} />
                )}
            </div>
            {token && user && <Footer />}
        </div>
    );
}

export default App;
