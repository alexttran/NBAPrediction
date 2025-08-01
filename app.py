from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import os
import sys
from datetime import datetime

app = Flask(__name__)

# Configure CORS with specific settings for better security
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# Global variables for model and data
model = None
full_df = None
predictors = None

def load_model_files():
    """Load model and data files with better error handling"""
    global model, full_df, predictors
    
    try:
        # Check if files exist before loading
        required_files = ['nba_model.joblib', 'nba_dataframe.joblib', 'nba_predictors.joblib']
        missing_files = []
        
        for file_name in required_files:
            if not os.path.exists(file_name):
                missing_files.append(file_name)
        
        if missing_files:
            print(f"ERROR: Missing required files: {missing_files}")
            print("Please ensure all model files are in the same directory as this script.")
            return False
        
        # Load the files
        print("Loading model files...")
        model = joblib.load('nba_model.joblib')
        full_df = joblib.load('nba_dataframe.joblib')
        predictors = joblib.load('nba_predictors.joblib')
        
        print(f"✓ Model loaded successfully!")
        print(f"✓ DataFrame loaded with {len(full_df)} records")
        print(f"✓ Predictors loaded: {len(predictors)} features")
        
        # Validate data structure
        if full_df is not None:
            required_columns = ['team_x', 'team_y', 'date_next']
            missing_columns = [col for col in required_columns if col not in full_df.columns]
            if missing_columns:
                print(f"WARNING: Missing required columns in DataFrame: {missing_columns}")
                return False
                
        return True
        
    except Exception as e:
        print(f"ERROR loading model files: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in directory: {os.listdir('.')}")
        return False

def predict_winner(team1, team2, model, full_df, predictors):
    """
    Predict winner between two teams with improved error handling
    """
    try:
        # Normalize team names (remove extra spaces, handle case variations)
        team1 = team1.strip()
        team2 = team2.strip()
        
        print(f"Predicting winner between: '{team1}' vs '{team2}'")
        
        # Try both combinations since the order might matter
        matchup1 = full_df[(full_df["team_x"] == team1) & (full_df["team_y"] == team2)]
        matchup2 = full_df[(full_df["team_x"] == team2) & (full_df["team_y"] == team1)]
        
        if not matchup1.empty:
            matchup = matchup1.sort_values("date_next").iloc[-1]
            prediction_for_team1 = True
        elif not matchup2.empty:
            matchup = matchup2.sort_values("date_next").iloc[-1]
            prediction_for_team1 = False
        else:
            # If no exact match found, try to find similar team names
            available_teams = list(set(full_df["team_x"].unique()) | set(full_df["team_y"].unique()))
            print(f"Available teams in dataset: {sorted(available_teams)}")
            raise ValueError(f"No matchup data found between '{team1}' and '{team2}'. Available teams: {sorted(available_teams)}")
        
        # Check if all required predictors are available
        missing_predictors = [p for p in predictors if p not in matchup.index]
        if missing_predictors:
            raise ValueError(f"Missing predictor columns: {missing_predictors}")
        
        # Prepare features for prediction
        X = matchup[predictors].values.reshape(1, -1)
        
        # Check for NaN values
        if pd.isna(X).any():
            print("WARNING: NaN values found in features, filling with 0")
            X = pd.DataFrame(X).fillna(0).values
        
        # Make prediction
        pred = model.predict(X)[0]
        
        # Interpret prediction based on which team combination we used
        if prediction_for_team1:
            winner = team1 if pred == 1 else team2
        else:
            winner = team2 if pred == 1 else team1
            
        print(f"Prediction result: {winner}")
        return jsonify(winner)
        
    except Exception as e:
        print(f"Error in predict_winner: {str(e)}")
        raise

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    """Predict winner endpoint with comprehensive error handling"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Check if model is loaded
        if model is None or full_df is None or predictors is None:
            return jsonify({
                'success': False,
                'error': 'Model or data not loaded properly. Please check server logs.'
            }), 500
        
        # Get and validate request data
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
            
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        if 'team1' not in data or 'team2' not in data:
            return jsonify({
                'success': False,
                'error': 'Please provide both team1 and team2'
            }), 400
        
        team1 = data['team1']
        team2 = data['team2']
        
        # Validate team names
        if not team1 or not team2:
            return jsonify({
                'success': False,
                'error': 'Team names cannot be empty'
            }), 400
            
        if team1 == team2:
            return jsonify({
                'success': False,
                'error': 'Cannot predict winner when both teams are the same'
            }), 400
        
        # Make prediction
        winner = predict_winner(team1, team2, model, full_df, predictors)
        
        return jsonify({
            'success': True,
            'team1': team1,
            'team2': team2,
            'predicted_winner': winner,
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        print(f"Unexpected error in predict endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Prediction failed: {str(e)}'
        }), 500

@app.route('/teams', methods=['GET'])
def get_teams():
    """Get available teams endpoint"""
    try:
        if full_df is None:
            return jsonify({
                'success': False,
                'error': 'Data not loaded'
            }), 500
        
        # Get unique teams from both columns
        teams_x = set(full_df['team_x'].unique())
        teams_y = set(full_df['team_y'].unique())
        all_teams = sorted(list(teams_x.union(teams_y)))
        
        # Remove any NaN values
        all_teams = [team for team in all_teams if pd.notna(team)]
        
        return jsonify({
            'success': True,
            'teams': all_teams,
            'count': len(all_teams)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'data_loaded': full_df is not None,
        'predictors_loaded': predictors is not None,
        'timestamp': datetime.now().isoformat(),
        'data_records': len(full_df) if full_df is not None else 0
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API info"""
    return jsonify({
        'message': 'NBA Prediction API',
        'version': '1.0',
        'endpoints': {
            '/health': 'GET - Health check',
            '/teams': 'GET - Get available teams',
            '/predict': 'POST - Predict winner (requires team1 and team2)'
        },
        'status': 'running'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("NBA Prediction API Starting...")
    print("=" * 50)
    
    # Load model files on startup
    if not load_model_files():
        print("CRITICAL ERROR: Failed to load required model files!")
        print("Please ensure the following files are in the same directory:")
        print("- nba_model.joblib")
        print("- nba_dataframe.joblib") 
        print("- nba_predictors.joblib")
        sys.exit(1)
    
    print("=" * 50)
    print("🏀 NBA Prediction API Ready!")
    print("API will be available at: http://localhost:5000")
    print("Health check: http://localhost:5000/health")
    print("Available teams: http://localhost:5000/teams")
    print("=" * 50)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5001)