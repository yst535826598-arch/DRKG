import os
import shutil  
from utils.LLM_function import *
import config
config.init_config()
def move_file(src_file, dst_folder):
    shutil.move(src_file, dst_folder)
def step1_read_file(file_path):
    with open(file_path,'r',encoding='utf-8') as file:
        texts=file.readline()
        text_dict_origin=eval(texts)
    text_dict={}
    id=''
    for id in text_dict_origin:
        if len(text_dict_origin[id]['text'])<10:
            print(text_dict_origin[id]['text'])
            print(1)
            continue
        text_dict[id]={}
        text_dict[id]['矿床']=deposit_name
        text_dict[id]['文本']=text_dict_origin[id]['text']
        text_dict[id]['抽取的实体']={}
        text_dict[id]['抽取的三元组']=[]
    return text_dict
def step2_NER_NC_RC(my_text,entitys_labels_dict):
    final={}
    entity,figure=level1_entity_multiple_strategy(my_text,strategy='multiple',repetitions=2)
    print("获得如下地质概念:"+str(entity))
    if entity=="ERROR" or len(entity)<1:
        return "ERROR","ERROR","ERROR"
    print("执行逐个划分标签")
    get_label={}
    entitys_labels_array=[]
    for label in entitys_labels_dict.keys():
        entitys_labels_array.append(label)
    entitys_labels_array.append('数值与公式')
    for two in entity:  
        get_label[two]=level1_entity_label_single(two,my_text,label=entitys_labels_array)
    print("获得如下地质概念的标签:"+str(get_label))
    temp_get_label=eval(str(get_label))
    for word1 in temp_get_label.keys():
        if temp_get_label[word1]=='数值与公式':
            get_label.pop(word1)
    entity=[]
    for word1 in get_label.keys():      
        entity.append(word1)
    if len(figure)<1 or figure=="ERROR":
        figure_label="ERROR"
        print("此片段无数值型信息")
    else:
        print("执行逐个划分标签")
        figure_label={}
        for two in figure:  
            st=level1_entity_label_single(two,my_text,label=figure_array)
            if st=='ERROR':
                continue
            figure_label[two]=st
    if figure_label=="ERROR":
        figure_label={}
    print("获得如下数值的标签:"+str(figure_label))
    for un in get_label.keys():
        label=get_label[un]
        if label.find('金矿')!=-1:
            print(un)
            print("这是个金矿，略过")
            continue
        answer='无'
        for c in entitys_labels_dict.keys():
            if label.find(c)!=-1 and c!='数值与公式':
                label=c
                answer=label
                break
            else:
                answer=get_label[un]
        final[un]=answer
    my_ex_time=0
    triple_2=[]
    triple_1="ERROR"
    while(my_ex_time<2):
        if my_ex_time==0:
            mtime=0
            while(triple_1=="ERROR"and mtime<2):
                mtime=mtime+1
                triple_1=level2_relation_extract(entity,my_text)
                if type(triple_1) is not list:
                    print('{}次'.format(str(mtime)))
                    triple_1="ERROR"
                    continue
            my_ex_time=my_ex_time+1
            continue
        if triple_1=="ERROR":
            triple_2=[]
            break
        for i in triple_1:
            sp=str(i).split('#')
            try:
                head=sp[0]
                tail=sp[1]
                relation=sp[2]
            except:
                continue 
            if final.get(head,-100)!=-100 and final.get(tail,-100)!=-100:        
                triple_2.append(i)
        my_ex_time=my_ex_time+1
        break
    return final,triple_2,figure_label
def step3_categorize(text_dict2):
    unite={}
    full_word={}
    merge_history={}
    mai_entity_list={}
    figure_list={}
    for labeli in figure_array:
        figure_list[labeli]=[]
    for i in text_dict2.keys():
        unite[i]=text_dict2[i]['抽取的实体']
        t_figure_list=text_dict2[i]['抽取的数值']
        for name in t_figure_list.keys():
            if figure_list.get(t_figure_list[name],-100)==-100 and t_figure_list[name]!="其他数值或符号":
                figure_list[t_figure_list[name]]=[]
                figure_dict={'内容':name,'来源':deposit_name+'#'+files+'#'+i}
                figure_list[t_figure_list[name]].append(figure_dict)
            else:
                figure_dict={'内容':name,'来源':deposit_name+'#'+files+'#'+i}
                figure_list[t_figure_list[name]].append(figure_dict)


    for i in unite.keys():
        t=unite[i]
        for l in t.keys():
            mai_entity_list[l]=t[l]
            label=t[l]
            if temp_label.get(label,-100)==-100:
                temp_label[label]={}
                temp_label[label][l]=[i]
                continue
            if temp_label[label].get(l,-100)==-100:
                temp_label[label][l]=[i]
            else:
                temp_label[label][l].append(i)
    temp_tri=[]
    for text in text_dict2.keys():
        triplet=text_dict2[text]['抽取的三元组']
        for tri in triplet:
            sp=str(tri).split('#')
            try:
                head=sp[0]
                tail=sp[1]
                relation=sp[2]
            except:
                continue
            if merge_history.get(head,-100)!=-100:
                head=merge_history[head]
            if merge_history.get(tail,-100)!=-100:
                tail=merge_history[tail]
            temp_tri.append({
                'head':head,
                'tail':tail,
                'relation':relation,
                'textID':text
                #'article':files,                   
                })
            full_word[head]=1
            full_word[tail]=1

    temp_label['全部三元组']=temp_tri
    final_word_array_addition={}
    final_word_array_entity={}
    for word in full_word.keys():            
        if mai_entity_list.get(word,-100)!=-100:
            final_word_array_entity[word]={'类型': '不明', '唯一性': '不明','标签':mai_entity_list[word]}
        else:
            final_word_array_addition[word]={'类型': '不明', '唯一性': '不明','标签':'非矿床属性实例'}

    #把所有数值综合到一起
    return final_word_array_entity,final_word_array_addition,figure_list


if __name__ == '__main__':
    #第一步抽取  假如出问题重启代码即可，有恢复进度功能
    date=config.args.date
    origin_path="./data/{}/origin/".format(date)
    result_path="./data/{}/step1_result/".format(date)
    figure_array=config.args.KGfigure_labels
    entitys_labels_dict=config.args.KGentity_labels
    mission=os.listdir(origin_path)
    for deposit_name in mission:
        result_path1=os.path.join(result_path,deposit_name)
        deposits_files_path=os.path.join(origin_path,deposit_name)
        folder=os.listdir(deposits_files_path)
        for files in folder:
            print(deposit_name)
            print(files)
            save={}
            temp_label={}
            for label in entitys_labels_dict.keys():
                if label=='数值与公式':
                    continue
                temp_label[label]={}
            target_file_path=os.path.join(deposits_files_path,files)
            #deposit_file_path=os.path.join(move_path,deposit_name)
            if os.path.exists(os.path.join(result_path1,'{}抽取结果#'.format(date)+files)) is True:
                print("略过一个已抽取完成文件")
                continue
            else:
                os.makedirs(result_path1, exist_ok=True)
            text_dict=step1_read_file(target_file_path)                  
            print("完成读取")
            for text_id in text_dict.keys():

                my_text=text_dict[text_id]['文本']            
                #print(my_text)
                entitys,triples,figures=step2_NER_NC_RC(my_text,entitys_labels_dict)
                if entitys=="ERROR":
                    continue
                save[text_id]={}
                save[text_id]['抽取的实体']=entitys
                save[text_id]['抽取的三元组']=triples
                save[text_id]['抽取的数值']=figures
            #with open(os.path.join(result_path,"{}抽取结果".format(date)+'#'+files), "w",encoding='utf-8') as f:
            #    f.write(str(save))
            #print("开始汇总")
            text_dict2=eval(str(save))        
            final_word_array_entity,final_word_array_addition,figure_list=step3_categorize(text_dict2)
            temp_label['实例词表']=final_word_array_entity
            temp_label['扩展词表']=final_word_array_addition
            temp_label['数值表']=figure_list
            with open(os.path.join(result_path1,'{}抽取结果#'.format(date)+files), "w",encoding='utf-8') as f:
                f.write(str(temp_label))
            #move_file(os.path.join(deposits_files_path,files),os.path.join(deposit_file_path,files))#move_path
        #chroma_client.delete_collection(name='collection_entity{}'.format(str(deposit_number)))
        #deposit_number=deposit_number+1
