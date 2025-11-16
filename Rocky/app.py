from flask import Flask, jsonify, request
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
    
    Args:
        gate_name (str): Name of the gate (payu1euro, payu1pln, payu1)
    
    Returns:
        JSON response with payment status
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

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "available_gates": list(GATE_MODULES.keys())
    })

@app.route('/')
def index():
    """Root endpoint with API information"""
    return jsonify({
        "message": "Payment Gateway API",
        "version": "1.0.0",
        "endpoints": {
            "payment": "/rocky/gate/{gate}/cc={card_details}",
            "health": "/health"
        },
        "available_gates": {
            "payu1euro": "PayU Euro (0.10 EUR)",
            "payu1pln": "PayU PLN (1.00 PLN)",
            "payu1": "PayU USD ($1.00)"
        },
        "example": "https://cxchk.site/rocky/gate/payu1euro/cc=4111111111111111|12|25|123"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)