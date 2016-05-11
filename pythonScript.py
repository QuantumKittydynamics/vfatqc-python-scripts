#!/bin/env python

# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 09:28:14 2016

@author: Hugo
"""

import sys, os, random, time
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/kernel")
from ipbus import *

Passed = '\033[92m   > Passed... \033[0m'
Failed = '\033[91m   > Failed... \033[0m' 

def txtTitle(str):
    print '\033[1m' + str + '\033[0m'

import cProfile, pstats, StringIO
pr = cProfile.Profile()
pr.enable()

gilbIP = raw_input("> Enter the GLIB's IP address: ")
Date = raw_input("> Enter the Name of the Test [In case of conflict, the old file will be overwrite]: ")
glib = GLIB(gilbIP.strip())   

GLIB_REG_TEST = raw_input("> Number of register tests to perform on the GLIB [100]: ")
OH_REG_TEST = raw_input("> Number of register tests to perform on the OptoHybrid [100]: ")
I2C_TEST = raw_input("> Number of I2C tests to perform on the VFAT2s [100]: ")
TK_RD_TEST = raw_input("> Number of tracking data packets to readout [100]: ")
RATE_WRITE = raw_input("> Write the data to disk when testing the rate [Y/n]: ")

GLIB_REG_TEST = 100 if GLIB_REG_TEST == "" else int(GLIB_REG_TEST)
OH_REG_TEST = 100 if OH_REG_TEST == "" else int(OH_REG_TEST)
I2C_TEST = 100 if I2C_TEST == "" else int(I2C_TEST)
TK_RD_TEST = 100 if TK_RD_TEST == "" else int(TK_RD_TEST)
RATE_WRITE = False if (RATE_WRITE == "N" or RATE_WRITE == "n") else True

THRESH_ABS = 0.1
THRESH_REL = 0.05
THRESH_MAX = 255
THRESH_MIN = 0
N_EVENTS = 1000.00
N_EVENTS_SCURVE = 1000.00
N_EVENTS_TRIM = 1000.00
VCAL_MIN = 0
VCAL_MAX = 255
MAX_TRIM_IT = 26
CHAN_MIN=0
CHAN_MAX=128
print

####################################################

txtTitle("A. Testing the GLIB's presence")
print "   Trying to read the GLIB board ID... If this test fails, the script will stop."

if (glib.get("board_id") != None ): print Passed
else:
    print Failed
    sys.exit()

testA = True

print

####################################################

txtTitle("B. Testing the OH's presence")
print "   Trying to set the OptoHybrid registers... If this test fails, the script will stop."

glib.set("oh_sys_clk_src", 1)
glib.set("oh_sys_t1_src", 1)
glib.set("oh_sys_trigger_lim", 0)

if (glib.get("oh_sys_t1_src") == 1): print Passed
else:
    print Failed
    sys.exit()

testB = True

print

####################################################

txtTitle("C. Testing the GLIB registers")
print "   Performing single and FIFO reads on the GLIB counters and ensuring they increment." 

countersSingle = []
countersFifo = []
countersTest = True

for i in range(0, GLIB_REG_TEST): countersSingle.append(glib.get("glib_cnt_stb_cnt"))
countersFifo = glib.fifoRead("glib_cnt_stb_cnt", GLIB_REG_TEST)

for i in range(1, GLIB_REG_TEST):
    if (countersSingle[i - 1] + 1 != countersSingle[i]): countersTest = False
    if (countersFifo[i - 1] + 1 != countersFifo[i]): countersTest = False

if (countersTest): print Passed
else: print Failed

testC = countersTest

print

####################################################

txtTitle("D. Testing the OH registers")
print "   Performing single and FIFO reads on the OptoHybrid counters and ensuring they increment." 

countersSingle = []
countersFifo = []
countersTest = True

for i in range(0, OH_REG_TEST): countersSingle.append(glib.get("oh_cnt_wb_gtx_stb"))
countersFifo = glib.fifoRead("oh_cnt_wb_gtx_stb", OH_REG_TEST)

for i in range(1, OH_REG_TEST):
    if (countersSingle[i - 1] + 1 != countersSingle[i]): countersTest = False
    if (countersFifo[i - 1] + 1 != countersFifo[i]): countersTest = False

if (countersTest): print Passed
else: print Failed

testD = countersTest

print

####################################################

txtTitle("E. Detecting the VFAT2s over I2C")
print "   Detecting VFAT2s on the GEM by reading out their chip ID." 

presentVFAT2sSingle = []
presentVFAT2sFifo = []

glib.set("ei2c_reset", 0)
glib.get("vfat2_all_chipid0")
chipIDs = glib.fifoRead("ei2c_data", 24)

for i in range(0, 24):
    if ((glib.get("vfat2_" + str(i) + "_chipid0") & 0xff) != 0): presentVFAT2sSingle.append(i)
    if ((chipIDs[i] & 0xff) != 0): presentVFAT2sFifo.append(i)

if (presentVFAT2sSingle == presentVFAT2sFifo): Passed
else: Failed

testE = True

print

for i in range(0,24):
    if (chipIDs[i] & 0xff !=0):
        print ("VFAT2 connected at port %s has the ID : %s" %(i, chipIDs[i] & 0xff))
    else:
        print ("No VFAT2 connected at port %s" %i)

print

####################################################

txtTitle("F. Testing the I2C communication with the VFAT2s")
print "   Performing random read/write operation on each connect VFAT2." 

testF = True

for i in presentVFAT2sSingle:
    validOperations = 0
    for j in range(0, I2C_TEST):
        writeData = random.randint(0, 255)
        glib.set("vfat2_" + str(i) + "_ctrl3", writeData)
        readData = glib.get("vfat2_" + str(i) + "_ctrl3") & 0xff
        if (readData == writeData): validOperations += 1
    glib.set("vfat2_" + str(i) + "_ctrl3", 0)
    if (validOperations == I2C_TEST):  print Passed, "#" + str(i)
    else: 
        print Failed, "#" + str(i)
        testF = False

print

####################################################

txtTitle("G. Reading out tracking data")
print "   Sending triggers and testing if the Event Counter adds up."

glib.set("ei2c_reset", 0)
glib.set("vfat2_all_ctrl0", 0)

testG = True

for i in presentVFAT2sSingle:
    glib.set("vfat2_" + str(i) + "_ctrl0", 55)
    glib.set("oh_sys_vfat2_mask", ~(0x1 << i))
    glib.set("tk_data_rd", 0)

    nPackets = 0
    timeOut = 0
    ecs = []

    glib.set("t1_reset", 1)
    glib.set("t1_mode", 0)
    glib.set("t1_type", 0)
    glib.set("t1_n", TK_RD_TEST)
    glib.set("t1_interval", 600)
    glib.set("t1_toggle", 1)

    while (glib.get("tk_data_cnt") != 7 * TK_RD_TEST): 
        timeOut += 1
        if (timeOut == 10 * TK_RD_TEST): break

    while (glib.get("tk_data_empty") != 1):
        packets = glib.fifoRead("tk_data_rd", 7)
        ec = int((0x00000ff0 & packets[0]) >> 4)
        nPackets += 1
        ecs.append(ec)

    glib.set("vfat2_" + str(i) + "_ctrl0", 0)

    if (nPackets != TK_RD_TEST): print Failed, "#" + str(i)
    else:
        followingECS = True
        for j in range(0, TK_RD_TEST - 1):
            if (ecs[j + 1] - ecs[j] != 1): followingECS = False
        if (followingECS): print Passed, "#" + str(i)
        else: 
            print Failed, "#" + str(i)
            testG = False

print

####################################################

txtTitle("H. Reading out tracking data")
print "   Turning on all VFAT2s and looking that all the Event Counters add up."

testH = True

if (testG):
    glib.set("ei2c_reset", 0)
    glib.set("vfat2_all_ctrl0", 55)

    mask = 0
    for i in presentVFAT2sSingle: mask |= (0x1 << i)
    glib.set("oh_sys_vfat2_mask", ~mask)

    glib.set("t1_reset", 1)
    glib.set("t1_mode", 0)
    glib.set("t1_type", 2)
    glib.set("t1_n", 1)
    glib.set("t1_interval", 10)
    glib.set("t1_toggle", 1)

    glib.set("tk_data_rd", 1)

    glib.set("t1_reset", 1)
    glib.set("t1_mode", 0)
    glib.set("t1_type", 0)
    glib.set("t1_n", TK_RD_TEST)
    glib.set("t1_interval", 400)
    glib.set("t1_toggle", 1)

    nPackets = 0
    timeOut = 0
    ecs = []

    while (glib.get("tk_data_cnt") != len(presentVFAT2sSingle) * TK_RD_TEST):
        timeOut += 1 
        if (timeOut == 20 * TK_RD_TEST): break

    while (glib.get("tk_data_empty") != 1):
        packets = glib.fifoRead("tk_data_rd", 7)
        ec = int((0x00000ff0 & packets[0]) >> 4)
        nPackets += 1
        ecs.append(ec)

    glib.set("ei2c_reset", 0)
    glib.set("vfat2_all_ctrl0", 0)

    if (nPackets != len(presentVFAT2sSingle) * TK_RD_TEST): print Failed, "#" + str(i)
    else:
        followingECS = True
        for i in range(0, TK_RD_TEST - 1):
            for j in range(0, len(presentVFAT2sSingle) - 1):
                if (ecs[i * len(presentVFAT2sSingle) + j + 1] != ecs[i * len(presentVFAT2sSingle) + j]): followingECS = False
            if (ecs[(i + 1) * len(presentVFAT2sSingle)] - ecs[i * len(presentVFAT2sSingle)] != 1): followingECS = False
        if (followingECS): print Passed
        else: 
            print Failed
            testH = False

    glib.set("t1_reset", 1)

else:
    print "   Skipping this test as the previous test did not succeed..."
    testH = False

print 

########################## The Script ################################
# For each VFAT2 Connected

for port in presentVFAT2sSingle:
    ## this is hacked to ignore middle column
    if port>7 and port<16:
	continue
    ## this is hacked to only scan VFAT2
    if port != 2:
        continue
    print "------------------------------------------------------"
    print "--------------- Testing VFAT2 port %s" %port,"-----------------"
    print "------------------------------------------------------"
    nameIP = gilbIP.replace(".","_")
    f = open(str(Date)+"_Data_GLIB_IP_"+ str(nameIP)+"_VFAT2_" + str(port)+ "_ID_" + str(chipIDs[port]&0xff),'w')    
    m = open(str(Date)+"_SCurve_by_channel"+ "_VFAT2_" + str(port)+ "_ID_" + str(chipIDs[port]&0xff),'w')  
    TotVCal0 = []
    TotVCal31 = []
    TotFoundVCal = []
    VCal_ref0 = 0
    VCal_ref31 = 0
    
    glib.set("oh_trigger_source", 1)

    
    glib.set("vfat2_" + str(port) + "_ctrl0", 55)
    glib.set("vfat2_" + str(port) + "_ctrl1", 0)
    glib.set("vfat2_" + str(port) + "_ctrl2", 48)
    glib.set("vfat2_" + str(port) + "_ctrl3", 0)
    glib.set("vfat2_" + str(port) + "_ipreampin", 168)
    glib.set("vfat2_" + str(port) + "_ipreampfeed", 80)
    glib.set("vfat2_" + str(port) + "_ipreampout", 150)
    glib.set("vfat2_" + str(port) + "_ishaper", 150)
    glib.set("vfat2_" + str(port) + "_ishaperfeed", 100)
    glib.set("vfat2_" + str(port) + "_icomp", 75)
    glib.set("vfat2_" + str(port) + "_vthreshold2", 0)
    glib.set("vfat2_" + str(port) + "_vthreshold1", 0)	 
    glib.set("t1_reset", 1)
    glib.set("t1_mode", 1)
    glib.set("t1_n", 0)
    glib.set("t1_interval", 400)
    glib.set("t1_delay", 40)
    glib.set("t1_toggle", 1)
    
    for channel in range(CHAN_MIN, CHAN_MAX):
        regName = "vfat2_" + str(port) + "_channel" + str(channel + 1)
	regValue = (1 << 6) + 16
        glib.set(regName, regValue)
    
################## Threshold Scan by VFAT2 #########################  
        
    glib.set('scan_reset', 1)
    glib.set('scan_mode', 0)
    glib.set('scan_vfat2', port)
    glib.set('scan_min', 0)
    glib.set('scan_max', 255)
    glib.set('scan_step', 1)
    glib.set('scan_n', 3000)
    glib.set('scan_toggle', 1)
    while (glib.get("scan_status") != 0): r = 1
    data_threshold = glib.fifoRead('scan_data', 256)
    for d in range (0,len(data_threshold)):
        print ((data_threshold[d] & 0xff000000) >> 24), " = ", (100*(data_threshold[d] & 0xffffff)/3000.0)
        if (100*(data_threshold[d] & 0xffffff)/ 3000.0) < THRESH_ABS and ((100*(data_threshold[d-1] & 0xffffff) / N_EVENTS) - (100*(data_threshold[d] & 0xffffff) / N_EVENTS)) < THRESH_REL:
            f.write("Threshold set to: " + str(d)+"\n")
            glib.set("vfat2_" + str(port) + "_vthreshold1", int(d))                
            break
    if d == 0 or d== 255: 
	print "ignored"
	for d in range (0,len(data_threshold)):
	    f.write(str((data_threshold[d] & 0xff000000) >> 24)+"\n") 
	    f.write(str(100*(data_threshold[d] & 0xffffff)/3000.0)+"\n")
	f.close()
	continue          
    for d in range (0,len(data_threshold)):
        f.write(str((data_threshold[d] & 0xff000000) >> 24)+"\n") 
        f.write(str(100*(data_threshold[d] & 0xffffff)/3000.0)+"\n")  
# for each channel
    for channel in range(CHAN_MIN, CHAN_MAX): 
        ## debug
        #if channel > 10:
        #    continue

        print "------------------- channel ", str(channel), "-------------------"
                
################## S-curve by channel ######################    
#### With TRIM DAC to 0
        glib.set("vfat2_" + str(port) + "_vthreshold2", 0)
        glib.set("vfat2_" + str(port) + "_latency", 37)
        regName = "vfat2_" + str(port) + "_channel" + str(channel + 1)
        regValue = (1 << 6)
        glib.set(regName, regValue)
          
        glib.set('scan_reset', 1)
        glib.set('scan_mode', 3)
        glib.set('scan_channel', channel)
        glib.set('scan_vfat2', port)
        glib.set('scan_min', VCAL_MIN)
        glib.set('scan_max', VCAL_MAX)
        glib.set('scan_step', 1)
        glib.set('scan_n', int(N_EVENTS_SCURVE))
        glib.set('scan_toggle', 1)
        while (glib.get("scan_status") != 0): i = 1
        data_scurve = glib.fifoRead('scan_data', VCAL_MAX - VCAL_MIN)
        glib.set(regName, 0)
        print
        print "---------------- s-curve data trimDAC 0 --------------------"
        for d0 in data_scurve:
            Eff = (d0 & 0xffffff) / N_EVENTS_SCURVE
            VCal = (d0 & 0xff000000) >> 24
	    if (Eff >= 0.48):
       	        print VCal, " => ",Eff
    	        TotVCal0.append(VCal)
	        break

        
#### With TRIM DAC to 16
        regValue = (1 << 6) + 16
        glib.set(regName, regValue)
          
        glib.set('scan_reset', 1)
        glib.set('scan_mode', 3)
        glib.set('scan_channel', channel)
        glib.set('scan_vfat2', port)
        glib.set('scan_min', VCAL_MIN)
        glib.set('scan_max', VCAL_MAX)
        glib.set('scan_step', 1)
        glib.set('scan_n', int(N_EVENTS_SCURVE))
        glib.set('scan_toggle', 1)
        while (glib.get("scan_status") != 0): i = 1
        data_scurve = glib.fifoRead('scan_data', VCAL_MAX - VCAL_MIN)
        glib.set(regName, 0)
        print
        print "---------------- s-curve data trimDAC 16 --------------------"
        m.write("SCurve_"+str(channel)+"\n")
        for d16 in data_scurve:
        	Eff = (d16 & 0xffffff) / N_EVENTS_SCURVE
        	VCal = (d16 & 0xff000000) >> 24
        	m.write(str(VCal)+"\n")
        	m.write(str(Eff)+"\n")
                   
        
        
        
#### With TRIM DAC to 31
        regValue = (1 << 6) + 31
        glib.set(regName, regValue)         
        glib.set('scan_reset', 1)
        glib.set('scan_mode', 3)
        glib.set('scan_channel', channel)
        glib.set('scan_vfat2', port)
        glib.set('scan_min', VCAL_MIN)
        glib.set('scan_max', VCAL_MAX)
        glib.set('scan_step', 1)
        glib.set('scan_n', int(N_EVENTS_SCURVE))
        glib.set('scan_toggle', 1)
        while (glib.get("scan_status") != 0): i = 1
        data_scurve = glib.fifoRead('scan_data', VCAL_MAX - VCAL_MIN)
        glib.set(regName, 0)
        print
        print "---------------- s-curve data trimDAC 31 --------------------"
        try:
            for d31 in data_scurve:
                Eff = (d31 & 0xffffff) / N_EVENTS_SCURVE
                VCal = (d31 & 0xff000000) >> 24
		if (Eff >= 0.48):
            	    print VCal, " => ",Eff
            	    TotVCal31.append(VCal)
		    break

        except:
            print "Error while reading the data, they will be ignored"
            continue
################## Adjust the trim for each channel ######################
    print
    print "------------------------ TrimDAC routine ------------------------"
    print
    h=open(str(Date)+"_VCal_VFAT2_" + str(port)+ "_ID_" + str(chipIDs[port]&0xff),'w')
    VCal_ref0 = sum(TotVCal0)/len(TotVCal0)
    h.write(str(TotVCal0)+"\n")
    VCal_ref31 = sum(TotVCal31)/len(TotVCal31)
    h.write(str(TotVCal31)+"\n")
    VCal_ref = (VCal_ref0 + VCal_ref31)/2
    print "VCal_ref0", VCal_ref0
    print "VCal_ref31", VCal_ref31
    g=open(str(Date)+"_TRIM_DAC_value_VFAT_"+str(port)+ "_ID_" + str(chipIDs[port]&0xff),'w')

    
    for channel in range(CHAN_MIN, CHAN_MAX):
        ## debug
        #if channel > 10:
        #    continue
        TRIM_IT = 0
        print "TrimDAC Channel", channel
        regName = "vfat2_" + str(port) + "_channel" + str(channel + 1)
        trimDAC = 16
        foundGood = False

        while (foundGood == False):
            regValue = (1 << 6) + trimDAC
       	    glib.set(regName, regValue)
          
            glib.set('scan_reset', 1)
            glib.set('scan_mode', 3)
            glib.set('scan_channel', channel)
            glib.set('scan_vfat2', port)
            glib.set('scan_min', VCAL_MIN)
            glib.set('scan_max', VCAL_MAX)
            glib.set('scan_step', 1)
            glib.set('scan_n', int(N_EVENTS_SCURVE))
            glib.set('scan_toggle', 1)
            while (glib.get("scan_status") != 0): i = 1
            data_trim = glib.fifoRead('scan_data', VCAL_MAX - VCAL_MIN)
            glib.set(regName, 0)
            try:
                for d in data_trim:
                    Eff = (d & 0xffffff) / N_EVENTS_SCURVE
                    VCal = (d & 0xff000000) >> 24
	     	    if (Eff >= 0.48):
            		print VCal, " => ",Eff
            		foundVCal = VCal
			break
            except:
                print "Error while reading the data, they will be ignored"
                continue

            if (foundVCal > VCal_ref and TRIM_IT < MAX_TRIM_IT and trimDAC < 31):
                trimDAC += 1
                TRIM_IT +=1
            elif (foundVCal < VCal_ref and TRIM_IT < MAX_TRIM_IT and trimDAC > 0):
                trimDAC -= 1
                TRIM_IT +=1
            else: 
                g.write(str(trimDAC)+"\n")
                TotFoundVCal.append(foundVCal)
                f.write("S_CURVE_"+str(channel)+"\n")
                for d in data_trim: 
                    f.write(str((d & 0xff000000) >> 24)+"\n") 
                    f.write(str((d & 0xffffff)/N_EVENTS_TRIM)+"\n")
                break
    m.close()
    h.write(str(TotFoundVCal)+"\n")
    h.close()
    g.close() 
    VCalList = []
    minVcal = 0
################# Set all the Trim_DAC to the right value ################# 
    g=open(str(Date)+"_TRIM_DAC_value_VFAT_"+str(port)+"_ID_"+ str(chipIDs[port]&0xff),'r')
    for channel in range(CHAN_MIN, CHAN_MAX):
        ## debug
        #if channel > 10:
        #    continue
        regName = "vfat2_" + str(port) + "_channel" + str(channel + 1)
        trimDAC = (g.readline()).rstrip('\n')
        print trimDAC
        regValue = (1 << 6) + int(trimDAC)

    g.close()  
########################## Final threshold by VFAT2 ###################### 
    f.write("second_threshold\n")
    glib.set('scan_reset', 1)
    glib.set('scan_mode', 0)
    glib.set('scan_vfat2', port)
    glib.set('scan_min', 0)
    glib.set('scan_max', 255)
    glib.set('scan_step', 1)
    glib.set('scan_n', 3000)
    glib.set('scan_toggle', 1)
    while (glib.get("scan_status") != 0): r = 1
    data = glib.fifoRead('scan_data', 255)
    for d in data:
        f.write(str((d & 0xff000000) >> 24)+"\n") 
        f.write(str(100*(d & 0xffffff)/3000.0)+"\n")     
    f.close()
    
pr.disable()
s = StringIO.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print s.getvalue()