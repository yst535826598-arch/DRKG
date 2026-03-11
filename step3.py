import os
import pickle  # 新增：用于高效、小体积保存数据的原生库
import copy    # 新增：用于替代 eval(str()) 的深拷贝库
from py2neo import *
import chromadb
from utils.KG_function import *
from utils.LLM_function import *
from utils.Vector_Database_function import *
import config

config.init_config()

def step1_load_entitys_embedding(load_entitys_embedding,deposits_path,final_path,date):
    embedding_load_history={}
    full_word_table_entitys={}
    if load_entitys_embedding:
        print("正在加载实体嵌入表")
        # 【修改】使用 pickle 二进制读取，防内存溢出
        with open(os.path.join(final_path,"{}实体嵌入表加载历史.pkl".format(date)),'rb') as file:
            embedding_load_history=pickle.load(file)
        # 【修改】使用 copy.deepcopy 替代 eval(str())
        full_word_table_entitys=copy.deepcopy(embedding_load_history['full_word_table_entitys'])
        
        print(len(full_word_table_entitys))
        for en in full_word_table_entitys.keys():
            em=full_word_table_entitys[en]['嵌入向量']
            add_attribute_to_chromadb(collection_entitys,en,em)
        
    deposits=os.listdir(deposits_path)
    for t_deposit in deposits:
        if load_merge_history is True:
            print("载入对齐历史，跳过实例载入")
            break
        deposit=t_deposit
        if embedding_load_history.get(deposit,-100)!=-100:
            print("已恢复并略过{}".format(deposit))
            continue
        folder_path=os.path.join(deposits_path,t_deposit)
        deposits_files=os.listdir(folder_path)
        for deposits_file in deposits_files:
            if deposits_file.find(str(date))==-1:
                continue
            # 原始输入文件仍然使用 eval 读取，保持与你原数据兼容
            with open(os.path.join(folder_path,deposits_file),'r',encoding='utf-8') as file:
                texts=file.readline()
                deposit_dict=eval(texts)
            
            temp_word_table_entity=deposit_dict["实例词表"]
            temp_triplet=deposit_dict["全部三元组"]
                    #add_attribute_to_chromadb(collection_addition,word,emb)
            for word in temp_word_table_entity.keys():#full_word_table_entity
                if full_word_table_entitys.get(word,-100)==-100 :
                    full_word_table_entitys[word]=temp_word_table_entity[word]
                    emb=temp_word_table_entity[word]['嵌入向量']
                    t_label=temp_word_table_entity[word]['类型']
                    add_attribute_to_chromadb(collection_entitys,word,emb)
                
            for tlabel in deposit_dict.keys():
                if tlabel=='全部三元组' or tlabel=='实例词表' or tlabel=='扩展词表'or tlabel=="词类型嵌入表"or tlabel=="属性表"or tlabel=="论文数量":
                    continue
                for entitys in deposit_dict[tlabel].keys():
                    if full_word_table_entitys.get(entitys,-100)==-100:
                        full_word_table_entitys[entitys]={}
                        full_word_table_entitys[entitys]['标签']=tlabel

                        full_word_table_entitys[entitys]['唯一性']="不明"
                        full_word_table_entitys[entitys]['类型']="不明"
                        emb=my_embeddings_fuction(entitys)
                        full_word_table_entitys[entitys]['嵌入向量']=emb
                        add_attribute_to_chromadb(collection_entitys,entitys,emb)

            
        embedding_load_history[deposit]=1
        embedding_load_history['full_word_table_entitys']=full_word_table_entitys
        # 【修改】使用 pickle 二进制保存
        with open(os.path.join(final_path,"{}实体嵌入表加载历史.pkl".format(date)), "wb") as f:
            pickle.dump(embedding_load_history, f)
    return full_word_table_entitys

def step2_merge_all(load_merge_history,recover,full_word_table_entitys,final_path,date):
    if load_merge_history is False:
        merage_protect_entity={}
        merge_history_entitys={}
        save_the_graph={}
        # 【修改】深拷贝替代 eval(str())
        word_table_entity_mirror=copy.deepcopy(full_word_table_entitys)
        full=len(word_table_entity_mirror)
        if recover is True:
            # 【修改】使用 pickle 二进制读取
            with open(os.path.join(final_path,"{}对齐中间备份.pkl".format(date)),'rb') as file:
                save_the_graph=pickle.load(file)
            merge_history_entitys=save_the_graph['实例对齐记录']
            full_word_table_entitys=save_the_graph['对齐后实例词表']
            flag=0
            for word in word_table_entity_mirror.keys():#恢复对齐历史
                flag=flag+1
                res=round((flag/full),3)
                print("恢复对齐进度{}%".format(res*100))
                if merge_history_entitys.get(word,-100)!=-100:
                    emb=word_table_entity_mirror[word]['嵌入向量']
                    similar,similarID,similar_distance=determine_attribute_distance(collection_entitys,emb,2)
                    if similar[0]==word:
                        collection_entitys.delete(ids=[similarID[0]])
                    continue
        flag=0
        for word in word_table_entity_mirror.keys():#以后加个已完成百分比
            flag=flag+1
            res=round((flag/full),3)
            print("对齐进度{}%".format(res*100))
            if merge_history_entitys.get(word,-100)!=-100:
                continue
            # 【修改】深拷贝替代 eval(str())
            merge_history_entitys[word]=copy.deepcopy(full_word_table_entitys[word])
            merge_history_entitys[word]['名称']=word
            emb=word_table_entity_mirror[word]['嵌入向量']
            similar,similarID,similar_distance=determine_attribute_distance(collection_entitys,emb,10)
            mapping={}
            array_4_aligen=[]
            for code in range(0,len(similar)):
                distance=similar_distance[code]
                if distance<global_distance:
                    array_4_aligen.append(similar[code])
                    mapping[similar[code]]={'ID':similarID[code],
                                            '嵌入向量':word_table_entity_mirror[similar[code]]['嵌入向量'],
                                            '距离':similar_distance[code]
                                            }
            united=level2_merge_special(array_4_aligen)
            if str(united).find('NO')!=-1 or str(united).find('ERROR')!=-1:
                tt_result=[]
                for code in array_4_aligen:
                    if code==word:
                        continue
                    else:
                        tt_result.append(code)
                try:
                    # 【修改】深拷贝替代 eval(str())
                    merge_history_entitys[word]=copy.deepcopy(full_word_table_entitys[tt_result[0]])
                    merge_history_entitys[word]['名称']=tt_result[0]
                    merage_protect_entity[word]=1
                    collection_entitys.delete(ids=[mapping[word]['ID']])
                except:
                    print("array为空")
                continue     
            else:
                print(united)
                head_array=[]
                for one in united:
                    sp=one.split('#')
                    head=sp[0]
                    if mapping.get(head,-100)==-100:
                        print("合并时出现未见词，跳过")
                        continue
                    # 【修改】深拷贝替代 eval(str())
                    merge_history_entitys[head]=copy.deepcopy(full_word_table_entitys[head])
                    merge_history_entitys[head]['名称']=head
                    head_array.append(head)
                    merage_protect_entity[head]=1
                    collection_entitys.delete(ids=[mapping[head]['ID']])
                    for u in range(1,len(sp)):
                        if mapping.get(sp[u],-100)==-100 :
                            print("合并时出现未见词，跳过")
                            continue
                        try:
                            if sp[u]!=head and merage_protect_entity.get(sp[u],-100)==-100:
                                del full_word_table_entitys[sp[u]]
                        except:
                            print("{}已经被删除过".format(sp[u]))
                            continue
                        print("删除{},合并到{}".format(sp[u],head))
                        try:
                            # 【修改】深拷贝替代 eval(str())
                            merge_history_entitys[sp[u]]=copy.deepcopy(full_word_table_entitys[head])
                        except:
                            # 【修改】深拷贝替代 eval(str())
                            merge_history_entitys[sp[u]]=copy.deepcopy(merge_history_entitys[head])
                        merge_history_entitys[sp[u]]['名称']=head
                        collection_entitys.delete(ids=[mapping[sp[u]]['ID']])
            if flag%10==0 and flag!=0:#每10个保存一次
                print("中间过程备份")
                save_the_graph['对齐后实例词表']=full_word_table_entitys
                save_the_graph['实例对齐记录']=merge_history_entitys
                # 【修改】使用 pickle 二进制保存
                with open(os.path.join(final_path,"{}对齐中间备份.pkl".format(date)), "wb") as f:
                    pickle.dump(save_the_graph, f)
        save_the_graph['对齐后实例词表']=full_word_table_entitys
        save_the_graph['实例对齐记录']=merge_history_entitys
        # 【修改】使用 pickle 二进制保存
        with open(os.path.join(final_path,"{}对齐记录.pkl".format(date)), "wb") as f:
            pickle.dump(save_the_graph, f)
    if load_merge_history is True:
        # 【修改】使用 pickle 二进制读取
        with open(os.path.join(final_path,"{}对齐记录.pkl".format(date)),'rb') as file:
            save_the_graph=pickle.load(file)
        merge_history_entitys=save_the_graph['实例对齐记录']
        full_word_table_entitys=save_the_graph['对齐后实例词表']
    return merge_history_entitys,full_word_table_entitys

def step3_load2neo4j(deposit_name,deposit_dict,graph_label_entitys,graph_label_attribute,final_entitys,final_tri):
    paper_number=int(deposit_dict['论文数量'])
    deposit_node=create_node_plus(graph_label_entitys,deposit_name,data={'论文数量':paper_number})
    deposit_node.add_label('矿床')
    graph.push(deposit_node)
    attribute_dict=deposit_dict['数值表']
    for attr_label in attribute_dict.keys():
        for item in attribute_dict[attr_label]:
            t=item['内容'].split('#')
            try:
                entity_data=t[1]
                message=t[0]
                origin=item['来源']
            except:
                print("问题属性"+str(item['内容']))
                continue
            if attr_label=='地球化学异常元素符号':
                att_node=create_node_plus(graph_label_attribute,entity_data)
                att_node.add_label(attr_label)
                graph.push(att_node)
                final_tri=if_relation_exist_plus(deposit_node,att_node,attr_label,final_tri,data=deposit_name)
            else:
                att_node=create_node_plus(graph_label_attribute,entity_data,data={'来源':origin,'描述':message})
                att_node.add_label(attr_label)
                graph.push(att_node)
                final_tri=if_relation_exist_plus(deposit_node,att_node,attr_label,final_tri,data=deposit_name)    
    t_dict={'type':graph_label_entitys,
            'name':deposit_name,
            'additional_type':'矿床',
            'data':'空'}
    final_entitys[deposit_name]=t_dict
    for label in deposit_dict.keys():
        number_for_label=0
        if label=='全部三元组' or label=='实例词表' or label=='扩展词表'or label=="词类型嵌入表"or label=="数值表"or label=="论文数量":
            continue
        for entitys in deposit_dict[label].keys():
            data={}
            deposit_dict[label][entitys] is None
            print(entitys+':')
            if merge_history_entitys.get(entitys,-100)!=-100:
                entity_detial=merge_history_entitys[entitys]
                entitys=entity_detial['名称']
            else:
                try:
                    entity_detial=full_word_table_entitys[entitys]
                except:
                    print(deposit_name)
                    print(entitys)
                    continue
            _only=entity_detial['唯一性']
            
            a_node=create_node_plus(graph_label_entitys,entitys)
            t_dict={'type':[graph_label_entitys],
                    'name':entitys,
                    'additional_type':'空',
                    'data':'空'}
            final_entitys[entitys]=t_dict
            final_tri=if_relation_exist_plus(deposit_node,a_node,label,final_tri,data=deposit_name)
            a_node.add_label(label)
            graph.push(a_node)
            number_for_label=number_for_label+1
        deposit_node=create_node_plus(graph_label_entitys,deposit_name,data={'{}标签下节点数量'.format(str(label)):number_for_label})
    
    tri_array=deposit_dict['全部三元组']
    for tri in tri_array:
        head=tri['head']
        if merge_history_entitys.get(head,-100)!=-100:
            head_detail=merge_history_entitys[head]
            head=head_detail['名称']
        else:
            print("不在实例也不在addition，问题词 略过{}".format(head))
            continue
        tail=tri['tail']
        if merge_history_entitys.get(tail,-100)!=-100:
            tail_detail=merge_history_entitys[tail]
            tail=tail_detail['名称']
        else:
            print("不在实例也不在addition，问题词略过{}".format(tail))
            continue
        relation=tri['relation']
        textID=tri['textID']
        article=tri['article']
        data=article+'#'+textID
        head_node=create_node_plus(graph_label_entitys,head)
        tail_node=create_node_plus(graph_label_entitys,tail)
        final_tri=if_relation_exist_plus(head_node,tail_node,relation,final_tri,data=data)
    return final_entitys,final_tri

if __name__ == '__main__':
    date="1229"
    global_distance=0.6

    #一般开始时候全是False，怕中间出错。全跑完以后系统中出现缓存文件后，第二个和第四个改成True
    load_entitys_embedding=False#假如step1_load_entitys_embedding以后步骤出问题，改True恢复
    load_merge_history=True#假如step2_merge_all以后步骤出问题或者用step1-2结果重新导入图谱，改True恢复。有完整合并结果才能恢复
    merge_recover=False# 假如step2_merge_all自己出问题，改True恢复对齐进度，load_merge_history=True时不执行。 step2_merge_all非常耗时
    load2neo4j=True#对齐完是否直接导入图谱
    graph_label_entitys='{}图谱实体'.format(date)
    graph_label_attribute='{}图谱数值'.format(date)
    deposits_path="./data/{}/step2_result/".format(date)
    final_path="./data/{}/step3_result/".format(date)
    os.makedirs(final_path, exist_ok=True)
    chroma_client = chromadb.Client()
    collection_entitys = chroma_client.create_collection(name='collection_entitys')
    save_the_graph={}
    final_entitys={}
    final_tri=[]
    full_word_table_entitys=step1_load_entitys_embedding(load_entitys_embedding,deposits_path,final_path,date)
    full_word={}
    full_word['对齐前实例词表']=full_word_table_entitys
    
    # 【修改】使用 pickle 二进制保存
    with open(os.path.join(final_path,"{}对齐前记录.pkl".format(date)), "wb") as f:
        pickle.dump(full_word, f)
        
    merge_history_entitys,full_word_table_entitys=step2_merge_all(load_merge_history,merge_recover,full_word_table_entitys,final_path,date)
    
    if load2neo4j is False:
        print("略过导入neo4j")
    else:
        deposit_number=0
        deposits=os.listdir(deposits_path)
        for deposit in deposits:
            deposit_number=deposit_number+1
            print(deposit+"第{}个矿床，总计{}个".format(deposit_number,str(len(deposits))))
            folder_path=os.path.join(deposits_path,deposit)
            deposits_files=os.listdir(folder_path)
            for deposits_file in deposits_files:
                # 原始输入读取不变
                with open(os.path.join(folder_path,deposits_file),'r',encoding='utf-8') as file:
                    texts=file.readline()
                    deposit_dict=eval(texts)
                final_entitys,final_tri=step3_load2neo4j(deposit,deposit_dict,graph_label_entitys,graph_label_attribute,final_entitys,final_tri)        
        
        save_the_graph['对齐后实例词表']=full_word_table_entitys
        save_the_graph['最终实例节点']=final_entitys
        save_the_graph['最终三元组']=final_tri
        
        # 【修改】使用 pickle 二进制保存
        with open(os.path.join(final_path,"{}图谱备份.pkl".format(date)), "wb") as f:
            pickle.dump(save_the_graph, f)