#coding:utf-8
"""
@summary: Synchro assigment directory's files
@Author: Allen
@Email: lingyunzou@aliyun.com
@Info: Coding in windows10, python3.5.1
"""
import sys
import os
import time
import shutil
import pickle
import filecmp
import uuid
import configparser

from itertools import combinations, product
from functools import wraps
from multiprocessing import Pool


__version__ = '0.0.0'
user_home = os.path.expanduser('~')
g_info_f = 'sync.info'
g_copy_count = 0
g_del_count = 0

def del_empty_dir(currentDir):
    """
    @summary: recursion delete all empty directory
    :param currentDir: path
    :return: None
    """
    if not os.path.isdir(currentDir):
        return
    fileList = os.listdir(currentDir)
    for d in fileList:
        dir = currentDir + os.sep + d
        if os.path.isdir(dir):
            del_empty_dir(dir)
    if not os.listdir(currentDir):
        os.rmdir(currentDir)
        return

def get_cur_time(time_stamp=time.time(), format_str='%Y%m%d'):
    time_local = time.localtime(time_stamp)
    strf_time = time.strftime(format_str, time_local)
    return strf_time

def get_cost_time(func):
    """
    @summary: decrator to get function cost cpu second time
    :param func: function
    :return:
    """
    @wraps(func)
    def _inner(*args, **kwargs):
        st = time.clock()
        res = func(*args, **kwargs)
        print('%s cost seconds : %s' % (func.__name__, time.clock() - st))
        return res
    return _inner

def pickle_save(fn, data):
    with open(fn, 'wb') as fp:
        pickle.dump(data, fp)


class SyncDirs(object):
    def __init__(self, conf=None):
        self.identify = None
        self.backup = None
        self.conf = conf or os.path.join(user_home, 'SyncFilesConf.ini')

    @get_cost_time
    def run(self, del_empty=True):
        """
        @summary: start process assigment directory files
        :return: None
        """
        abs_files_info, last_info_d = self.get_all_files()
        cur_info_d = dict(abs_files_info)
        if last_info_d is not None:
            last_info_d_set = {k: set([i[0] for i in v]) for k, v in last_info_d.items()}
            cur_info_d_set = {k: set([i[0] for i in v]) for k, v in cur_info_d.items()}
            self._proc_delete(last_info_d_set, cur_info_d_set)

        self._proc_new_modify(abs_files_info)
        all_dirs = [i[0] for i in abs_files_info]
        if del_empty:
            list(map(lambda x: del_empty_dir(x), all_dirs))

        tmp_info, _ = self.get_all_files()
        for _d in tmp_info:
            path = os.path.join(_d[0], g_info_f)
            pickle_save(path, _d[1])

        print('=' * 50, '\n')
        print('Copy files : %s' % g_copy_count)
        print('Delete files : %s' % g_del_count)
        print('=' * 50, '\n')

    def _proc_delete(self, last, cur):
        """
        @summary: sync deleted files, move the delete file to backup directory
        :param last: last run time directory tree set
        :param cur: current run time directory tree set
        :return: None
        """
        deleted_info = {}
        all_dirs = cur.keys()
        for _dn, _info_set in last.items():
            _d_c_set = cur.get(_dn, None)
            if _d_c_set:
                diff_set = _info_set - _d_c_set
                deleted_info[_dn] = list(diff_set)
        deleted_info = {k: v for k, v in deleted_info.items() if v}
        if deleted_info:
            targets = [i for i in list(product(*[deleted_info.items(), all_dirs])) if i[-1] != i[0][0]]
            bak_dir = os.path.join(self.backup, get_cur_time())
            for t in targets:
                src_d_s = map(lambda x:os.path.join(t[1], x), t[0][1])
                dst_d_s = map(lambda x:os.path.join(bak_dir, x), t[0][1])
                move_infos = zip(src_d_s, dst_d_s)
                for m in move_infos:
                    self._move(m[0], m[1])

    def _proc_new_modify(self, files_info):
        """
        @summary: process multiple directory's difference and newly files
        :param files_info:
        :return: None
        """
        for both_con in combinations(files_info, 2):
            dir_name_1, dir_files_d_1 = both_con[0][0], {i[0]: i[1] for i in both_con[0][1]}
            dir_name_2, dir_files_d_2 = both_con[1][0], {i[0]: i[1] for i in both_con[1][1]}
            dir_files_1 = dir_files_d_1.keys()
            dir_files_2 = dir_files_d_2.keys()

            # 处理非共有的文件
            diff_files = list(set(dir_files_1) ^ set(dir_files_2))
            for f_dif in diff_files:
                if f_dif in (self.identify, g_info_f):
                    continue
                d1_fn = os.path.join(dir_name_1, f_dif)
                d2_fn = os.path.join(dir_name_2, f_dif)
                if not os.path.exists(d1_fn):
                    os.makedirs(os.path.split(d1_fn)[0], exist_ok=True)
                    self._copy_files(d2_fn, d1_fn)
                else:
                    os.makedirs(os.path.split(d2_fn)[0], exist_ok=True)
                    self._copy_files(d1_fn, d2_fn)

            # 处理共有文件，最近更新的文件覆盖之前的文件
            common_files = list(set(dir_files_1) & set(dir_files_2))
            for f_com in common_files:
                f1 = os.path.join(dir_name_1, f_com)
                f2 = os.path.join(dir_name_2, f_com)
                try:
                    if f_com in (self.identify, g_info_f) or filecmp.cmp(f1, f2):
                        continue
                except FileNotFoundError as e:
                    continue
                try:
                    if dir_files_d_1[f_com] > dir_files_d_2[f_com]:
                        self._copy_files(f1, f2)
                    elif dir_files_d_1[f_com] < dir_files_d_2[f_com]:
                        self._copy_files(f2, f1)
                    else:
                        pass
                except (FileNotFoundError, PermissionError) as e:
                    pass

    def get_all_files(self):
        """
        @summary: multiprocessing to get all file's info
        :return: (top_path, file's info), info_d
            $top_path,type==str
            $file's info, type==list, [(absolute path, file's modification time), (), (), ...]
            $info_d, type==dict, key==diretory path, value==last time file's info
        """
        poo = Pool()
        mon_dirs, identify, backup = self._parser_conf()
        pool_list = []
        self.identify = identify
        self.backup = backup
        info_d = {}
        for d in mon_dirs:
            if not os.path.exists(d):
                print("Attention directory did't exist: %s" % d)
                continue
            info_f = os.path.join(d, g_info_f)
            if os.path.exists(os.path.join(d, identify)):
                pool_list.append(poo.apply_async(self._get_file_tree, args=(d,)))
                if not os.path.exists(info_f):
                    info_d[d] = {}
                else:
                    try:
                        with open(info_f, 'rb') as fp:
                            info_d[d] = pickle.load(fp)
                    except EOFError as e:
                        info_d[d] = {}
            else:
                print(u"Attention directory '%s' did't contain identify file : %s, So can't syncronization" % (d, identify))
        poo.close()
        poo.join()
        all_files_info = [i.get() for i in pool_list]
        all_files_info = [(i[0], [(os.path.relpath(o[0], i[0]), o[1]) for o in i[1]]) for i in all_files_info]
        return all_files_info, info_d

    def _copy_files(self, src, dst):
        global g_copy_count
        try:
            shutil.copy2(src=src, dst=dst)
            g_copy_count += 1
            print('Copy: Source || Destination     %s || %s' % (src, dst))
        except (FileNotFoundError, PermissionError) as e:
            pass

    def _get_file_tree(self, top_path):
        """
        @sumamry: get top_path's all files
        :param top_path: assigment diretory path
        :return: top_path, file's info
            $top_path,type==str
            $file's info, type==list, [(absolute path, file's modification time), (), (), ...]
        """
        all_f = [[os.path.join(i[0], o) for o in i[2]] for i in list(os.walk(top_path)) if i[2]]
        files_info = []
        for f_l in all_f:
            for f in f_l:
                try:
                    files_info.append((f, os.stat(f).st_mtime))
                except PermissionError:
                    pass
        return top_path, files_info

    def _move(self, src, dst):
        global g_del_count
        os.makedirs(os.path.split(dst)[0], exist_ok=True)
        if os.path.exists(dst):
            ident = '(%s)' % str(uuid.uuid1())
            dst = ident.join(os.path.splitext(dst))
        try:
            shutil.move(src, dst)
            g_del_count += 1
        except FileNotFoundError as e:
            pass

    def _parser_conf(self):
        """
        @sumamry: parser config file
        :return: assigment directorys; identify name; backup directory
        """
        if not os.path.exists(self.conf):
            print("The config file %s did't exist" % self.conf)
            sys.exit(1)
        default_sect = set(['dirs', 'identify', 'backup'])
        parser = configparser.ConfigParser()
        parser.read(self.conf, encoding="utf-8-sig")
        sections = set(parser.sections())
        if default_sect - sections:
            print("The config file %s must contain sections ['dirs', 'identify', 'backup']")
        return list(parser['dirs'].values()), list(parser['identify'].values())[0], list(parser['backup'].values())[0]



if __name__ == '__main__':
    sync_work = SyncDirs()
    sync_work.run(del_empty=True)

