

## Implementation Details

### Conversational Memory
The conversational memory is handled natively using LangChain's `chat_history` mechanism:
1. In the `ChatPromptTemplate`, we include a `MessagesPlaceholder(variable_name="chat_history")`. This placeholder reserves a spot for all previous dialog turns to be injected into the LLM's context window.
2. In the `while` loop, we maintain a Python list `chat_history = []`.
3. After every interaction, the user's string input is wrapped in a `HumanMessage`, and the agent's response string is wrapped in an `AIMessage`. Both are immediately appended to the list.
4. By passing this list into the `agent_executor.invoke()` call, the agent gains full context of prior turns, allowing it to easily resolve references like "the second one" to the specific flight discussed previously.

### Confirmation Guardrail Enforcement
The critical confirmation guardrail is purely enforced via the agent's `SYSTEM_PROMPT`. 
I provided strict instructions: *"You MUST NEVER call the `book_flight` tool without first getting explicit confirmation from the user in a separate turn."*
The prompt dictates a highly specific workflow for the agent to follow when a user requests a booking:
1. Check seat availability first to prevent bad user experiences.
2. Restate **all** flight details (flight ID, route, date, times, passengers, total price) in its text response.
3. End the message with the exact question: *"Do you confirm this booking? (Yes/No)"*.
4. Wait for the next turn. It will only invoke the `book_flight` tool if the `chat_history` shows that the user said yes in their subsequent reply. This leverages the instruction-following capabilities of the LLM to cleanly separate the intent-gathering step from the tool-invocation step.

### Edge Cases Handled
**Zero-Seat Flights Excluded from Search:**
When searching for flights, the `search_flights` tool filters out any flights where `seats_available <= 0`. For example, flight `6E202` (Delhi to Mumbai) has 0 seats in the database. By filtering it out during the initial search, we prevent the user from attempting to book an unavailable flight when they ask for "the second one" out of the listed options, making the conversational flow much smoother and avoiding unnecessary tool failures.
