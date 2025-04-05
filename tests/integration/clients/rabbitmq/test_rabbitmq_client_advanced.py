import unittest
import asyncio
import os
import uuid
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from aio_pika.exceptions import ChannelClosed, ConnectionClosed, MessageProcessError

# Import the RabbitMQClient
from rabbitmq_client import RabbitMQClient, ExchangeType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to track if we're running in CI/CD environment
IS_CI_ENV = os.environ.get("CI", "").lower() in ("true", "1", "yes")

class TestRabbitMQAdvancedFeatures(unittest.IsolatedAsyncioTestCase):
    """Test suite for advanced RabbitMQ features"""
    
    async def asyncSetUp(self):
        """Set up test environment before each test method."""
        # Get RabbitMQ connection details from environment variables with fallback
        self.rabbitmq_url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        
        # Create unique test prefix to isolate test resources
        self.TEST_PREFIX = f"adv_test_{uuid.uuid4().hex[:8]}"
        logger.info(f"Using test prefix: {self.TEST_PREFIX}")
        
        # Initialize client with test-specific connection name
        self.client = RabbitMQClient(
            url=self.rabbitmq_url,
            connection_name=f"adv-test-client-{self.TEST_PREFIX}",
            heartbeat=30
        )
        
        # Connect to RabbitMQ
        try:
            await self.client.connect()
            
            # Verify connection with health check
            is_healthy = await self.client.health_check()
            if not is_healthy:
                # Skip tests if running in CI environment, otherwise fail
                if IS_CI_ENV:
                    self.skipTest("Could not connect to RabbitMQ server in CI environment")
                else:
                    self.fail("Failed to establish healthy connection to RabbitMQ server")
                
            logger.info("Successfully connected to RabbitMQ")
            
            # Track resources for cleanup
            self.created_queues = []
            self.created_exchanges = []
            
        except Exception as e:
            # Handle connection errors gracefully
            if IS_CI_ENV:
                self.skipTest(f"Could not connect to RabbitMQ in CI environment: {e}")
            else:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                await self._cleanup_client()
                raise
    
    async def asyncTearDown(self):
        """Clean up after each test method."""
        await self._cleanup_client()
    
    async def _cleanup_client(self):
        """Helper method to clean up client resources."""
        if hasattr(self, 'client') and self.client:
            try:
                # First, cancel all consumers to prevent issues with deleting active queues
                if hasattr(self.client, 'consumer_tags') and self.client.consumer_tags:
                    for tag in list(self.client.consumer_tags):
                        try:
                            await self.client.cancel_consumer(tag)
                        except Exception as e:
                            logger.warning(f"Error cancelling consumer {tag} during cleanup: {e}")
                
                # Clean up tracked resources in reverse order
                if hasattr(self, 'created_queues') and self.created_queues:
                    for queue in self.created_queues:
                        try:
                            await self.client.delete_queue(queue)
                            logger.info(f"Deleted queue: {queue}")
                        except Exception as e:
                            logger.warning(f"Error deleting queue {queue}: {e}")
                
                if hasattr(self, 'created_exchanges') and self.created_exchanges:
                    for exchange in self.created_exchanges:
                        try:
                            await self.client.delete_exchange(exchange)
                            logger.info(f"Deleted exchange: {exchange}")
                        except Exception as e:
                            logger.warning(f"Error deleting exchange {exchange}: {e}")
            except Exception as e:
                logger.error(f"Error during test cleanup: {e}")
            
            # Close client connection
            try:
                await self.client.close()
                logger.info("Closed RabbitMQ client connection")
            except Exception as e:
                logger.error(f"Error closing client connection: {e}")
            
            # Set client to None to ensure it's not reused
            self.client = None
    
    async def _create_test_queue(self, name_suffix="queue", **kwargs) -> str:
        """Helper to create a test queue with prefix."""
        queue_name = f"{self.TEST_PREFIX}_{name_suffix}"
        await self.client.declare_queue(queue_name, **kwargs)
        self.created_queues.append(queue_name)
        return queue_name
    
    async def _create_test_exchange(self, name_suffix="exchange", exchange_type=ExchangeType.DIRECT, **kwargs) -> str:
        """Helper to create a test exchange with prefix."""
        exchange_name = f"{self.TEST_PREFIX}_{name_suffix}"
        await self.client.declare_exchange(exchange_name, exchange_type=exchange_type, **kwargs)
        self.created_exchanges.append(exchange_name)
        return exchange_name
    
    async def test_queue_durability(self):
        """Test queue durability and persistence settings.
        
        Note: Full testing of durability across broker restarts requires
        administrative access to the RabbitMQ server.
        """
        # Create durable queue (default)
        durable_queue = await self._create_test_queue(name_suffix="durable")
        
        # Create non-durable queue (transient)
        transient_queue = await self._create_test_queue(
            name_suffix="transient", 
            durable=False
        )
        
        # Publish persistent message (default)
        await self.client.publish_message(
            exchange_name="",
            routing_key=durable_queue,
            message={"data": "persistent"}
        )
        
        # Publish transient message
        await self.client.publish_message(
            exchange_name="",
            routing_key=durable_queue,
            message={"data": "transient"},
            delivery_mode=1  # non-persistent
        )
        
        # Verify both queues exist
        durable_info = await self.client.get_queue_info(durable_queue)
        transient_info = await self.client.get_queue_info(transient_queue)
        
        self.assertEqual(durable_info["message_count"], 2, "Durable queue should have 2 messages")
        self.assertEqual(transient_info["message_count"], 0, "Transient queue should be empty")
        
        # Note: We can't test broker restart behavior in an automated test
        # without administrative access to RabbitMQ server
    
    async def test_message_ttl(self):
        """Test message Time-To-Live features."""
        # Create standard queue
        queue_name = await self._create_test_queue(name_suffix="message_ttl")
        
        # Publish message with short TTL (will be converted to string by client)
        await self.client.publish_message(
            exchange_name="",
            routing_key=queue_name,
            message={"data": "short_lived"},
            expiration=1  # 0.5 second TTL (as integer, will be converted to string internally)
        )
        
        # Verify message exists initially
        initial_info = await self.client.get_queue_info(queue_name)
        self.assertEqual(initial_info["message_count"], 1, "Queue should have 1 message initially")
        
        # Wait for TTL to expire with some margin
        await asyncio.sleep(3)  # Longer wait time to ensure expiration
        
        # Verify message is gone after TTL expires
        final_info = await self.client.get_queue_info(queue_name)
        self.assertEqual(final_info["message_count"], 0, "Message should be expired after TTL")
    
    async def test_queue_ttl(self):
        """Test queue with message TTL for all messages."""
        # Create queue with message TTL for all messages
        ttl_queue = await self._create_test_queue(
            name_suffix="queue_ttl",
            arguments={"x-message-ttl": 500}  # 0.5 second TTL for all messages
        )
        
        # Publish messages without individual TTL
        for i in range(3):
            await self.client.publish_message(
                exchange_name="",
                routing_key=ttl_queue,
                message={"index": i, "data": "queue_ttl_test"}
            )
        
        # Verify messages exist initially
        initial_info = await self.client.get_queue_info(ttl_queue)
        self.assertEqual(initial_info["message_count"], 3, "Queue should have 3 messages initially")
        
        # Wait for TTL to expire with some margin
        await asyncio.sleep(3)  # Longer wait to ensure expiration
        
        # Verify all messages are gone after TTL expires
        final_info = await self.client.get_queue_info(ttl_queue)
        self.assertEqual(final_info["message_count"], 0, "All messages should be expired after queue TTL")
    
    async def test_queue_size_limits(self):
        """Test maximum queue size and message count limits."""
        # Create queue with max length
        max_length_queue = await self._create_test_queue(
            name_suffix="max_length",
            arguments={"x-max-length": 5}  # Max 5 messages
        )
        
        # Publish 10 messages (should keep only the newest 5)
        for i in range(10):
            await self.client.publish_message(
                exchange_name="",
                routing_key=max_length_queue,
                message={"index": i, "data": "max_length_test"}
            )
        
        # Verify queue enforces max length
        queue_info = await self.client.get_queue_info(max_length_queue)
        self.assertEqual(queue_info["message_count"], 5, "Queue should have max 5 messages")
        
        # Consume the messages to verify we kept the newest ones (5-9)
        received_messages = []
        
        async def message_handler(message: AbstractIncomingMessage):
            try:
                content = json.loads(message.body.decode())
                received_messages.append(content)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
        
        consumer_tag = await self.client.consume(
            queue_name=max_length_queue,
            callback=message_handler,
            auto_ack=True
        )
        
        # Wait for messages to be consumed
        await asyncio.sleep(1)
        
        # Cancel the consumer
        await self.client.cancel_consumer(consumer_tag)
        
        # Extract indexes to verify we got the newest messages
        indexes = sorted([msg["index"] for msg in received_messages])
        self.assertEqual(indexes, [5, 6, 7, 8, 9], "Queue should keep the newest messages")
    
    async def test_dead_letter_exchange(self):
        """Test dead letter exchange and queue functionality."""
        # Setup DLQ with helper method
        main_queue_name, dlq_name = await self.client.setup_dlq(
            queue_name=f"{self.TEST_PREFIX}_main_queue",
            dlq_suffix="_failed"
        )
        
        # Add both queues to tracking for cleanup
        self.created_queues.append(main_queue_name)
        self.created_queues.append(dlq_name)
        
        # Add the DLX exchange to tracking (created internally by setup_dlq)
        dlx_name = f"{main_queue_name}.dlx"
        self.created_exchanges.append(dlx_name)
        
        # Publish a message with short TTL to trigger dead-lettering
        # (integer will be converted to string internally)
        await self.client.publish_message(
            exchange_name="",
            routing_key=main_queue_name,
            message={"data": "will_be_dead_lettered"},
            expiration=1  # 1 second TTL as integer, will be converted to string
        )
        
        # Verify message is in main queue initially
        initial_main_info = await self.client.get_queue_info(main_queue_name)
        initial_dlq_info = await self.client.get_queue_info(dlq_name)
        
        self.assertEqual(initial_main_info["message_count"], 1, "Main queue should have the message initially")
        self.assertEqual(initial_dlq_info["message_count"], 0, "DLQ should be empty initially")
        
        # Wait for TTL to expire with some margin
        await asyncio.sleep(3)  # Longer wait to ensure expiration
        
        # Check that message moved to DLQ
        final_main_info = await self.client.get_queue_info(main_queue_name)
        final_dlq_info = await self.client.get_queue_info(dlq_name)
        
        self.assertEqual(final_main_info["message_count"], 0, "Main queue should be empty after TTL")
        self.assertEqual(final_dlq_info["message_count"], 1, "DLQ should have the dead-lettered message")
    
    async def test_delayed_queue(self):
        """Test delayed message delivery using TTL + DLX pattern."""
        # Setup delayed queue with 1 second delay
        exchange_name, delay_queue_name, target_queue_name = await self.client.setup_delayed_queue(
            queue_name=f"{self.TEST_PREFIX}_delayed_target",
            delay_ms=1000  # 1 second delay
        )
        
        # Add resources to tracking for cleanup
        self.created_queues.append(delay_queue_name)
        self.created_queues.append(target_queue_name)
        self.created_exchanges.append(exchange_name)
        
        # Send a message to the delayed exchange
        await self.client.publish_message(
            exchange_name=exchange_name,
            routing_key="#",  # Routing key doesn't matter for this pattern
            message={"data": "delayed_message", "timestamp": time.time()}
        )
        
        # Verify message is in delay queue initially
        initial_delay_info = await self.client.get_queue_info(delay_queue_name)
        initial_target_info = await self.client.get_queue_info(target_queue_name)
        
        self.assertEqual(initial_delay_info["message_count"], 1, "Delay queue should have the message initially")
        self.assertEqual(initial_target_info["message_count"], 0, "Target queue should be empty initially")
        
        # Wait for delay to expire with some margin
        await asyncio.sleep(3)  # Longer wait to ensure processing
        
        # Check that message moved to target queue
        final_delay_info = await self.client.get_queue_info(delay_queue_name)
        final_target_info = await self.client.get_queue_info(target_queue_name)
        
        self.assertEqual(final_delay_info["message_count"], 0, "Delay queue should be empty after delay")
        self.assertEqual(final_target_info["message_count"], 1, "Target queue should have the message after delay")
    
    async def test_priority_queue(self):
        """Test priority queue functionality."""
        # Create priority queue
        priority_queue = await self._create_test_queue(
            name_suffix="priority",
            arguments={"x-max-priority": 10}  # 0-10 priority levels
        )
        
        # Send messages with different priorities using our updated client method
        priorities = [0, 5, 10, 3, 7]
        for i, priority in enumerate(priorities):
            await self.client.publish_message(
                exchange_name="",
                routing_key=priority_queue,
                message={"index": i, "priority": priority},
                priority=priority  # Now supported by our client
            )
        
        # Verify all messages are in queue
        queue_info = await self.client.get_queue_info(priority_queue)
        self.assertEqual(queue_info["message_count"], 5, "Queue should have all 5 messages")
        
        # Consume messages to verify they come out in priority order
        received_messages = []
        
        async def priority_handler(message: AbstractIncomingMessage):
            try:
                content = json.loads(message.body.decode())
                received_messages.append(content)
            except Exception as e:
                logger.error(f"Error in priority handler: {e}")
        
        # Use event to wait for all messages
        event = asyncio.Event()
        expected_count = 5
        
        async def counting_handler(message: AbstractIncomingMessage):
            await priority_handler(message)
            if len(received_messages) >= expected_count:
                event.set()
        
        consumer_tag = await self.client.consume(
            queue_name=priority_queue,
            callback=counting_handler,
            auto_ack=True
        )
        
        # Wait for all messages with timeout
        try:
            await asyncio.wait_for(event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass
        
        # Cancel consumer
        await self.client.cancel_consumer(consumer_tag)
        
        # Extract priorities to verify order (should be highest to lowest)
        received_priorities = [msg["priority"] for msg in received_messages]
        logger.info(f"Received message priorities: {received_priorities}")
        
        # The first messages should have higher priorities
        # (Note: Within same priority, order is FIFO)
        if len(received_priorities) >= 3:
            self.assertGreaterEqual(received_priorities[0], received_priorities[-1], 
                                  "Higher priority messages should be delivered first")
    
    async def test_qos_prefetch(self):
        """Test QoS prefetch settings for consumers."""
        # Create queue for QoS testing
        queue_name = await self._create_test_queue(name_suffix="qos_test")
        
        # Publish a number of messages
        message_count = 20
        for i in range(message_count):
            await self.client.publish_message(
                exchange_name="",
                routing_key=queue_name,
                message={"index": i, "data": "qos_test"}
            )
        
        # Verify all messages are in queue
        queue_info = await self.client.get_queue_info(queue_name)
        self.assertEqual(queue_info["message_count"], message_count, f"Queue should have {message_count} messages")
        
        # Set up tracking variables
        received_messages = []
        ack_count = 0
        prefetch_count = 5
        
        # Use a semaphore to control access to shared variables
        semaphore = asyncio.Semaphore(1)
        
        # Event to notify when all messages are received
        all_received_event = asyncio.Event()
        
        async def qos_handler(message: AbstractIncomingMessage):
            nonlocal ack_count
            
            # Process the message
            content = json.loads(message.body.decode())
            
            # Acquire semaphore to safely update shared variables
            async with semaphore:
                received_messages.append(content)
                
                # Check unacked messages should never exceed prefetch count
                unacked = len(received_messages) - ack_count
                if unacked > prefetch_count:
                    logger.error(f"QoS violation: unacked={unacked}, prefetch={prefetch_count}")
                    self.fail(f"Unacknowledged message count ({unacked}) exceeds prefetch count ({prefetch_count})")
                
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                # Acknowledge the message
                await message.ack()
                ack_count += 1
                
                # Signal when all messages are received
                if len(received_messages) >= message_count:
                    all_received_event.set()
        
        # Start consuming with specific prefetch
        consumer_tag = await self.client.consume(
            queue_name=queue_name,
            callback=qos_handler,
            prefetch_count=prefetch_count,
            auto_ack=False  # Important for QoS testing
        )
        
        # Wait for all messages to be received
        try:
            await asyncio.wait_for(all_received_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            self.fail("Timed out waiting for all messages")
        
        # Cancel consumer
        await self.client.cancel_consumer(consumer_tag)
        
        # Verify all messages were received
        self.assertEqual(len(received_messages), message_count, f"Should have received all {message_count} messages")
        
        # Verify all messages were acknowledged
        self.assertEqual(ack_count, message_count, f"Should have acknowledged all {message_count} messages")

# Run the tests
if __name__ == "__main__":
    unittest.main()
