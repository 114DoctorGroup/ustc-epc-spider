# EPC Spider——最好用的EPC刷课工具



## 介绍
这是用来在中科大EPC(English Practice Center)平台上抢课的Python脚本。EPC在很多时候可谓是一课难求，尤其是drama。然而鲜有人知的事实是，每天都会有不少人退课，故“捡漏”成为了很有效的选课技巧。

通过使用此脚本，你能够方便地选到别人刚退掉的课程，完全可以做到今天抢课，明天就上课，甚至在一周内选到2次drama！

## 功能&特点
1. 全自动抢课。自动识别验证码，被踢下线后（或者由于其他原因，cookies失效）也能自动登录。
2. 在可预约学时足够时，自动抢指定时间区间内、指定类型的课程。

3. 在可预约学时不足时，当有更早时间的课程有余位时，自动改签。
4. 如果改签失败（通常是因为人数已满），程序会立即尝试回滚，重新选上刚刚退掉的课。

## 使用说明

脚本的所有配置均配置在仓库根目录下的config.json里。

**如何指定时间区间**

在`config.json`内设置order_week_beforeequal和order_week_afterequal，即可设定想选的课的时间范围。

另外，当可用学时不足且replace.enable被启用时，replace\_earlier也会影响时间区间。

- 当replace_earlier为False时，选课区间为：

  [第order_week_beforeequal周开始, order_week_afterequal结束]

- 当replace_earlier为True时，只会选比candidate更早的课，即选课区间为：

  [第order_week_beforeequal周开始, candidate课程的开始时间]

**如何启用改签**

首先，需要将enable.replace设为True。这样，当可用学时不足时，程序会将已预约的课程改签至符合选课条件的一门课。

另外，可用`"replace.candidate"`指定一门将被改签的已预约课程，若不指定，则candidate默认为已预约的最晚课程。

若不想启用改签，可在`config.json`内把`"enable.replace"`设置为`False`。

**如何指定课程类型**

config.json内有四个bool字段："enable.situation_dialog", "enable.topical_discuss"，  "enable.debate", "enable.drama"，当它们中的部分或全部被 设为`true`时，脚本会启用相应课程的查找。

"enable.situation_dialog"必须设为False，因为程序不支持抢1学分的课。

课程类型启用的越多，总体抢到课的概率越高，但总的刷新周期会变长，请酌情考虑。



**config.json所有字段的解释**

| 字段                    | 说明                                                         |
| ----------------------- | ------------------------------------------------------------ |
| stuno                   | 必填 字符串 你的学号                                         |
| passwd                  | 必填 字符串 你的密码 必须是研究生信息平台自己的，不是统一认证的密码。 |
| verbose                 | 必填 bool 是否实时在stdout输出余课的周数                     |
| enable.loop             | 必填 bool 是否在抢到课后继续跑 （不稳定，建议设为false）     |
| enable.order            | 必填 bool 是否启用选课 设为false的话，只会输出余课周数，而不会抢课 |
| enable.replace          | 必填 bool 是否启用换课 当可用预约学时不足，且此项启用时，程序会考虑退掉已选的课，并换成更早的课 |
| enable.duplicate        | 必填 bool 是否允许重复 如果你不想选已经上过的课，可将此项设为false |
| enable.situation_dialog | 必填 bool 必须为false 暂不支持抢1学时的课，估计你们也会觉得很不划算 |
| enable.topical_discuss  | 必填 bool 是否抢topical discussion                           |
| enable.debate           | 必填 bool 是否抢debate                                       |
| enable.drama            | 必填 bool 是否抢drama                                        |
| order_week_beforeequal  | 必填 int 最晚的选课周 周数大于此值的课将不会考虑.            |
| order_week_afterequal   | 必填 int 最早的选课周 周数小于此值的课将不会考虑             |
| replace.earlier         | 必填 bool 仅在enable.replace启用时有效 是否需要换成比被替换课程的时间更早的课程 |
| replace.candidate       | 可空 string 被替换的课程名称 若空，则为已预约的最晚的一门课  |
| replace.forbidden       | 可空 string 禁止被替换的课程名称                             |
| course.forbidden        | 可空 string 禁选的课程名称                                   |
| course.favorite         | 可空 string 限选的课程名称 若非空，则只有该项指定的课程才会被考虑选 |

## 安装与运行

本脚本依赖python的`requests`包。

1. 首先，git clone
2. 复制`config.json.example`到`config.json`。
3. 在`config.json`内填入相关信息。
4. 运行`python epc_main.py


## Credits

开发

- [songchaow](https://github.com/songchaow)
  从小就喜欢写爬虫的他，这次终于写了一个实用的爬虫，并使用它为自己抢到了许多许多的drama...
- [ypluo](https://github.com/ypluo) 看了一下午的代码后，罗博为songchaow的爬虫添加了自定义可上课时间段的功能。他的代码位于分支[time_demand](https://github.com/114DoctorGroup/epc-spider/tree/time_demand)。不过songchaow对此并不怎么感冒，因为songchaow只选drama...
- [ChaoWao](https://github.com/ChaoWao) WangChao小哥哥为爬虫添加了强大的验证码识别功能。从此，大家再也不用担心被踢下线啦。

产品经理

- [ChaoWao](https://github.com/ChaoWao)

  随着ChaoWang一阵阵对程序的吐槽，程序的功能被增补地越来越完善。

测试

- [ChaoWao](https://github.com/ChaoWao) 程序在早期存在各种不稳定，songchaow害怕自己心爱的drama被错误地退掉，不敢拿自己的账号测试。于是ChaoWang挺身而出，在前期找出了许多bug，为爬虫的稳定性做出了巨大贡献。

程序员鼓励师

- [cxypjy](https://github.com/orgs/114DoctorGroup/people/cxypjy)
- [ChaoWao](https://github.com/ChaoWao)

你可以从[这篇文章]( https://www.songchaow.cn/2019/11/02/drama.html )了解这个程序是如何诞生的（还没写完）。