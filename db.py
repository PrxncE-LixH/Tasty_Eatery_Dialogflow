import mysql.connector
global cnx

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='tasty_eatery' 
)

def get_order_status(order_id: int):
    # Get the status of a specific order by its ID.from db

    #create a cursor object
    cursor = cnx.cursor()

    # query
    query = ("SELECT status FROM order_tracking WHERE order_id = %s")

    #execute the query
    cursor.execute(query, (order_id, )) 

    #fectch results
    results = cursor.fetchone()

    #close connection
    cursor.close()

    if results is not None:
        return results[0]
    else:
        return None
    

def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()

    # Inserting the record into the order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))

    # Committing the changes
    cnx.commit()

    # Closing the cursor
    cursor.close()


def get_next_order_ID(): # get the next order ID from db
    cursor = cnx.cursor()

    # query
    query = ("SELECT MAX(order_id) from orders")
    cursor.execute(query) 

    #fetch results
    results = cursor.fetchone()[0]

    #close the cursor
    cursor.close()

    # return the order id
    if results is None:
        return 1
    else:
        return results + 1 

def get_order_total(order_id):
    cursor =  cnx.cursor()

    # query
    query = f"SELECT get_total_order_price({order_id})" # this os a procedure(function) already written in the db
    cursor.execute(query) 

    #fetch results
    results = cursor.fetchone()[0]

    #close the cursor
    cursor.close()

    return results



def insert_order_item(food_items, quantity, order_id):
    try:
        cursor =  cnx.cursor()

        #calling the store procedure 
        cursor.callproc('insert_order_item', (food_items, quantity, order_id ))

        cnx.commit() # commit changes

        cursor.close()

        print("Order inserted successfully.")
        return 1
    
    except mysql.connector.Error as err:
        print("An error occurred: {}".format(err))

        #rollback changes
        cnx.rollback()
        return -1
    
    except Exception as e:
        print("An error occurred: ", {e})

        #rollback changes
        cnx.rollback()
        return -1



