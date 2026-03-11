from py2neo import * 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import os
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram
import config
config.init_config()
graph= Graph(config.args.KGlink, name=config.args.KGname,auth=(config.args.KGcount, config.args.KGcode))

def get_linkage_matrix(model):
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)

    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # 叶子节点
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)

    return linkage_matrix
def plot_dendrogram(model, **kwargs):
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # 叶节点
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count
    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)
 
    dendrogram(linkage_matrix, **kwargs)
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
def weight_jarcard(deposit_name_A,deposit_name_B,label_list,graph_label,node_degree,method="Uniform"):
    score={}
    sum=0
    sum_weight=0
    for label in label_list.keys():
        listA={}
        listB={}
        sum_weight=sum_weight+label_list[label]
        node_query_entitysA = 'MATCH p=(n:`{}`:`矿床`)-[r*1]-(b:`{}`) where n.name="{}"  RETURN distinct b.name'.format(graph_label,label,deposit_name_A)
        node_resultsA = graph.run(node_query_entitysA)
        node_query_entitysB = 'MATCH p=(n:`{}`:`矿床`)-[r*1]-(b:`{}`) where n.name="{}"  RETURN distinct b.name'.format(graph_label,label,deposit_name_B)
        node_resultsB = graph.run(node_query_entitysB)
        #du1=0
        for number in node_resultsA:
            #print(number['count(distinct b.name)'])
            node_name=number['b.name']
            if listA.get(node_name,-100)==-100:
                listA[node_name]=1
        for number in node_resultsB:
            #print(number['count(distinct b.name)'])
            node_name=number['b.name']
            if listB.get(node_name,-100)==-100:
                listB[node_name]=1
        node_query_entitysA = 'MATCH p=(n:`{}`:`矿床`)-[r*1]-(b:`{}`)-[x*1]-(m) where n.name="{}" and  not (m:`矿床`) and  not (b:`矿床`)  RETURN distinct  m.name'.format(graph_label,label,deposit_name_A)
        node_resultsA = graph.run(node_query_entitysA)
        node_query_entitysB = 'MATCH p=(n:`{}`:`矿床`)-[r*1]-(b:`{}`)-[x*1]-(m) where n.name="{}" and  not (m:`矿床`) and  not (b:`矿床`)  RETURN distinct  m.name'.format(graph_label,label,deposit_name_B)
        node_resultsB = graph.run(node_query_entitysB)
        for number in node_resultsA:
            #print(number['count(distinct b.name)'])
            node_name=number['m.name']
            if listA.get(node_name,-100)==-100:
                listA[node_name]=1
        for number in node_resultsB:
            #print(number['count(distinct b.name)'])
            node_name=number['m.name']
            if listB.get(node_name,-100)==-100:
                listB[node_name]=1
        common_elements_array_and = list(set(listA.keys()) & set(listB.keys()))
        common_elements_array_or =list(set(listA.keys()).union(set(listB.keys())))
        if len(common_elements_array_and)==0:
            print("没有共节点")
            label_score=0
            score[label]=label_score
            sum=sum+0
            continue
        else:
            up=float(0)
            down=float(0)
            for i in common_elements_array_and:
                try:
                    up=up+node_degree[label][i][method]#'DC'#Uniform
                except:
                    up=up+0
                    continue
            for i in common_elements_array_or:
                try:
                    down=down+node_degree[label][i][method]

                except:
                    down=down+0
                    continue
            label_score=up/down
        score[label]=label_score
        sum=sum+label_score*label_list[label]
    average=sum/sum_weight
    return average,score
def compute_log_gaussian_weight(degrees, mu, sigma, eps=1e-8):
    """
    计算基于对数高斯核的权重 W(f_k)

    参数:
        degrees (array-like): 节点的度序列，必须 > 0
        mu (float): 对数域中的均值
        sigma (float): 对数域中的标准差，必须 > 0
        eps (float): 防止 log(0) 的小常数（如果 degrees 可能含 0）

    返回:
        np.ndarray: 权重数组，形状与 degrees 相同，取值范围 (0, 1]
    """
    degrees = np.asarray(degrees)
    if np.any(degrees <= 0):
        # 安全处理：加 eps 或报错
        # 这里选择加 eps，但更推荐确保输入合法
        degrees = np.clip(degrees, eps, None)
    
    log_deg = np.log(degrees)
    exponent = - (log_deg - mu) ** 2 / (2 * sigma ** 2)
    weights = np.exp(exponent)
    return weights



def DC_PDF_main(graph_label_entitys,manual_label,deposit_name_dict):
    node_query = "MATCH (n:`{}`:`{}`) where not (n:`矿床`) return distinct n.name".format(graph_label_entitys,manual_label)
    #node_query = "MATCH (n:`{}`) where not (n:`矿床`) return distinct n.name".format(graph_label_entitys)
    node_degree={}
    results = graph.run(node_query)
    PDF_array=[]
    for c in results:
        node_name=c['n.name']
        DC_array='MATCH p=(n:`{}`)-[r*1]-(m:`{}`)  where n.name="{}" and n.name<>m.name and not (m:`矿床`)   RETURN count (distinct m.name) as num'.format(graph_label_entitys,graph_label_entitys,node_name)
        results1 = graph.run(DC_array)
        Degree_Centrality=0
        node_degree[node_name]={}
        for i in results1:
            Degree_Centrality=int(i['num'])
            node_degree[node_name]['DC']=Degree_Centrality
            break
        deposit_array="MATCH p=(n:`{}`)-[r*1]-(b:`{}`:`矿床`) where n.name='{}' and  n.name<>b.name return count(distinct  b.name )as a".format(graph_label_entitys,graph_label_entitys,node_name)
        try:
            results2 = graph.run(deposit_array)
        except:
            node_degree[node_name]['deposits']=0
            continue
        t=0
        for i in results2:
            t=int(i['a'])
            if t<=1:
                t=0
            else:
                deposit_array="MATCH p=(n:`{}`)-[r*1]-(b:`{}`:`矿床`) where n.name='{}' and  n.name<>b.name return distinct  b.name as a".format(graph_label_entitys,graph_label_entitys,node_name)
                results3 = graph.run(deposit_array)
                for l in results3:
                    deposit_name=l['a']
                    if deposit_name_dict.get(deposit_name,-100)!=-100:
                        t=t+1
            if t<=1:
                node_degree[node_name]['deposits']=0
            else:
                node_degree[node_name]['deposits']=t
                PDF_array.append(t)

            break
    for word in node_degree.keys():
        if node_degree[word]['deposits']<=1:
            continue
        node_degree[word]['Uniform']=float(1)
    return node_degree

if __name__ == '__main__':
    date=config.args.date
    entitys_labels_dict=config.args.KGentity_labels
    code="1"#这次分析的代号，用于区分不同实验的结果数据
    save=True #True 现场计算节点权重（比较费时）并保存。False 总结用保存的节点权重
    output_path="./data/{}/analysis_result/".format(date)
    graph_label_entitys='{}图谱实体'.format(date)
    os.makedirs(output_path, exist_ok=True)
    deposit_name_dict={}
    deposit_query = "MATCH (n:`{}`:`矿床`) return distinct n.name".format(graph_label_entitys)
    results = graph.run(deposit_query)
    deposit_name_array=[]
    for c in results:
        deposit_name=c['n.name']
        deposit_name_array.append(deposit_name)
    artificial_select_deposit=deposit_name_array
    for deposit in deposit_name_array:
        deposit_name_dict[deposit]=1
    DC_PDF_full={}
    count=0
    for manual_label in entitys_labels_dict:
        if save is False:
            break
        count=count+1
        print("{:.2f}%".format(100*count/len(entitys_labels_dict)))
        DC_PDF_label=DC_PDF_main(graph_label_entitys,manual_label,deposit_name_dict)
        DC_PDF_full[manual_label]=DC_PDF_label
    if save is True:
        with open(output_path+"weights{}.txt".format(code), "w",encoding='utf-8') as f:
            f.write(str(DC_PDF_full))
    else:
        with open(output_path+"weights{}.txt".format(code),'r',encoding='utf-8') as file:
            texts=file.readline()
            DC_PDF_full=eval(texts)
    my_distance_metric=np.zeros((len(deposit_name_array), len(deposit_name_array)))
    distance_4_heatmap={}
    for label in entitys_labels_dict.keys():
        distance_4_heatmap[label]=np.zeros((len(deposit_name_array), len(deposit_name_array)))
    for deposit_code_A in range(0,len(deposit_name_array)):
        for deposit_code_B in range(deposit_code_A+1,len(deposit_name_array)):
            print(deposit_name_array[deposit_code_A])
            print(deposit_name_array[deposit_code_B])
            score,for_heatmap=weight_jarcard(deposit_name_array[deposit_code_A],deposit_name_array[deposit_code_B],entitys_labels_dict,graph_label_entitys,DC_PDF_full,method='Uniform') # 'Uniform'节点等权重 'DC' 节点点度中心性做权重
            print("相似度为{}".format(str(score)))
            my_distance_metric[deposit_code_A][deposit_code_B]=score
            my_distance_metric[deposit_code_B][deposit_code_A]=score
    distance_matrix = my_distance_metric.max() - my_distance_metric
    for i in range(0,len(deposit_name_array)):
        distance_matrix[i][i]=0

    print(my_distance_metric)
    model = AgglomerativeClustering(distance_threshold=0, n_clusters=None,metric="precomputed",linkage="complete")#complete
    # fit进行数据拟合后，可以通过 labels_ 属性获取每个样本的类别标签。
    model = model.fit(distance_matrix)
    #plt.figure(figsize=(50, 50))
    plt.tight_layout()
    plt.rcParams['font.size'] = 5
    plt.title("Hierarchical Clustering Dendrogram{}".format(code))


    # 1. 动态加载同目录下的字体文件（确保文件名与你上传的一致）
    font_manager.fontManager.addfont('/mnt/c/Windows/Fonts/msyh.ttc') 

    # 2. 设置全局字体为刚才加载的字体
    plt.rcParams['font.family'] = ['sans-serif']
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 如果用的是黑体，这里改为 ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False # 顺便解决坐标轴负号变方块的问题
    # 绘制树状图的前三个层级
    #plot_dendrogram(model, truncate_mode="level",labels=artificial_set_deposit)
    plot_dendrogram(model,labels=artificial_select_deposit,leaf_font_size=7,leaf_rotation=0,orientation="right")
    #plt.xlabel("Number of points in node (or index of point if no parenthesis)")
    #plt.tick_params(labelsize=14)
    plt.show()
    print(1)

