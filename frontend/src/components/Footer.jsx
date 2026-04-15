import React from 'react';
import './Footer.css';

const Footer = () => {
    return (
        <footer className="app-footer glass-effect">
            <div className="footer-content">
                <p>&copy; {new Date().getFullYear()} AI Powered Multi Converter. All rights reserved.</p>
                <div className="footer-links">
                    <a href="#">Privacy Policy</a>
                    <a href="#">Terms of Service</a>
                    <a href="https://github.com" target="_blank" rel="noreferrer">GitHub</a>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
