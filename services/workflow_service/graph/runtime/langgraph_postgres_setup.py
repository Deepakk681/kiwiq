from db.session import get_pool
from langgraph.checkpoint.postgres import PostgresSaver

if __name__ == "__main__":
    with get_pool() as pool:
        checkpointer = PostgresSaver(pool)
        # NOTE: you need to call .setup() the first time you're using your checkpointer
        checkpointer.setup()
