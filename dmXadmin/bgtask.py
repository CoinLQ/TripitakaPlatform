from background_task import background
import logging
from tsdata.models import LQSutra, LQReel

from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@background(schedule=0)
def create_lqreels_for_lqsutras(lqsutra_sid_list):
    logger.info("event=create_lqreels_for_new_lqsutras start")
    for sid in lqsutra_sid_list:
        create_lqreels_for_sutra(sid)
    logger.info("event=create_lqreels_for_new_lqsutras end")


def create_lqreels_for_sutra(sid):
    """为一部 龙泉经 生产 缺失的龙泉卷数据"""
    lqreel_lst = []
    try:
        lqsutra = LQSutra.objects.filter(sid=sid).first()
    except ObjectDoesNotExist:
        logger.error(f"event=none-exist-sid v={sid}")
        return lqreel_lst
    total_reels = lqsutra.total_reels  # 根据 sid从龙泉经目对象中获得
    for reel_no in range(1, total_reels + 1):
        try:
            LQReel.objects.get(lqsutra=lqsutra, reel_no=reel_no)
        except ObjectDoesNotExist:
            lqreel = LQReel(
                lqsutra=lqsutra,
                reel_no=reel_no,
                start_vol=0, start_vol_page=0,
                end_vol=0, end_vol_page=0,
                is_existed=False
            )
            lqreel.rid = "%s_%s" % (lqsutra.sid, str(reel_no).zfill(3))
            lqreel_lst.append(lqreel)
    lqreels = LQReel.objects.bulk_create(lqreel_lst)
    logger.info(f"event=created_lqreels sutra={lqsutra} new_reels={lqreel_lst}")
    return lqreels
