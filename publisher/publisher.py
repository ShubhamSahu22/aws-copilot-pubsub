# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# -------------       Imports      ------------------------
from flask import Flask, request, render_template, redirect, url_for
import os
import sys
import json
import uuid
import boto3
import names
import random
import logging

# ------------       Global Config        -----------------
app = Flask(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
aws_region = os.getenv("AWS_DEFAULT_REGION", 'eu-west-1')

# ------------    SNS (Message sending)     ---------------
sns_client = boto3.client('sns', region_name=aws_region)
sns_topics_arn = json.loads(os.getenv("COPILOT_SNS_TOPIC_ARNS", '{}'))
dest_topic_name = 'ordersTopic'

# Validate that the required SNS topic exists
if dest_topic_name not in sns_topics_arn:
    raise ValueError(f"Topic '{dest_topic_name}' not found in COPILOT_SNS_TOPIC_ARNS.")
    
topic_arn = sns_topics_arn[dest_topic_name]

# ---------    DynamoDB (NoSQL Database)     --------------
dynamodb = boto3.resource('dynamodb', region_name=aws_region)
table_name = os.getenv("ORDERS_TABLE_NAME")

if not table_name:
    raise ValueError("ORDERS_TABLE_NAME environment variable is not set.")

db_table = dynamodb.Table(table_name)

# ----------        Main Page         ---------------------
@app.route('/', methods=["GET", "POST"])
def submit_order():
    # When "Send" button is clicked
    if request.method == 'POST':
        try:
            # Generate an Id
            order_id = str(uuid.uuid4())
            
            # Get data from the form
            customer = request.form['customer']
            amount = float(request.form['amount'])
            
            if amount < 0:
                raise ValueError("Amount must be a positive number.")
            
            # Save the data to DynamoDB Table
            db_table.put_item(
                Item={
                    'id': order_id,
                    'customer': customer,
                    'amount': amount,
                }
            )
            logging.info(f'Request saved in database with ID: {order_id}')
            
            # Send a message to the SNS topic
            sns_client.publish(
                TargetArn=topic_arn,
                Message=json.dumps({
                    'customer': customer,
                    'amount': amount,
                }),
                MessageAttributes={
                    'amount': {
                        'DataType': 'Number',
                        'StringValue': str(amount)
                    }
                }
            )
            logging.info(f'Message sent to SNS topic: {topic_arn}')
            
            # Redirect to the request page
            return redirect(url_for('request_page', request_id=order_id))
        
        except ValueError as ve:
            logging.error(f"Value error: {ve}")
            return render_template('index.html', error=str(ve), customer=customer, amount=amount)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return render_template('index.html', error="An error occurred. Please try again later.", customer=customer, amount=amount)

    # Generate a random name and amount to prepopulate the text box
    name = names.get_full_name()
    amount = round(random.uniform(0, 100), 2)
    
    return render_template('index.html', customer=name, amount=amount)

# ------------      Request Redirection Page      -------------------
@app.route('/request/<uuid:request_id>')
def request_page(request_id):
    try:
        response = db_table.get_item(
            Key={'id': str(request_id)}
        )
        # Check if the item exists
        if 'Item' not in response:
            return f"Order with ID {request_id} not found.", 404
        
        return render_template('order.html', response=response['Item'])

    except Exception as e:
        logging.error(f"Error retrieving order with ID {request_id}: {e}")
        return "Failed to retrieve order. Please try again later.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
