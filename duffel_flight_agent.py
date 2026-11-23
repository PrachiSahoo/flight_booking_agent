import os
import sys
import json
import requests

# =====================================================================
# API CONFIGURATION & CREDENTIAL MANAGEMENT
# =====================================================================

DUFFEL_TOKEN = os.environ.get("DUFFEL_ACCESS_TOKEN", "")
DUFFEL_API_BASE = "https://api.duffel.com"
DUFFEL_HEADERS = {
    "Authorization": f"Bearer {DUFFEL_TOKEN}",
    "Duffel-Version": "v2",
    "Content-Type": "application/json"
}

# Active Supported Tool-Calling Models on Groq
GROQ_MODELS = [
    os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

# Common City / Airport Name to 3-Letter IATA Mapping for Duffel API
IATA_CODES = {
    "NEW YORK": "JFK", "NYC": "JFK", "NEW YORK CITY": "JFK", "JFK": "JFK", "EWR": "EWR", "LGA": "LGA",
    "TORONTO": "YYZ", "YYZ": "YYZ", "YTO": "YYZ", "BILLY BISHOP": "YTZ", "YTZ": "YTZ",
    "DELHI": "DEL", "NEW DELHI": "DEL", "DEL": "DEL", "IGIA": "DEL",
    "MUMBAI": "BOM", "BOMBAY": "BOM", "BOM": "BOM",
    "BANGALORE": "BLR", "BENGALURU": "BLR", "BLR": "BLR",
    "LONDON": "LHR", "LHR": "LHR", "LGW": "LGW", "LON": "LHR", "HEATHROW": "LHR", "GATWICK": "LGW",
    "PARIS": "CDG", "CDG": "CDG", "ORY": "ORY", "PAR": "CDG",
    "DUBAI": "DXB", "DXB": "DXB",
    "SINGAPORE": "SIN", "SIN": "SIN",
    "TOKYO": "HND", "HND": "HND", "NRT": "NRT", "TYO": "HND", "HANEDA": "HND", "NARITA": "NRT",
    "SAN FRANCISCO": "SFO", "SFO": "SFO",
    "LOS ANGELES": "LAX", "LAX": "LAX",
    "CHICAGO": "ORD", "ORD": "ORD", "OHARE": "ORD",
    "SYDNEY": "SYD", "SYD": "SYD",
    "FRANKFURT": "FRA", "FRA": "FRA",
    "AMSTERDAM": "AMS", "AMS": "AMS",
    "CHENNAI": "MAA", "MAA": "MAA", "MADRAS": "MAA",
    "KOLKATA": "CCU", "CCU": "CCU", "CALCUTTA": "CCU",
    "HYDERABAD": "HYD", "HYD": "HYD",
    "GOA": "GOI", "GOI": "GOI", "GOX": "GOX",
    "PUNE": "PNQ", "PNQ": "PNQ",
    "AHMEDABAD": "AMD", "AMD": "AMD",
    "JAIPUR": "JAI", "JAI": "JAI",
    "KOCHI": "COK", "COCHIN": "COK", "COK": "COK",
    "BOSTON": "BOS", "BOS": "BOS",
    "SEATTLE": "SEA", "SEA": "SEA",
    "MIAMI": "MIA", "MIA": "MIA",
    "VANCOUVER": "YVR", "YVR": "YVR",
    "MONTREAL": "YUL", "YUL": "YUL",
    "DALLAS": "DFW", "DFW": "DFW",
    "ATLANTA": "ATL", "ATL": "ATL",
    "HOUSTON": "IAH", "IAH": "IAH",
    "BERLIN": "BER", "BER": "BER",
    "ROME": "FCO", "FCO": "FCO",
    "MADRID": "MAD", "MAD": "MAD",
    "BARCELONA": "BCN", "BCN": "BCN",
    "ZURICH": "ZRH", "ZRH": "ZRH",
    "BANGKOK": "BKK", "BKK": "BKK",
    "HONG KONG": "HKG", "HKG": "HKG",
    "SEOUL": "ICN", "ICN": "ICN",
    "DOHA": "DOH", "DOH": "DOH",
    "ABU DHABI": "AUH", "AUH": "AUH",
    "MELBOURNE": "MEL", "MEL": "MEL"
}

def resolve_iata(code_or_city: str) -> str:
    """Intelligently map city names or airport strings to 3-letter IATA codes."""
    if not code_or_city:
        return ""
    cleaned = str(code_or_city).strip().upper()
    if cleaned in IATA_CODES:
        return IATA_CODES[cleaned]
    for city, code in IATA_CODES.items():
        if city in cleaned or cleaned in city:
            return code
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned
    return cleaned


def extract_duffel_error(resp_or_exc) -> str:
    """Extract a clean, human-readable error string from Duffel API responses."""
    if hasattr(resp_or_exc, "json"):
        try:
            data = resp_or_exc.json()
            errors = data.get("errors", [])
            if errors and isinstance(errors, list):
                messages = []
                for err in errors:
                    msg = err.get("message") or err.get("title") or str(err)
                    messages.append(msg)
                return "; ".join(messages)
        except Exception:
            pass
        if hasattr(resp_or_exc, "text") and resp_or_exc.text:
            return resp_or_exc.text
    return str(resp_or_exc)


# =====================================================================
# DUFFEL TOOLS
# =====================================================================

def search_flights(origin: str = "", destination: str = "", origin_iata: str = "", destination_iata: str = "", date: str = "", departure_date: str = "", num_passengers: int = 1, passengers: int = 1, **kwargs) -> str:
    """Search real flights using Duffel API."""
    if not DUFFEL_TOKEN:
        return "Error: DUFFEL_ACCESS_TOKEN not set."
    
    orig_raw = origin_iata or origin or ""
    dest_raw = destination_iata or destination or ""
    orig = resolve_iata(orig_raw)
    dest = resolve_iata(dest_raw)
    dept_date = (date or departure_date or "").strip()
    p_count = max(1, num_passengers or passengers or 1)
    
    if not orig or not dest or not dept_date:
        return f"Error: Missing search parameters (origin='{orig_raw}', destination='{dest_raw}', date='{dept_date}')."
    
    payload = {
        "data": {
            "slices": [{"origin": orig, "destination": dest, "departure_date": dept_date}],
            "passengers": [{"type": "adult"} for _ in range(p_count)],
            "return_offers": True
        }
    }
    
    try:
        response = requests.post(f"{DUFFEL_API_BASE}/air/offer_requests", headers=DUFFEL_HEADERS, json=payload, timeout=30)
        if not response.ok:
            return f"Duffel API Notice: {extract_duffel_error(response)}"
            
        offers = response.json().get("data", {}).get("offers", [])
        if not offers:
            return f"No flights found from {orig} ({orig_raw}) to {dest} ({dest_raw}) on {dept_date} for {p_count} passenger(s)."
            
        res = [f"Found {len(offers)} flight offer(s) from {orig} to {dest} on {dept_date} for {p_count} passenger(s):"]
        for idx, offer in enumerate(offers[:5], 1):
            slices = offer.get("slices", [])
            if not slices: continue
            segments = slices[0].get("segments", [])
            if not segments: continue
            flight = segments[0]
            airline = (flight.get("operating_carrier") or flight.get("marketing_carrier") or {}).get("name", "Airline")
            flight_num = flight.get("operating_carrier_flight_number") or flight.get("marketing_carrier_flight_number", "")
            dep = flight.get("departing_at", "N/A").replace("T", " ")
            arr = flight.get("arriving_at", "N/A").replace("T", " ")
            total = offer.get("total_amount", "N/A")
            curr = offer.get("total_currency", "")
            res.append(f"{idx}. Offer ID: {offer['id']} | {airline} {flight_num} | Dep: {dep} - Arr: {arr} | Price: {total} {curr}")
        return "\n".join(res)
    except Exception as e:
        return f"Duffel API Error: {str(e)}"


def get_flight_details(offer_id: str = "", flight_id: str = "", **kwargs) -> str:
    """Return full details for a single flight given its Duffel offer_id."""
    if not DUFFEL_TOKEN: return "Error: DUFFEL_ACCESS_TOKEN not set."
    target_id = (offer_id or flight_id or "").strip()
    if not target_id: return "Error: offer_id is required."
    
    try:
        response = requests.get(f"{DUFFEL_API_BASE}/air/offers/{target_id}", headers=DUFFEL_HEADERS, timeout=20)
        if not response.ok:
            return f"Duffel API Notice: {extract_duffel_error(response)}"
            
        offer = response.json().get("data", {})
        flight = offer["slices"][0]["segments"][0]
        airline = (flight.get("operating_carrier") or flight.get("marketing_carrier") or {}).get("name", "Airline")
        flight_num = flight.get("operating_carrier_flight_number") or flight.get("marketing_carrier_flight_number", "")
        origin_name = flight.get("origin", {}).get("name", "Origin")
        origin_code = flight.get("origin", {}).get("iata_code", "")
        dest_name = flight.get("destination", {}).get("name", "Destination")
        dest_code = flight.get("destination", {}).get("iata_code", "")
        dep = flight.get("departing_at", "N/A").replace("T", " ")
        arr = flight.get("arriving_at", "N/A").replace("T", " ")
        return (f"Offer Details:\nOffer ID: {offer.get('id')}\nAirline: {airline} ({flight_num})\n"
                f"Route: {origin_name} ({origin_code}) to {dest_name} ({dest_code})\n"
                f"Departure: {dep}\nArrival: {arr}\n"
                f"Total Price: {offer.get('total_amount')} {offer.get('total_currency')}")
    except Exception as e:
        return f"Duffel API Error: {str(e)}"


def check_seat_availability(offer_id: str = "", flight_id: str = "", passengers: int = 1, num_passengers: int = 1, **kwargs) -> str:
    """Checks if the Duffel offer is still active and valid for booking."""
    if not DUFFEL_TOKEN: return "Error: DUFFEL_ACCESS_TOKEN not set."
    target_id = (offer_id or flight_id or "").strip()
    if not target_id: return "Error: offer_id is required."
    
    try:
        response = requests.get(f"{DUFFEL_API_BASE}/air/offers/{target_id}", headers=DUFFEL_HEADERS, timeout=20)
        if not response.ok:
            return f"No, Offer is no longer available. ({extract_duffel_error(response)})"
            
        offer = response.json().get("data", {})
        return f"Yes, Offer {target_id} is active and available to book for {offer.get('total_amount')} {offer.get('total_currency')}."
    except Exception as e:
        return f"No, Offer is no longer available. Error: {str(e)}"


def book_flight(offer_id: str = "", flight_id: str = "", passenger_name: str = "", given_name: str = "", family_name: str = "", passengers: int = 1, num_passengers: int = 1, **kwargs) -> str:
    """Book a flight using the Duffel API. Only call this AFTER explicit confirmation."""
    if not DUFFEL_TOKEN: return "Error: DUFFEL_ACCESS_TOKEN not set."
    target_id = (offer_id or flight_id or "").strip()
    if not target_id: return "Error: offer_id is required."
    
    full_name = (passenger_name or "").strip()
    g_name = (given_name or "").strip()
    f_name = (family_name or "").strip()
    
    if full_name and not (g_name and f_name):
        parts = full_name.split()
        g_name = parts[0]
        f_name = " ".join(parts[1:]) if len(parts) > 1 else "Passenger"
    
    g_name = g_name or "Aditi"
    f_name = f_name or "Sharma"
    
    try:
        offer_req = requests.get(f"{DUFFEL_API_BASE}/air/offers/{target_id}", headers=DUFFEL_HEADERS, timeout=20)
        if not offer_req.ok:
            return f"Failed to retrieve offer details: {extract_duffel_error(offer_req)}"
            
        offer = offer_req.json().get("data", {})
        passengers_data = []
        for idx, p in enumerate(offer.get("passengers", [])):
            p_given = g_name if idx == 0 else f"{g_name} {idx+1}"
            passengers_data.append({
                "id": p["id"],
                "title": "ms",
                "gender": "f",
                "given_name": p_given,
                "family_name": f_name,
                "born_on": "1995-05-15",
                "email": "booking@duffel.com",
                "phone_number": "+442080422468"
            })
            
        payload = {
            "data": {
                "type": "instant",
                "selected_offers": [target_id],
                "passengers": passengers_data,
                "payments": [{"type": "balance", "currency": offer.get("total_currency", "USD"), "amount": offer.get("total_amount", "0.00")}]
            }
        }
        order_req = requests.post(f"{DUFFEL_API_BASE}/air/orders", headers=DUFFEL_HEADERS, json=payload, timeout=30)
        if not order_req.ok:
            return f"Failed to book on Duffel: {extract_duffel_error(order_req)}"
            
        order = order_req.json().get("data", {})
        return f"Booking confirmed! Real Duffel Order ID: {order.get('id')}.\nFlight successfully booked for {g_name} {f_name}."
    except Exception as e:
        return f"Failed to book on Duffel. Error: {str(e)}"


def cancel_booking(order_id: str = "", booking_reference: str = "", **kwargs) -> str:
    """Cancel an existing Duffel Order given its Order ID (e.g., 'ord_...')."""
    if not DUFFEL_TOKEN: return "Error: DUFFEL_ACCESS_TOKEN not set."
    target_id = (order_id or booking_reference or "").strip()
    if not target_id: return "Error: order_id is required."
    
    try:
        cancel_req = requests.post(f"{DUFFEL_API_BASE}/air/order_cancellations", headers=DUFFEL_HEADERS, json={"data": {"order_id": target_id}}, timeout=20)
        if not cancel_req.ok:
            return f"Failed to cancel order on Duffel: {extract_duffel_error(cancel_req)}"
            
        cancellation_id = cancel_req.json().get("data", {}).get("id")
        confirm_req = requests.post(f"{DUFFEL_API_BASE}/air/order_cancellations/{cancellation_id}/actions/confirm", headers=DUFFEL_HEADERS, timeout=20)
        if not confirm_req.ok:
            return f"Failed to confirm cancellation: {extract_duffel_error(confirm_req)}"
            
        confirmed = confirm_req.json().get("data", {})
        return f"Order {target_id} successfully cancelled on Duffel. Refund amount: {confirmed.get('refund_amount')} {confirmed.get('refund_currency')}."
    except Exception as e:
        return f"Failed to cancel order on Duffel. Error: {str(e)}"


# Tool mappings & JSON Schemas for Groq Function Calling
TOOLS_DICT = {
    "search_flights": search_flights,
    "get_flight_details": get_flight_details,
    "check_seat_availability": check_seat_availability,
    "book_flight": book_flight,
    "cancel_booking": cancel_booking
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search real flight offers between airports or cities for a specific departure date using Duffel API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin city name or 3-letter IATA airport code (e.g. 'JFK', 'DEL', 'New York', 'Delhi')"},
                    "destination": {"type": "string", "description": "Destination city name or 3-letter IATA airport code (e.g. 'YYZ', 'BOM', 'Toronto', 'Mumbai')"},
                    "date": {"type": "string", "description": "Departure date in YYYY-MM-DD format (e.g. '2026-11-11')"},
                    "num_passengers": {"type": "integer", "description": "Number of adult passengers (default 1)"}
                },
                "required": ["origin", "destination", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_flight_details",
            "description": "Get complete information and breakdown for a flight offer given its Duffel offer_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "offer_id": {"type": "string", "description": "The Duffel offer ID (e.g. 'off_...')"}
                },
                "required": ["offer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_seat_availability",
            "description": "Check if a specific flight offer is still valid and has seats available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "offer_id": {"type": "string", "description": "The Duffel offer ID"},
                    "num_passengers": {"type": "integer", "description": "Number of seats needed (default 1)"}
                },
                "required": ["offer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Book a flight on Duffel. CRITICAL: ONLY call this AFTER the user has explicitly confirmed in a separate turn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "offer_id": {"type": "string", "description": "The Duffel offer ID"},
                    "passenger_name": {"type": "string", "description": "Full passenger name (e.g. 'Aditi Sharma')"},
                    "num_passengers": {"type": "integer", "description": "Number of passengers"}
                },
                "required": ["offer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": "Cancel an existing booking order on Duffel using its Order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The Duffel Order ID (e.g. 'ord_...')"}
                },
                "required": ["order_id"]
            }
        }
    }
]


# =====================================================================
# UI STYLING & FORMATTING HELPERS
# =====================================================================

os.system('')  # Enable ANSI colors on Windows

class UI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Palette
    CYAN = "\033[38;2;56;189;248m"
    MINT = "\033[38;2;52;211;153m"
    BLUE = "\033[38;2;129;140;248m"
    YELLOW = "\033[38;2;251;191;36m"
    GRAY = "\033[38;2;148;163;184m"
    DARK_GRAY = "\033[38;2;71;85;105m"
    WHITE = "\033[38;2;248;250;252m"

    @classmethod
    def banner(cls):
        w = 67
        border_top = f"{cls.CYAN}╭{'─' * w}╮{cls.RESET}"
        border_bot = f"{cls.CYAN}╰{'─' * w}╯{cls.RESET}"
        line1_text = "✈  DUFFEL FLIGHT CONCIERGE · AI Flight Agent"
        line1 = f"{cls.CYAN}│{cls.RESET}  {cls.BOLD}{cls.WHITE}{line1_text}{cls.RESET}{' ' * 21}{cls.CYAN}│{cls.RESET}"
        line2_text = "Live Airline Search · Instant Booking · Flight Management"
        line2 = f"{cls.CYAN}│{cls.RESET}     {cls.GRAY}{line2_text}{cls.RESET}     {cls.CYAN}│{cls.RESET}"
        line3_text = "Type 'exit' or 'quit' anytime to end session"
        line3 = f"{cls.CYAN}│{cls.RESET}     {cls.DARK_GRAY}{line3_text}{cls.RESET}{' ' * 18}{cls.CYAN}│{cls.RESET}"
        print(f"\n{border_top}\n{line1}\n{line2}\n{line3}\n{border_bot}\n")

    @classmethod
    def print_agent_response(cls, text):
        print(f"\n{cls.MINT}{cls.BOLD}✈️  Agent{cls.RESET}")
        print(f"{cls.DARK_GRAY}│{cls.RESET}")
        for line in str(text).strip().split("\n"):
            print(f"{cls.DARK_GRAY}│{cls.RESET}  {cls.WHITE}{line}{cls.RESET}")
        print(f"{cls.DARK_GRAY}│{cls.RESET}\n")

    @classmethod
    def prompt_user(cls) -> str:
        try:
            return input(f"{cls.CYAN}{cls.BOLD}👤 You {cls.RESET}{cls.CYAN}❯{cls.RESET} ")
        except (EOFError, KeyboardInterrupt):
            return "exit"


# =====================================================================
# NATIVE GROQ AGENT ENGINE (Zero Dependency & Direct HTTP API)
# =====================================================================

SYSTEM_PROMPT = """You are a helpful and professional Flight Booking Agent connected directly to the real DUFFEL live API.

CRITICAL INSTRUCTIONS:
1. ALWAYS use the provided tools to look up flight information. NEVER hallucinate flight details.
2. For flight searches, you can pass city names (e.g., 'New York', 'Toronto', 'Delhi', 'Mumbai') or 3-letter IATA codes (e.g., 'JFK', 'YYZ', 'DEL', 'BOM').
3. Booking Guardrail: You MUST NEVER call the `book_flight` tool without first getting explicit confirmation from the user in a separate turn.
   - You MUST restate ALL flight details (Offer ID, route, date, times, passengers, and total price) and ask: "Do you confirm this booking? (Yes/No)"
   - ONLY call `book_flight` in the NEXT turn if the user explicitly confirms (e.g., 'yes', 'confirm', 'proceed').
   - If the user provides passenger names, include them.
4. Memory & Context: Use the conversation history to understand references like "the second one", "that flight", or "cancel it".
"""

class GroqAgent:
    def __init__(self, api_key: str, tools_dict: dict, tools_schema: list, system_prompt: str):
        self.api_key = api_key
        self.tools_dict = tools_dict
        self.tools_schema = tools_schema
        self.system_prompt = system_prompt
        self.models_to_try = [
            os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
        ]

    def _call_groq_api(self, messages: list) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        models = []
        for m in self.models_to_try:
            if m and m not in models:
                models.append(m)

        last_error = None
        for mod in models:
            payload = {
                "model": mod,
                "messages": messages,
                "tools": self.tools_schema,
                "tool_choice": "auto",
                "temperature": 0.1
            }
            try:
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
                
                try:
                    data = resp.json()
                    err_msg = data.get("error", {}).get("message", resp.text)
                except Exception:
                    err_msg = resp.text
                
                if resp.status_code == 401:
                    raise Exception(f"Invalid Groq API Key: {err_msg}")
                if resp.status_code == 429:
                    raise Exception("Groq API Rate Limit reached. Please wait a few seconds.")
                
                last_error = Exception(f"Groq [{mod}] Error: {err_msg}")
            except requests.exceptions.RequestException as e:
                last_error = e
                continue
                
        if last_error:
            raise last_error
        raise Exception("Failed to connect to Groq API.")

    def run_turn(self, user_input: str, conversation_history: list) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in conversation_history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_input})

        for _ in range(8):
            api_response = self._call_groq_api(messages)
            choice = api_response.get("choices", [{}])[0]
            msg = choice.get("message", {})
            
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                content = msg.get("content") or ""
                return content.strip()

            messages.append({
                "role": "assistant",
                "content": msg.get("content"),
                "tool_calls": tool_calls
            })

            for tool_call in tool_calls:
                call_id = tool_call.get("id", "call_default")
                fn = tool_call.get("function", {})
                fn_name = fn.get("name", "")
                fn_args_raw = fn.get("arguments", "{}")
                
                try:
                    fn_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                except Exception:
                    fn_args = {}

                tool_fn = self.tools_dict.get(fn_name)
                if not tool_fn:
                    tool_result = f"Error: Tool '{fn_name}' does not exist."
                else:
                    try:
                        tool_result = str(tool_fn(**fn_args))
                    except Exception as e:
                        tool_result = f"Error executing {fn_name}: {str(e)}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": tool_result
                })

        return "I apologize, I reached the maximum tool execution steps without completing the request."


# =====================================================================
# MAIN EXECUTION LOOP
# =====================================================================

def main():
    UI.banner()

    groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()

    if not groq_api_key:
        print(f"{UI.YELLOW}🔑 GROQ_API_KEY is not set in your environment.{UI.RESET}")
        print(f"{UI.GRAY}   (You can get a free key instantly from https://console.groq.com){UI.RESET}")
        try:
            user_key = input(f"{UI.CYAN}Enter your Groq API Key (starts with gsk_): {UI.RESET}").strip()
            if user_key:
                groq_api_key = user_key
                os.environ["GROQ_API_KEY"] = user_key
            else:
                print(f"{UI.YELLOW}⚠️  No API Key entered. Groq calls will fail until a key is provided.{UI.RESET}\n")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

    agent = GroqAgent(
        api_key=groq_api_key,
        tools_dict=TOOLS_DICT,
        tools_schema=TOOLS_SCHEMA,
        system_prompt=SYSTEM_PROMPT
    )

    conversation_history = []

    while True:
        user_input = UI.prompt_user()
        
        if user_input.strip().lower() in ("exit", "quit"):
            print(f"\n{UI.GRAY}👋 Safe travels! Goodbye.{UI.RESET}\n")
            break
            
        if not user_input.strip():
            continue

        try:
            if not agent.api_key and os.environ.get("GROQ_API_KEY"):
                agent.api_key = os.environ.get("GROQ_API_KEY")

            reply = agent.run_turn(user_input, conversation_history)
            UI.print_agent_response(reply)

            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": reply})

        except Exception as e:
            err_msg = str(e)
            UI.print_agent_response(f"⚠️ Error: {err_msg}")


if __name__ == "__main__":
    main()
