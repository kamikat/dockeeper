#!/usr/bin/env python

import os
import logging
from sys import argv, stderr, exit
from os.path import isdir, exists, join, relpath
from kazoo.client import KazooClient, KazooState

logging.basicConfig();

if len(argv) < 3:
  print >>stderr, 'Usage: %s <service_id> <config_dir>' % argv[0]
  exit(-1)

node_id = '%s/%d' % (os.uname()[1], os.getpid())

service_id = argv[1]
service_ns = os.getenv('SERVICE_NAMESPACE', '/service')

config_dir = argv[2]

success = False

print >>stderr, 'Connecting... [%s]' % node_id

zk = KazooClient(hosts=os.getenv('ZK_HOST', '127.0.0.1:2181'))

@zk.add_listener
def on_connection(state):
  if state == KazooState.LOST:
    if (success):
      print >>stderr, 'Connection closed.'
      exit(0)
    else:
      print >>stderr, 'Connection to Zookeeper lost.'
      exit(1)
  elif state == KazooState.SUSPENDED:
    print >>stderr, 'Connection to Zookeeper lost... Retrying...'
  else:
    print >>stderr, 'Connected.'

zk.start()

base_zk_path = '%s/%s' % (service_ns, service_id)

def resolve_path(path):
  rel_path = relpath(path, config_dir)
  return base_zk_path if rel_path == '.' else join(base_zk_path, rel_path)

if exists(config_dir) and isdir(config_dir):
  print >>stderr, 'Acquiring access lock...'
  with zk.Lock(base_zk_path + '.lock', node_id):
    for dirname, dirs, files in os.walk(config_dir):
      zk.ensure_path(resolve_path(dirname))
      print >>stderr, '  Directory zk://' + resolve_path(dirname)
      for filename in files:
        filename = join(dirname, filename)
        config_path = resolve_path(filename)
        value = open(filename, 'rb').read()
        if zk.exists(config_path):
          print >>stderr, '   Updating zk://%s from %s [%d bytes]' % (config_path, filename, len(value))
          zk.retry(zk.set, config_path, value)
        else:
          print >>stderr, '   Creating zk://%s from %s [%d bytes]' % (config_path, filename, len(value))
          zk.retry(zk.create, config_path, value)
else:
  print >>stderr, 'Invalid configuration directory'

success = True

zk.stop();
