#! /usr/bin/env python

import unittest
import os, tempfile, shutil, filecmp
import nanomonsnv


class Test_detect_main(unittest.TestCase):

    def setUp(self):
        self.parser = nanomonsnv.parser.create_parser()

    def test1(self):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        tmp_dir = tempfile.mkdtemp()
        in_tumor_bam = cur_dir + "/../data/COLO829_v600_test.bam"
        in_normal_bam = cur_dir + "/../data/COLO829BL_v600_test.bam"
        reference = "/home/ubuntu/environment/database/GRCh37.fa"
        output_file = tmp_dir+"/COLO829_V600_test1_detectout.txt"
        args = self.parser.parse_args(["detect", in_tumor_bam, in_normal_bam, output_file, reference])
        args.func(args)

        answer_file = cur_dir + "/../data/COLO829_V600_test_detectout.txt"
        self.assertTrue(filecmp.cmp(output_file, answer_file, shallow=False))
        shutil.rmtree(tmp_dir)
