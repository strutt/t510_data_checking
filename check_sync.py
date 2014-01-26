# -*- coding: utf-8 -*-
from pylab import *
import datetime

dirc='/Users/benstrutt/Dropbox/data/'
fname_694='test_run_20_scope_694_date_1_23_2014_time_10_24_AM.lvm'
fname_784='test_run_20_scope_784_date_1_23_2014_time_10_24_AM.lvm'
fname_5204='test_run_20_scope_5204_date_1_23_2014_time_10_24_AM.lvm'

path_694=''.join([dirc,fname_694])
path_784=''.join([dirc,fname_784])
path_5204=''.join([dirc,fname_5204])
#print path

#############################################
#############################################
#############################################

def timediff(t1, t2): #entered as strings
  N=min(len(t1),len(t2))
  print 'in timediff'
  diff=[]
  for k in range(0,N):
      hr1=float(t1[k].split(':')[3])
      mn1=float(t1[k].split(':')[4])
      sc1=float(t1[k].split(':')[5])
      hr2=float(t2[k].split(':')[3])
      mn2=float(t2[k].split(':')[4])
      sc2=float(t2[k].split(':')[5])
      d_hr=hr1-hr2
      d_mn=mn1-mn2
      d_sc=sc1-sc2
      delta = d_sc + d_mn*60 + d_hr*60*60
      print ''
      print hr1, mn1, sc1
      print hr2, mn2, sc2
      print d_hr, d_mn, d_sc, delta
      diff.append(delta)
  return diff

#################################################
#################################################
#################################################

def check_time_sync():
  dates_694=[]
  dates_784=[]
  dates_5204=[]
  for line in file(path_694):
    if('2014:' in line):
      dates_694.append(line[0:29])
  for line in file(path_784):
    if('2014:' in line):
      dates_784.append(line[0:29])
  for line in file(path_5204):
    if('2014:' in line):
      dates_5204.append(line[0:29])
  print dates_784
  N=min((len(dates_694),len(dates_784)),len(dates_5204))
  print len(dates_694)
  print len(dates_784)
  print len(dates_5204)

  for k in range(0,N):
    print k
    print dates_694[k]
    #print dates_784[k].split('//')[1]
    print dates_5204[k]
    #print ''
    
  print len(dates_694)
  print len(dates_784)
  print len(dates_5204)
  v1=[]
  v2=[]
  v3=[]
  
  d1=[]
  d2=[]
  d3=[]

  for k in range(0,len(dates_694)):
    v1.append(float(dates_694[k].split(':')[5]))
  for k in range(0,len(dates_784)): 
    v2.append(float(dates_784[k].split(':')[5]))
  for k in range(0,len(dates_5204)): 
    v3.append(float(dates_5204[k].split(':')[5]))

  #print d1
  #exit()
  N1=len(dates_694)
  N2=len(dates_784)
  N3=len(dates_5204)
  subplot(211)
  plot(v1)
  #plot(v2)
  plot(v3)
  v1=array(v1)
  v2=array(v2)
  v3=array(v3)
  subplot(212)
  #plot(v3[0:N1]-v1[0:N3])
  #plot(mod(v1[0:N1]-v3[0:N3],60))
  print 'test'
  plot(timediff(dates_5204,dates_694))

  #plot(v2)
  #plot(v3)
  show()



check_time_sync()
exit()
