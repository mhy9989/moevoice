from pkgutil import ImpImporter
import sys, re
from torch import no_grad, LongTensor
import os
from .text.symbols import symbols
from .text.symbols import symbols2

import json
from . import commons
from . import utils
from .models import SynthesizerTrn
from .text import text_to_sequence


from scipy.io.wavfile import write

def get_text(text, hps, cleaned=False,type = 1):
    if cleaned:
        text_norm = text_to_sequence(text, hps.symbols, [])
    else:
        text_norm = text_to_sequence(text, hps.symbols, hps.data.text_cleaners,type)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = LongTensor(text_norm)
    return text_norm

dir_path = os.path.dirname(__file__)

async def get_moegoe(speaker_id,text,mod_name="meishi",noise_scale=0.6,noise_scale_w=0.668,length_scale=1):
    models = {}
    info_config = os.path.join(dir_path, f'model/info.json')
    with open(info_config, "r", encoding="utf-8") as f:
        models_info = json.load(f)
    for i, info in models_info.items():
        models[i]=info
    if models[mod_name]["type"] == 1:
        config = os.path.join(dir_path, f'model/config.json')
        speaker_id=models[mod_name]["sid"]
    else:
        config = os.path.join(dir_path, f'model/{mod_name}/{mod_name}.json')
    model = os.path.join(dir_path, f'model/{mod_name}/{mod_name}.pth')
    hps_ms = utils.get_hparams_from_file(config)
    if models[mod_name]["type"] == 1:
        hps_ms.symbols = symbols2
    if models[mod_name]["type"] == 2:
        hps_ms.symbols = symbols
    net_g_ms = SynthesizerTrn(
        len(hps_ms.symbols),
        hps_ms.data.filter_length // 2 + 1,
        hps_ms.train.segment_size // hps_ms.data.hop_length,
        n_speakers= 0 if ((models[mod_name]["type"]== 1) and (models[mod_name]["sid"] == 0) and (mod_name != "kyoka")) else hps_ms.data.n_speakers,
        **hps_ms.model)
    _ = net_g_ms.eval()
    utils.load_checkpoint(model, net_g_ms)
    
    text = text.replace('\n', ' ').replace('\r', '').replace(" ", "")

    try:
        if models[mod_name]["type"] == 2:
            stn_tst = get_text(text, hps_ms,type=2)
        else:
            stn_tst = get_text(text, hps_ms)
    except:
        return "Invalid text!"
            
    out_path = os.path.join(dir_path, 'demo.wav')
    with no_grad():
        x_tst = stn_tst.unsqueeze(0)
        x_tst_lengths = LongTensor([stn_tst.size(0)])
        sid = LongTensor([speaker_id])
        audio = net_g_ms.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=noise_scale, noise_scale_w=noise_scale_w, length_scale=length_scale)[0][0,0].data.cpu().float().numpy()
    write(out_path, hps_ms.data.sampling_rate, audio)
    return "Successful"
