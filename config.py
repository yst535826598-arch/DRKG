# config.py
import argparse
from typing import Optional

# 全局配置对象（在导入时初始化为 None）
args: Optional[argparse.Namespace] = None

def init_config():
    global args
    if args is not None:
        return  # 已初始化
    figure_array=['地球化学异常元素符号','成矿深度',
                '成矿温度',
                '其他温度',
                '成矿时间或年代',
                '其他时间或年代',
                '矿体尺寸',
                '元素比值',
                '公式',
                '其他数值或符号',
                '蚀变带宽度']
    entitys_labels_dict={'地层':1,
                '区域构造背景':1,
                '沉积岩':1,#待定
                '变质岩':1,
                '褶皱':1,
                '断裂':1,
                '剪切带':1,
                '节理':1,#待定
                '侵入岩':1,#待定
                '火山岩':1,#待定
                '脉岩':1,#待定
                '变质作用':1,#
                '蚀变':1,
                '矿石与矿物':1,
                '围岩':1
                }
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, default="1229")
    parser.add_argument('--APIKEY', type=str, default="sk-7c36adfd428542d0b2400963c1da396c")
    parser.add_argument('--URL', type=str, default="https://dashscope.aliyuncs.com/compatible-mode/v1")    
    parser.add_argument('--model', type=str, default="qwen3-235b-a22b-instruct-2507")
    parser.add_argument('--embedding_model', type=str, default="text-embedding-v4")#默认是上面URL提供的
    parser.add_argument('--KGlink', type=str, default="bolt://localhost:7687")
    parser.add_argument('--KGname', type=str, default="neo4j")
    parser.add_argument('--KGcount', type=str, default="neo4j")
    parser.add_argument('--KGcode', type=str, default="neo4j@openspg")
    parser.add_argument('--KGentity_labels', type=dict, default=entitys_labels_dict)
    parser.add_argument('--KGfigure_labels', type=dict, default=figure_array)
    args = parser.parse_args()

    # 可选：打印配置
    print(f"[CONFIG] APIKEY: {args.APIKEY}, URL: {args.URL}, MODEL: {args.model}")