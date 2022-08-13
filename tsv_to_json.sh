#!/bin/sh

awk '/^[^#]/ {
print "{ \"id\":\"e",n++,"\", \"name\":\"",$2,"\", \"sourceVertexId\":\"",$1,"\", \"targetVertexId\":\"",$3,"\", \"input\":\"",$2,"\", \"output\":\"\" },"
}' OFS= $1

