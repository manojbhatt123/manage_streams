"""
module contains utility functions related to receiver app
"""
import logging

from django.db import IntegrityError, DatabaseError
from fetch_stream.models import StreamMessage, StreamMessageAction

logger = logging.getLogger(__name__)

SUPPORTED_MESSAGE_ACTIONS = [
    action_item.value for action_item in StreamMessageAction
]


def receive_and_store_stream_message(message, subscription_id):
    """
    Method to process messages received by stream API Listener

    Args:
        message (dict): dict of article data
        subscription_id (str): stream subscription_id
    """
    if hasattr(receive_and_store_stream_message, 'counter'):
        receive_and_store_stream_message.counter += 1

    stream_obj = getattr(receive_and_store_stream_message, 'stream_obj', None)
    if not stream_obj:
        logger.exception(
            f'DowJonesStreamAPI: Stream Obj missing, '
            f'subscription_id: {subscription_id}, message: {message}'
        )
        return False

    try:
        message_action = message['action']
        accession_no = message['an']
        if message_action in SUPPORTED_MESSAGE_ACTIONS:
            try:
                message_obj, created = StreamMessage.objects.get_or_create(
                    message_id=accession_no, action=message_action,
                    stream=stream_obj
                )
                if created:
                    message_obj.stream = stream_obj
                    message_obj.raw_message_dict = message
                    message_obj.save()
                    logger.info(
                        f'DowJonesStreamAPI: Created new message with '
                        f'ID: {message_obj.id}, an: {accession_no}, '
                        f'action: {message_action}'
                    )
                else:
                    logger.info(
                        f'DowJonesStreamAPI: Message already exists with '
                        f'ID: {message_obj.id} with an: {accession_no} '
                        f'and action: {message_action}'
                    )
            except IntegrityError:
                logger.info(
                    f'DowJonesStreamAPI: Duplicate message with '
                    f'an: {accession_no} and action: {message_action}'
                )
            except DatabaseError as e:
                logger.info(
                    f'DowJonesStreamAPI: Unknown database error, '
                    f'an: {accession_no}, action: {message_action}, Error: {e}'
                )
        else:
            logger.info(
                f"DowJonesStreamAPI: Unknown message action "
                f"received: {message_action}, accession_no: {accession_no}"
            )
        return True
    except Exception as e:
        logger.exception(
            'DowJonesStreamAPI: Error in processing the message for '
            'subscription_id: {}, Error: {}, message_dict: {}'.format(
                subscription_id, e, message
            )
        )
