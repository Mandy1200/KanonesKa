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
  X,
  Trash
} from 'lucide-react';
import './App.css';
import { supabase } from './supabaseClient';

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
  const [activeSourcesModal, setActiveSourcesModal] = useState(null);
  const [isPlanningMode, setIsPlanningMode] = useState(false);
  const [planningStep, setPlanningStep] = useState(0);
  const [tripData, setTripData] = useState({ origin: '', destination: '', profile: '', days: 0, itinerary: '', photo_url: '', flight_route: null });
  const [savedTrips, setSavedTrips] = useState([]);

  // Supabase Auth States
  const [session, setSession] = useState(null);
  const [authTab, setAuthTab] = useState('login'); // 'login' | 'signup'
  const [authEmail, setAuthEmail] = useState('');
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authSuccess, setAuthSuccess] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [isEditingUsername, setIsEditingUsername] = useState(false);
  const [tempUsername, setTempUsername] = useState('');

  // Listen to Supabase Auth State changes
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Fetch saved trips from Supabase whenever session is active
  useEffect(() => {
    if (session?.user) {
      fetchSavedTrips();
    } else {
      setSavedTrips([]);
    }
  }, [session]);

  const fetchSavedTrips = async () => {
    try {
      const { data, error } = await supabase
        .from('saved_trips')
        .select('*')
        .order('created_at', { ascending: true });
        
      if (error) {
        console.error("Error loading saved trips:", error);
      } else if (data) {
        setSavedTrips(data);
      }
    } catch (err) {
      console.error("Failed to fetch saved trips:", err);
    }
  };

  const startPlanningMode = () => {
    setIsPlanningMode(true);
    setPlanningStep(1);
    setTripData({ origin: '', destination: '', profile: '', itinerary: '', photo_url: '', flight_route: null });
    
    setMessages(prev => [...prev, {
      sender: 'assistant',
      text: '✈️ **KanonesKa Travel Planner Initiated**\n\nWhere are you starting your journey from?\n\n*Supported origins: India\'s top 100 cities (e.g. Pune, Delhi, Mumbai, Hyderabad, Ahmedabad, Bhubaneswar, Bangalore, Kolkata, Chennai)*',
      isPlanningWizard: true
    }]);
  };

  const resetPlanningMode = () => {
    setIsPlanningMode(false);
    setPlanningStep(0);
    setTripData({ origin: '', destination: '', profile: '', itinerary: '', photo_url: '', flight_route: null });
    window.location.reload();
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    setAuthSuccess('');

    if (authTab === 'login') {
      if (!authEmail || !authPassword) {
        setAuthError('Please fill in all credentials.');
        setAuthLoading(false);
        return;
      }
      const resolvedEmail = authEmail.includes('@') 
        ? authEmail.trim().toLowerCase() 
        : `${authEmail.trim().toLowerCase()}@kanoneska.local`;

      try {
        const { error } = await supabase.auth.signInWithPassword({
          email: resolvedEmail,
          password: authPassword
        });
        if (error) throw error;
      } catch (err) {
        setAuthError(err.message || 'Authentication failed.');
      } finally {
        setAuthLoading(false);
      }
    } else {
      if (!authUsername || !authEmail || !authPassword) {
        setAuthError('Please fill in Username, Email, and Password.');
        setAuthLoading(false);
        return;
      }

      try {
        const { error } = await supabase.auth.signUp({
          email: authEmail.trim().toLowerCase(),
          password: authPassword,
          options: {
            data: {
              username: authUsername.trim()
            }
          }
        });
        if (error) throw error;
        setAuthSuccess('Sign up successful! You can now switch tabs and log in.');
      } catch (err) {
        setAuthError(err.message || 'Authentication failed.');
      } finally {
        setAuthLoading(false);
      }
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    window.location.reload();
  };

  const deleteSavedTrip = async (tripId, e) => {
    e.stopPropagation();
    try {
      const { error } = await supabase
        .from('saved_trips')
        .delete()
        .eq('id', tripId);
      
      if (error) throw error;
      setSavedTrips(prev => prev.filter(t => t.id !== tripId));
    } catch (err) {
      console.error("Error deleting trip:", err);
      alert("Failed to delete trip record.");
    }
  };

  const saveCurrentTrip = async () => {
    if (!tripData.origin || !tripData.destination || !tripData.profile || !tripData.itinerary) {
      alert("Itinerary is not generated yet. Finish the steps first!");
      return;
    }

    try {
      const payload = {
        user_id: session.user.id,
        origin: tripData.origin,
        destination: tripData.destination,
        profile: tripData.profile,
        days: tripData.days || 3,
        itinerary: tripData.itinerary,
        photo_url: tripData.photo_url || '',
        flight_route: { ...tripData.flight_route, sources: tripData.sources }
      };

      const { data, error } = await supabase
        .from('saved_trips')
        .insert([payload])
        .select();

      if (error) throw error;

      setSavedTrips(prev => [...prev, data[0]]);
      
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `🎉 **Trip Saved successfully to YOUR SAVED TRIPS!**\n\nWould you like to plan another leg of your journey starting from **${tripData.destination}**? (e.g. going from ${tripData.destination} ➔ USA)`,
        isLegPrompt: true
      }]);
    } catch (err) {
      console.error("Error saving trip:", err);
      alert("Failed to save trip to cloud database: " + err.message);
    }
  };

  const startNextLeg = () => {
    const previousDest = tripData.destination;
    setTripData({
      origin: previousDest,
      destination: '',
      profile: '',
      itinerary: '',
      photo_url: '',
      flight_route: null
    });
    setPlanningStep(2);
    
    setMessages(prev => [...prev, {
      sender: 'assistant',
      text: `🗺️ **Starting Next Leg of Your Journey**\n\nStarting Location: **${previousDest}**\n\nWhat is the next destination of your journey? (e.g., USA, Singapore, London, Tokyo)`,
      isPlanningWizard: true
    }]);
  };

  const handlePlanningWizardStep = async (userInput) => {
    setLoading(true);
    try {
      if (planningStep === 1) {
        const resolvedOrigin = userInput.trim().charAt(0).toUpperCase() + userInput.trim().slice(1);
        setTripData(prev => ({ ...prev, origin: resolvedOrigin }));
        setPlanningStep(2);
        
        setMessages(prev => [...prev, {
          sender: 'assistant',
          text: `🛫 **Origin Locked: ${resolvedOrigin}**\n\nWhat is your dream destination? (e.g. Bali, Singapore, Tokyo, Sydney, London, Paris)`,
          isPlanningWizard: true
        }]);
      }
      else if (planningStep === 2) {
        const resolvedDest = userInput.trim();
        setTripData(prev => ({ ...prev, destination: resolvedDest }));
        setPlanningStep(3);
        
        setMessages(prev => [...prev, {
          sender: 'assistant',
          text: `🛬 **Destination Set: ${resolvedDest}**\n\nWho is traveling with you? Select your profile to personalize safety and activities.`,
          isPlanningWizard: true
        }]);
      }
      else if (planningStep === 4) {
        const parsedDays = parseInt(userInput.trim(), 10);
        if (isNaN(parsedDays) || parsedDays < 1 || parsedDays > 15) {
          setMessages(prev => [...prev, {
            sender: 'assistant',
            text: '⚠️ **Invalid Duration**\n\nPlease type or click a valid number of days between 1 and 15.',
            isPlanningWizard: true
          }]);
          setLoading(false);
          return;
        }
        setLoading(false);
        triggerPlanGeneration(parsedDays);
      }
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const handleWizardProfile = (profile) => {
    const updatedTripData = { ...tripData, profile: profile };
    setTripData(updatedTripData);
    setPlanningStep(4);
    
    setMessages(prev => [...prev, {
      sender: 'user',
      text: `Selected Profile: ${profile}`
    }]);

    setMessages(prev => [...prev, {
      sender: 'assistant',
      text: '📅 **How many days will your trip be?**\n\nSelect a duration below or enter a number (between 1 and 15):',
      isPlanningWizard: true
    }]);
  };

  const handleWizardDays = (days) => {
    setMessages(prev => [...prev, {
      sender: 'user',
      text: `${days} Days`
    }]);
    triggerPlanGeneration(days);
  };

  const triggerPlanGeneration = async (days) => {
    setLoading(true);
    setPlanningStep(5);

    setMessages(prev => [...prev, {
      sender: 'assistant',
      text: '🤖 *Connecting to flight router and generating safety-grounded compliance itinerary...*'
    }]);

    try {
      const response = await fetch(`${API_BASE_URL}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: tripData.origin,
          destination: tripData.destination,
          profile: tripData.profile,
          days: days
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to generate plan");
      }

      const data = await response.json();
      
      setTripData(prev => ({
        ...prev,
        days: days,
        itinerary: data.itinerary,
        photo_url: data.photo_url,
        flight_route: data.flight_route,
        latency: data.latency,
        sources: data.sources || []
      }));
      setPlanningStep(6);

      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: data.itinerary,
        sources: data.sources || [],
        latency: data.latency,
        cached: false
      }]);

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `❌ **Failed to Generate Plan**\n\nError: ${error.message}. Let's re-try the destination step.`
      }]);
      setPlanningStep(2);
    } finally {
      setLoading(false);
    }
  };

  const renderMessageText = (text) => {
    const imgRegex = /!\[(.*?)\]\((.*?)\)/;
    const match = text.match(imgRegex);
    if (match) {
      const alt = match[1];
      const url = match[2];
      const cleanText = text.replace(imgRegex, '');
      return (
        <div>
          <img 
            src={url} 
            alt={alt} 
            style={{ 
              width: '100%', 
              maxHeight: '240px', 
              objectFit: 'cover', 
              borderRadius: '8px', 
              marginBottom: '12px',
              border: '1px solid var(--border-glass)' 
            }} 
          />
          {cleanText.split('\n').map((line, idx) => (
            <span key={idx}>{line}<br /></span>
          ))}
        </div>
      );
    }
    
    return text.split('\n').map((line, idx) => (
      <span key={idx}>{line}<br /></span>
    ));
  };

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

    if (isPlanningMode) {
      handlePlanningWizardStep(queryText);
      return;
    }

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
        latency: data.latency,
        cached: data.cached
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
      {!session ? (
        <div className="auth-split-container">
          {/* Left Side: Designer Map Card */}
          <div className="auth-design-side">
            <div className="map-design-card">
              <div className="map-grid-overlay"></div>
              
              <div style={{ zIndex: 2 }}>
                <span style={{ fontSize: '32px' }}>🌏</span>
                <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '24px', fontWeight: 800, marginTop: '12px', color: 'white' }}>
                  KANONESKA
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px', lineHeight: '1.5' }}>
                  Your stateful, multi-leg travel compliance and itinerary assistant. Track visa restrictions, vaping rules, cash limits, and local safety protocols.
                </p>
              </div>

              {/* Glowing Route Map Graphic */}
              <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: '20px' }}>
                <div className="map-glow-dot one"></div>
                <div className="map-glow-dot two"></div>
                <div className="map-glow-dot three"></div>
                
                {/* SVG Connecting Paths */}
                <svg style={{ position: 'absolute', width: '100%', height: '100%' }}>
                  <path 
                    d="M 120,95 Q 260,110 395,200" 
                    fill="none" 
                    stroke="rgba(255, 107, 53, 0.4)" 
                    strokeWidth="2" 
                    strokeDasharray="6,4" 
                  />
                  <path 
                    d="M 395,200 Q 300,240 240,280" 
                    fill="none" 
                    stroke="rgba(56, 189, 248, 0.4)" 
                    strokeWidth="2" 
                    strokeDasharray="6,4" 
                  />
                </svg>
              </div>

              {/* Removed active loops text */}
            </div>
          </div>

          {/* Right Side: Credentials Card */}
          <div className="auth-form-side">
            <div className="auth-form-card">
              <div className="auth-title-block">
                <h2>{authTab === 'login' ? 'Welcome Back' : 'Get Started'}</h2>
                <p>{authTab === 'login' ? 'Sign in to access your saved travel itineraries' : 'Create an account to start planning your journeys'}</p>
              </div>

              <div className="auth-tabs">
                <button 
                  className={`auth-tab-btn ${authTab === 'login' ? 'active' : ''}`}
                  onClick={() => { setAuthTab('login'); setAuthError(''); setAuthSuccess(''); }}
                >
                  Login
                </button>
                <button 
                  className={`auth-tab-btn ${authTab === 'signup' ? 'active' : ''}`}
                  onClick={() => { setAuthTab('signup'); setAuthError(''); setAuthSuccess(''); }}
                >
                  Register
                </button>
              </div>

              <form onSubmit={handleAuth} className="auth-inputs-wrapper">
                {authTab === 'login' ? (
                  <div className="auth-input-group">
                    <label htmlFor="login-username">Username or Email</label>
                    <input 
                      type="text" 
                      id="login-username"
                      className="auth-input-field"
                      placeholder="Enter your username or email"
                      value={authEmail}
                      onChange={(e) => setAuthEmail(e.target.value)}
                      required
                    />
                  </div>
                ) : (
                  <>
                    <div className="auth-input-group">
                      <label htmlFor="signup-username">Username</label>
                      <input 
                        type="text" 
                        id="signup-username"
                        className="auth-input-field"
                        placeholder="Choose a username"
                        value={authUsername}
                        onChange={(e) => setAuthUsername(e.target.value)}
                        required
                      />
                    </div>
                    <div className="auth-input-group">
                      <label htmlFor="signup-email">Email Address</label>
                      <input 
                        type="email" 
                        id="signup-email"
                        className="auth-input-field"
                        placeholder="name@example.com"
                        value={authEmail}
                        onChange={(e) => setAuthEmail(e.target.value)}
                        required
                      />
                    </div>
                  </>
                )}

                <div className="auth-input-group">
                  <label htmlFor="password">Password</label>
                  <input 
                    type="password" 
                    id="password"
                    className="auth-input-field"
                    placeholder="••••••••"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    required
                  />
                </div>

                {authError && <div className="auth-error-msg">{authError}</div>}
                {authSuccess && <div className="auth-success-msg">{authSuccess}</div>}

                <button 
                  type="submit" 
                  className="auth-submit-btn"
                  disabled={authLoading}
                >
                  {authLoading ? 'Verifying...' : authTab === 'login' ? 'Sign In' : 'Sign Up'}
                </button>
              </form>
            </div>
          </div>
        </div>
      ) : (
        <>
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
          {session && (
            <div 
              className="user-badge-shell"
              onClick={() => {
                if (!isEditingUsername) {
                  setTempUsername(session.user.user_metadata?.username || session.user.email.split('@')[0]);
                  setIsEditingUsername(true);
                }
              }}
              style={{ 
                fontSize: '12px', 
                color: 'white', 
                marginRight: '10px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-glass)',
                padding: '6px 14px',
                borderRadius: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              title="Click to edit username"
            >
              <span>👤</span> 
              {isEditingUsername ? (
                <input 
                  type="text" 
                  value={tempUsername}
                  onChange={(e) => setTempUsername(e.target.value)}
                  onKeyDown={async (e) => {
                    if (e.key === 'Enter' && tempUsername.trim()) {
                      const newUsername = tempUsername.trim();
                      const { data, error } = await supabase.auth.updateUser({
                        data: { username: newUsername }
                      });
                      if (!error) {
                        setSession(prev => ({
                          ...prev,
                          user: {
                            ...prev.user,
                            user_metadata: {
                              ...prev.user.user_metadata,
                              username: newUsername
                            }
                          }
                        }));
                      } else {
                        console.error("Failed to update username in Supabase:", error);
                      }
                      setIsEditingUsername(false);
                    } else if (e.key === 'Escape') {
                      setIsEditingUsername(false);
                    }
                  }}
                  onBlur={() => setIsEditingUsername(false)}
                  autoFocus
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'white',
                    outline: 'none',
                    fontSize: '12px',
                    width: '100px',
                    fontWeight: 600
                  }}
                />
              ) : (
                <span>{session.user.user_metadata?.username || session.user.email.split('@')[0]}</span>
              )}
            </div>
          )}
          
          {!isPlanningMode ? (
            <button 
              className="plan-trip-btn"
              onClick={startPlanningMode}
              style={{
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                border: 'none',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '13px',
                fontWeight: 800,
                cursor: 'pointer',
                boxShadow: '0 0 15px rgba(255, 107, 53, 0.4)',
                transition: 'all 0.2s',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}
            >
              🚀 PLAN A TRIP
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                className="plan-save-btn"
                onClick={saveCurrentTrip}
                disabled={planningStep < 6 || loading}
                style={{
                  background: 'var(--accent-emerald)',
                  border: 'none',
                  color: 'white',
                  padding: '8px 16px',
                  borderRadius: '20px',
                  fontSize: '13px',
                  fontWeight: 800,
                  cursor: 'pointer',
                  opacity: (planningStep < 6 || loading) ? 0.5 : 1
                }}
              >
                💾 Save
              </button>
              <button 
                className="plan-delete-btn"
                onClick={resetPlanningMode}
                style={{
                  background: '#ef4444',
                  border: 'none',
                  color: 'white',
                  padding: '8px 16px',
                  borderRadius: '20px',
                  fontSize: '13px',
                  fontWeight: 800,
                  cursor: 'pointer'
                }}
              >
                🗑️ Delete
              </button>
            </div>
          )}

          {session && (
            <button 
              className="logout-nav-btn"
              onClick={handleLogout}
              style={{
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                border: 'none',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '13px',
                fontWeight: 800,
                cursor: 'pointer',
                boxShadow: '0 0 15px rgba(255, 107, 53, 0.4)',
                transition: 'all 0.2s',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginLeft: '10px'
              }}
            >
              Logout
            </button>
          )}
        </div>
      </header>

      {/* Main Grid */}
      <main className="dashboard">
        
        {/* Left Panel: 55 Countries Selector OR Saved Trips list */}
        <section className="sidebar-left">
          {!isPlanningMode ? (
            <>
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
            </>
          ) : (
            <>
              <h2 className="section-title">
                <Globe size={16} /> Your Saved Trips ({savedTrips.length})
              </h2>
              <div className="saved-trips-list scrollbar-custom" style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '10px' }}>
                {savedTrips.length === 0 ? (
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '40px', padding: '0 10px', lineHeight: '1.5' }}>
                    No saved trips yet. Click Plan a Trip above and save your route.
                  </div>
                ) : (
                  savedTrips.map((trip, tIdx) => (
                    <div 
                      key={tIdx} 
                      className="saved-trip-item" 
                      style={{
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: '1px solid var(--border-glass)',
                        borderRadius: '10px',
                        padding: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      onClick={() => {
                        const msg = {
                          sender: 'assistant',
                          text: trip.itinerary,
                          sources: trip.flight_route.sources || [],
                          latency: trip.latency,
                          cached: false
                        };
                        setMessages(prev => [...prev, msg]);
                        setHasSearched(true);
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px', color: 'var(--accent-secondary)', fontWeight: 'bold', marginBottom: '4px' }}>
                        <span>{trip.profile} ({trip.days} Days)</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span>INR {trip.flight_route.total_price.toLocaleString()}</span>
                          <button 
                            className="saved-trip-delete-btn"
                            onClick={(e) => deleteSavedTrip(trip.id, e)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: 'var(--text-secondary)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              padding: '2px'
                            }}
                          >
                            <Trash size={11} style={{ color: '#ef4444' }} />
                          </button>
                        </div>
                      </div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: 'white' }}>
                        {trip.origin} ➔ {trip.destination}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Layovers: {trip.flight_route.layovers} | {trip.flight_route.total_duration}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
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
                      <div style={{ whiteSpace: 'normal', lineHeight: '1.6' }}>
                        {renderMessageText(msg.text)}
                      </div>
                      
                      {msg.isPlanningWizard && planningStep === 3 && (
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '12px' }}>
                          {['Solo Female', 'Family', 'Couple', 'Duo'].map((prof) => (
                            <button
                              key={prof}
                              onClick={() => handleWizardProfile(prof)}
                              style={{
                                background: 'rgba(255, 107, 53, 0.1)',
                                border: '1px solid var(--accent-primary)',
                                color: 'white',
                                borderRadius: '20px',
                                padding: '6px 14px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                fontWeight: 600,
                                transition: 'all 0.2s'
                              }}
                              className="profile-btn"
                            >
                              {prof}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {msg.isPlanningWizard && planningStep === 4 && (
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '12px' }}>
                          {[3, 5, 7, 10].map((num) => (
                            <button
                              key={num}
                              onClick={() => handleWizardDays(num)}
                              style={{
                                background: 'rgba(56, 189, 248, 0.1)',
                                border: '1px solid #38bdf8',
                                color: 'white',
                                borderRadius: '20px',
                                padding: '6px 14px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                fontWeight: 600,
                                transition: 'all 0.2s'
                              }}
                              className="days-btn"
                            >
                              {num} Days
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {msg.isLegPrompt && (
                        <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                          <button
                            onClick={startNextLeg}
                            style={{
                              background: 'var(--accent-emerald)',
                              border: 'none',
                              color: 'white',
                              borderRadius: '8px',
                              padding: '8px 16px',
                              fontSize: '12px',
                              cursor: 'pointer',
                              fontWeight: 600
                            }}
                          >
                            Yes, plan next leg!
                          </button>
                          <button
                            onClick={resetPlanningMode}
                            style={{
                              background: 'rgba(255, 255, 255, 0.1)',
                              border: '1px solid var(--border-glass)',
                              color: 'white',
                              borderRadius: '8px',
                              padding: '8px 16px',
                              fontSize: '12px',
                              cursor: 'pointer',
                              fontWeight: 600
                            }}
                          >
                            No thanks, reset!
                          </button>
                        </div>
                      )}
                      
                      {/* Sources Trigger (Only for assistant response) */}
                      {msg.sender === 'assistant' && msg.sources && msg.sources.length > 0 && (
                        <div className="source-accordion">
                          <div 
                            className="accordion-header" 
                            style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                            onClick={() => setActiveSourcesModal({
                              sources: msg.sources,
                              latency: msg.latency,
                              cached: msg.cached
                            })}
                          >
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <Compass size={12} /> View Retrieved Compliance Sources ({msg.sources.length})
                            </span>
                            <ExternalLink size={12} style={{ opacity: 0.7 }} />
                          </div>
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
                placeholder={
                  isPlanningMode
                    ? (planningStep === 1 
                        ? "Enter starting city (e.g. Bhubaneswar)..." 
                        : planningStep === 2 
                        ? "Enter dream destination (e.g. Bali)..." 
                        : planningStep === 3
                        ? "Select profile above..."
                        : "Enter number of days (e.g. 5)...")
                    : `Ask about compliance in ${activeCountry ? activeCountry.country.split('(')[0] : 'any destination'}...`
                }
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                disabled={loading || (isPlanningMode && planningStep === 3)}
              />
              <button 
                className="send-button"
                onClick={() => handleSend()}
                disabled={loading || !input.trim() || (isPlanningMode && planningStep === 3)}
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

      {/* Fullscreen Compliance Sources Modal */}
      {activeSourcesModal && (
        <div 
          className="sources-modal-overlay" 
          onClick={() => setActiveSourcesModal(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
          }}
        >
          <div 
            className="sources-modal-content" 
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'rgba(23, 23, 37, 0.95)',
              border: '1px solid var(--border-glass)',
              borderRadius: '16px',
              width: '90%',
              maxWidth: '1200px',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              padding: '24px',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
              color: 'white',
              overflow: 'hidden'
            }}
          >
            <header 
              className="modal-header"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid var(--border-glass)',
                paddingBottom: '16px',
                marginBottom: '16px'
              }}
            >
              <h3 style={{ fontSize: '18px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                <Compass size={20} style={{ color: 'var(--accent-secondary)' }} />
                Retrieved Compliance Sources ({activeSourcesModal.sources.length})
              </h3>
              <button 
                className="close-modal-btn" 
                onClick={() => setActiveSourcesModal(null)}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: 'none',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
              >
                <X size={18} />
              </button>
            </header>

            <div 
              className="modal-meta-row"
              style={{
                display: 'flex',
                gap: '15px',
                fontSize: '11px',
                color: '#9ca3af',
                marginBottom: '16px',
                alignItems: 'center'
              }}
            >
              <span>⚡ Latency: <strong>{activeSourcesModal.latency}s</strong></span>
              {activeSourcesModal.cached && (
                <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent-emerald)', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>
                  ⚡ SEMANTIC CACHE HIT
                </span>
              )}
              <span>🤖 Model Pipeline: <strong>Llama-3 + Cross-Encoder Reranker</strong></span>
            </div>

            <div 
              className="modal-sources-grid"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '20px',
                overflowY: 'auto',
                paddingRight: '4px',
                flex: 1
              }}
            >
              {activeSourcesModal.sources.map((src, sIdx) => (
                <div 
                  key={sIdx} 
                  className="modal-source-card"
                  style={{
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    overflowY: 'auto'
                  }}
                >
                  <div 
                    className="card-meta"
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <span style={{ color: 'var(--accent-secondary)', fontWeight: 700, fontSize: '13px' }}>
                      {src.country}
                    </span>
                    <span style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', color: '#9ca3af' }}>
                      {src.category}
                    </span>
                  </div>

                  <div 
                    className="card-scores"
                    style={{
                      display: 'flex',
                      gap: '4px',
                      flexWrap: 'wrap'
                    }}
                  >
                    <span className="score-badge rerank" style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(247, 147, 30, 0.1)', color: 'var(--accent-secondary)' }}>
                      Rerank: {src.rerank_score.toFixed(3)}
                    </span>
                    <span className="score-badge dense" style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8' }}>
                      Dense: {src.dense_score.toFixed(3)}
                    </span>
                    <span className="score-badge sparse" style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(168, 85, 247, 0.1)', color: '#a855f7' }}>
                      Sparse: {src.sparse_score.toFixed(3)}
                    </span>
                  </div>

                  <p 
                    className="card-text"
                    style={{
                      fontSize: '12px',
                      color: '#d1d5db',
                      lineHeight: '1.5',
                      margin: 0
                    }}
                  >
                    {src.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      </>)}
    </div>
  );
}

export default App;
