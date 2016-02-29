#!/usr/bin/python
# -*- coding: utf-8 -*-
# vi: sw=4 ts=4 sts=4 noet ft=python :

# Copyright 2016 Alexander Böhm
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from elasticsearch import Elasticsearch, helpers, exceptions
import sys
import argparse
import re

class QueryOlderThan(argparse.Action):
	def __init__(self, option_strings, dest, nargs=None, **kwargs):
		if nargs is not None:
			raise ValueError("nargs not allowed")
		super(QueryOlderThan, self).__init__(option_strings, dest, **kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		setattr(namespace, self.dest, { "query": { "range": { "@timestamp": { "lt": "now-"+values } } } })

class QueryNewerThan(argparse.Action):
	def __init__(self, option_strings, dest, nargs=None, **kwargs):
		if nargs is not None:
			raise ValueError("nargs not allowed")
		super(QueryNewerThan, self).__init__(option_strings, dest, **kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		setattr(namespace, self.dest, { "query": { "range": { "@timestamp" : { "gt": "now-"+values } } } })

class QueryHasTags(argparse.Action):
	def __init__(self, option_strings, dest, nargs=None, **kwargs):
		if nargs is not None:
			raise ValueError("nargs not allowed")
		super(QueryHasTags, self).__init__(option_strings, dest, **kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		setattr(namespace, self.dest, { "query": { "terms": { "tags": values.split(',') } } })

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Elasticsearch document deletion utility')
	parser.add_argument(
		'--url', '-u',
		help='URL to HTTP-interface of elasticsearch (default: localhost:9200)',
		dest='url',
		nargs='?',
		default='localhost:9200',
		)
	parser.add_argument(
		'--doctype', '-d',
		help='select document type (default: any)',
		dest='doc_type',
		nargs='?',
		default=None,
		)
	parser.add_argument(
		'--query', '-q',
		help='a query-dsl expression (default: all documents)',
		dest='query',
		nargs='?',
		default=None,
		)
	parser.add_argument(
		'--index', '-i',
		help='select index (document: all indices)',
		dest='index',
		nargs='?',
		default=None,
		)
	parser.add_argument(
		'--force', '-f',
		action='store_true',
		help='run without confirmation',
		dest='force',
		default=False,
		)
	parser.add_argument(
		'--verbose', '-v',
		action='count',
		help='print what\'s going on',
		)
	parser.add_argument(
		'--dryrun', '-r',
		action='store_true',
		help='don\'t execute delete commands',
		default=False,
		)
	group = parser.add_mutually_exclusive_group(required=False)
	group.add_argument(
		'--newer', '-n',
		action=QueryNewerThan,
		help='select all documents newer than given time (relative)',
		dest='query',
	)
	group.add_argument(
		'--older', '-o',
		action=QueryOlderThan,
		help='select all documents older than given time (relative)',
		dest='query',
	)
	group.add_argument(
		'--tags', '-t',
		action=QueryHasTags,
		help='select all documents with tags (separated by commas)',
		dest='query',
	)
	args = parser.parse_args()

	if (args.verbose >= 1 and args.query != None):
		print('Query: %s' % (args.query))

	try:
		es = Elasticsearch([args.url])
		scroll = es.search(
			index=args.index,
			doc_type=args.doc_type,
			scroll='5m',
			search_type='scan',
			body=args.query,
			)
		total = scroll['hits']['total']

	except exceptions.ImproperlyConfigured as e:
		print('Bad parameter for elasticsearch: %s' % (e))
		sys.exit(0)

	if (args.verbose >= 1):
		print('total count of documents: %i' % (total))

	if (args.force == False):
		while True:
			sys.stdout.write('type \'YES\' to start delete: ')
			try:
				d = ""
				while len(d) < 4:
					c = sys.stdin.read(1)
					if c == '\n':
						break
					else:
						d += c

				if d[:3] == "YES":
					break

			except KeyboardInterrupt:
				sys.exit(0)
			except:
				pass

			print('No confirmation. Exiting.')
			sys.exit(0)

	deletes = 0
	try:
		while (deletes < total):
			r = es.scroll(scroll_id=scroll['_scroll_id'], scroll='60s')

			ids = ""
			bulk_deletes = []
			for i in r['hits']['hits']:
				if (args.verbose >= 2):
					ids += i['_id']+" "

				bulk_deletes.append({
					'_op_type': 'delete',
					'_index': i['_index'],
					'_type': i['_type'],
					'_id': i['_id'],
				})

			if (args.verbose >= 2):
				print("selected document IDs: %s" % (ids))

			if (args.dryrun == False):
				helpers.bulk(es, bulk_deletes)

			deletes += len(r['hits']['hits'])
			if (args.verbose >= 1):
				print('documents deleted: %i' % (deletes))

	except KeyboardInterrupt:
		pass

	sys.exit(0)


