import queue
import threading
import asyncio
import json
import decimal
import signal

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from proton_driver import client

from .utils.logging import getLogger
logger = getLogger()

class QueryRequest(BaseModel):
    sql: str

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)

class Query():
    def __init__(self, sql, client):
        self.sql = sql
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.client = client
        self.terminate_flag = threading.Event()
        self.header = None
        self.finished = False
        self.error = False

        producer_thread = threading.Thread(target=self.run)
        producer_thread.start()

    def run(self):
        logger.info(f'run sql {self.sql}')
        try:
            rows = self.client.execute_iter(self.sql, with_column_types=True)
            header = next(rows)
            self.header = header
            for row in rows:
                with self.lock:
                    if self.terminate_flag.is_set():
                        break
                    self.queue.put(row)
        except Exception as e:
            logger.warning(f'failed to get query result {e}')
            self.error = True
        finally:
            logger.info(f'run sql {self.sql} finished')
            self.finished = True

    def pull(self):
        result = []
        with self.lock:
            while not self.queue.empty():
                m = self.queue.get()
                result.append(m)
        return result

    async def get_header(self):
        while self.header is None:
            if self.is_error():
                return None
            await asyncio.sleep(1)
        return self.header

    def cancel(self):
        self.terminate_flag.set()
        try:
            # self.client.cancel()
            self.client.disconnect()
        except Exception:
            logger.exception('failed to disconnect proton')

    def is_finshed(self):
        return self.finished

    def is_error(self):
        return self.error

global_queries = []
running = True

app = FastAPI()

def stop_server(*args):
    global running
    running = False

@app.on_event("startup")
def startup_event():
    signal.signal(signal.SIGINT, stop_server)

@app.on_event("shutdown")
def shutdown_event():
    logger.warning("Application shutdown")
    for q in global_queries:
        try:
            q.cancel()
        except Exception:
            pass


@app.get("/")
def info():
    return {"info": "proton query service"}

app.mount("/static", StaticFiles(directory="static"), name="static")

async def query_stream(sql):
    global running
    try:
        proton_client = client.Client(host="localhost",port=8463)
        query = Query(sql,proton_client)
        header = await query.get_header()
        if header is None:
            logger.info(f'wrong sql, no header')
            return

        global_queries.append(query)
        while True:
            messages = query.pull()
            for m in messages:
                try:
                    result = {}
                    for index, (name, t) in enumerate(header):
                        if t.startswith('date'):
                            result[name] = str(m[index]) # convert datetime type to string
                        else:
                            result[name] = m[index]
                    result_str = json.dumps(result, cls=DecimalEncoder).encode("utf-8") + b"\n"
                    yield result_str
                except Exception as e:
                    query.cancel()
                    logger.info(f'query cancelled due to {e}' )
                    break

            if query.is_error():
                logger.info(f'query finished with error {sql}' )
                query.cancel()
                break

            if query.is_finshed():
                logger.info(f'query finished {sql}' )
                break

            if not running:
                logger.info(f'exit' )
                break

            await asyncio.sleep(1)
    except Exception:
        logger.exception(f'failed to run query {sql}')
        

@app.post("/queries")
def query_pipeline(req: QueryRequest):
    return StreamingResponse(query_stream(req.sql), media_type="application/json")
