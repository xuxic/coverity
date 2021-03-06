'''
Copyright (c) 2015, Baidu.com, Inc. All Rights Reserved
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
'''

import nose
import time
import unittest

import common
from conf import const

def setup():
    pass

def teardown():
    pass

class S1(unittest.TestCase):
    
    def setUp(self):
        out = common.runcmd_output("cd %s; ./teracli showts|grep kReady" % (const.teracli_dir), ignore_status=True)
        #assert( len(out.split('\n')) == len(const.tabletnode_list) )
        common.check_core()
        common.cleanup()
        #common.createbyfile('testcase/data/table_schema')
        
    def tearDown(self):
        pass

        '''
        table write w/snapshot
        1. write data set 1
        2. create snapshot
        3. write data set 2
        4. scan w/snapshot, scan w/o snapshot & compare
        :return: None
        '''
    def test_table_write_snapshot(self):

        common.create_singleversion_table()
        table_name = 'test'
        dump_file1 = 'dump1.out'
        dump_file2 = 'dump2.out'
        scan_file1 = 'scan1.out'
        scan_file2 = 'scan2.out'
        common.run_tera_mark([(dump_file1, False)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=10, value_size=100, num=10000, key_size=20)
        snapshot = common.snapshot_op(table_name)
        common.run_tera_mark([(dump_file2, False)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=11, value_size=100, num=10000, key_size=20)
        common.compact_tablets(common.get_tablet_list(table_name))
        common.scan_table(table_name=table_name, file_path=scan_file1, allversion=False, snapshot=snapshot)
        common.scan_table(table_name=table_name, file_path=scan_file2, allversion=False, snapshot=0)
        nose.tools.assert_true(common.compare_files(dump_file1, scan_file1, need_sort=True))
        nose.tools.assert_true(common.compare_files(dump_file2, scan_file2, need_sort=True))

        '''
        table write deletion w/snapshot
        1. write data set 1
        2. create snapshot
        3. delete data set 1
        4. scan w/snapshot, scan w/o snapshot & compare
        :return: None
        '''
    def test_table_write_del_snapshot(self):

        common.create_singleversion_table()
        table_name = 'test'
        dump_file = 'dump.out'
        scan_file1 = 'scan1.out'
        scan_file2 = 'scan2.out'
        common.run_tera_mark([(dump_file, False)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=10, value_size=100, num=10000, key_size=20)
        snapshot = common.snapshot_op(table_name)
        common.run_tera_mark([], op='d', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=11, value_size=100, num=10000, key_size=20)
        common.compact_tablets(common.get_tablet_list(table_name))
        common.scan_table(table_name=table_name, file_path=scan_file1, allversion=False, snapshot=snapshot)
        common.scan_table(table_name=table_name, file_path=scan_file2, allversion=False, snapshot=0)
        nose.tools.assert_true(common.compare_files(dump_file, scan_file1, need_sort=True))
        nose.tools.assert_true(common.file_is_empty(scan_file2))

        '''
        table write w/version w/snapshot
        1. write data set 1, 2
        2. create snapshot
        3. write data set 3, 4
        4. scan w/snapshot, scan w/o snapshot & compare
        :return: None
        '''
    def test_table_write_multiversion_snapshot(self):

        common.create_multiversion_table()
        table_name = 'test'
        dump_file1 = 'dump1.out'
        dump_file2 = 'dump2.out'
        scan_file1 = 'scan1.out'
        scan_file2 = 'scan2.out'
        common.run_tera_mark([(dump_file1, False)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=10, value_size=100, num=10000, key_size=20)
        common.run_tera_mark([(dump_file1, True)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=11, value_size=100, num=10000, key_size=20)
        snapshot = common.snapshot_op(table_name)
        common.run_tera_mark([(dump_file2, False)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=10, value_size=100, num=10000, key_size=20)
        common.run_tera_mark([(dump_file2, True)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=11, value_size=100, num=10000, key_size=20)
        common.compact_tablets(common.get_tablet_list(table_name))
        common.scan_table(table_name=table_name, file_path=scan_file1, allversion=True, snapshot=snapshot)
        common.scan_table(table_name=table_name, file_path=scan_file2, allversion=True, snapshot=0)
        nose.tools.assert_true(common.compare_files(dump_file1, scan_file1, need_sort=True))
        nose.tools.assert_true(common.compare_files(dump_file2, scan_file2, need_sort=True))

        '''
        kv cluster relaunch
        1. write data set 1
        2. create snapshot
        3. write data set 2
        4. scan w/snapshot, scan w/o snapshot & compare
        5. kill & launch cluster
        6. repeat 4
        :return: None
        '''
    def kv_snapshot_relaunch(self):

        table_name = 'test'
        dump_file1 = 'dump1.out'
        dump_file2 = 'dump2.out'
        scan_file1 = 'scan1.out'
        scan_file2 = 'scan2.out'
        common.run_tera_mark([(dump_file1, False)], op='w', table_name=table_name, random='random',
                             key_seed=1, value_seed=10, value_size=100, num=10000, key_size=20)
        snapshot = common.snapshot_op(table_name)
        common.run_tera_mark([(dump_file2, False)], op='w', table_name=table_name, random='random',
                             key_seed=1, value_seed=11, value_size=100, num=10000, key_size=20)
        common.compact_tablets(common.get_tablet_list(table_name))
        common.scan_table(table_name=table_name, file_path=scan_file1, allversion=True, snapshot=snapshot)
        common.scan_table(table_name=table_name, file_path=scan_file2, allversion=True, snapshot=0)
        nose.tools.assert_true(common.compare_files(dump_file1, scan_file1, need_sort=True))
        nose.tools.assert_true(common.compare_files(dump_file2, scan_file2, need_sort=True))
        common.cluster_op('kill')
        common.cluster_op('launch')
        time.sleep(2)
        common.scan_table(table_name=table_name, file_path=scan_file1, allversion=False, snapshot=snapshot)
        common.scan_table(table_name=table_name, file_path=scan_file2, allversion=False, snapshot=0)
        nose.tools.assert_true(common.compare_files(dump_file1, scan_file1, need_sort=True))
        nose.tools.assert_true(common.compare_files(dump_file2, scan_file2, need_sort=True))

        '''
        kv cluster relaunch
        1. write data set 1
        2. create snapshot
        3. write data set 2
        4. scan w/snapshot, scan w/o snapshot & compare
        5. kill & launch cluster
        6. repeat 4
        :return: None
        '''
    def test_kv_snapshot_relaunch(self):

        common.create_kv_table()
        self.kv_snapshot_relaunch()
        
        '''
        table cluster relaunch
        1. write data set 1
        2. create snapshot
        3. write data set 2
        4. scan w/snapshot, scan w/o snapshot & compare
        5. kill & launch cluster
        6. repeat 4
        :return: None
        '''
    def table_snapshot_relaunch(self):

        table_name = 'test'
        dump_file1 = 'dump1.out'
        dump_file2 = 'dump2.out'
        scan_file1 = 'scan1.out'
        scan_file2 = 'scan2.out'
        common.run_tera_mark([(dump_file1, False)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=10, value_size=100, num=10000, key_size=20)
        snapshot = common.snapshot_op(table_name)
        common.run_tera_mark([(dump_file2, False)], op='w', table_name=table_name, cf='cf0:q,cf1:q', random='random',
                             key_seed=1, value_seed=11, value_size=100, num=10000, key_size=20)
        common.compact_tablets(common.get_tablet_list(table_name))
        common.scan_table(table_name=table_name, file_path=scan_file1, allversion=True, snapshot=snapshot)
        common.scan_table(table_name=table_name, file_path=scan_file2, allversion=True, snapshot=0)
        nose.tools.assert_true(common.compare_files(dump_file1, scan_file1, need_sort=True))
        nose.tools.assert_true(common.compare_files(dump_file2, scan_file2, need_sort=True))
    
        common.cluster_op('kill')
        common.cluster_op('launch')
        time.sleep(2)
        common.scan_table(table_name=table_name, file_path=scan_file1, allversion=True, snapshot=snapshot)
        common.scan_table(table_name=table_name, file_path=scan_file2, allversion=True, snapshot=0)
        nose.tools.assert_true(common.compare_files(dump_file1, scan_file1, need_sort=True))
        nose.tools.assert_true(common.compare_files(dump_file2, scan_file2, need_sort=True))
        
        '''
        table cluster relaunch
        1. write data set 1
        2. create snapshot
        3. write data set 2
        4. scan w/snapshot, scan w/o snapshot & compare
        5. kill & launch cluster
        6. repeat 4
        :return: None
        '''
    def test_table_snapshot_relaunch(self):

        common.create_singleversion_table()
        self.table_snapshot_relaunch()
        
        '''
        kv snapshot w/multi tablets
        1. test_kv_snapshot_relaunch()
        :return:
        '''
    def test_kv_snapshot_multitablets(self):

        common.createbyfile(schema=const.data_path + 'kv.schema', deli=const.data_path + 'deli.10')
        self.kv_snapshot_relaunch()

        '''
        table snapshot w/multi tablets
        1. test_tablev_snapshot_relaunch()
        :return:
        '''
    def test_table_snapshot_multitablets(self):

        common.createbyfile(schema=const.data_path + 'table.schema', deli=const.data_path + 'deli.10')
        self.table_snapshot_relaunch()
