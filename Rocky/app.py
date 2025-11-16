from flask import Flask, jsonify, request, render_template_string
from urllib.parse import unquote
import importlib
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Add GATE directory to Python path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
gate_dir = os.path.join(current_dir, 'GATE')
sys.path.insert(0, gate_dir)

# Dictionary mapping gate names to their corresponding modules
GATE_MODULES = {
    'payu1euro': 'payu1euro',
    'payu1pln': 'payu1pln',
    'payu1': 'payu1',
}

@app.route('/rocky/gate/<gate_name>/cc=')
def process_gate(gate_name):
    """
    Process payment request for specified gate
    """
    try:
        # Check if the gate exists
        if gate_name not in GATE_MODULES:
            logger.error(f"Unknown gate: {gate_name}")
            return jsonify({
                "value": "Invalid gate specified.",
                "status": "declined"
            }), 400
        
        # Get card details from the query string
        card_details = request.query_string.decode('utf-8')
        
        # URL decode the card details
        card_details = unquote(card_details)
        
        # Validate that card details are provided
        if not card_details:
            logger.error("No card details provided")
            return jsonify({
                "value": "Card details are required.",
                "status": "declined"
            }), 400
        
        # Log the request (without sensitive data)
        logger.info(f"Processing payment via gate: {gate_name}")
        
        # Import the appropriate module
        module_name = GATE_MODULES[gate_name]
        try:
            gate_module = importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {str(e)}")
            return jsonify({
                "value": "Gate module not available.",
                "status": "declined"
            }), 500
        
        # Call the process_payment function from the imported module
        try:
            result = gate_module.process_payment(card_details)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error processing payment with {module_name}: {str(e)}")
            return jsonify({
                "value": "Payment processing failed.",
                "status": "declined"
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "value": "Internal server error.",
            "status": "declined"
        }), 500

@app.route('/')
def index():
    """Root endpoint showing a simple HTML page"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Success</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            text-align: center;
            padding: 0;
            margin: 0;
            background: linear-gradient(to bottom right, #1a2a6c, #b21f1f, #1a2a6c);
            color: #fff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        .success-container {
            position: relative;
            z-index: 2;
            padding: 40px;
            max-width: 800px;
        }
        h1 {
            font-size: 56px;
            margin-bottom: 30px;
            font-weight: 700;
            letter-spacing: -1px;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            animation: fadeInUp 1s ease-out;
        }
        .message {
            font-size: 26px;
            line-height: 1.5;
            margin-bottom: 40px;
            opacity: 0.9;
            animation: fadeInUp 1.2s ease-out;
        }
        .checkmark {
            width: 120px;
            height: 120px;
            margin: 0 auto 40px;
            position: relative;
            animation: scaleIn 0.8s ease-out;
        }
        .checkmark-circle {
            stroke-dasharray: 166;
            stroke-dashoffset: 166;
            stroke-width: 2;
            stroke-miterlimit: 10;
            stroke: #fff;
            fill: none;
            animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
        }
        .checkmark-check {
            transform-origin: 50% 50%;
            stroke-dasharray: 48;
            stroke-dashoffset: 48;
            stroke-width: 3;
            stroke: #fff;
            fill: none;
            animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
        }
        .particles {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 1;
        }
        .particle {
            position: absolute;
            display: block;
            pointer-events: none;
            opacity: 0;
        }
        .particle:nth-child(1) {
            top: 20%;
            left: 20%;
            font-size: 20px;
            animation: float 15s infinite;
        }
        .particle:nth-child(2) {
            top: 80%;
            left: 80%;
            font-size: 24px;
            animation: float 12s infinite;
        }
        .particle:nth-child(3) {
            top: 40%;
            left: 40%;
            font-size: 16px;
            animation: float 18s infinite;
        }
        .particle:nth-child(4) {
            top: 60%;
            left: 10%;
            font-size: 22px;
            animation: float 14s infinite;
        }
        .particle:nth-child(5) {
            top: 30%;
            left: 70%;
            font-size: 18px;
            animation: float 16s infinite;
        }
        @keyframes float {
            0% {
                transform: translateY(0) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) rotate(720deg);
                opacity: 0;
            }
        }
        @keyframes stroke {
            100% {
                stroke-dashoffset: 0;
            }
        }
        @keyframes scaleIn {
            0% {
                transform: scale(0);
                opacity: 0;
            }
            100% {
                transform: scale(1);
                opacity: 1;
            }
        }
        @keyframes fadeInUp {
            0% {
                transform: translateY(30px);
                opacity: 0;
            }
            100% {
                transform: translateY(0);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="particles">
        <span class="particle">✦</span>
        <span class="particle">✧</span>
        <span class="particle">✦</span>
        <span class="particle">✧</span>
        <span class="particle">✦</span>
    </div>
    
    <div class="success-container">
        <div class="checkmark">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
        </div>
        <h1>Web Page Created Successfully</h1>
    </div>
</body>
</html>
    """
    return render_template_string(html_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
