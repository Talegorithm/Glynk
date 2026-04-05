本文主要介绍如何安装SDK实现听悟能力体验。

| **安装SDK** | **说明** |
| --- | --- |
| 阿里云SDK | 使用音视频文件离线转写以及实时记录，均需先安装此[阿里云SDK](#caacc4307d6hu)再使用API接口实现离线和实时任务的管理、状态与结果的查询。 |
| 智能语音交互实时转写SDK | 当您使用实时记录时，创建实时任务后，安装此[实时转写SDK](#328267807emdo)（不含音频采集功能）实现实时音频流的采集和推送，以及实时转写结果的接收。 |

## **安装阿里云SDK**

本产品（听悟/2022-09-30及听悟/2023-09-30）两个版本的OpenAPI接口形式均采用[ROA](https://help.aliyun.com/zh/sdk/product-overview/roa-mechanism)签名风格，签名细节参见[ROA风格请求体&签名机制](https://help.aliyun.com/zh/sdk/product-overview/roa-mechanism)。您可以从这里[听悟OpenAPI SDK](https://api.aliyun.com/api-tools/sdk/tingwu?version=2023-09-30&language=java-tea&tab=primer-doc)下载听悟基于OpenAPI封装后的SDK。当然您也可以从这里[阿里云SDK](https://help.aliyun.com/zh/sdk/product-overview/alibaba-cloud-sdk)下载各种语言的阿里云OpenAPI原生SDK。

需要注意的是，在使用API前，您需要准备好身份账号及访问密钥（AccessKey），才能有效通过客户端工具（SDK、CLI等）访问API。细节请参见[创建AccessKey](https://help.aliyun.com/zh/ram/user-guide/create-an-accesskey-pair)。以下简单介绍主流常见开发语言如何安装使用阿里云SDK的步骤。

### **Java**

**说明**

Java SDK支持Java8及以上环境，可在[maven网站](https://mvnrepository.com/artifact/com.aliyun/aliyun-java-sdk-core)查看版本号，依赖时将上述安装命令中的\`the-latest-version\`替换为最新版本。

通过以下方式将阿里云SDK添加到您的Java工程，也可以[下载完整Java示例代码](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20240625/wdqckz/tingwu-client-java-demo.zip)继续集成。

XML

```
    <dependency>
      <groupId>com.aliyun</groupId>
      <artifactId>aliyun-java-sdk-core</artifactId>
      <version>the-latest-version</version>
    </dependency>
```

Gradle

```
// see https://mvnrepository.com/artifact/com.aliyun/aliyun-java-sdk-core
implementation group: 'com.aliyun', name: 'aliyun-java-sdk-core', version: 'the-latest-version'
```

### **Python**

执行以下命令，使用pip安装aliyun-python-sdk-core。

```
pip install aliyun-python-sdk-core
```

### **Go**

阿里云Go SDK支持Go 1.7及以上版本，您可以通过如下方式安装。

使用glide方式安装：

```
glide get github.com/aliyun/alibaba-cloud-sdk-go
```

使用go vendor方式安装：

```
go get -u github.com/aliyun/alibaba-cloud-sdk-go/sdk
```

### **C++**

您可以通过以下命令安装阿里云C++ SDK，当然您也可以直接参考[阿里云SDK](https://help.aliyun.com/zh/sdk/product-overview/alibaba-cloud-sdk)文档自行安装。

```
git clone https://github.com/aliyun/aliyun-openapi-cpp-sdk.git
cd aliyun-openapi-cpp-sdk
sudo sh easyinstall.sh core
```

编译完成之后，您可以[下载完整C++ 示例代码](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20240625/hkmsdc/tingwu-client-cpp-demo.zip)继续集成。

## **安装智能语音交互实时转写SDK**

当您使用实时记录时，除需要使用从阿里云OpenAPI接口创建实时任务、查询任务状态、结束实时任务外，您还需要实时采集音频流、推送、识别，此时您可以通过以下实时转写（不含音频采集功能）SDK完成。

### **Java**

通过以下方式将智能语音交互实时转写SDK添加到您的Java工程。

```
<dependency>    
      <groupId>com.alibaba.nls</groupId>  
      <artifactId>nls-sdk-transcriber</artifactId>   
      <version>2.2.9</version>
</dependency>
```

### **Go**

通过以下方式将智能语音交互实时转写SDK添加到您的Go工程。

使用glide方式安装：

```
glide get github.com/aliyun/alibaba-cloud-nls-go-sdk
```

使用go vendor方式安装：

```
go get -u github.com/aliyun/alibabacloud-nls-go-sdk
```

### Python

通过下载[nls-1.1.0-py3-none-any.whl](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20240723/ibxkbv/nls-1.1.0-py3-none-any.whl)并进行pip安装，获取智能语音交互实时转写SDK。

```
pip install nls-1.1.0-py3-none-any.whl
```

### C++

我们已将听悟实时转写所依赖的C++ SDK预编译并放置在示例代码的压缩包中，您可以直接使用。当然您也可以直接下载[该SDK的开源代码](https://github.com/aliyun/alibabacloud-nls-cpp-sdk)自行编译。

### Android

1.  [移动端SDK选择与下载](https://help.aliyun.com/zh/isi/sdk-selection-and-download)。
    
2.  解压ZIP包，在`app/libs`目录下获取AAR格式的SDK包，将AAR包集成到您的工程项目中进行依赖。如果需要Android CPP接入方式，可在ZIP包的**android\_libs**和**android\_include**中获得动态库和头文件。
    
3.  使用Android Studio打开此工程查看参考代码实现，其中实时语音识别示例代码为RealtimeMeetingActivity.java文件，替换url后可直接运行。
    

### iOS

1.  [移动端SDK选择与下载](https://help.aliyun.com/zh/isi/sdk-selection-and-download)。
    
2.  解压ZIP包，将ZIP包中的nuisdk.framework添加到您的工程中，并在工程Build Phases的Link Binary With Libraries中添加nuisdk.framework
    
3.  使用Xcode打开此工程，工程中提供了参考代码以及一些直接可使用的工具类，例如音频播放录制和文件操作，您可以直接复制源码到您的实际工程进行使用。其中实时转写示例代码为RealtimeMeetingViewController。替换url后可直接运行。
    

### Harmony

| **类别** | **兼容范围** |
| --- | --- |
| 系统  | 支持HarmonyOS Next 5.0 版本， API LEVEL 12, DevEco Studio版本号5.0.3.403 ~ 5.0.3.700 |
| 架构  | arm64-v8a |

1.  [下载harmony推流SDK和示例代码](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20251027/ykegdr/V1.5.016.napi.002.004_8697fb278a9c6cf5b189f85193ac789828857fc3.tar.gz)。
    
2.  以arkts HAR包的形式进行集成。解压ZIP包，其中nuisdk-release/neonui.har 是SDK生成的HAR包文件，在用户工程项目中导入调用即可。如果需要HarmonyOS Next CPP接入方式，可在ZIP包的harmonyos\_libs和harmonyos\_include中获得动态库和头文件。
    
    1.  har包导入方式：
        
        1.  har包放入工程目录下。以entry模块调用为例，存放路径为 entry/libs/neonui.har。
            
        2.  修改entry模块的oh-package.json5内容，在"dependencies"字段增加neonui.har包的依赖。
            
            ```
            "dependencies": {
              "package": "file:libs/neonui.har"  
            }                                       
            ```
            
        3.  在entry模块目录下，执行命令安装依赖包
            
            ```
             cd entry
             ohpm install
            ```
            
        4.  对工程进行重新编译。
            

3.  使用DevEco Studio打开harmony\_nlsdemo目录下工程查看参考代码实现，其中实时推流示例代码为RealtimeMeeting.ets文件，替换其中的url，即可直接运行。
    

### **Flutter**

1.  [下载Flutter推流SDK和示例代码](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250811/vkeijq/aliyun_tingwu_flutter-20250811-V2.6.5-01B.zip)。
    
2.  解压ZIP包，参考example/lib/main.dart调用示例以及README.md使用说明。

本文介绍音视频文件记录接入流程。

音视频文件转写是针对已经录制完成的录音文件或视频文件，进行离线处理（包含语音识别、翻译、要点提炼、摘要总结、PPT提取及摘要等功能）的服务。

离线转写是非实时业务场景，且提交待处理的文件是提交基于HTTP或HTTPS可访问的文件URL地址，不支持提交本地文件或其他比如FTP协议类的文件地址。

## **使用须知**

-   支持单轨或双轨的mp3、wav、m4a、wma、aac、ogg、amr、flac、aiff格式的音频文件和mp4、wmv、m4v、flv、rmvb、dat、mov、mkv、webm、avi、mpeg、3gp、ogg格式的视频文件。
    
-   文件大小不超过6GB。
    
-   音频时长不超过6小时。
    
-   音频采样率8K/16K/24K/48K。
    
-   需要识别的音视频文件必须支持可通过公网形式的url访问和下载。
    
-   提交的音视频文件URL的访问权限需要设置为公开，URL中只能使用域名不能使用IP地址、不可包含空格，请尽量避免使用中文。
    
    -   推荐使用阿里云OSS：如果OSS中文件访问权限为公开，可参见[使用预签名URL下载或预览文件](https://help.aliyun.com/zh/oss/user-guide/how-to-obtain-the-url-of-a-single-object-or-the-urls-of-multiple-objects#concept-39607-zh/section-st4-efq-v5j)，获取文件访问链接；如果OSS中文件访问权限为私有，可参见[使用预签名URL下载或预览文件](https://help.aliyun.com/zh/oss/user-guide/how-to-obtain-the-url-of-a-single-object-or-the-urls-of-multiple-objects#concept-39607-zh/section-wnz-0he-q20)，通过SDK生成有有效时间的访问链接。
        
    -   您也可以把录音文件存放在自行搭建的文件服务器，提供文件下载。请保证HTTP的响应头（Header）中Content-Length的长度值和Body中数据的真实长度一致，否则会导致下载失败。
        
    -   因离线任务存在排队情况，为保障3小时内完成，因此您若设置了带有效期限制的访问url，请设置有效期不低于3小时，以避免过期而无法下载音视频文件进行处理。
        
-   支持的调用方式：轮询方式和回调方式，您可以任选其一即可。
    
-   支持设置多种语言识别：中文、英文、粤语、中英自由说（长段中英混）、日语、韩语，详见 [音视频文件服务参数表](https://help.aliyun.com/zh/tingwu/features#056035e03dopk)。
    
-   对于API维度的QPS（Queries Per Second）限制如下：
    
    -   [创建听悟任务](https://help.aliyun.com/zh/tingwu/api-tingwu-2023-09-30-createtask)用户级别QPS限制为20。
        
    -   [查询任务状态和任务结果](https://help.aliyun.com/zh/tingwu/api-tingwu-2023-09-30-gettaskinfo)用户级别QPS限制为100。
        

**重要**

-   提交音视频文件离线转写任务后，任务在3小时内完成并返回识别文本和大模型结果(如有)。但一次性上传大规模数据（半小时内上传超过500小时时长的录音）的除外。
    
-   如有大规模离线文件处理需求的用户，请联系售前专家另行沟通。
    
-   对于音视频文件存储在阿里云OSS北京region的用户，强烈建议其生成内网签名的url再提交任务，可节省公网费用，也能加速任务处理速度。可参见[ECS实例通过OSS内网地址访问OSS资源](https://help.aliyun.com/zh/oss/access-to-oss-resources-from-ecs-instances-by-using-an-internal-endpoint-of-oss)
    

**警告**

超过QPS之后则可能报错：`Throttling.User : Request was denied due to user flow control.`。建议查询接口的轮询间隔适当延长，不宜过短。

## **交互流程**

用户客户端与服务端的交互流程如图所示：

![image](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/9952485171/p799995.png)

## **接入步骤**

-   [提交音视频文件转写任务](#7e2f92c07989a)
    

用户客户端提交录音文件识别请求。

正常情况下，服务端返回该请求任务的TaskId，用于后续查询识别结果。

如果调用出错，响应报文中会给出相关错误信息，以及RequestId，可据此排查调用参数。

-   [任务处理结果查询（可选）](#8e5c267078vhq)
    

基于上一步提交任务后返回的TaskId来查询处理结果。

如通过此方式轮询查询结果，注意轮询频率不要过高，以便被限流。比如您可以**按每1分钟或每5分钟**的频率持续查询。

-   [任务完成后的回调通知（可选）](#8ac4862087xym)
    

使用回调通知的方式来获取结果，不同于主动轮询，您可以在提交任务后，等待服务端处理完成时主动地通知您任务状态。

当前我们支持通过HTTP的回调方式将任务处理状态通知到您。

-   [任务完成后添加新的AI参数再次运行、刷新任务结果（可选）](#a0da476079z2o)
    

您可以在任务完成后，补充新的参数，触发新的算法处理，刷新任务结果。

### **前提条件**

-   [创建AccessKey](https://help.aliyun.com/zh/tingwu/getting-started-1#48b2f4707ehf9)
    
-   [创建项目](https://help.aliyun.com/zh/tingwu/getting-started-1#b602cfa07egrl)
    
-   [安装SDK](https://help.aliyun.com/zh/tingwu/install-the-sdk)
    

### **AccessKey环境变量设置**

需要使用您的AccessKey的Id和secret替换如下命令中的YOUR\_ACCESS\_KEY\_ID和YOUR\_ACCESS\_KEY\_SECRET。

```
export ALIBABA_CLOUD_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID &&
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=YOUR_ACCESS_KEY_SECRET
```

### 提交音视频离线转写任务

参考[API详情](https://help.aliyun.com/zh/tingwu/api-tingwu-2023-09-30-createtask)创建一个音视频离线转写任务，常用参数如下。

#### **请求参数**

| **名称** | **参数** | **类型** | **默认值** | **说明** |
| --- | --- | --- | --- | --- |
| AppKey | AppKey | string | \\- | **必选**，请设置为您在管控台上创建的AppKey。 |
| 基本请求信息 （Input） | Input.FileUrl | string | \\- | **必选**，音视频文件下载地址，支持http或https形式的地址。 |
| Input.SourceLanguage | string | \\- | **必选**，[根据音视频中的语种类别来配置对应的参数。](#add3f77073a0h) - 若已知语音中的语种，如实选择中文（cn）， 英语（en）， 粤语（yue）， 日语（ja）、韩语（ko），推荐使用此方式。 - 若未知语音中涉及的语种，可传入自动语种识别（auto），语种算法检测后，系统自动切换模型进行语音识别，此功能仅在离线转写任务下可用。 - 若语音中的语种非单语种，涉及多个语种，可传入（multilingual），识别出对应语种的文字。结合Input.LanguageHints一起使用。 |
| Input.LanguageHints | list\\[string\\] | null | [指定多语言模型时需语音识别出文字的语种列表](#c49c0bf020mpj)。 当语音中涉及多个语种的语音均需识别出文字时，此参数用于限制语种类别，且仅当Input.SourceLanguage='multilingual'时配置生效。 |
| Input.TaskKey | string | null | 用户自行设置的自定义标识。 |
| Input.ProgressiveCallbacksEnabled | boolean | false | 是否开启回调功能。 当需要开启回调功能时，您需要在[控制台](https://nls-portal.console.aliyun.com/tingwu/projects)配置好回调类型和地址，并在创建任务时将该参数置为true。 |
| 转码（Transcoding) | Parameters.Transcoding.TargetAudioFormat | string | null | 当前只支持设置mp3转换。 |
| Parameters.Transcoding.TargetVideoFormat | string | null | 当前只支持设置mp4转换；仅在原文件为视频格式设置才有意义。 |
| 语音识别 （Transcription） | Parameters.Transcription.DiarizationEnabled | boolean | false | 是否在语音识别过程中开启说话人分离功能。 |
| Parameters.Transcription.Diarization.SpeakerCount | int | \\- | 开启说话人分离功能时，设置的说话人数，支持最多不超过100人。 - 不设置：不使用说话人角色区分 - 0：说话人角色区分结果为不定人数 当有此参数时，使用此参数辅助指定的人数，最终分轨人数以真实分类人数为准。 |
| Parameters.Transcription.PhraseId | String | \\- | 热词词表ID。 |
| 翻译 (Translation) | Parameters.TranslationEnabled | boolean | false | 是否开启翻译功能。 |
| Parameters.Translation.TargetLanguages | list\\[string\\] | \\- | 如果开启翻译，需要设置目标翻译语言。 支持设置中文（cn）、 英语（en）、日语（ja）、韩语（ko）、德语（de）、法语（fr）、俄语（ru）。 |
| 章节速览 | Parameters.AutoChaptersEnabled | boolean | false | 章节速览功能，包括：议程标题和议程摘要。 |
| 要点提炼 (MeetingAssistance) | Parameters.MeetingAssistanceEnabled | boolean | false | 要点提炼功能，包括：关键词、重点内容、待办、场景识别。 |
| Parameters.MeetingAssistance.Types | list\\[string\\] | \\- | 如果开启要点提炼功能，您可以设置1个或者多个对应的类型： - Actions ： 待办事项 - KeyInformation ： 关键信息（含关键词和重点内容） 注意：若您只打开了功能开关，但没有添加任何算法类型，则该功能模型处理所有算法模型。 |
| 摘要总结 (Summarization) | Parameters.SummarizationEnabled | boolean | false | 是否开启摘要总结功能。 |
| Parameters.Summarization.Types | list\\[string\\] | \\- | 如果开启摘要总结功能，需要设置摘要类型。支持设置1个或多个。 - Paragraph（全文摘要） - Conversational（发言总结） - QuestionsAnswering（问答回顾） - MindMap（思维导图） |
| PPT提取及摘要 | Parameters.PptExtractionEnabled | boolean | false | 是否开启PPT功能，包含PPT抽取、PPT摘要。 注：仅支持PPT在主要界面（投屏或周边有人物视频），不支持人物在PPT前走动或演讲。 可通过通义听悟网站测试效果。[点此测试](https://tingwu.aliyun.com/home) |
| 口语书面化 | Parameters.TextPolishEnabled | boolean | false | 是否开启口语书面化功能。 |
| 服务质检 | Parameters.ServiceInspectionEnabled | boolean | false | 是否开启服务质检功能。 |
| Parameters.ServiceInspection | object | \\- | 参考[服务质检参数对象](https://help.aliyun.com/zh/tingwu/service-inspection#823d1c4278rt5)对服务过程中的对话进行质量检测，支持自定义多个质检维度，辅助客户提升服务水平。 |
| 自定义Prompt | Parameters.CustomPromptEnabled | boolean | false | 是否开启自定义prompt功能。 |
| Parameters.CustomPrompt | object | \\- | 参考[自定义prompt参数对象](https://help.aliyun.com/zh/tingwu/custom-prompt#94461d6b78d8h)由客户自主定义大模型提示词，引导大模型完成客户定义的各类任务。 |
| 大模型后处理任务全局参数 | Parameters.Model | String | \\- | 大模型后处理任务支持的模型，可选：`default`、`qwen-plus`和`qwq`。**注意：该参数不覆盖自定义Prompt中的可选模型参数。** |
| Parameters.LlmOutputLanguage | String | \\- | 大模型任务支持指定输出的语种，可选： - `cn`：中文 - `en`：英文 **注意：该参数目前仅对思维导图和章节速览生效。** |

#### **示例代码**

Python

```
#!/usr/bin/env python
#coding=utf-8

import os
import json
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

def init_parameters():
    body = dict()
    body['AppKey'] = '输入您在听悟管控台创建的Appkey'

    # 基本请求参数
    input = dict()
    input['SourceLanguage'] = 'cn'
    input['TaskKey'] = 'task' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    input['FileUrl'] = '输入待测试的音频url链接'
    body['Input'] = input

    # AI相关参数，按需设置即可
    parameters = dict()

    # 音视频转换相关
    transcoding = dict()
    # 将原音视频文件转成mp3文件，用以后续浏览器播放
    # transcoding['TargetAudioFormat'] = 'mp3'
    # transcoding['SpectrumEnabled'] = False
    # parameters['Transcoding'] = transcoding

    # 语音识别控制相关
    transcription = dict()
    # 角色分离 ： 可选
    transcription['DiarizationEnabled'] = True
    diarization = dict()
    diarization['SpeakerCount'] = 2
    transcription['Diarization'] = diarization
    parameters['Transcription'] = transcription

    # 文本翻译控制相关 ： 可选
    parameters['TranslationEnabled'] = True
    translation = dict()
    translation['TargetLanguages'] = ['en'] # 假设翻译成英文
    parameters['Translation'] = translation

    # 章节速览相关 ： 可选，包括： 标题、议程摘要
    parameters['AutoChaptersEnabled'] = True

    # 智能纪要相关 ： 可选，包括： 待办、关键信息(关键词、重点内容、场景识别)
    parameters['MeetingAssistanceEnabled'] = True
    meetingAssistance = dict()
    meetingAssistance['Types'] = ['Actions', 'KeyInformation']
    parameters['MeetingAssistance'] = meetingAssistance

    # 摘要控制相关 ： 可选，包括： 全文摘要、发言人总结摘要、问答摘要(问答回顾)
    parameters['SummarizationEnabled'] = True
    summarization = dict()
    summarization['Types'] = ['Paragraph', 'Conversational', 'QuestionsAnswering', 'MindMap']
    parameters['Summarization'] = summarization

    # ppt抽取和ppt总结 ： 可选
    parameters['PptExtractionEnabled'] = True
    
    # 口语书面化 ： 可选
    parameters['TextPolishEnabled'] = True
    
    # 大模型后处理任务全局参数 ： 可选
    parameters['Model'] = 'qwq'
    parameters['LlmOutputLanguage'] = 'en'

    body['Parameters'] = parameters
    return body

body = init_parameters()
print(body)

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
request.add_query_param('type', 'offline')

request.set_content(json.dumps(body).encode('utf-8'))
response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))
```

Java

```
package com.alibaba.tingwu.client.demo.offlinetask;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.aliyuncs.CommonRequest;
import com.aliyuncs.CommonResponse;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.exceptions.ClientException;
import com.aliyuncs.http.FormatType;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.http.ProtocolType;
import com.aliyuncs.profile.DefaultProfile;
import org.junit.Test;

/**
 * @author tingwu2023
 * @desc 演示了通过OpenAPI 创建音视频文件的离线转写任务 的调用方式。
 */
public class SubmitFiletransTaskTest {

    @Test
    public void summitTask() throws ClientException {
        CommonRequest request = createCommonRequest("tingwu.cn-beijing.aliyuncs.com", "2023-09-30", ProtocolType.HTTPS, MethodType.PUT, "/openapi/tingwu/v2/tasks");
        request.putQueryParameter("type", "offline");

        JSONObject root = new JSONObject();
        root.put("AppKey", "输入您在听悟管控台创建的Appkey");

        String path = "输入待测试的音频url链接";
        JSONObject input = new JSONObject();
        input.fluentPut("FileUrl", path)
                .fluentPut("SourceLanguage", "cn")
                .fluentPut("TaskKey", "task" + System.currentTimeMillis());
        root.put("Input", input);

        JSONObject parameters = initRequestParameters();
        root.put("Parameters", parameters);

        System.out.println(root.toJSONString());
        request.setHttpContent(root.toJSONString().getBytes(), "utf-8", FormatType.JSON);

        // TODO 请通过环境变量设置您的AccessKeyId、AccessKeySecret
        DefaultProfile profile = DefaultProfile.getProfile("cn-beijing", System.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), System.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"));
        IAcsClient client = new DefaultAcsClient(profile);
        CommonResponse response = client.getCommonResponse(request);
        System.out.println(response.getData());
        JSONObject body = JSONObject.parseObject(response.getData());
        JSONObject data = (JSONObject) body.get("Data");
        System.out.println("TaskId = " + data.getString("TaskId"));
    }

    public static JSONObject initRequestParameters() {
        JSONObject parameters = new JSONObject();

        // 音视频转换： 可选
        JSONObject transcoding = new JSONObject();
        transcoding.put("TargetAudioFormat", "mp3");
        transcoding.put("SpectrumEnabled", false);
        parameters.put("Transcoding", transcoding);

        // 语音识别
        JSONObject transcription = new JSONObject();
        transcription.put("DiarizationEnabled", true);
        JSONObject speaker_count = new JSONObject();
        speaker_count.put("SpeakerCount", 2);
        transcription.put("Diarization", speaker_count);
        parameters.put("Transcription", transcription);

        // 翻译： 可选
        JSONObject translation = new JSONObject();
        JSONArray langArry = new JSONArray();
        langArry.add("en");
        translation.put("TargetLanguages", langArry);
        parameters.put("Translation", translation);
        parameters.put("TranslationEnabled", true);

        // 章节速览： 可选
        parameters.put("AutoChaptersEnabled", true);

        // 智能纪要： 可选
        parameters.put("MeetingAssistanceEnabled", true);
        JSONObject meetingAssistance = new JSONObject();
        JSONArray mTypes = new JSONArray().fluentAdd("Actions").fluentAdd("KeyInformation");
        meetingAssistance.put("Types", mTypes);
        parameters.put("MeetingAssistance", meetingAssistance);
      
        // 摘要相关： 可选
        parameters.put("SummarizationEnabled", true);
        JSONObject summarization = new JSONObject();
        JSONArray sTypes = new JSONArray().fluentAdd("Paragraph").fluentAdd("Conversational").fluentAdd("QuestionsAnswering").fluentAdd("MindMap");
        summarization.put("Types", sTypes);
        parameters.put("Summarization", summarization);

        // PPT抽取： 可选
        parameters.put("PptExtractionEnabled", true);
      
      	// 口语书面化： 可选
        parameters.put("TextPolishEnabled", true);
        
        // 大模型后处理任务全局参数 ： 可选
        parameters.put("Model", "qwq"); 
        parameters.put("LlmOutputLanguage", "en");

        return parameters;
    }
  
    public static CommonRequest createCommonRequest(String domain, String version, ProtocolType protocolType, MethodType method, String uri) {
        // 创建API请求并设置参数
        CommonRequest request = new CommonRequest();
        request.setSysDomain(domain);
        request.setSysVersion(version);
        request.setSysProtocol(protocolType);
        request.setSysMethod(method);
        request.setSysUriPattern(uri);
        request.setHttpContentType(FormatType.JSON);
        return request;
    }
}
```

Go

```
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/aliyun/alibaba-cloud-sdk-go/sdk"
	"github.com/aliyun/alibaba-cloud-sdk-go/sdk/requests"
)

type TranscodeingParam struct {
	TargetAudioFormat     string `json:"TargetAudioFormat,omitempty"`
	TargetVideoFormat     string `json:"TargetVideoFormat,omitempty"`
	VideoThumbnailEnabled bool   `json:"VideoThumbnailEnabled,omitempty"`
	SpectrumEnabled       bool   `json:"SpectrumEnabled,omitempty"`
}

type DiarizationParam struct {
	SpeakerCount *int `json:"SpeakerCount,omitempty"`
}

type TranscriptionParam struct {
	AudioEventDetectionEnabled bool              `json:"AudioEventDetectionEnabled,omitempty"`
	DiarizationEnabled         bool              `json:"DiarizationEnabled,omitempty"`
	Diarization                *DiarizationParam `json:"Diarization,omitempty"`
}

type TranslationParam struct {
	TargetLanguages []string `json:"TargetLanguages,omitempty"`
}

type SummarizationParam struct {
	Types []string `json:"Types,omitempty"`
}

type ExtraParamerters struct {
	Transcoding              *TranscodeingParam  `json:"Transcoding,omitempty"`
	Transcription            *TranscriptionParam `json:"Transcription,omitempty"`
	TranslationEnabled       bool                `json:"TranslationEnabled,omitempty"`
	Translation              *TranslationParam   `json:"Translation,omitempty"`
	AutoChaptersEnabled      bool                `json:"AutoChaptersEnabled,omitempty"`
	MeetingAssistanceEnabled bool                `json:"MeetingAssistanceEnabled,omitempty"`
	SummarizationEnabled     bool                `json:"SummarizationEnabled,omitempty"`
	Summarization            *SummarizationParam `json:"Summarization,omitempty"`
	TextPolishEnabled        bool                `json:"TextPolishEnabled,omitempty"`
	Model                    string              `json:"Model,omitempty"`           
        LlmOutputLanguage        string              `json:"LlmOutputLanguage,omitempty"` 
}

type InputParam struct {
	SourceLanguage string `json:"SourceLanguage"`
	FileUrl        string `json:"FileUrl,omitempty"`
	TaskKey        string `json:"TaskKey,omitempty"`
	Format         string `json:"Format,omitempty"`
	SampleRate     int    `json:"SampleRate,omitempty"`
}

type TaskBodyParam struct {
	Appkey      string            `json:"AppKey"`
	Input       InputParam        `json:"Input"`
	Paramerters *ExtraParamerters `json:"Parameters,omitempty"`
}

type GetTaskInfoResponse struct {
	RequestId string `json:"RequestId"`
	Code      string `json:"Code"`
	Message   string `json:"Message"`
	Data      struct {
		TaskId     string `json:"TaskId"`
		TaskKey    string `json:"TaskKey"`
		TaskStatus string `json:"TaskStatus"`
	} `json:"Data"`
}

func init_request_param_offline() *ExtraParamerters {
	param := new(ExtraParamerters)
	param.Transcoding = new(TranscodeingParam)
	transcription := new(TranscriptionParam)
	transcription.Diarization = new(DiarizationParam)
	transcription.Diarization.SpeakerCount = new(int)
        *transcription.Diarization.SpeakerCount = 0
	transcription.DiarizationEnabled = true
	param.Transcription = transcription

	param.TranslationEnabled = false
	param.AutoChaptersEnabled = false
	param.MeetingAssistanceEnabled = false
	param.SummarizationEnabled = true

	summarization := new(SummarizationParam)
	summarization.Types = []string{
		"Paragraph",
		"Conversational",
		"QuestionsAnswering",
                "MindMap",
	}
	param.Summarization = summarization
	param.TextPolishEnabled = false
	
	param.Model = "qwq"              
        param.LlmOutputLanguage = "en"

	return param
}

func test_submit_offline_task() {
	akkey := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
	aksecret := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
	client, err := sdk.NewClientWithAccessKey("cn-beijing", akkey, aksecret)
	if err != nil {
		log.Default().Fatalln(err)
		return
	}

	request := requests.NewCommonRequest()
	request.Method = "PUT"
	request.Domain = "tingwu.cn-beijing.aliyuncs.com"
	request.Version = "2023-09-30"
	request.SetContentType("application/json")
	request.PathPattern = "/openapi/tingwu/v2/tasks"
	request.QueryParams["type"] = "offline"

	param := new(TaskBodyParam)
	param.Appkey = "输入您在听悟管控台创建的Appkey"
	param.Input.SourceLanguage = "cn"
	param.Input.FileUrl = "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/asr_example.wav"
	param.Input.TaskKey = "task_" + fmt.Sprint(time.Now().Unix())

	param.Paramerters = init_request_param_offline()
        b, _ := json.Marshal(param)
	log.Default().Print("request body:\n", string(b))
	request.SetContent(b)
	request.SetScheme("https")

	response, err := client.ProcessCommonRequest(request)
	if err != nil {
		log.Default().Fatalln(err)
		return
	}

	log.Default().Print("response body:\n", string(response.GetHttpContentBytes()))
}

func main() {
	test_submit_offline_task()
}
```

C++

```
#include <cstdlib>
#include <string>
#include <alibabacloud/core/AlibabaCloud.h>
#include <alibabacloud/core/CommonRequest.h>
#include <alibabacloud/core/CommonClient.h>
#include <alibabacloud/core/CommonResponse.h>
#include "jsoncpp/json.h"
/**
 * @author tingwu2023
 * @desc 演示了通过OpenAPI 创建音视频文件的离线转写任务 的调用方式。
 */
int main( int argc, char** argv ) {
    AlibabaCloud::InitializeSdk();
    AlibabaCloud::ClientConfiguration configuration( "cn-beijing" );
    // specify timeout when create client.
    configuration.setConnectTimeout(1500);
    configuration.setReadTimeout(4000);
    // Please ensure that the environment variables ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET are set.
    AlibabaCloud::Credentials credential( getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET") );
    AlibabaCloud::CommonClient client( credential, configuration );

    AlibabaCloud::CommonRequest request(AlibabaCloud::CommonRequest::RequestPattern::RoaPattern);
    request.setHttpMethod(AlibabaCloud::HttpRequest::Method::Put);
    request.setDomain("tingwu.cn-beijing.aliyuncs.com");
    request.setVersion("2023-09-30");
    request.setResourcePath("/openapi/tingwu/v2/tasks");
    request.setHeaderParameter("Content-Type", "application/json");
    request.setQueryParameter("type", "offline");

    Json::Value root;
    root["Appkey"] = "输入您在听悟管控台创建的Appkey";

    Json::Value input;
    input["FileUrl"] = "输入待测试的音频url链接";
    input["SourceLanguage"] = "cn";
    input["TaskKey"] = "输入您为该次请求自定义的标识";
    root["Input"] = input;

    Json::Value parameters;
    // 音视频文件转换 通常来说，不需要设置此参数
    // Json::Value transcoding;
    // transcoding["TargetAudioFormat"] = "mp3";
    // parameters["Transcoding"] = transcoding;

    // 语音转写: 以下是开启说话人分离功能(角色分离)，若您不需要，则无须设置
    Json::Value transcription;
    transcription["DiarizationEnabled"] = true;
    Json::Value speakerCount;
    speakerCount["SpeakerCount"] = 2;
    transcription["Diarization"] = speakerCount;
    parameters["Transcription"] = transcription;

    // 翻译： 可选
    Json::Value translation;
    Json::Value langauges;
    langauges.append("en");
    translation["TargetLanguages"] = langauges;
    parameters["Translation"] = translation;
    parameters["TranslationEnabled"] = true;

    // 章节速览： 可选
    parameters["AutoChaptersEnabled"] = true;

    // 智能纪要： 可选，包括： 待办、关键信息(关键词、重点内容、场景识别)
    parameters["MeetingAssistanceEnabled"] = true;
    Json::Value meetingAssistance;
    Json::Value meetingAssistanceTypeList;
    meetingAssistanceTypeList.append("Actions");
    meetingAssistanceTypeList.append("KeyInformation");
    meetingAssistance["Types"] = meetingAssistanceTypeList;
    parameters["MeetingAssistanceTypeList"] = meetingAssistanceTypeList;

    // 摘要相关： 可选， 以下设置将3种摘要类型都启用了，您可以按需增删
    parameters["SummarizationEnabled"] = true;
    Json::Value summarization;
    Json::Value summarizationTypeList;
    summarizationTypeList.append("Paragraph");
    summarizationTypeList.append("Conversational");
    summarizationTypeList.append("QuestionsAnswering");
    summarizationTypeList.append("MindMap");
    summarization["Types"] = summarizationTypeList;
    parameters["Summarization"] = summarization;

    // PPT抽取： 可选， 建议仅当是视频文件时且视频中有ppt相关视频画面时开启
    //parameters["PptExtractionEnabled"] = true;
  	
    // 口语书面化： 可选
    parameters["TextPolishEnabled"] = true;
    
    # 大模型后处理任务全局参数 ： 可选
    parameters["Model"] = "qwq";
    parameters["LlmOutputLanguage"] = "en";

    root["Parameters"] = parameters;

    Json::FastWriter writer;
    std::string body = writer.write(root);
    printf("input json: [%s]\n", body.c_str());
    request.setContent(body.c_str(), body.size());
      
    auto response = client.commonResponse(request);
    if (response.isSuccess()) {
        printf("request success.\n");
        printf("result: %s\n", response.result().payload().c_str());
    } else {
        printf("error: %s\n", response.error().errorMessage().c_str());
        printf("request id: %s\n", response.error().requestId().c_str());
    }
      
    AlibabaCloud::ShutdownSdk();
    return 0;
} 
```

#### **示例输出**

当任务仍在运行中时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3vc4b45d898fcadb*********",
        "TaskKey":"task16988********",
        "TaskStatus":"ONGOING"
    },
    "Message":"success",
    "RequestId":"2001dc2a-9b46-4a2f-9822-b140********"
}
```

#### **协议解析**

具体字段定义如下。

| **参数名** | **类型** | **说明** |
| --- | --- | --- |
| TaskId | string | 创建任务时生成的TaskId，用于查询任务状态、结果以及排查问题时使用。 |
| TaskStatus | string | 任务状态 |
| TaskKey | string | 您创建任务时设置的TaskKey |
| RequestId | string | RequestId用于排查问题使用。 |

在您提交音视频离线转写任务之后，任务即处于运行状态。

### **查询任务状态和结果**

-   查询任务时，您需要将“提交任务”时返回的TaskId作为输入，发起查询请求，根据返回的状态判断任务是否已完成。
    

#### **请求参数**

| **参数名** | **类型** | **是否必填** | **说明** |
| --- | --- | --- | --- |
| TaskId | string | 是   | 您提交任务时返回的TaskId信息 |

#### **示例代码**

Python

```
#!/usr/bin/env python
#coding=utf-8

import os
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

uri = '/openapi/tingwu/v2/tasks' + '/' + '请输入您提交任务时返回的TaskId'
request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'GET', uri)

response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))
```

Java

```
package com.alibaba.tingwu.client.demo.common;

import com.aliyuncs.CommonRequest;
import com.aliyuncs.CommonResponse;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.exceptions.ClientException;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.http.ProtocolType;
import com.aliyuncs.profile.DefaultProfile;
import org.junit.Test;

/**
 * @author tingwu2023
 * @desc 演示了通过OpenAPI 根据TaskId查询任务状态和结果 的调用方式。
 */
public class GetTaskInfoTest {
    @Test
    public void getTaskInfo() throws ClientException {
        String taskId = "请输入创建任务(含离线转写、实时会议)的TaskId";
        String queryUrl = String.format("/openapi/tingwu/v2/tasks" + "/%s", taskId);

        CommonRequest request = createCommonRequest("tingwu.cn-beijing.aliyuncs.com", "2023-09-30", ProtocolType.HTTPS, MethodType.GET, queryUrl);
        // TODO 请通过环境变量设置您的AccessKeyId、AccessKeySecret
        DefaultProfile profile = DefaultProfile.getProfile("cn-beijing", System.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), System.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"));
        IAcsClient client = new DefaultAcsClient(profile);
        CommonResponse response = client.getCommonResponse(request);
        System.out.println(response.getData());
    }
  
    public static CommonRequest createCommonRequest(String domain, String version, ProtocolType protocolType, MethodType method, String uri) {
        // 创建API请求并设置参数
        CommonRequest request = new CommonRequest();
        request.setSysDomain(domain);
        request.setSysVersion(version);
        request.setSysProtocol(protocolType);
        request.setSysMethod(method);
        request.setSysUriPattern(uri);
        request.setHttpContentType(FormatType.JSON);
        return request;
    }
}
```

Go

```
package main

import (
	"encoding/json"
	"log"
	"os"

	"github.com/aliyun/alibaba-cloud-sdk-go/sdk"
	"github.com/aliyun/alibaba-cloud-sdk-go/sdk/requests"
)

type GetTaskInfoResponse struct {
	RequestId string `json:"RequestId"`
	Code      string `json:"Code"`
	Message   string `json:"Message"`
	Data      struct {
		TaskId     string `json:"TaskId"`
		TaskKey    string `json:"TaskKey"`
		TaskStatus string `json:"TaskStatus"`
	} `json:"Data"`
}

func get_task_info(taskid string, akkey string, aksecret string) (*GetTaskInfoResponse, string, error) {
	client, err := sdk.NewClientWithAccessKey("cn-beijing", akkey, aksecret)
	if err != nil {
		return nil, "", err
	}

	request := requests.NewCommonRequest()
	request.Method = "GET"
	request.Domain = "tingwu.cn-beijing.aliyuncs.com"
	request.Version = "2023-09-30"
	request.PathPattern = "/openapi/tingwu/v2/tasks/" + taskid
	request.SetScheme("https")

	log.Default().Print("request task:", taskid)
	response, err := client.ProcessCommonRequest(request)
	if err != nil {
		return nil, "", err
	}

	log.Default().Print("response body:\n", string(response.GetHttpContentBytes()))
	resp := new(GetTaskInfoResponse)
	err = json.Unmarshal(response.GetHttpContentBytes(), resp)
	if err != nil {
		return nil, response.GetHttpContentString(), err
	}
	return resp, response.GetHttpContentString(), nil
}

func main() {
	akkey := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
	aksecret := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
	_, raw, _ := get_task_info("请输入创建任务(含离线转写、实时会议)的TaskId", akkey, aksecret)
	log.Default().Println("response :", raw)
}
```

C++

```
#include <cstdlib>
#include <iostream>
#include <string>
#include <alibabacloud/core/AlibabaCloud.h>
#include <alibabacloud/core/CommonRequest.h>
#include <alibabacloud/core/CommonClient.h>
#include <alibabacloud/core/CommonResponse.h>
/**
 * @author tingwu2023
 * @desc 演示了通过OpenAPI 根据TaskId查询任务状态和结果 的调用方式。
 */
int main( int argc, char** argv ) {
    std::string taskId = "请输入创建任务(含离线转写、实时会议)的TaskId";

    AlibabaCloud::InitializeSdk();
    AlibabaCloud::ClientConfiguration configuration( "cn-beijing" );
    // specify timeout when create client.
    configuration.setConnectTimeout(1500);
    configuration.setReadTimeout(4000);
    // Please ensure that the environment variables ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET are set.
    AlibabaCloud::Credentials credential( getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET") );
    AlibabaCloud::CommonClient client( credential, configuration );
    AlibabaCloud::CommonRequest request(AlibabaCloud::CommonRequest::RequestPattern::RoaPattern);
    request.setHttpMethod(AlibabaCloud::HttpRequest::Method::Get);
    request.setDomain("tingwu.cn-beijing.aliyuncs.com");
    request.setVersion("2023-09-30");
    request.setHeaderParameter("Content-Type", "application/json");
    request.setResourcePath("/openapi/tingwu/v2/tasks/" + taskId);

    auto response = client.commonResponse(request);
    if (response.isSuccess()) {
        printf("request success.\n");
        printf("result: %s\n", response.result().payload().c_str());
    } else {
        printf("error: %s\n", response.error().errorMessage().c_str());
        printf("request id: %s\n", response.error().requestId().c_str());
    }
      
    AlibabaCloud::ShutdownSdk();
    return 0;
} 
```

#### **示例输出**

当任务仍在运行中时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"ONGOING"
    },
    "Message":"success",
    "RequestId":"5fa32fc6-441f-4dd1-bb86-c030********"
}
```

当任务在运行中但有部分结果时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"ONGOING",
        "OutputMp3Path":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_20231101141801.mp3?ExLTAI****************AccessKeyId=LTAI****************&amp;Signature=********JBMijH7wLq0xX6aivHc%3D",
        "Result":{
            "Transcription":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_Transcription_20231101141926.json?Expires=1698906034&amp;OSSAcceLTAI****************&amp;Signature=********NJlqSEWJxfkMwjwsHCA%3D"
        }
    },
    "Message":"success",
    "RequestId":"1b20e0d9-c55c-4cc3-85af-80b4********"
}
```

当任务已完成时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"COMPLETED",
        "OutputMp3Path":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_20231101141801.mp3?ExLTAI****************AccessKeyId=LTAI****************&amp;Signature=********JBMijH7wLq0xX6aivHc%3D",
        "Result":{
            "AutoChapters":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_AutoChapters_20231101141955.json?Expires=1698906034&amp;OSSAcceLTAI****************&amp;Signature=********Ax9FvifYAO8dj4qzWg%3D",
            "Transcription":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_Transcription_20231101141926.json?Expires=1698906034&amp;OSSAccessKeyId=LTAI****************&amp;Signature=********NJlqSEWJxfkMwjwsHCA%3D"
        }
    },
    "Message":"success",
    "RequestId":"1b20e0d9-c55c-4cc3-85af-80b4********"
}
```

当任务失败时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"b76389677b1441fa82165cb1********",
        "TaskStatus":"FAILED",
        "ErrorCode":"TSC.AudioFileLink",
        "ErrorMessage":"Audio file link invalid."
    },
    "Message":"success",
    "RequestId":"d181d898-b627-4040-b7c9-9563********"
}
```

### **回调通知任务状态和结果**

如果您希望通过回调方式来获取任务状态和结果，需要在[控制台](https://nls-portal.console.aliyun.com/tingwu/projects)配置好回调类型和地址，创建离线转写任务时将参数AppKey配置为对应的项目AppKey，同时将参数Input.ProgressiveCallbacksEnabled设为true。

**重要**

当您选择http回调方式时，我们将设置一个最大请求时间限制。这意味着，如果我们在发起请求后的超过**5秒钟**内没有收到您的回复，我们将不再等待返回结果，系统判断回调请求发送失败，稍后将会进行重试。

我们建议您审核和调整您的系统，以确保能够在5秒钟内响应我们的回调请求。这可能包括但不限于：

-   优化您的处理逻辑，确保高效执行；
    
-   对不必要的长操作进行异步处理，不在主回调响应路径中等待；
    
-   实施错误处理和重试机制，以应对超时或失败的情况。
    

**说明**

**回调重试机制说明**：

当回调消息发送失败时，听悟服务端会在**5秒钟**后重新发送一次回调消息，如果第二次发送仍然失败，则会在之后的每**5分钟**再发送一次，重试次数最多为**3次**。

#### **示例输出**

当单个AI模型子任务完成时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"ONGOING",
        "TaskKey":"TingwuDemo",
        "Result":{
            "Transcription":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_Transcription_20231101141926.json?Expires=1698906034&amp;OSSAcceLTAI****************&amp;Signature=********NJlqSEWJxfkMwjwsHCA%3D"
        }
    },
    "Message":"success",
    "RequestId":"5cf2b587ac6e41e6a1f06ca1********"
}
```

当任务完成时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"COMPLETED",
        "TaskKey":"TingwuDemo",
        "Result":{
            "AutoChapters":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_AutoChapters_20231101141955.json?Expires=1698906034&amp;OSSAcceLTAI****************&amp;Signature=********Ax9FvifYAO8dj4qzWg%3D",
            "Transcription":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/e8adc0b3bc4b42d898fcadb0a1710635/e8adc0b3bc4b42d898fcadb0a1710635_Transcription_20231101141926.json?Expires=1698906034&amp;OSSAccessKeyId=LTAI****************&amp;Signature=********NJlqSEWJxfkMwjwsHCA%3D"
        }
    },
    "Message":"success",
    "RequestId":"9c60b07f152445349eaa6161********"
}
```

当任务失败时：

```
{
    "Code":"0",
    "Data":{
        "TaskId":"e8adc0b3bc4b42d898fcadb0********",
        "TaskStatus":"FAILED",
        "TaskKey":"TingwuDemo",
        "ErrorCode":"TSC.AudioFileLink",
        "ErrorMessage":"Audio file link invalid."
    },
    "Message":"success",
    "RequestId":"5e1c0babe36844e49f1b7bee********"
}
```

### 重跑任务刷新结果

若您需要对已完成任务进行刷新，比如重新生成某个算法结果，或者增量增加某个算法结果，则可以通过“提交任务”时返回的TaskId以及新的控制参数作为输入，再次发起任务处理请求，等待结果完成。

比如您在首次创建任务时未启动章节速览功能，此时您可直接增加新的参数后继续该任务，而无须再提交音视频文件从头开始运行。

**重要**

发起重跑任务的前提条件是该任务已经完成（COMPLETED），也即是对已完成的任务执行重跑，而不能对运行中或是失败的任务执行重跑。

#### **请求参数**

| **功能名称** | **参数** | **类型** | **默认值** | **说明** |
| --- | --- | --- | --- | --- |
| 基本请求信息 (Input) | TaskId | string | \\- | **必选**，您待重跑的任务TaskId |
| 翻译 (Translation) | TranslationEnabled | boolean | false | 是否开启翻译功能。 |
| Translation.TargetLanguages | list\\[string\\] | \\[en\\] | - 如果开启翻译，需要设置目标翻译语言 - 支持设置 中文（cn）、英语（en）、日语（ja）、韩语（ko）、德语（de）、法语（fr）、俄语（ru）。 |
| 章节速览 | AutoChaptersEnabled | boolean | false | 章节速览功能，包括：议程标题和议程摘要。 |
| 要点提炼 | MeetingAssistanceEnabled | boolean | false | 关键词、行动项、待办、场景识别。 |
| 摘要总结 | SummarizationEnabled | boolean | false | 是否开启摘要功能。 |
| Summarization.Types | list\\[string\\] | \\[\\] | 支持设置1个或多个。 - Paragraph（全文摘要） - Conversational（发言总结） - QuestionsAnswering（问答回顾、要点回顾） - MindMap（思维导图） |
| PPT提取及摘要 | PptExtractionEnabled | boolean | false | 是否开启PPT功能，包含PPT抽取、PPT摘要。 |
| 口语书面化 | TextPolishEnabled | boolean | false | 是否开启口语书面化功能。 |
| 服务质检 | ServiceInspectionEnabled | boolean | false | 是否开启服务质检功能。 |
| ServiceInspection | object | \\- | 参考[服务质检参数对象](https://help.aliyun.com/zh/tingwu/service-inspection#823d1c4278rt5)对服务过程中的对话进行质量检测，支持自定义多个质检维度，辅助客户提升服务水平。 |
| 自定义Prompt | CustomPromptEnabled | boolean | false | 是否开启自定义prompt功能。 |
| CustomPrompt | object | \\- | 参考[自定义prompt参数对象](https://help.aliyun.com/zh/tingwu/custom-prompt#94461d6b78d8h)由客户自主定义大模型提示词，引导大模型完成客户定义的各类任务。 |

#### **示例代码**

Python

```
#!/usr/bin/env python
#coding=utf-8

import os
import json
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

def init_parameters():
    root = dict()
    root['AppKey'] = '输入您在听悟管控台创建的Appkey'
    # 基本请求参数
    input = dict()
    input['TaskId'] = '请输入已完成任务的TaskId'
    root['Input'] = input

    # AI相关参数，按需设置即可
    parameters = dict()
    # 音视频转换： 暂不支持重新运行
    # 语音识别: 暂不支持重新运行语音识别算法

    # 翻译： 可选
    parameters['TranslationEnabled'] = True
    translation = dict()
    translation['TargetLanguages'] = ['en'] # 假设翻译成英文
    parameters['Translation'] = translation

    # 章节速览： 可选
    parameters['AutoChaptersEnabled'] = True

    # 智能纪要： 可选
    parameters['MeetingAssistanceEnabled'] = True

    # 摘要相关： 可选
    parameters['SummarizationEnabled'] = True
    summarization = dict()
    summarization['Types'] = ['Paragraph', 'Conversational', 'QuestionsAnswering', 'MindMap']
    parameters['Summarization'] = summarization
    root['Parameters'] = parameters

    # PPT抽取： 可选（不支持对实时会议或原文件是音频格式的离线转写任务的重跑）
    parameters['PptExtractionEnabled'] = True
    
    # 口语书面化： 可选
    parameters['TextPolishEnabled'] = True
    
    root['Parameters'] = parameters
    return root

body = init_parameters()
print(body)

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
request.add_query_param('type', 'offline')

request.set_content(json.dumps(body).encode('utf-8'))
response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))
```

Java

```
package com.alibaba.tingwu.client.demo.common;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.aliyuncs.CommonRequest;
import com.aliyuncs.CommonResponse;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.exceptions.ClientException;
import com.aliyuncs.http.FormatType;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.http.ProtocolType;
import com.aliyuncs.profile.DefaultProfile;
import org.junit.Test;

/**
 * @author tingwu2023
 * @desc 演示了通过OpenAPI 根据TaskId对已完成的任务进行重新运行的 调用方式。
 */
public class RerunTaskTest {

    @Test
    public void testRerunTask() throws ClientException {
        CommonRequest request = createCommonRequest("tingwu.cn-beijing.aliyuncs.com", "2023-09-30", ProtocolType.HTTPS, MethodType.PUT, "/openapi/tingwu/v2/tasks");
        request.putQueryParameter("type", "offline");

        JSONObject root = new JSONObject();
        JSONObject input = new JSONObject();
        input.put("TaskId", "请输入已完成任务的TaskId");
        root.put("Input", input);
        root.put("AppKey", "输入您在听悟管控台创建的Appkey");

        JSONObject parameters = initRequestParametersForReRun();
        root.put("Parameters", parameters);

        System.out.println(root.toJSONString());
        request.setHttpContent(root.toJSONString().getBytes(), "utf-8", FormatType.JSON);

        // TODO 请通过环境变量设置您的AccessKeyId、AccessKeySecret
        DefaultProfile profile = DefaultProfile.getProfile("cn-beijing", System.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), System.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"));
        IAcsClient client = new DefaultAcsClient(profile);
        CommonResponse response = client.getCommonResponse(request);
        System.out.println(response.getData());
    }

    public static JSONObject initRequestParametersForReRun() {
        JSONObject parameters = new JSONObject();

        // 音视频转换： 暂不支持重新运行

        // 语音识别: 暂不支持重新运行语音识别算法

        // 翻译： 可选
        JSONObject translation = new JSONObject();
        JSONArray langArry = new JSONArray();
        langArry.add("en");
        translation.put("TargetLanguages", langArry);
        parameters.put("Translation", translation);
        parameters.put("TranslationEnabled", true);

        // 章节速览： 可选
        parameters.put("AutoChaptersEnabled", true);

        // 智能纪要： 可选
        parameters.put("MeetingAssistanceEnabled", true);

        // 摘要相关： 可选
        parameters.put("SummarizationEnabled", true);
        JSONObject summarization = new JSONObject();
        JSONArray types = new JSONArray().fluentAdd("Paragraph").fluentAdd("Conversational").fluentAdd("QuestionsAnswering").fluentAdd("MindMap");
        summarization.put("Types", types);
        parameters.put("Summarization", summarization);

        // PPT抽取： 可选（不支持对实时会议或原文件是音频格式的离线转写任务的重跑）
        //parameters.put("PptExtractionEnabled", false);
      
      	// 口语书面化：可选
        parameters.put("TextPolishEnabled", true);

        return parameters;
    }
  
    public static CommonRequest createCommonRequest(String domain, String version, ProtocolType protocolType, MethodType method, String uri) {
        CommonRequest request = new CommonRequest();
        request.setSysDomain(domain);
        request.setSysVersion(version);
        request.setSysProtocol(protocolType);
        request.setSysMethod(method);
        request.setSysUriPattern(uri);
        request.setHttpContentType(FormatType.JSON);
        return request;
    }
}
```

Go

```
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/aliyun/alibaba-cloud-sdk-go/sdk"
	"github.com/aliyun/alibaba-cloud-sdk-go/sdk/requests"
)

type TranscodeingParam struct {
	TargetAudioFormat     string `json:"TargetAudioFormat,omitempty"`
	TargetVideoFormat     string `json:"TargetVideoFormat,omitempty"`
	VideoThumbnailEnabled bool   `json:"VideoThumbnailEnabled,omitempty"`
	SpectrumEnabled       bool   `json:"SpectrumEnabled,omitempty"`
}

type DiarizationParam struct {
	SpeakerCount int `json:"SpeakerCount,omitempty"`
}

type TranscriptionParam struct {
	AudioEventDetectionEnabled bool              `json:"AudioEventDetectionEnabled,omitempty"`
	DiarizationEnabled         bool              `json:"DiarizationEnabled,omitempty"`
	Diarization                *DiarizationParam `json:"Diarization,omitempty"`
}

type TranslationParam struct {
	TargetLanguages []string `json:"TargetLanguages,omitempty"`
}

type SummarizationParam struct {
	Types []string `json:"Types,omitempty"`
}

type ExtraParamerters struct {
	Transcoding              *TranscodeingParam  `json:"Transcoding,omitempty"`
	Transcription            *TranscriptionParam `json:"Transcription,omitempty"`
	TranslationEnabled       bool                `json:"TranslationEnabled,omitempty"`
	Translation              *TranslationParam   `json:"Translation,omitempty"`
	AutoChaptersEnabled      bool                `json:"AutoChaptersEnabled,omitempty"`
	MeetingAssistanceEnabled bool                `json:"MeetingAssistanceEnabled,omitempty"`
	SummarizationEnabled     bool                `json:"SummarizationEnabled,omitempty"`
	Summarization            *SummarizationParam `json:"Summarization,omitempty"`
  TextPolishEnabled        bool                `json:"TextPolishEnabled,omitempty"`
}

type InputParam struct {
	SourceLanguage string `json:"SourceLanguage"`
	FileUrl        string `json:"FileUrl,omitempty"`
	TaskKey        string `json:"TaskKey,omitempty"`
	TaskId         string `json:"TaskId,omitempty"`
	Format         string `json:"Format,omitempty"`
	SampleRate     int    `json:"SampleRate,omitempty"`
}

type TaskBodyParam struct {
	Appkey      string            `json:"AppKey"`
	Input       InputParam        `json:"Input"`
	Paramerters *ExtraParamerters `json:"Parameters,omitempty"`
}

type GetTaskInfoResponse struct {
	RequestId string `json:"RequestId"`
	Code      string `json:"Code"`
	Message   string `json:"Message"`
	Data      struct {
		TaskId     string `json:"TaskId"`
		TaskKey    string `json:"TaskKey"`
		TaskStatus string `json:"TaskStatus"`
	} `json:"Data"`
}

func init_request_param_offline() *ExtraParamerters {
	param := new(ExtraParamerters)
	param.Transcoding = new(TranscodeingParam)

	transcription := new(TranscriptionParam)
	transcription.Diarization = new(DiarizationParam)
	transcription.Diarization.SpeakerCount = 2
	transcription.DiarizationEnabled = true
	param.Transcription = transcription

	// 设置翻译语言
	translation := new(TranslationParam)
	translation.TargetLanguages = []string{"en"}
	param.Translation = translation
	param.TranslationEnabled = true
	param.AutoChaptersEnabled = false
	param.MeetingAssistanceEnabled = false
	param.SummarizationEnabled = true

	summarization := new(SummarizationParam)
	summarization.Types = []string{"Paragraph", "Conversational", "QuestionsAnswering", "MindMap"}
	param.Summarization = summarization
  param.TextPolishEnabled = true

	return param
}

func test_rerun_task() {
	akkey := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
	aksecret := os.Getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
	client, err := sdk.NewClientWithAccessKey("cn-beijing", akkey, aksecret)
	if err != nil {
		log.Default().Fatalln(err)
		return
	}

	request := requests.NewCommonRequest()
	request.Method = "PUT"
	request.Domain = "tingwu.cn-beijing.aliyuncs.com"
	request.Version = "2023-09-30"
	request.SetContentType("application/json")
	request.PathPattern = "/openapi/tingwu/v2/tasks"
	request.QueryParams["type"] = "offline"

	param := new(TaskBodyParam)
	param.Appkey = "输入您在听悟管控台创建的Appkey"
	param.Input.SourceLanguage = "cn"
	param.Input.TaskId = "请输入已完成任务的TaskId"
	param.Input.FileUrl = "https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/asr_example.wav"
	param.Input.TaskKey = "task_" + fmt.Sprint(time.Now().Unix())

	b, _ := json.Marshal(param)
	log.Default().Print("request body:\n", string(b))
	request.SetContent(b)
	request.SetScheme("https")

	response, err := client.ProcessCommonRequest(request)
	if err != nil {
		log.Default().Fatalln(err)
		return
	}

	log.Default().Print("response body:\n", string(response.GetHttpContentBytes()))
}

func main() {
	test_rerun_task()
}
```

#### **示例输出**

在重跑任务后，您可以根据该TaskId继续查询任务状态和结果，输入请求与提交任务时基本一致，以JSON格式的字符串传入请求对象的Body，示例JSON报文如下：

```
{
    "Input":{
        "TaskId":"be602978409b47ecb1788e36********"
    },
    "Parameters":{
        "Translation":{
            "TargetLanguages":[
                "en"
            ]
        },
        "TranslationEnabled":true
    }
}
```

#### **协议解析**

具体字段定义如下。

| **参数名** | **类型** | **说明** |
| --- | --- | --- |
| TaskId | string | 创建任务时生成的TaskId |
| TaskStatus | string | 任务状态，包括： - ONGOING ：运行中 - COMPLETED : 已完成 - FAILED ： 任务失败 - INVALID ：无效，可能是TaskId不存在 |
| OutputMp3Path | string | 若您在请求参数时，设置了将原始音视频转成mp3格式，通过此字段返回生成的mp3文件的http下载链接 |
| Result | list\\[\\] | 多个算法结果的集合： - Transcription ：[语音转写](https://help.aliyun.com/zh/tingwu/voice-transcription) - AutoChapters ： [章节速览](https://help.aliyun.com/zh/tingwu/chapter-quick-view) - Summarization： [摘要总结（全文摘要、发言总结、问答回顾、思维导图）](https://help.aliyun.com/zh/tingwu/large-model-summary) - MeetingAssistance ： [要点提炼（待办事项、关键词、重点内容）](https://help.aliyun.com/zh/tingwu/intelligent-summary) - PptExtraction：[PPT抽取及摘要](https://help.aliyun.com/zh/tingwu/ppt-extraction-and-summary) - Translation ： [文本翻译](https://help.aliyun.com/zh/tingwu/text-translation) 提示，此处返回的均是下载链接，您可以参考对应模型章节的介绍，处理结果。 |
| ErrorCode | string | 错误原因 |
| ErrorMessage | string | 错误详细信息 |

## 常见问题

**生成的http链接肯定是有效的，为什么报AudioFileLink？**

-   虽然通常情况下结果可以分钟级返回，但并不能保证。因离线任务转写属于异步处理过程，存在着排队状态，因此当前离线任务时效性是3小时内返回。如果您设置的音频http链接有效期不足3小时，则可能存在当处理该任务时由于链接已过期而无法下载的可能。
    

**返回结果的http链接是有时效性的吗？**

-   返回结果中参数Result内的http链接有30天的有效期，30天后您将无法通过该链接访问到任务结果。需要注意的是，Result内容中的http链接同样为30天有效期，例如PPT抽取的Result中包含了PPT封面的图片文件http链接，该链接同样会在30天后失效。
    
-   如果返回结果中的http链接失效，您可以通过调用任务查询接口，重新获取30天有效期的任务结果。
    

**重跑任务在什么时候或什么场景下使用？**

-   如果您每次提交的离线转写任务都是预知需要进行哪些算法处理、获取哪些结果的话，可以在提交时一次性设置对应功能参数即可，此时是不需要进行重跑的。
    
-   如果您基于听悟API进行二次封装开发，比如自有SaaS服务，允许用户基于交互的方式展现不同算法结果，您可以通过此接口进行重跑，加速执行速度。
    

**重跑任务和我重新提交一次音视频文件离线转写有什么区别或好处？**

-   如果您重新提交一次音视频文件离线转写+新增参数的方式一样可以完成本文档描述的功能， 但若您通过重跑任务的形式执行，因为该方式并不是从0开始处理，会复用上一次的部分算法结果，因此执行时间会相对变短，以及由于复用，相对的调用成本也不会带来冗余。
    

**语种该怎么选择？**

-   常见语种场景示例如下：
    
    | 语种类型 | 对应参数 | 适用场景 | 参考示例 |
    | 单语种 （已知语种） | 参数名：Input.SourceLanguage 参数值可配置（单选）：中文（cn）、 英语（en）、粤语（yue）、日语（ja）、韩语（ko） | - 单语种语音识别模型。 - 中、英支持8K和16K。 - 日、粤、韩仅支持16K。 | **示例1：** 若已知语音的语种是中文 Input.SourceLanguage="cn" 识别结果：感谢您使用通义听悟。 **示例2：** 若已知语音的语种是英文 Input.SourceLanguage="en" 识别结果：Thank you for using Tongyi Tingwu. |
    | 单语种 （未知语种） | 参数名：Input.SourceLanguage 参数值：auto | - 自动单语种识别。 - 仅支持16K。 - 若未知语音中涉及的语种，可传入自动语种识别（auto），语种算法检测后，系统自动选择对应的单语种模型进行语音识别，**此功能仅在离线转写任务下可用**。 - auto的语种判定范围：中、英、日、粤、韩。 | **示例1：** 若未知语音的语种，需要自动先进行语种检测和判定再进行识别。 Input.SourceLanguage="auto" 识别结果：感谢您使用通义听悟。 [查看语种识别结果](https://help.aliyun.com/zh/tingwu/voice-transcription#f59049cdday10)。 |
    | 多语种混合 | - 参数名1：Input.SourceLanguage 参数值：multilingual - 参数名2：Input.LanguageHints 参数值可配置（可多选）： 中文（cn）， 英语（en）， 粤语（yue）， 日语（ja）、韩语（ko）、德语（de）、法语（fr）、俄语（ru） | - 多语种语音识别。 - 仅支持16K。 - 支持同时识别出中文、英文、日语、粤语、韩语、德语、法语和俄语。 - 支持限定语种的范围。 | **示例1：** 若语音中的语种非单语种，涉及多个语种，直接识别对应语种的文字。 Input.SourceLanguage="multilingual" 识别结果：hello, everyone. 感谢您使用通义听悟。 **示例2：** 若语音中的语种非单语种，涉及多个语种，但已知语种的范围（如只有中、英、粤），直接识别对应语种的文字，同时避免误识别出日、法、俄等和场景无关的语种。 Input.SourceLanguage="multilingual" Input.LanguageHints=\\['cn', 'en', 'yue'\\] |




本文主要介绍语音转写的AI能力和实现方式。

语音转写是通义听悟的核心功能， 用以将音视频文件或实时音频流中的语音转写成文字。语音转写是通义听悟API服务链路中的第一个节点，必选其中的一种形式，无法禁用。支持中、英、粤、日等语种，可在转写参数中配置说话人分离功能。

## 请求参数

| **参数名** | **类型** | **是否必填** | **说明** |
| --- | --- | --- | --- |
| Transcription | object | 否   | 语音识别控制参数对象。 |
| Transcription.DiarizationEnabled | boolean | 否   | 是否在转写过程中开启发言人区分（说话人分离）功能。 |
| Transcription.Diarization | object | 否   | 说话人分离功能对象。 |
| Transcription.Diarization.SpeakerCount | int | 否   | 0：说话人角色区分结果为不定人数。 2：说话人角色区分结果为2人。 |
| Transcription.PhraseId | string | 否   | 热词词表ID。 |
| Transcription.Model | string | 否   | **语音转写模型选择**，通过该参数可调用领域专属模型，用于提升特定领域的识别准确率，该参数为空时则调用默认模型。目前可选参数如下： - "domain-automotive"：汽车领域销售对话语音识别模型，可适用于实时和离线转写任务； - "domain-education"：教育领域网课场景语音识别模型，仅适用于离线转写任务； - 其他领域语音识别模型即将上线，敬请期待。 |

其他请求参数的含义，请根据实时或离线场景查阅对应文档：

-   [实时场景-请求参数](https://help.aliyun.com/zh/tingwu/interface-and-implementation#0c04ec5078mbg)
    
-   [离线场景-请求参数](https://help.aliyun.com/zh/tingwu/offline-transcribe-of-audio-and-video-files#ee63e72178qqa)
    

**说明**

Transcription.Model参数：通过该参数可调用**领域专属模型**，可用于提升特定领域的识别准确率。目前可选用的领域专属模型如下表所示：

| **模型名称** | **参数值** | **支持语言** | **采样率** | **实时/离线** | **适用场景** |
| --- | --- | --- | --- | --- | --- |
| 汽车领域销售对话语音识别模型 | domain-automotive | 中文  | 16k | 离线  | 适用于汽车行业，包括门店接待、汽车试驾、车型推销等场景下的语音识别 |
| 教育领域网课场景语音识别模型 | domain-education | 中文  | 16k | 离线  | 适用于教育行业，包括网课等场景下的语音识别 |

## **示例设置**

```
// 完全不设置
{
    "Input":{
        ...
    },
    "Parameters":{

    }
}

// 设置开启说话人分离功能
{
    "Input":{
        ...
    },
    "Parameters":{
        "Transcription":{
            "DiarizationEnabled":true,
            "Diarization":{
                "SpeakerCount":2
            }
        }
    }
}
```

## **代码示例**

Python

```
#!/usr/bin/env python
#coding=utf-8

import os
import json
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

def init_parameters():
    root = dict()
    root['AppKey'] = '输入您在听悟管控台创建的Appkey'

    # 基本请求参数
    input = dict()
    input['SourceLanguage'] = 'cn'
    input['TaskKey'] = 'task' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    input['FileUrl'] = '输入待测试的音频url链接'
    root['Input'] = input

    # AI相关参数，按需设置即可
    parameters = dict()

    # 语音识别控制相关
    transcription = dict()
    # 角色分离
    transcription['DiarizationEnabled'] = True
    diarization = dict()
    diarization['SpeakerCount'] = 2
    transcription['Diarization'] = diarization
    parameters['Transcription'] = transcription

    root['Parameters'] = parameters
    return root

body = init_parameters()
print(body)

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
request.add_query_param('type', 'offline')

request.set_content(json.dumps(body).encode('utf-8'))
response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))
```

Java

```
package com.alibaba.tingwu.client.demo.aitest;
import com.alibaba.fastjson.JSONObject;
import com.aliyuncs.CommonRequest;
import com.aliyuncs.CommonResponse;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.exceptions.ClientException;
import com.aliyuncs.http.FormatType;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.http.ProtocolType;
import com.aliyuncs.profile.DefaultProfile;
import org.junit.Test;

/**
 * @author tingwu2023
 */
public class TranscriptionTest {

    @Test
    public void testFiletrans() throws ClientException {
        CommonRequest request = createCommonRequest("tingwu.cn-beijing.aliyuncs.com", "2023-09-30", ProtocolType.HTTPS, MethodType.PUT, "/openapi/tingwu/v2/tasks");
        request.putQueryParameter("type", "offline");

        JSONObject root = new JSONObject();
        root.put("AppKey", "输入您在听悟管控台创建的Appkey");

        JSONObject input = new JSONObject();
        input.fluentPut("FileUrl", "输入待测试的音频url链接")
                .fluentPut("SourceLanguage", "cn")
                .fluentPut("TaskKey", "task" + System.currentTimeMillis());
        root.put("Input", input);

        JSONObject parameters = new JSONObject();
        JSONObject transcription = new JSONObject();
        transcription.put("DiarizationEnabled", true);
        JSONObject speakerCount = new JSONObject();
        speakerCount.put("SpeakerCount", 2);
        transcription.put("Diarization", speakerCount);
        parameters.put("Transcription", transcription);
        root.put("Parameters", parameters);
        System.out.println(root.toJSONString());
        request.setHttpContent(root.toJSONString().getBytes(), "utf-8", FormatType.JSON);

        // TODO 请通过环境变量设置您的AccessKeyId、AccessKeySecret
        DefaultProfile profile = DefaultProfile.getProfile("cn-beijing", System.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), System.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"));
        IAcsClient client = new DefaultAcsClient(profile);
        CommonResponse response = client.getCommonResponse(request);
        System.out.println(response.getData());
    }
  
    public static CommonRequest createCommonRequest(String domain, String version, ProtocolType protocolType, MethodType method, String uri) {
        // 创建API请求并设置参数
        CommonRequest request = new CommonRequest();
        request.setSysDomain(domain);
        request.setSysVersion(version);
        request.setSysProtocol(protocolType);
        request.setSysMethod(method);
        request.setSysUriPattern(uri);
        request.setHttpContentType(FormatType.JSON);
        return request;
    }
}
```

## 示例输出

```
{
    "Code":"0",
    "Data":{
        "TaskId":"10683ca4ad3f4f06bdf6e9dd********",
        "TaskStatus":"COMPLETED",
        "Result":{
            "Transcription":"http://speech-swap.oss-cn-zhangjiakou.aliyuncs.com/tingwu_data/output/1738248129743478/10683ca4ad3f4f06bdf6e9dc1f3c1584/10683ca4ad3f4f06bdf6e9dc1f3c1584_Transcription_20231031165005.json?Expires=1698828606&amp;LTAI****************&amp;Signature=GMm%2BdN2tUPx*********ehu74%3D"
        }
    },
    "Message":"success",
    "RequestId":"7a63ee43-8a35-4ef2-8d5c-c76*********"
}
```

其中Transcription字段对应的即为语音转写结果的http url下载链接。

## 协议解析

上述输出中的语音转写结果url中的内容为JSON格式的报文，示例如下所示。（实时转写结果中不包含AudioInfo中的Size、SampleRate和Language字段）

```
{
    "TaskId":"10683ca4ad3f4f06bdf6e9dc*********",
    "Transcription":{
        "AudioInfo": {
            "Size": 670663,
            "Duration": 10394,
            "SampleRate": 48000,
            "Language": "cn"
        },
        "Paragraphs":[
            {
                "ParagraphId":"16987422100275*******",
                "SpeakerId":"1",
                "Words":[
                    {
                        "Id":10,
                        "SentenceId":1,
                        "Start":4970,
                        "End":5560,
                        "Text":"您好，"
                    },
                    {
                        "Id":20,
                        "SentenceId":1,
                        "Start":5730,
                        "End":6176,
                        "Text":"我是"
                    }
                ]
            }
        ]
        "AudioSegments": [
            [12130, 16994],
            [17000, 19720],
            [19940, 28649]
        ]
    }
}
```

具体字段定义如下。

| **参数名** | **类型** | **说明** |
| --- | --- | --- |
| TaskId | string | 创建任务时生成的TaskId。 |
| Transcription | object | 语音转写结果对象。 |
| Transcription.Paragraphs | list\\[\\] | 语音转写结构以段落形式组织的集合。 |
| Transcription.Paragraphs\\[i\\].ParagraphId | string | 段落级别id。 |
| Transcription.Paragraphs\\[i\\].SpeakerId | string | 发言人id。 |
| Transcription.Paragraphs\\[i\\].Words | list\\[\\] | 该段落包含的word信息。 |
| Transcription.Paragraphs\\[i\\].Words\\[i\\].Id | int | word序号，通常无须关注。 |
| Transcription.Paragraphs\\[i\\].Words\\[i\\].SentenceId | int | 句子id，同属于一个SentenceId的word信息可以组装成一句话。 |
| Transcription.Paragraphs\\[i\\].Words\\[i\\].Start | long | 该word相对于音频起始时间的开始时间，相对时间戳，单位毫秒。 |
| Transcription.Paragraphs\\[i\\].Words\\[i\\].End | long | 该word相对于音频起始时间的结束时间，相对时间戳，单位毫秒。 |
| Transcription.Paragraphs\\[i\\].Words\\[i\\].Text | string | word文本。 |
| Transcription.AudioInfo | object | 音频信息对象。 |
| Transcription.AudioInfo.Size | long | 音频大小，单位：字节。 |
| Transcription.AudioInfo.Duration | long | 音频时长，单位：毫秒。（实时语音转写时，该字段不表示实际音频时长） |
| Transcription.AudioInfo.SampleRate | int | 音频采样率。 |
| Transcription.AudioInfo.Language | string | 音频语种。 |
| Transcription.AudioSegments | list\\[\\]\\[\\] | 有效音频片断范围。 |
| Transcription.AudioSegments\\[i\\]\\[0\\] | int | 有效音频片段的开始时间，单位为毫秒。 |
| Transcription.AudioSegments\\[i\\]\\[1\\] | int | 有效音频片段的结束时间，单位为毫秒。 |

## **常见问题**

**上传一个文件，为什么识别结果为空？**

您可以检查原始音视频文件是否存在有效人声、背景噪音过多等问题。

本文主要介绍章节速览的AI能力和实现方式。章节速览是将音视频内容，先按交流主题进行分割，再提炼总结每个内容分段的标题及摘要。通过章节速览，可快速了解内容的结构；并在较长的内容中，快速定位所需的主题。

## 请求参数

| **参数名** | **类型** | **是否必填** | **说明** |
| --- | --- | --- | --- |
| AutoChaptersEnabled | boolean | 否   | 默认为false |
| AutoChapters | Object | 否   | 章节速览控制参数对象 |
| AutoChapters.ChapterGranularity | String | 否   | 章节粒度，可选参数：Coarse、General、Meticulous。如果不填写该参数，会默认设置为Meticulous。 Coarse：粗粒度，每小时音/视频约4个章节 General：中等粒度，每小时音/视频约6个章节 Meticulous：细粒度，每小时音/视频约12-15个章节 |
| AutoChapters.TitleLengthLevel | String | 否   | 章节标题长度级别，可选参数：Short、Normal、Long。如果不填写该参数，会默认设置为Long。 Short：6-25字，平均约13字 Normal：10-28字，平均约16字 Long：10-30字，平均约20字 |

其他请求参数的含义，请根据实时或离线场景查阅对应文档：

-   [实时场景-请求参数](https://help.aliyun.com/zh/tingwu/interface-and-implementation#0c04ec5078mbg)
    
-   [离线场景-请求参数](https://help.aliyun.com/zh/tingwu/offline-transcribe-of-audio-and-video-files#ee63e72178qqa)
    

## 示例设置

```
{
    "Input":{
        ...
    },
    "Parameters":{
        ...
        "AutoChaptersEnabled": true,
        "AutoChapters": {
            "ChapterGranularity": "Coarse",
            "TitleLengthLevel": "Short"
        }
        ...
    }
}
```

## 代码示例

Python

```
#!/usr/bin/env python
#coding=utf-8

import os
import json
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

def init_parameters():
    root = dict()
    root['AppKey'] = '输入您在听悟管控台创建的Appkey'

    # 基本请求参数
    input = dict()
    input['SourceLanguage'] = 'cn'
    input['TaskKey'] = 'task' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    input['FileUrl'] = '输入待测试的音频url链接'
    root['Input'] = input

    # AI相关参数，按需设置即可
    parameters = dict()
    # 章节速览
    parameters['AutoChaptersEnabled'] = True
    parameters['AutoChapters'] = {
        "ChapterGranularity": "Coarse",
        "TitleLengthLevel": "Short"
    }
    root['Parameters'] = parameters
    return root

body = init_parameters()
print(body)

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
request.add_query_param('type', 'offline')

request.set_content(json.dumps(body).encode('utf-8'))
response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))
```

Java

```
package com.alibaba.tingwu.client.demo.aitest;

import com.alibaba.fastjson.JSONObject;
import com.aliyuncs.CommonRequest;
import com.aliyuncs.CommonResponse;
import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.exceptions.ClientException;
import com.aliyuncs.http.FormatType;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.http.ProtocolType;
import com.aliyuncs.profile.DefaultProfile;
import org.junit.Test;

/**
 * @author tingwu2023
 */
public class AutoChaptersTest {

    @Test
    public void testAutoChapters() throws ClientException {
        CommonRequest request = createCommonRequest("tingwu.cn-beijing.aliyuncs.com", "2023-09-30", ProtocolType.HTTPS, MethodType.PUT, "/openapi/tingwu/v2/tasks");
        request.putQueryParameter("type", "offline");

        JSONObject root = new JSONObject();
        root.put("AppKey", "输入您在听悟管控台创建的Appkey");

        JSONObject input = new JSONObject();
        input.fluentPut("FileUrl", "输入待测试的音频url链接")
                .fluentPut("SourceLanguage", "cn")
                .fluentPut("TaskKey", "task" + System.currentTimeMillis());
        root.put("Input", input);

        JSONObject parameters = new JSONObject();
        parameters.put("AutoChaptersEnabled", true);
        JSONObject autoChapters = new JSONObject();
        autoChapters.put("ChapterGranularity", "Coarse");
        autoChapters.put("TitleLengthLevel", "Short");
        parameters.put("AutoChapters", autoChapters);
        root.put("Parameters", parameters);
        System.out.println(root.toJSONString());
        request.setHttpContent(root.toJSONString().getBytes(), "utf-8", FormatType.JSON);

        // TODO 请通过环境变量设置您的AccessKeyId、AccessKeySecret
        DefaultProfile profile = DefaultProfile.getProfile("cn-beijing", System.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), System.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"));
        IAcsClient client = new DefaultAcsClient(profile);
        CommonResponse response = client.getCommonResponse(request);
        System.out.println(response.getData());
    }

    public static CommonRequest createCommonRequest(String domain, String version, ProtocolType protocolType, MethodType method, String uri) {
        // 创建API请求并设置参数
        CommonRequest request = new CommonRequest();
        request.setSysDomain(domain);
        request.setSysVersion(version);
        request.setSysProtocol(protocolType);
        request.setSysMethod(method);
        request.setSysUriPattern(uri);
        request.setHttpContentType(FormatType.JSON);
        return request;
    }
}
```

## 示例输出

```
{
    "Message": "success", 
    "Code": "0", 
    "Data": {
        "Result": {
            "Transcription": "http://speech-swap-hangzhou.oss-cn-hangzhou.aliyuncs.com/tingwu/output/1503864348104017/05c45066fc6d496dae9b583426fdaae8/05c45066fc6d496dae9b583426fdaae8_Transcription_20231028230430.json?Expires=1698593389&OSSAccessKeyId=LTAI****************&Signature=*********huzKcM4tzimubU%3D", 
            "AutoChapters": "http://speech-swap-hangzhou.oss-cn-hangzhou.aliyuncs.com/tingwu/output/1503864348104017/05c45066fc6d496dae9b583426fdaae8/05c45066fc6d496dae9b583426fdaae8_AutoChapters_20231028230459.json?Expires=1698593389&OSSAccessKeyId=LTAI****************&Signature=*********V8O%2BG4paM0VMv0AIyK4%3D"
        }, 
        "TaskId": "05c45066fc6df96dg09bf8z4*********", 
        "TaskStatus": "COMPLETED"
    }, 
    "RequestId": "7AE5CB5C-7287-16D1-BA93-G43********"
}
```

其中AutoChapters字段对应的即为章节速览结果的http url下载链接。

## 协议解析

上述输出中的章节速览结果url中的内容为JSON格式的报文，示例如下所示。

```
{
    "TaskId":"05c45066fc6df96dg09bf8z4*********",
    "AutoChapters":[
        {
            "Id":1,
            "Start":1930,
            "End":283874,
            "Headline":"阿里巴巴云栖大会及技术责任",
            "Summary":"云栖大会作为中国产业界的盛会，成为数字时代共同讨论的场所。阿里巴巴通过青橙奖助力青年科学家追求科学先进性。阿里云在云计算和数字生态方面不断发展，努力成为全球先进的计算基础设施。同时，阿里巴巴也在不断追求技术先进性，包括自主可控的云操作系统、算法模型的训练等。阿里巴巴希望通过低代码环境让普通人也能享受数据的成果和创造。此外，在芯片领域，阿里巴巴也在努力突破核心技术。"
        },
        {
            "Id":2,
            "Start":284050,
            "End":452084,
            "Headline":"云计算：推动中国走向现代化",
            "Summary":"平头哥围绕云计算场景定义了倚天710芯片，并助力冬奥在云上举办。云计算为各行各业带来全新的生产管理方式，推动中国走向现代化。阿里巴巴致力于追求技术先进性，并为社会发展担当更大责任，努力使云计算成为可持续发展的绿色动力。"
        }
    ]
}
```

具体字段定义如下。

| **参数名** | **类型** | **说明** |
| --- | --- | --- |
| TaskId | string | 创建任务时生成的TaskId。 |
| AutoChapters | list\\[\\] | 章节速览集合， 含有0个、1个或多个章节速览信息。 |
| AutoChapters\\[i\\].Id | int | 该章节序号。 |
| AutoChapters\\[i\\].Start | long | 该章节相对于音频起始时间的开始时间，相对时间戳，单位毫秒。 |
| AutoChapters\\[i\\].End | long | 该章节相对于音频起始时间的结束时间，相对时间戳，单位毫秒。 |
| AutoChapters\\[i\\].Headline | string | 该章节的一句话标题。 |
| AutoChapters\\[i\\].Summary | string | 章节总结。 |

## 常见问题

**章节速览功能在什么场景下可以调用？**

-   您可以在创建音视频文件离线转写或创建实时会议时，直接设置；
    
-   您也可以在离线转写或实时会议结束后，再次发起重跑任务请求（必须基于同一个TaskId），生成章节信息。
    

**为什么我调用后没有生成章节速览的结果，或章节速览结果为空？**

-   一个可能是调用参数没有启用或设置不正确，请您仔细参考开发文档进行对比并正确设置。
    
-   一个可能是您设置的语言模型并不支持生成章节信息，比如若音视频文件是日语，当前是不支持章节速览处理的。
    
-   另外一个可能是音视频文件的信息不够丰富，比如音视频文件转写后的ASR信息太少（可能是背景噪音过多或过差），导致模型无法生成章节信息。此时您可以更换一条涵盖有效信息更丰富的音视频文件进行测试。