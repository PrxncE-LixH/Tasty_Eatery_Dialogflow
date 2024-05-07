
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db
import functions


app = FastAPI()

inprogress_orders = {}

@app.post("/")
async def handle_requests(request: Request):
    payload = await request.json() # get data from request

    # get info from the payload based on the structure of the webhook sent by diagflow
    intent = payload['queryResult']['intent']['displayName']
    param = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts'] 

    session_ID = functions.get_session_ID(output_contexts[0]['name'])


    intent_handler = {
        "order.add - context: ongoing-order": add_to_order,
        "order.remove - context: ongoing-order": remove_from_order,
        "order.complete - context: ongoing-order": complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    return intent_handler[intent](param, session_ID)


def add_to_order(param: dict, session_ID: str):
    # get the food items and qunatities
    # refer to diagflow json
    food_items = param['food-items']
    food_quantities = param['number']

    if len(food_items) != len(food_quantities):
        fulfillment_text = "Sorry I didn't understand that. You need to explicitly specify the quantity for each item."
    else:
        food_dict = dict(zip(food_items, food_quantities)) # make a new dict with the food item and food qty 
                                                           # {pizza: 2, mago: 1} 

        # handling instances where bot asks anything else after initial order:
        if session_ID in inprogress_orders: # if it already exists merge the new order from anything else with the previous order
            current_food_dict = inprogress_orders[session_ID]
            current_food_dict.update(food_dict)            # merge new order - dict with the previous order - dict
            inprogress_orders[session_ID] = current_food_dict
        else:
            inprogress_orders[session_ID] = food_dict  #if the session is not yet in progress, save it as a new entry

        order_str = functions.get_str_food_dict(inprogress_orders[session_ID])
        fulfillment_text = f"Order received for {food_items} and {food_quantities}. Would you want something else? "

def remove_from_order(param: dict, session_ID: str):
    if session_ID not in inprogress_orders:  
        return JSONResponse(content={"fulfillmentText": "I am facing some difficulties retrieving your order. Make sure you already have an order placed"
        })
    
    current_order = inprogress_orders[session_ID] # retrieve the current dict with food items in it
    food_items = param["food-items"]

    removed_items = []
    doesnt_exist = []

    for item in food_items:         # iterate through the dict
        if item not in current_order:
            doesnt_exist.append(item)    # save items that werent found in the dict
        else:
            removed_items.append(item)   # saved removed items to be displayed 
            del current_order[item]

    if len(removed_items) > 0: # if there's some items in the removed dict
        fulfillment_text = f'Removed {", ".join(removed_items)} from your order.'

    if len(doesnt_exist) > 0:    # if some items exist in the doesnt_exist dict
        fulfillment_text = f'These items do not exist in your current order: {", ".join(doesnt_exist)}.'

    if not current_order.keys():    
        fulfillment_text += "Your order in empty."
    else:
        order_str = functions.get_str_food_dict(current_order)
        fulfillment_text += f'This is what you have left in your order: {order_str}.'

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })



def insert_to_db(order: dict):
    next_order_ID = db.get_next_order_ID()

    for food_item, quantity in order.items():
        r_code = db.insert_order_item(
            food_item,
            quantity,
            next_order_ID
        )

        if r_code == -1:
            return -1
        
    db.insert_order_tracking(next_order_ID, "In progress.") #insert tracking order in the database
    return next_order_ID


def complete_order(param: dict, session_ID: str): # using a function to insert order into the database
    if session_ID not in inprogress_orders:
        fulfillment_text = "Order not received, please place your order again."

    else:
        order = inprogress_orders[session_ID]
        order_id = insert_to_db(order)

        if order_id == -1:
            fulfillment_text = "Order not processed, please try again."
        
        else:
            total_cost = db.get_order_total(order_id)
            fulfillment_text = f"Awesome, your order has been placed."\
                                 f"Your order ID is # {order_id}." \
                                 f"Your total is ${total_cost}." 
        
        del inprogress_orders[session_ID] # this removes the data from inprogress dict making it empty for the next order

    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })


def track_order(param: dict, session_ID: str): # takes a dictionary as a parameter
    order_id = int(param['number']) # this will be in the json response Diagnostic info from diagflow
    order_status = db.get_order_status(order_id) # pass order_id as a param to the function 

    if order_status:
        fulfillment_text = f"Your order is {order_status}"
    else:
        fulfillment_text = f"There is no order associated with the provided ID. Please check the ID again."


    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

# add store hours 
# find a way to clear the dict when an order is incomplete and new order is typed. 