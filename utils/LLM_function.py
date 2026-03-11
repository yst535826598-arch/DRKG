from openai import OpenAI
import time
import config
config.init_config()
def ask_llm_base(question,system_prompt='你是一名地质专家，我需要你回答一些专业地质问题。',mykey=config.args.APIKEY,mybase_url=config.args.URL,mymodel=config.args.model):
    time.sleep(0.05)
    client = OpenAI(
        api_key=mykey,  # 替换成真实DashScope的API_KEY
        base_url=mybase_url,  # 填写DashScope服务endpoint
    )
    chat_completion = client.chat.completions.create(
    temperature=0.5,
    model=mymodel,
    messages=[
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': question
            }
        ],
    max_tokens=1000,
    )
    return chat_completion.choices[0].message.content
def llm_check_part_array(p1,p2,time=3,mymodel='default'):
    flag=time
    while(flag):
        if mymodel!='default':
            answer=ask_llm_base(question=p2,system_prompt=p1,mymodel=mymodel)
        else:
            answer=ask_llm_base(question=p2,system_prompt=p1)
        print(answer)
        start=answer.find('ARRAYSTART')
        end=answer.find('ARRAYEND')
        if start!=-1 and end!=-1:
            mydict=answer[start+11:end]
            try:
                start=mydict.find('[')
                end=mydict.rfind(']')
                mydict=mydict[start:end+1]
                mydict=mydict.replace('/','')
                mydict=eval(mydict)
                if type(mydict) is not list or type(mydict) is tuple:
                    raise KeyError
                break
            except:
                print("回答不合格，重复中")
                print(answer)
                flag=flag-1
                continue
        else:            
            print("回答不合格，重复中")
            print(answer)
            flag=flag-1
            continue
    if flag==0:
        return "ERROR"
    return mydict 
def llm_check_part_dict(p1,p2,time=3,mymodel='default'):
    flag=time
    while(flag):
        if mymodel!='default':
            answer=ask_llm_base(question=p2,system_prompt=p1,mymodel=mymodel)
        else:
            answer=ask_llm_base(question=p2,system_prompt=p1)
        print(answer)
        start=answer.find('ARRAYSTART')
        end=answer.find('ARRAYEND')
        if start!=-1 and end!=-1:
            mydict=answer[start+11:end]
            try:
                start=mydict.find('{')
                end=mydict.rfind('}')
                mydict=mydict[start:end+1]
                mydict=mydict.replace('/','')
                mydict=eval(mydict)
                if type(mydict) is not dict or type(mydict) is tuple:
                    print(mydict)
                    raise ValueError("发现非字典输出")
                break
            except:
                print("回答不合格，重复中")
                print(answer)
                flag=flag-1
                continue
        else:            
            print("回答不合格，重复中")
            print(answer)
            flag=flag-1
            continue
    if flag==0:
        return "ERROR"
    return mydict 
def llm_check_YESNO(p1,p2,time=3,mymodel='default'):
    flag=time
    while(flag):
        if mymodel!='default':
            answer=ask_llm_base(question=p2,system_prompt=p1,mymodel=mymodel)
        else:
            answer=ask_llm_base(question=p2,system_prompt=p1)
        print(answer)
        start=answer.find('ARRAYSTART')
        end=answer.find('ARRAYEND')
        reason=answer[end+9:]
        if start!=-1 and end!=-1:
            mydict=answer[start+11:end]
            try:
                if mydict.find('YES')!=-1:
                    return True,reason
                if mydict.find('NO')!=-1:
                    return False,reason
                break
            except:
                print("回答不合格，重复中")
                print(answer)
                flag=flag-1
                continue
        else:            
            print("回答不合格，重复中")
            print(answer)
            flag=flag-1
            continue
    if flag==0:
        return False,"空"
    return False,"空"
def level2_check(question,answer):
    p1="你是一名地质专家，我需要你协助我确认收集的信息是否有明显错误。如果有错误，请简短指出并提供改正方法"
    p2="信息收集是通过问答的形式进行的，完整的问题如下："+question+"获得信息如下："+answer+"\n.如果收集到的信息有明显错误，例如回答不符合问题要求、收集的信息与原文不符，请回答NO。如果没有明显错误，请回答YES。你在回答划分结果时必须严格遵守以下的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。格式样例:ARRAYSTART YES或NO ARRAYEND "
    mydict,reason=llm_check_YESNO(p1,p2,time=3)      
    return mydict,reason
def level1_entity(text):
    p1="你是一名地质专家，你的任务是从一段话中抽取地质实例。由于矿床名称在其他步骤中已提取，你回答的地质实例不应包括具体矿床，例如坪水金矿。你应全程使用中文回答。"
    p2="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含其他的抽象地质概念和地质实例，你的任务就是从中提取这些地质实例。你需要注意你只能从信息中抽取除矿床以外的地质实例，而非抽象地质概念。具体来说，板块是一个抽象地质概念，而太平洋板块是这个抽象地质概念下的一个地质实例并且不是一个具体的矿床，所以你应选择太平洋板块，同时忽略俯冲太平洋板块这样的同义词，其他地质实例以此类推。同时诸如你的回答必须严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['除金矿床以外的地质概念或实体'] ARRAYEND 你要抽取的一段话是:"+text
    check_part="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含其他的抽象地质概念和地质实例，你的任务就是从中提取这些地质实例。你需要注意你只能从信息中抽取除矿床以外的地质实例，而非抽象地质概念。具体来说，板块是一个抽象地质概念，而太平洋板块是这个抽象地质概念下的一个地质实例并且不是一个具体的矿床，所以你应选择太平洋板块，同时忽略俯冲太平洋板块这样的同义词，其他地质实例以此类推。你要抽取的一段话是:"+text
    my_time=4
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=3)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:
           print(mydict)
           return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level1_entity_forPhenomenon(text):
    p1="你是一名地质专家，你的任务是从一段话中抽取明确且信息丰富的地质现象，具体指地质运动时期、矿化蚀变、变质作用、侵入事件等抽象的地质现象或概念，不包括各种公式、数值、及函数。由于矿床名称在其他步骤中已提取，你回答的内容不应包括具体矿床，例如坪水金矿。你应全程使用中文回答。"
    p2="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含地质现象或概念，你的任务就是从中提取这些地质现象或概念。你需要注意你只能从信息中抽取除矿床以外的地质现象，而非地质实例。具体来说，碳酸盐是一个具体的沉积岩类型，而碳酸盐化是与碳酸盐相关的一种矿化蚀变现象并且不是一个具体的矿床，所以你应选择碳酸盐化，同时忽略强烈碳酸盐化这样的同义词，其他地质现象以此类推。此外，例如俯冲与太平洋板块俯冲，由于俯冲的概念过于宽泛，不符合明确且信息丰富的要求，你应回答太平洋板块俯冲，其他地质现象以此类推。你的回答必须严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['除金矿床以外的地质现象'] ARRAYEND 你要抽取的一段话是:"+text
    check_part="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含地质现象或概念，你的任务就是从中提取这些地质现象或概念。你需要注意你只能从信息中抽取除矿床以外的地质现象，而非地质实例。具体来说，碳酸盐是一个具体的沉积岩类型，而碳酸盐化是与碳酸盐相关的一种矿化蚀变并且不是一个具体的矿床，所以你应选择碳酸盐化，同时忽略强烈碳酸盐化这样的同义词，其他地质现象以此类推。此外，例如俯冲与太平洋板块俯冲，由于俯冲的概念过于宽泛，不符合明确且信息丰富的要求，你应回答太平洋板块俯冲，其他地质现象以此类推。你要抽取的一段话是:"+text
    my_time=4
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=3)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:
           print(mydict)
           return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level1_entity_forConcept(text):
    p1="你是一名地质专家，你的任务是从一段话中抽取明确且信息丰富的地质概念与名词，具体指地质上的矿物、岩石、地层、褶皱、断裂等不唯一但具备统一特征的一类地质概念与名词，不包括各种公式、数值、及函数。例如黄铁矿，泛指一类硫化物矿物;花岗岩，泛指一类侵入岩;走滑断裂，泛指一类断裂;Au异常，泛指Au元素异常高值。由于矿床名称在其他步骤中已提取，你回答的内容不应包括具体矿床，例如坪水金矿。你应全程使用中文回答。"
    p2="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含地质概念与名词，你的任务就是从中提取不唯一但具备统一特征的一类地质概念与名词。你需要注意你只能从信息中抽取除矿床以外的地质现象，而非地质实例。具体来说，碳酸盐是一类具体的沉积岩类型，而碳酸盐化是与碳酸盐相关的一种矿化蚀变现象并且不是一个具体的矿床，所以你应选择碳酸盐;板岩是一类低级变质岩，杨家店板岩特指某区域的板岩，你应选择板岩。其他地质概念与名词以此类推。此外，例如俯冲与太平洋板块俯冲，由于俯冲的概念过于宽泛，不符合明确且信息丰富的要求，你应回答太平洋板块俯冲，其他地质现象以此类推。你的回答必须严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['除金矿床以外的地质现象'] ARRAYEND 你要抽取的一段话是:"+text
    check_part="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含地质概念与名词，你的任务就是从中提取不唯一但具备统一特征的一类地质概念与名词。你需要注意你只能从信息中抽取除矿床以外的地质现象，而非地质实例。具体来说，碳酸盐是一类具体的沉积岩类型，而碳酸盐化是与碳酸盐相关的一种矿化蚀变现象并且不是一个具体的矿床，所以你应选择碳酸盐;板岩是一类低级变质岩，杨家店板岩特指某区域的板岩，你应选择板岩。其他地质现象以此类推。你要抽取的一段话是:"+text
    my_time=4
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=3)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:
           print(mydict)
           return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level1_entity_forExample(text):
    p1="你是一名地质专家，你的任务是从一段话中抽取地质实例，不包括各种公式、数值、及函数。由于矿床名称在其他步骤中已提取，你回答的地质实例不应包括具体矿床，例如坪水金矿。你应全程使用中文回答。"
    p2="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含地质实例，你的任务就是从中提取这些地质实例。你需要注意你只能从信息中抽取除矿床以外的地质实例，而非抽象地质概念。具体来说，板块是一个抽象地质概念，而太平洋板块是这个抽象地质概念下的一个地质实例并且不是一个具体的矿床，所以你应选择太平洋板块，同时忽略俯冲太平洋板块这样的同义词，其他地质实例以此类推，例如特指泥盆系形成的地层的:泥盆系地层;某条山沟:李家沟;。同时诸如你的回答必须严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['除金矿床以外的地质实体'] ARRAYEND 你要抽取的一段话是:"+text
    check_part="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含地质实例，你的任务就是从中提取这些地质实例。你需要注意你只能从信息中抽取除矿床以外的地质实例，而非抽象地质概念。具体来说，板块是一个抽象地质概念，而太平洋板块是这个抽象地质概念下的一个地质实例并且不是一个具体的矿床，所以你应选择太平洋板块，同时忽略俯冲太平洋板块这样的同义词，其他地质实例以此类推。你要抽取的一段话是:"+text
    my_time=4
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=3)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:
           print(mydict)
           return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level1_entity_forfigure(text):
    p1="你是一名地质专家，你的任务是从一段话中抽取具备地质意义的数字或者符号形式的矿床信息。由于矿床名称在其他步骤中已提取，你回答的地质实例不应包括具体矿床，例如坪水金矿。你应全程使用中文回答。"
    p2="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含数字或者符号形式的矿床信息，你的任务就是从中提取这些矿床信息。你需要注意这些信息大多表现为数学符号或者数字形式，例如：成矿年龄225Ma中的225Ma、成矿深度20KM 中的20KM、元素异常组合Au-Ag-Pb中的Au和Ag和Pb，其他以此类推。你需要注意你应同时用一个词来回答这个数值或字符的含义，同时对于元素异常组合这样的包含数个字符的请分开回答，如果文字中没有任何数值或者符号类信息请回答无。你的回答必须严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['含义1#数字或者符号1','含义2#数字或者符号2'] ARRAYEND  没有任何符合要求信息时回答ARRAYSTART ['无#无'] ARRAYEND     你要抽取的一段话是:"+text
    check_part="我会给出一段话，这段话描述一个矿床的部分属性。这些属性里包含数字或者符号形式的矿床信息，你的任务就是从中提取这些矿床信息。你需要注意这些信息大多表现为数学符号或者数字形式，例如：成矿年龄225Ma中的225Ma、成矿深度20KM 中的20KM、元素异常组合Au-Ag-Pb中的Au和Ag和Pb，其他以此类推。你需要注意你应同时用一个词来回答这个数值或字符的含义，同时对于元素异常组合这样的包含数个字符的请分开回答，如果文字中没有任何数值或者符号类信息请回答无。你的回答必须严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['含义1#数字或者符号1','含义2#数字或者符号2'] ARRAYEND  没有任何符合要求信息时回答ARRAYSTART ['无#无'] ARRAYEND     你要抽取的一段话是:"+text
    my_time=1
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=3)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:
           print(mydict)
           return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level1_entity_multiple_strategy(text,strategy='single',repetitions=1):#multiple
    flag=0
    result_dict={}
    result_array=[]
    result_dict_figure={}
    result_array_figure=[]
    if strategy=='single':
        while(flag<repetitions):
            flag=flag+1
            entitys=level1_entity(text)
            for i in entitys:
                if result_dict.get(i,-100)==-100:
                    result_dict[i]=1
    if strategy=='multiple':
        while(flag<repetitions):
            flag=flag+1
            entitys_Phenomenon=level1_entity_forPhenomenon(text)
            entitys_Example=level1_entity_forExample(text)
            entitys_Concept=level1_entity_forConcept(text)
            entitys_figure=level1_entity_forfigure(text)
            for i in entitys_Concept:
                if result_dict.get(i,-100)==-100:
                    result_dict[i]=1
            for i in entitys_Example:
                if result_dict.get(i,-100)==-100:
                    result_dict[i]=1
            for i in entitys_Phenomenon:
                if result_dict.get(i,-100)==-100:
                    result_dict[i]=1
            for i in entitys_figure:
                if result_dict_figure.get(i,-100)==-100 and i!='无#无':
                    result_dict_figure[i]=1
    for entity in result_dict.keys():
        result_array.append(entity)
    for entity in result_dict_figure.keys():
        result_array_figure.append(entity)
    return result_array,result_array_figure
def level1_entity_label_single(entity,text,label):
    print(label)
    p1="你是一名地质专家，我需要你阅读一段文字并给指定地质名词划分到指定类别。"
    p2="我现在有一段话和从这段话抽取的一个地质名词[{}]，但我不清楚这个地质名词属于以下哪个类别术语{}。因此你需要依据上下文和词性给这个地质名词划分类别。这些类别术语分别描述了矿床的不同特征和相关构造背景。请注意每个地质名词你只可以回答类别术语中的一个类别,且绝对不能回答所给以外的类别。你在回答划分结果时必须严格遵守python字典的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。".format(str(entity),str(label))+"回答格式样例:ARRAYSTART {'地质名词':'类别'} ARRAYEND 分类样例 '凤太矿集区':'构造背景','黄铁矿':'矿石矿物','星红铺组':'地层'"+" 这个地质名词抽取自这一段话:"+text
    check_part="我现在有一段话和从这段话抽取的一个地质名词[{}]，但我不清楚这个地质名词属于以下哪个类别术语{}。因此你需要依据上下文和词性给这个地质名词划分类别。这些类别术语分别描述了矿床的不同特征和相关构造背景。请注意每个地质名词你只可以回答类别术语中的一个类别,且绝对不能回答所给以外的类别。分类样例 '凤太矿集区':'构造背景','黄铁矿':'矿石矿物','星红铺组':'地层'".format(str(entity),str(label))+" 这些地质名词是{}  抽取自这一段话:".format(str(entity))+text
    my_time=3
    reason=""
    while(my_time>0):
        mydict=llm_check_part_dict(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=3)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:
            flag=0
            for key in mydict.keys():
                for biaozhun in label:
                    try:
                        if mydict[key]==biaozhun or mydict[key].find(biaozhun)!=-1 or biaozhun.find(mydict[key])!=-1:
                            ccc=1
                    except:
                        flag=flag-1
                        continue

                    if mydict[key]==biaozhun or mydict[key].find(biaozhun)!=-1 or biaozhun.find(mydict[key])!=-1:
                       mydict[key]=biaozhun
                       flag=flag+1
                       #print(mydict[key])
                       #print(biaozhun)
                       break
            if flag>=len(mydict) and mydict.get(entity,-100)!=-100:
                return mydict[entity]
            else:
                my_time=my_time-1
                continue
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level2_relation_extract(entity,text):#地层
    p1="你是一名地质专家，你的任务是抽取一段文字中指定词汇间的关系，并以三元组的形式回答。请注意回答的三元组应符合下面提示词中定义的关系并直接、精简、准确、冗余低。"
    p2="我从一段文字中提取到了以下地质概念:{}。这些概念间还有一些关系留在文字中，你需要从中找到这些概念间的关系并回答。你必须回答如下定义的关系：因果关系：事件→事件/事件→实体（岩浆上侵，导致，围岩蚀变）。组成关系：整体→部分（矿石，由...组成，黄铜矿）。来源关系：实体→来源地	（成矿物质，源自，深部流体）。分类关系：实体→类别	（闪锌矿，属于，硫化物）。机制关系：实体→实体，实体通过某种机制受控于/影响另一实体（矿化，受控于，断裂构造；地层A，以断裂B为界；岩体A，侵入，地层B）。演化关系：实体→新实体（石灰岩，变质为，大理岩）。属性关系：实体→特征	（岩体，年龄，135Ma）。时空关系：实体→时间/空间/时空相关的另一实体（铜矿，位于，西藏；形成于，喜山期；热液，经过，裂隙；地层A，地层B，交错产出）。回答格式必须严格遵守严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['头概念#尾概念#关系','头概念#尾概念#关系'] ARRAYEND 这段文字是:".format(str(entity))+text
    check_part="我从一段文字中提取到了以下地质概念:{}。这些概念间还有一些关系留在文字中，你需要从中找到这些概念间的关系并回答。你必须回答如下定义的关系：因果关系：事件→事件/事件→实体（岩浆上侵，导致，围岩蚀变）。组成关系：整体→部分（矿石，由...组成，黄铜矿）。来源关系：实体→来源地	（成矿物质，源自，深部流体）。分类关系：实体→类别	（闪锌矿，属于，硫化物）。机制关系：实体→实体，实体通过某种机制受控于/影响另一实体（矿化，受控于，断裂构造；地层A，以断裂B为界；岩体A，侵入，地层B）。演化关系：实体→新实体（石灰岩，变质为，大理岩）。属性关系：实体→特征	（岩体，年龄，135Ma）。时空关系：实体→时间/空间/时空相关的另一实体（铜矿，位于，西藏；形成于，喜山期；热液，经过，裂隙；地层A，地层B，交错产出）。回答格式必须严格遵守严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['头概念#尾概念#关系','头概念#尾概念#关系'] ARRAYEND 这段文字是:".format(str(entity))+text
    my_time=2
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=5)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:    
            if str(mydict).find('{')!=-1:
                continue
            return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level2_merge_special(entitys):#地层
    p1="你是一名地质专家，你的任务是阅读多个词汇，并回答其中的同义词。"
    p2="我从一篇论文中提取到了以下地质概念:{}。你的任务就是找出其中完全同义的词，并挑选一个最优词，随后回答哪些词会被合并到这个最优词上。只有完全同义的词可以被合并，例如金矿床和含金矿床，方铅矿和方铅矿石。绝对不可将子概念合并到父级概念上，例如方解石与碳酸盐不可以，因为方解石属于碳酸盐，印支组与印支组砂岩不可以因为印支组砂岩是印支组的一部分。请注意如果没有任何可合并的词，请回答NO。回答格式必须严格遵守严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['最优词#被合并词1#被合并词2#被合并词3'] ARRAYEND  无任何可合并词时的回答样例:ARRAYSTART ['NO'] ARRAYEND ".format(str(entitys))
    check_part="我从一篇论文中提取到了以下地质概念:{}。你的任务就是找出其中完全同义的词，并挑选一个最优词，随后回答哪些词会被合并到这个最优词上。只有完全同义的词可以被合并，例如金矿床和含金矿床，方铅矿和方铅矿石。绝对不可将子概念合并到父级概念上，例如方解石与碳酸盐。请注意如果没有任何可合并的词，请回答NO。回答格式必须严格遵守严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。".format(str(entitys))
    my_time=2
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=5)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:           
           return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
def level2_merge_entity2addition(entitys,special):#地层
    p1="你是一名地质专家，你的任务是阅读多个词汇，并回答特定一个词的同义词。"
    p2="我从一篇论文中提取到了以下地质概念词组D:{}，以及一个特定词A:{}。你的任务就是从所给地质概念词组D中，找出特定词A的完全同义的词，随后回答哪些词会被合并到这个特定词上。只有完全同义的词可以被合并，例如金矿床和含金矿床，方铅矿和方铅矿石。绝对不可将子概念合并到父级概念上，例如方解石与碳酸盐不可以，因为方解石属于碳酸盐二者不完全同义，印支组与印支组砂岩不可以因为印支组砂岩是印支组的一部分。请注意如果没有任何可合并的词，请回答NO。回答格式必须严格遵守严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。回答格式样例:ARRAYSTART ['特定词A#被合并词1#被合并词2#被合并词3'] ARRAYEND  无任何可合并词时的回答样例:ARRAYSTART ['NO'] ARRAYEND ".format(str(entitys),special)
    check_part="我从一篇论文中提取到了以下地质概念词组D:{}，以及一个特定词A:{}。你的任务就是从所给地质概念词组D中，找出特定词A的完全同义的词，随后回答哪些词会被合并到这个特定词上。只有完全同义的词可以被合并，例如金矿床和含金矿床，方铅矿和方铅矿石。绝对不可将子概念合并到父级概念上，例如方解石与碳酸盐不可以，因为方解石属于碳酸盐二者不完全同义，印支组与印支组砂岩不可以因为印支组砂岩是印支组的一部分。请注意如果没有任何可合并的词，请回答NO。回答格式必须严格遵守严格遵守python字符串数组的格式，回答前后使用ARRAYSTART和ARRAYEND作为标识。".format(str(entitys),special)
    my_time=2
    reason=""
    while(my_time>0):
        mydict=llm_check_part_array(p1+"请注意你在上一次回答同样问题时出错，出错内容和更正思路如下:"+reason,p2,time=5)
        if mydict=="ERROR":
            my_time=my_time-1
            continue
        r,reason=level2_check(check_part,str(mydict))
        if r:           
           return mydict 
        else:
            my_time=my_time-1
            continue
    print("超过最大次数退出")
    return "ERROR"
