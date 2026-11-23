import os
import sys
import uuid
import json
import requests

# =====================================================================
# MOCK FLIGHT DATA & STORAGE
# =====================================================================

MOCK_FLIGHTS = [
    {"flight_id": "AI101", "origin": "Delhi", "destination": "Mumbai", "date": "2026-09-10", "departure": "06:00", "arrival": "08:15", "price": 4500, "seats_available": 3},
    {"flight_id": "6E202", "origin": "Delhi", "destination": "Mumbai", "date": "2026-09-10", "departure": "09:30", "arrival": "11:45", "price": 3900, "seats_available": 0},
    {"flight_id": "UK303", "origin": "Delhi", "destination": "Mumbai", "date": "2026-09-10", "departure": "18:00", "arrival": "20:15", "price": 5200, "seats_available": 6},
    {"flight_id": "AI404", "origin": "Mumbai", "destination": "Bengaluru", "date": "2026-09-12", "departure": "07:00", "arrival": "08:45", "price": 3800, "seats_available": 2},
    {"flight_id": "6E505", "origin": "Kolkata", "destination": "Chennai", "date": "2026-09-15", "departure": "13:20", "arrival": "15:40", "price": 4100, "seats_available": 5},
    {"flight_id": "SG606", "origin": "Delhi", "destination": "Kolkata", "date": "2026-09-11", "departure": "10:00", "arrival": "12:10", "price": 3600, "seats_available": 4},
    {"flight_id": "AC808", "origin": "New York", "destination": "Toronto", "date": "2026-11-11", "departure": "08:30", "arrival": "10:15", "price": 12500, "seats_available": 5},
    {"flight_id": "DL909", "origin": "New York", "destination": "Toronto", "date": "2026-11-11", "departure": "15:00", "arrival": "16:45", "price": 14200, "seats_available": 4},
]

BOOKINGS = {}

# =====================================================================
# TOOLS
# =====================================================================

def search_flights(origin: str = "", destination: str = "", date: str = "", **kwargs) -> str:
    """Search MOCK_FLIGHTS for flights matching origin, destination, and date."""
    orig = origin.strip().lower()
    dest = destination.strip().lower()
    dt = date.strip()

    matches = []
    for f in MOCK_FLIGHTS:
        if (f["origin"].lower() == orig and
            f["destination"].lower() == dest and
            f["date"] == dt and
            f["seats_available"] > 0):
            matches.append(f)

    if not matches:
        return f"No available flights found from {origin} to {destination} on {date}."

    res = [f"Found {len(matches)} available flight(s) from {origin} to {destination} on {date}:"]
    for idx, f in enumerate(matches, 1):
        res.append(f"{idx}. Flight {f['flight_id']}: {f['departure']} to {f['arrival']}, Price: {f['price']} INR, Seats: {f['seats_available']}")
    return "\n".join(res)


def get_flight_details(flight_id: str = "", **kwargs) -> str:
    """Return full details for a single flight given its flight_id."""
    fid = flight_id.strip().upper()
    for f in MOCK_FLIGHTS:
        if f["flight_id"].upper() == fid:
            return (f"Flight {f['flight_id']} details:\n"
                    f"Route: {f['origin']} to {f['destination']}\n"
                    f"Date: {f['date']}\n"
                    f"Times: {f['departure']} - {f['arrival']}\n"
                    f"Price: {f['price']} INR\n"
                    f"Seats Available: {f['seats_available']}")
    return f"Flight with ID {flight_id} not found."


def check_seat_availability(flight_id: str = "", passengers: int = 1, num_passengers: int = 1, **kwargs) -> str:
    """Check whether a flight has enough seats for the given number of passengers."""
    fid = flight_id.strip().upper()
    p_count = max(1, passengers or num_passengers or 1)
    for f in MOCK_FLIGHTS:
        if f["flight_id"].upper() == fid:
            if f["seats_available"] >= p_count:
                return f"Yes, flight {f['flight_id']} has {f['seats_available']} seats available, which is enough for {p_count} passenger(s)."
            else:
                return f"No, flight {f['flight_id']} only has {f['seats_available']} seats available. Not enough for {p_count} passenger(s)."
    return f"Flight with ID {flight_id} not found."


def book_flight(flight_id: str = "", passenger_name: str = "", passengers: int = 1, num_passengers: int = 1, **kwargs) -> str:
    """Book a flight for a passenger. Only call this AFTER explicit user confirmation."""
    fid = flight_id.strip().upper()
    p_count = max(1, passengers or num_passengers or 1)
    p_name = (passenger_name or "Aditi Sharma").strip()

    for f in MOCK_FLIGHTS:
        if f["flight_id"].upper() == fid:
            if f["seats_available"] < p_count:
                return f"Failed to book. Only {f['seats_available']} seats left on {f['flight_id']}."
            
            f["seats_available"] -= p_count
            booking_ref = uuid.uuid4().hex[:8].upper()
            BOOKINGS[booking_ref] = {
                "flight_id": f["flight_id"],
                "passenger_name": p_name,
                "passengers": p_count,
                "status": "CONFIRMED"
            }
            return f"Booking confirmed! Reference: {booking_ref}.\nFlight {f['flight_id']} successfully booked for {p_count} passenger(s) under name '{p_name}'."
    return f"Flight with ID {flight_id} not found."


def cancel_booking(booking_reference: str = "", **kwargs) -> str:
    """Cancel an existing booking given its booking reference."""
    ref = booking_reference.strip().upper()
    if ref in BOOKINGS:
        booking = BOOKINGS[ref]
        if booking["status"] == "CANCELLED":
            return f"Booking {ref} is already cancelled."

        flight_id = booking["flight_id"]
        passengers = booking["passengers"]

        for f in MOCK_FLIGHTS:
            if f["flight_id"] == flight_id:
                f["seats_available"] += passengers
                break

        booking["status"] = "CANCELLED"
        return f"Booking {ref} successfully cancelled. {passengers} seat(s) restored to flight {flight_id}."

    return f"Booking reference {booking_reference} not found."


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
            "description": "Search available flights by origin city, destination city, and date (YYYY-MM-DD).",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin city (e.g. 'Delhi', 'Mumbai', 'New York')"},
                    "destination": {"type": "string", "description": "Destination city (e.g. 'Mumbai', 'Toronto')"},
                    "date": {"type": "string", "description": "Flight date in YYYY-MM-DD format (e.g. '2026-09-10')"}
                },
                "required": ["origin", "destination", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_flight_details",
            "description": "Get detailed flight info (times, price, seats) given a flight_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_id": {"type": "string", "description": "The flight identifier (e.g. 'AI101', 'UK303')"}
                },
                "required": ["flight_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_seat_availability",
            "description": "Check if a flight has enough seats for the requested passenger count.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_id": {"type": "string", "description": "Flight ID (e.g. 'UK303')"},
                    "passengers": {"type": "integer", "description": "Number of passengers needed"}
                },
                "required": ["flight_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Book a flight for a passenger. ONLY call this AFTER the user has explicitly confirmed in a separate turn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_id": {"type": "string", "description": "Flight ID (e.g. 'UK303')"},
                    "passenger_name": {"type": "string", "description": "Passenger name"},
                    "passengers": {"type": "integer", "description": "Number of passengers"}
                },
                "required": ["flight_id", "passenger_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": "Cancel an existing booking using its booking reference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_reference": {"type": "string", "description": "The booking reference (e.g. '9A2B4C6D')"}
                },
                "required": ["booking_reference"]
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
        line1_text = "✈  FLIGHT CONCIERGE AI · Booking Assistant"
        line1 = f"{cls.CYAN}│{cls.RESET}  {cls.BOLD}{cls.WHITE}{line1_text}{cls.RESET}{' ' * 24}{cls.CYAN}│{cls.RESET}"
        line2_text = "Smart Flight Search · Booking Confirmation · Cancellation"
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
# NATIVE GROQ AGENT ENGINE
# =====================================================================

SYSTEM_PROMPT = """You are a helpful and professional Flight Booking Agent.
Your goal is to assist users in searching for flights, checking details, and securely booking them.

CRITICAL INSTRUCTIONS:
1. NEVER hallucinate flight details. ALWAYS use the provided tools to look up flight information, IDs, prices, and availability.
2. Booking Guardrail: You MUST NEVER call the `book_flight` tool without first getting explicit confirmation from the user in a separate turn.
   - When the user asks to book a flight, FIRST use `check_seat_availability` to ensure enough seats exist if you haven't done so recently.
   - If seats are available, respond by restating ALL flight details (flight_id, route, date, times, price, number of passengers, and total price).
   - You MUST end your response by asking the user: "Do you confirm this booking? (Yes/No)"
   - ONLY call `book_flight` in the NEXT turn if the user explicitly confirms (e.g. says yes, confirm, etc.).
3. Memory & Context: Use the conversation history to understand references like "the second one", "that flight", or "book it".
4. When a user asks to cancel, ask for the booking reference if not provided, then call `cancel_booking`.
5. If the user asks about a city that doesn't exist or isn't found, clearly state that no matching flights were found.
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
                    tool_result = f"Error: Tool '{fn_name}' not found."
                else:
                    try:
                        tool_result = str(tool_fn(**fn_args))
                    except Exception as e:
                        tool_result = f"Error: {str(e)}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": tool_result
                })

        return "I apologize, I could not complete your request after multiple tool execution steps."


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
