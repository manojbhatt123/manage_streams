"""
Command to open a stream listener to receive the data

command usage -
python manage.py receive_and_store_stream_data -s 1
"""
import logging
import os
import signal
from time import sleep

from django.core.management.base import BaseCommand
from dnaStreaming.listener import Listener
from fetch_stream.models import Stream

from receiver.utils import receive_and_store_stream_message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Stream listener to receive messages'

    def add_arguments(self, parser):
        parser.add_argument(
            "-s", "--stream_id", action="store",
            dest="stream_id", type=int, help=(
                "Stream primary key to initiate listener for specific stream"
            )
        )
        parser.add_argument(
            "-m", "--max_messages", action="store",
            dest="max_messages", type=int, default=500,
            help=(
                "max messages limit, only for synchronous listener"
            )
        )
        parser.add_argument(
            "-t", "--time_to_live", action="store",
            dest="time_to_live", type=int, default=50,
            help=(
                "Time to keep the listener alive, default is 50 minutes"
            )
        )
        parser.add_argument(
            "-a", "--async",
            action='store_true',
            help='Flag to trigger sync/async listener',
        )

    @staticmethod
    def terminate_process():
        """
        method to kill the current process to exit as the listener is not
        existing itself after call future.cancel or giving max message limit.

        this method will be removed once we find a way to exist from
        such processes.
        """
        # ToDo: Need to figure out a better way to exit
        current_process_id = os.getpid()
        for count in range(0, 10):
            sleep(1)

        logger.info(
            f'DowJonesStreamAPI: Kill process id: {current_process_id}'
        )
        os.kill(current_process_id, signal.SIGTERM)

    def handle(self, *args, **options):
        stream_id = options.get('stream_id')
        job_ttl = options.get('time_to_live')
        async_flag = options.get('async')
        max_messages_limit = options.get('max_messages')

        if not stream_id:
            logger.info(
                'DowJonesStreamAPI: Stream id is required. Exiting ...'
            )
            return

        query_params = {
            'active': True, 'id': stream_id
        }

        try:
            stream_obj = Stream.objects.select_related('account').get(
                **query_params
            )
            user_key = stream_obj.account.user_key
            subscription_id = stream_obj.subscription_id
        except Stream.DoesNotExist:
            logger.error(
                f'DowJonesStreamAPI: Active stream does not exist with '
                f'ID: {stream_id}. Exiting ...'
            )
            return
        except Exception as e:
            logger.error(
                f'DowJonesStreamAPI: Unknown error while starting DNA listener '
                f'for stream pk id: {stream_id}, Error: {e}'
            )
            return

        # lets initialize the Stream API listener
        listener = Listener(user_key=user_key)
        receive_and_store_stream_message.counter = 0
        receive_and_store_stream_message.max_message_limit = max_messages_limit
        receive_and_store_stream_message.stream_obj = stream_obj
        if async_flag:
            # let's listen async
            future = listener.listen_async(
                receive_and_store_stream_message,
                subscription_id=subscription_id
            )

            # keep open the listener for given ttl (50 minutes by default)
            for count in range(0, job_ttl * 60):
                sleep(1)

            # Close the listener and stop receiving messages after given ttl
            if future.running():
                future.cancel()

            logger.info(
                f'DowJonesStreamAPI: Listener closed!'
            )
        else:
            listener.listen(
                receive_and_store_stream_message,
                subscription_id=subscription_id,
                maximum_messages=max_messages_limit
            )
        logger.info(
            f'DowJonesStreamAPI: Total received messages: '
            f'{receive_and_store_stream_message.counter}'
        )
        self.terminate_process()
