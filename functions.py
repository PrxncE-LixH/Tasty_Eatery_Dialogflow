import re

def get_session_ID(session_str: str):  # regex to match session id from diagflow json response
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)

    if match:
        extracted_str = match.group(1)
        return extracted_str
    
    return ""

def get_str_food_dict(food_dict: dict):     # 
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])


#if __name__=="__main__":
    # Testing the functions below with some example inputs
    #print(get_str_food_dict({"samosa":2, "pizza": 2}))