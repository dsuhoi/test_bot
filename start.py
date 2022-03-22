import multiprocessing as mp

import tgtest as tgt
import vktest as vkt

if __name__ == "__main__":
    vk_proc = mp.Process(target=vkt.bot.run_forever)
    tg_proc = mp.Process(
        target=tgt.executor.start_polling,
        args=(tgt.dp,),
        kwargs={"skip_updates": True},
    )
    vk_proc.start()
    tg_proc.start()
