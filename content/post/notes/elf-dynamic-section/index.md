---
title: "ELF文件 Dynamic Section"
description: "介绍 ELF 文件动态 Section 的结构、各 DT 标记含义，以及共享库依赖与 PLT/GOT 符号解析流程"
date: 2026-07-27T16:13:41+08:00
slug: "elf-dynamic-section"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - PWN
    - ELF
    - 动态链接
---

Dynamic Section（动态Section）

> 假如一个object文件参与了动态的连接，它的程序头将有一个类型为PT_DYNAMIC的元素，该段包含了.dynamic section，一个_DYNAMIC特别的符号，表面了该Section包含以下结构的一个数组

```C
  typedef struct {
      Elf32_Sword d_tag;
      union {
          Elf32_Sword d_val;
          Elf32_Addr d_ptr;
      } d_un;
  } Elf32_Dyn;

  extern Elf32_Dyn _DYNAMIC[];

```

对每一个有该类型的object，d_tag控制着d_un的解释

**\* d_val**

那些Elf32_Word object描绘了具有不同解释的整形变量。

**\* d_ptr**

那些Elf32_Word object描绘了程序的虚拟地址。在执行时，文件的虚拟地址可能和内存虚拟地址不匹配，当解释包含在动态结构中的地址时是基于原始文件的值和内存的基地址，为了一致性，文件不包含在重定位入口来纠正在动态结构中的地址。

| Name        | Value      | d_un        | Executable  | Shared Object |
| :---------- | :--------- | :---------- | :---------- | :------------ |
| DT_NULL     | 0          | ignored     | mandatory   | mandatory     |
| DT_NEEDED   | 1          | d_val       | optional    | optional      |
| DT_PLTRELSZ | 2          | d_val       | optional    | optional      |
| DT_PLTGOT   | 3          | d_ptr       | optional    | optional      |
| DT_HASH     | 4          | d_ptr       | mandatory   | mandatory     |
| DT_STRTAB   | 5          | d_ptr       | mandatory   | mandatory     |
| DT_SYMTAB   | 6          | d_ptr       | mandatory   | mandatory     |
| DT_RELA     | 7          | d_ptr       | mandatory   | optional      |
| DT_RELASZ   | 8          | d_val       | mandatory   | optional      |
| DT_RELAENT  | 9          | d_val       | mandatory   | optional      |
| DT_STRSZ    | 10         | d_val       | mandatory   | mandatory     |
| DT_SYMENT   | 11         | d_val       | mandatory   | mandatory     |
| DT_INIT     | 12         | d_ptr       | optional    | optional      |
| DT_FINI     | 13         | d_ptr       | optional    | optional      |
| DT_SONAME   | 14         | d_val       | ignored     | optional      |
| DT_RPATH    | 15         | d_val       | optional    | ignored       |
| DT_SYMBOLIC | 16         | ignored     | ignored     | optional      |
| DT_REL      | 17         | d_ptr       | mandatory   | optional      |
| DT_RELSZ    | 18         | d_val       | mandatory   | optional      |
| DT_RELENT   | 19         | d_val       | mandatory   | optional      |
| DT_PLTREL   | 20         | d_val       | optional    | optional      |
| DT_DEBUG    | 21         | d_ptr       | optional    | ignored       |
| DT_TEXTREL  | 22         | ignored     | optional    | optional      |
| DT_JMPREL   | 23         | d_ptr       | optional    | optional      |
| DT_LOPROC   | 0x70000000 | unspecified | unspecified | unspecified   |
| DT_HIPROC   | 0x7fffffff | unspecified | unspecified | unspecified   |

***DT_NULL**

一个DT_NULL标记的入口表示了_DYNAMIC数组的结束

***DT_NEEDED**

这个元素保存着以NULL结尾的字符串表的偏移量，那些字符串时所需库的名字，该偏移量是以DT_STRTAB为入口的表的索引

***DT_PLTRELSZ**

该元素保存着跟PLT关联的重定位入口的总字节大小，假设一个入口类型DT_JMPREL存在，那么DT_PLTRELSZ必须存在

***DT_PLTGOT**

该元素保存的是跟PLT关联的地址和GOT

***DT_HASH**

该元素保存着符号哈希表的地址，哈希表指向DT_SYMTAB元素引用的符号表

***DT_STRTAB**

该元素保存着字符串表地址，包括了符号名，库名，和一些其他的在该表中的字符串

***DT_SYMTAB**

该元素保存着符号表的地址，对于32位类型的文件来说，关联着一个Elf32_Sym入口

***DT_RELA**

该元素保存着重定位表的地址，就像32位文件中的Elf32_Rela，一个object文件可能很多个重定位Section，当为一个可执行和共享文件建立重定位表的时候，连接编辑器连接那些Section到一个单一的表，尽管在object文件中那些Section是保持独立的，动态连接器只看成是一个简单的表。当动态连接器为一个可执行文件创建一个进程映象或者是加一个共享object到进程映象中，它读重定位表和执行相关的动作。假如该元素存在，动态结构必须也要有DT_RELASZ和DT_RELAENT元素。当文件的重定位是mandatory，DT_RELA 或者 DT_REL可能出现（同时出现是允许的，但是不必要的）。

***DT_RELASZ**

该元素保存着DT_RELA重定位表的总字节大小

***DT_RELAENT**

该元素保存着DT_RELA重定位入口的字节大小

***DT_STRSZ**

该元素保存着字符串表的字节大小

***DT_SYMENT**

该元素保存着符号表入口的字节大小

***DT_INIT**

该元素保存着初始化函数的地址

***DT_FINI**

该元素保存着终止函数的地址

***DT_SONAME**

该元素保存着以NULL结尾的字符串表偏移量，那些名字是共享object的名字，偏移量是在DT_STRTAB入口记录的表的索引

***DT_RPATH**

该元素保存着以NULL结尾的搜索库的搜索目录字符串的字符串表偏移量

***DT_SYMBOLIC**

在共享object库中出现的该元素为在库中的引用改变动态链接器符号解析的算法，替代在可执行文件中的符号搜索，动态链接器从他自己的共享object开始

***DT_REL**

该元素相似于DT_RELA，除了它的表有潜在的加数，正如32-bit文件类型的Elf32_Rel一样，假如这个元素存在，它的动态结构必须也同时要有DT_RELSZ和DT_RELENT的元素。

***DT_RELSZ**

该元素保存着DT_REL重定位表的总字节大小

***DT_RELENT**

该元素保存着DT_RELENT重定位入口的字节大小

***DT_PLTREL**

该成员指明了PLT指向的重定位入口的类型，d_val成员保存着DT_REL或DT_RELA

***DT_DEBUG**

该成员被调试使用，它的内容没有被ABI指定

***DT_TEXTREL**

如在程序头表中段许可所指出的那样，这个成员的缺乏代表没有重置入口会引起非写段的修改。假如该成员存在，一个或多个重定位入口可能请求修改一个非写段，并且动态连接器能因此有准备。

***DT_JMPREL**

假如存在，它的入口d_ptr成员保存着重定位入口，假如lazy方式打开，那么分离它们的重定位入口让动态链接器在进程初始化时忽略他们

***DT_LOPROC** **through** **DT_HIPROC**

在该范围内的变量为特殊的处理器语义保留，除了在数组末尾的DT_NULL元素，和DT_NEEDED元素相关的次序，入口可能在任何次序

---

## Shared Object Dependencies（共享Object的依赖关系）

当连接器处理一个文档库时，它取出库中成员并且将它们拷贝到一个输出的object文件中，当运行时没有一个动态连接器时，那么静态的连接服务是可用的，共享object也提供服务，动态连接器必须把正确的共享object文件连接到实行的进程映像中，因此，可执行文件和共享的object文件之间存在明确的依赖性

当动态链接器为一个object文件创建内存段时，依赖关系（在动态结构的DT_NEEDED入口中记录）表明哪些object来为程序提供服务，通过重复的连接参考的共享object和他们的依赖关系，动态链接器可以建造一个完全的进程映像，当解决一个符号引用的时候，动态连接器以宽度优先搜索（breadth-first）来检查符号表，换句话说，它先查看自己的可实行程序中的符号表，然后是顶端DT_NEEDED入口（按顺序）的符号表，再接下来是第二级的DT_NEEDED入口，依次类推，共享object文件必须对进程是可读的；其他权限是不需要的。

> 注意：即使当一个共享object被引用多次（在依赖列关系表中），动态连接器
> 只把它连接到进程中一次。

在依赖关系列表中的名字，既会被 `DT_SONAME` 字符串拷贝，也会被建立 object 文件时的路径名拷贝。例如，动态链接器建立一个可执行文件（使用带 `DT_SONAME` 入口的 `lib1` 共享文件）和一个路径名为 `/usr/lib/lib2` 的共享 object 库，那么该可执行文件将在它自己的依赖关系列表中包含 `lib1` 和 `/usr/lib/lib2`。

假如一个共享 object 名字在任何地方包含了一个或更多的反斜杠字符（`/`），例如上面的 `/usr/lib/lib2` 文件或目录，动态链接器会直接把那个字符串自己作为路径名来使用。

假如名字没有反斜杠字符（`/`），例如上面的 `lib1`，动态链接器将按照以下三种方法的优先级顺序，来指定共享文件的搜索路径。

第一，检查动态数组标记 `DT_RPATH`。它保存着目录列表的字符串（用冒号 `:` 分隔）。例如，字符串 `/home/dir/lib:/home/dir2/lib:` 会告诉动态链接器先搜索 `/home/dir/lib`，再搜索 `/home/dir2/lib`，然后是当前目录。

第二，检查进程环境中的变量 `LD_LIBRARY_PATH`。它可以保存跟上面一样的目录列表（可以随意跟一个分号 `;` 和其他目录列表）。所有的 `LD_LIBRARY_PATH` 目录会在 `DT_RPATH` 指向的目录之后被搜索。尽管一些程序（例如连接编辑器）会对分号前和分号后的目录进行不同处理，但动态链接器不会，它会接受分号符号并按序搜索。例如 `LD_LIBRARY_PATH=/home/dir/lib:/home/dir2/lib:` 与包含分号的写法是等效的。

最后，如果通过上面的两个目录查找想要得到的库均宣告失败，那么动态链接器会去搜索系统默认的 `/usr/lib` 目录。

> 注意：出于安全考虑，对于设置了 set-user（SUID）和 set-group（SGID）的特权程序，动态链接器会直接忽略 `LD_LIBRARY_PATH` 所指定的搜索目录。但它依然会正常搜索 `DT_RPATH` 指明的目录和 `/usr/lib`。

## PLT和GOT解析过程

以下的步骤，描述了动态链接器和程序如何协作通过 PLT 和 GOT 来解析符号引用。

1. 当第一次创建程序的内存映象时，动态链接器为在 GOT 中特别的变量设置第二次和第三次的入口。下面关于那些变量有更多的解释。

2. 假如 PLT 是位置无关的，那么 GOT 的地址一定是保留在 %ebx 中的。每个在进程映象中共享的 object 文件有它自己的 PLT，并且仅仅在同一个 object 文件中，控制传输到 PLT 入口。从而，要调用的函数有责任在调用 PLT 入口前，设置 PLT 地址到寄存器中。

3. 举例说明，假如程序调用函数 name1，它将控制权传输到标号 .PLT1。

4. 第一条指令跳到 GOT 中 name1 的地址入口。在初始化时，该 GOT 入口保存着紧跟着的 pushl 指令的地址，而不是 name1 的真实地址。

5. 因此，程序会在堆栈中压入（push）一个重定位的偏移量。该重定位的偏移量是一个 32 位、非负的字节偏移量（从重定位表算起）。指派的重定位入口将是一个 R_386_JMP_SLOT 类型，它的偏移量指明了 GOT 入口（即在前面的 jmp 指令中被使用的入口）。该重定位入口也包含一个符号表的索引，因此可以告诉动态链接器哪个符号要被引用，在这里是 name1。

6. 在压入重定位的偏移量后，程序跳到 .PLT0，也就是 PLT 中的第一个入口。pushl 指令在堆栈中放置第二个 GOT 入口（got_plus_4 或 4(%ebx)）的值，从而给动态链接器提供一个字（word）的鉴别信息。然后程序跳到第三个 GOT 入口（got_plus_8 或 8(%ebx)），这会将控制权传输给动态链接器。

7. 当动态链接器接到控制权后，它会展开堆栈，查看指派的重定位入口，寻找符号的值，并在 GOT 入口中存储 name1 的真实地址，然后将控制权传输到想要的目的地。

8. 后续对 PLT 入口的调用将直接把控制权传输到 name1，而不需要第二次调用动态链接器了。所以，在 .PLT1 中的 jmp 指令将直接跳转到 name1，代替了原本“顺延执行（falling through）”转到 pushl 指令的过程。

LD_BIND_NOW 环境变量能改变动态链接器的行为。假如这个变量为非空，动态链接器会在传输控制到程序前计算 PLT 入口。换句话说，动态链接器会在进程初始化时处理重定位类型为 R_386_JMP_SLOT 的入口。否则，动态链接器会以懒惰（Lazy）的方式计算 PLT 入口，将符号解析和重定位推迟到该表入口的第一次执行时。

注意：一般来说，以懒惰（Lazy）方式绑定是对整体应用程序执行的改进。因为不使用的符号就不会招致动态链接器做无用功。然而，对于一些应用程序，在两种情况下使用懒惰方式是不受欢迎的。

第一，初始引用一个共享 object 函数比后来的调用要花的时间长，因为动态链接器需要截取调用来解析符号。一些应用程序是不能容忍这种延迟的。

第二，假如发生错误并且动态链接器不能解析该符号，动态链接器将终止程序。在懒惰方式下，这可能发生在程序运行的任意时刻。同样，一些应用程序是不能容忍这种不确定性的。通过关闭懒惰方式，如果发生解析错误，动态链接器会在应用程序接到控制权之前的初始化阶段，就强迫程序失败退出。

---

*上述内容若有理解不够深入或表述不够恰当之处，欢迎各位师傅批评指正。*
