# Workflow Run Logs - Run ID: 96130334-1e84-48d7-9734-4d453b79b042

## Log Summary

| Log Level | Count |
|-----------|-------|
| DEBUG | 0 |
| INFO | 79 |
| WARNING | 2 |
| ERROR | 19 |
| CRITICAL | 0 |

## ⚠️ Critical Messages and Errors

### Error Messages

**[2025-10-02T10:28:19.292583Z]** <span style='color:red'>ERROR</span>

`Process for flow run 'test_on_demand_external_research_workflow:--96130334-1e84-48d7-9734-4d453b79b042' exited with status code: 1`

**[2025-10-02T10:28:19.125073Z]** <span style='color:red'>ERROR</span>

`Process for flow run 'test_on_demand_external_research_workflow:--96130334-1e84-48d7-9734-4d453b79b042' exited with status code: 1`

**[2025-10-02T10:28:18.304669Z]** <span style='color:red'>ERROR</span>

`Finished in state Failed("Flow run encountered an exception: UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value")`

**[2025-10-02T10:28:18.288872Z]** <span style='color:red'>ERROR</span>

```
Encountered exception during execution: UnboundLocalError("cannot access local variable 'state_update' where it is not associated with a value")
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1359, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1421, in run_flow_async
    await engine.call_flow_fn()
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1373, in call_flow_fn
    result = await call_with_parameters(self.flow.fn, self.parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 196, in workflow_execution_flow
    raise e # Re-raise the original error
    ^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 171, in workflow_execution_flow
    workflow_run_update_result = await run_graph(
                                 ^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 822, in run_graph
    raise graph_exec_err
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**[2025-10-02T10:28:18.265482Z]** <span style='color:red'>ERROR</span>

```
Graph execution failed for Workflow name test_on_demand_external_research_workflow - Run ID 96130334-1e84-48d7-9734-4d453b79b042: cannot access local variable 'state_update' where it is not associated with a value
Traceback (most recent call last):
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**[2025-10-02T10:28:18.262063Z]** <span style='color:red'>ERROR</span>

`Finished in state TimedOut('Task run exceeded timeout of 3600.0 second(s)', type=FAILED)`

**[2025-10-02T10:28:18.261652Z]** <span style='color:red'>ERROR</span>

`Task run exceeded timeout of 3600.0 second(s)`

**[2025-10-02T10:28:18.255957Z]** <span style='color:red'>ERROR</span>

```
Task run failed with exception: TaskRunTimeoutError('Scope timed out after 3600.0 second(s).') - No retries configured for this task.
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 271, in async_receive_data
    done, pending = await asyncio.wait(
                    ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 30, in timeout_async
    yield
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1439, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1518, in run_task_async
    await engine.call_task_fn(txn)
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1456, in call_task_fn
    result = await call_with_parameters(self.task.fn, parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 646, in process_retry_wrapper
    return await self.process(input_data, config, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/db/customer_data.py", line 844, in process
    doc_metadata = await customer_data_service.get_document_metadata(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/kiwi_app/workflow_app/service_customer_data.py", line 2065, in get_document_metadata
    document = await self.versioned_mongo_client.client.fetch_object(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 1078, in fetch_object
    collection = await self._get_collection()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 140, in _get_collection
    await self._client.admin.command('ping')
  File "/usr/local/lib/python3.12/site-packages/pymongo/_csot.py", line 109, in csot_wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 932, in command
    return await self._command(
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 770, in _command
    return await conn.command(
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/helpers.py", line 47, in inner
    return await func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 564, in command
    self._raise_connection_failure(error)
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 536, in command
    return await command(
           ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 203, in command
    reply = await receive_message(conn, request_id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 335, in receive_message
    data = await async_receive_data(conn, length - 16, deadline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 286, in async_receive_data
    await asyncio.wait(tasks)
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError: <object object at 0xffff5ce0ef80>

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1429, in run_context
    with timeout_async(
         ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 32, in timeout_async
    raise timeout_exc_type(f"Scope timed out after {seconds} second(s).")
prefect.task_engine.TaskRunTimeoutError: Scope timed out after 3600.0 second(s).
```

**[2025-10-02T10:28:18.072136Z]** <span style='color:red'>ERROR</span>

`Finished in state Failed("Flow run encountered an exception: UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value")`

**[2025-10-02T10:28:18.054720Z]** <span style='color:red'>ERROR</span>

```
Encountered exception during execution: UnboundLocalError("cannot access local variable 'state_update' where it is not associated with a value")
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1359, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1421, in run_flow_async
    await engine.call_flow_fn()
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1373, in call_flow_fn
    result = await call_with_parameters(self.flow.fn, self.parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 196, in workflow_execution_flow
    raise e # Re-raise the original error
    ^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 171, in workflow_execution_flow
    workflow_run_update_result = await run_graph(
                                 ^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 822, in run_graph
    raise graph_exec_err
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**[2025-10-02T10:28:18.034196Z]** <span style='color:red'>ERROR</span>

```
Graph execution failed for Workflow name test_on_demand_external_research_workflow - Run ID 96130334-1e84-48d7-9734-4d453b79b042: cannot access local variable 'state_update' where it is not associated with a value
Traceback (most recent call last):
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**[2025-10-02T10:28:18.031141Z]** <span style='color:red'>ERROR</span>

`Finished in state TimedOut('Task run exceeded timeout of 3600.0 second(s)', type=FAILED)`

**[2025-10-02T10:28:18.030629Z]** <span style='color:red'>ERROR</span>

`Task run exceeded timeout of 3600.0 second(s)`

**[2025-10-02T10:28:18.028496Z]** <span style='color:red'>ERROR</span>

```
Task run failed with exception: TaskRunTimeoutError('Scope timed out after 3600.0 second(s).') - No retries configured for this task.
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 271, in async_receive_data
    done, pending = await asyncio.wait(
                    ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 30, in timeout_async
    yield
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1439, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1518, in run_task_async
    await engine.call_task_fn(txn)
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1456, in call_task_fn
    result = await call_with_parameters(self.task.fn, parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 646, in process_retry_wrapper
    return await self.process(input_data, config, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/db/customer_data.py", line 844, in process
    doc_metadata = await customer_data_service.get_document_metadata(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/kiwi_app/workflow_app/service_customer_data.py", line 2065, in get_document_metadata
    document = await self.versioned_mongo_client.client.fetch_object(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 1078, in fetch_object
    collection = await self._get_collection()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 140, in _get_collection
    await self._client.admin.command('ping')
  File "/usr/local/lib/python3.12/site-packages/pymongo/_csot.py", line 109, in csot_wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 932, in command
    return await self._command(
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 770, in _command
    return await conn.command(
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/helpers.py", line 47, in inner
    return await func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 564, in command
    self._raise_connection_failure(error)
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 536, in command
    return await command(
           ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 203, in command
    reply = await receive_message(conn, request_id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 335, in receive_message
    data = await async_receive_data(conn, length - 16, deadline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 286, in async_receive_data
    await asyncio.wait(tasks)
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError: <object object at 0xffff3d0bbbc0>

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1429, in run_context
    with timeout_async(
         ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 32, in timeout_async
    raise timeout_exc_type(f"Scope timed out after {seconds} second(s).")
prefect.task_engine.TaskRunTimeoutError: Scope timed out after 3600.0 second(s).
```

**[2025-10-02T10:27:47.563297Z]** <span style='color:red'>ERROR</span>

```
Encountered exception during execution: UnboundLocalError("cannot access local variable 'state_update' where it is not associated with a value")
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1359, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1421, in run_flow_async
    await engine.call_flow_fn()
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1373, in call_flow_fn
    result = await call_with_parameters(self.flow.fn, self.parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 196, in workflow_execution_flow
    raise e # Re-raise the original error
    ^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 171, in workflow_execution_flow
    workflow_run_update_result = await run_graph(
                                 ^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 822, in run_graph
    raise graph_exec_err
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**[2025-10-02T10:27:47.542193Z]** <span style='color:red'>ERROR</span>

```
Graph execution failed for Workflow name test_on_demand_external_research_workflow - Run ID 96130334-1e84-48d7-9734-4d453b79b042: cannot access local variable 'state_update' where it is not associated with a value
Traceback (most recent call last):
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**[2025-10-02T10:27:47.533254Z]** <span style='color:red'>ERROR</span>

`Finished in state TimedOut('Task run exceeded timeout of 3600.0 second(s)', type=FAILED)`

**[2025-10-02T10:27:47.532886Z]** <span style='color:red'>ERROR</span>

`Task run exceeded timeout of 3600.0 second(s)`

**[2025-10-02T10:27:47.526371Z]** <span style='color:red'>ERROR</span>

```
Task run failed with exception: TaskRunTimeoutError('Scope timed out after 3600.0 second(s).') - No retries configured for this task.
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 271, in async_receive_data
    done, pending = await asyncio.wait(
                    ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 30, in timeout_async
    yield
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1439, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1518, in run_task_async
    await engine.call_task_fn(txn)
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1456, in call_task_fn
    result = await call_with_parameters(self.task.fn, parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 646, in process_retry_wrapper
    return await self.process(input_data, config, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/db/customer_data.py", line 844, in process
    doc_metadata = await customer_data_service.get_document_metadata(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/kiwi_app/workflow_app/service_customer_data.py", line 2065, in get_document_metadata
    document = await self.versioned_mongo_client.client.fetch_object(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 1078, in fetch_object
    collection = await self._get_collection()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 140, in _get_collection
    await self._client.admin.command('ping')
  File "/usr/local/lib/python3.12/site-packages/pymongo/_csot.py", line 109, in csot_wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 932, in command
    return await self._command(
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 770, in _command
    return await conn.command(
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/helpers.py", line 47, in inner
    return await func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 564, in command
    self._raise_connection_failure(error)
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 536, in command
    return await command(
           ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 203, in command
    reply = await receive_message(conn, request_id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 335, in receive_message
    data = await async_receive_data(conn, length - 16, deadline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 286, in async_receive_data
    await asyncio.wait(tasks)
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError: <object object at 0xffff3d0baa50>

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1429, in run_context
    with timeout_async(
         ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 32, in timeout_async
    raise timeout_exc_type(f"Scope timed out after {seconds} second(s).")
prefect.task_engine.TaskRunTimeoutError: Scope timed out after 3600.0 second(s).
```

---

## ⚠️ Warning Messages

**[2025-10-02T10:28:18.197466Z]** <span style='color:orange'>WARNING</span>

```
 #### RETRY DETECTED for workflow run! ####


```

**[2025-10-02T10:28:17.997443Z]** <span style='color:orange'>WARNING</span>

```
 #### RETRY DETECTED for workflow run! ####


```

---

## Complete Log (Chronological Order)

### <span style='color:red'>Log Entry 1</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:19.292583Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Process for flow run 'test_on_demand_external_research_workflow:--96130334-1e84-48d7-9734-4d453b79b042' exited with status code: 1`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 2</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:19.125073Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Process for flow run 'test_on_demand_external_research_workflow:--96130334-1e84-48d7-9734-4d453b79b042' exited with status code: 1`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 3</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.304669Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Finished in state Failed("Flow run encountered an exception: UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value")`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 4</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.288872Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Encountered exception during execution: UnboundLocalError("cannot access local variable 'state_update' where it is not associated with a value")
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1359, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1421, in run_flow_async
    await engine.call_flow_fn()
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1373, in call_flow_fn
    result = await call_with_parameters(self.flow.fn, self.parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 196, in workflow_execution_flow
    raise e # Re-raise the original error
    ^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 171, in workflow_execution_flow
    workflow_run_update_result = await run_graph(
                                 ^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 822, in run_graph
    raise graph_exec_err
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 5

**Timestamp:** 2025-10-02T10:28:18.288762Z

**Level:** INFO

**Message:**

`External context manager closed successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 6

**Timestamp:** 2025-10-02T10:28:18.288601Z

**Level:** INFO

**Message:**

`External context manager resources closed successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 7

**Timestamp:** 2025-10-02T10:28:18.282193Z

**Level:** INFO

**Message:**

`Closing external context manager resources...`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 8

**Timestamp:** 2025-10-02T10:28:18.281624Z

**Level:** INFO

**Message:**

`Published final status update event (failed) for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 9

**Timestamp:** 2025-10-02T10:28:18.275862Z

**Level:** INFO

**Message:**

`Published final status update event (failed) for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 10

**Timestamp:** 2025-10-02T10:28:18.274654Z

**Level:** INFO

**Message:**

`Persisted event WorkflowEvent.WORKFLOW_RUN_STATUS (RunID: 96130334-1e84-48d7-9734-4d453b79b042, SeqID: 1) to MongoDB.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 11

**Timestamp:** 2025-10-02T10:28:18.272871Z

**Level:** INFO

**Message:**

`Updated final status (failed) and outputs in DB for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 12</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.265482Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Graph execution failed for Workflow name test_on_demand_external_research_workflow - Run ID 96130334-1e84-48d7-9734-4d453b79b042: cannot access local variable 'state_update' where it is not associated with a value
Traceback (most recent call last):
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 13</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.262063Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Finished in state TimedOut('Task run exceeded timeout of 3600.0 second(s)', type=FAILED)`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 14</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.261652Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Task run exceeded timeout of 3600.0 second(s)`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 15</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.255957Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Task run failed with exception: TaskRunTimeoutError('Scope timed out after 3600.0 second(s).') - No retries configured for this task.
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 271, in async_receive_data
    done, pending = await asyncio.wait(
                    ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 30, in timeout_async
    yield
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1439, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1518, in run_task_async
    await engine.call_task_fn(txn)
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1456, in call_task_fn
    result = await call_with_parameters(self.task.fn, parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 646, in process_retry_wrapper
    return await self.process(input_data, config, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/db/customer_data.py", line 844, in process
    doc_metadata = await customer_data_service.get_document_metadata(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/kiwi_app/workflow_app/service_customer_data.py", line 2065, in get_document_metadata
    document = await self.versioned_mongo_client.client.fetch_object(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 1078, in fetch_object
    collection = await self._get_collection()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 140, in _get_collection
    await self._client.admin.command('ping')
  File "/usr/local/lib/python3.12/site-packages/pymongo/_csot.py", line 109, in csot_wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 932, in command
    return await self._command(
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 770, in _command
    return await conn.command(
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/helpers.py", line 47, in inner
    return await func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 564, in command
    self._raise_connection_failure(error)
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 536, in command
    return await command(
           ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 203, in command
    reply = await receive_message(conn, request_id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 335, in receive_message
    data = await async_receive_data(conn, length - 16, deadline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 286, in async_receive_data
    await asyncio.wait(tasks)
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError: <object object at 0xffff5ce0ef80>

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1429, in run_context
    with timeout_async(
         ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 32, in timeout_async
    raise timeout_exc_type(f"Scope timed out after {seconds} second(s).")
prefect.task_engine.TaskRunTimeoutError: Scope timed out after 3600.0 second(s).
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 16

**Timestamp:** 2025-10-02T10:28:18.253588Z

**Level:** INFO

**Message:**

`Finished in state Completed()`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 17

**Timestamp:** 2025-10-02T10:28:18.235368Z

**Level:** INFO

**Message:**

`load_additional_user_files_node: load_customer_data - Successfully parsed 1 load configurations from list at 'transformed_data'.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 18

**Timestamp:** 2025-10-02T10:28:18.234858Z

**Level:** INFO

**Message:**

`load_additional_user_files_node: load_customer_data - Attempting to load configurations dynamically from input path: transformed_data`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:orange'>Log Entry 19</span>

**<span style='color:orange'>Timestamp:</span>** 2025-10-02T10:28:18.197466Z

**Level:** <span style='color:orange'>WARNING</span>

**Message:**

```
 #### RETRY DETECTED for workflow run! ####


```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 20

**Timestamp:** 2025-10-02T10:28:18.189863Z

**Level:** INFO

**Message:**

`Updated Run 96130334-1e84-48d7-9734-4d453b79b042 status to RUNNING in DB.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 21

**Timestamp:** 2025-10-02T10:28:18.180413Z

**Level:** INFO

**Message:**

`Executing graph stream with input data: {'is_shared': False, 'namespace': 'external_research_reports_momentum_{item}', 'asset_name': 'healthcare_ai_2024', 'research_context': 'Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024. Focus on recent breakthroughs, adoption challenges, regulatory considerations, and future implications for medical professionals.', 'load_additional_user_files': [{'docname': 'ai_diagnostic_trends_2024', 'is_shared': False, 'namespace': 'research_context_files_momentum'}]}`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 22

**Timestamp:** 2025-10-02T10:28:18.180099Z

**Level:** INFO

**Message:**

`Graph compiled successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 23

**Timestamp:** 2025-10-02T10:28:18.098361Z

**Level:** INFO

**Message:**

`Graph entities built successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 24</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.072136Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Finished in state Failed("Flow run encountered an exception: UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value")`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 25

**Timestamp:** 2025-10-02T10:28:18.066922Z

**Level:** INFO

**Message:**

```


Creating dynamic schema class hitl_node__default_research_approval_OutputSchema with fields dict_keys(['user_action', 'revision_feedback', 'load_additional_user_files'])
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 26

**Timestamp:** 2025-10-02T10:28:18.065911Z

**Level:** INFO

**Message:**

```


Creating dynamic schema class input_node_input_node_OutputSchema with fields dict_keys(['docname', 'is_shared', 'namespace', 'asset_name', 'research_context', 'load_additional_user_files'])
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 27

**Timestamp:** 2025-10-02T10:28:18.064546Z

**Level:** INFO

**Message:**

`Building graph for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 28</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.054720Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Encountered exception during execution: UnboundLocalError("cannot access local variable 'state_update' where it is not associated with a value")
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1359, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1421, in run_flow_async
    await engine.call_flow_fn()
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1373, in call_flow_fn
    result = await call_with_parameters(self.flow.fn, self.parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 196, in workflow_execution_flow
    raise e # Re-raise the original error
    ^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 171, in workflow_execution_flow
    workflow_run_update_result = await run_graph(
                                 ^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 822, in run_graph
    raise graph_exec_err
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 29

**Timestamp:** 2025-10-02T10:28:18.054611Z

**Level:** INFO

**Message:**

`External context manager closed successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 30

**Timestamp:** 2025-10-02T10:28:18.054414Z

**Level:** INFO

**Message:**

`External context manager resources closed successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 31

**Timestamp:** 2025-10-02T10:28:18.049489Z

**Level:** INFO

**Message:**

`Info for Workflow run: Retry Count: #2 - Workflow Name: test_on_demand_external_research_workflow - Workflow ID: 1e6c659d-40d5-43a2-9209-6d5ee3b5706f - Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 32

**Timestamp:** 2025-10-02T10:28:18.048336Z

**Level:** INFO

**Message:**

`Closing external context manager resources...`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 33

**Timestamp:** 2025-10-02T10:28:18.047963Z

**Level:** INFO

**Message:**

`Published final status update event (failed) for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 34

**Timestamp:** 2025-10-02T10:28:18.043270Z

**Level:** INFO

**Message:**

`Published final status update event (failed) for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 35

**Timestamp:** 2025-10-02T10:28:18.042240Z

**Level:** INFO

**Message:**

`External context manager initialized`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 36

**Timestamp:** 2025-10-02T10:28:18.041909Z

**Level:** INFO

**Message:**

`RAG service initialized successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 37

**Timestamp:** 2025-10-02T10:28:18.039114Z

**Level:** INFO

**Message:**

`Persisted event WorkflowEvent.WORKFLOW_RUN_STATUS (RunID: 96130334-1e84-48d7-9734-4d453b79b042, SeqID: 1) to MongoDB.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 38

**Timestamp:** 2025-10-02T10:28:18.037712Z

**Level:** INFO

**Message:**

`Updated final status (failed) and outputs in DB for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 39</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.034196Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Graph execution failed for Workflow name test_on_demand_external_research_workflow - Run ID 96130334-1e84-48d7-9734-4d453b79b042: cannot access local variable 'state_update' where it is not associated with a value
Traceback (most recent call last):
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 40</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.031141Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Finished in state TimedOut('Task run exceeded timeout of 3600.0 second(s)', type=FAILED)`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 41</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.030629Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Task run exceeded timeout of 3600.0 second(s)`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 42</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:28:18.028496Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Task run failed with exception: TaskRunTimeoutError('Scope timed out after 3600.0 second(s).') - No retries configured for this task.
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 271, in async_receive_data
    done, pending = await asyncio.wait(
                    ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 30, in timeout_async
    yield
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1439, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1518, in run_task_async
    await engine.call_task_fn(txn)
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1456, in call_task_fn
    result = await call_with_parameters(self.task.fn, parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 646, in process_retry_wrapper
    return await self.process(input_data, config, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/db/customer_data.py", line 844, in process
    doc_metadata = await customer_data_service.get_document_metadata(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/kiwi_app/workflow_app/service_customer_data.py", line 2065, in get_document_metadata
    document = await self.versioned_mongo_client.client.fetch_object(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 1078, in fetch_object
    collection = await self._get_collection()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 140, in _get_collection
    await self._client.admin.command('ping')
  File "/usr/local/lib/python3.12/site-packages/pymongo/_csot.py", line 109, in csot_wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 932, in command
    return await self._command(
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 770, in _command
    return await conn.command(
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/helpers.py", line 47, in inner
    return await func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 564, in command
    self._raise_connection_failure(error)
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 536, in command
    return await command(
           ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 203, in command
    reply = await receive_message(conn, request_id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 335, in receive_message
    data = await async_receive_data(conn, length - 16, deadline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 286, in async_receive_data
    await asyncio.wait(tasks)
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError: <object object at 0xffff3d0bbbc0>

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1429, in run_context
    with timeout_async(
         ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 32, in timeout_async
    raise timeout_exc_type(f"Scope timed out after {seconds} second(s).")
prefect.task_engine.TaskRunTimeoutError: Scope timed out after 3600.0 second(s).
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 43

**Timestamp:** 2025-10-02T10:28:18.027061Z

**Level:** INFO

**Message:**

`Finished in state Completed()`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 44

**Timestamp:** 2025-10-02T10:28:18.013218Z

**Level:** INFO

**Message:**

`load_additional_user_files_node: load_customer_data - Successfully parsed 1 load configurations from list at 'transformed_data'.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 45

**Timestamp:** 2025-10-02T10:28:18.012892Z

**Level:** INFO

**Message:**

`load_additional_user_files_node: load_customer_data - Attempting to load configurations dynamically from input path: transformed_data`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:orange'>Log Entry 46</span>

**<span style='color:orange'>Timestamp:</span>** 2025-10-02T10:28:17.997443Z

**Level:** <span style='color:orange'>WARNING</span>

**Message:**

```
 #### RETRY DETECTED for workflow run! ####


```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 47

**Timestamp:** 2025-10-02T10:28:17.994035Z

**Level:** INFO

**Message:**

`Updated Run 96130334-1e84-48d7-9734-4d453b79b042 status to RUNNING in DB.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 48

**Timestamp:** 2025-10-02T10:28:17.985586Z

**Level:** INFO

**Message:**

`Executing graph stream with input data: {'is_shared': False, 'namespace': 'external_research_reports_momentum_{item}', 'asset_name': 'healthcare_ai_2024', 'research_context': 'Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024. Focus on recent breakthroughs, adoption challenges, regulatory considerations, and future implications for medical professionals.', 'load_additional_user_files': [{'docname': 'ai_diagnostic_trends_2024', 'is_shared': False, 'namespace': 'research_context_files_momentum'}]}`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 49

**Timestamp:** 2025-10-02T10:28:17.985240Z

**Level:** INFO

**Message:**

`Graph compiled successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 50

**Timestamp:** 2025-10-02T10:28:17.917212Z

**Level:** INFO

**Message:**

`Graph entities built successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 51

**Timestamp:** 2025-10-02T10:28:17.892435Z

**Level:** INFO

**Message:**

```


Creating dynamic schema class hitl_node__default_research_approval_OutputSchema with fields dict_keys(['user_action', 'revision_feedback', 'load_additional_user_files'])
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 52

**Timestamp:** 2025-10-02T10:28:17.891491Z

**Level:** INFO

**Message:**

```


Creating dynamic schema class input_node_input_node_OutputSchema with fields dict_keys(['docname', 'is_shared', 'namespace', 'asset_name', 'research_context', 'load_additional_user_files'])
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 53

**Timestamp:** 2025-10-02T10:28:17.890597Z

**Level:** INFO

**Message:**

`Building graph for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 54

**Timestamp:** 2025-10-02T10:28:17.883599Z

**Level:** INFO

**Message:**

`Info for Workflow run: Retry Count: #1 - Workflow Name: test_on_demand_external_research_workflow - Workflow ID: 1e6c659d-40d5-43a2-9209-6d5ee3b5706f - Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 55

**Timestamp:** 2025-10-02T10:28:17.880568Z

**Level:** INFO

**Message:**

`External context manager initialized`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 56

**Timestamp:** 2025-10-02T10:28:17.880321Z

**Level:** INFO

**Message:**

`RAG service initialized successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 57

**Timestamp:** 2025-10-02T10:28:17.617730Z

**Level:** INFO

**Message:**

`Starting workflow execution for Run ID: 96130334-1e84-48d7-9734-4d453b79b042, Workflow ID: 1e6c659d-40d5-43a2-9209-6d5ee3b5706f`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 58

**Timestamp:** 2025-10-02T10:28:17.616439Z

**Level:** INFO

**Message:**

`Beginning flow run 'test_on_demand_external_research_workflow:--96130334-1e84-48d7-9734-4d453b79b042' for flow 'workflow-execution'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 59

**Timestamp:** 2025-10-02T10:28:17.210836Z

**Level:** INFO

**Message:**

`Starting workflow execution for Run ID: 96130334-1e84-48d7-9734-4d453b79b042, Workflow ID: 1e6c659d-40d5-43a2-9209-6d5ee3b5706f`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 60

**Timestamp:** 2025-10-02T10:28:17.209852Z

**Level:** INFO

**Message:**

`Beginning flow run 'test_on_demand_external_research_workflow:--96130334-1e84-48d7-9734-4d453b79b042' for flow 'workflow-execution'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 61

**Timestamp:** 2025-10-02T10:28:13.393000Z

**Level:** INFO

**Message:**

`Downloading flow code from storage at '.'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 62

**Timestamp:** 2025-10-02T10:28:11.395015Z

**Level:** INFO

**Message:**

`Completed submission of flow run 'b8e28e5c-6052-44e1-a6e8-2461080bb984'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 63

**Timestamp:** 2025-10-02T10:28:11.385336Z

**Level:** INFO

**Message:**

`Opening process...`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 64

**Timestamp:** 2025-10-02T10:28:11.373731Z

**Level:** INFO

**Message:**

`Runner 'runner-25d32f5c-1fa7-4003-a9af-056f9ab5f47e' submitting flow run 'b8e28e5c-6052-44e1-a6e8-2461080bb984'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 65

**Timestamp:** 2025-10-02T10:27:47.585107Z

**Level:** INFO

**Message:**

`Received non-final state 'AwaitingRetry' when proposing final state 'Failed' and will attempt to run again...`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 66</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:27:47.563297Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Encountered exception during execution: UnboundLocalError("cannot access local variable 'state_update' where it is not associated with a value")
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1359, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1421, in run_flow_async
    await engine.call_flow_fn()
  File "/usr/local/lib/python3.12/site-packages/prefect/flow_engine.py", line 1373, in call_flow_fn
    result = await call_with_parameters(self.flow.fn, self.parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 196, in workflow_execution_flow
    raise e # Re-raise the original error
    ^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 171, in workflow_execution_flow
    workflow_run_update_result = await run_graph(
                                 ^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/services/worker.py", line 822, in run_graph
    raise graph_exec_err
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 67

**Timestamp:** 2025-10-02T10:27:47.563176Z

**Level:** INFO

**Message:**

`External context manager closed successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 68

**Timestamp:** 2025-10-02T10:27:47.562979Z

**Level:** INFO

**Message:**

`External context manager resources closed successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 69

**Timestamp:** 2025-10-02T10:27:47.557711Z

**Level:** INFO

**Message:**

`Closing external context manager resources...`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 70

**Timestamp:** 2025-10-02T10:27:47.557418Z

**Level:** INFO

**Message:**

`Published final status update event (failed) for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 71

**Timestamp:** 2025-10-02T10:27:47.548449Z

**Level:** INFO

**Message:**

`Published final status update event (failed) for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 72

**Timestamp:** 2025-10-02T10:27:47.547735Z

**Level:** INFO

**Message:**

`Persisted event WorkflowEvent.WORKFLOW_RUN_STATUS (RunID: 96130334-1e84-48d7-9734-4d453b79b042, SeqID: 4) to MongoDB.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 73

**Timestamp:** 2025-10-02T10:27:47.546768Z

**Level:** INFO

**Message:**

`Updated final status (failed) and outputs in DB for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 74</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:27:47.542193Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Graph execution failed for Workflow name test_on_demand_external_research_workflow - Run ID 96130334-1e84-48d7-9734-4d453b79b042: cannot access local variable 'state_update' where it is not associated with a value
Traceback (most recent call last):
  File "/app/services/workflow_service/services/worker.py", line 487, in run_graph
    async for chunk in adapter.aexecute_graph_stream(
  File "/app/services/workflow_service/graph/runtime/adapter.py", line 923, in aexecute_graph_stream
    async for chunk in graph.astream(current_input, config=lg_config, stream_mode=stream_modes):
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/main.py", line 2939, in astream
    async for _ in runner.atick(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 401, in atick
    _panic_or_proceed(
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_runner.py", line 511, in _panic_or_proceed
    raise exc
  File "/usr/local/lib/python3.12/site-packages/langgraph/pregel/_retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 706, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/langgraph/_internal/_runnable.py", line 474, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 733, in run
    raise e
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 668, in run
    if self.__class__.runtime_postprocessor and (not self.private_output_mode) and (not isinstance(state_update, (Command, Send, Interrupt))) and (not isinstance(output_data, (Command, Send, Interrupt))):
                                                                                                   ^^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'state_update' where it is not associated with a value
During task with name 'route_docname_check' and id '5684e418-be70-af84-c3bc-f1f69b3e38ca'
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 75</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:27:47.533254Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Finished in state TimedOut('Task run exceeded timeout of 3600.0 second(s)', type=FAILED)`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 76</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:27:47.532886Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

`Task run exceeded timeout of 3600.0 second(s)`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### <span style='color:red'>Log Entry 77</span>

**<span style='color:red'>Timestamp:</span>** 2025-10-02T10:27:47.526371Z

**Level:** <span style='color:red'>ERROR</span>

**Message:**

```
Task run failed with exception: TaskRunTimeoutError('Scope timed out after 3600.0 second(s).') - No retries configured for this task.
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 271, in async_receive_data
    done, pending = await asyncio.wait(
                    ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 30, in timeout_async
    yield
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1439, in run_context
    yield self
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1518, in run_task_async
    await engine.call_task_fn(txn)
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1456, in call_task_fn
    result = await call_with_parameters(self.task.fn, parameters)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/core/base.py", line 646, in process_retry_wrapper
    return await self.process(input_data, config, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/workflow_service/registry/nodes/db/customer_data.py", line 844, in process
    doc_metadata = await customer_data_service.get_document_metadata(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/services/kiwi_app/workflow_app/service_customer_data.py", line 2065, in get_document_metadata
    document = await self.versioned_mongo_client.client.fetch_object(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 1078, in fetch_object
    collection = await self._get_collection()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/libs/src/mongo_client/mongo_client_v2_secure.py", line 140, in _get_collection
    await self._client.admin.command('ping')
  File "/usr/local/lib/python3.12/site-packages/pymongo/_csot.py", line 109, in csot_wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 932, in command
    return await self._command(
           ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/database.py", line 770, in _command
    return await conn.command(
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/helpers.py", line 47, in inner
    return await func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 564, in command
    self._raise_connection_failure(error)
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/pool.py", line 536, in command
    return await command(
           ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 203, in command
    reply = await receive_message(conn, request_id)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/asynchronous/network.py", line 335, in receive_message
    data = await async_receive_data(conn, length - 16, deadline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pymongo/network_layer.py", line 286, in async_receive_data
    await asyncio.wait(tasks)
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 464, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 550, in _wait
    await waiter
asyncio.exceptions.CancelledError: <object object at 0xffff3d0baa50>

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/prefect/task_engine.py", line 1429, in run_context
    with timeout_async(
         ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/contextlib.py", line 158, in __exit__
    self.gen.throw(value)
  File "/usr/local/lib/python3.12/site-packages/prefect/utilities/timeout.py", line 32, in timeout_async
    raise timeout_exc_type(f"Scope timed out after {seconds} second(s).")
prefect.task_engine.TaskRunTimeoutError: Scope timed out after 3600.0 second(s).
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 78

**Timestamp:** 2025-10-02T10:27:47.524420Z

**Level:** INFO

**Message:**

`Finished in state Completed()`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 79

**Timestamp:** 2025-10-02T10:27:47.510482Z

**Level:** INFO

**Message:**

`load_additional_user_files_node: load_customer_data - Successfully parsed 1 load configurations from list at 'transformed_data'.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 80

**Timestamp:** 2025-10-02T10:27:47.510190Z

**Level:** INFO

**Message:**

`load_additional_user_files_node: load_customer_data - Attempting to load configurations dynamically from input path: transformed_data`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 81

**Timestamp:** 2025-10-02T10:27:47.489331Z

**Level:** INFO

**Message:**

`Finished in state Completed()`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 82

**Timestamp:** 2025-10-02T10:27:47.476879Z

**Level:** INFO

**Message:**

`Finished in state Completed()`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 83

**Timestamp:** 2025-10-02T10:27:47.450686Z

**Level:** INFO

**Message:**

`Finished in state Completed()`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 84

**Timestamp:** 2025-10-02T10:27:47.415462Z

**Level:** INFO

**Message:**

`input_node: input_node - Source field 'docname' not found in node central state!`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 85

**Timestamp:** 2025-10-02T10:27:47.377850Z

**Level:** INFO

**Message:**

`Updated Run 96130334-1e84-48d7-9734-4d453b79b042 status to RUNNING in DB.`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 86

**Timestamp:** 2025-10-02T10:27:47.368444Z

**Level:** INFO

**Message:**

`Executing graph stream with input data: {'is_shared': False, 'namespace': 'external_research_reports_momentum_{item}', 'asset_name': 'healthcare_ai_2024', 'research_context': 'Analyze the impact of artificial intelligence on healthcare diagnostics and patient care in 2024. Focus on recent breakthroughs, adoption challenges, regulatory considerations, and future implications for medical professionals.', 'load_additional_user_files': [{'docname': 'ai_diagnostic_trends_2024', 'is_shared': False, 'namespace': 'research_context_files_momentum'}]}`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 87

**Timestamp:** 2025-10-02T10:27:47.368007Z

**Level:** INFO

**Message:**

`Graph compiled successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 88

**Timestamp:** 2025-10-02T10:27:47.271093Z

**Level:** INFO

**Message:**

`Graph entities built successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 89

**Timestamp:** 2025-10-02T10:27:47.243267Z

**Level:** INFO

**Message:**

```


Creating dynamic schema class hitl_node__default_research_approval_OutputSchema with fields dict_keys(['user_action', 'revision_feedback', 'load_additional_user_files'])
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 90

**Timestamp:** 2025-10-02T10:27:47.242414Z

**Level:** INFO

**Message:**

```


Creating dynamic schema class input_node_input_node_OutputSchema with fields dict_keys(['docname', 'is_shared', 'namespace', 'asset_name', 'research_context', 'load_additional_user_files'])
```

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 91

**Timestamp:** 2025-10-02T10:27:47.241541Z

**Level:** INFO

**Message:**

`Building graph for Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 92

**Timestamp:** 2025-10-02T10:27:47.221536Z

**Level:** INFO

**Message:**

`Info for Workflow run: - Workflow Name: test_on_demand_external_research_workflow - Workflow ID: 1e6c659d-40d5-43a2-9209-6d5ee3b5706f - Run ID: 96130334-1e84-48d7-9734-4d453b79b042`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 93

**Timestamp:** 2025-10-02T10:27:47.215321Z

**Level:** INFO

**Message:**

`External context manager initialized`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 94

**Timestamp:** 2025-10-02T10:27:47.215049Z

**Level:** INFO

**Message:**

`RAG service initialized successfully`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 95

**Timestamp:** 2025-10-02T10:27:46.351230Z

**Level:** INFO

**Message:**

`Starting workflow execution for Run ID: 96130334-1e84-48d7-9734-4d453b79b042, Workflow ID: 1e6c659d-40d5-43a2-9209-6d5ee3b5706f`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 96

**Timestamp:** 2025-10-02T10:27:46.350224Z

**Level:** INFO

**Message:**

`Beginning flow run 'test_on_demand_external_research_workflow:--96130334-1e84-48d7-9734-4d453b79b042' for flow 'workflow-execution'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 97

**Timestamp:** 2025-10-02T10:27:43.485169Z

**Level:** INFO

**Message:**

`Downloading flow code from storage at '.'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 98

**Timestamp:** 2025-10-02T10:27:41.326971Z

**Level:** INFO

**Message:**

`Completed submission of flow run 'b8e28e5c-6052-44e1-a6e8-2461080bb984'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 99

**Timestamp:** 2025-10-02T10:27:41.317606Z

**Level:** INFO

**Message:**

`Opening process...`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

---

### Log Entry 100

**Timestamp:** 2025-10-02T10:27:41.304613Z

**Level:** INFO

**Message:**

`Runner 'runner-25d32f5c-1fa7-4003-a9af-056f9ab5f47e' submitting flow run 'b8e28e5c-6052-44e1-a6e8-2461080bb984'`

**Flow Run ID:** b8e28e5c-6052-44e1-a6e8-2461080bb984

