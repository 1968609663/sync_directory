# sync_directory
## version:
  create 2017-11-23 by Allen;

## 介绍：
* 运行在 python3.x 版本，使用标准库，不依赖第三方库；
* 运行时候可以同步多个文件夹内的文件，同步功能包括：文件新增，文件修改，文件删除；

## 配置：
* 在当前用户的家目录下放入配置文件 'SyncFilesConf.ini', 配置文件中包含三个部分：[dirs], [identify], [backup]；
* dirs: "D1 = D:\tmp\1"，表示指定同步操作的目录（可以指定多个目录）；"D1" 并没有实际意义（但是不能重复）；"D:\tmp\1" 表示目录路径；
* identify: "NAME = YiZai", 识别文件，注意没有文件后缀名，只有同步目录下有这个文件才能执行同步同能，例如自己创建文件 D:\tmp\1\YiZai； 
* backup: 指定备份目录，删除的文件会自动移动到该目录下的对应日期目录下（目录下保持原始目录结构），对于同名文件使用 uuid 进行区分；
* 按照指定的配置信息创建对应的文件夹和对应的文件；



## introduce:
* running in python3.x, use starnd libary;
* multiple local directory's file synchronization;
* process directory's file handle: new, modify, delete; 


## config: 
* in current user home directory create configure file 'SyncFilesConf.ini', the config contain sections [dirs], [identify], [backup];
* [dirs]: the section's item key meaningless, but attention item value means the process directory;
* [identify]: NAME = YiZai, express in process directory should contain a file 'YiZai' that use identify;
* [backup]: assign to the backup directory, deleted files will move in the directory to backup;
 