from background_task import background
import logging
from tsdata.models import create_lqreels_for_sutra


logger = logging.getLogger(__name__)


@background(schedule=0)
def create_lqreels_for_lqsutras(lqsutra_sid_list):
    logger.info("event=create_lqreels_for_new_lqsutras start")
    for sid in lqsutra_sid_list:
        create_lqreels_for_sutra(sid)
    logger.info("event=create_lqreels_for_new_lqsutras end")



