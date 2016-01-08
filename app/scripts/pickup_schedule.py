import json
from app import mysql
from app.models import Utils
from app.models import Mailer
from app.models import Order
from app.models import User
from app.models import Lend

def pickupSchedule():
    date = Utils.getCurrentTimestamp().split(' ')[0]

    # Order Pickup
    order_list = []
    cursor = mysql.connect().cursor()
    cursor.execute("""SELECT o.order_id 
        FROM orders o
        WHERE DATE(o.order_return) = %s""",
        (date,))
    order_ids = cursor.fetchall()
    all_time_slots = Order.getTimeSlot()

    for order_id in order_ids:
        order = Order(int(order_id[0]))
        order_info = order.getOrderInfo()

        user = User(order_info['user_id'])
        order_info['user'] = user.getObj()

        order_info['pickup_slot'] = [ts for ts in all_time_slots if ts['slot_id'] == order_info['pickup_slot']][0]

        # check if item is in inventory
        cursor.execute("""SELECT isbn_13 FROM inventory WHERE inventory_id = %d"""%(order_info['inventory_id']))
        order_info['isbn_13'] = cursor.fetchone()[0]
        order_list.append(order_info)
    
    if order_list:
        pickups = json.dumps({'orders': order_list}, indent=4)
        Mailer.genericMailer({'subject':'Pickups for '+date, 'body': pickups})

    '''
    # Rentals delivery
    rental_list = []
    cursor = mysql.connect().cursor()
    cursor.execute("""SELECT l.lender_id,
        u.name, u.phone,
        ua.address,
        i.item_id, i.item_name, i.author,
        l.status_id, l.delivery_date, l.delivery_slot,
        iv.inventory_id, iv.isbn_13, iv.item_condition
        FROM lenders l
        INNER JOIN users u ON l.user_id = u.user_id
        INNER JOIN user_addresses ua ON ua.address_id = l.address_id
        INNER JOIN inventory iv ON iv.inventory_id = l.inventory_id
        INNER JOIN items i ON i.item_id = iv.item_id
        WHERE DATE(l.delivery_date) = %s""",
        (date,))
    raw_data = cursor.fetchall()
    rental_list = []
    all_time_slots = Order.getTimeSlot()
    for row in raw_data:
        rental = {}
        rental['order_id'] = row[0]
        rental['user'] = {
                'name': row[1],
                'phone': row[2],
                'address' :row[3]
                }
        rental['item'] = {
                'item_id': row[4],
                'item_name': row[5],
                'author': row[6],
                'inventory_id': row[10],
                'isbn_13': row[11],
                'item_condition': row[12]
                }
        rental['delivery_slot'] = [ts for ts in all_time_slots if ts['slot_id'] == row[9]][0]
        rental_list.append(rental) 
   
    if rental_list:
        deliveries = json.dumps({'rentals': rental_list}, indent=4)
        Mailer.genericMailer({'subject':'Rental deliveries for '+date, 'body': deliveries})
    '''
    return None