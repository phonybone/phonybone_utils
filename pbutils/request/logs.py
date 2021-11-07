import logging

fmt = "%(levelname)s %(threadName)s %(filename)s:%(lineno)s %(message)s"
logging.basicConfig(format=fmt)
log = logging.getLogger('arequest')
log.setLevel(logging.INFO)
