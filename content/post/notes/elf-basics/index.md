---
title: "ELF知识点"
description: "讲解 ELF 动态链接中的 DT_RELA 与 DT_JMPREL 重定位表，及其在 ret2dlresolve 技术中的作用。"
date: 2026-07-29T15:14:47+08:00
slug: "elf-basics"
image: ""
math: true
categories:
    - 学习笔记
tags:
    - PWN
    - ELF
    - 动态链接
---

## DT_REL(32)或DT_RELA(64)

对应段名：.rel_dyn或.rela.dyn

里面存着全局变量的引用，或者不需要延迟绑定的内部函数指针，在程序启动阶段即开始处理，也就是程序刚一加载，动态链接器就顺着DT_RELA把这张表从头到尾全检查一遍，把所有真实内存地址都填好

## DT_JMPREL

对应段名：.rel.plt或.rela.plt

里面存着所有通过PLT表调用的外部函数(比如read，write，system等等)，在程序运行中也就是第一次调用函数时处理，其实这就是延迟绑定的过程

**针对ret2dlresolve技术**，我们底层核心函数是_dl_runtime_resolve，当我们在ROP链触发这个函数时， _dl_fixup写死了，它只会去link_map里找DT_JMPREL这个指针，然后把传进来的reloc_arg当做偏移量，然后去找出reloc重定位表，对于32位，reloc_arg是一个字节偏移量，找重定位结构体的方法是：
$$
Elf32\_Rel\space *reloc=(Elf32\_Rel\space *)(真实的\_DT\_JMPREL地址+reloc\_arg)
$$
通常来说，对于32位很好算出reloc_arg，然后传进来就可以了

而对于64位，reloc_arg是一个数组下标，结构体计算方法变成了：
$$
Elf\_Rela\space *reloc=(Elf64\_Rela\space *)(\text{真实的}\_DT\_JMPREL\text{地址}+reloc\_arg*24)
$$

> 注：sizeof(Elf64_Rela)刚好24个字节

这样看，我们构造的差值还得被24整除，否则会报错，比较难。。同时，64位下reloc_arg不仅会去查重定位表，还会去查版本表(DT_VERSYM)，因此如果按照32位一样构造很大的reloc_arg的话，就会瞬间崩溃！

知道这个，就能理解为什么64位我们不能该参数而是要改地图了，而且伪造link_map时，我们必须把假地图的1_info[DT_JMPREL]指向我们在bss段布置的假重定位结构体(Elf64_Rela)，这样才能找到他

| 宏定义 (Macro)       | 对应的 ELF 段名 (Section) | 负责的业务范围         | 发生的时间点           | 在 ret2dlresolve 中的地位 |
| -------------------- | ------------------------- | ---------------------- | ---------------------- | ------------------------- |
| **DT_REL / DT_RELA** | .rel.dyn / .rela.dyn      | 全局变量、非 PLT 数据  | 启动前立刻完成 (Eager) | 不关心，解析器不读它      |
| **DT_JMPREL**        | .rel.plt / .rela.plt      | 外部函数调用 (GOT/PLT) | 运行时按需解析 (Lazy)  | **核心目标**，必须伪造它  |

---

## 表与表项

> 可以理解为整体与个体的关系

就拿重定位表和重定位表项来说吧。。

### 重定位表

它是一整块连续的内存区域，包含了程序里所有需要重定位的信息集合，在ELF中表示为：.rel.plt段，.rela.plt段，同时，在link_map中，DT_JMPREL指向的就是这张表的第一行第一列的基址

本质是一个结构体数组

### 重定位表项

它是重定位表(数组)里面的一个具体元素，一个表项，只负责一个具体的函数，表示有：Elf32_Rel，Elf64_Rela，都是重定位表项，里面存放着具体的执行逻辑，比如r_offset(填充地址)，r_info(找符号地址)

比如，64位下Elf64_Rela *reloc = (Elf64_Rela *)( 真实的_DT_JMPREL_地址 + reloc_arg * 24 );

reloc就是最终取出来的重定位表项

---

*以上内容如有理解不到位或表述不当的地方，还请各位师傅不吝赐教。*
