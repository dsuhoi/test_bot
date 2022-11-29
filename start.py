import multiprocessing as mp

import app.tgtest as tgt
import app.vktest as vkt

if __name__ == "__main__":
    vk_proc = mp.Process(target=vkt.bot.run_forever)
    tg_proc = mp.Process(
        target=tgt.executor.start_polling,
        args=(tgt.dp,),
        kwargs={"skip_updates": True, "on_startup": tgt.init_info},
    )
    vk_proc.start()
    tg_proc.start()
