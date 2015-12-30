#!/usr/bin/env python

import os
import logging
from sys import argv, stderr, exit
from os.path import isdir, exists, join, relpath
from os import makedirs, rename
from shutil import rmtree
from time import sleep
from kazoo.client import KazooClient, KazooState

logging.basicConfig()

node_id = '%s/%d' % (os.uname()[1], os.getpid())

print >>stderr, 'Connecting...'

zk = KazooClient(hosts=os.getenv('ZK_HOST', '127.0.0.1:2181'))

@zk.add_listener
def on_connection(state):
  if state == KazooState.LOST:
    print >>stderr, 'Connection to Zookeeper lost.'
  elif state == KazooState.SUSPENDED:
    print >>stderr, 'Connection to Zookeeper lost... Retrying...'
  else:
    print >>stderr, 'Connected.'
    schedule_synchronize()

service_ns = os.getenv('SERVICE_NAMESPACE', '/service')
service_id = os.getenv('SERVICE_ID')
instance_ns = os.getenv('INSTANCE_NAMESPACE', '/instance')
instance_id = os.getenv('INSTANCE_ID', node_id)

base_zk_path = '%s/%s' % (service_ns, service_id)

def schedule_synchronize():
  global flag_change, flag_throttle
  flag_change = True
  flag_throttle = True

def on_watch_event(ev):
  global flag_change, flag_throttle
  flag_change = True
  flag_throttle = False
  print >>stderr, ev

def service_reload():
  composefile = 'docker-compose.yml'
  if exists(composefile + '.zdsave'):
    # docker-compose stop
    cmd = 'docker-compose -f %s.zdsave -p %s kill' % (composefile, service_id)
    print >>stderr, 'Stopping %s... (%s)' % (service_id, cmd)
    ret = os.system(cmd)
    if not ret:
      print >>stderr, 'Stopped %s.' % service_id
    else:
      print >>stderr, 'Failed to stop %s.' % service_id
  if not exists(composefile):
    print >>stderr, 'No docker-compose.yml file for %s service.' % service_id
  else:
    # docker-compose up
    cmd = 'docker-compose -f %s -p %s up -d' % (composefile, service_id)
    print >>stderr, 'Starting %s... (%s)' % (service_id, cmd)
    ret = os.system(cmd)
    if not ret:
      print >>stderr, 'Started %s.' % service_id
    else:
      print >>stderr, 'Failed to start %s.' % service_id

def fetch(node):
  changed = False
  filename = relpath(node, base_zk_path)
  zk.ensure_path(node)
  data, stat = zk.get(node, watch=on_watch_event)
  if stat.numChildren > 0 or node == base_zk_path:
    print >>stderr, '  Directory %s' % filename
    if exists(filename) and not isdir(filename):
      rmtree(filename)
      changed |= True
    if not exists(filename):
      makedirs(filename)
      changed |= True
    for child_node in zk.get_children(node, watch=on_watch_event):
      changed |= fetch(join(node, child_node))
  else:
    if exists(filename):
      filedata = open(filename, 'rb').read()
      changed |= len(filedata) != len(data) or filedata != data
      if changed:
        print >>stderr, '   Updating %s' % filename
        # keep a backup of previous configuration
        rename(filename, filename + '.zdsave')
      else:
        print >>stderr, '  Unchanged %s' % filename
    else:
      print >>stderr, '   Creating %s' % filename
      changed |= True
    f = open(filename, 'wb')
    f.write(data)
    f.close()
  return changed

def synchronize():
  print >>stderr, 'Acquiring access lock...'
  with zk.Lock(base_zk_path + '.lock', instance_id):
    print >>stderr, 'Synchronizing configuration...'
    if fetch(base_zk_path):
      print >>stderr, 'Reload service...'
      # keep locked to avoid more update to configuration during reload
      service_reload()

zk.start()

def loop():
  global flag_change, flag_throttle
  while True:
    if flag_change:
      if not flag_throttle:
        flag_throttle = True
      else:
        flag_change = False
        synchronize()
    sleep(1)

loop()

