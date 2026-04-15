import React, { useState, useEffect } from 'react';
import { converterAPI, statsAPI, authAPI } from '../services/api';
import './Dashboard.css';

const LANGUAGES = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C',
    'Go', 'Rust', 'Swift', 'Kotlin', 'Ruby', 'PHP', 'Dart', 'Scala',
    'R', 'MATLAB', 'Julia', 'Perl', 'Haskell', 'Lua', 'Objective-C',
    'Visual Basic', 'F#', 'Elixir', 'Clojure', 'Groovy', 'Assembly',
    'Shell', 'PowerShell', 'SQL'
];

const Dashboard = ({ token, user, onLogout }) => {
    const [sourceCode, setSourceCode] = useState('');
    const [convertedCode, setConvertedCode] = useState('');
    const [sourceLang, setSourceLang] = useState('Python');
    const [targetLang, setTargetLang] = useState('JavaScript');
    const [includeVideo, setIncludeVideo] = useState(true);
    const [isConverting, setIsConverting] = useState(false);
    const [recentConversions, setRecentConversions] = useState([]);
    const [showInputModal, setShowInputModal] = useState(false);
    const [videos, setVideos] = useState([]);
    const [activeVideo, setActiveVideo] = useState(null);
    const [error, setError] = useState('');
    const [stdin, setStdin] = useState('');
    const [output, setOutput] = useState('');
    const [isExecuting, setIsExecuting] = useState(false);
    const [executionError, setExecutionError] = useState('');
    const [stats, setStats] = useState({
        total_conversions: 0,
        successful_conversions: 0,
        success_rate: 0,
        most_used_source: null,
        most_used_target: null,
    });
    const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
    const [terminalInput, setTerminalInput] = useState('');
    const [terminalHistory, setTerminalHistory] = useState([]);
    const [lastTotalOutput, setLastTotalOutput] = useState('');
    const terminalRef = React.useRef(null);

    // Auto-scroll terminal to bottom
    useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [terminalHistory, output, executionError, isExecuting]);

    useEffect(() => {
        loadHistory();
        loadStats();
        loadVideos();
    }, []);

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const loadHistory = async () => {
        try {
            const { data } = await converterAPI.getHistory();
            if (data.success) {
                setRecentConversions(data.history);
            }
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    };

    const loadStats = async () => {
        try {
            const { data } = await statsAPI.getStats();
            if (data.success) {
                setStats(data.stats);
            }
        } catch (err) {
            console.error('Failed to load stats:', err);
        }
    };

    const loadVideos = async () => {
        try {
            const { data } = await statsAPI.getVideos();
            if (data.success) {
                setVideos(data.videos);
            }
        } catch (err) {
            console.error('Failed to load videos:', err);
        }
    };

    const handleConvert = async () => {
        if (!sourceCode.trim()) {
            alert('Please enter source code to convert');
            return;
        }

        setIsConverting(true);
        setError('');

        try {
            const { data } = await converterAPI.convert(
                sourceCode,
                sourceLang,
                targetLang
            );

            if (data.success) {
                setConvertedCode(data.converted_code);
                loadHistory();
                loadStats();
            }
        } catch (err) {
            console.error('Conversion error:', err);
            const errorMessage = err.response?.data?.detail || err.message;
            setError(errorMessage);
            setConvertedCode('// Error: ' + errorMessage);
        } finally {
            setIsConverting(false);
        }
    };

    const handleRunCode = async (skipDetection = false, useNewInput = null) => {
        if (!convertedCode) return;
        
        let currentStdin = useNewInput !== null ? useNewInput : stdin;
        
        setIsExecuting(true);
        setExecutionError('');
        
        if (useNewInput === null) {
            // This is a fresh run (starting from scratch)
            setTerminalHistory([]);
            setLastTotalOutput('');
            setStdin('');
            currentStdin = '';
        }

        try {
            const { data } = await converterAPI.runCode(convertedCode, targetLang, currentStdin);
            if (data.success) {
                const totalOutput = data.output || '';
                
                // Calculate the "new" part of the output compared to last time
                let newPart = totalOutput;
                if (useNewInput !== null && totalOutput.startsWith(lastTotalOutput)) {
                    newPart = totalOutput.substring(lastTotalOutput.length);
                }

                if (newPart) {
                    setTerminalHistory(prev => [...prev, { type: 'program', text: newPart }]);
                } else if (useNewInput === null && !totalOutput) {
                    setTerminalHistory([{ type: 'program', text: 'Code executed successfully with no output.' }]);
                }
                
                setLastTotalOutput(totalOutput);
                setOutput(totalOutput); // Keep for compatibility
            }
        } catch (err) {
            console.error('Execution error:', err);
            const errorMessage = err.response?.data?.detail || 'Failed to execute code. Please try again.';
            setExecutionError(errorMessage);
            setTerminalHistory(prev => [...prev, { type: 'error', text: errorMessage }]);
        } finally {
            setIsExecuting(false);
        }
    };

    const handleTerminalKeyDown = (e) => {
        if (e.key === 'Enter') {
            const input = terminalInput;
            // Echo input to history immediately
            setTerminalHistory(prev => [...prev, { type: 'user', text: input }]);
            
            // Ensure trailing newline for reliable input capture
            const newStdin = stdin ? `${stdin}${input}\n` : `${input}\n`;
            setStdin(newStdin);
            setTerminalInput('');
            handleRunCode(true, newStdin);
        }
    };

    const handleLogout = async () => {
        try {
            await authAPI.logout();
        } catch (err) {
            console.error('Logout error:', err);
        }
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        onLogout();
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        alert('Copied to clipboard!');
    };

    const handleSaveCode = () => {
        if (!convertedCode) return;

        const extensions = {
            Python: 'py',
            Java: 'java',
            JavaScript: 'js',
            TypeScript: 'ts',
            'C++': 'cpp',
            'C#': 'cs',
            C: 'c',
            Go: 'go',
            Rust: 'rs',
            Swift: 'swift',
            Kotlin: 'kt',
            Ruby: 'rb',
            PHP: 'php',
            Dart: 'dart',
            Scala: 'scala',
            R: 'R',
            MATLAB: 'm',
            Julia: 'jl',
            Perl: 'pl',
            Haskell: 'hs',
            Lua: 'lua',
            'Objective-C': 'm',
            'Visual Basic': 'vb',
            'F#': 'fs',
            Elixir: 'ex',
            Clojure: 'clj',
            Groovy: 'groovy',
            Assembly: 'asm',
            Shell: 'sh',
            PowerShell: 'ps1',
            SQL: 'sql'
        };

        const ext = extensions[targetLang] || 'txt';
        const filename = `converted_code.${ext}`;
        
        const blob = new Blob([convertedCode], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const swapLanguages = () => {
        setSourceLang(targetLang);
        setTargetLang(sourceLang);
        setSourceCode(convertedCode);
        setConvertedCode(sourceCode);
    };

    const getLanguageIcon = (lang) => {
        const icons = {
            Python: '🐍',
            Java: '☕',
            JavaScript: '📜',
            TypeScript: '💙',
            'C++': '⚙️',
            'C#': '🎯',
            Go: '🔵',
            Rust: '🦀',
            Swift: '🍎',
            Kotlin: '🟣',
            Ruby: '💎',
            PHP: '🐘',
        };
        return icons[lang] || '💻';
    };

    const handleClearHistory = async () => {
        if (!confirm('Are you sure you want to clear your conversion history?')) {
            return;
        }

        try {
            await converterAPI.clearHistory();
            setRecentConversions([]);
            loadStats();
        } catch (err) {
            console.error('Failed to clear history:', err);
            alert('Failed to clear history');
        }
    };

    const [editingVideo, setEditingVideo] = useState(null);
    const [editUrl, setEditUrl] = useState('');

    const handleRecentConversionClick = async (item) => {
        if (!item.id) return;
        
        try {
            const { data } = await converterAPI.getConversionDetail(item.id);
            if (data.success) {
                setSourceLang(data.conversion.source_language);
                setTargetLang(data.conversion.target_language);
                setSourceCode(data.conversion.source_code);
                setConvertedCode(data.conversion.converted_code);
                setOutput('');
                setTerminalHistory([]);
                setLastTotalOutput('');
                setExecutionError('');
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        } catch (err) {
            console.error('Failed to load conversion details:', err);
            setError('Failed to load conversion details.');
        }
    };

    const handleEditClick = (video, e) => {
        e.stopPropagation();
        setEditingVideo(video.id);
        setEditUrl(video.video_url || '');
    };

    const handleSaveVideo = async (id, e) => {
        e.stopPropagation();
        try {
            // Extract Video ID or Playlist ID
            let newUrl = editUrl;
            const playlistMatch = editUrl.match(/[?&]list=([^#\&\?]+)/);
            const videoMatch = editUrl.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/);

            if (playlistMatch) {
                newUrl = `https://www.youtube.com/embed/videoseries?list=${playlistMatch[1]}`;
            } else if (videoMatch) {
                newUrl = `https://www.youtube.com/embed/${videoMatch[1]}`;
            }

            await statsAPI.updateVideo(id, newUrl);
            setEditingVideo(null);
            loadVideos();
        } catch (err) {
            console.error('Failed to update video:', err);
            alert('Failed to update video URL');
        }
    };

    return (
        <div className="dashboard">
            {isConverting && (
                <div className="loading-overlay">
                    <div className="loading-content">
                        <div className="loading-spinner"></div>
                        <div className="loading-text">Converting Code...</div>
                        <div className="loading-subtext">AI is analyzing and translating your code</div>
                    </div>
                </div>
            )}

            <div className="dashboard-container">
                {/* Header */}
                <header className="header">
                    <h1 className="header-title gradient-text">AI Multi-Code Converter</h1>
                    <div className="header-actions">
                        <button 
                            className="icon-btn theme-toggle" 
                            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
                        >
                            {theme === 'light' ? '🌙' : '☀️'}
                        </button>
                        <div className="user-info">
                            <div className="user-avatar">{user.email.charAt(0).toUpperCase()}</div>
                            <span className="user-name">{user.full_name || user.email}</span>
                        </div>
                        <button className="logout-btn" onClick={handleLogout}>
                            Logout
                        </button>
                    </div>
                </header>

                {/* Stats Bar */}
                <div className="stats-bar">
                    <div className="stat-card">
                        <div className="stat-value gradient-text">{stats.total_conversions}</div>
                        <div className="stat-label">Total Conversions</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value gradient-text">{stats.success_rate.toFixed(1)}%</div>
                        <div className="stat-label">Success Rate</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value gradient-text">{stats.most_used_source || 'N/A'}</div>
                        <div className="stat-label">Most Used Source</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value gradient-text">{stats.most_used_target || 'N/A'}</div>
                        <div className="stat-label">Most Used Target</div>
                    </div>
                </div>

                {/* Error Alert */}
                {error && (
                    <div className="error-alert">
                        <span>{error}</span>
                        <button className="close-btn" onClick={() => setError('')}>×</button>
                    </div>
                )}

                {/* Converter Layout Container */}
                <div className="converter-layout-wrapper">
                    <div className="converter-grid">
                        {/* Source Code Panel */}
                        <div className="converter-panel">
                            <div className="panel-header">
                                <div className="language-selector">
                                    <select
                                        className="language-select"
                                        value={sourceLang}
                                        onChange={(e) => setSourceLang(e.target.value)}
                                    >
                                        {LANGUAGES.map((lang) => (
                                            <option key={lang} value={lang}>
                                                {getLanguageIcon(lang)} {lang}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <button
                                    className="icon-btn"
                                    onClick={() => setSourceCode('')}
                                    title="Clear"
                                >
                                    🗑️
                                </button>
                            </div>
                            <textarea
                                className="code-editor code-font"
                                placeholder="// Paste your source code here..."
                                value={sourceCode}
                                onChange={(e) => setSourceCode(e.target.value)}
                            />
                        </div>

                        {/* Central Swap Button */}
                        <div className="swap-button-container">
                            <button className="swap-btn-circular" onClick={swapLanguages} title="Swap languages">
                                ⇄
                            </button>
                        </div>

                        {/* Converted Code Panel */}
                        <div className="converter-panel">
                            <div className="panel-header">
                                <div className="language-selector">
                                    <select
                                        className="language-select"
                                        value={targetLang}
                                        onChange={(e) => setTargetLang(e.target.value)}
                                    >
                                        {LANGUAGES.map((lang) => (
                                            <option key={lang} value={lang}>
                                                {getLanguageIcon(lang)} {lang}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        className="icon-btn"
                                        onClick={() => setConvertedCode('')}
                                        title="Clear"
                                        disabled={!convertedCode}
                                    >
                                        🗑️
                                    </button>
                                    <button
                                        className="icon-btn"
                                        onClick={() => copyToClipboard(convertedCode)}
                                        title="Copy to clipboard"
                                        disabled={!convertedCode}
                                    >
                                        📋
                                    </button>
                                    <button
                                        className="icon-btn"
                                        onClick={handleSaveCode}
                                        title="Save code to file"
                                        disabled={!convertedCode}
                                    >
                                        💾
                                    </button>
                                    <button
                                        className="icon-btn run-btn"
                                        onClick={handleRunCode}
                                        title="Run Code"
                                        disabled={!convertedCode || isExecuting}
                                    >
                                        {isExecuting ? '⏳' : '▶️'}
                                    </button>
                                </div>
                            </div>
                            <textarea
                                className="code-editor code-font"
                                placeholder="// Converted code will appear here..."
                                value={convertedCode}
                                onChange={(e) => setConvertedCode(e.target.value)}
                            />
                            
                            {/* Terminal Output Window */}
                            {(output || executionError || isExecuting) && (
                                <div className="terminal-window">
                                    <div className="terminal-header">
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <span className="terminal-title">Terminal Output</span>
                                            <button 
                                                className="reset-terminal-btn" 
                                                onClick={() => { setStdin(''); setOutput(''); setTerminalHistory([]); setLastTotalOutput(''); setTerminalInput(''); setExecutionError(''); }}
                                                title="Reset Terminal & Inputs"
                                            >
                                                🔄 Reset
                                            </button>
                                        </div>
                                        <button className="terminal-close" onClick={() => { setOutput(''); setExecutionError(''); }}>×</button>
                                    </div>
                                    <div className="terminal-body code-font" ref={terminalRef}>
                                        {terminalHistory.map((line, idx) => (
                                            <div key={idx} className={`terminal-line terminal-line-${line.type}`}>
                                                {line.type === 'user' ? (
                                                    <span className="terminal-input-echo">
                                                        <span className="terminal-prompt-symbol">&gt;</span> {line.text}
                                                    </span>
                                                ) : line.type === 'error' ? (
                                                    <div className="terminal-error">{line.text}</div>
                                                ) : (
                                                    <pre className="terminal-text">{line.text}</pre>
                                                )}
                                            </div>
                                        ))}
                                        
                                        {isExecuting && (
                                            <div className="terminal-loading">
                                                <span className="typing-dot">.</span>
                                                <span className="typing-dot">.</span>
                                                <span className="typing-dot">.</span>
                                                Executing...
                                            </div>
                                        )}
                                        
                                        {/* Interactive Input Prompt */}
                                        {!isExecuting && (
                                            <div className="terminal-input-row">
                                                <span className="terminal-prompt-symbol">&gt;</span>
                                                <input
                                                    type="text"
                                                    className="terminal-input-field code-font"
                                                    value={terminalInput}
                                                    onChange={(e) => setTerminalInput(e.target.value)}
                                                    onKeyDown={handleTerminalKeyDown}
                                                    placeholder="Type input here..."
                                                    autoFocus
                                                />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Main Conversion Button Underneath editors */}
                <div className="convert-action-container">
                    <button className="convert-btn-large" onClick={handleConvert} disabled={isConverting}>
                        <span>{isConverting ? 'Scanning & Translating...' : '✨ Convert Code'}</span>
                    </button>
                </div>

                {/* Lower Information Panel */}
                <div className="control-panel options-panel">
                    <div className="options-section">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={includeVideo}
                                onChange={(e) => setIncludeVideo(e.target.checked)}
                            />
                            <span>Include Explanatory Video Tutorial</span>
                        </label>
                    </div>

                    {/* Recent Conversions */}
                    <div className="recent-conversions">
                        <div className="recent-header">
                            <h4 className="recent-title">Recent Conversions</h4>
                            {recentConversions.length > 0 && (
                                <button
                                    className="clear-history-btn"
                                    onClick={handleClearHistory}
                                    title="Clear All History"
                                >
                                    Clear All
                                </button>
                            )}
                        </div>
                        <div className="recent-list">
                            {recentConversions.length > 0 ? (
                                recentConversions.map((item, index) => (
                                    <div 
                                        key={index} 
                                        className="recent-item clickable-recent" 
                                        onClick={() => handleRecentConversionClick(item)} 
                                        style={{ cursor: 'pointer' }}
                                        title="Click to load this conversion into the editor"
                                    >
                                        <div className="recent-icon">↔</div>
                                        <div className="recent-details">
                                            <div className="recent-lang">
                                                {item.from} → {item.to}
                                            </div>
                                            <div className="recent-status">({item.status})</div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="empty-state">No conversions yet. Start converting code!</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Video Tutorials */}
                {includeVideo && videos.length > 0 && (
                    <div className="video-section">
                        <div className="video-header">
                            <h3 className="video-title">Programming Language Tutorials</h3>
                            <p className="video-subtitle">
                                Showing tutorials for {sourceLang} and {targetLang}. Click a card to play.
                            </p>
                        </div>
                        <div className="video-grid">
                            {videos
                                .filter(video => video.language === sourceLang || video.language === targetLang)
                                .map((video, index) => (
                                    <div
                                        key={index}
                                        className={`video-card ${activeVideo === video.id ? 'active' : ''}`}
                                        onClick={() => !editingVideo && setActiveVideo(video.id)}
                                    >
                                        {editingVideo === video.id ? (
                                            <div className="video-edit-overlay" onClick={(e) => e.stopPropagation()}>
                                                <input
                                                    type="text"
                                                    className="video-url-input"
                                                    value={editUrl}
                                                    onChange={(e) => setEditUrl(e.target.value)}
                                                    placeholder="Paste YouTube URL/Playlist"
                                                />
                                                <div className="video-edit-actions">
                                                    <button className="save-btn" onClick={(e) => handleSaveVideo(video.id, e)}>Save</button>
                                                    <button className="cancel-btn" onClick={() => setEditingVideo(null)}>Cancel</button>
                                                </div>
                                            </div>
                                        ) : activeVideo === video.id ? (
                                            <div className="video-player-wrapper">
                                                <iframe
                                                    src={`${video.video_url}${video.video_url.includes('?') ? '&' : '?'}autoplay=1`}
                                                    title={video.title}
                                                    frameBorder="0"
                                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                    allowFullScreen
                                                    className="video-iframe"
                                                ></iframe>
                                            </div>
                                        ) : (
                                            <div className="video-thumbnail">
                                                <div className="play-icon">{getLanguageIcon(video.language)}</div>
                                                <div className="play-overlay">
                                                    <span>▶ Play Tutorial</span>
                                                </div>
                                                <button
                                                    className="edit-video-btn"
                                                    onClick={(e) => handleEditClick(video, e)}
                                                    title="Edit Video URL"
                                                >
                                                    ✎
                                                </button>
                                            </div>
                                        )}
                                        <div className="video-info">
                                            <div className="video-lang">{video.language}</div>
                                            <div className="video-desc">{video.title}</div>
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
