from nonebot import MessageSegment, NoneBot
from hoshino import Service, priv
from hoshino.typing import CQEvent
from typing import Union
import re
import aiohttp, base64, time, random, hashlib
from .MoeGoe.MoeGoe import get_moegoe
import os

sv_help = '''
- 让[宁宁|爱瑠|芳乃|茉子|丛雨|小春|七海]说
- 让[妃爱|华乃|锦香|诗樱|天梨|和泉|广梦|圣莉]说
- 让[四季|栞那|墨染|爱衣|凉音]说
- 让[穹|目瑛|奈绪|一叶]说
- 让[Sua|Mimiru|Arin|Yeonhwa|Yuhwa|Seonbae]说
- 让[派蒙|凯亚|安柏|丽莎|琴|香菱|枫原万叶|
  迪卢克|温迪|可莉|早柚|托马|芭芭拉|优菈|
  云堇|钟离|魈|凝光|雷电将军|北斗|
  甘雨|七七|刻晴|神里绫华|戴因斯雷布|雷泽|
  神里绫人|罗莎莉亚|阿贝多|八重神子|宵宫|
  荒泷一斗|九条裟罗|夜兰|珊瑚宫心海|五郎|
  散兵|女士|达达利亚|莫娜|班尼特|申鹤|
  行秋|烟绯|久岐忍|辛焱|砂糖|胡桃|重云|
  菲谢尔|诺艾尔|迪奥娜|鹿野院平藏]说
- 让[小暗|茉茉|娜娜|美柑|唯|芽亚|涅墨西斯|静|
  希莉奴|菈菈|沙姫|春菜|ルン|芽衣|恭子|里纱|
  未央|提亚悠九条凛|藤崎绫|结城华|涼子|アゼンダ|梨子|
  梨斗|佩凯|健一|レン|校长]说
- 让[美羽|布良梓|艾莉娜|莉音|尼古拉|小夜|夕里|萌香|安娜|直太|兵马|元树]说
- 让[夏目|栞那|希|爱衣|凉音]说
- 让[姬爱|华乃|日海|诗音|天梨|和泉里|广梦|莉莉子]说
- 让[莲华|雾枝|雫|亚璃子|灯露椎|夕莉]说
- 让[xcw]说
- 让[优妮|切噜|华哥]说
- 让[佩可|可可萝|凯露|雪菲|爱梅斯|惠理子|初音|日和|镜华|美空]说
- 让[桃井|伊吕波|未花|美游|花凛|明日奈|梓|爱丽丝|
    白子|星野|日奈|伊织|泉奈|优香|阿罗那|小春|日富美]说
- 让[黑塔|卡夫卡]说
（上述pcr和ba角色支持昵称）
'''.strip()

sv = Service(
    name = '模拟语音',  #功能名
    use_priv = priv.NORMAL, #使用权限   
    manage_priv = priv.ADMIN, #管理权限
    visible = True, #False隐藏
    enable_on_default = True, #是否默认启用
    bundle = '娱乐', #属于哪一类
    help_ = sv_help #帮助文本
    )

voice_dic = {
"KR" : {'Sua': 0, 'Mimiru': 1, 'Arin': 2, 'Yeonhwa': 3, 'Yuhwa': 4, 'Seonbae': 5},
"CN" : ["派蒙", "凯亚", "安柏", "丽莎", "琴", "香菱", "枫原万叶",
  "迪卢克", "温迪", "可莉", "早柚", "托马", "芭芭拉", "优菈",
  "云堇", "钟离", "魈", "凝光", "雷电将军", "北斗",
  "甘雨", "七七", "刻晴", "神里绫华", "戴因斯雷布", "雷泽",
  "神里绫人", "罗莎莉亚", "阿贝多", "八重神子", "宵宫",
  "荒泷一斗", "九条裟罗", "夜兰", "珊瑚宫心海", "五郎",
  "散兵", "女士", "达达利亚", "莫娜", "班尼特", "申鹤",
  "行秋", "烟绯", "久岐忍", "辛焱", "砂糖", "胡桃", "重云",
  "菲谢尔", "诺艾尔", "迪奥娜", "鹿野院平藏"],
"Friend" : {
    "0" : ["优妮", "ユニ", "Yuni", "u2", "优妮辈先", "辈先", "书记", "uni"],
    "1" : ["琪爱儿","チエル","Chieru","切露","茄露","茄噜","切噜"], 
    "2" : ["克萝依","クロエ","Kuroe","华哥","黑江"]},
"Meishi" : {
    "0" : ["贪吃佩可", "ペコリーヌ","Pecoriinu","佩可莉姆","吃货","佩可","公主","饭团","🍙"],
    "1" : ["可可萝","コッコロ","Kokkoro","可可罗","妈","普白"],
    "2" : ["凯留", "キャル","Kyaru","凯露","希留耶","Kiruya","黑猫","臭鼬","普黑"],
    "3" : ["雪菲","冰龙","シェフィ"]},
"JP" : {
    'tolove': {'小暗': '金色の闇', '茉茉': 'モモ', '娜娜': 'ナナ', '美柑': '結城美柑', 
        '唯': '古手川唯', '芽亚': '黒咲芽亜', '涅墨西斯': 'ネメシス', '静': '村雨静', 
        '希莉奴': 'セリーヌ', '菈菈': 'ララ', '沙姫': '天条院沙姫', '春菜': '西連寺春菜', 
        'ルン': 'ルン', '芽衣': 'メイ', '恭子': '霧崎恭子', '里纱': '籾岡里紗', 
        '未央': '沢田未央','提亚悠': 'ティアーユ', '九条凛': '九条凛', '藤崎绫': '藤崎綾', 
        '结城华': '結城華', '涼子': '御門涼子', 'アゼンダ': 'アゼンダ', '梨子': '夕崎梨子', 
        '梨斗': '結城梨斗', '佩凯': 'ペケ', '健一': '猿山ケンイチ', 'レン': 'レン', 
        '校长': '校長'},
    'yuzu': {'宁宁': '綾地寧々', '爱瑠': '因幡めぐる', '芳乃': '朝武芳乃', '茉子': '常陸茉子',
     '丛雨': 'ムラサメ', '小春': '鞍馬小春', '七海': '在原七海'},
    'zero': {},
    'sora': {'穹': '春日野穹', '瑛': '天女目瑛', '奈绪': '依媛奈緒', '一叶': '渚一葉'},
    'dracu': {'美羽': '矢来美羽', '布良梓': '布良梓', '艾莉娜': 'エリナ', '莉音': '稲丛莉音', 
    '尼古拉': 'ニコラ', '小夜': '荒神小夜', '夕里': '大房ひよ里', '萌香': '淡路萌香', 
    '安娜': 'アンナ', '直太': '倉端直太', '兵马': '枡形兵馬', '元树': '扇元樹'},
    'stella': {'夏目': '四季ナツメ', '栞那': '明月栞那', '希': '墨染希', '爱衣': '火打谷愛衣', 
    '凉音': '汐山涼音' },
    'mangekyo': {'莲华': '蓮華', '雾枝': '篝ノ霧枝', '雫': '沢渡雫', '灯露椎': '灯露椎',
     '夕莉': '覡夕莉'},
    'hamidashi': {'姬爱': '和泉妃愛', '华乃': '常盤華乃', '日海': '錦あすみ', '诗音': '鎌倉詩桜', 
    '天梨': '竜閑天梨', '和泉里': '和泉里', '广梦': '新川広夢', '莉莉子': '聖莉々子'}},    
"BA" : {
    "momoi": ["momoi","才羽桃井","桃井","小桃"],
    "iroha": ["iroha","枣伊吕波","伊吕波","168"],
    "mika":  ["mika", "圣园未花","未花"],
    "miyu": ["miyu","霞泽美游","美游"],
	"karin": ["karin","角楯花凛","花凛"],
	"asuna": ["asuna","一之濑明日奈","明日奈"],
	"azusa": ["azusa","白洲梓","梓","小梓"],
	"alice": ["alice","天童爱丽丝","爱丽丝","女儿"],
	"shiroko": ["shiroko","砂狼白子","白子","悍匪"],
	"hoshino": ["hoshino","小鸟游星野","星野","大叔"],
	"hina": ["hina","空崎日奈","日奈","阳奈","大老婆"],
	"iori": ["iori","银镜伊织","伊织","佐仓","佐三枪"],
	"izuna": ["izuna","久田泉奈","泉奈","小狐狸"],
	"yuuka": ["yuuka","早濑优香","优香","邮箱","没包人"],
    "arona": ["arona","阿罗那","阿罗娜"],
    "koharu": ["koharu","小春"],
    "hifumi": ["hifumi","日富美"]
    },
    "PCR": {
        "ameth": ["ameth","爱梅斯","爱美斯"],
        "eriko": ["eriko","惠理子","病娇"],
        "hatsune": ["hatsune","初音","星法","星星法","⭐法","睡法"],
        "herta": ["herta","黑塔"],
        "kafka": ["kafka","卡夫卡"],
        "hiyori": ["hiyori","日和","日和莉","猫拳","🐱👊"],
        "kyoka": ["kyoka","冰川镜华","xcw","镜华",'小仓唯'],
        "misora": ["misora","美空"],
    }
}

KR = [i for i in voice_dic["KR"]]
CN = voice_dic["CN"]
Friend = [j for i in voice_dic["Friend"].values() for j in i]
Meishi = [j for i in voice_dic["Meishi"].values() for j in i]
JP = [j for i in voice_dic["JP"].values() for j in i]
BA = [j for i in voice_dic["BA"].values() for j in i]
PCR = [j for i in voice_dic["PCR"].values() for j in i]
ALL = KR + CN + Friend + JP + Meishi + BA + PCR

MoeGoeAPI = 'https://moegoe.azurewebsites.net/api/'
VoiceAPI = 'http://106.53.138.218:6321/api/voice'
TranslateAPI = 'https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'

dir_path = os.path.dirname(__file__)
save_path = os.path.join(dir_path, 'MoeGoe/demo.wav')

class Error(Exception):

    def __init__(self, args: object) -> None:
        self.error = args

def randomhash():
    z = '0123456789abcdefghijklmnopqrstuvwxyz'
    hash = ''
    for _ in range(10):
        hash += random.choice(z)
    return hash

async def get_key(dct, value):
    return [k for (k,v) in dct.items() if value in v][0]

async def voiceApi(api: str, params: Union[str, dict] = None) -> str:
    async with aiohttp.request('GET', api, params=params) as resp:
        if resp.status == 200:
            data = await resp.read()
        else:
            raise Error(resp.status)
    return 'base64://' + base64.b64encode(data).decode()


@sv.on_prefix(["n让" + i + '说' for i in Meishi])
async def voice(bot: NoneBot, ev: CQEvent):

    text: str = ev.message.extract_plain_text().strip()
    if not text:
        await bot.finish(ev, '请输入需要合成语音的文本', at_sender=True)
    id: str = ev.get('prefix')[2:-1]
    jap = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]') 
    krr = re.compile(r'[\uAC00-\uD7A3]') 
    if not jap.search(text):
        text = await translate(text,'ja')
    index = await get_key(voice_dic['Meishi'], id)
    text = await get_moegoe(int(index), text, 3) 
    if text == "Successful":
        voice = f'file:///{save_path}'
    
    data = MessageSegment.record(voice)

    await bot.send(ev, data)

@sv.on_prefix(["让" + i + '说' for i in ALL])
async def voice(bot: NoneBot, ev: CQEvent):

    text: str = ev.message.extract_plain_text().strip()
    if not text:
        await bot.finish(ev, '请输入需要合成语音的文本', at_sender=True)
    id: str = ev.get('prefix')[1:-1]
    jap = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]') 
    krr = re.compile(r'[\uAC00-\uD7A3]') 
    if id in CN:
        for i, t in enumerate(CN):
            if t == id:
                index = i
        text = await get_moegoe(int(index), text, "genshin") 
        if text == "Successful":
            voice = f'file:///{save_path}'
    
    elif id in KR:
        if not krr.search(text):
            text = await translate(text,'ko')
        id = voice_dic["KR"][id]
        voice = await voiceApi(MoeGoeAPI + "speakkr", {'id': id, 'text': text})
    elif id in JP:
        if not jap.search(text):
            text = await translate(text,'ja')
        index = await get_key(voice_dic['JP'], id)
        voice = await voiceApi(VoiceAPI, {'model': index, 'speaker': id, 'text': text})
    elif id in Friend:
        if not jap.search(text):
            text = await translate(text,'ja')
        index = await get_key(voice_dic['Friend'], id)
        text = await get_moegoe(int(index), text, "haopengyou") 
        if text == "Successful":
            voice = f'file:///{save_path}'
    elif id in BA:
        if not jap.search(text):
            text = await translate(text,'ja')
        index = await get_key(voice_dic['BA'], id)
        text = await get_moegoe(0, text, str(index))
        if text == "Successful":
            voice = f'file:///{save_path}'
    elif id in PCR:
        if not jap.search(text):
            text = await translate(text,'ja')
        index = await get_key(voice_dic['PCR'], id)
        text = await get_moegoe(0, text, str(index))
        if text == "Successful":
            voice = f'file:///{save_path}'
    elif id in Meishi:
        if not jap.search(text):
            text = await translate(text,'ja')
        index = await get_key(voice_dic['Meishi'], id)
        text = await get_moegoe(int(index), text, "meishi") 
        if text == "Successful":
            voice = f'file:///{save_path}'
    
    data = MessageSegment.record(voice)

    await bot.send(ev, data)

@sv.on_suffix('语言帮助')
async def voicehelp(bot: NoneBot, ev: CQEvent):
    await bot.send(ev, sv_help)


async def translate(text: str,lan: str) -> str:
    lts = str(int(time.time() * 1000))
    salt = lts + str(random.randint(0, 9))
    sign_str = 'fanyideskweb' + text + salt + 'Ygy_4c=r#e#4EX^NUGUc5'
    m = hashlib.md5()
    m.update(sign_str.encode())
    sign = m.hexdigest()

    headers = {
        'Referer': 'https://fanyi.youdao.com/',
        'Cookie': 'OUTFOX_SEARCH_USER_ID=-1124603977@10.108.162.139; JSESSIONID=aaamH0NjhkDAeAV9d28-x; OUTFOX_SEARCH_USER_ID_NCOO=1827884489.6445506; fanyi-ad-id=305426; fanyi-ad-closed=1; ___rl__test__cookies=1649216072438',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36'
    }
    data = {
        'i': text,
        'from': 'zh-CHS',
        'to': lan,
        'smartresult': 'dict',
        'client': 'fanyideskweb',
        'salt': salt,
        'sign': sign,
        'lts': lts,
        'bv': 'a0d7903aeead729d96af5ac89c04d48e',
        'doctype': 'json',
        'version': '2.1',
        'keyfrom': 'fanyi.web',
        'action': 'FY_BY_REALTlME',
    }

    async with aiohttp.request('POST', TranslateAPI, headers=headers, data=data) as resp:
        response = await resp.json()

    return response['translateResult'][0][0]['tgt']