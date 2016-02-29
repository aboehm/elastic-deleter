# Elastic-deleter

Yet another elasticsearch utility helps by document deletion.

## Help

```
usage: elastic-deleter.py [-h] [--url [URL]] [--doctype [DOC_TYPE]]
                          [--query [QUERY]] [--index [INDEX]] [--force]
                          [--verbose] [--dryrun]
                          [--newer QUERY | --older QUERY | --tags QUERY]

Elasticsearch document deletion utility

optional arguments:
  -h, --help            show this help message and exit
  --url [URL], -u [URL]
                        URL to HTTP-interface of elasticsearch (default:
                        localhost:9200)
  --doctype [DOC_TYPE], -d [DOC_TYPE]
                        select document type (default: any)
  --query [QUERY], -q [QUERY]
                        a query-dsl expression (default: all documents)
  --index [INDEX], -i [INDEX]
                        select index (document: all indices)
  --force, -f           run without confirmation
  --verbose, -v         print what's going on
  --dryrun, -r          don't execute delete commands
  --newer QUERY, -n QUERY
                        select all documents newer than given time (relative)
  --older QUERY, -o QUERY
                        select all documents older than given time (relative)
  --tags QUERY, -t QUERY
                        select all documents with tags (separated by commas)
```
## Examples

Delete from Node *localhost* any document of type with an error tag:

```
elastic-deleter.py -d syslog -u http://localhost:9200 --tags error
```

Delete from Node *es0.cluster* any document in index *logstash*, that has an timestamp older than two weaks from now:

```
elastic-deleter.py -i logstash -u es0.cluster:9200 --older 2w
```

Delete from Node *localhost* any document, that has an timestamp within the last three days:

```
elastic-deleter.py -i logstash --older 3d
```

