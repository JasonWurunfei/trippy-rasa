from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import requests
import random
import re
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

class ValidateRegisterForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_register_form"
    
    def validate_username(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        username = slot_value
        pattern = re.compile("^[a-zA-Z][a-zA-Z0-9]*$")
        if pattern.match(username):
            r = requests.get(f'{config["DB_API_ADDRESS"]}/user/checkname', 
                            params={"username": username})
            res = r.json()['result']
            if res:
                dispatcher.utter_message(f"ok, so your username is {username}")
                return {"username": username}
            else:
                dispatcher.utter_message(f"The username '{username}' is used by others, \
                    please choose another one.")
                return {"username": None}
        else:
            dispatcher.utter_message(f"Sorry, username '{username}' is not acceptable.")
            return {"username": None}

    def validate_password(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        password = slot_value
        pattern = re.compile("^[^\s-]+$")
        if pattern.match(password):
            dispatcher.utter_message(f"ok, so your password is {password}")
            return {"password": password}
        else:
            dispatcher.utter_message(f"Sorry, password '{password}' is not acceptable.")
            return {"password": None}

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

class LoginOrRegister(Action):

    def name(self) -> Text:
        return "action_login_or_register"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(
            text="I need to know your user account to proceed, \
                do you want to login with existing account or register a new one?",
            buttons= [
                {"payload": f"/login", "title": "Login"},
                {"payload": f"/register", "title": "Register"},
            ]
        )
        last_intent = tracker.get_intent_of_latest_message()
        return [SlotSet("last_intent", last_intent)]

class CreateUserOrder(Action):

    def name(self) -> Text:
        return "action_create_user_order"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")

        username = tracker.get_slot("username")

        r = requests.get(f'{config["DB_API_ADDRESS"]}/package/destination', 
                        params={"destination": destination})
        package = r.json()['packages'][0]
        r = requests.post(f'{config["DB_API_ADDRESS"]}/order', 
                    json = {
                        "username": username,
                        "package_id": package['id']
                    })
        if r.status_code == requests.codes.created:
            dispatcher.utter_message(f"Your order to {destination} is created!")
            guide = package['guide']
            dispatcher.utter_message(
                f"Your guide of the tour is {guide['name']}, his/her phone number is {guide['phone_number']} \
                and his/her email is {guide['email']}, the guide will give you guided tours of major landmarks \
                and venues. This is included in the package so it's free.")
            hotel = package['hotel']
            dispatcher.utter_message(f"We have also secure a hotel room for you at {hotel['name']} with \
                our special discount, you only need to pay anthor ${hotel['price']} to book the room.")
            car_rental = package['car_rental']
            dispatcher.utter_message(f"We also help you find a good car rental comany which is \
                provided by {car_rental['name']} at a cost of only ${car_rental['price']}. \
                It is also much cheaper than their normal price.")
            dispatcher.utter_message(f"Have a fantastic trip!")
        elif r.status_code == requests.codes.bad_request:
            dispatcher.utter_message(
                f"You have already booked a trip to {destination}. Have a fantastic trip!")
        else:
            dispatcher.utter_message(
                f"Sorry, something went wrong during order creation.")
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

class ActionQueryCompanyContact(Action):

    def name(self) -> Text:
        return "action_query_company_contact"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        r = requests.get(
            f'{config["DB_API_ADDRESS"]}/info/contact').json()
        dispatcher.utter_message("Here is Trippy's contact information")
        dispatcher.utter_message(text=r['contact'])

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
            dispatcher.utter_message(f"Hi {username}")
            last_intent = tracker.get_slot("last_intent")
            destination = tracker.get_slot("destination")
            if last_intent == "book_package":
                if destination:
                    dispatcher.utter_message(f"You were saying you want to buy the trip to {destination}, \
                        is that correct?")
                else:
                    dispatcher.utter_message("We offer packages to Switzerland, Japan, Thailand, \
                        South Korea, Czech Republic, France, Italy, and Spain. Where do you want to go?")
            else:
                if last_intent == "ask_user_orders":
                    r = requests.get(f'{config["DB_API_ADDRESS"]}/user/orders', 
                        params={"username": username})
                    packages = r.json()
                    dispatcher.utter_message("you've ordered the following:")
                    for i, package in enumerate(packages, 1):
                        dispatcher.utter_message(
                            f"{i} {package['title']} [Country: {package['country']}, \
                            Destination: {package['destination']}]")
                else:
                    dispatcher.utter_message("How can I help?")
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
            dispatcher.utter_message(f"Hi {username}")
            last_intent = tracker.get_slot("last_intent")
            destination = tracker.get_slot("destination")
            if last_intent == "book_package":
                if destination:
                    dispatcher.utter_message(f"You were saying you want to buy the trip to {destination}, \
                        is that correct?")
                else:
                    dispatcher.utter_message("We offer packages to Switzerland, Japan, \
                        Thailand, South Korea, Czech Republic, France, Italy, and Spain. \
                        Where do you want to go?")
            else:
                dispatcher.utter_message("How can I help?")
            return [
                SlotSet("is_authenticated", True),
                SlotSet("username", username), 
                SlotSet("password", password)
            ]
        else:
            dispatcher.utter_message(f"The username '{username}' is taken, please choose another one")
            return [
                SlotSet("username", None), 
                SlotSet("password", None),
            ]

class CancelUserTrip(Action):
    def name(self) -> Text:
        return "action_cancel_user_trip"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        destination = tracker.get_slot("target_destination")
        username = tracker.get_slot("username")
        r = requests.delete(f'{config["DB_API_ADDRESS"]}/order/cancel', 
                            params= {
                                "username": username,
                                "destination": destination
                            })
        if r.status_code == requests.codes.ok:
            dispatcher.utter_message("trip canceled")
        elif r.status_code == requests.codes.not_found:
            dispatcher.utter_message("Can not find your package order. \
                Please contact trippy directly.")
        else:
            dispatcher.utter_message(
                "Sorry, something wrong happened during cancelation")
        return [SlotSet("target_destination", None)]

class QueryAvailableFlight(Action):
    def name(self) -> Text:
        return "action_get_next_available_flight"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        undesired_flight_ids = tracker.get_slot("undesired_flight_ids")
        # By default all package is assigned with flight id 1. This is just for demostation, 
        # should not happen in real production. Since user said flight unavailable 
        # hence id 1 is not desired.
        undesired_flight_ids = undesired_flight_ids if undesired_flight_ids is not None else [1] 
        r = requests.get(f'{config["DB_API_ADDRESS"]}/flight/available', 
                            params={"undesired_flight_ids": undesired_flight_ids})
        flight = r.json()['new_flight']
        if flight:
            dispatcher.utter_message(
                f"I've found the next availble flight offered by {flight['airline']} \
                which will take off in {flight['departure_time']} hours at departure port \
                No.{flight['departure_port']}")
            undesired_flight_ids.append(flight['id'])
            return [SlotSet("undesired_flight_ids", undesired_flight_ids)]
        else:
            dispatcher.utter_message("I'm sorry, there is currently no available flight.")
            return [SlotSet("no_available_flight", True)]

class ChangeFlight(Action):
    def name(self) -> Text:
        return "action_change_flight"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
         # remove the room from the undesired list
        undesired_flight_ids = tracker.get_slot("undesired_flight_ids")
        flight_id = undesired_flight_ids.pop()
        destination = tracker.get_slot("target_destination")
        username = tracker.get_slot("username")

        r = requests.put(f'{config["DB_API_ADDRESS"]}/user/order/flight', 
                params={
                    'destination': destination, 
                    'username': username,
                    'flight_id': flight_id
                })
        if r.status_code == requests.codes.ok:
            dispatcher.utter_message(
                "Flight changed! Your boarding pass can be print at the airport \
                lounge. Have a safe flight.")
        elif r.status_code == requests.codes.not_found:
            dispatcher.utter_message(f"Sorry, you haven't ordered package to {destination}.")
        else:
            dispatcher.utter_message("Sorry, something when wrong during the process.")
        return [
            SlotSet("undesired_flight_ids", undesired_flight_ids),
            SlotSet("no_available_flight", False),
            SlotSet("target_destination", None),
        ]

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
        packages = r.json()['packages']
        dispatcher.utter_message("you've ordered the following:")
        for i, package in enumerate(packages, 1):
            dispatcher.utter_message(
                f"{i} {package['title']} [Country: {package['country']}, \
                Destination: {package['destination']}]")

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

        destination = tracker.get_slot("target_destination")
        username = tracker.get_slot("username")

        r = requests.put(f'{config["DB_API_ADDRESS"]}/user/order/guide', 
                params={'destination': destination, 'username': username})
        new_guide = r.json()['new_guide']

        dispatcher.utter_message(f"Ok, I have rearrange your guide, \
            the new guide is {new_guide['name']} Phone: {new_guide['phone_number']} \
            Email: {new_guide['email']}. Have a great trip!")

        return [SlotSet("target_destination", None)]

class OfferCoupon(Action):
    def name(self) -> Text:
        return "action_offer_coupon"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        destination = next(tracker.get_latest_entity_values("destination"), "Praha")
        r = requests.get(f'{config["DB_API_ADDRESS"]}/restaurant/available', 
                            params={
                                "destination": destination,
                                "old_restaurant_name": "Unknown"
                            })
        restaurant = r.json()['new_restaurant']
        dispatcher.utter_message(f"here is a coupon code you can use at {restaurant['name']}, \
            which is a restaurant very close to your location, for your compensation")
        dispatcher.utter_message(f"Trippy@{restaurant['name']}{random.randint(4000,8000)}")
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
        destination = next(tracker.get_latest_entity_values("destination"), "Praha")
        undesired_hotel_ids = tracker.get_slot("undesired_hotel_ids")
        undesired_hotel_ids = undesired_hotel_ids if undesired_hotel_ids is not None else []
        r = requests.get(f'{config["DB_API_ADDRESS"]}/hotel/available', 
                            params={
                                "destination": destination,
                                "undesired_hotel_ids": undesired_hotel_ids
                            })
        hotel = r.json()['new_hotel']
        if hotel:
            dispatcher.utter_message(f"I've found a new hotel room at {hotel['name']}. \
                Here are their contact information:")
            dispatcher.utter_message(f"Address: {hotel['address']}, Telephone: {hotel['telephone']}")
            dispatcher.utter_message(f"The room price is ${hotel['price']}")
            undesired_hotel_ids.append(hotel['id'])
            return [SlotSet("undesired_hotel_ids", undesired_hotel_ids)]
        else:
            dispatcher.utter_message("I'm sorry, there is currently no available room.")
            return [SlotSet("no_available_room", True)]

class ChangeNewRoom(Action):
    def name(self) -> Text:
        return "action_change_new_room"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # remove the room from the undesired list
        undesired_hotel_ids = tracker.get_slot("undesired_hotel_ids")
        hotel_id = undesired_hotel_ids.pop()
        destination = tracker.get_slot("target_destination")
        username = tracker.get_slot("username")

        r = requests.put(f'{config["DB_API_ADDRESS"]}/user/order/hotel', 
                params={
                    'destination': destination, 
                    'username': username,
                    'hotel_id': hotel_id
                })
        if r.status_code == requests.codes.ok:
            dispatcher.utter_message("Okay, your room has been rearranged!")
        elif r.status_code == requests.codes.not_found:
            dispatcher.utter_message(f"Sorry, you haven't ordered package to {destination}.")
        else:
            dispatcher.utter_message("Sorry, something went wrong during the process.")
        return [
            SlotSet("undesired_hotel_ids", undesired_hotel_ids),
            SlotSet("no_available_room", False),
            SlotSet("target_destination", None)
        ]

def utter_packages(dispatcher: CollectingDispatcher, packages: List[Dict]) -> None:
    for i, package in enumerate(packages, 1):
        dispatcher.utter_message(
            text=f"#{i} {package['title']} | Country: {package['country']} | \
            Destination: {package['destination']}",
            image=package['pic_url'])
        dispatcher.utter_message(f"Description: {package['description']}")
        dispatcher.utter_message(f"The trip is {package['duration']} days long \
            and the price is \${package['price']}")
    dispatcher.utter_message("You can book a package by telling me the package destination.")

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
        if country.title() not in ALLOWED_COUNTRIES:
            allowed_countries = ", ".join(ALLOWED_COUNTRIES)
            dispatcher.utter_message(f"We don't have travel package to {country}, \
                but we do have packages to {allowed_countries}.")
            return []
        
        r = requests.get(f'{config["DB_API_ADDRESS"]}/package/country', 
                params={"country": country.title()})
 
        dispatcher.utter_message(f"Here are some packages in {country.title()}.")
        packages = r.json()['packages']

        utter_packages(dispatcher, packages)
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
        showed_packages_ids = tracker.get_slot("showed_packages_ids")
        showed_packages_ids = showed_packages_ids if showed_packages_ids is not None else []
        r = requests.get(f'{config["DB_API_ADDRESS"]}/package/popular', 
                            params={
                                "batch": 4,
                                "showed_package_ids": showed_packages_ids
                            })
        packages = r.json()['packages']
        if len(packages) != 0:
            dispatcher.utter_message("Here are some popular package:")
            utter_packages(dispatcher, packages)
            new_package_ids = [package['id'] for package in packages]
            return [SlotSet("showed_packages_ids", showed_packages_ids + new_package_ids),]
        else:
            dispatcher.utter_message("I've show you all packages that Trippy offers.")
            return [SlotSet("no_more_packages", True)]
