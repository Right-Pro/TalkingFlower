# -*- coding: utf-8 -*-
"""事件监视器 - 检测天气、CPU监测和固定时间触发语音"""
import random
import time
import psutil
import urllib.parse
import urllib.request
import json
import ssl
from datetime import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

WEATHER_MAP = {
    # 晴天
    'sunny': '晴',
    'clear': '晴',
    'clear sky': '晴',
    # 多云
    'partly cloudy': '多云',
    'cloudy': '多云',
    'overcast': '阴',
    'overcast clouds': '阴',
    'mostly cloudy': '多云',
    'scattered clouds': '少云',
    'few clouds': '晴间多云',
    'broken clouds': '多云',
    # 雨
    'light rain': '小雨',
    'moderate rain': '中雨',
    'heavy rain': '大雨',
    'rain': '雨',
    'light rain shower': '阵雨',
    'rain shower': '阵雨',
    'heavy rain shower': '大阵雨',
    'patchy rain possible': '局部小雨',
    'patchy light rain': '局部小雨',
    'patchy rain nearby': '局部雨',
    'drizzle': '毛毛雨',
    'light drizzle': '毛毛雨',
    'patchy light drizzle': '局部毛毛雨',
    # 雪
    'light snow': '小雪',
    'moderate snow': '中雪',
    'heavy snow': '大雪',
    'snow': '雪',
    'light snow showers': '阵雪',
    'snow showers': '阵雪',
    'patchy snow possible': '局部小雪',
    'patchy light snow': '局部小雪',
    'blizzard': '暴风雪',
    'blowing snow': '吹雪',
    # 雨夹雪
    'sleet': '雨夹雪',
    'light sleet': '小雨夹雪',
    'light sleet showers': '阵雨夹雪',
    'patchy sleet possible': '局部雨夹雪',
    # 雷电
    'thunder': '雷暴',
    'thunderstorm': '雷雨',
    'light thunderstorm': '小雷雨',
    'heavy thunderstorm': '大雷雨',
    'thundery outbreaks possible': '可能有雷暴',
    'patchy light rain with thunder': '局部雷阵雨',
    'moderate or heavy rain with thunder': '中到大雷阵雨',
    # 雾和霾
    'mist': '薄雾',
    'fog': '雾',
    'freezing fog': '冻雾',
    'haze': '霾',
    'smoke': '烟',
    'dust': '浮尘',
    'sand': '沙尘',
    'sandstorm': '沙尘暴',
    # 风
    'wind': '大风',
    'windy': '大风',
    'strong wind': '强风',
    'gale': '烈风',
    'storm': '风暴',
    'violent storm': '狂风',
    'tornado': '龙卷风',
    'cyclone': '气旋',
    # 其他
    'freezing rain': '冻雨',
    'heavy freezing rain': '大冻雨',
    'light freezing rain': '小冻雨',
    'ice pellets': '冰粒',
    'light showers of ice pellets': '小冰粒阵雨',
    'moderate or heavy showers of ice pellets': '中到大冰粒阵雨',
    'frost': '霜',
    'hail': '冰雹',
    'light hail': '小冰雹',
    'heavy hail': '大冰雹',
    'rain with hail': '雨夹冰雹',
    'hot': '炎热',
    'cold': '寒冷',
    'warm': '温暖',
    'cool': '凉爽',
    'chilly': '微寒',
    'very cold': '严寒',
    'very hot': '酷热',
    'dry': '干燥',
    'humid': '潮湿',
    'wet': '潮湿',
}
CITY_COORDS = {
    # 直辖市
    '北京': [116.4074, 39.9042],
    '上海': [121.4737, 31.2304],
    '天津': [117.2009, 39.0842],
    '重庆': [106.5516, 29.5630],
    # 黑龙江
    '哈尔滨': [126.5340, 45.8038],
    '齐齐哈尔': [123.9182, 47.3543],
    '牡丹江': [129.6186, 44.5829],
    '大庆': [125.1030, 46.5893],
    '鹤岗': [130.2775, 47.3321],
    '鸡西': [130.9693, 45.2952],
    '双鸭山': [131.1614, 46.6464],
    '伊春': [128.8408, 47.7275],
    '佳木斯': [130.3188, 46.8002],
    '七台河': [131.0031, 45.7708],
    '黑河': [127.4879, 50.2443],
    '绥化': [126.9694, 46.6545],
    '大兴安岭': [124.5922, 51.9237],
    # 吉林
    '长春': [125.3235, 43.8171],
    '吉林': [126.5494, 43.8378],
    '四平': [124.3504, 43.1664],
    '辽源': [125.1437, 42.8880],
    '通化': [125.9397, 41.7284],
    '白山': [126.4232, 41.9391],
    '松原': [124.8254, 45.1411],
    '白城': [122.8397, 45.6211],
    '延边州': [129.5138, 42.9068],
    '延吉': [129.5138, 42.9068],
    # 辽宁
    '沈阳': [123.4315, 41.8057],
    '大连': [121.6147, 38.9140],
    '鞍山': [122.9943, 41.1089],
    '抚顺': [123.9211, 41.8759],
    '本溪': [123.7665, 41.2940],
    '丹东': [124.3544, 40.0008],
    '锦州': [121.1283, 41.0951],
    '营口': [122.2354, 40.6667],
    '阜新': [121.6480, 42.0166],
    '辽阳': [123.2397, 41.2673],
    '盘锦': [122.0707, 41.1199],
    '铁岭': [123.8423, 42.2866],
    '朝阳': [120.3890, 41.5740],
    '葫芦岛': [120.8369, 40.7109],
    # 河北
    '石家庄': [114.5149, 38.0423],
    '唐山': [118.1802, 39.6309],
    '秦皇岛': [119.6005, 39.9354],
    '邯郸': [114.4906, 36.6116],
    '邢台': [114.5047, 37.0708],
    '保定': [115.4646, 38.8740],
    '张家口': [114.8876, 40.8244],
    '承德': [117.9325, 40.9510],
    '沧州': [116.8388, 38.3037],
    '廊坊': [116.6838, 39.5378],
    '衡水': [115.6860, 37.7350],
    # 山东
    '济南': [117.1205, 36.6510],
    '青岛': [120.3826, 36.0671],
    '淄博': [118.0550, 36.8135],
    '枣庄': [117.3237, 34.8107],
    '东营': [118.6747, 37.4337],
    '烟台': [121.4481, 37.4635],
    '潍坊': [119.1618, 36.7069],
    '济宁': [116.3906, 35.4146],
    '泰安': [117.0874, 36.2010],
    '威海': [122.1204, 37.5135],
    '日照': [119.5269, 35.4164],
    '临沂': [118.3564, 35.0513],
    '德州': [116.3595, 37.4357],
    '聊城': [115.9852, 36.4560],
    '滨州': [117.9728, 37.3826],
    '菏泽': [115.4810, 35.2336],
    # 江苏
    '南京': [118.7969, 32.0603],
    '苏州': [120.5853, 31.2989],
    '无锡': [120.3119, 31.4910],
    '常州': [119.9741, 31.8112],
    '徐州': [117.2841, 34.2058],
    '南通': [120.8943, 31.9802],
    '连云港': [119.2216, 34.5967],
    '淮安': [119.0153, 33.6104],
    '盐城': [120.1614, 33.3474],
    '扬州': [119.4127, 32.3942],
    '镇江': [119.4339, 32.1318],
    '泰州': [119.9255, 32.4555],
    '宿迁': [118.2755, 33.9617],
    # 浙江
    '杭州': [120.1551, 30.2741],
    '宁波': [121.5509, 29.8753],
    '温州': [120.6994, 27.9943],
    '嘉兴': [120.7551, 30.7461],
    '湖州': [120.0945, 30.8930],
    '绍兴': [120.5823, 30.0011],
    '金华': [119.6476, 29.0781],
    '衢州': [118.8595, 28.9700],
    '舟山': [122.1069, 30.0160],
    '台州': [121.4208, 28.6564],
    '丽水': [119.9229, 28.4671],
    # 安徽
    '合肥': [117.2272, 31.8206],
    '芜湖': [118.4331, 31.3529],
    '蚌埠': [117.3893, 32.9156],
    '淮南': [116.9998, 32.6255],
    '马鞍山': [118.5068, 31.6894],
    '淮北': [116.7983, 33.9548],
    '铜陵': [117.8123, 30.9448],
    '安庆': [117.0635, 30.5429],
    '黄山': [118.3387, 29.7154],
    '滁州': [118.3163, 32.3016],
    '阜阳': [115.8145, 32.8900],
    '宿州': [116.9643, 33.6464],
    '六安': [116.5232, 31.7349],
    '亳州': [115.7791, 33.8446],
    '池州': [117.4893, 30.6560],
    '宣城': [118.7587, 30.9454],
    # 河南
    '郑州': [113.6253, 34.7466],
    '开封': [114.3073, 34.7972],
    '洛阳': [112.4340, 34.6187],
    '平顶山': [113.1927, 33.7661],
    '安阳': [114.3924, 36.0976],
    '鹤壁': [114.2970, 35.7470],
    '新乡': [113.9268, 35.3030],
    '焦作': [113.2420, 35.2159],
    '濮阳': [115.0292, 35.7619],
    '许昌': [113.8525, 34.0357],
    '漯河': [114.0165, 33.5815],
    '三门峡': [111.2001, 34.7730],
    '南阳': [112.5283, 32.9908],
    '商丘': [115.6564, 34.4142],
    '信阳': [114.0910, 32.1469],
    '周口': [114.6969, 33.6261],
    '驻马店': [114.0224, 33.0115],
    # 湖北
    '武汉': [114.3054, 30.5931],
    '黄石': [115.0390, 30.2018],
    '十堰': [110.7980, 32.6292],
    '宜昌': [111.2865, 30.6919],
    '襄阳': [112.1223, 32.0090],
    '鄂州': [114.8957, 30.3911],
    '荆门': [112.1994, 31.0356],
    '孝感': [113.9169, 30.9245],
    '荆州': [112.2397, 30.3352],
    '黄冈': [114.8723, 30.4539],
    '咸宁': [114.3225, 29.8413],
    '随州': [113.3825, 31.6909],
    '恩施州': [109.4882, 30.2722],
    '恩施': [109.4882, 30.2722],
    # 湖南
    '长沙': [112.9388, 28.2282],
    '株洲': [113.1330, 27.8278],
    '湘潭': [112.9440, 27.8297],
    '衡阳': [112.5720, 26.8932],
    '邵阳': [111.4678, 27.2393],
    '岳阳': [113.1294, 29.3571],
    '常德': [111.6986, 29.0319],
    '张家界': [110.4792, 29.1173],
    '益阳': [112.3552, 28.5700],
    '郴州': [113.0147, 25.7705],
    '永州': [111.6134, 26.4204],
    '怀化': [110.0012, 27.5694],
    '娄底': [111.9944, 27.7000],
    '湘西州': [109.7389, 28.3119],
    '吉首': [109.7389, 28.3119],
    # 广东
    '广州': [113.2644, 23.1291],
    '深圳': [114.0579, 22.5431],
    '珠海': [113.5767, 22.2708],
    '汕头': [116.7087, 23.3710],
    '佛山': [113.1219, 23.0218],
    '韶关': [113.5972, 24.8105],
    '湛江': [110.3589, 21.2707],
    '肇庆': [112.4653, 23.0469],
    '江门': [113.0940, 22.5952],
    '茂名': [110.9193, 21.6624],
    '惠州': [114.4161, 23.1108],
    '梅州': [116.1223, 24.2886],
    '汕尾': [115.3753, 22.7862],
    '河源': [114.6978, 23.7463],
    '阳江': [111.9822, 21.8579],
    '清远': [113.0560, 23.6820],
    '东莞': [113.7518, 23.0207],
    '中山': [113.3927, 22.5176],
    '潮州': [116.6328, 23.6564],
    '揭阳': [116.3727, 23.5500],
    '云浮': [112.0444, 22.9151],
    # 福建
    '福州': [119.2965, 26.0745],
    '厦门': [118.0894, 24.4798],
    '莆田': [119.0077, 25.4540],
    '三明': [117.6392, 26.2639],
    '泉州': [118.6758, 24.8744],
    '漳州': [117.6462, 24.5111],
    '南平': [118.1778, 26.6418],
    '龙岩': [117.0175, 25.0751],
    '宁德': [119.5485, 26.6667],
    # 江西
    '南昌': [115.8540, 28.6830],
    '景德镇': [117.1784, 29.2690],
    '萍乡': [113.8543, 27.6229],
    '九江': [115.9536, 29.6615],
    '新余': [114.9308, 27.8178],
    '鹰潭': [117.0677, 28.2602],
    '赣州': [114.9350, 25.8311],
    '吉安': [114.9866, 27.1117],
    '宜春': [114.3911, 27.8043],
    '抚州': [116.3580, 27.9492],
    '上饶': [117.9436, 28.4546],
    # 四川
    '成都': [104.0668, 30.5728],
    '自贡': [104.7735, 29.3527],
    '攀枝花': [101.7160, 26.5804],
    '泸州': [105.4423, 28.8718],
    '德阳': [104.3979, 31.1270],
    '绵阳': [104.6796, 31.4675],
    '广元': [105.8436, 32.4355],
    '遂宁': [105.5927, 30.5329],
    '内江': [105.0584, 29.5802],
    '乐山': [103.7654, 29.5821],
    '南充': [106.1107, 30.8376],
    '眉山': [103.8485, 30.0756],
    '宜宾': [104.6429, 28.7513],
    '广安': [106.6331, 30.4559],
    '达州': [107.5023, 31.2095],
    '雅安': [103.0431, 29.9802],
    '巴中': [106.7475, 31.8679],
    '资阳': [104.6276, 30.1290],
    # 贵州
    '贵阳': [106.6302, 26.6477],
    '六盘水': [104.8303, 26.5927],
    '遵义': [106.9274, 27.7255],
    '安顺': [105.9476, 26.2535],
    '毕节': [105.2840, 27.3017],
    '铜仁': [109.1896, 27.7313],
    '黔西南州': [104.8972, 25.0893],
    '兴义': [104.8972, 25.0893],
    '黔东南州': [107.9828, 26.5833],
    '凯里': [107.9828, 26.5833],
    '黔南州': [107.5193, 26.2586],
    '都匀': [107.5193, 26.2586],
    # 云南
    '昆明': [102.8329, 24.8801],
    '曲靖': [103.7963, 25.4897],
    '玉溪': [102.5469, 24.3518],
    '保山': [99.1618, 25.1120],
    '昭通': [103.7172, 27.3370],
    '丽江': [100.2271, 26.8550],
    '普洱': [100.9722, 22.8252],
    '临沧': [100.0889, 23.8830],
    '楚雄州': [101.5456, 25.0420],
    '红河州': [103.3814, 23.3642],
    '蒙自': [103.3814, 23.3642],
    '文山州': [104.2333, 23.3933],
    '西双版纳州': [100.7977, 22.0073],
    '景洪': [100.7977, 22.0073],
    '大理州': [100.2676, 25.6065],
    '德宏州': [98.5857, 24.4337],
    '芒市': [98.5857, 24.4337],
    '怒江州': [98.8566, 25.8176],
    '迪庆州': [99.7022, 27.8185],
    '香格里拉': [99.7022, 27.8185],
    # 陕西
    '西安': [108.9398, 34.3416],
    '铜川': [108.9640, 34.9166],
    '宝鸡': [107.2371, 34.3630],
    '咸阳': [108.7089, 34.3294],
    '渭南': [109.5098, 34.4999],
    '延安': [109.4908, 36.5853],
    '汉中': [107.0286, 33.0777],
    '榆林': [109.7347, 38.2852],
    '安康': [109.0293, 32.6900],
    '商洛': [109.9397, 33.8686],
    # 甘肃
    '兰州': [103.8343, 36.0611],
    '嘉峪关': [98.2773, 39.7852],
    '金昌': [102.1884, 38.5135],
    '白银': [104.1726, 36.5450],
    '天水': [105.7249, 34.5809],
    '武威': [102.6380, 37.9283],
    '张掖': [100.4497, 38.9259],
    '平凉': [106.6648, 35.5430],
    '酒泉': [98.4945, 39.7324],
    '庆阳': [107.6436, 35.7098],
    '定西': [104.5935, 35.5764],
    '陇南': [104.9217, 33.4062],
    '临夏州': [103.2109, 35.6010],
    '甘南州': [102.9115, 34.9864],
    '合作': [102.9115, 34.9864],
    # 青海
    '西宁': [101.7782, 36.6171],
    '海东': [102.1043, 36.5020],
    '海北州': [100.9007, 36.9600],
    '黄南州': [102.0157, 35.5197],
    '海南州': [100.6205, 36.2802],
    '果洛州': [100.2449, 34.4730],
    '玉树州': [97.0065, 33.0058],
    '海西州': [97.3722, 37.3747],
    '德令哈': [97.3722, 37.3747],
    '格尔木': [94.9033, 36.4014],
    # 台湾
    '台北': [121.5654, 25.0330],
    '新北': [121.4657, 25.0120],
    '桃园': [121.3000, 24.9936],
    '台中': [120.6736, 24.1477],
    '台南': [120.1840, 22.9911],
    '高雄': [120.3014, 22.6273],
    '基隆': [121.7449, 25.1314],
    '新竹': [120.9686, 24.8067],
    '嘉义': [120.4528, 23.4818],
    # 内蒙古
    '呼和浩特': [111.7492, 40.8426],
    '包头': [109.8404, 40.6579],
    '乌海': [106.7953, 39.6538],
    '赤峰': [118.8878, 42.2578],
    '通辽': [122.2443, 43.6525],
    '鄂尔多斯': [109.7813, 39.6084],
    '呼伦贝尔': [119.7658, 49.2116],
    '巴彦淖尔': [107.3877, 40.7432],
    '乌兰察布': [113.1338, 40.9939],
    '兴安盟': [122.0686, 46.0772],
    '乌兰浩特': [122.0686, 46.0772],
    '锡林郭勒盟': [116.0482, 43.9334],
    '锡林浩特': [116.0482, 43.9334],
    '阿拉善盟': [105.7289, 38.8515],
    '阿拉善左旗': [105.7289, 38.8515],
    # 广西
    '南宁': [108.3661, 22.8172],
    '柳州': [109.4155, 24.3259],
    '桂林': [110.1794, 25.2345],
    '梧州': [111.2791, 23.4769],
    '北海': [109.1201, 21.4812],
    '防城港': [108.3547, 21.6861],
    '钦州': [108.6545, 21.9797],
    '贵港': [109.5989, 23.1110],
    '玉林': [110.1390, 22.6314],
    '百色': [106.6184, 23.9023],
    '贺州': [111.5665, 24.4036],
    '河池': [108.0854, 24.6928],
    '来宾': [109.2215, 23.7503],
    '崇左': [107.3648, 22.3765],
    # 西藏
    '拉萨': [91.1409, 29.6456],
    '日喀则': [88.8778, 29.2674],
    '昌都': [97.1720, 31.1385],
    '林芝': [94.3615, 29.6487],
    '山南': [91.7731, 29.2371],
    '那曲': [92.0514, 31.4761],
    '阿里地区': [80.1000, 32.5000],
    '噶尔': [80.1000, 32.5000],
    # 宁夏
    '银川': [106.2309, 38.4872],
    '石嘴山': [106.3828, 39.0163],
    '吴忠': [106.1989, 37.9852],
    '固原': [106.2848, 36.0046],
    '中卫': [105.1968, 37.5149],
    # 新疆
    '乌鲁木齐': [87.6168, 43.8256],
    '克拉玛依': [84.8895, 45.5792],
    '吐鲁番': [89.1897, 42.9514],
    '哈密': [93.5154, 42.8190],
    '阿克苏': [80.2644, 41.1708],
    '喀什': [75.9897, 39.4704],
    '和田': [79.9225, 37.1143],
    '伊犁': [81.3242, 43.9169],
    '塔城': [82.9858, 46.7456],
    '阿勒泰': [88.1380, 47.8483],
    '昌吉州': [87.3025, 44.0120],
    '博尔塔拉州': [82.0664, 44.9058],
    '博乐': [82.0664, 44.9058],
    '巴音郭楞州': [86.1513, 41.7686],
    '库尔勒': [86.1513, 41.7686],
    '克孜勒苏州': [76.1675, 39.7149],
    '阿图什': [76.1675, 39.7149],
    # 新疆自治区直辖县级市
    '石河子': [86.0410, 44.3066],
    '阿拉尔': [81.2805, 40.5477],
    '图木舒克': [79.0738, 39.8673],
    '五家渠': [87.5269, 44.1678],
    '北屯': [87.8134, 47.3632],
    '铁门关': [85.6706, 41.8622],
    '双河': [82.3531, 44.8400],
    '可克达拉': [80.6364, 43.9471],
    '昆玉': [79.2915, 37.2109],
    '胡杨河': [84.8270, 44.6929],
    '新星': [93.7344, 42.7935],
    # 海南
    '海口': [110.3492, 20.0174],
    '三亚': [109.5083, 18.2475],
    '三沙': [112.3393, 16.8309],
    '儋州': [109.5808, 19.5209],
    # 海南省直辖县级市
    '五指山': [109.5174, 18.7759],
    '琼海': [110.4746, 19.2584],
    '文昌': [110.7977, 19.5432],
    '万宁': [110.3891, 18.7951],
    '东方': [108.6538, 19.0964],
    '定安': [110.3240, 19.6812],
    '屯昌': [110.1034, 19.3519],
    '澄迈': [109.9981, 19.7372],
    '临高': [109.6908, 19.9128],
    '白沙': [109.4515, 19.2248],
    '昌江': [109.0553, 19.2983],
    '乐东': [109.1730, 18.7491],
    '陵水': [110.0379, 18.5060],
    '保亭': [109.7022, 18.6391],
    '琼中': [109.8388, 19.0333],
    # 港澳台
    '香港': [114.1694, 22.3193],
    '澳门': [113.5491, 22.1987],
}
CAIYUN_SKYCON_MAP = {
    # 降雪 (最高优先级)
    'LIGHT_SNOW': '小雪',
    'MODERATE_SNOW': '中雪',
    'HEAVY_SNOW': '大雪',
    'STORM_SNOW': '暴雪',
    # 降雨
    'LIGHT_RAIN': '小雨',
    'MODERATE_RAIN': '中雨',
    'HEAVY_RAIN': '大雨',
    'STORM_RAIN': '暴雨',
    # 雾
    'FOG': '雾',
    # 沙尘
    'SAND': '沙尘',
    'DUST': '浮尘',
    # 雾霾
    'HEAVY_HAZE': '重度雾霾',
    'MODERATE_HAZE': '中度雾霾',
    'LIGHT_HAZE': '轻度雾霾',
    # 大风
    'WIND': '大风',
    # 阴
    'CLOUDY': '阴',
    # 多云
    'PARTLY_CLOUDY_DAY': '多云',
    'PARTLY_CLOUDY_NIGHT': '多云',
    # 晴 (最低优先级)
    'CLEAR_DAY': '晴',
    'CLEAR_NIGHT': '晴',
}

class EventWatcher(QObject):
    idle_trigger = pyqtSignal()
    weather_good = pyqtSignal()
    cpu_temp_high = pyqtSignal()
    cpu_temp_low = pyqtSignal()
    cpu_usage_high = pyqtSignal()
    cpu_usage_low = pyqtSignal()
    time_morning = pyqtSignal()
    time_noon = pyqtSignal()
    time_sunset = pyqtSignal()
    time_night = pyqtSignal()
    time_bedtime = pyqtSignal()
    time_wake = pyqtSignal()
    time_announce = pyqtSignal(int, int)
    astronomy_updated = pyqtSignal(str, str)
    weather_data_ready = pyqtSignal(str, dict)
    weather_popup = pyqtSignal()
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._weather_cooldown = 0
        self._cpu_temp_high_cooldown = 0
        self._cpu_temp_low_cooldown = 0
        self._last_weather_check = None
        self._last_cpu_check = 0
        self._last_temp_status = None
        self._first_temp_check = True
        self.is_bedtime = False
        self._cpu_monitor_mode = config.get("cpu_monitor_mode", "temp")
        self._cpu_usage_high_cooldown = 0
        self._cpu_usage_low_cooldown = 0
        self._last_usage_status = None
        self._last_morning_triggered = -1
        self._last_noon_triggered = -1
        self._last_sunset_triggered = -1
        self._last_night_triggered = -1
        self._last_bedtime_triggered = -1
        self._last_wake_triggered = -1
        self._last_hour_announced = -1
        self._idle_timer = QTimer()
        self._idle_timer.timeout.connect(self._on_idle_timer)
        self._reset_idle_timer()
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._on_system_check)
        self._check_timer.start(30000)
        if self.config.get("cpu_monitor_enabled", True):
            print("\n[CPU] CPU监测已启用...")
            self._check_cpu()
    
    def _reset_idle_timer(self):
        interval = random.randint(900, 1800)
        self._idle_timer.stop()
        self._idle_timer.start(interval * 1000)
    
    def _on_idle_timer(self):
        if not self.is_bedtime:
            self.idle_trigger.emit()
        self._reset_idle_timer()
    
    def _on_system_check(self):
        current_time = time.time()
        now = datetime.now()
        if current_time - self._weather_cooldown > 3600:
            self._check_weather()
        if current_time - self._last_cpu_check > 10:
            self._check_cpu()
            self._last_cpu_check = current_time
        self._check_fixed_time(now)
    
    def _check_cpu(self):
        if not self.config.get("cpu_monitor_enabled", True):
            return
        if self._cpu_monitor_mode == "usage":
            self._check_cpu_usage()
        else:
            self._check_cpu_temp()
    
    def _check_cpu_temp(self):
        """检查CPU温度 - 详细记录所有传感器"""
        if self._first_temp_check:
            print("\n[CPU] ========== 开始温度监测 ==========")
            print("[CPU] 正在搜索所有可用温度传感器...")
            self._first_temp_check = False
        
        max_temp = None
        all_temps = []
        
        # 方法1: psutil - 详细记录每个传感器
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    print(f"[CPU] psutil 找到 {len(temps)} 个传感器组:")
                    for name, entries in temps.items():
                        for entry in entries:
                            label = entry.label if entry.label else "未命名"
                            temp = entry.current
                            print(f"[CPU]   - {name}/{label}: {temp}°C")
                            if temp and -50 < temp < 150:  # 合理范围
                                all_temps.append((f"{name}/{label}", temp))
                                if max_temp is None or temp > max_temp:
                                    max_temp = temp
        except Exception as e:
            print(f"[CPU] psutil 错误: {e}")
        
        # 方法2: Windows WMI (备选)
        if max_temp is None:
            print("[CPU] psutil 未找到有效温度，尝试 WMI...")
            wmi_temp = self._get_windows_cpu_temp()
            if wmi_temp:
                all_temps.append(("WMI ThermalZone", wmi_temp))
                max_temp = wmi_temp
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if max_temp is not None and all_temps:
            print(f"[CPU] 所有传感器: {', '.join([f'{n}={t:.1f}' for n,t in all_temps])}")
            
            if max_temp > 80:
                current_status, status_label = "high", "高温"
            elif max_temp < 40:
                current_status, status_label = "low", "低温"
            else:
                current_status, status_label = "normal", "正常"
            
            if self._last_temp_status is not None and self._last_temp_status != current_status:
                status_names = {'high': '高温', 'low': '低温', 'normal': '正常'}
                old_label = status_names.get(self._last_temp_status, self._last_temp_status)
                print(f"[CPU] [{timestamp}] 状态: {old_label} -> {status_label} (最高: {max_temp:.1f}°C)")
            else:
                print(f"[CPU] [{timestamp}] 最高温度: {max_temp:.1f}°C [{status_label}]")
            
            current_time = time.time()
            if max_temp > 80:
                if current_time - self._cpu_temp_high_cooldown > 300:
                    self.cpu_temp_high.emit()
                    self._cpu_temp_high_cooldown = current_time
                self._last_temp_status = current_status
            elif max_temp < 40:
                if current_time - self._cpu_temp_low_cooldown > 600:
                    self.cpu_temp_low.emit()
                    self._cpu_temp_low_cooldown = current_time
                self._last_temp_status = current_status
            else:
                self._last_temp_status = current_status
        else:
            print(f"[CPU] [{timestamp}] 无法读取温度")
            print("[CPU] 建议: 安装OpenHardwareMonitor驱动或使用使用率监测")
    
    def _check_cpu_usage(self):
        if self._first_temp_check:
            print("\n[CPU] ========== 开始使用率监测 ==========")
            print("[CPU] 使用率监测已启用 (无需管理员权限)")
            self._first_temp_check = False
        try:
            usage = psutil.cpu_percent(interval=1)
            timestamp = datetime.now().strftime("%H:%M:%S")
            if usage > 80:
                current_status, status_label = "high", "高负载"
            elif usage < 20:
                current_status, status_label = "low", "低负载"
            else:
                current_status, status_label = "normal", "正常"
            if self._last_usage_status is not None and self._last_usage_status != current_status:
                status_names = {'high': '高负载', 'low': '低负载', 'normal': '正常'}
                old_label = status_names.get(self._last_usage_status, self._last_usage_status)
                print(f"[CPU] [{timestamp}] 负载变化: {old_label} -> {status_label} ({usage:.1f}%)")
            else:
                print(f"[CPU] [{timestamp}] 使用率: {usage:.1f}% [{status_label}]")
            current_time = time.time()
            if usage > 80:
                if current_time - self._cpu_usage_high_cooldown > 300:
                    self.cpu_usage_high.emit()
                    self._cpu_usage_high_cooldown = current_time
                self._last_usage_status = current_status
            elif usage < 20:
                if current_time - self._cpu_usage_low_cooldown > 600:
                    self.cpu_usage_low.emit()
                    self._cpu_usage_low_cooldown = current_time
                self._last_usage_status = current_status
            else:
                self._last_usage_status = current_status
        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[CPU] [{timestamp}] 无法读取使用率: {e}")
    
    def _get_windows_cpu_temp(self):
        """获取Windows CPU温度 - 使用WMI"""
        import subprocess
        
        temps = []
        
        # 使用 PowerShell 获取温度
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | ForEach-Object { $_.CurrentTemperature }'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.isdigit():
                    temp_k = int(line)
                    temp_c = (temp_k / 10) - 273.15
                    if -50 < temp_c < 150:
                        temps.append(temp_c)
                        print(f"[CPU] WMI ThermalZone: {temp_c:.1f}°C")
        except Exception as e:
            print(f"[CPU] WMI 读取失败: {e}")
        
        return max(temps) if temps else None
    
    def _check_weather(self):
        print("\n[Weather] ========== 天气检查 ==========")
        city = self.config.get("weather_city", "")
        weather_api = self.config.get("weather_api", "wttr.in")
        print(f"[Weather] 配置城市: {city if city else '(未设置)'}")
        print(f"[Weather] API来源: {weather_api}")
        if not city:
            print("[Weather] 未设置城市，跳过天气检查")
            self._weather_cooldown = time.time()
            return
        weather_data = None
        daily_data = None
        if weather_api == "caiyun":
            api_key = self.config.get("caiyun_api_key", "").strip()
            if not api_key:
                print("[Weather] 错误: 未配置彩云天气API Key")
                self.weather_data_ready.emit("[错误] 请先在程序根目录的config.json中填写您的API！", {})
                self._weather_cooldown = time.time()
                return
            weather_data = self._fetch_caiyun_weather(city, api_key)
            # 延迟1秒后获取生活指数（避免429错误）
            import time
            time.sleep(1)
            daily_data = self._fetch_caiyun_daily(city, api_key)
        else:
            weather_data = self._fetch_wttr_weather(city)
        if weather_data:
            try:
                if weather_api == "caiyun":
                    self._parse_caiyun_data(city, weather_data, daily_data)
                else:
                    self._parse_wttr_data(city, weather_data)
            except Exception as e:
                print(f"[Weather] 解析数据失败: {e}")
                self._last_weather_check = "unknown"
        else:
            print("[Weather] 获取天气失败")
            if not self._last_weather_check:
                self._last_weather_check = "good"
        self._weather_cooldown = time.time()
        print("[Weather] ========== 完成 ==========\n")
    
    def _parse_caiyun_data(self, city, data, daily_data=None):
        result = data.get('result', {})
        realtime = result.get('realtime', {})
        temperature = realtime.get('temperature', '?')
        apparent_temp = realtime.get('apparent_temperature', '?')
        humidity = realtime.get('humidity', 0)
        skycon = realtime.get('skycon', '')
        wind_speed = realtime.get('wind', {}).get('speed', '?')
        air_quality = realtime.get('air_quality', {})
        aqi_chn = air_quality.get('aqi', {}).get('chn', '?')
        pm25 = air_quality.get('pm25', '?')
        weather_zh = CAIYUN_SKYCON_MAP.get(skycon, skycon)
        if skycon in ['CLEAR_DAY', 'CLEAR_NIGHT']:
            status = 'sunny'
        elif 'RAIN' in skycon:
            status = 'rainy'
        else:
            status = 'good'
        self._last_weather_check = status
        humidity_percent = int(humidity * 100) if humidity else '?'
        print(f"[Weather] 来源: 彩云天气")
        print(f"[Weather] 城市: {city}")
        print(f"[Weather] 天气: {weather_zh}")
        print(f"[Weather] 温度: {temperature}°C (体感 {apparent_temp}°C)")
        print(f"[Weather] 湿度: {humidity_percent}%")
        
        # 解析生活指数
        life_index = {}
        if daily_data:
            try:
                daily_result = daily_data.get('result', {})
                daily_list = daily_result.get('daily', {}).get('life_index', {})
                
                # 穿衣指数
                dressing = daily_list.get('dressing', [{}])[0]
                life_index['dressing'] = {
                    'level': dressing.get('index', '-'),
                    'desc': dressing.get('desc', '-')
                }
                
                # 紫外线指数
                ultraviolet = daily_list.get('ultraviolet', [{}])[0]
                life_index['ultraviolet'] = {
                    'level': ultraviolet.get('index', '-'),
                    'desc': ultraviolet.get('desc', '-')
                }
                
                # 舒适度指数
                comfort = daily_list.get('comfort', [{}])[0]
                life_index['comfort'] = {
                    'level': comfort.get('index', '-'),
                    'desc': comfort.get('desc', '-')
                }
                
                # 感冒指数
                cold_risk = daily_list.get('coldRisk', [{}])[0]
                life_index['coldRisk'] = {
                    'level': cold_risk.get('index', '-'),
                    'desc': cold_risk.get('desc', '-')
                }
                
                # 洗车指数
                car_washing = daily_list.get('carWashing', [{}])[0]
                life_index['carWashing'] = {
                    'level': car_washing.get('index', '-'),
                    'desc': car_washing.get('desc', '-')
                }
                
                print(f"[Weather] 生活指数: 穿衣{dressing.get('desc')}, 紫外线{ultraviolet.get('desc')}")
            except Exception as e:
                print(f"[Weather] 生活指数解析失败: {e}")
        
        weather_info = {
            'city': city, 'weather': weather_zh, 'temperature': temperature,
            'apparent_temperature': apparent_temp, 'humidity': humidity_percent,
            'wind_speed': wind_speed, 'aqi': aqi_chn, 'pm25': pm25, 
            'source': '彩云天气', 'life_index': life_index
        }
        if status in ['sunny', 'good']:
            self.weather_good.emit()
        info_text = f"[{datetime.now().strftime('%H:%M')}] 天气: {weather_zh}, {temperature}°C"
        self.weather_data_ready.emit(info_text, weather_info)
    
    def _parse_wttr_data(self, city, data):
        current = data.get('current_condition', [{}])[0]
        temp = current.get('temp_C', '?')
        feels = current.get('FeelsLikeC', '?')
        humidity = current.get('humidity', '?')
        desc = current.get('weatherDesc', [{}])[0].get('value', '')
        weather_zh = WEATHER_MAP.get(desc.lower(), desc)
        status = 'good'
        print(f"[Weather] 来源: wttr.in")
        print(f"[Weather] 城市: {city}")
        print(f"[Weather] 天气: {weather_zh}")
        print(f"[Weather] 温度: {temp}°C")
        weather_info = {
            'city': city, 'weather': weather_zh, 'temperature': temp,
            'apparent_temperature': feels, 'humidity': humidity,
            'aqi': '-', 'pm25': '-', 'source': 'wttr.in'
        }
        if status in ['sunny', 'good']:
            self.weather_good.emit()
        info_text = f"[{datetime.now().strftime('%H:%M')}] 天气: {weather_zh}, {temp}°C"
        self.weather_data_ready.emit(info_text, weather_info)
    
    def _fetch_caiyun_weather(self, city, api_key):
        try:
            coords = CITY_COORDS.get(city)
            if not coords:
                return None
            lng, lat = coords
            url = f"https://api.caiyunapp.com/v2.6/{api_key}/{lng},{lat}/realtime"
            print(f"[Weather] 请求: 彩云天气 API (realtime)")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as r:
                data = json.loads(r.read().decode('utf-8'))
            if data.get('status') != 'ok':
                return None
            return data
        except Exception as e:
            print(f"[Weather] API错误: {e}")
            return None
    
    def _fetch_caiyun_daily(self, city, api_key):
        """获取彩云天气生活指数数据"""
        try:
            coords = CITY_COORDS.get(city)
            if not coords:
                return None
            lng, lat = coords
            url = f"https://api.caiyunapp.com/v2.6/{api_key}/{lng},{lat}/daily?dailysteps=1"
            print(f"[Weather] 请求: 彩云天气 API (daily)")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as r:
                data = json.loads(r.read().decode('utf-8'))
            if data.get('status') != 'ok':
                return None
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("[Weather] Daily API: 请求过于频繁，跳过生活指数")
            else:
                print(f"[Weather] Daily API错误: HTTP {e.code}")
            return None
        except Exception as e:
            print(f"[Weather] Daily API错误: {e}")
            return None
    
    def _fetch_wttr_weather(self, city):
        try:
            url = f'http://wttr.in/{urllib.parse.quote(city)}?format=j1'
            print(f"[Weather] 请求: wttr.in")
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            print(f"[Weather] wttr.in错误: {e}")
            return None
    
    def _check_fixed_time(self, now):
        current_hour = now.hour
        current_minute = now.minute
        times = {
            'morning': self.config.get("time_morning", "08:00"),
            'noon': self.config.get("time_noon", "12:00"),
            'sunset': self.config.get("time_sunset", "18:00"),
            'night': self.config.get("time_night", "22:00"),
            'bedtime': self.config.get("time_bedtime", "23:00"),
            'wake': self.config.get("time_wake", "07:00")
        }
        if current_minute == 0 and not self.is_bedtime:
            if self._last_hour_announced != current_hour:
                self._last_hour_announced = current_hour
                self.time_announce.emit(current_hour, current_minute)
        for period, time_str in times.items():
            if self._check_time_match(current_hour, current_minute, time_str):
                attr = f"_last_{period}_triggered"
                signal = getattr(self, f"time_{period}").emit
                if getattr(self, attr) != now.day:
                    setattr(self, attr, now.day)
                    if period == 'bedtime':
                        self.is_bedtime = True
                    elif period == 'wake':
                        self.is_bedtime = False
                    signal()
    
    def _check_time_match(self, hour, minute, time_str):
        try:
            h, m = map(int, time_str.split(":"))
            return hour == h and minute == m
        except:
            return False
    
    def force_idle(self):
        self.idle_trigger.emit()
        self._reset_idle_timer()
    
    def force_check_weather(self, city=""):
        if city:
            self.config["weather_city"] = city
        self._weather_cooldown = 0
        self._check_weather()
