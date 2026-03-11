from py2neo import * 
import csv
import os
from utils.KG_function import *
import config
config.init_config()
graph= Graph(config.args.KGlink, name=config.args.KGname,auth=(config.args.KGcount, config.args.KGcode))


def find_same_from_dic(word,mydict,time):
    if mydict.get(word,-100)==-100 or time<0:
        return '无'
    same=mydict[word]['same']
    if same=='无':
        return same
    else:
        if mydict[same]['same']!='无':
            return find_same_from_dic(same,mydict,time-1)
        else:
            return same
def get_connected_entities_by_label(deposit_name_A,label_list,graph_label):#得加个权重
    t_results={}
    for label in label_list.keys():
        node_query_entitysA = 'MATCH p=(n:`{}`:`矿床`)-[r*1]-(b:`{}`) where n.name="{}"  RETURN distinct b.name'.format(graph_label,label,deposit_name_A)
        node_resultsA = graph.run(node_query_entitysA)
        listA=[]
        for number in node_resultsA:
            node_name=number['b.name']
            listA.append(node_name)
        t_results[label]=listA
    return t_results
if __name__ == '__main__':
    date=config.args.date
    entitys_labels_dict=config.args.KGentity_labels
    graph_label_entitys='{}图谱实体'.format(date)
    output_path="./data/{}/analysis_result/".format(date)
    os.makedirs(output_path, exist_ok=True)
    deposits_name=["巴西","常家大林","东北寨","二台子","格尔托","黄石关"]#手动指定矿床
    code="D"#用于区分不同矿床种类的统计
    frequence_list={}
    for label in entitys_labels_dict.keys():
        frequence_list[label]={}
    for deposit_name in deposits_name:
        print(deposit_name)
        t_result=get_connected_entities_by_label(deposit_name,entitys_labels_dict,graph_label_entitys)
        for label in t_result.keys():
            for node in t_result[label]:
                if frequence_list[label].get(node,-100)==-100:
                    frequence_list[label][node]=1
                else:
                    frequence_list[label][node]=frequence_list[label][node]+1

    for label in frequence_list.keys():
        print(label)
        sorted_dict = dict(sorted(frequence_list[label].items(), key=lambda item: item[1], reverse=True))
        data=[]
        for i in sorted_dict.keys():
            t={}
            t['节点名称']=i
            t['占比']=sorted_dict[i]/len(deposits_name)
            data.append(t)
        csv_file_path = output_path+'词频统计{}{}.csv'.format(code,label)
        fieldnames=['节点名称','占比']  
        with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:  
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)  
            writer.writeheader()  
            writer.writerows(data)



