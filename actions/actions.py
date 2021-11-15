from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

ALLOWED_COUNTRIES = [
    "Switzerland",
    "Japan",
    "Thailand",
    "South Korea",
    "Czech Republic",
    "France",
    "Italy",
    "Spain",
]

ALLOWED_DESTINATIONS = [
    "Praha",
    "Kalovy Vary",
    "Fuengirola",
    "Madrid",
    "Versailles Palace",
    "Mont Saint-Michel",
    "Venice",
    "Pompeii",
    "Chiangmai",
    "Bangkok",
    "Seoul",
    "Busan",
    "Lucerne",
    "Zurich",
    "Hokkaido",
    "Kobe",
]

class ValidateBookPackageForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_book_package_form"
    
    def validate_destination(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        destination = slot_value
        if destination.title() not in ALLOWED_DESTINATIONS:
            allowed_destinations = ", ".join(ALLOWED_DESTINATIONS)
            dispatcher.utter_message(text=
                f"Sorry, I don't recognize {destination}, we only have packages in {allowed_destinations}.", 
                buttons =[
                    {"payload": f"/inform\{destination: {destination}\}", "title": destination} \
                    for destination in ALLOWED_DESTINATIONS
                ])
            return {"destination": None}
        
        dispatcher.utter_message(text=f"ok, you want the {destination} package.")
        return {"destination": slot_value}


class CreateUserOrder(Action):

    def name(self) -> Text:
        return "action_create_user_order"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")

        username = tracker.get_slot("username")
        dispatcher.utter_message(f"username: {username}, destination: {destination}")
        r = requests.get(f'{config["DB_API_ADDRESS"]}/package/destination', 
                        params={"destination": destination})
        package = r.json()['packages'][0]
        r = requests.post(f'{config["DB_API_ADDRESS"]}/order', 
                    json = {
                        "username": username,
                        "package_id": package['id']
                    })
        dispatcher.utter_message("The order is created!")
        guide = package['guide']
        dispatcher.utter_message(f"Your guide of the tour is {guide['name']}, his phone number is {guide['phone_number']} and his email is {guide['email']}")
        hotel = package['hotel']
        dispatcher.utter_message(f"We have also secure a hotel room for you at {hotel['name']} with our special discount, you only need to pay anthor ${hotel['price']} to book the room.")
        car_rental = package['car_rental']
        dispatcher.utter_message(f"We also help you find a good car rental comany which is provided by {car_rental['name']} at a cost of only ${car_rental['price']}. It is also much cheaper than their normal price :)")
        dispatcher.utter_message(f"Have a fantastic trip!")
        return [SlotSet("destination", None)]


class ActionQueryCompanyInfo(Action):

    def name(self) -> Text:
        return "action_query_company_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        r = requests.get(
            f'{config["DB_API_ADDRESS"]}/info/company').json()

        dispatcher.utter_message(text=r['info'])

        return []


class LoginUser(Action):
    def name(self) -> Text:
        return "action_login_user"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        username = tracker.get_slot("username")
        password = tracker.get_slot("password")

        r = requests.post(f'{config["DB_API_ADDRESS"]}/user/login', 
                    json = {
                        "username": username,
                        "password": password
                    })
        if r.status_code == requests.codes.ok:
            dispatcher.utter_message(f"Hi {username}, how can I help you?")
            return [SlotSet("is_authenticated", True)]
        
        else:
            dispatcher.utter_message(f"Sorry, it seems that the username or the password is not vaild.")
            dispatcher.utter_message(response="login_form")
            return [SlotSet("username", None), SlotSet("password", None)]

class RegisterUser(Action):
    def name(self) -> Text:
        return "action_register_user"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        username = tracker.get_slot("username")
        password = tracker.get_slot("password")
        r = requests.post(f'{config["DB_API_ADDRESS"]}/user/register', 
                            json = {
                                "username": username,
                                "password": password
                            })
        if r.status_code == requests.codes.created:
            dispatcher.utter_message(f"Hi {username}, how can I help you?")
            return [
                SlotSet("is_authenticated", True),
                SlotSet("username", username), 
                SlotSet("password", password)
            ]
        else:
            dispatcher.utter_message(f"The username '{username}' is taken, please choose another one")
        return []

class CancelUserTrip(Action):
    def name(self) -> Text:
        return "action_cancel_user_trip"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("trip canceled")

        return []

class QueryAvailableFlight(Action):
    def name(self) -> Text:
        return "action_get_next_available_flight"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(
            "I've found the next availble flight offered by Etihad Airways \
            which will take off in 2 hours at departure port No.3")

        return []

class ChangeFlight(Action):
    def name(self) -> Text:
        return "action_change_flight"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(
            "Flight changed! Your boarding pass can be print at the airport \
            lounge. Have a save flight :)")

        return []

class QueryUserOrders(Action):
    def name(self) -> Text:
        return "action_query_user_orders"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        username = tracker.get_slot("username")
        r = requests.get(f'{config["DB_API_ADDRESS"]}/user/orders', 
                        params={"username": username})
        packages = r.json()
        dispatcher.utter_message("you've ordered the following:")
        for i, package in enumerate(packages, 1):
            dispatcher.utter_message(
                f"{i}. {package['title']} [Country: {package['country']}, Destination: {package['destination']}]")

        return [SlotSet("orders", [
            f"{package['title']} {package['country']} {package['destination']}" for package in packages
        ])]

class ChangeGuide(Action):
    def name(self) -> Text:
        return "action_change_guide"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("the new guide is xxx")

        return []

class OfferCoupon(Action):
    def name(self) -> Text:
        return "action_offer_coupon"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("here is the restaurant coupon for your compensation")

        return []

class FindNewRoom(Action):
    def name(self) -> Text:
        return "action_find_new_room"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("here is the new room")

        return []

class ChangeNewRoom(Action):
    def name(self) -> Text:
        return "action_change_new_room"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message("Change to the new room")

        return []

class QueryCountrySpecificPackages(Action):
    def name(self) -> Text:
        return "action_query_country_specific_packages"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        country = next(tracker.get_latest_entity_values("country"), None)
        dispatcher.utter_message(f"here are some package to {country}")

        return []


class QueryPopularPackages(Action):
    def name(self) -> Text:
        return "action_query_popular_packages"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        r = requests.get(f'{config["DB_API_ADDRESS"]}/package/popular')
        packages = r.json()['packages']
        dispatcher.utter_message("here are some popular package:")
        for i, package in enumerate(packages, 1):
            dispatcher.utter_message(f"""
            {i}. {package['title']}
            Country: {package['country']} Destination{package['destination']}
            {package['description']}
            """)
        return []
