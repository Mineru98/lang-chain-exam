import asyncio
import json

import ollama


def get_antonyms(word: str) -> str:
    "Get the antonyms of the any given word"

    words = {
        "hot": "cold",
        "small": "big",
        "weak": "strong",
        "light": "dark",
        "lighten": "darken",
        "dark": "bright",
    }

    return json.dumps(words.get(word, "Not available in database"))


def get_flight_times(departure: str, arrival: str) -> str:
    flights = {
        "NYC-LAX": {
            "departure": "08:00 AM",
            "arrival": "11:30 AM",
            "duration": "5h 30m",
        },
        "LAX-NYC": {
            "departure": "02:00 PM",
            "arrival": "10:30 PM",
            "duration": "5h 30m",
        },
        "LHR-JFK": {
            "departure": "10:00 AM",
            "arrival": "01:00 PM",
            "duration": "8h 00m",
        },
        "JFK-LHR": {
            "departure": "09:00 PM",
            "arrival": "09:00 AM",
            "duration": "7h 00m",
        },
        "CDG-DXB": {
            "departure": "11:00 AM",
            "arrival": "08:00 PM",
            "duration": "6h 00m",
        },
        "DXB-CDG": {
            "departure": "03:00 AM",
            "arrival": "07:30 AM",
            "duration": "7h 30m",
        },
    }

    key = f"{departure}-{arrival}".upper()
    return json.dumps(flights.get(key, {"error": "Flight not found"}))


async def run(model: str, user_input: str):
    client = ollama.AsyncClient()
    messages = [
        {
            "role": "user",
            "content": user_input,
        }
    ]

    response = await client.chat(
        model=model,
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_flight_times",
                    "description": "Get the flight times between two cities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "departure": {
                                "type": "string",
                                "description": "The departure city (airport code)",
                            },
                            "arrival": {
                                "type": "string",
                                "description": "The arrival city (airport code)",
                            },
                        },
                        "required": ["departure", "arrival"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_antonyms",
                    "description": "Get the antonyms of any given words",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "word": {
                                "type": "string",
                                "description": "The word for which the opposite is required.",
                            },
                        },
                        "required": ["word"],
                    },
                },
            },
        ],
    )

    messages.append(response["message"])

    if not response["message"].get("tool_calls"):
        print("\nThe model didn't use the function. Its response was:")
        print(response["message"]["content"])
        return

    if response["message"].get("tool_calls"):
        available_functions = {
            "get_flight_times": get_flight_times,
            "get_antonyms": get_antonyms,
        }
        for tool in response["message"]["tool_calls"]:
            function_to_call = available_functions[tool["function"]["name"]]
            print(f"function to call: {function_to_call}")

            if function_to_call == get_flight_times:
                function_response = function_to_call(
                    tool["function"]["arguments"]["departure"],
                    tool["function"]["arguments"]["arrival"],
                )
                print(f"function response: {function_response}")

            elif function_to_call == get_antonyms:
                function_response = function_to_call(
                    tool["function"]["arguments"]["word"],
                )
                print(f"function response: {function_response}")

            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )


while True:
    user_input = input("\n Please ask=> ")
    if not user_input:
        user_input = "What is the flight time from NYC to LAX?"
    if user_input.lower() == "exit":
        break

    # asyncio.run(run("mistral-nemo", user_input))
    asyncio.run(run("nemotron-mini", user_input))
