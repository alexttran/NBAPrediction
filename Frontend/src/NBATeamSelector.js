import React, { useState } from 'react';
import './NBATeamSelector.css';

const NBATeamSelector = () => {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [homeSearch, setHomeSearch] = useState('');
  const [awaySearch, setAwaySearch] = useState('');
  const [winner, setWinner] = useState('');
  const [homeDropdownOpen, setHomeDropdownOpen] = useState(false);
  const [awayDropdownOpen, setAwayDropdownOpen] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const nbaTeams = [
    'Atlanta Hawks (ATL)',
    'Boston Celtics (BOS)',
    'Brooklyn Nets (BRK)',
    'Charlotte Hornets (CHO)',
    'Chicago Bulls (CHI)',
    'Cleveland Cavaliers (CLE)',
    'Dallas Mavericks (DAL)',
    'Denver Nuggets (DEN)',
    'Detroit Pistons (DET)',
    'Golden State Warriors (GSW)',
    'Houston Rockets (HOU)',
    'Indiana Pacers (IND)',
    'LA Clippers (LAC)',
    'Los Angeles Lakers (LAL)',
    'Memphis Grizzlies (MEM)',
    'Miami Heat (MIA)',
    'Milwaukee Bucks (MIL)',
    'Minnesota Timberwolves (MIN)',
    'New Orleans Pelicans (NOP)',
    'New York Knicks (NYK)',
    'Oklahoma City Thunder (OKC)',
    'Orlando Magic (ORL)',
    'Philadelphia 76ers (PHI)',
    'Phoenix Suns (PHO)',
    'Portland Trail Blazers (POR)',
    'Sacramento Kings (SAC)',
    'San Antonio Spurs (SAS)',
    'Toronto Raptors (TOR)',
    'Utah Jazz (UTA)',
    'Washington Wizards (WAS)'
  ];

  const handleReset = () => {
    setHomeTeam('');
    setAwayTeam('');
    setHomeSearch('');
    setAwaySearch('');
    setHomeDropdownOpen(false);
    setAwayDropdownOpen(false);
  };

  const handlePredict = async () => {

    const result = await predictWinner()
    //setWinner(result)
  }

  const filterTeams = (searchTerm) => {
    return nbaTeams.filter(team => 
      team.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const handleAwayTeamSelect = (team) => {
    setAwayTeam(team.slice(-4, -1));
    setAwaySearch(team);
    setAwayDropdownOpen(false);
  };

  const handleHomeTeamSelect = (team) => {
    setHomeTeam(team.slice(-4, -1));
    setHomeSearch(team);
    setHomeDropdownOpen(false);
  };

  const handleAwaySearchChange = (e) => {
    setAwaySearch(e.target.value);
    setAwayDropdownOpen(true);
    if (e.target.value === '') {
      setAwayTeam('');
    }
  };

  const handleHomeSearchChange = (e) => {
    setHomeSearch(e.target.value);
    setHomeDropdownOpen(true);
    if (e.target.value === '') {
      setHomeTeam('');
    }
  };

  const predictWinner = async () => {
    if (!homeTeam || !awayTeam) {
      setError('Please select both home and away teams');
      return;
    }

    if (homeTeam === awayTeam) {
      setError('Please select different teams');
      return;
    }

    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const response = await fetch('http://localhost:5001/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team1: awayTeam,
          team2: homeTeam
        }),
      });

      const data = await response.json();
      setWinner(JSON.stringify(data).slice(21,24));

      if (response.ok && data.success) {
        setWinner(JSON.stringify(data).slice(21,24));
      } else {
        //setError(data.error || 'Prediction failed');
      }
    } catch (err) {
      //setError('Failed to connect to prediction service. Make sure the Flask API is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-container">
      <div className="content-card">
        <h1 className="title">
          NBA Matchup
        </h1>
        
        <div className="form-container">
          {/* Away Team Dropdown */}
          <div className="input-group">
            <label className="input-label">
              Away Team
            </label>
            <div className="dropdown-container">
              <input
                type="text"
                value={awaySearch}
                onChange={handleAwaySearchChange}
                onFocus={() => setAwayDropdownOpen(true)}
                placeholder="Search or select away team"
                className="team-input"
              />
              {awayDropdownOpen && (
                <div className="dropdown-menu">
                  {filterTeams(awaySearch).map((team) => (
                    <div
                      key={team}
                      onClick={() => handleAwayTeamSelect(team)}
                      className="dropdown-item"
                    >
                      {team}
                    </div>
                  ))}
                  {filterTeams(awaySearch).length === 0 && (
                    <div className="no-results">No teams found</div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* VS Divider */}
          <div className="vs-container">
            <div className="vs-badge">
              VS
            </div>
          </div>

          {/* Home Team Dropdown */}
          <div className="input-group">
            <label className="input-label">
              Home Team
            </label>
            <div className="dropdown-container">
              <input
                type="text"
                value={homeSearch}
                onChange={handleHomeSearchChange}
                onFocus={() => setHomeDropdownOpen(true)}
                placeholder="Search or select home team"
                className="team-input"
              />
              {homeDropdownOpen && (
                <div className="dropdown-menu">
                  {filterTeams(homeSearch).map((team) => (
                    <div
                      key={team}
                      onClick={() => handleHomeTeamSelect(team)}
                      className="dropdown-item"
                    >
                      {team}
                    </div>
                  ))}
                  {filterTeams(homeSearch).length === 0 && (
                    <div className="no-results">No teams found</div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Display Selected Teams */}
          {(homeTeam || awayTeam) && (
            <div className="matchup-display">
              <h3 className="matchup-title">Selected Matchup</h3>
              <div className="matchup-teams">
                <div className="team-name">
                  {awayTeam || 'No away team selected'}
                </div>
                <div className="at-symbol">@</div>
                <div className="team-name">
                  {homeTeam || 'No home team selected'}
                </div>
              </div>
            </div>
          )}

          {/* Reset Button */}
          {(homeTeam || awayTeam) && (
            <button
              onClick={handleReset}
              className="reset-button"
            >
              Reset Selection
            </button>
          )}
          {(homeTeam && awayTeam) && (
            <button
              onClick={predictWinner}
              className="reset-button"
            >
              Predict Winner
            </button>
          )}
          <h2> Winner: {winner}!</h2>
        </div>
      </div>
    </div>
  );
};

export default NBATeamSelector;