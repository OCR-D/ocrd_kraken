import multiprocessing as mp

from ocrd_utils import config, initLogging

class KrakenPredictor(mp.context.SpawnProcess):
    def __init__(self, logger, parameter):
        self.logger = logger
        self.parameter = parameter
        ctxt = mp.get_context('spawn')
        self.taskq = ctxt.Queue(maxsize=1 + config.OCRD_MAX_PARALLEL_PAGES)
        self.resultq = ctxt.Queue(maxsize=1 + config.OCRD_MAX_PARALLEL_PAGES)
        self.terminate = ctxt.Event()
        ctxt = mp.get_context('fork') # base.Processor will fork workers
        self.results = ctxt.Manager().dict()
        super().__init__()
        self.daemon = True
    def __call__(self, page_id, *page_input):
        self.taskq.put((page_id, page_input))
        self.logger.debug("sent task for '%s'", page_id)
        #return self.get(page_id)
        result = self.get(page_id)
        self.logger.debug("received result for '%s'", page_id)
        return result
    def get(self, page_id):
        while not self.terminate.is_set():
            if page_id in self.results:
                result = self.results.pop(page_id)
                if isinstance(result, Exception):
                    raise Exception(f"predictor failed for {page_id}") from result
                return result
            try:
                page_id, result = self.resultq.get(timeout=0.7)
            except mp.queues.Empty:
                continue
            self.logger.debug("storing results for '%s'", page_id)
            self.results[page_id] = result
        raise Exception(f"predictor terminated while waiting on results for {page_id}")
    def run(self):
        initLogging()
        try:
            self.setup()
        except Exception as e:
            self.logger.exception("setup failed")
            self.terminate.set()
        while not self.terminate.is_set():
            try:
                page_id, page_input = self.taskq.get(timeout=1.1)
            except mp.queues.Empty:
                continue
            self.logger.debug("predicting '%s'", page_id)
            try:
                page_output = self.predict(*page_input)
            except Exception as e:
                self.logger.error("prediction failed: %s", e.__class__.__name__)
                page_output = e
            self.resultq.put((page_id, page_output))
            self.logger.debug("sent result for '%s'", page_id)
        self.resultq.close()
        self.resultq.cancel_join_thread()
        self.logger.debug("predictor terminated")
    def setup(self):
        raise NotImplementedError()
    def predict(self, *inputs):
        raise NotImplementedError()
    def shutdown(self):
        # do not terminate from forked processor instances
        if mp.parent_process() is None:
            self.terminate.set()
            self.taskq.close()
            self.taskq.cancel_join_thread()
            self.logger.debug(f"terminated {self} in {mp.current_process().name}")
        else:
            self.logger.debug(f"not touching {self} in {mp.current_process().name}")
    def __del__(self):
        self.logger.debug(f"deinit of {self} in {mp.current_process().name}")
        self.shutdown()
