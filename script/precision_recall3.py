from __future__ import print_function 
import sys, argparse
import os, time
import math
import subprocess
import pysam
import shutil

# TP / (TP + FN) = recall
def tpr(lvT, relevant_element):
    return len(lvT) / relevant_element

# TP / (TP + FP) = precision
def ppv(lvT, lvF):
    return len(lvT) / (len(lvT)+len(lvF))
    
def get_presigion_recall(variant_file, group, hout, relevant_element=42993):

    l_valid_T = []
    l_valid_F = []
    with open(variant_file, 'r') as hin:
        for line in hin:
            line = line.rstrip('\n')
            F = line.split('\t')
            if F[38] == "True":
                l_valid_T.append(1)
            else:
                l_valid_F.append(1)
            
            print (str(round(ppv(l_valid_T,l_valid_F),4)) +"\t"+ str(round(tpr(l_valid_T, relevant_element),4)) +"\t"+ group, file = hout)


def filter_result(in_file, out_file, filter_type):
    
    hout = open(out_file, 'w')
    with open(in_file, 'r') as hin:
        for line in hin:
            F = line.rstrip('\n').split('\t')
    
            if int(filter_type) >= 4:
                #
                # fisher test
                if float(F[10]) < - math.log10(0.005): continue
            
            if int(filter_type) >= 2:
                # 2
                # strandness tumor
                if float(F[11]) > 0.95 or float(F[11]) < 0.05: continue 
                # 2
                # max_plus_base_qual_tumor
                if int(F[15]) < 10: continue
                # 2
                # max_minus_base_qual_tumor
                if int(F[16]) < 10: continue
    
            if int(filter_type) >= 3:
                # 3
                # import pdb; pdb.set_trace()        
                # non-matched control max error ratio
                if float(F[28]) > 0.12: continue
                # 3
                # non-matched control median error ratio
                if float(F[29]) > 0.10: continue
            
            print('\t'.join(F), file = hout)
    hout.close()

def annotate_anno(variant_file, output_file, ccl_tabix):

    target_rnames_ccl = []
    tabix_cmd = ['tabix','-l',ccl_tabix]
    print(tabix_cmd)
    proc = subprocess.Popen(tabix_cmd, stdout = subprocess.PIPE)
    for chromosome_name in proc.stdout:
        chromosome_name = chromosome_name.decode().rstrip('\n')
        target_rnames_ccl.append(chromosome_name)
    proc.stdout.close()
    proc.wait()
    
    header_end_flag = False
    ccl_tabix_db = pysam.Tabixfile(ccl_tabix, encoding="utf-8")
    hout = open(output_file, 'w')
    with open(variant_file, 'r') as hin:
        for line in hin:
            line = line.rstrip('\n')
            
            if line.startswith('#'):
                print(line, file = hout)
            else:
                header_end_flag = True
            
            if not header_end_flag: continue
            
            nanosnv_record = line
            F = line.split('\t')
            # chrom = "chr"+F[0]
            chrom = F[0]
            pos = F[1]
            ref = F[2]
            alt = F[3]
            if ccl_tabix is not None:
            
                called_by = False
                if chrom in target_rnames_ccl:
                    for record_line in ccl_tabix_db.fetch(chrom, int(pos) - 1, int(pos) + 1):
                        record = record_line.split('\t')
                        
                        TYPE = ""
                        continue_flag = True
                        infos = record[7].split(';')
                        for info in infos:
                            if info.startswith("TYPE="):
                                TYPE = info.replace("TYPE=", '')
                                if TYPE in ["SNV","MNV"]:
                                    continue_flag = False
                                    break
                        
                        if continue_flag: continue
                        if record[0] != chrom: continue
                        if record[1] != pos: continue
                        if record[4] != alt: continue

                        infos = record[7].split(';')
                        for info in infos:
                            if info.startswith("called_by="):
                                # called_by = info.replace("called_by=", '')
                                called_by = True
                                break

                nanosnv_record = nanosnv_record + "\t" + str(called_by)
                
            print(nanosnv_record, file = hout)  

    hout.close()            


input_file = sys.argv[1]
output_file = sys.argv[2]
ccl_tabix = sys.argv[3]


cmd = ["sort", "-k", "11", "-r", "-n", input_file]
with open(output_file+".sorted.txt", 'w') as hout:
    subprocess.check_call(cmd, stdout=hout)

annotate_anno(output_file+".sorted.txt", output_file+".anno.txt", ccl_tabix)

shutil.copy(output_file+".anno.txt", output_file+".filt1.txt")
filter_result(output_file+".anno.txt", output_file+".filt2.txt", 2)
filter_result(output_file+".anno.txt", output_file+".filt3.txt", 3)

with open(output_file, 'w') as hout:
    get_presigion_recall(output_file+".filt1.txt","Unfiltered", hout)
    get_presigion_recall(output_file+".filt2.txt","Filtered", hout)
    get_presigion_recall(output_file+".filt3.txt","Filtered panel-of-normal", hout)
