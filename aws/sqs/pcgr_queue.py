#!/usr/bin/env python
import boto3

# Get the service resource
sqs = boto3.resource('sqs')

# Create the queue. This returns an SQS.Queue instance
queue = sqs.create_queue(QueueName='pcgr', Attributes={'DelaySeconds': '5'})

# You can now access identifiers and attributes
print(queue.url)
print(queue.attributes.get('DelaySeconds'))


for message in queue.receive_messages(MessageAttributeNames=['sample']):
    sample = ''
    if message.message_attributes is not None:
        sample_name = message.message_attributes.get('sample').get('StringValue')
        if sample_name:
            sample = ' ({0})'.format(sample_name)

    print('{0}{1}'.format(message.body, sample))

    message.delete()
