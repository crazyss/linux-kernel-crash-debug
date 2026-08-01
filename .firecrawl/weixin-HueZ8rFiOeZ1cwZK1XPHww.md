![cover_image](https://mmbiz.qpic.cn/mmbiz_jpg/Ug16vicVibORCibXiczfnXVFMIoibMfWYu70oXClgxSEWaDRkpLzjjN955E81Uv0BrcXtknWXrc8bCKd1B5MMVRGKtZiaJ07lLlnExHWQT3zk5new/0?wx_fmt=jpeg)

# Kernel panic之如何通过汇编定位mutex lock指针

OriginalHerbertHerbert
Kernel Panic Lab

在小说阅读器读本章

去阅读

在小说阅读器中沉浸阅读

我们在推导稳定性问题的时候，可能会遇到某个task在等待mutex lock而一直挂起的情况，类似如以下log:

bt pid

#0 \[xxxxxx\] \_\_switch\_to at xxxxxx

#1  \[xxxxxx\] \_\_schedule at xxxxxx

#2 \[xxxxxx\] schedule at xxxxxx

#3 \[xxxxxx\] schedule\_preempt\_disabled

#4 \[xxxxxx\] \_\_mutex\_lock at xxxxxx

#5 \[xxxxxx\] \_\_mutex\_lock\_slowpath at x

#6 \[xxxxxx\] mutex\_lock at xxxxxx

#7 \[xxxxxx\] func\_x at xxxxxx

在这种状况下，首先如果我们需要拿到mutex lock具体的锁的地址的话，一般可以从两个方向来拿:

1.  如果这里的lock指针是一个全局变量，这样的话汇编代码里一般会直接从某个地址里去取这个lock的指针，如下所示:

adrp    x0,     0xffffffc00ac1e000

add     x0,     x0,    0x7f0

bl      0xffffffc0097ec8ec <mutex\_lock>

x0 = 0xffffffc00ac1e000 + 0x7f0

     = 0xffffffc00ac1e7f0，

x0作为第一个传参传给mutex\_lock，由此可见x0就是lock的指针，也就是0xffffffc00ac1e7f0，然后再通过下面的命令，即可以看到mutex lock当前的owner是哪个task:

struct mutex 0xffffffc00ac1e7f0 -x

struct mutex {

      owner = {

           counter = 0xfffff8083afb601

      },

......

}

这里拿到的owner的counter需要注意的是最后三位(bit0-2)是用来存flag的，所以需要先mask掉才是真正的owner task，如上所示，counter是0xfffff8083afb601，实际的owner是0xfffff8083afb600，用以下命令可以读到这个task的详细信息:

struct task\_struct 0xffffff8083afb600

拿到这个task的pid后，通过bt pid即可拿到最近的调用栈。

2.  如果在汇编中无法直接拿到lock的指针值，那么可以尝试在栈里看是否有保存这个指针，例如如果有以下汇编:

假设func\_x调用mutex\_lock，假设func\_x在跳到mutex\_lock前有以下汇编:

func\_x:

mov   x0,  x19

bl      0xffffffc0097ec8ec <mutex\_lock>

由上面汇编可知，x0是lock的指针，而x0是等于x19的，再看mutex\_lock函数的汇编，如下所示:

mutex\_lock:

sub sp, sp, #0x30

stp x29, x30, \[sp,#16\]

add x29, sp, #0x10

stp x20, x19, \[sp,#32\]

由上面汇编可以看到x19在进入mutex\_lock函数后有被压栈，所以这里可以从栈里把x19拿到，而x19从前面的分析可以知道是等于 lock这个锁的指针的 所有就能拿到struct mutex这个结构体的指针，如果这里刚好没有压栈的话怎么办，那就多看看前后几个函数的反汇编，看有没有哪里有把lock的指针压栈的，有的话就把他从栈里取出来。

这里实际演示一下如何从栈里把前面的lock指针抠出来，假设调用栈如下所示:

#6 \[ffffffc00804bb70\] mutex\_lock

#7 \[fffffffc00804bbf0\] func\_x

左边\[ \]内是FP的值，在Arm64里也就是X29，所以在mutex\_lock函数中，X29=FP=ffffffc00804bb70，并且从前面的汇编可以看到:

mutex\_lock:

sub sp, sp, #0x30

stp x29, x30, \[sp,#16\]

add x29, sp, #0x10

这里的X29 = sp + 0x10，因为这里的X29=ffffffc00804bb70，所以

sp = ffffffc00804bb70 -0x10 =ffffffc00804bb60

并从前面的汇编看，有以下指令:

stp x20, x19, \[sp,#32\]

所以x20, x19是保存在这里的sp + 32的位置的，也就是ffffffc00804bb60 + 0x20 =ffffffc00804bb80这个地址，我们把这个地址读出来，就可以拿到lock的指针:

rd ffffffc00804bb80 32

ffffffc00804bb88这个地址存的就是X19也就是lock的指针的值。

预览时标签不可点

Scan to Follow

Got It

Scan with Weixin to

use this Mini Program

CancelAllow

CancelAllow

CancelAllow

×分析

![跳转二维码](https://mp.weixin.qq.com/s/HueZ8rFiOeZ1cwZK1XPHww)

![作者头像](http://mmbiz.qpic.cn/sz_mmbiz_png/D1vib8icibchiaKKDe9S2SqcjMWp45LObN1NhGdFF5hqpbPjcVVDEL6EefzvnL8tfpI23l2zeQgrqO1ZS244lJ2E5g/0?wx_fmt=png)

微信扫一扫可打开此内容，

使用完整服务

: ，，，，，，，，，，，，.VideoMini ProgramLike，轻点两下取消赞Wow，轻点两下取消在看ShareCommentFavorite听过