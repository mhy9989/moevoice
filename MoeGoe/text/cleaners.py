""" from https://github.com/keithito/tacotron """

'''
Cleaners are transformations that run over the input text at both training and eval time.

Cleaners can be selected by passing a comma-delimited list of cleaner names as the "cleaners"
hyperparameter. Some cleaners are English-specific. You'll typically want to use:
  1. "english_cleaners" for English text
  2. "transliteration_cleaners" for non-English text that can be transliterated to ASCII using
     the Unidecode library (https://pypi.python.org/pypi/Unidecode)
  3. "basic_cleaners" if you do not want to transliterate (in this case, you should also update
     the symbols in symbols.py to match your data).
'''

import re
from unidecode import unidecode
import pyopenjtalk
from jamo import h2j, j2hcj
from phonemizer import phonemize
from pypinyin import pinyin, lazy_pinyin, load_phrases_dict, Style, load_single_dict
from pypinyin.style._utils import get_finals, get_initials
from pypinyin_dict.phrase_pinyin_data import cc_cedict
from pypinyin_dict.pinyin_data import kmandarin_8105
import jieba

# This is a list of Korean classifiers preceded by pure Korean numerals.
_korean_classifiers = '군데 권 개 그루 닢 대 두 마리 모 모금 뭇 발 발짝 방 번 벌 보루 살 수 술 시 쌈 움큼 정 짝 채 척 첩 축 켤레 톨 통'

# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')

# Regular expression matching Japanese without punctuation marks:
_japanese_characters = re.compile(r'[A-Za-z\d\u3005\u3040-\u30ff\u4e00-\u9fff\uff11-\uff19\uff21-\uff3a\uff41-\uff5a\uff66-\uff9d]')

# Regular expression matching non-Japanese characters or punctuation marks:
_japanese_marks = re.compile(r'[^A-Za-z\d\u3005\u3040-\u30ff\u4e00-\u9fff\uff11-\uff19\uff21-\uff3a\uff41-\uff5a\uff66-\uff9d]')

# List of (regular expression, replacement) pairs for abbreviations:
_abbreviations = [(re.compile('\\b%s\\.' % x[0], re.IGNORECASE), x[1]) for x in [
  ('mrs', 'misess'),
  ('mr', 'mister'),
  ('dr', 'doctor'),
  ('st', 'saint'),
  ('co', 'company'),
  ('jr', 'junior'),
  ('maj', 'major'),
  ('gen', 'general'),
  ('drs', 'doctors'),
  ('rev', 'reverend'),
  ('lt', 'lieutenant'),
  ('hon', 'honorable'),
  ('sgt', 'sergeant'),
  ('capt', 'captain'),
  ('esq', 'esquire'),
  ('ltd', 'limited'),
  ('col', 'colonel'),
  ('ft', 'fort'),
]]

# List of (hangul, hangul divided) pairs:
_hangul_divided = [(re.compile('%s' % x[0]), x[1]) for x in [
  ('ㄳ', 'ㄱㅅ'),
  ('ㄵ', 'ㄴㅈ'),
  ('ㄶ', 'ㄴㅎ'),
  ('ㄺ', 'ㄹㄱ'),
  ('ㄻ', 'ㄹㅁ'),
  ('ㄼ', 'ㄹㅂ'),
  ('ㄽ', 'ㄹㅅ'),
  ('ㄾ', 'ㄹㅌ'),
  ('ㄿ', 'ㄹㅍ'),
  ('ㅀ', 'ㄹㅎ'),
  ('ㅄ', 'ㅂㅅ'),
  ('ㅘ', 'ㅗㅏ'),
  ('ㅙ', 'ㅗㅐ'),
  ('ㅚ', 'ㅗㅣ'),
  ('ㅝ', 'ㅜㅓ'),
  ('ㅞ', 'ㅜㅔ'),
  ('ㅟ', 'ㅜㅣ'),
  ('ㅢ', 'ㅡㅣ'),
  ('ㅑ', 'ㅣㅏ'),
  ('ㅒ', 'ㅣㅐ'),
  ('ㅕ', 'ㅣㅓ'),
  ('ㅖ', 'ㅣㅔ'),
  ('ㅛ', 'ㅣㅗ'),
  ('ㅠ', 'ㅣㅜ')
]]

# List of (Latin alphabet, hangul) pairs:
_latin_to_hangul = [(re.compile('%s' % x[0], re.IGNORECASE), x[1]) for x in [
  ('a', '에이'),
  ('b', '비'),
  ('c', '시'),
  ('d', '디'),
  ('e', '이'),
  ('f', '에프'),
  ('g', '지'),
  ('h', '에이치'),
  ('i', '아이'),
  ('j', '제이'),
  ('k', '케이'),
  ('l', '엘'),
  ('m', '엠'),
  ('n', '엔'),
  ('o', '오'),
  ('p', '피'),
  ('q', '큐'),
  ('r', '아르'),
  ('s', '에스'),
  ('t', '티'),
  ('u', '유'),
  ('v', '브이'),
  ('w', '더블유'),
  ('x', '엑스'),
  ('y', '와이'),
  ('z', '제트')
]]


def expand_abbreviations(text):
  for regex, replacement in _abbreviations:
    text = re.sub(regex, replacement, text)
  return text


def lowercase(text):
  return text.lower()


def collapse_whitespace(text):
  return re.sub(_whitespace_re, ' ', text)


def convert_to_ascii(text):
  return unidecode(text)


def latin_to_hangul(text):
  for regex, replacement in _latin_to_hangul:
    text = re.sub(regex, replacement, text)
  return text


def divide_hangul(text):
  for regex, replacement in _hangul_divided:
    text = re.sub(regex, replacement, text)
  return text


def hangul_number(num, sino=True):
  '''Reference https://github.com/Kyubyong/g2pK'''
  num = re.sub(',', '', num)

  if num == '0':
      return '영'
  if not sino and num == '20':
      return '스무'

  digits = '123456789'
  names = '일이삼사오육칠팔구'
  digit2name = {d: n for d, n in zip(digits, names)}
  
  modifiers = '한 두 세 네 다섯 여섯 일곱 여덟 아홉'
  decimals = '열 스물 서른 마흔 쉰 예순 일흔 여든 아흔'
  digit2mod = {d: mod for d, mod in zip(digits, modifiers.split())}
  digit2dec = {d: dec for d, dec in zip(digits, decimals.split())}

  spelledout = []
  for i, digit in enumerate(num):
    i = len(num) - i - 1
    if sino:
      if i == 0:
        name = digit2name.get(digit, '')
      elif i == 1:
        name = digit2name.get(digit, '') + '십'
        name = name.replace('일십', '십')
    else:
      if i == 0:
        name = digit2mod.get(digit, '')
      elif i == 1:
        name = digit2dec.get(digit, '')
    if digit == '0':
      if i % 4 == 0:
        last_three = spelledout[-min(3, len(spelledout)):]
        if ''.join(last_three) == '':
          spelledout.append('')
          continue
      else:
        spelledout.append('')
        continue
    if i == 2:
      name = digit2name.get(digit, '') + '백'
      name = name.replace('일백', '백')
    elif i == 3:
      name = digit2name.get(digit, '') + '천'
      name = name.replace('일천', '천')
    elif i == 4:
      name = digit2name.get(digit, '') + '만'
      name = name.replace('일만', '만')
    elif i == 5:
      name = digit2name.get(digit, '') + '십'
      name = name.replace('일십', '십')
    elif i == 6:
      name = digit2name.get(digit, '') + '백'
      name = name.replace('일백', '백')
    elif i == 7:
      name = digit2name.get(digit, '') + '천'
      name = name.replace('일천', '천')
    elif i == 8:
      name = digit2name.get(digit, '') + '억'
    elif i == 9:
      name = digit2name.get(digit, '') + '십'
    elif i == 10:
      name = digit2name.get(digit, '') + '백'
    elif i == 11:
      name = digit2name.get(digit, '') + '천'
    elif i == 12:
      name = digit2name.get(digit, '') + '조'
    elif i == 13:
      name = digit2name.get(digit, '') + '십'
    elif i == 14:
      name = digit2name.get(digit, '') + '백'
    elif i == 15:
      name = digit2name.get(digit, '') + '천'
    spelledout.append(name)
  return ''.join(elem for elem in spelledout)


def number_to_hangul(text):
  '''Reference https://github.com/Kyubyong/g2pK'''
  tokens = set(re.findall(r'(\d[\d,]*)([\uac00-\ud71f]+)', text))
  for token in tokens:
    num, classifier = token
    if classifier[:2] in _korean_classifiers or classifier[0] in _korean_classifiers:
      spelledout = hangul_number(num, sino=False)
    else:
      spelledout = hangul_number(num, sino=True)
    text = text.replace(f'{num}{classifier}', f'{spelledout}{classifier}')
  # digit by digit for remaining digits
  digits = '0123456789'
  names = '영일이삼사오육칠팔구'
  for d, n in zip(digits, names):
    text = text.replace(d, n)
  return text


def basic_cleaners(text):
  '''Basic pipeline that lowercases and collapses whitespace without transliteration.'''
  text = lowercase(text)
  text = collapse_whitespace(text)
  return text


def transliteration_cleaners(text):
  '''Pipeline for non-English text that transliterates to ASCII.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = collapse_whitespace(text)
  return text


def japanese_cleaners(text):
  '''Pipeline for notating accent in Japanese text.
  Reference https://r9y9.github.io/ttslearn/latest/notebooks/ch10_Recipe-Tacotron.html'''
  sentences = re.split(_japanese_marks, text)
  marks = re.findall(_japanese_marks, text)
  text = ''
  for i, sentence in enumerate(sentences):
    if re.match(_japanese_characters, sentence):
      if text!='':
        text+=' '
      labels = pyopenjtalk.extract_fullcontext(sentence)
      for n, label in enumerate(labels):
        phoneme = re.search(r'\-([^\+]*)\+', label).group(1)
        if phoneme not in ['sil','pau']:
          text += phoneme.replace('ch','ʧ').replace('sh','ʃ').replace('cl','Q')
        else:
          continue
        n_moras = int(re.search(r'/F:(\d+)_', label).group(1))
        a1 = int(re.search(r"/A:(\-?[0-9]+)\+", label).group(1))
        a2 = int(re.search(r"\+(\d+)\+", label).group(1))
        a3 = int(re.search(r"\+(\d+)/", label).group(1))
        if re.search(r'\-([^\+]*)\+', labels[n + 1]).group(1) in ['sil','pau']:
          a2_next=-1
        else:
          a2_next = int(re.search(r"\+(\d+)\+", labels[n + 1]).group(1))
        # Accent phrase boundary
        if a3 == 1 and a2_next == 1:
          text += ' '
        # Falling
        elif a1 == 0 and a2_next == a2 + 1 and a2 != n_moras:
          text += '↓'
        # Rising
        elif a2 == 1 and a2_next == 2:
          text += '↑'
    if i<len(marks):
      text += unidecode(marks[i]).replace(' ','')
  if re.match('[A-Za-z]',text[-1]):
    text += '.'
  return text


def japanese_cleaners2(text):
  return japanese_cleaners(text).replace('ts','ʦ')


def zh_ja_mixture_cleaners(text):
  '''Pipeline for notating accent in Japanese text.
  Reference https://r9y9.github.io/ttslearn/latest/notebooks/ch10_Recipe-Tacotron.html'''
  sentences = re.split(_japanese_marks, text)
  marks = re.findall(_japanese_marks, text)
  text = ''
  for i, sentence in enumerate(sentences):
    if re.match(_japanese_characters, sentence):
      if text!='':
        text+=' '
      labels = pyopenjtalk.extract_fullcontext(sentence)
      for n, label in enumerate(labels):
        phoneme = re.search(r'\-([^\+]*)\+', label).group(1)
        if phoneme not in ['sil','pau']:
          text += phoneme.replace('ch','ʧ').replace('sh','ʃ').replace('cl','Q')
        else:
          continue
        n_moras = int(re.search(r'/F:(\d+)_', label).group(1))
        a1 = int(re.search(r"/A:(\-?[0-9]+)\+", label).group(1))
        a2 = int(re.search(r"\+(\d+)\+", label).group(1))
        a3 = int(re.search(r"\+(\d+)/", label).group(1))
        if re.search(r'\-([^\+]*)\+', labels[n + 1]).group(1) in ['sil','pau']:
          a2_next=-1
        else:
          a2_next = int(re.search(r"\+(\d+)\+", labels[n + 1]).group(1))
        # Accent phrase boundary
        if a3 == 1 and a2_next == 1:
          text += ' '
        # Falling
        elif a1 == 0 and a2_next == a2 + 1 and a2 != n_moras:
          text += '↓'
        # Rising
        elif a2 == 1 and a2_next == 2:
          text += '↑'
    if i<len(marks):
      text += unidecode(marks[i]).replace(' ','')
  text.replace('ts','ʦ').replace('u','ɯ').replace('...','…')
  if re.match('[A-Za-zɯɹəɥ→↓↑]',text[-1]):
    text += '.'
  return text


def korean_cleaners(text):
  '''Pipeline for Korean text'''
  text = latin_to_hangul(text)
  text = number_to_hangul(text)
  text = j2hcj(h2j(text))
  text = divide_hangul(text)
  if re.match('[\u3131-\u3163]',text[-1]):
    text += '.'
  return text



kmandarin_8105.load()
cc_cedict.load()
PHRASE_LIST = [
  "琴", "安柏", "丽莎", "凯亚", "芭芭拉", "迪卢克", "雷泽", "温迪", "可莉", "班尼特", "诺艾尔", "菲谢尔",
  "砂糖", "莫娜", "迪奥娜", "阿贝多", "罗莎莉亚", "优菈", "魈", "北斗", "凝光", "香菱", "行秋", "重云",
  "七七", "刻晴", "达达利亚", "钟离", "辛焱", "甘雨", "胡桃", "烟绯", "申鹤", "云堇", "夜兰", "神里绫华",
  "神里", "绫华", "枫原万叶", "枫原", "万叶", "宵宫", "早柚", "雷电将军", "九条裟罗", "九条", "裟罗", "珊瑚宫心海",
  "珊瑚宫", "心海", "托马", "荒泷", "一斗", "荒泷派", "五郎", "八重神子", "神子", "神里绫人", "绫人",
  "久岐忍", "鹿野院平藏", "平藏", "蒙德", "璃月", "稻妻", "北风的王狼", "风魔龙", "特瓦林", "若陀龙王", "龙脊雪山",
  "金苹果群岛", "渊下宫", "层岩巨渊", "奥赛尔", "七天神像", "钩钩果", "落落莓", "塞西莉亚花", "风车菊", "尘歌壶",
  "提瓦特", "明冠山地", "风龙废墟", "明冠峡", "坠星山谷", "果酒湖", "望风山地", "坎瑞亚", "须弥", "枫丹", "纳塔",
  "至冬", "丘丘人", "丘丘暴徒", "深渊法师", "深渊咏者", "盗宝团", "愚人众", "深渊教团", "骗骗花", "急冻树", "龙蜥",
  "鸣神岛", "神无冢", "八酝岛", "海祇岛", "清籁岛", "鹤观", "绝云间", "群玉阁", "南十字", "死兆星", "木漏茶室", "神樱",
  "鸣神大社", "天使的馈赠", "社奉行", "勘定奉行", "天领奉行", "夜叉", "风神", "岩神", "雷神", "风之神", "岩之神", "雷之神",
  "风神瞳", "岩神瞳", "雷神瞳", "摩拉克斯", "契约之神", "雷电影", "雷电真", "八重宫司", "宫司大人", "巴巴托斯", "玉衡星",
  "天权星", "璃月七星", "留云借风", "削月筑阳", "理水叠山", "请仙典仪"
]

for phrase in PHRASE_LIST:
    jieba.add_word(phrase)

load_phrases_dict({"若陀": [["rě"], ["tuó"]], "平藏": [["píng"], ["zàng"]],
    "派蒙": [["pài"], ["méng"]], "安柏": [["ān"], ["bó"]],
    "一斗": [["yī"], ["dǒu"]]
    })

def chinese_cleaners(text):
  return " ".join(lazy_pinyin(jieba.cut(text), style=Style.TONE3, errors='ignore'))

def chinese_cleaners2(text):
  return " ".join([
    p
    for phone in pinyin(text, style=Style.TONE3, v_to_u=True)
    for p in [
      get_initials(phone[0], strict=True),
      get_finals(phone[0][:-1], strict=True) + phone[0][-1]
      if phone[0][-1].isdigit()
      else get_finals(phone[0], strict=True)
      if phone[0][-1].isalnum()
      else phone[0],
    ]
    if len(p) != 0 and not p.isdigit()
  ])


def english_cleaners(text):
  '''Pipeline for English text, including abbreviation expansion.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = expand_abbreviations(text)
  phonemes = phonemize(text, language='en-us', backend='espeak', strip=True)
  phonemes = collapse_whitespace(phonemes)
  return phonemes


def english_cleaners2(text):
  '''Pipeline for English text, including abbreviation expansion. + punctuation + stress'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = expand_abbreviations(text)
  phonemes = phonemize(text, language='en-us', backend='espeak', strip=True, preserve_punctuation=True, with_stress=True)
  phonemes = collapse_whitespace(phonemes)
  return phonemes