import React, { useState, useEffect, useRef } from 'react';
import { 
  Globe, 
  Send, 
  Search, 
  Wifi, 
  CreditCard, 
  Smartphone, 
  Zap, 
  Compass, 
  AlertTriangle, 
  Droplet, 
  ShieldAlert, 
  UserCheck, 
  Sparkles,
  ChevronDown,
  ChevronUp,
  MapPin,
  Clock,
  ExternalLink,
  X
} from 'lucide-react';
import './App.css';

const API_BASE_URL = window.location.origin;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [countries, setCountries] = useState([]);
  const [filteredCountries, setFilteredCountries] = useState([]);
  const [activeCountry, setActiveCountry] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const [hasSearched, setHasSearched] = useState(false);

  const messagesEndRef = useRef(null);

  // Check connection status & fetch country list
  useEffect(() => {
    fetch(`${API_BASE_URL}/countries`)
      .then((res) => {
        if (!res.ok) throw new Error('API offline');
        setIsOnline(true);
        return res.json();
      })
      .then((data) => {
        setCountries(data);
        setFilteredCountries(data);
        // Set UAE as default active country
        const defaultCountry = data.find(c => c.country.includes('UAE')) || data[0];
        setActiveCountry(defaultCountry);
      })
      .catch((err) => {
        console.error('Error fetching countries:', err);
        setIsOnline(false);
      });
  }, []);

  // Filter countries search
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredCountries(countries);
    } else {
      const filtered = countries.filter(c => 
        c.country.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.search_keywords_tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
      setFilteredCountries(filtered);
    }
  }, [searchQuery, countries]);

  // Scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const queryText = textToSend || input;
    if (!queryText.trim()) return;

    setHasSearched(true);

    // Add user message
    const userMsg = { sender: 'user', text: queryText };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, top_k: 10, final_k: 3 }),
      });

      if (!response.ok) throw new Error('Error getting response');

      const data = await response.json();
      
      // Add assistant response
      const assistantMsg = {
        sender: 'assistant',
        text: data.answer,
        sources: data.sources || [],
        latency: data.latency
      };
      setMessages(prev => [...prev, assistantMsg]);

      // If response mentions a country in our list, auto-select it in the sidebar
      const matchedCountry = countries.find(c => 
        queryText.toLowerCase().includes(c.country.split('(')[0].trim().toLowerCase())
      );
      if (matchedCountry) {
        setActiveCountry(matchedCountry);
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { 
        sender: 'assistant', 
        text: 'Sorry, I am having trouble connecting to the KanonesKa intelligence server. Please verify your Groq API key is configured.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSource = (index) => {
    setExpandedSources(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleSuggestion = (suggestion, countryName) => {
    // Set active country
    const matched = countries.find(c => c.country === countryName);
    if (matched) setActiveCountry(matched);
    handleSend(suggestion);
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="brand">
          <div className="brand-logo">🌍</div>
          <div className="brand-text">
            <h1>KanonesKa</h1>
            <p>Stateful RAG Travel Compliance Companion for Indian Citizens</p>
          </div>
        </div>
        
        <div className="nav-actions">
          <div className="api-status">
            <span className={`status-dot ${isOnline ? 'online' : 'offline'}`}></span>
            <span>{isOnline ? 'Intelligence Server Connected' : 'Server Offline'}</span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="dashboard">
        
        {/* Left Panel: 55 Countries Selector */}
        <section className="sidebar-left">
          <h2 className="section-title">
            <Globe size={16} /> Destinations ({filteredCountries.length})
          </h2>
          <div className="search-box-wrapper">
            <Search className="search-icon-left" size={16} />
            <input 
              type="text" 
              placeholder="Search destination..."
              className="country-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="clear-search-btn" onClick={() => setSearchQuery('')}>
                <X size={14} />
              </button>
            )}
          </div>
          <div className="country-list scrollbar-custom">
            {filteredCountries.map((c, idx) => (
              <div 
                key={idx}
                className={`country-item ${activeCountry?.country === c.country ? 'active' : ''}`}
                onClick={() => { setActiveCountry(c); setHasSearched(true); }}
              >
                <span>✈️</span>
                <span>{c.country}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Middle Panel: Dynamic Chat Feed */}
        <section className="chat-feed">
          <div className="messages-container scrollbar-custom">
            {messages.length === 0 ? (
              <div className="welcome-screen">
                <div className="globe-icon-large">🌏</div>
                <h2>Prepare for your Outbound Journey</h2>
                <p>
                  KanonesKa evaluates visa rules, gold limits, duty-free caps, local taboos, and emergency contact details for Indian travelers across 55 destinations.
                </p>
                <div className="suggestion-chips">
                  <div 
                    className="suggestion-chip"
                    onClick={() => handleSuggestion("Can I carry gold/cash into UAE? What is the limit?", "United Arab Emirates (UAE)")}
                  >
                    UAE Gold & Cash Limits 💰
                  </div>
                  <div 
                    className="suggestion-chip"
                    onClick={() => handleSuggestion("Is vaping legal in Singapore?", "Singapore")}
                  >
                    Vaping in Singapore 🚭
                  </div>
                  <div 
                    className="suggestion-chip"
                    onClick={() => handleSuggestion("What are the plug types and is tap water safe in Japan?", "Japan")}
                  >
                    Japan Tech & Water 🔌
                  </div>
                  <div 
                    className="suggestion-chip"
                    onClick={() => handleSuggestion("Is there a visa on arrival for Indians in Bali? What about the tourism levy?", "Indonesia (Bali)")}
                  >
                    Bali Visa & Tourist Levy 🏖️
                  </div>
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className={`message-bubble ${msg.sender}`}>
                  <div className="avatar">
                    {msg.sender === 'user' ? '🧑' : '🤖'}
                  </div>
                  <div className="message-text-wrapper">
                    <div className="message-text">
                      <p style={{ whiteSpace: 'pre-line' }}>{msg.text}</p>
                      
                      {/* Accordion Sources (Only for assistant response) */}
                      {msg.sender === 'assistant' && msg.sources && msg.sources.length > 0 && (
                        <div className="source-accordion">
                          <div className="accordion-header" onClick={() => toggleSource(index)}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <Compass size={12} /> View Retrieved Compliance Sources ({msg.sources.length})
                            </span>
                            {expandedSources[index] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </div>
                          
                          {expandedSources[index] && (
                            <div className="accordion-body">
                              <div style={{ display: 'flex', gap: '15px', fontSize: '11px', color: '#9ca3af', marginBottom: '5px' }}>
                                <span>⚡ Latency: <strong>{msg.latency}s</strong></span>
                                <span>🤖 Models: <strong>Llama-3 + Cross-Encoder</strong></span>
                              </div>
                              {msg.sources.map((src, sIdx) => (
                                <div key={sIdx} className="source-item">
                                  <div className="source-item-meta">
                                    <span style={{ color: 'var(--accent-secondary)', fontWeight: 600 }}>
                                      {src.country} ({src.category})
                                    </span>
                                    <div style={{ display: 'flex', gap: '6px' }}>
                                      <span className="score-badge rerank">Rerank: {src.rerank_score.toFixed(3)}</span>
                                      <span className="score-badge dense">Dense: {src.dense_score.toFixed(3)}</span>
                                      <span className="score-badge sparse">Sparse: {src.sparse_score.toFixed(3)}</span>
                                    </div>
                                  </div>
                                  <p style={{ fontSize: '12px', color: '#d1d5db', lineHeight: '1.4' }}>
                                    {src.text}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {loading && (
              <div className="message-bubble assistant">
                <div className="avatar">🤖</div>
                <div className="message-text" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={16} className="rotate-icon" style={{ color: 'var(--accent-secondary)' }} />
                  <span>KanonesKa is retrieving compliance indexes...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <div className="input-wrapper">
              <input 
                type="text" 
                placeholder={`Ask about compliance in ${activeCountry ? activeCountry.country.split('(')[0] : 'any destination'}...`}
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                disabled={loading}
              />
              <button 
                className="send-button"
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </section>

        {/* Right Panel: Dynamic Active Country Metrics Widget */}
        {!hasSearched ? (
          <section className="sidebar-right scrollbar-custom" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', gap: '20px', padding: '30px' }}>
            <Compass size={64} style={{ color: 'var(--accent-secondary)', filter: 'drop-shadow(0 0 15px rgba(247, 147, 30, 0.25))' }} />
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 800, background: 'linear-gradient(to right, #ffffff, var(--accent-secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              TRAVEL FAR, STAY INFORMED
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '240px', lineHeight: '1.6' }}>
              Select a destination or ask a compliance question to view real-world travel safety snapshots.
            </p>
          </section>
        ) : (
          activeCountry && (
            <section className="sidebar-right scrollbar-custom">
              <div style={{ textAlign: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '15px' }}>
                <div style={{ fontSize: '36px', marginBottom: '8px' }}>✈️</div>
                <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700 }}>
                  {activeCountry.country}
                </h2>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--accent-secondary)', letterSpacing: '0.5px' }}>
                  Quick Compliance Snapshot
                </span>
              </div>

            <div className="compliance-grid">
              
              <div className="compliance-card">
                <div className="card-icon"><Droplet size={18} /></div>
                <div className="card-content">
                  <h3>Tap Water Safe</h3>
                  <p>{activeCountry.tap_water_potable ? '🟢 Potable' : '🔴 Drink Bottled Water'}</p>
                </div>
              </div>

              <div className="compliance-card">
                <div className="card-icon"><Zap size={18} /></div>
                <div className="card-content">
                  <h3>Power Outlet Info</h3>
                  <p>{activeCountry.power_plug_types} ({activeCountry.voltage_frequency})</p>
                </div>
              </div>

              <div className="compliance-card">
                <div className="card-icon"><Smartphone size={18} /></div>
                <div className="card-content">
                  <h3>Ride Hailing Apps</h3>
                  <p>{activeCountry.primary_ride_hailing_apps.split(',')[0]}</p>
                </div>
              </div>

              <div className="compliance-card">
                <div className="card-icon"><CreditCard size={18} /></div>
                <div className="card-content">
                  <h3>Payment Mechanics</h3>
                  <p>{activeCountry.local_currency_code} - {activeCountry.cash_vs_card_reliance}</p>
                </div>
              </div>

              <div className="compliance-card">
                <div className="card-icon"><AlertTriangle size={18} /></div>
                <div className="card-content">
                  <h3>Vaping Regulations</h3>
                  <p>{activeCountry.vaping_e_cigarette_legality}</p>
                </div>
              </div>

              <div className="compliance-card">
                <div className="card-icon"><UserCheck size={18} /></div>
                <div className="card-content">
                  <h3>Solo Female Safety</h3>
                  <p>{activeCountry.solo_female_safety_rating}</p>
                </div>
              </div>

            </div>

            {/* Offical Immigration Link Button */}
            <div style={{ marginTop: 'auto', paddingTop: '15px' }}>
              <a 
                href={activeCountry.official_government_travel_link}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  width: '100%',
                  padding: '12px',
                  background: 'rgba(255, 107, 53, 0.1)',
                  border: '1px solid var(--accent-primary)',
                  borderRadius: '10px',
                  color: 'white',
                  textDecoration: 'none',
                  fontSize: '13px',
                  fontWeight: 600,
                  transition: 'all 0.2s'
                }}
                className="gov-link-btn"
              >
                <span>Verify on Government Portal</span>
                <ExternalLink size={14} />
              </a>
            </div>

          </section>
          )
        )}

      </main>
    </div>
  );
}

export default App;
