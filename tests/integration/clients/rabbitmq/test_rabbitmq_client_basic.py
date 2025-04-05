import asyncio
import os
import uuid
import traceback
import logging
import json
import unittest
from typing import Dict, Any, List
from aio_pika.abc import AbstractIncomingMessage

# Import the RabbitMQClient
from rabbitmq_client import RabbitMQClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestRabbitMQClient(unittest.TestCase):
    """Test case for RabbitMQ client functionality."""
    
    async def asyncSetUp(self):
        """Set up test environment before each test."""
        self.rabbitmq_url = os.environ.get("RABBITMQ_URL", None)
        if not self.rabbitmq_url:
            raise ValueError("RABBITMQ_URL environment variable not set.")

        # Use test identifiers
        self.TEST_PREFIX = f"test_run_{uuid.uuid4().hex[:6]}"
        
        # Initialize RabbitMQ client
        self.client = RabbitMQClient(
            url=self.rabbitmq_url,
            connection_name=f"test-client-{self.TEST_PREFIX}"
        )
        
        # Connect to RabbitMQ
        await self.client.connect()
        
        # Track resources for cleanup
        self.test_queues = []
        self.test_exchanges = []
        
    async def asyncTearDown(self):
        """Clean up test environment after each test."""
        try:
            # Delete all test queues
            for queue_name in self.test_queues:
                await self.client.delete_queue(queue_name)
                logger.info(f"Deleted queue: {queue_name}")
            
            # Delete all test exchanges
            for exchange_name in self.test_exchanges:
                await self.client.delete_exchange(exchange_name)
                logger.info(f"Deleted exchange: {exchange_name}")
        finally:
            # Always close the client
            if self.client:
                await self.client.close()
                logger.info("RabbitMQ client closed.")
    
    async def test_rabbitmq_client(self):
        """Test the RabbitMQ client functionality."""
        logger.info(f"\n--- Starting RabbitMQ Client Test Run with Prefix: {self.TEST_PREFIX} ---")

        # --- Test Connection ---
        logger.info("\n--- Testing Connection ---")
        connected = await self.client.health_check()
        logger.info(f"Connection health check: {connected}")
        self.assertTrue(connected, "Health check failed!")
        
        # --- Test Queue and Exchange Declaration ---
        logger.info("\n--- Testing Queue and Exchange Declaration ---")
        
        # Declare test exchange
        exchange_name = f"{self.TEST_PREFIX}.exchange"
        exchange = await self.client.declare_exchange(exchange_name)
        self.test_exchanges.append(exchange_name)
        logger.info(f"Declared exchange: {exchange_name}")
        
        # Declare test queue
        queue_name = f"{self.TEST_PREFIX}.queue"
        queue = await self.client.declare_queue(queue_name)
        self.test_queues.append(queue_name)
        logger.info(f"Declared queue: {queue_name}")
        
        # Bind queue to exchange
        await self.client.bind_queue_to_exchange(queue_name, exchange_name, routing_key="test")
        logger.info(f"Bound queue '{queue_name}' to exchange '{exchange_name}' with routing key 'test'")
        
        # --- Test Message Publishing ---
        logger.info("\n--- Testing Message Publishing ---")
        
        # Publish a test message
        test_message = {
            "message_id": str(uuid.uuid4()),
            "content": "Hello, RabbitMQ!",
            "timestamp": "2023-01-01T12:00:00Z",
            "priority": "high"
        }
        
        await self.client.publish_message(
            exchange_name=exchange_name,
            routing_key="test",
            message=test_message,
            headers={"source": "test_client"},
        )
        logger.info(f"Published message to exchange '{exchange_name}' with routing key 'test'")
        
        # Get queue info to verify message count
        queue_info = await self.client.get_queue_info(queue_name)
        logger.info(f"Queue info after publishing: {queue_info}")
        self.assertGreater(queue_info["message_count"], 0, "Message not delivered to queue!")
        
        # --- Test Message Consumption ---
        logger.info("\n--- Testing Message Consumption ---")
        
        # Create a shared variable to store the received message
        received_messages = []
        
        # Define message handler
        async def message_handler(message: AbstractIncomingMessage):
            try:
                # Decode message body
                if message.content_type == 'application/json':
                    body = json.loads(message.body.decode())
                else:
                    body = message.body.decode()
                
                logger.info(f"Received message: {body}")
                received_messages.append(body)
                
                # Don't ack here, the wrapper will do it
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                raise
        
        # Start consuming
        consumer_tag = await self.client.consume(
            queue_name=queue_name,
            callback=message_handler,
            prefetch_count=1
        )
        logger.info(f"Started consuming from queue '{queue_name}' with tag '{consumer_tag}'")
        
        # Wait for message to be processed
        for _ in range(10):  # Wait up to 1 second
            if received_messages:
                break
            await asyncio.sleep(0.1)
        
        # Verify message was received
        logger.info(f"Received {len(received_messages)} messages")
        self.assertGreater(len(received_messages), 0, "Did not receive any messages!")
        self.assertEqual(received_messages[0]["content"], "Hello, RabbitMQ!", "Message content mismatch!")
        
        # Cancel consumer
        await self.client.cancel_consumer(consumer_tag)
        logger.info(f"Cancelled consumer with tag '{consumer_tag}'")
        
        # --- Test RPC Pattern ---
        logger.info("\n--- Testing RPC Pattern ---")
        
        # Create an RPC server (responds to messages)
        async def rpc_server():
            # Declare queue for RPC requests
            rpc_queue_name = f"{self.TEST_PREFIX}.rpc_queue"
            await self.client.declare_queue(rpc_queue_name)
            self.test_queues.append(rpc_queue_name)
            
            # Define RPC request handler
            async def rpc_handler(message: AbstractIncomingMessage):
                try:
                    # Parse request
                    if message.content_type == 'application/json':
                        request = json.loads(message.body.decode())
                    else:
                        request = message.body.decode()
                    
                    logger.info(f"RPC Server received request: {request}")
                    
                    # Create response
                    response = {
                        "result": f"Processed {request.get('data', 'unknown')}",
                        "status": "success"
                    }
                    
                    # Publish response to reply_to queue
                    if message.reply_to:
                        await self.client.publish_message(
                            exchange_name="",  # Default exchange
                            routing_key=message.reply_to,
                            message=response,
                            correlation_id=message.correlation_id
                        )
                        logger.info(f"RPC Server sent response to {message.reply_to}")
                    
                    # Acknowledge the message
                    await message.ack()
                    
                except Exception as e:
                    logger.error(f"Error in RPC handler: {e}")
                    await message.reject(requeue=False)
            
            # Start consuming RPC requests
            consumer_tag = await self.client.consume(
                queue_name=rpc_queue_name,
                callback=rpc_handler,
                prefetch_count=1,
                auto_ack=False
            )
            
            logger.info(f"RPC Server started, listening on '{rpc_queue_name}'")
            return rpc_queue_name, consumer_tag
        
        # Start RPC server
        rpc_queue_name, rpc_consumer_tag = await rpc_server()
        
        # Make RPC call
        rpc_request = {"data": "test_data", "timestamp": "2023-01-01T12:00:00Z"}
        
        rpc_response = await self.client.rpc_call(
            exchange_name="",  # Default exchange
            routing_key=rpc_queue_name,
            message=rpc_request,
            timeout=5.0
        )
        
        logger.info(f"RPC Client received response: {rpc_response}")
        self.assertIsNotNone(rpc_response, "RPC call returned no response!")
        self.assertEqual(rpc_response["status"], "success", "RPC call failed!")
        self.assertEqual(rpc_response["result"], "Processed test_data", "RPC response invalid!")
        
        # Cancel RPC server consumer
        await self.client.cancel_consumer(rpc_consumer_tag)
        
        # --- Test Advanced Patterns ---
        logger.info("\n--- Testing Advanced Patterns ---")
        
        # Test Dead Letter Queue
        dlq_queue, dlq_name = await self.client.setup_dlq(
            queue_name=f"{self.TEST_PREFIX}.dlq_test",
            dlq_suffix="_failed",
            max_retries=3
        )
        self.test_queues.extend([dlq_queue, dlq_name])
        self.test_exchanges.append(f"{dlq_queue}.dlx")
        logger.info(f"Set up DLQ: {dlq_queue} -> {dlq_name}")
        
        # Test Delayed Queue
        delay_exchange, delay_queue, target_queue = await self.client.setup_delayed_queue(
            queue_name=f"{self.TEST_PREFIX}.delayed_target",
            delay_ms=1000
        )
        self.test_queues.extend([delay_queue, target_queue])
        self.test_exchanges.append(delay_exchange)
        logger.info(f"Set up delayed queue: {delay_exchange} -> {delay_queue} -> {target_queue}")
        
        # Test Fanout
        fanout_exchange, fanout_queues = await self.client.setup_fanout(
            exchange_name=f"{self.TEST_PREFIX}.fanout",
            queue_prefix=f"{self.TEST_PREFIX}.fanout_worker",
            queue_count=3
        )
        self.test_queues.extend(fanout_queues)
        self.test_exchanges.append(fanout_exchange)
        logger.info(f"Set up fanout: {fanout_exchange} -> {fanout_queues}")
        
        logger.info("\n--- RabbitMQ Client Test Run Completed Successfully ---")

async def main():
    """Run the test case."""
    test = TestRabbitMQClient()
    try:
        await test.asyncSetUp()
        await test.test_rabbitmq_client()
    except Exception as e:
        logger.error(f"An unexpected error occurred during test run: {e}")
        logger.error(traceback.format_exc())
        raise e
    finally:
        await test.asyncTearDown()

if __name__ == "__main__":
    unittest.main()
    # asyncio.run(main())
